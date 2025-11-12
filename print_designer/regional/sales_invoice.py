"""
Regional GL Entries for Sales Invoice - Thai Tax Compliance

This module handles VAT account selection for Sales Invoice based on VAT Treatment field.

Key Concept:
- Sales Taxes and Charges Template ALWAYS has a VAT account (required field)
- Default template VAT account = Company's default_output_vat_account
- User intent is expressed via 'vat_treatment' field on Sales Invoice
- Regional GL entries OVERRIDE the template's VAT account based on VAT Treatment value

VAT Treatment Logic:
- "VAT Undue" → Use Company's default_output_vat_undue_account
- "Standard VAT" → Use Company's default_output_vat_account
"""

import frappe
from frappe import _
from frappe.utils import flt


def make_regional_gl_entries(gl_entries, doc):
    """
    Add/modify regional GL entries for Sales Invoice Thai tax compliance.

    This function overrides VAT account selection based on VAT Treatment field.

    Args:
        gl_entries: List of GL entry dicts to be modified
        doc: Sales Invoice document

    Returns:
        Modified gl_entries list
    """
    # Only process Sales Invoice documents
    if doc.doctype != "Sales Invoice":
        return gl_entries

    # Check if VAT Treatment field is set
    vat_treatment = getattr(doc, "vat_treatment", None)
    if not vat_treatment:
        # No VAT Treatment specified, use template's default behavior
        return gl_entries

    # Get Company document to fetch default VAT accounts
    company_doc = None
    if doc.company:
        try:
            company_doc = frappe.get_doc("Company", doc.company)
        except frappe.DoesNotExistError:
            frappe.log_error(
                f"Company '{doc.company}' not found for Sales Invoice {doc.name}",
                "Regional GL Entries - Sales Invoice",
            )
            return gl_entries

    if not company_doc:
        return gl_entries

    # Fetch Company default VAT accounts
    output_vat_undue_account = getattr(company_doc, "default_output_vat_undue_account", None)
    output_vat_account = getattr(company_doc, "default_output_vat_account", None)

    # Determine which VAT account to use based on VAT Treatment
    target_vat_account = None

    if "VAT Undue" in vat_treatment or "Undue" in vat_treatment:
        # VAT not yet occurred (services, payment not received)
        # Use VAT Undue account
        target_vat_account = output_vat_undue_account
        frappe.logger().debug(
            f"[Sales Invoice {doc.name}] VAT Treatment: {vat_treatment} → Using VAT Undue account: {target_vat_account}"
        )
    elif "Standard VAT" in vat_treatment or "Standard" in vat_treatment:
        # VAT point occurred (goods, immediate VAT)
        # Use standard VAT account
        target_vat_account = output_vat_account
        frappe.logger().debug(
            f"[Sales Invoice {doc.name}] VAT Treatment: {vat_treatment} → Using Standard VAT account: {target_vat_account}"
        )

    # If no target VAT account determined, return unchanged GL entries
    if not target_vat_account:
        frappe.logger().warning(
            f"[Sales Invoice {doc.name}] Could not determine target VAT account for VAT Treatment: {vat_treatment}"
        )
        return gl_entries

    # Find and replace VAT account in GL entries
    # VAT GL entries typically have:
    # - Credit side (for sales)
    # - Account type = "Tax" or account name contains "VAT" or "Output Tax"
    vat_entries_modified = 0

    for gl_entry in gl_entries:
        account = gl_entry.get("account", "")
        credit_amount = flt(gl_entry.get("credit", 0))

        # Identify VAT entries by:
        # 1. Credit side (output VAT for sales)
        # 2. Account name contains VAT/Output/Tax keywords
        is_vat_entry = credit_amount > 0 and (
            "VAT" in account.upper()
            or "OUTPUT TAX" in account.upper()
            or "ภาษีขาย" in account
            or "OUTPUT VAT" in account.upper()
        )

        if is_vat_entry:
            original_account = gl_entry["account"]
            gl_entry["account"] = target_vat_account
            vat_entries_modified += 1

            frappe.logger().info(
                f"[Sales Invoice {doc.name}] Replaced VAT account: {original_account} → {target_vat_account} "
                f"(Amount: {credit_amount})"
            )

    if vat_entries_modified > 0:
        frappe.logger().info(
            f"[Sales Invoice {doc.name}] Modified {vat_entries_modified} VAT GL entries "
            f"based on VAT Treatment: {vat_treatment}"
        )
    else:
        frappe.logger().warning(
            f"[Sales Invoice {doc.name}] No VAT GL entries found to modify. "
            f"VAT Treatment: {vat_treatment}, Target account: {target_vat_account}"
        )

    return gl_entries
