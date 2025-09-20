import frappe
from frappe import _
from frappe.utils import flt, getdate, add_months
from frappe.model.naming import make_autoname

def create_wht_certificate_from_payment_entry(payment_entry_doc):
    """
    Create Withholding Tax Certificate automatically when Payment Entry is created
    from Purchase Invoice with WHT amount
    """
    print(f"DEBUG wht_certificate_generator: Starting for Payment Entry {payment_entry_doc.name}")
    print(f"DEBUG: Document properties - name: {payment_entry_doc.name}, payment_type: {payment_entry_doc.payment_type}")
    print(f"DEBUG: Document state - docstatus: {payment_entry_doc.docstatus}, is_new: {payment_entry_doc.is_new()}")

    # Only process Payment Entry documents where user enabled WHT
    apply_wht = getattr(payment_entry_doc, 'pd_custom_apply_withholding_tax', 0)
    print(f"DEBUG: pd_custom_apply_withholding_tax = {apply_wht} (type: {type(apply_wht)})")

    if not apply_wht:
        print("DEBUG: Skipping - WHT not enabled by user")
        raise frappe.ValidationError("WHT Certificate creation not enabled. Please check 'Apply Withholding Tax' checkbox.")

    # Check if WHT amount exists
    wht_amount = flt(getattr(payment_entry_doc, 'pd_custom_withholding_tax_amount', 0))
    print(f"DEBUG: pd_custom_withholding_tax_amount = {wht_amount} (type: {type(wht_amount)})")

    if wht_amount <= 0:
        print(f"DEBUG: Skipping - WHT amount is {wht_amount}")
        raise frappe.ValidationError(f"Invalid WHT amount: {wht_amount}. WHT amount must be greater than 0.")

    # Skip if certificate already exists
    existing_cert = frappe.db.exists("Withholding Tax Certificate", {
        "payment_entry": payment_entry_doc.name
    })
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
    purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice_name)

    # Create WHT Certificate
    try:
        print(f"DEBUG: Creating new WHT Certificate document")
        wht_cert = frappe.new_doc("Withholding Tax Certificate")

        # Certificate Information
        print(f"DEBUG: Processing posting date: {payment_entry_doc.posting_date}")
        posting_date = getdate(payment_entry_doc.posting_date)
        buddhist_year = posting_date.year + 543
        buddhist_year_short = str(buddhist_year)[-2:]
        month_num = posting_date.month

        print(f"DEBUG: Date calculations - year: {buddhist_year}, month: {month_num}")

        # Generate certificate number with zero-padded month for consistent naming
        month_padded = str(month_num).zfill(2)
        naming_pattern = f"WHTC-{buddhist_year_short}{month_padded}-.#####"
        print(f"DEBUG: Generating certificate number with pattern: {naming_pattern}")
        wht_cert.certificate_number = make_autoname(naming_pattern)
        wht_cert.certificate_date = payment_entry_doc.posting_date
        wht_cert.tax_year = f"{buddhist_year}"

        # Map month number to the required format for Tax Month field
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
            12: "12 - ธันวาคม (December)"
        }
        wht_cert.tax_month = tax_month_options.get(month_num, "")
        print(f"DEBUG: Setting tax_month to: {wht_cert.tax_month}")

        print(f"DEBUG: Certificate basic info set successfully")

        # Supplier Information
        print(f"DEBUG: Setting supplier information")
        wht_cert.supplier = payment_entry_doc.party
        print(f"DEBUG: Set supplier: {payment_entry_doc.party}")
        wht_cert.supplier_name = payment_entry_doc.party_name
        print(f"DEBUG: Set supplier_name: {payment_entry_doc.party_name}")

        print(f"DEBUG: Checking purchase invoice tax_id")
        if hasattr(purchase_invoice, 'tax_id') and purchase_invoice.tax_id:
            print(f"DEBUG: Setting supplier_tax_id: {purchase_invoice.tax_id}")
            wht_cert.supplier_tax_id = purchase_invoice.tax_id
        else:
            print(f"DEBUG: No tax_id found in purchase invoice")

        # Get supplier address
        print(f"DEBUG: Getting supplier doc: {payment_entry_doc.party}")
        supplier_doc = frappe.get_doc("Supplier", payment_entry_doc.party)
        print(f"DEBUG: Got supplier doc, checking primary address")

        if supplier_doc.supplier_primary_address:
            print(f"DEBUG: Getting address doc: {supplier_doc.supplier_primary_address}")
            address_doc = frappe.get_doc("Address", supplier_doc.supplier_primary_address)
            print(f"DEBUG: Setting supplier address from address_line1: {address_doc.address_line1}")
            wht_cert.supplier_address = address_doc.address_line1
            if address_doc.address_line2:
                print(f"DEBUG: Adding address_line2: {address_doc.address_line2}")
                wht_cert.supplier_address += f", {address_doc.address_line2}"
            if address_doc.city:
                print(f"DEBUG: Adding city: {address_doc.city}")
                wht_cert.supplier_address += f", {address_doc.city}"
            if address_doc.state:
                print(f"DEBUG: Adding state: {address_doc.state}")
                wht_cert.supplier_address += f", {address_doc.state}"
        else:
            print(f"DEBUG: No primary address found for supplier")

        # Payment Information
        print(f"DEBUG: Setting payment information")
        wht_cert.payment_entry = payment_entry_doc.name
        print(f"DEBUG: Set payment_entry: {payment_entry_doc.name}")
        wht_cert.payment_date = payment_entry_doc.posting_date
        print(f"DEBUG: Set payment_date: {payment_entry_doc.posting_date}")
        wht_cert.purchase_invoice = purchase_invoice_name
        print(f"DEBUG: Set purchase_invoice: {purchase_invoice_name}")
        wht_cert.company = payment_entry_doc.company
        print(f"DEBUG: Set company: {payment_entry_doc.company}")

        # WHT Details
        print(f"DEBUG: Setting WHT details")
        print(f"DEBUG: Getting income type from purchase invoice")
        wht_cert.income_type = _get_income_type_from_purchase_invoice(purchase_invoice)
        print(f"DEBUG: Set income_type: {wht_cert.income_type}")

        print(f"DEBUG: Getting income description")
        wht_cert.income_description = _get_income_description(purchase_invoice)
        print(f"DEBUG: Set income_description: {wht_cert.income_description}")

        print(f"DEBUG: Setting WHT rate")
        wht_cert.wht_rate = flt(getattr(payment_entry_doc, 'pd_custom_withholding_tax_rate', 0))
        print(f"DEBUG: Set wht_rate: {wht_cert.wht_rate}")

        print(f"DEBUG: Setting WHT condition")
        wht_cert.wht_condition = "1. หัก ณ ที่จ่าย (Withhold at Source)"
        print(f"DEBUG: Set wht_condition: {wht_cert.wht_condition}")

        # Amount Details
        print(f"DEBUG: Setting amount details")
        wht_cert.tax_base_amount = flt(getattr(payment_entry_doc, 'pd_custom_tax_base_amount', 0))
        print(f"DEBUG: Set tax_base_amount: {wht_cert.tax_base_amount}")
        wht_cert.wht_amount = wht_amount
        print(f"DEBUG: Set wht_amount: {wht_cert.wht_amount}")

        # Calculate other amounts
        print(f"DEBUG: Calculating other amounts")
        total_payment = flt(getattr(payment_entry_doc, 'pd_custom_total_payment_amount', 0))
        print(f"DEBUG: Got total_payment: {total_payment}")
        if total_payment == 0:
            total_payment = wht_cert.tax_base_amount + flt(purchase_invoice.total_taxes_and_charges or 0)

        wht_cert.total_payment_amount = total_payment
        wht_cert.net_payment_amount = total_payment - wht_amount

        # PND Form Type and supplier classification based on supplier type
        pnd_form_type, supplier_classification = _get_pnd_form_and_classification(payment_entry_doc.party)
        wht_cert.pnd_form_type = pnd_form_type
        wht_cert.supplier_type_classification = supplier_classification

        # Set initial status
        print(f"DEBUG: Setting status and remarks")
        wht_cert.status = "Draft"
        print(f"DEBUG: Set status: {wht_cert.status}")

        # Remarks
        wht_cert.remarks = f"Auto-generated from Payment Entry {payment_entry_doc.name} for Purchase Invoice {purchase_invoice_name}"
        print(f"DEBUG: Set remarks: {wht_cert.remarks}")

        # Save and submit the certificate
        print(f"DEBUG: About to save WHT Certificate")
        try:
            wht_cert.insert(ignore_permissions=True)
            print(f"DEBUG: WHT Certificate saved successfully: {wht_cert.name}")
        except Exception as insert_error:
            print(f"DEBUG INSERT ERROR: {str(insert_error)}")
            print(f"DEBUG INSERT ERROR TYPE: {type(insert_error)}")
            import traceback
            print(f"DEBUG INSERT TRACEBACK: {traceback.format_exc()}")
            raise insert_error

        # Create a link back to Payment Entry
        if not hasattr(payment_entry_doc, 'pd_custom_wht_certificate'):
            # Add custom field to Payment Entry if it doesn't exist
            _ensure_wht_certificate_link_field()

        # Update Payment Entry with certificate link
        print(f"DEBUG: Linking WHT Certificate {wht_cert.name} to Payment Entry {payment_entry_doc.name}")
        frappe.db.set_value("Payment Entry", payment_entry_doc.name, "pd_custom_wht_certificate", wht_cert.name)

        # Submit the certificate to finalize it
        print(f"DEBUG: Submitting WHT Certificate {wht_cert.name}")
        wht_cert.submit()

        # Commit all changes to database before auto-refresh
        frappe.db.commit()  # Ensure everything is committed to database
        print(f"DEBUG: All changes committed to database")

        # Verify the link was created successfully
        linked_cert = frappe.db.get_value("Payment Entry", payment_entry_doc.name, "pd_custom_wht_certificate")
        print(f"DEBUG: Verification - Payment Entry {payment_entry_doc.name} now linked to certificate: {linked_cert}")

        if linked_cert != wht_cert.name:
            frappe.log_error(
                message=f"WARNING: WHT Certificate link verification failed. Expected: {wht_cert.name}, Got: {linked_cert}",
                title="WHT Certificate Link Warning"
            )
            print(f"WARNING: Certificate link verification failed!")
        else:
            print(f"SUCCESS: Certificate link verified successfully")

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
                "pnd_form_type": wht_cert.pnd_form_type
            },
            is_async=True
        )

        frappe.msgprint(
            _("Withholding Tax Certificate {0} created successfully").format(wht_cert.name),
            alert=True,
            indicator="green"
        )

    except Exception as e:
        # Log full error details
        frappe.log_error(
            message=f"Error creating WHT Certificate for Payment Entry {payment_entry_doc.name}: {str(e)}",
            title="WHT Certificate Error"
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
        12: "12 - ธันวาคม (December)"
    }
    return tax_month_options.get(month_num, f"{month_num:02d}")


