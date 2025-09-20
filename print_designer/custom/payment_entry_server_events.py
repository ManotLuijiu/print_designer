#!/usr/bin/env python3
"""
Payment Entry Server Events

Server-side event handlers for Payment Entry DocType to automatically create
Withholding Tax Certificates and handle Thai tax compliance workflows.
"""

import frappe
from frappe import _
from frappe.utils import flt


def after_insert(doc, method):
    """
    Called after Payment Entry is created.
    Automatically create WHT Certificate if applicable.
    """
    print(f"DEBUG after_insert: Payment Entry {doc.name}, Type: {doc.payment_type}")
    frappe.log_error(
        message=f"after_insert called for Payment Entry {doc.name}, Type: {doc.payment_type}",
        title="Payment Entry after_insert Debug"
    )

    # Only process if this Payment Entry was created from Purchase Invoice with WHT
    if doc.payment_type != "Pay":
        print(f"DEBUG: Skipping - Payment type is {doc.payment_type}, not Pay")
        return

    # Check if user enabled WHT certificate generation
    apply_wht = getattr(doc, 'pd_custom_apply_withholding_tax', 0)

    print(f"DEBUG: pd_custom_apply_withholding_tax = {apply_wht}")

    if not apply_wht:
        print("DEBUG: Skipping - WHT not enabled by user")
        return

    print(f"DEBUG: Creating WHT Certificate for Payment Entry {doc.name}")

    # Import the WHT certificate generator
    from print_designer.custom.wht_certificate_generator import create_wht_certificate_from_payment_entry

    try:
        # Create WHT Certificate
        create_wht_certificate_from_payment_entry(doc)
        print(f"DEBUG: WHT Certificate created successfully")

    except Exception as e:
        print(f"DEBUG ERROR: Failed to create WHT Certificate: {str(e)}")
        frappe.log_error(
            message=f"Error in Payment Entry after_insert WHT certificate creation: {str(e)}",
            title="WHT Certificate Auto-Creation Error"
        )
        # Don't prevent Payment Entry creation if certificate creation fails
        frappe.msgprint(
            _("Payment Entry created successfully, but WHT Certificate creation failed: {0}").format(str(e)),
            alert=True,
            indicator="orange"
        )


def on_submit(doc, method):
    """
    Called when Payment Entry is submitted.
    Submit the linked WHT Certificate if it exists.
    """
    if doc.payment_type != "Pay":
        return

    # Check if there's a linked WHT Certificate
    wht_certificate_name = getattr(doc, 'pd_custom_wht_certificate', None)

    if not wht_certificate_name:
        return

    try:
        # Get the WHT Certificate and submit it
        wht_cert = frappe.get_doc("Withholding Tax Certificate", wht_certificate_name)

        if wht_cert.docstatus == 0:  # Only submit if it's in Draft status
            wht_cert.status = "Issued"
            wht_cert.submit()

            frappe.msgprint(
                _("Withholding Tax Certificate {0} has been submitted and issued").format(wht_certificate_name),
                alert=True,
                indicator="green"
            )

    except Exception as e:
        frappe.log_error(
            message=f"Error submitting WHT Certificate {wht_certificate_name}: {str(e)}",
            title="WHT Certificate Submission Error"
        )
        frappe.msgprint(
            _("Payment Entry submitted, but WHT Certificate submission failed: {0}").format(str(e)),
            alert=True,
            indicator="orange"
        )


def on_cancel(doc, method):
    """
    Called when Payment Entry is cancelled.
    Cancel the linked WHT Certificate if it exists.
    """
    if doc.payment_type != "Pay":
        return

    # Check if there's a linked WHT Certificate
    wht_certificate_name = getattr(doc, 'pd_custom_wht_certificate', None)

    if not wht_certificate_name:
        return

    try:
        # Get the WHT Certificate and cancel it
        wht_cert = frappe.get_doc("Withholding Tax Certificate", wht_certificate_name)

        if wht_cert.docstatus == 1:  # Only cancel if it's submitted
            wht_cert.cancel()

            frappe.msgprint(
                _("Withholding Tax Certificate {0} has been cancelled").format(wht_certificate_name),
                alert=True,
                indicator="orange"
            )

    except Exception as e:
        frappe.log_error(
            message=f"Error cancelling WHT Certificate {wht_certificate_name}: {str(e)}",
            title="WHT Certificate Cancellation Error"
        )
        frappe.msgprint(
            _("Payment Entry cancelled, but WHT Certificate cancellation failed: {0}").format(str(e)),
            alert=True,
            indicator="red"
        )


