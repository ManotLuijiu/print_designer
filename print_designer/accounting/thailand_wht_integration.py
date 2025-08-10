"""
Thailand Withholding Tax Accounting Integration

Handles the accounting entries for Thailand withholding tax:
Debit Withholding Tax Assets (3%)
Debit Cash or Bank (97%)
     Credit Account Receivable (100%)
"""

import frappe
from frappe import _
from frappe.utils import flt


def process_payment_entry_wht(doc, method=None):
    """
    Process withholding tax for Payment Entry
    Called via doc_events hook on Payment Entry submission
    """

    # Only process for receive payments with WHT enabled
    if doc.payment_type != "Receive" or not doc.get("apply_wht"):
        return

    # Only for companies with Thailand service business enabled
    company_wht_enabled = frappe.db.get_value(
        "Company", doc.company, "thailand_service_business"
    )
    if not company_wht_enabled:
        return

    try:
        # Calculate and update WHT amounts
        _calculate_wht_amounts(doc)

        # Create additional accounting entries for WHT
        _create_wht_accounting_entries(doc)

        # Update payment amount to reflect net amount
        _update_payment_amounts(doc)

        frappe.msgprint(
            _("Thailand withholding tax applied successfully. WHT Amount: {0}").format(
                frappe.format_value(doc.wht_amount, {"fieldtype": "Currency"})
            )
        )

    except Exception as e:
        frappe.throw(_("Error processing Thailand withholding tax: {0}").format(str(e)))


def _calculate_wht_amounts(doc):
    """Calculate withholding tax amounts based on payment references"""

    if not doc.wht_rate:
        doc.wht_rate = 3.0  # Default 3% for Thailand services

    # Calculate total amount subject to WHT
    total_wht_base = 0

    for ref in doc.references:
        if ref.reference_doctype == "Sales Invoice":
            # Check if the invoice is subject to WHT
            invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
            if invoice.get("subject_to_wht"):
                total_wht_base += flt(ref.allocated_amount)

    # Calculate WHT amount
    doc.wht_amount = flt((total_wht_base * flt(doc.wht_rate)) / 100, 2)

    # Calculate net payment amount
    doc.net_payment_amount = flt(doc.paid_amount) - flt(doc.wht_amount)

    # Set WHT account if not already set
    if not doc.wht_account:
        doc.wht_account = frappe.db.get_value(
            "Company", doc.company, "default_wht_account"
        )


def _create_wht_accounting_entries(doc):
    """Create additional accounting entries for withholding tax"""

    if not doc.wht_amount or not doc.wht_account:
        return

    # Create a Journal Entry for the withholding tax
    journal_entry = frappe.new_doc("Journal Entry")
    journal_entry.voucher_type = "Journal Entry"
    journal_entry.company = doc.company
    journal_entry.posting_date = doc.posting_date
    journal_entry.user_remark = _("Withholding Tax for Payment Entry {0}").format(
        doc.name
    )
    journal_entry.reference_type = "Payment Entry"
    journal_entry.reference_name = doc.name

    # Debit: Withholding Tax Assets
    journal_entry.append(
        "accounts",
        {
            "account": doc.wht_account,
            "debit_in_account_currency": doc.wht_amount,
            "credit_in_account_currency": 0,
            "party_type": doc.party_type,
            "party": doc.party,
            "reference_type": "Payment Entry",
            "reference_name": doc.name,
        },
    )

    # Credit: Reduce the receivable by WHT amount
    # Find the receivable account from the payment entry
    receivable_account = None
    for ref in doc.references:
        if ref.reference_doctype == "Sales Invoice":
            receivable_account = frappe.db.get_value(
                "Sales Invoice", ref.reference_name, "debit_to"
            )
            break

    if receivable_account:
        journal_entry.append(
            "accounts",
            {
                "account": receivable_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": doc.wht_amount,
                "party_type": doc.party_type,
                "party": doc.party,
                "reference_type": "Payment Entry",
                "reference_name": doc.name,
            },
        )

    # Save and submit the journal entry
    journal_entry.flags.ignore_permissions = True
    journal_entry.save()
    journal_entry.submit()

    # Link the journal entry to payment entry
    doc.add_comment(
        "Comment",
        _("Withholding Tax Journal Entry created: {0}").format(journal_entry.name),
    )


def _update_payment_amounts(doc):
    """Update payment entry amounts to reflect net payment after WHT"""

    if not doc.wht_amount:
        return

    # Update the paid amount to net amount (this affects the cash/bank account)
    original_paid_amount = doc.paid_amount
    doc.paid_amount = doc.net_payment_amount

    # Update received amount if different
    if doc.received_amount == original_paid_amount:
        doc.received_amount = doc.net_payment_amount

    # Add a comment explaining the adjustment
    doc.add_comment(
        "Comment",
        _("Payment adjusted for Thailand WHT: Original {0}, WHT {1}, Net {2}").format(
            frappe.format_value(original_paid_amount, {"fieldtype": "Currency"}),
            frappe.format_value(doc.wht_amount, {"fieldtype": "Currency"}),
            frappe.format_value(doc.net_payment_amount, {"fieldtype": "Currency"}),
        ),
    )