def _get_income_type_from_purchase_invoice(purchase_invoice):
    """Determine income type based on Purchase Invoice items"""
    # Check if there are service items
    has_service = False
    for item in purchase_invoice.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        if item_doc.is_stock_item == 0:  # Service item
            has_service = True
            break

    if has_service:
        return "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service"
    else:
        return "12. อื่นๆ - Others"


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


def _get_pnd_form_and_classification(supplier_name):
    """
    Get PND form type and supplier classification based on supplier type according to Thai Revenue Department rules:
    - Individual/Personal (Staff): PND.1 (ภ.ง.ด.1) - Salary
    - Individual/Personal (Non-staff): PND.3 (ภ.ง.ด.3) - Services/Freelance
    - Company/Juristic Person: PND.53 (ภ.ง.ด.53) - Corporate

    Returns:
        tuple: (pnd_form_doctype_name, supplier_classification)
    """
    try:
        # Get supplier details to determine type
        supplier_doc = frappe.get_doc("Supplier", supplier_name)

        # Check supplier_type field if it exists
        supplier_type = getattr(supplier_doc, 'supplier_type', '')

        # Check if this is an individual or company based on name patterns and supplier type
        supplier_name_lower = supplier_name.lower()

        # Thai company indicators
        company_indicators = [
            'จำกัด', 'บริษัท', 'company', 'ltd', 'limited', 'corp', 'corporation',
            'co.,ltd', 'co. ltd', 'มหาชน', 'public', 'partnership', 'ห้างหุ้นส่วน'
        ]

        # Check if supplier name contains company indicators
        is_company = any(indicator in supplier_name_lower for indicator in company_indicators)

        # Check supplier type
        if supplier_type:
            supplier_type_lower = supplier_type.lower()
            if 'company' in supplier_type_lower or 'corporate' in supplier_type_lower or 'juristic' in supplier_type_lower:
                is_company = True
            elif 'individual' in supplier_type_lower or 'person' in supplier_type_lower:
                is_company = False

        if is_company:
            # Company or Juristic Person - return the DocType name
            return ("PND53 Form", "Company/Juristic Person (PND.53)")
        else:
            # Individual - For now, default to PND.3 (Services)
            # Note: PND.1 is for salary/employee payments, which would need additional logic
            # to determine if this is an employee vs. freelancer/service provider
            return ("PND3 Form", "Individual - Non-staff (PND.3)")

    except Exception as e:
        frappe.log_error(f"Error determining PND form type for supplier {supplier_name}: {str(e)}")
        # Default fallback - return the DocType name
        return ("PND3 Form", "Individual - Non-staff (PND.3)")


