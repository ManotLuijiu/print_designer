from datetime import date
from typing import Any, cast

import frappe
from frappe import _
from frappe.utils import flt, getdate

from print_designer.custom.document_permission import (
    require_doctype_permission,
    require_document_read,
    require_document_write,
)
from print_designer.custom.wht_certificate_creator import (
    build_certificate_values,
    build_income_items,
    create_certificate,
    get_entity_type,
    get_wht_rows,
    resolve_certificate_income_type,
)


def _fallback_income_type(purchase_invoice, payment_entry_doc):
    """The values of the certificate that the site cannot know by itself.

    The line of the certificate, the line of its rows, the form of the tax
    and the classification are the values of the canonical mapping of Print
    Designer, which reads the kind of the payee; see
    `print_designer.custom.wht_canonical_mapping`.  The fallback carries only
    the values that come from the transaction: the description of the items
    of the purchase invoice and the rate of the payment entry.
    """
    return {
        "rate": flt(getattr(payment_entry_doc, "pd_custom_withholding_tax_pct_details", 0)),
        "description": _get_income_description(purchase_invoice),
    }


def _create_the_certificate(payment_entry_doc, purchase_invoice, purchase_invoice_name):
    """The certificate of the withholding tax of a payment entry.

    The values of the certificate are the values of the income type of the
    site, the `Thai WHT Income Type`, which works together with the
    `Tax Withholding Category` of ERPNext; see
    `print_designer.custom.wht_canonical_mapping`.
    """
    fallback = _fallback_income_type(purchase_invoice, payment_entry_doc)
    entity_type = get_entity_type(payment_entry_doc)

    # The rows of the withholding tax are the rows of the payment entry.
    rows = get_wht_rows(payment_entry_doc)

    items = build_income_items(payment_entry_doc, rows, entity_type, fallback)
    values = build_certificate_values(
        payment_entry_doc,
        items,
        entity_type,
        remarks=(
            f"Auto-generated from Payment Entry {payment_entry_doc.name} "
            f"for Purchase Invoice {purchase_invoice_name}"
        ),
        fallback=fallback,
    )
    values["purchase_invoice"] = purchase_invoice_name

    if purchase_invoice.tax_id:
        values["supplier_tax_id"] = purchase_invoice.tax_id

    total_payment = flt(getattr(payment_entry_doc, "pd_custom_total_payment_amount", 0))
    if total_payment == 0:
        total_payment = flt(values["tax_base_amount"]) + flt(
            purchase_invoice.total_taxes_and_charges or 0
        )
    values["total_payment_amount"] = total_payment

    return create_certificate(payment_entry_doc, values)


