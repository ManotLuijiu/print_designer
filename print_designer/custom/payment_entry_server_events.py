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
    Submit the linked WHT Certificate if it exists (Pay scenario).
    Create Receive WHT Register entry if it exists (Receive scenario).
    """
    # Handle Pay scenario - submit WHT Certificate
    if doc.payment_type == "Pay":
        # Check if there's a linked WHT Certificate
        wht_certificate_name = getattr(doc, 'pd_custom_wht_certificate_details', None)
        if wht_certificate_name:
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
        # Create Input VAT conversion GL entries
        _create_input_vat_conversion_gl_entries(doc)
        # Also create Thai Purchase VAT record for reconciliation
        _create_thai_purchase_vat_from_pe_simple(doc)
    # Handle Receive scenario - create Receive WHT Register entry
    elif doc.payment_type == "Receive":
        _create_receive_wht_register_entry(doc)


def _create_thai_purchase_vat_from_pe_simple(doc):
    """
    Create Thai Purchase VAT record directly from Payment Entry.
    Called after Input VAT GL entries are created on PE submit.
    No dependency on Input VAT Undue record.
    Also updates PE with VAT amount and link to Thai Purchase VAT.
    """
    # Only for Pay payment type
    if doc.payment_type != "Pay":
        return

    # Check if this PE has VAT Undue treatment
    vat_treatment = getattr(doc, 'pd_custom_vat_treatment_details', None)
    if not vat_treatment or vat_treatment != "VAT Undue":
        return

    # Check if Thai Purchase VAT already exists for this PE
    existing = frappe.db.exists("Thai Purchase VAT", {"payment_entry": doc.name})
    if existing:
        return

    try:
        from frappe.utils import getdate
        from frappe import _

        thai_vat = frappe.new_doc("Thai Purchase VAT")

        # Company details
        thai_vat.purchase_for_company = doc.company
        company_doc = frappe.get_doc("Company", doc.company)
        thai_vat.purchase_for_branch = getattr(company_doc, 'branch', '') or '00000'

        # Get Purchase Invoice details from references
        purchase_invoice = ""
        for ref in doc.references:
            if ref.reference_doctype == "Purchase Invoice":
                purchase_invoice = ref.reference_name
                break
        thai_vat.purchase_invoice = purchase_invoice

        # Get supplier info from PE
        if doc.party_type == "Supplier":
            thai_vat.supplier = doc.party
            supplier_doc = frappe.get_doc("Supplier", doc.party)
            thai_vat.supplier_name = getattr(supplier_doc, 'supplier_name', doc.party)
            thai_vat.supplier_tax_id = getattr(supplier_doc, 'tax_id', '') or ""
            thai_vat.supplier_branch = getattr(supplier_doc, 'pd_custom_branch_code', '') or '00000'

        thai_vat.posting_date = doc.posting_date
        thai_vat.bill_date = doc.posting_date

        # Tax Invoice details
        thai_vat.bill_no = getattr(doc, 'pd_custom_tax_invoice_number', '') or doc.name
        thai_vat.tax_invoice_number = getattr(doc, 'pd_custom_tax_invoice_number', '')
        thai_vat.tax_invoice_date = getattr(doc, 'pd_custom_tax_invoice_date', '') or doc.posting_date
        thai_vat.tax_base_amount = flt(getattr(doc, 'pd_custom_tax_base_amount', 0))
        thai_vat.bill_series = getattr(doc, 'pd_custom_bill_series', '') or ""

        # Payment Entry link
        thai_vat.payment_entry = doc.name

        # VAT period from posting date
        posting_date = getdate(doc.posting_date)
        thai_vat.vat_month = str(posting_date.month)
        thai_vat.vat_year = str(posting_date.year)

        # Amounts - calculate VAT from tax base
        tax_base = flt(getattr(doc, 'pd_custom_tax_base_amount', 0))
        vat_amount = tax_base * 0.07 if tax_base > 0 else 0
        thai_vat.base_amount = tax_base
        thai_vat.vat_amount = vat_amount
        thai_vat.total_amount = tax_base + vat_amount

        thai_vat.flags.ignore_permissions = True
        thai_vat.insert()
        frappe.db.commit()

        # Update PE with VAT amount and Thai Purchase VAT reference
        _update_pe_vat_fields(doc, thai_vat)

        frappe.log_error(
            message=f"SUCCESS: Created Thai Purchase VAT {thai_vat.name} for {doc.name}",
            title="Thai Purchase VAT Created"
        )

        frappe.msgprint(
            _("Thai Purchase VAT record created: {0}").format(thai_vat.name),
            alert=True,
            indicator="green"
        )

    except Exception as e:
        import traceback
        frappe.log_error(
            message=f"Error creating Thai Purchase VAT for {doc.name}: {str(e)}\n{traceback.format_exc()}",
            title="Thai Purchase VAT Creation Error"
        )
        frappe.msgprint(
            _("Payment Entry submitted, but Thai Purchase VAT record creation failed: {0}").format(str(e)),
            alert=True,
            indicator="orange"
        )


def _update_pe_vat_fields(doc, thai_vat_record):
    """
    Update Payment Entry with VAT amount and Thai Purchase VAT reference.
    Called after Thai Purchase VAT record is created.
    """
    try:
        # Calculate VAT amount from tax_base * 7%
        tax_base = flt(getattr(doc, 'pd_custom_tax_base_amount', 0))
        vat_amount = tax_base * 0.07 if tax_base > 0 else 0

        # Update PE in database
        frappe.db.set_value(
            "Payment Entry",
            doc.name,
            {
                "pd_custom_vat_amount": vat_amount,
                "pd_custom_input_vat_ref": thai_vat_record.name
            }
        )
        frappe.db.commit()

        # Update in-memory doc for immediate UI reflection
        doc.pd_custom_vat_amount = vat_amount
        doc.pd_custom_input_vat_ref = thai_vat_record.name

    except Exception as e:
        frappe.log_error(
            message=f"Error updating PE VAT fields for {doc.name}: {str(e)}",
            title="PE VAT Fields Update Error"
        )



def _create_receive_wht_register_entry(doc):
    """
    Create Receive WHT Register entry from Payment Entry (Receive) values.
    Only creates if WHT certificate number is provided.
    """
    # Check if WHT certificate number is provided
    wht_cert_no = getattr(doc, 'pd_custom_wht_certificate_no', None)
    if not wht_cert_no:
        return  # No WHT certificate, nothing to create
    # Check if entry already exists (avoid duplicates)
    existing_register = getattr(doc, 'pd_custom_receive_wht_register', None)
    if existing_register:
        return  # Already linked to an existing register
    try:
        from print_designer.print_designer.doctype.receive_wht_register.receive_wht_register import create_receive_wht_register_entry
        result = create_receive_wht_register_entry(doc.name)
        if result.get("status") == "created":
            # Update PE with the link
            frappe.db.set_value(
                "Payment Entry",
                doc.name,
                "pd_custom_receive_wht_register",
                result.get("name")
            )
            frappe.msgprint(
                _("Receive WHT Register {0} has been created").format(result.get("name")),
                alert=True,
                indicator="green"
            )
    except Exception as e:
        frappe.log_error(
            message=f"Error creating Receive WHT Register for PE {doc.name}: {str(e)}",
            title="Receive WHT Register Creation Error"
        )
        frappe.msgprint(
            _("Payment Entry submitted, but Receive WHT Register creation failed: {0}").format(str(e)),
            alert=True,
            indicator="orange"
        )

def on_cancel(doc, method):
    """
    Called when Payment Entry is cancelled.
    Cancel the linked WHT Certificate and delete Input VAT GL entries if they exist.
    """
    if doc.payment_type != "Pay":
        return
    
    # C.1 Cancel linked WHT Certificate and clear the link
    wht_certificate_name = getattr(doc, 'pd_custom_wht_certificate_details', None)
    if wht_certificate_name:
        try:
            wht_cert = frappe.get_doc("Withholding Tax Certificate", wht_certificate_name)
            if wht_cert.docstatus == 1:
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

    # C.2 Delete Input VAT GL entries created from this PE
    _delete_input_vat_gl_entries(doc)
    # C.3 Delete/Cancel Thai Purchase VAT record linked to this PE
    _delete_thai_purchase_vat_record(doc)

    # C.4 Clear VAT-related fields in PE (vat_amount and input_vat_ref)
    _clear_pe_vat_fields(doc)


def on_update_after_submit(doc, method):
    """
    After amended PE is saved (but before submit).
    Clear any stale WHTC references from pd_custom_wht_certificate_details.
    """
    if doc.payment_type != "Pay":
        return
    
    # Get current WHTC ref
    wht_cert_ref = getattr(doc, 'pd_custom_wht_certificate_details', None)
    if wht_cert_ref:
        # Check if the referenced WHTC is cancelled
        wht_status = frappe.db.get_value("Withholding Tax Certificate", wht_cert_ref, "docstatus")
        if wht_status == 2:  # Cancelled
            # Clear the stale reference
            frappe.db.sql("""
                UPDATE `tabPayment Entry` 
                SET pd_custom_wht_certificate_details = NULL 
                WHERE name = %s
            """, (doc.name,))
            frappe.db.commit()
            frappe.msgprint(
                _("Cleared cancelled WHT Certificate reference from {0}").format(doc.name),
                alert=True,
                indicator="orange"
            )


def _delete_input_vat_gl_entries(doc):
    """
    Delete GL entries for Input VAT conversion when Payment Entry is cancelled.
    """
    try:
        # Get accounts from Company
        input_vat_account = frappe.get_value("Company", doc.company, "default_input_vat_account")
        input_vat_undue_account = frappe.get_value("Company", doc.company, "default_input_vat_undue_account")
        
        if not input_vat_account or not input_vat_undue_account:
            return
        
        # Find and delete GL entries for Input VAT accounts linked to this PE
        frappe.db.sql("""
            DELETE FROM `tabGL Entry` 
            WHERE voucher_no = %s 
            AND voucher_type = 'Payment Entry'
            AND account IN (%s, %s)
        """, (doc.name, input_vat_account, input_vat_undue_account))
        
        frappe.db.commit()
        
        frappe.msgprint(
            _("Input VAT GL entries deleted for {0}").format(doc.name),
            alert=True,
            indicator="orange"
        )
    except Exception as e:
        frappe.log_error(
            message=f"Error deleting Input VAT GL entries for {doc.name}: {str(e)}",
            title="Input VAT GL Entry Deletion Error"
        )


def _delete_thai_purchase_vat_record(doc):
    """
    Delete Thai Purchase VAT record linked to this Payment Entry on cancellation.
    Reverses the record created during PE submission.
    """
    try:
        # Find Thai Purchase VAT records linked to this PE
        thai_vat_records = frappe.db.get_all(
            "Thai Purchase VAT",
            filters={"payment_entry": doc.name},
            pluck="name"
        )

        if not thai_vat_records:
            return

        deleted_count = 0
        for record_name in thai_vat_records:
            try:
                # Try to delete the record directly
                frappe.db.delete("Thai Purchase VAT", {"name": record_name})
                deleted_count += 1
                frappe.log_error(
                    message=f"Deleted Thai Purchase VAT: {record_name} (linked to cancelled PE: {doc.name})",
                    title="Thai Purchase VAT Cancelled"
                )
            except Exception as del_e:
                frappe.log_error(
                    message=f"Error deleting Thai Purchase VAT {record_name}: {str(del_e)}",
                    title="Thai Purchase VAT Deletion Error"
                )

        if deleted_count > 0:
            frappe.db.commit()
            frappe.msgprint(
                _("Thai Purchase VAT record(s) deleted for cancelled Payment Entry {0}").format(doc.name),
                alert=True,
                indicator="orange"
            )

    except Exception as e:
        frappe.log_error(
            message=f"Error processing Thai Purchase VAT deletion for {doc.name}: {str(e)}",
            title="Thai Purchase VAT Cancellation Error"
        )


def _clear_pe_vat_fields(doc):
    """
    Clear VAT-related fields in Payment Entry on cancellation.
    Clears: pd_custom_vat_amount, pd_custom_input_vat_ref
    """
    try:
        frappe.db.set_value(
            "Payment Entry",
            doc.name,
            {
                "pd_custom_vat_amount": 0,
                "pd_custom_input_vat_ref": None
            }
        )
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(
            message=f"Error clearing PE VAT fields for {doc.name}: {str(e)}",
            title="PE VAT Fields Clear Error"
        )


def validate(doc, method):
    """
    Called before Payment Entry is saved.
    1. Auto-fill pd_custom_tax_base_amount (amount before VAT)
    """
    # Only process for Pay payment type with Thai tax
    # Only process for Pay payment type with Thai tax
    if doc.payment_type != "Pay":
        return
    # Step 1: Auto-fill pd_custom_tax_base_amount
    _auto_fill_tax_base_amount(doc)
    # Step 2: Validate mandatory Thai tax fields
    _validate_mandatory_tax_invoice_fields(doc)
    # Step 3: Validate Thai tax fields consistency
    _validate_thai_tax_consistency(doc)
def _auto_fill_tax_base_amount(doc):
    """
    Auto-fill pd_custom_tax_base_amount (amount before VAT).
    Tax base = base_net_total or (total_allocated_amount - VAT amount)
    """
    # Check if already set
    current_tax_base = flt(getattr(doc, 'pd_custom_tax_base_amount', 0))
    if current_tax_base > 0:
        return  # Already has value, don't override
    # Calculate tax base amount
    # Method 1: Use base_net_total from PI references
    total_allocated = flt(getattr(doc, 'total_allocated_amount', 0))
    # Method 2: Try to get from references (sum of PI base_net_total)
    tax_base = 0
    if hasattr(doc, 'references') and doc.references:
        for ref in doc.references:
            if hasattr(ref, 'ref_docname') and ref.ref_docname:
                try:
                    pi = frappe.get_doc("Purchase Invoice", ref.ref_docname)
                    if hasattr(pi, 'net_total') and pi.net_total:
                        tax_base += flt(pi.net_total)
                except:
                    pass
    # Fallback: total_allocated - VAT (if references not available)
    if tax_base <= 0 and total_allocated > 0:
        # Get VAT amount from taxes
        vat_amount = 0
        if hasattr(doc, 'taxes') and doc.taxes:
            for tax in doc.taxes:
                if hasattr(tax, 'rate') and flt(tax.rate) == 7:  # VAT 7%
                    vat_amount = flt(tax.amount)
        if vat_amount > 0:
            tax_base = total_allocated - vat_amount
    # Set the value if calculated
    if tax_base > 0 and hasattr(doc, 'pd_custom_tax_base_amount'):
        doc.pd_custom_tax_base_amount = tax_base
def _validate_mandatory_tax_invoice_fields(doc):
    """
    Validate mandatory Thai tax invoice fields.
    Required when: payment_type == 'Pay' AND has VAT amount
    """
    # Check if this PE has VAT (non-zero taxes)
    has_vat = False
    if hasattr(doc, 'taxes') and doc.taxes:
        for tax in doc.taxes:
            if flt(getattr(tax, 'rate', 0)) == 7 and flt(getattr(tax, 'amount', 0)) > 0:
                has_vat = True
                break
    # Only validate if has VAT
    if not has_vat:
        return
    # Get field values
    tax_invoice_number = getattr(doc, 'pd_custom_tax_invoice_number', None)
    tax_invoice_date = getattr(doc, 'pd_custom_tax_invoice_date', None)
    # Build error list
    missing_fields = []
    if not tax_invoice_number:
        missing_fields.append("Tax Invoice Number (pd_custom_tax_invoice_number)")
    if not tax_invoice_date:
        missing_fields.append("Tax Invoice Date (pd_custom_tax_invoice_date)")
    # Raise validation error if any field is missing
    if missing_fields:
        frappe.throw(
            _("Missing mandatory Thai Tax Invoice fields: {0}. Please fill in before saving.").format(
                ", ".join(missing_fields)
            ),
            title=_("Thai Tax Invoice Validation")
        )

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

def _create_input_vat_conversion_gl_entries(doc):
    """
    Create GL entries for Input VAT conversion when Payment Entry is submitted.
    Creates 2 GL entries (Debit Input VAT, Credit Input VAT Undue) linked to same PE.
    Only runs for Pay payment type with VAT Undue treatment.
    """
    # Log entry for debugging
    frappe.log_error(
        message=f"DEBUG _create_input_vat: PE={doc.name}, type={doc.payment_type}",
        title="Input VAT Debug"
    )
    
    # Only process for Pay payment type
    if doc.payment_type != "Pay":
        return
    
    # Check if this PE has VAT Undue treatment
    vat_treatment = getattr(doc, 'pd_custom_vat_treatment_details', None)
    if not vat_treatment or vat_treatment != "VAT Undue":
        return
    
    # Check if tax invoice details exist
    tax_invoice_number = getattr(doc, 'pd_custom_tax_invoice_number', None)
    tax_base_amount = flt(getattr(doc, 'pd_custom_tax_base_amount', 0))
    
    frappe.log_error(
        message=f"DEBUG _create_input_vat: PE={doc.name}, vat_treatment={vat_treatment}, tax_inv={tax_invoice_number}, tax_base={tax_base_amount}",
        title="Input VAT Debug 2"
    )
    
    if not tax_invoice_number or tax_base_amount <= 0:
        return
    
    # Calculate VAT amount (7%)
    vat_amount = tax_base_amount * 0.07
    
    # Get accounts from Company
    input_vat_account = frappe.get_value("Company", doc.company, "default_input_vat_account")
    input_vat_undue_account = frappe.get_value("Company", doc.company, "default_input_vat_undue_account")
    
    frappe.log_error(
        message=f"DEBUG _create_input_vat: PE={doc.name}, accounts: input_vat={input_vat_account}, undue={input_vat_undue_account}, vat_amount={vat_amount}",
        title="Input VAT Debug 3"
    )
    
    if not input_vat_account or not input_vat_undue_account:
        frappe.msgprint(
            _("Input VAT accounts not configured in Company settings. Skipping Input VAT GL entries."),
            alert=True,
            indicator="orange"
        )
        return
    
    # Check if GL entries already exist for this conversion (prevent duplicates on re-submit)
    existing = frappe.db.exists("GL Entry", {
        "voucher_no": doc.name,
        "voucher_type": "Payment Entry",
        "account": input_vat_account
    })
    if existing:
        return
    
    try:
        # Get cost center from PE or Company default
        cost_center = getattr(doc, 'cost_center', None)
        if not cost_center:
            cost_center = frappe.get_value("Company", doc.company, "cost_center")
        
        # Create GL Entry - Debit to Input VAT account
        gle_debit = frappe.new_doc("GL Entry")
        gle_debit.account = input_vat_account
        gle_debit.debit_in_account_currency = vat_amount
        gle_debit.debit_in_company_currency = vat_amount
        gle_debit.voucher_type = "Payment Entry"
        gle_debit.voucher_subtype = "Pay"
        gle_debit.voucher_no = doc.name
        gle_debit.company = doc.company
        gle_debit.posting_date = doc.posting_date
        gle_debit.party_type = ""
        gle_debit.party = ""
        if cost_center:
            gle_debit.cost_center = cost_center
        gle_debit.flags.ignore_permissions = True
        gle_debit.insert()
        
        # Create GL Entry - Credit to Input VAT Undue account
        gle_credit = frappe.new_doc("GL Entry")
        gle_credit.account = input_vat_undue_account
        gle_credit.credit_in_account_currency = vat_amount
        gle_credit.credit_in_company_currency = vat_amount
        gle_credit.voucher_type = "Payment Entry"
        gle_credit.voucher_subtype = "Pay"
        gle_credit.voucher_no = doc.name
        gle_credit.company = doc.company
        gle_credit.posting_date = doc.posting_date
        gle_credit.party_type = ""
        gle_credit.party = ""
        if cost_center:
            gle_credit.cost_center = cost_center
        gle_credit.flags.ignore_permissions = True
        gle_credit.insert()
        
        frappe.db.commit()
        
        frappe.log_error(
            message=f"SUCCESS: Created Input VAT GL entries for {doc.name}: Debit={input_vat_account} {vat_amount}, Credit={input_vat_undue_account} {vat_amount}",
            title="Input VAT GL Success"
        )
        
        frappe.msgprint(
            _("Input VAT GL entries created: Debit {0} / Credit {1} = ฿{2:,.2f}").format(
                input_vat_account, input_vat_undue_account, vat_amount
            ),
            alert=True,
            indicator="green"
        )
        
    except Exception as e:
        import traceback
        frappe.log_error(
            message=f"Error creating Input VAT GL entries for {doc.name}: {str(e)}\n{traceback.format_exc()}",
            title="Input VAT GL Entry Error"
        )
        frappe.msgprint(
            _("Payment Entry submitted, but Input VAT GL entry creation failed: {0}").format(str(e)),
            alert=True,
            indicator="orange"
        )