def validate(doc, method):
    """
    Called before Payment Entry is saved.
    Validate Thai tax calculations and ensure consistency.
    """
    if doc.payment_type != "Pay":
        return

    # Validate Thai tax fields consistency
    _validate_thai_tax_consistency(doc)

    # COMMENTED OUT: Set has_thai_taxes flag based on actual tax amounts
    # Field pd_custom_has_thai_taxes is no longer used - visibility now controlled by depends_on conditions
    # _update_has_thai_taxes_flag(doc)


def _validate_thai_tax_consistency(doc):
    """
    Validate that Thai tax calculations are consistent.
    """
    # Get tax amounts
    tax_base_amount = flt(getattr(doc, 'pd_custom_tax_base_amount', 0))
    wht_rate = flt(getattr(doc, 'pd_custom_withholding_tax_rate', 0))
    wht_amount = flt(getattr(doc, 'pd_custom_withholding_tax_amount', 0))

    # If WHT rate and tax base exist, validate calculated WHT amount
    if tax_base_amount > 0 and wht_rate > 0:
        calculated_wht = tax_base_amount * (wht_rate / 100)

        # Allow small rounding differences (within 0.01)
        if abs(calculated_wht - wht_amount) > 0.01:
            frappe.msgprint(
                _("Warning: WHT Amount ({0}) doesn't match calculated amount ({1}) based on Tax Base ({2}) and WHT Rate ({3}%)").format(
                    wht_amount, calculated_wht, tax_base_amount, wht_rate
                ),
                alert=True,
                indicator="orange"
            )


# COMMENTED OUT: Function no longer needed as pd_custom_has_thai_taxes field is removed
# def _update_has_thai_taxes_flag(doc):
#     """
#     Update the has_thai_taxes flag based on actual tax amounts.
#     """
#     wht_amount = flt(getattr(doc, 'pd_custom_withholding_tax_amount', 0))
#     retention_amount = flt(getattr(doc, 'pd_custom_total_retention_amount', 0))

#     has_thai_taxes = bool(wht_amount > 0 or retention_amount > 0)

#     if hasattr(doc, 'pd_custom_has_thai_taxes'):
#         doc.pd_custom_has_thai_taxes = 1 if has_thai_taxes else 0


@frappe.whitelist()
def create_wht_certificate_from_payment_entry(payment_entry_name):
    """
    API endpoint to manually create WHT Certificate from Payment Entry.
    """
    print(f"DEBUG API create_wht_certificate_from_payment_entry: Called with payment_entry_name={payment_entry_name}")

    try:
        payment_entry_doc = frappe.get_doc("Payment Entry", payment_entry_name)

        print(f"DEBUG: Payment Entry loaded - Name: {payment_entry_doc.name}, Type: {payment_entry_doc.payment_type}")
        print(f"DEBUG: Document state - docstatus: {payment_entry_doc.docstatus}, flags: {payment_entry_doc.flags}")
        print(f"DEBUG: Payment Entry is_new: {payment_entry_doc.is_new()}")
        print(f"DEBUG: WHT fields - apply_wht: {getattr(payment_entry_doc, 'pd_custom_apply_withholding_tax', 'NOT_SET')}, wht_amount: {getattr(payment_entry_doc, 'pd_custom_withholding_tax_amount', 'NOT_SET')}")

        # Import and call the certificate generator
        from print_designer.custom.wht_certificate_generator import create_wht_certificate_from_payment_entry
        create_wht_certificate_from_payment_entry(payment_entry_doc)

        print(f"DEBUG: Certificate creation completed successfully")
        return {
            "status": "success",
            "message": _("Withholding Tax Certificate created successfully")
        }

    except Exception as e:
        print(f"DEBUG ERROR: Certificate creation failed: {str(e)}")
        import traceback
        print(f"DEBUG ERROR traceback: {traceback.format_exc()}")

        frappe.log_error(
            message=f"Manual WHT Certificate creation failed for {payment_entry_name}: {str(e)}\n\nTraceback:\n{traceback.format_exc()}",
            title="Manual WHT Certificate Creation Error"
        )

        return {
            "status": "error",
            "message": _("Failed to create WHT Certificate: {0}").format(str(e))
        }


@frappe.whitelist()
def get_wht_certificate_preview(payment_entry_name):
    """
    API endpoint to preview WHT Certificate data before creation.
    """
    try:
        # Import and call the preview function
        from print_designer.custom.wht_certificate_generator import get_wht_certificate_preview
        return get_wht_certificate_preview(payment_entry_name)

    except Exception as e:
        frappe.log_error(
            message=f"WHT Certificate preview failed for {payment_entry_name}: {str(e)}",
            title="WHT Certificate Preview Error"
        )

        return {
            "eligible": False,
            "message": _("Preview failed: {0}").format(str(e))
        }