def create_wht_certificate_from_payment_entry(payment_entry_doc):
    """
    Create Withholding Tax Certificate automatically when Payment Entry is created
    from Purchase Invoice with WHT amount
    """
    print(f"DEBUG wht_certificate_generator: Starting for Payment Entry {payment_entry_doc.name}")
    print(
        f"DEBUG: Document properties - name: {payment_entry_doc.name}, payment_type: {payment_entry_doc.payment_type}"
    )
    print(
        f"DEBUG: Document state - docstatus: {payment_entry_doc.docstatus}, is_new: {payment_entry_doc.is_new()}"
    )

    # Only process Payment Entry documents where user enabled WHT
    apply_wht = getattr(payment_entry_doc, "pd_custom_subject_to_wht", 0)
    print(f"DEBUG: pd_custom_subject_to_wht = {apply_wht} (type: {type(apply_wht)})")

    if not apply_wht:
        print("DEBUG: Skipping - WHT not enabled by user")
        raise frappe.ValidationError(
            "WHT Certificate creation not enabled. Please check 'Subject to Withholding Tax' checkbox."
        )

    # Check if WHT amount exists
    wht_amount = flt(getattr(payment_entry_doc, "pd_custom_withholding_tax_amount_details", 0))
    print(
        f"DEBUG: pd_custom_withholding_tax_amount_details = {wht_amount} (type: {type(wht_amount)})"
    )

    if wht_amount <= 0:
        print(f"DEBUG: Skipping - WHT amount is {wht_amount}")
        raise frappe.ValidationError(
            f"Invalid WHT amount: {wht_amount}. WHT amount must be greater than 0."
        )

    # Skip if certificate already exists
    existing_cert = frappe.db.exists(
        "Withholding Tax Certificate", {"payment_entry": payment_entry_doc.name}
    )
    print(f"DEBUG: Existing certificate check: {existing_cert}")

    if existing_cert:
        print(f"DEBUG: Skipping - Certificate already exists: {existing_cert}")
        raise frappe.ValidationError(f"WHT Certificate already exists: {existing_cert}")

    # Get Purchase Invoice details for certificate
    purchase_invoice_name = None
    print(f"DEBUG: Checking {len(payment_entry_doc.references)} references")
    for ref in payment_entry_doc.references:
        print(f"DEBUG: Reference - DocType: {ref.reference_doctype}, Name: {ref.reference_name}")
        if ref.reference_doctype == "Purchase Invoice":
            purchase_invoice_name = ref.reference_name
            print(f"DEBUG: Found Purchase Invoice: {purchase_invoice_name}")
            break

    if not purchase_invoice_name:
        print("DEBUG: Skipping - No Purchase Invoice reference found")
        return

    print(f"DEBUG: Getting Purchase Invoice doc: {purchase_invoice_name}")
    purchase_invoice = cast(Any, frappe.get_doc("Purchase Invoice", purchase_invoice_name))

    # Create WHT Certificate
    try:
        print("DEBUG: Creating new WHT Certificate document")
        wht_cert = _create_the_certificate(
            payment_entry_doc, purchase_invoice, purchase_invoice_name
        )
        print(f"DEBUG: WHT Certificate saved successfully: {wht_cert.name}")

        # The link of the payment entry and its certificate is kept by the
        # creator of the certificate.
        # Update Payment Entry with certificate NUMBER for Pay scenario
        # This makes the certificate number visible in the PE UI (_details fields)
        print(f"DEBUG: Setting pd_custom_wht_number_details = {wht_cert.certificate_number}")
        if payment_entry_doc.meta.has_field("pd_custom_wht_number_details"):
            frappe.db.set_value(
                "Payment Entry",
                payment_entry_doc.name,
                "pd_custom_wht_number_details",
                wht_cert.certificate_number,
            )

        # The certificate is submitted by the creator of the certificate
        print(f"DEBUG: Certificate {wht_cert.name} is submitted: {wht_cert.docstatus}")

        # Commit all changes to database before auto-refresh
        frappe.db.commit()  # Ensure everything is committed to database
        print("DEBUG: All changes committed to database")

        # Verify the link was created successfully
        linked_cert = frappe.db.get_value(
            "Payment Entry", payment_entry_doc.name, "pd_custom_wht_certificate"
        )
        print(
            f"DEBUG: Verification - Payment Entry {payment_entry_doc.name} now linked to certificate: {linked_cert}"
        )

        if linked_cert != wht_cert.name:
            frappe.log_error(
                message=f"WARNING: WHT Certificate link verification failed. Expected: {wht_cert.name}, Got: {linked_cert}",
                title="WHT Certificate Link Warning",
            )
            print("WARNING: Certificate link verification failed!")
        else:
            print("SUCCESS: Certificate link verified successfully")

        # Auto-refresh PND53 Form using background job for production reliability
        print(f"DEBUG: Scheduling background job for auto-refresh of certificate {wht_cert.name}")
        frappe.enqueue(
            method="print_designer.custom.wht_certificate_generator.auto_refresh_pnd_form_job",
            queue="short",
            timeout=120,
            job_name=f"auto_refresh_pnd53_{wht_cert.name}",
            wht_cert_name=wht_cert.name,
            wht_cert_data={
                "tax_year": wht_cert.tax_year,
                "tax_month": wht_cert.tax_month,
                "pnd_form_type": wht_cert.pnd_form_type,
            },
            is_async=True,
        )

        frappe.msgprint(
            _("Withholding Tax Certificate {0} created successfully").format(wht_cert.name),
            alert=True,
            indicator="green",
        )

    except Exception as e:
        # Log full error details
        frappe.log_error(
            message=f"Error creating WHT Certificate for Payment Entry {payment_entry_doc.name}: {str(e)}",
            title="WHT Certificate Error",
        )
        # Show concise message to user
        frappe.throw(_("Failed to create WHT Certificate. Check error log for details."))


# Removed _get_thai_month_name function - using numeric months (1-12) for simplicity


def _get_thai_month_display(month_num):
    """Get Thai month display format for preview"""
    tax_month_options = {
        1: "01 - มกราคม (January)",
        2: "02 - กุมภาพันธ์ (February)",
        3: "03 - มีนาคม (March)",
        4: "04 - เมษายน (April)",
        5: "05 - พฤษภาคม (May)",
        6: "06 - มิถุนายน (June)",
        7: "07 - กรกฎาคม (July)",
        8: "08 - สิงหาคม (August)",
        9: "09 - กันยายน (September)",
        10: "10 - ตุลาคม (October)",
        11: "11 - พฤศจิกายน (November)",
        12: "12 - ธันวาคม (December)",
    }
    return tax_month_options.get(month_num, f"{month_num:02d}")