def validate_payment_entry_wht(doc, method=None):
    """Validate WHT fields before saving Payment Entry"""

    if not doc.get("apply_wht"):
        return

    # Validate WHT account is set
    if not doc.wht_account:
        frappe.throw(_("Please select a Withholding Tax Account when applying WHT"))

    # Validate WHT account is valid
    if not frappe.db.exists("Account", doc.wht_account):
        frappe.throw(_("Invalid Withholding Tax Account: {0}").format(doc.wht_account))

    # Validate WHT rate
    if not doc.wht_rate or doc.wht_rate <= 0:
        frappe.throw(_("Invalid WHT Rate. Please enter a positive percentage"))

    # Validate that there are references subject to WHT
    has_wht_references = False
    for ref in doc.references:
        if ref.reference_doctype == "Sales Invoice":
            invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
            if invoice.get("subject_to_wht"):
                has_wht_references = True
                break

    if not has_wht_references:
        frappe.msgprint(
            _(
                "Warning: No sales invoices in this payment are marked as subject to withholding tax"
            )
        )


def update_invoice_wht_status(doc, method=None):
    """Update related invoices with WHT payment information"""

    if not doc.get("apply_wht") or not doc.wht_amount:
        return

    for ref in doc.references:
        if ref.reference_doctype == "Sales Invoice":
            invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
            if invoice.get("subject_to_wht"):
                # Add comment to invoice about WHT payment
                invoice.add_comment(
                    "Comment",
                    _("Withholding Tax applied in Payment {0}: {1} ({2}%)").format(
                        doc.name,
                        frappe.format_value(doc.wht_amount, {"fieldtype": "Currency"}),
                        doc.wht_rate,
                    ),
                )


# Utility functions for client scripts
@frappe.whitelist()
def calculate_estimated_wht(base_amount, wht_rate=None, company=None):
    """Calculate estimated WHT amount for sales documents"""
    try:
        # Debug logging
        print(f"DEBUG: Raw inputs - base_amount: {base_amount} (type: {type(base_amount)}), wht_rate: {wht_rate}, company: {company}")
        
        base_amount = flt(base_amount)
        print(f"DEBUG: Converted base_amount: {base_amount}")

        # If no rate provided, get from company settings
        if not wht_rate and company:
            company_doc = frappe.get_cached_doc("Company", company)
            wht_rate = company_doc.get("default_wht_rate") or 3.0
            print(f"DEBUG: Got company WHT rate: {wht_rate}")

        wht_rate = flt(wht_rate) if wht_rate else 3.0
        print(f"DEBUG: Final WHT rate: {wht_rate}")

        if base_amount <= 0:
            print("DEBUG: Base amount is 0 or negative, returning 0")
            return 0

        wht_amount = (base_amount * wht_rate) / 100
        result = flt(wht_amount, 2)
        print(f"DEBUG: Calculated WHT amount: {result}")
        return result

    except Exception as e:
        print(f"ERROR: {str(e)}")
        frappe.log_error(f"Error calculating WHT: {str(e)}")
        return 0


@frappe.whitelist()
def get_company_wht_rate(company):
    """Get the default WHT rate from company settings"""
    try:
        if not company:
            return 3.0

        company_doc = frappe.get_cached_doc("Company", company)
        return flt(company_doc.get("default_wht_rate")) or 3.0

    except Exception as e:
        frappe.log_error(f"Error getting company WHT rate: {str(e)}")
        return 3.0


@frappe.whitelist()
def calculate_net_total_after_wht(base_amount, company=None, vat_rate=7.0):
    """Calculate net total: base_amount + VAT - WHT"""
    try:
        base_amount = flt(base_amount)
        vat_rate = flt(vat_rate) if vat_rate else 7.0
        
        print(f"DEBUG: Net total calculation - base_amount: {base_amount}, vat_rate: {vat_rate}, company: {company}")
        
        if base_amount <= 0:
            return 0
        
        # Get WHT rate from company settings
        wht_rate = 3.0  # default
        if company:
            company_doc = frappe.get_cached_doc("Company", company)
            wht_rate = flt(company_doc.get("default_wht_rate")) or 3.0
        
        print(f"DEBUG: Using WHT rate: {wht_rate}%")
        
        # Calculate components
        vat_amount = (base_amount * vat_rate) / 100
        wht_amount = (base_amount * wht_rate) / 100
        
        # Net total = base + VAT - WHT
        net_total = base_amount + vat_amount - wht_amount
        
        result = flt(net_total, 2)
        print(f"DEBUG: base: {base_amount}, VAT: {vat_amount}, WHT: {wht_amount}, net: {result}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        frappe.log_error(f"Error calculating net total after WHT: {str(e)}")
        return 0


@frappe.whitelist()
def get_default_wht_account(company):
    """Get default WHT account for a company"""
    try:
        return frappe.db.get_value("Company", company, "default_wht_account")
    except:
        return None


@frappe.whitelist()
def check_invoice_wht_status(reference_type, reference_name):
    """Check if a sales invoice is subject to WHT"""
    try:
        if reference_type == "Sales Invoice":
            return frappe.db.get_value(
                "Sales Invoice", reference_name, "subject_to_wht"
            )
        return False
    except:
        return False
