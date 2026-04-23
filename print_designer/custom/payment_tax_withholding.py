"""
Thai WHT PaymentTaxWithholding Override.

Overrides _calculate_account_wise_amount to use pd_custom_wht_liability_account
(2132-02) instead of account_head (1151-05) for the taxes child table.

This ensures Advance Taxes and Charges in Payment Entry shows the WHT Liability
account instead of the Asset WHT account.
"""

import frappe
from collections import defaultdict
from frappe.utils import flt
from erpnext.accounts.doctype.tax_withholding_entry.tax_withholding_entry import (
    PaymentTaxWithholding,
)


class ThaiPaymentTaxWithholding(PaymentTaxWithholding):
    """
    Thai WHT override: use liability account (2132-02) instead of asset account (1151-05)
    in the Advance Taxes and Charges child table.
    """

    def _update_taxable_amounts(self):
        """
        Override for Thai WHT on advance payments.

        If references child table is empty → advance payment.
        If Type (charge_type) in taxes = "Gross-up" → use gross-up calculation:
          - taxable_amount = net / (1 - rate)
          - withholding = taxable_amount × rate
        Otherwise → use standard ERPNext calculation.
        """
        print(f"[Thai WHT] _update_taxable_amounts called")
        print(f"[Thai WHT] references count: {len(self.doc.references)}")
        print(f"[Thai WHT] payment_type: {self.doc.payment_type}")
        print(f"[Thai WHT] base_paid_amount: {self.doc.base_paid_amount}")
        print(f"[Thai WHT] base_received_amount: {self.doc.base_received_amount}")

        category = next(iter(self.category_details.values()))
        print(f"[Thai WHT] category name: {category.get('name')}")
        print(f"[Thai WHT] category tax_rate: {category.get('tax_rate')}")
        print(f"[Thai WHT] category taxable_amount before: {category.get('taxable_amount')}")

        # If references has rows → not an advance (invoice-based) → use standard
        if self.doc.references:
            print(f"[Thai WHT] Has references - using standard calculation")
            super()._update_taxable_amounts()
            print(f"[Thai WHT] category taxable_amount after standard: {category.get('taxable_amount')}")
            return

        # Advance case - check if any tax row uses Gross-up type.
        # NOTE: do NOT filter by is_tax_withholding_account here. The system-generated WHT row
        # has is_tax_withholding_account=1 but charge_type="Actual"; the user's Gross-up trigger
        # row typically has charge_type="Gross-up" but is_tax_withholding_account=0. Requiring
        # both on the same row means gross_up_rows is always empty → falls back to standard
        # calculation (taxable = 9700) → withholding = 291 instead of 300.
        gross_up_rows = [
            t for t in self.doc.taxes
            if t.get("charge_type") == "Gross-up"
        ]
        print(f"[Thai WHT] Gross-up rows count: {len(gross_up_rows)}")

        if not gross_up_rows:
            # No Gross-up row → use standard calculation
            print(f"[Thai WHT] No Gross-up row - using standard calculation")
            super()._update_taxable_amounts()
            print(f"[Thai WHT] category taxable_amount after standard: {category.get('taxable_amount')}")
            return

        # Gross-up calculation for advance payments
        # net = gross - (gross × rate) = gross × (1 - rate)
        # So: gross = net / (1 - rate)
        if self.doc.payment_type == "Pay":
            net_amount = flt(self.doc.base_paid_amount, self.precision)
        elif self.doc.payment_type == "Receive":
            net_amount = flt(self.doc.base_received_amount, self.precision)
        else:
            # Internal transfer - use standard
            print(f"[Thai WHT] Internal transfer - using standard calculation")
            super()._update_taxable_amounts()
            return

        # Get tax rate from category (NOT from the Gross-up row's rate field,
        # which is 0 for Gross-up type in ERPNext). The actual rate lives in
        # category.tax_rate (from TWC rates child table).
        tax_rate = category.get("tax_rate", 0) / 100.0
        print(f"[Thai WHT] net_amount: {net_amount}, tax_rate from category: {tax_rate}")

        if tax_rate > 0:
            # Reverse-calculate gross from net: gross = net / (1 - rate)
            taxable_amount = net_amount / (1 - tax_rate)
        else:
            taxable_amount = net_amount

        print(f"[Thai WHT] calculated taxable_amount: {taxable_amount}")
        category["taxable_amount"] = taxable_amount
        print(f"[Thai WHT] category taxable_amount after set: {category.get('taxable_amount')}")

        # IMPORTANT: Do NOT call super() here - the parent method would overwrite
        # category.taxable_amount back to net_amount (9700), breaking the gross-up
        # calculation. Return immediately so _create_entries_for_category uses gross.
        return

    def _create_entries_for_category(self, category):
        """
        Override to set pd_custom_gross_amount on each entry.

        For Gross-up advance payments, category.taxable_amount is the GROSS amount
        (reverse-calculated from net). Store this as pd_custom_gross_amount so the
        Tax Withholding Entry record shows the correct gross amount.
        """
        entries = super()._create_entries_for_category(category)

        # Set pd_custom_gross_amount = taxable_amount for all entries in gross-up case.
        # The taxable_amount is already the GROSS amount (10000) for Gross-up.
        gross_amount = category.get("taxable_amount")
        if gross_amount and gross_amount > 0:
            for entry in entries:
                entry["pd_custom_gross_amount"] = gross_amount

        return entries

    def _calculate_account_wise_amount(self):
        """
        Override to use pd_custom_wht_liability_account from TWC accounts child table
        instead of category.account_head (which is the asset account).
        """
        print(f"[Thai WHT] _calculate_account_wise_amount called")
        print(f"[Thai WHT] doc.tax_withholding_entries count: {len(self.doc.tax_withholding_entries)}")
        print(f"[Thai WHT] category_details keys: {list(self.category_details.keys())}")

        account_amount_map = defaultdict(float)

        for entry in self.doc.tax_withholding_entries:
            print(f"[Thai WHT]   entry: name={entry.name}, withholding_amount={entry.withholding_amount}, tax_rate={entry.tax_rate}")
            if entry.withholding_name != self.doc.name:
                print(f"[Thai WHT]     skipping - withholding_name={entry.withholding_name} != doc.name={self.doc.name}")
                continue

            category = self.category_details.get(entry.tax_withholding_category)
            if not category:
                print(f"[Thai WHT]     skipping - no category found")
                continue

            print(f"[Thai WHT]   category.account_head (asset): {category.get('account_head')}")

            # Thai WHT: use liability account if set, otherwise fall back to asset account
            liability_account = None
            if self.doc.company:
                twc_accounts = _get_twc_accounts_for_company(
                    category.name, self.doc.company
                )
                liability_account = twc_accounts.get("liability_account")
                print(f"[Thai WHT]   liability_account from TWC: {liability_account}")

            account = liability_account or category.account_head
            print(f"[Thai WHT]   final account used: {account}")

            account_amount_map[account] += entry.withholding_amount
            print(f"[Thai WHT]   account_amount_map[{account}] += {entry.withholding_amount} => {account_amount_map[account]}")

        print(f"[Thai WHT] _calculate_account_wise_amount returning: {dict(account_amount_map)}")
        return account_amount_map

    def update_tax_rows(self):
        """Override to call apply_taxes() instead of calculate_taxes_and_totals()."""
        print(f"[Thai WHT] update_tax_rows called")
        print(f"[Thai WHT] doc.taxes count: {len(self.doc.taxes)}")
        print(f"[Thai WHT] doc.tax_withholding_entries count: {len(self.doc.tax_withholding_entries)}")

        account_amount_map = self._calculate_account_wise_amount()
        print(f"[Thai WHT] account_amount_map: {dict(account_amount_map)}")

        category_withholding_map = self._get_category_withholding_map()
        print(f"[Thai WHT] category_withholding_map: {category_withholding_map}")

        existing_taxes = {
            row.account_head: row for row in self.doc.taxes if row.is_tax_withholding_account
        }
        print(f"[Thai WHT] existing_taxes accounts: {list(existing_taxes.keys())}")

        precision = self.doc.precision("tax_amount", "taxes")
        conversion_rate = self.get_conversion_rate()
        print(f"[Thai WHT] precision={precision}, conversion_rate={conversion_rate}")

        add_deduct_tax = "Deduct"

        if self.party_type == "Customer":
            add_deduct_tax = "Add"

        for account_head, base_amount in account_amount_map.items():
            tax_amount = flt(base_amount / conversion_rate, precision)
            print(f"[Thai WHT] account={account_head}, base_amount={base_amount}, tax_amount={tax_amount}")
            if not tax_amount:
                continue

            # Update existing tax row or create new one
            if existing_tax := existing_taxes.get(account_head):
                print(f"[Thai WHT] Updating existing tax row for {account_head}")
                existing_tax.tax_amount = tax_amount
                existing_tax.dont_recompute_tax = 1
                tax_row = existing_tax
                for_update = True
            else:
                print(f"[Thai WHT] Creating new tax row for {account_head}")
                tax_row = self._create_tax_row(account_head, tax_amount)
                for_update = False

            tax_row.add_deduct_tax = add_deduct_tax
            # Set item-wise tax breakup for this tax row
            self._set_item_wise_tax_for_tds(
                tax_row, account_head, category_withholding_map, for_update=for_update
            )

        self._remove_zero_tax_rows()
        # Manually recalculate total_taxes_and_charges from WHT rows
        # without calling apply_taxes() which resets all tax_amounts to 0
        total_taxes = sum(
            flt(t.tax_amount) for t in self.doc.taxes if t.get("is_tax_withholding_account")
        )
        print(f"[Thai WHT] total_taxes calculated: {total_taxes}")
        self.doc.total_taxes_and_charges = flt(total_taxes, self.doc.precision("total_taxes_and_charges"))
        self.doc.base_total_taxes_and_charges = flt(total_taxes, self.doc.precision("base_total_taxes_and_charges"))
        print(f"[Thai WHT] final doc.total_taxes_and_charges: {self.doc.total_taxes_and_charges}")