def _get_income_description(purchase_invoice):
    """Get income description from Purchase Invoice"""
    descriptions = []
    for item in purchase_invoice.items:
        if item.description and item.description not in descriptions:
            descriptions.append(item.description)

    if descriptions:
        return ", ".join(descriptions[:3])  # Limit to first 3 descriptions
    else:
        return "ค่าสินค้าและบริการ"


@frappe.whitelist(methods=["POST"])
def create_wht_certificate_manually(payment_entry_name):
    """Manual creation of WHT Certificate from Payment Entry

    The caller must be allowed to read the payment entry and to create the
    certificate.  The refusal is made before the payment entry is loaded, so
    that a caller without the right learns nothing about it.
    """
    require_document_read("Payment Entry", payment_entry_name)
    require_doctype_permission("Withholding Tax Certificate", "create")

    payment_entry_doc = cast(Any, frappe.get_doc("Payment Entry", payment_entry_name))
    create_wht_certificate_from_payment_entry(payment_entry_doc)
    return {"status": "success", "message": "WHT Certificate created successfully"}


@frappe.whitelist()
def get_wht_certificate_preview(payment_entry_name):
    """Preview WHT Certificate data before creation

    The caller must be allowed to read the payment entry, because the
    preview shows the data of the payment entry and of its purchase invoice.
    """
    require_document_read("Payment Entry", payment_entry_name)

    payment_entry_doc = cast(Any, frappe.get_doc("Payment Entry", payment_entry_name))

    # Check if eligible for WHT certificate
    apply_wht = getattr(payment_entry_doc, "pd_custom_subject_to_wht", 0)
    if not apply_wht:
        return {"eligible": False, "message": "WHT not enabled"}

    wht_amount = flt(getattr(payment_entry_doc, "pd_custom_withholding_tax_amount_details", 0))
    if wht_amount <= 0:
        return {"eligible": False, "message": "No WHT amount found"}

    # Get Purchase Invoice for preview
    purchase_invoice_name = None
    for ref in payment_entry_doc.references:
        if ref.reference_doctype == "Purchase Invoice":
            purchase_invoice_name = ref.reference_name
            break

    if not purchase_invoice_name:
        return {"eligible": False, "message": "No Purchase Invoice reference found"}

    purchase_invoice = cast(Any, frappe.get_doc("Purchase Invoice", purchase_invoice_name))
    posting_date = cast(date, getdate(payment_entry_doc.posting_date))
    buddhist_year = posting_date.year + 543

    # The preview shows the values of the certificate that the creation
    # makes; both read the same canonical mapping.
    resolved = resolve_certificate_income_type(
        payment_entry_doc,
        get_entity_type(payment_entry_doc),
        _fallback_income_type(purchase_invoice, payment_entry_doc),
    )

    preview_data = {
        "eligible": True,
        "certificate_number": f"WHTC-{str(buddhist_year)[-2:]}{posting_date.month:02d}-XXXXX",
        "certificate_date": payment_entry_doc.posting_date,
        "tax_year": f"{buddhist_year}",
        "tax_month": _get_thai_month_display(posting_date.month),
        "supplier": payment_entry_doc.party_name,
        "tax_base_amount": flt(getattr(payment_entry_doc, "pd_custom_tax_base_amount", 0)),
        "wht_rate": flt(getattr(payment_entry_doc, "pd_custom_withholding_tax_pct_details", 0)),
        "wht_amount": wht_amount,
        "income_type": resolved.get("income_type") or "",
        "pnd_form_type": resolved.get("pnd_form"),
    }

    return preview_data