def _ensure_wht_certificate_link_field():
    """Ensure WHT Certificate link field exists in Payment Entry"""
    try:
        if not frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "pd_custom_wht_certificate"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Payment Entry"
            custom_field.fieldname = "pd_custom_wht_certificate"
            custom_field.fieldtype = "Link"
            custom_field.options = "Withholding Tax Certificate"
            custom_field.label = "WHT Certificate"
            custom_field.description = "Link to generated Withholding Tax Certificate"
            custom_field.insert_after = "pd_custom_thai_compliance_tab"
            custom_field.depends_on = "eval:doc.pd_custom_has_thai_taxes"
            custom_field.read_only = 1
            custom_field.insert(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(f"Error creating WHT Certificate link field: {str(e)}")


@frappe.whitelist()
def create_wht_certificate_manually(payment_entry_name):
    """Manual creation of WHT Certificate from Payment Entry"""
    payment_entry_doc = frappe.get_doc("Payment Entry", payment_entry_name)
    create_wht_certificate_from_payment_entry(payment_entry_doc)
    return {"status": "success", "message": "WHT Certificate created successfully"}


@frappe.whitelist()
def get_wht_certificate_preview(payment_entry_name):
    """Preview WHT Certificate data before creation"""
    payment_entry_doc = frappe.get_doc("Payment Entry", payment_entry_name)

    # Check if eligible for WHT certificate
    apply_wht = getattr(payment_entry_doc, 'pd_custom_apply_withholding_tax', 0)
    if not apply_wht:
        return {"eligible": False, "message": "WHT not enabled"}

    wht_amount = flt(getattr(payment_entry_doc, 'pd_custom_withholding_tax_amount', 0))
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

    purchase_invoice = frappe.get_doc("Purchase Invoice", purchase_invoice_name)
    posting_date = getdate(payment_entry_doc.posting_date)
    buddhist_year = posting_date.year + 543

    preview_data = {
        "eligible": True,
        "certificate_number": f"WHTC-{str(buddhist_year)[-2:]}{posting_date.month:02d}-XXXXX",
        "certificate_date": payment_entry_doc.posting_date,
        "tax_year": f"{buddhist_year}",
        "tax_month": _get_thai_month_display(posting_date.month),
        "supplier": payment_entry_doc.party_name,
        "tax_base_amount": flt(getattr(payment_entry_doc, 'pd_custom_tax_base_amount', 0)),
        "wht_rate": flt(getattr(payment_entry_doc, 'pd_custom_withholding_tax_rate', 0)),
        "wht_amount": wht_amount,
        "income_type": _get_income_type_from_purchase_invoice(purchase_invoice),
        "pnd_form_type": _get_pnd_form_and_classification(payment_entry_doc.party)[0]  # Get only the PND form type
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
            print(f"DEBUG: Skipping auto-refresh - Certificate is for {wht_cert.pnd_form_type}, not PND53 Form")
            return

        print(f"DEBUG: Auto-refresh starting for WHT Certificate {wht_cert.name}")
        print(f"DEBUG: Certificate details - tax_year: {wht_cert.tax_year}, tax_month: {wht_cert.tax_month}")

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
        cert_exists = frappe.db.exists("Withholding Tax Certificate", {
            "name": wht_cert.name,
            "docstatus": 1,  # Submitted
            "status": "Issued"
        })
        print(f"DEBUG: Certificate {wht_cert.name} exists and submitted: {cert_exists}")

        if not cert_exists:
            print(f"DEBUG: Certificate {wht_cert.name} not found in database as submitted - skipping refresh")
            return

        # Find existing PND53 Form for this tax period
        existing_pnd_forms = frappe.get_all(
            "PND53 Form",
            filters={
                "tax_period_year": tax_year,
                "tax_period_month": month_num,
                "docstatus": ["!=", 2]  # Not cancelled
            },
            fields=["name", "tax_period_year", "tax_period_month"]
        )

        print(f"DEBUG: Found {len(existing_pnd_forms)} existing PND53 Forms for year {tax_year}, month {month_num}")

        # Refresh each matching PND53 Form
        for pnd_form in existing_pnd_forms:
            try:
                print(f"DEBUG: Refreshing PND53 Form {pnd_form.name} (year: {pnd_form.tax_period_year}, month: {pnd_form.tax_period_month})")
                pnd_doc = frappe.get_doc("PND53 Form", pnd_form.name)

                # Count certificates before refresh
                before_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(f"DEBUG: PND Form {pnd_form.name} had {before_count} certificates before refresh")

                pnd_doc.refresh_certificates()

                # Count certificates after refresh
                after_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(f"DEBUG: PND Form {pnd_form.name} now has {after_count} certificates after refresh")

                # Check if our certificate is now included
                cert_names = [item.withholding_tax_cert for item in pnd_doc.items if item.withholding_tax_cert]
                is_included = wht_cert.name in cert_names
                print(f"DEBUG: Certificate {wht_cert.name} is included in PND Form: {is_included}")

                if is_included:
                    print(f"DEBUG: SUCCESS - Certificate {wht_cert.name} successfully added to PND53 Form {pnd_form.name}")
                else:
                    print(f"DEBUG: WARNING - Certificate {wht_cert.name} not found in refreshed PND53 Form {pnd_form.name}")
                    print(f"DEBUG: PND Form certificates: {cert_names}")

            except Exception as refresh_error:
                print(f"DEBUG: Error refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}")
                frappe.log_error(
                    message=f"Error auto-refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}",
                    title="PND53 Auto-Refresh Error"
                )

        if not existing_pnd_forms:
            print(f"DEBUG: No PND53 Forms found for year {tax_year}, month {month_num} - auto-refresh not needed")

    except Exception as e:
        print(f"DEBUG: Error in auto-refresh function: {str(e)}")
        import traceback
        print(f"DEBUG: Auto-refresh traceback: {traceback.format_exc()}")
        frappe.log_error(
            message=f"Error in PND53 auto-refresh for WHT Certificate {wht_cert.name}: {str(e)}",
            title="PND53 Auto-Refresh Error"
        )


@frappe.whitelist()
def auto_refresh_pnd_form_job(wht_cert_name, wht_cert_data):
    """
    Production-grade background job for auto-refreshing PND53 Forms

    This function runs as a background job to ensure:
    1. Database consistency - certificate is fully committed
    2. Non-blocking - doesn't slow down user interface
    3. Retry capability - can be retried if it fails
    4. Proper logging - full audit trail for accounting system

    Args:
        wht_cert_name (str): Name of the WHT Certificate
        wht_cert_data (dict): Certificate data for refresh logic
    """
    try:
        frappe.set_user("Administrator")  # Ensure proper permissions

        print(f"DEBUG: Background job starting for WHT Certificate {wht_cert_name}")
        print(f"DEBUG: Job data - tax_year: {wht_cert_data.get('tax_year')}, tax_month: {wht_cert_data.get('tax_month')}")

        # Verify certificate exists and is properly submitted
        wht_cert = frappe.get_doc("Withholding Tax Certificate", wht_cert_name)
        if not wht_cert:
            raise frappe.DoesNotExistError(f"WHT Certificate {wht_cert_name} not found")

        if wht_cert.docstatus != 1:
            print(f"DEBUG: Certificate {wht_cert_name} not submitted (docstatus: {wht_cert.docstatus}), skipping refresh")
            return

        print(f"DEBUG: Certificate {wht_cert_name} verified - docstatus: {wht_cert.docstatus}, status: {wht_cert.status}")

        # Only handle PND53 Form type certificates
        if wht_cert_data.get('pnd_form_type') != "PND53 Form":
            print(f"DEBUG: Skipping job - Certificate is for {wht_cert_data.get('pnd_form_type')}, not PND53 Form")
            return

        # Extract tax period information
        tax_year = wht_cert_data.get('tax_year')
        tax_month = wht_cert_data.get('tax_month')

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
                "docstatus": ["!=", 2]  # Not cancelled
            },
            fields=["name", "tax_period_year", "tax_period_month"]
        )

        print(f"DEBUG: Found {len(existing_pnd_forms)} existing PND53 Forms for year {tax_year}, month {month_num}")

        if not existing_pnd_forms:
            print(f"DEBUG: No PND53 Forms found for year {tax_year}, month {month_num} - job completed")
            return

        # Refresh each matching PND53 Form
        refreshed_forms = []
        for pnd_form in existing_pnd_forms:
            try:
                print(f"DEBUG: Processing PND53 Form {pnd_form.name}")
                pnd_doc = frappe.get_doc("PND53 Form", pnd_form.name)

                # Count certificates before refresh
                before_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(f"DEBUG: PND Form {pnd_form.name} had {before_count} certificates before refresh")

                # Perform the refresh using the same method as manual refresh
                pnd_doc.populate_wht_certificates()
                pnd_doc.calculate_totals()
                pnd_doc.save(ignore_permissions=True)

                # Count certificates after refresh
                after_count = len(pnd_doc.items) if pnd_doc.items else 0
                print(f"DEBUG: PND Form {pnd_form.name} now has {after_count} certificates after refresh")

                # Check if our certificate is now included
                cert_names = [item.withholding_tax_cert for item in pnd_doc.items if item.withholding_tax_cert]
                is_included = wht_cert_name in cert_names
                print(f"DEBUG: Certificate {wht_cert_name} is included in PND Form: {is_included}")

                if is_included:
                    print(f"DEBUG: SUCCESS - Certificate {wht_cert_name} successfully added to PND53 Form {pnd_form.name}")
                    refreshed_forms.append(pnd_form.name)
                else:
                    print(f"DEBUG: WARNING - Certificate {wht_cert_name} not found in refreshed PND53 Form {pnd_form.name}")
                    print(f"DEBUG: PND Form certificates: {cert_names}")

            except Exception as refresh_error:
                print(f"DEBUG: Error refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}")
                frappe.log_error(
                    message=f"Background job error refreshing PND53 Form {pnd_form.name}: {str(refresh_error)}",
                    title="PND53 Background Job Error"
                )

        # Final commit to ensure all changes are saved
        frappe.db.commit()

        print(f"DEBUG: Background job completed successfully")
        print(f"DEBUG: Refreshed {len(refreshed_forms)} PND53 Forms: {refreshed_forms}")

        # Log successful completion for audit trail
        frappe.logger().info(f"Auto-refresh job completed for WHT Certificate {wht_cert_name}, refreshed PND Forms: {refreshed_forms}")

    except Exception as e:
        print(f"DEBUG: Background job error: {str(e)}")
        import traceback
        print(f"DEBUG: Background job traceback: {traceback.format_exc()}")

        frappe.log_error(
            message=f"Background job error for WHT Certificate {wht_cert_name}: {str(e)}\n\nTraceback:\n{traceback.format_exc()}",
            title="PND53 Background Job Error"
        )
        raise  # Re-raise to mark job as failed for retry