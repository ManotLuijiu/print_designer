# Copyright (c) 2026, Print Designer
# For license information, please see license.txt

"""
ERPNext TDS Disabler for Thai WHT Compliance

Disables ERPNext's default TDS (Tax Deducted at Source) behavior
for companies using Thai WHT Compliance.

ERPNext's TDS creates SEPARATE GL entries for withholding tax,
which conflicts with Thai accounting logic where WHT is part of the invoice.

When pd_custom_disable_erpnext_tds is ON in Company settings:
- apply_tds flag is forced to 0
- No separate TDS GL entries are created
- Thai WHT Compliance fields handle the withholding instead
"""

import frappe


def disable_tds_for_thai_wht(doc, method):
    """
    Disable ERPNext TDS for companies using Thai WHT Compliance.
    
    Called on: Purchase Invoice validate (on Save)
    
    Logic:
    - Check if Company has pd_custom_disable_erpnext_tds = 1
    - If yes, force apply_tds = 0 regardless of supplier settings
    - Show message to user that TDS is disabled
    """
    if doc.doctype != "Purchase Invoice":
        return
    
    # Get Company's TDS disable setting
    try:
        disable_tds = frappe.get_value(
            "Company", 
            doc.company, 
            "pd_custom_disable_erpnext_tds"
        )
    except Exception:
        # Field might not exist yet - gracefully skip
        return
    
    if not disable_tds:
        return  # Company doesn't use Thai WHT - let ERPNext handle normally
    
    # Check if apply_tds was auto-set by ERPNext
    if doc.apply_tds:
        doc.apply_tds = 0
        frappe.msgprint(
            msg="⚠️ ERPNext TDS has been disabled for this Company. "
                "Please use the Thai WHT Compliance fields instead.",
            title="TDS Disabled",
            indicator="blue"
        )


def block_tds_gl_entries(doc, method):
    """
    Ensure no separate TDS GL entries are created for Thai WHT transactions.
    
    Called on: Purchase Invoice on_submit
    
    Safety check - verify apply_tds is 0 before GL entries are made.
    This is a belt-and-suspenders check in case ERPNext's logic tries to run.
    """
    if doc.doctype != "Purchase Invoice":
        return
    
    try:
        disable_tds = frappe.get_value(
            "Company", 
            doc.company, 
            "pd_custom_disable_erpnext_tds"
        )
    except Exception:
        return
    
    if not disable_tds:
        return
    
    # Double-check: ensure apply_tds is 0 before submission
    if doc.apply_tds:
        doc.apply_tds = 0
        frappe.msgprint(
            msg="⚠️ TDS flag was reset before submission. "
                "Thai WHT Compliance is being used instead of ERPNext TDS.",
            title="TDS Override",
            indicator="blue"
        )


@frappe.whitelist()
def get_tds_status_for_company(company):
    """API to check TDS status for a company"""
    try:
        disable_tds = frappe.get_value(
            "Company", 
            company, 
            "pd_custom_disable_erpnext_tds"
        )
        return {
            "company": company,
            "tds_disabled": bool(disable_tds),
            "message": "ERPNext TDS is disabled - using Thai WHT Compliance" if disable_tds else "ERPNext TDS is enabled"
        }
    except Exception as e:
        return {
            "company": company,
            "tds_disabled": False,
            "message": f"Error checking TDS status: {str(e)}"
        }