def _auto_refresh_pnd_form(wht_cert):
    """
    Automatically refresh PND53 Form when a new WHT certificate is created
    to ensure the form reflects the new certificate without manual intervention
    """
    try:
        # Only handle PND53 Form type certificates
        if wht_cert.pnd_form_type != "PND53 Form":
            print(
                f"DEBUG: Skipping auto-refresh - Certificate is for {wht_cert.pnd_form_type}, not PND53 Form"
            )
            return

        print(f"DEBUG: Auto-refresh starting for WHT Certificate {wht_cert.name}")
        print(
            f"DEBUG: Certificate details - tax_year: {wht_cert.tax_year}, tax_month: {wht_cert.tax_month}"
        )

        # Extract year and month from certificate
        tax_year = wht_cert.tax_year
        tax_month = wht_cert.tax_month

        # Extract month number from tax_month (format: "09 - กันยายน (September)")
        month_num = None
        if tax_month and " - " in tax_month:
            month_num = int(tax_month.split(" - ")[0])
        else:
            print(f"DEBUG: Could not extract month number from tax_month: {tax_month}")
            return

        print(f"DEBUG: Looking for PND53 Form with year={tax_year}, month={month_num}")

        # Verify this certificate actually exists in database before refresh
        cert_exists = frappe.db.exists(
            "Withholding Tax Certificate",
            {
                "name": wht_cert.name,
                "docstatus": 1,  # Submitted
                "status": "Issued",
            },
        )
        print(f"DEBUG: Certificate {wht_cert.name} exists and submitted: {cert_exists}")

        if not cert_exists:
            print(
                f"DEBUG: Certificate {wht_cert.name} not found in database as submitted - skipping refresh"
            )
            return

        # Find existing PND53 Form for this tax period
        existing_pnd_forms = frappe.get_all(
            "PND53 Form",
            filters={
                "tax_period_year": tax_year,
                "tax_period_month": month_num,
                "docstatus": ["!=", 2],  # Not cancelled
            },
            fields=["name", "tax_period_year", "tax_period_month"],
        )

        print(
            f"DEBUG: Found {len(existing_pnd_forms)} existing PND53 Forms for year {tax_year}, month {month_num}"
        )

        # Refresh each matching PND53 Form
        for pnd_form in existing_pnd_forms:
            try:
                print(
                    f"DEBUG: Refreshing PND53 Form {pnd_form.name} (year: {pnd_form.tax_period_year}, month: {pnd_form.tax_period_month})"
                )
                pnd_doc = cast(Any, frappe.get_doc("PND53 Form", pnd_form.name))

                # Count certificates before refresh
                before_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(
                    f"DEBUG: PND Form {pnd_form.name} had {before_count} certificates before refresh"
                )

                pnd_doc.refresh_certificates()

                # Count certificates after refresh
                after_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(
                    f"DEBUG: PND Form {pnd_form.name} now has {after_count} certificates after refresh"
                )

                # Check if our certificate is now included
                cert_names = [
                    item.withholding_tax_cert for item in pnd_doc.items if item.withholding_tax_cert
                ]
                is_included = wht_cert.name in cert_names
                print(f"DEBUG: Certificate {wht_cert.name} is included in PND Form: {is_included}")

                if is_included:
                    print(
                        f"DEBUG: SUCCESS - Certificate {wht_cert.name} successfully added to PND53 Form {pnd_form.name}"
                    )
                else:
                    print(
                        f"DEBUG: WARNING - Certificate {wht_cert.name} not found in refreshed PND53 Form {pnd_form.name}"
                    )
                    print(f"DEBUG: PND Form certificates: {cert_names}")

            except Exception as refresh_error:
                print(f"DEBUG: Error refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}")
                frappe.log_error(
                    message=f"Error auto-refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}",
                    title="PND53 Auto-Refresh Error",
                )

        if not existing_pnd_forms:
            print(
                f"DEBUG: No PND53 Forms found for year {tax_year}, month {month_num} - auto-refresh not needed"
            )

    except Exception as e:
        print(f"DEBUG: Error in auto-refresh function: {str(e)}")
        import traceback

        print(f"DEBUG: Auto-refresh traceback: {traceback.format_exc()}")
        frappe.log_error(
            message=f"Error in PND53 auto-refresh for WHT Certificate {wht_cert.name}: {str(e)}",
            title="PND53 Auto-Refresh Error",
        )


