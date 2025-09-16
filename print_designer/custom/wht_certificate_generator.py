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

    # Only process Payment Entry documents with Thai taxes
    has_thai_taxes = getattr(payment_entry_doc, 'pd_custom_has_thai_taxes', 0)
    print(f"DEBUG: pd_custom_has_thai_taxes = {has_thai_taxes}")

    if not has_thai_taxes:
        print("DEBUG: Skipping - No Thai taxes")
        return

    # Check if WHT amount exists
    wht_amount = flt(getattr(payment_entry_doc, 'pd_custom_withholding_tax_amount', 0))
    print(f"DEBUG: pd_custom_withholding_tax_amount = {wht_amount}")

    if wht_amount <= 0:
        print(f"DEBUG: Skipping - WHT amount is {wht_amount}")
        return

    # Skip if certificate already exists
    existing_cert = frappe.db.exists("Withholding Tax Certificate", {
        "payment_entry": payment_entry_doc.name
    })
    print(f"DEBUG: Existing certificate check: {existing_cert}")

    if existing_cert:
        print(f"DEBUG: Skipping - Certificate already exists: {existing_cert}")
        return

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
        wht_cert = frappe.new_doc("Withholding Tax Certificate")

        # Certificate Information
        posting_date = getdate(payment_entry_doc.posting_date)
        buddhist_year = posting_date.year + 543
        buddhist_year_short = str(buddhist_year)[-2:]
        month = str(posting_date.month).zfill(2)

        # Generate certificate number
        naming_pattern = f"WHTC-{buddhist_year_short}{month}-.#####"
        wht_cert.certificate_number = make_autoname(naming_pattern)
        wht_cert.certificate_date = payment_entry_doc.posting_date
        wht_cert.tax_year = f"{buddhist_year}"
        wht_cert.tax_month = f"{month:02d} - {_get_thai_month_name(posting_date.month)}"

        # Supplier Information
        wht_cert.supplier = payment_entry_doc.party
        wht_cert.supplier_name = payment_entry_doc.party_name
        if hasattr(purchase_invoice, 'tax_id') and purchase_invoice.tax_id:
            wht_cert.supplier_tax_id = purchase_invoice.tax_id

        # Get supplier address
        supplier_doc = frappe.get_doc("Supplier", payment_entry_doc.party)
        if supplier_doc.supplier_primary_address:
            address_doc = frappe.get_doc("Address", supplier_doc.supplier_primary_address)
            wht_cert.supplier_address = address_doc.address_line1
            if address_doc.address_line2:
                wht_cert.supplier_address += f", {address_doc.address_line2}"
            if address_doc.city:
                wht_cert.supplier_address += f", {address_doc.city}"
            if address_doc.state:
                wht_cert.supplier_address += f", {address_doc.state}"

        # Payment Information
        wht_cert.payment_entry = payment_entry_doc.name
        wht_cert.payment_date = payment_entry_doc.posting_date
        wht_cert.purchase_invoice = purchase_invoice_name
        wht_cert.company = payment_entry_doc.company

        # WHT Details
        wht_cert.income_type = _get_income_type_from_purchase_invoice(purchase_invoice)
        wht_cert.income_description = _get_income_description(purchase_invoice)
        wht_cert.wht_rate = flt(getattr(payment_entry_doc, 'pd_custom_withholding_tax_rate', 0))
        wht_cert.wht_condition = "1. หัก ณ ที่จ่าย (Withhold at Source)"

        # Amount Details
        wht_cert.tax_base_amount = flt(getattr(payment_entry_doc, 'pd_custom_tax_base_amount', 0))
        wht_cert.wht_amount = wht_amount

        # Calculate other amounts
        total_payment = flt(getattr(payment_entry_doc, 'pd_custom_total_payment_amount', 0))
        if total_payment == 0:
            total_payment = wht_cert.tax_base_amount + flt(purchase_invoice.total_taxes_and_charges or 0)

        wht_cert.total_payment_amount = total_payment
        wht_cert.net_payment_amount = total_payment - wht_amount

        # PND Form Type and supplier classification based on supplier type
        pnd_form_type, supplier_classification = _get_pnd_form_and_classification(payment_entry_doc.party)
        wht_cert.pnd_form_type = pnd_form_type
        wht_cert.supplier_type_classification = supplier_classification

        # Set initial status
        wht_cert.status = "Draft"

        # Remarks
        wht_cert.remarks = f"Auto-generated from Payment Entry {payment_entry_doc.name} for Purchase Invoice {purchase_invoice_name}"

        # Save and submit the certificate
        wht_cert.insert(ignore_permissions=True)

        # Create a link back to Payment Entry
        if not hasattr(payment_entry_doc, 'pd_custom_wht_certificate'):
            # Add custom field to Payment Entry if it doesn't exist
            _ensure_wht_certificate_link_field()

        # Update Payment Entry with certificate link
        frappe.db.set_value("Payment Entry", payment_entry_doc.name, "pd_custom_wht_certificate", wht_cert.name)

        frappe.msgprint(
            _("Withholding Tax Certificate {0} created successfully").format(wht_cert.name),
            alert=True,
            indicator="green"
        )

    except Exception as e:
        frappe.log_error(f"Error creating WHT Certificate: {str(e)}")
        frappe.throw(_("Failed to create Withholding Tax Certificate: {0}").format(str(e)))


def _get_thai_month_name(month_num):
    """Get Thai month name"""
    thai_months = {
        1: "มกราคม (January)",
        2: "กุมภาพันธ์ (February)",
        3: "มีนาคม (March)",
        4: "เมษายน (April)",
        5: "พฤษภาคม (May)",
        6: "มิถุนายน (June)",
        7: "กรกฎาคม (July)",
        8: "สิงหาคม (August)",
        9: "กันยายน (September)",
        10: "ตุลาคม (October)",
        11: "พฤศจิกายน (November)",
        12: "ธันวาคม (December)"
    }
    return thai_months.get(month_num, "")


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
        tuple: (pnd_form_type, supplier_classification)
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
            # Company or Juristic Person
            return ("ภ.ง.ด.53 (PND 53)", "Company/Juristic Person (PND.53)")
        else:
            # Individual - For now, default to PND.3 (Services)
            # Note: PND.1 is for salary/employee payments, which would need additional logic
            # to determine if this is an employee vs. freelancer/service provider
            return ("ภ.ง.ด.3 (PND 3)", "Individual - Non-staff (PND.3)")

    except Exception as e:
        frappe.log_error(f"Error determining PND form type for supplier {supplier_name}: {str(e)}")
        # Default fallback
        return ("ภ.ง.ด.3 (PND 3)", "Individual - Non-staff (PND.3)")


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
    if not hasattr(payment_entry_doc, 'pd_custom_has_thai_taxes') or not payment_entry_doc.pd_custom_has_thai_taxes:
        return {"eligible": False, "message": "No Thai taxes found"}

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
        "tax_month": f"{posting_date.month:02d} - {_get_thai_month_name(posting_date.month)}",
        "supplier": payment_entry_doc.party_name,
        "tax_base_amount": flt(getattr(payment_entry_doc, 'pd_custom_tax_base_amount', 0)),
        "wht_rate": flt(getattr(payment_entry_doc, 'pd_custom_withholding_tax_rate', 0)),
        "wht_amount": wht_amount,
        "income_type": _get_income_type_from_purchase_invoice(purchase_invoice),
        "pnd_form_type": _get_pnd_form_and_classification(payment_entry_doc.party)[0]  # Get only the PND form type
    }

    return preview_data