def _get_twc_accounts_for_company(twc_name, company):
    """
    Get the TWC accounts row for the given company, returning both
    asset account (account) and liability account (pd_custom_wht_liability_account).
    """
    print(f"[Thai WHT] _get_twc_accounts_for_company called: twc_name={twc_name}, company={company}")
    if not twc_name or not company:
        return {}

    try:
        twc = frappe.get_cached_doc("Tax Withholding Category", twc_name)
        print(f"[Thai WHT]   TWC fetched: {twc.name}, accounts rows: {len(twc.accounts)}")
        for row in twc.accounts:
            print(f"[Thai WHT]     TWC account row: company={row.company}, account={row.account}, liability={row.get('pd_custom_wht_liability_account')}")
            if row.company == company:
                result = {
                    "account": row.account,
                    "liability_account": row.get("pd_custom_wht_liability_account"),
                }
                print(f"[Thai WHT]   match found: {result}")
                return result
    except Exception as e:
        print(f"[Thai WHT]   exception: {e}")

    return {}


def patch_payment_tax_withholding(doc, method):
    """
    Monkey-patch PaymentTaxWithholding to use ThaiPaymentTaxWithholding.
    Called in before_validate to ensure Payment Entry uses the liability account.
    """
    import erpnext.accounts.doctype.payment_entry.payment_entry as pe_module

    print(f"[PATCH] patch_payment_tax_withholding called for {doc.doctype} {doc.name}")
    print(f"[PATCH] doc.tax_withholding_category = {doc.tax_withholding_category}")
    print(f"[PATCH] doc.company = {doc.company}")
    print(f"[PATCH] doc.payment_type = {doc.payment_type}")
    print(f"[PATCH] doc.references count = {len(doc.references) if doc.references else 0}")
    print(f"[PATCH] doc.taxes count = {len(doc.taxes) if doc.taxes else 0}")

    # Replace the class reference so PaymentEntry.validate() instantiates our class
    old_class = pe_module.PaymentTaxWithholding
    pe_module.PaymentTaxWithholding = ThaiPaymentTaxWithholding
    print(f"[PATCH] Replaced {old_class} with {ThaiPaymentTaxWithholding}")


@frappe.whitelist()
def get_tax_withholding_group(tax_withholding_category):
    """
    Get Form Type (TH) from Thai WHT Income Type based on Tax Withholding Category.
    Returns the form_type_th value (e.g. 'ภงด.3' or 'ภงด.53') to populate tax_withholding_group.
    """
    if not tax_withholding_category:
        return None

    try:
        # Find Thai WHT Income Type where tax_withholding_category matches
        twi = frappe.db.get_value(
            "Thai WHT Income Type",
            {"tax_withholding_category": tax_withholding_category, "is_active": 1},
            "form_type_th",
            as_dict=True
        )
        if twi and twi.form_type_th:
            return twi.form_type_th
    except Exception:
        pass

    return None