@frappe.whitelist(methods=["POST"])
def auto_refresh_pnd_form_job(wht_cert_name, wht_cert_data):
    """
    Production-grade background job for auto-refreshing PND53 Forms

    This function runs as a background job to ensure:
    1. Database consistency - certificate is fully committed
    2. Non-blocking - doesn't slow down user interface
    3. Retry capability - can be retried if it fails
    4. Proper logging - full audit trail for accounting system

    The caller must be allowed to write the certificate.  The check is made
    before the job runs as the Administrator, so that the right of the
    caller is the right that counts.

    Args:
        wht_cert_name (str): Name of the WHT Certificate
        wht_cert_data (dict): Certificate data for refresh logic
    """
    require_document_write("Withholding Tax Certificate", wht_cert_name)

    try:
        frappe.set_user("Administrator")  # Ensure proper permissions

        print(f"DEBUG: Background job starting for WHT Certificate {wht_cert_name}")
        print(
            f"DEBUG: Job data - tax_year: {wht_cert_data.get('tax_year')}, tax_month: {wht_cert_data.get('tax_month')}"
        )

        # Verify certificate exists and is properly submitted
        wht_cert = cast(Any, frappe.get_doc("Withholding Tax Certificate", wht_cert_name))
        if not wht_cert:
            raise frappe.DoesNotExistError(f"WHT Certificate {wht_cert_name} not found")

        if wht_cert.docstatus != 1:
            print(
                f"DEBUG: Certificate {wht_cert_name} not submitted (docstatus: {wht_cert.docstatus}), skipping refresh"
            )
            return

        print(
            f"DEBUG: Certificate {wht_cert_name} verified - docstatus: {wht_cert.docstatus}, status: {wht_cert.status}"
        )

        # Only handle PND53 Form type certificates
        if wht_cert_data.get("pnd_form_type") != "PND53 Form":
            print(
                f"DEBUG: Skipping job - Certificate is for {wht_cert_data.get('pnd_form_type')}, not PND53 Form"
            )
            return

        # Extract tax period information
        tax_year = wht_cert_data.get("tax_year")
        tax_month = wht_cert_data.get("tax_month")

        # Extract month number from tax_month (format: "09 - กันยายน (September)")
        month_num = None
        if tax_month and " - " in tax_month:
            month_num = int(tax_month.split(" - ")[0])
        else:
            print(f"DEBUG: Could not extract month number from tax_month: {tax_month}")
            return

        print(f"DEBUG: Looking for PND53 Forms with year={tax_year}, month={month_num}")

        # Find existing PND53 Forms for this tax period
        existing_pnd_forms = frappe.get_all(
            "PND53 Form",
            filters={
                "tax_period_year": tax_year,
                "tax_period_month": month_num,
                "docstatus": ["!=", 2],  # Not cancelled
            },
            fields=["name", "tax_period_year", "tax_period_month"],
        )

        print(
            f"DEBUG: Found {len(existing_pnd_forms)} existing PND53 Forms for year {tax_year}, month {month_num}"
        )

        if not existing_pnd_forms:
            print(
                f"DEBUG: No PND53 Forms found for year {tax_year}, month {month_num} - job completed"
            )
            return

        # Refresh each matching PND53 Form
        refreshed_forms = []
        for pnd_form in existing_pnd_forms:
            try:
                print(f"DEBUG: Processing PND53 Form {pnd_form.name}")
                pnd_doc = cast(Any, frappe.get_doc("PND53 Form", pnd_form.name))

                # Count certificates before refresh
                before_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(
                    f"DEBUG: PND Form {pnd_form.name} had {before_count} certificates before refresh"
                )

                # Perform the refresh using the same method as manual refresh
                pnd_doc.populate_wht_certificates()
                pnd_doc.calculate_totals()
                pnd_doc.save(ignore_permissions=True)

                # Count certificates after refresh
                after_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(
                    f"DEBUG: PND Form {pnd_form.name} now has {after_count} certificates after refresh"
                )

                # Check if our certificate is now included
                cert_names = [
                    item.withholding_tax_cert for item in pnd_doc.items if item.withholding_tax_cert
                ]
                is_included = wht_cert_name in cert_names
                print(f"DEBUG: Certificate {wht_cert_name} is included in PND Form: {is_included}")

                if is_included:
                    print(
                        f"DEBUG: SUCCESS - Certificate {wht_cert_name} successfully added to PND53 Form {pnd_form.name}"
                    )
                    refreshed_forms.append(pnd_form.name)
                else:
                    print(
                        f"DEBUG: WARNING - Certificate {wht_cert_name} not found in refreshed PND53 Form {pnd_form.name}"
                    )
                    print(f"DEBUG: PND Form certificates: {cert_names}")

            except Exception as refresh_error:
                print(f"DEBUG: Error refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}")
                frappe.log_error(
                    message=f"Background job error refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}",
                    title="PND53 Background Job Error",
                )

        # Final commit to ensure all changes are saved
        frappe.db.commit()

        print("DEBUG: Background job completed successfully")
        print(f"DEBUG: Refreshed {len(refreshed_forms)} PND53 Forms: {refreshed_forms}")

        # Log successful completion for audit trail
        frappe.logger().info(
            f"Auto-refresh job completed for WHT Certificate {wht_cert_name}, refreshed PND Forms: {refreshed_forms}"
        )

    except Exception as e:
        print(f"DEBUG: Background job error: {str(e)}")
        import traceback

        print(f"DEBUG: Background job traceback: {traceback.format_exc()}")

        frappe.log_error(
            message=f"Background job error for WHT Certificate {wht_cert_name}: {str(e)}\n\nTraceback:\n{traceback.format_exc()}",
            title="PND53 Background Job Error",
        )
        raise  # Re-raise to mark job as failed for retry
