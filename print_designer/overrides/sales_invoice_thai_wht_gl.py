# Copyright (c) 2026, Print Designer
# For license information, please see license.txt

"""
Override Sales Invoice GL posting for Thai WHT Compliance.

When charge_type = "Thai Tax Compliance", the tax amount should:
- POST AS DEBIT (reduce receivable) instead of credit
- This correctly represents WHT as a deduction from the invoice total

Usage:
    This module patches SalesInvoice.make_tax_gl_entries to handle Thai WHT.
    Registered in hooks.py under doc_events for Sales Invoice.
"""

import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


def patch_sales_invoice_make_tax_gl_entries():
    """
    Monkey-patch SalesInvoice.make_tax_gl_entries to handle Thai WHT.
    
    Thai WHT (charge_type = "Thai Tax Compliance") should post as DEBIT
    to reduce the customer receivable, not as CREDIT which adds to tax liability.
    """
    from erpnext.accounts.utils import get_account_currency
    from frappe.utils import flt
    
    original_method = SalesInvoice.make_tax_gl_entries
    
    def thai_wht_make_tax_gl_entries(self, gl_entries):
        """Enhanced make_tax_gl_entries with Thai WHT support."""
        frappe.logger().debug({
            "event": "thai_wht_gl_make_tax_entries_start",
            "doctype": self.doctype,
            "docname": self.name,
            "existing_gl_entries": len(gl_entries),
        })
        
        # Call original for non-Thai-WHT taxes
        non_wht_taxes = [t for t in self.get("taxes") if t.charge_type != "Thai Tax Compliance"]
        wht_taxes = [t for t in self.get("taxes") if t.charge_type == "Thai Tax Compliance"]
        
        frappe.logger().debug({
            "event": "thai_wht_tax_breakdown",
            "non_wht_taxes": len(non_wht_taxes),
            "wht_taxes": len(wht_taxes),
        })
        
        # Temporarily filter to non-WHT taxes for original method
        if non_wht_taxes:
            original_taxes = list(self.get("taxes"))
            self._taxes = self.get("taxes")
            
            # Patch self.get to return filtered taxes
            def filtered_get(key):
                if key == "taxes":
                    return non_wht_taxes
                return getattr(self, key, None)
            
            # Use lambda to avoid attribute issues
            self.get = lambda key: non_wht_taxes if key == "taxes" else getattr(self, key, None)
            original_method(self, gl_entries)
            self.get = lambda key: getattr(self, key, None)
        
        # Handle Thai WHT taxes (post as DEBIT)
        for tax in self.get("taxes"):
            if tax.charge_type != "Thai Tax Compliance":
                continue
            
            frappe.logger().debug({
                "event": "thai_wht_creating_gl_entry",
                "tax_account": tax.account_head,
                "tax_amount": tax.tax_amount_after_discount_amount,
                "base_tax_amount": tax.base_tax_amount_after_discount_amount,
            })
            
            if not flt(tax.base_tax_amount_after_discount_amount):
                continue
            
            account_currency = get_account_currency(tax.account_head)
            
            # Thai WHT tax amounts are stored as negative (from JS)
            # Use abs() to get positive values for GL posting
            base_amount = abs(flt(tax.base_tax_amount_after_discount_amount))
            amount = abs(flt(tax.tax_amount_after_discount_amount))
            base_amount_after_discount = abs(flt(tax.base_tax_amount_after_discount_amount))
            
            gl_entry = {
                "account": tax.account_head,
                "against": self.customer,
                "debit": flt(base_amount, tax.precision("tax_amount_after_discount_amount")),
                "debit_in_account_currency": (
                    flt(base_amount_after_discount, tax.precision("base_tax_amount_after_discount_amount"))
                    if account_currency == self.company_currency
                    else flt(amount, tax.precision("tax_amount_after_discount_amount"))
                ),
                "debit_in_transaction_currency": flt(
                    amount, tax.precision("tax_amount_after_discount_amount")
                ),
                "cost_center": tax.cost_center,
                "remarks": _("Thai WHT: {0}").format(tax.custom_original_charge_type or "WHT"),
            }
            
            gl_entries.append(
                self.get_gl_dict(gl_entry, account_currency, item=tax)
            )
    
    # Replace the method
    SalesInvoice.make_tax_gl_entries = thai_wht_make_tax_gl_entries


def execute():
    """Called by hooks.py on after_migrate."""
    patch_sales_invoice_make_tax_gl_entries()
    frappe.msgprint(
        msg=_("Thai WHT GL Override installed: 'Thai Tax Compliance' posts as debit"),
        title=_("Thai Tax Override"),
        indicator="blue"
    )
