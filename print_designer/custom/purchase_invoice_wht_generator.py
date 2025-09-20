#!/usr/bin/env python3
"""
Purchase Invoice WHT Certificate Generator

Handles automatic creation of Withholding Tax Certificates from Purchase Invoice
for cash services purchases with Thai WHT compliance.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_months
from frappe.model.naming import make_autoname


def on_submit_purchase_invoice(doc, method):
    """
    Called when Purchase Invoice is submitted.
    Create WHT Certificate for cash services purchases with Thai WHT compliance.
    """
    # Check if this is a cash services purchase with WHT
    if not is_cash_services_with_wht(doc):
        return

    # Create WHT Certificate
    create_wht_certificate_from_purchase_invoice(doc)


def is_cash_services_with_wht(purchase_invoice):
    """
    Check if Purchase Invoice qualifies for automatic WHT Certificate creation.
    Requirements:
    1. is_paid = 1 (Cash purchase)
    2. apply_thai_wht_compliance = 1 (Thai WHT enabled)
    3. Contains service items (not goods)
    """
    # Check cash purchase and Thai WHT compliance flags
    is_paid = purchase_invoice.get('is_paid', 0)
    apply_thai_wht = purchase_invoice.get('apply_thai_wht_compliance', 0)

    if not is_paid or not apply_thai_wht:
        return False

    # Check if there are service items
    has_service = False
    for item in purchase_invoice.items:
        item_doc = frappe.get_doc("Item", item.item_code)
        if item_doc.is_stock_item == 0:  # Service item
            has_service = True
            break

    if not has_service:
        frappe.log_error(
            f"Purchase Invoice {purchase_invoice.name} is cash purchase with WHT but has no service items",
            "WHT Certificate Generator"
        )
        return False

    # Check if WHT certificate already exists
    existing_cert = frappe.db.exists("Withholding Tax Certificate", {
        "purchase_invoice": purchase_invoice.name
    })

    if existing_cert:
        frappe.log_error(
            f"WHT Certificate already exists for Purchase Invoice {purchase_invoice.name}",
            "WHT Certificate Generator"
        )
        return False

    return True


def create_wht_certificate_from_purchase_invoice(purchase_invoice):
    """
    Create Withholding Tax Certificate from cash services Purchase Invoice.
    This is for immediate cash purchases where WHT is deducted at the time of purchase.
    """
    try:
        wht_cert = frappe.new_doc("Withholding Tax Certificate")

        # Certificate Information
        posting_date = getdate(purchase_invoice.posting_date)
        buddhist_year = posting_date.year + 543
        buddhist_year_short = str(buddhist_year)[-2:]
        month_num = posting_date.month
        month = str(month_num).zfill(2)

        # Generate certificate number
        naming_pattern = f"WHTC-{buddhist_year_short}{month}-.#####"
        wht_cert.certificate_number = make_autoname(naming_pattern)
        wht_cert.certificate_date = purchase_invoice.posting_date
        wht_cert.tax_year = f"{buddhist_year}"
        wht_cert.tax_month = f"{month} - {_get_thai_month_name(month_num)}"

        # Supplier Information
        wht_cert.supplier = purchase_invoice.supplier
        wht_cert.supplier_name = purchase_invoice.supplier_name
        if hasattr(purchase_invoice, 'tax_id') and purchase_invoice.tax_id:
            wht_cert.supplier_tax_id = purchase_invoice.tax_id

        # Get supplier address
        supplier_doc = frappe.get_doc("Supplier", purchase_invoice.supplier)
        if supplier_doc.supplier_primary_address:
            address_doc = frappe.get_doc("Address", supplier_doc.supplier_primary_address)
            wht_cert.supplier_address = address_doc.address_line1
            if address_doc.address_line2:
                wht_cert.supplier_address += f", {address_doc.address_line2}"
            if address_doc.city:
                wht_cert.supplier_address += f", {address_doc.city}"
            if address_doc.state:
                wht_cert.supplier_address += f", {address_doc.state}"

        # Purchase Information
        wht_cert.purchase_invoice = purchase_invoice.name
        wht_cert.payment_date = purchase_invoice.posting_date  # Cash purchase - same date
        wht_cert.company = purchase_invoice.company

        # WHT Details
        wht_cert.income_type = _get_income_type_from_purchase_invoice(purchase_invoice)
        wht_cert.income_description = _get_income_description(purchase_invoice)

        # Get WHT rate and amount from Purchase Invoice custom fields
        wht_rate = flt(purchase_invoice.get('wht_rate', 0))
        wht_amount = flt(purchase_invoice.get('wht_amount', 0))

        # Calculate tax base amount (before VAT)
        tax_base_amount = purchase_invoice.base_net_total or purchase_invoice.net_total

        # If WHT amount is not set, calculate it
        if wht_amount == 0 and wht_rate > 0:
            wht_amount = tax_base_amount * (wht_rate / 100)

        # If WHT rate is not set but amount exists, calculate rate
        if wht_rate == 0 and wht_amount > 0 and tax_base_amount > 0:
            wht_rate = (wht_amount / tax_base_amount) * 100

        wht_cert.wht_rate = wht_rate
        wht_cert.wht_condition = "1. หัก ณ ที่จ่าย (Withhold at Source)"

        # Amount Details
        wht_cert.tax_base_amount = tax_base_amount
        wht_cert.wht_amount = wht_amount

        # Calculate total and net payment amounts
        total_payment = purchase_invoice.grand_total
        wht_cert.total_payment_amount = total_payment
        wht_cert.net_payment_amount = total_payment - wht_amount

        # PND Form Type and supplier classification
        pnd_form_type, supplier_classification = _get_pnd_form_and_classification(purchase_invoice.supplier)
        wht_cert.pnd_form_type = pnd_form_type
        wht_cert.supplier_type_classification = supplier_classification

        # Set initial status
        wht_cert.status = "Draft"

        # Remarks
        wht_cert.remarks = f"Auto-generated from Purchase Invoice {purchase_invoice.name} (Cash Services Purchase)"

        # Save and optionally submit the certificate
        wht_cert.insert(ignore_permissions=True)

        # Auto-submit if configured
        if frappe.db.get_single_value("Accounts Settings", "auto_submit_wht_certificate"):
            wht_cert.submit()

        frappe.msgprint(
            _("Withholding Tax Certificate {0} created successfully for cash services purchase").format(wht_cert.name),
            alert=True,
            indicator="green"
        )

        # Update Purchase Invoice with certificate link
        frappe.db.set_value("Purchase Invoice", purchase_invoice.name, "wht_certificate", wht_cert.name)

    except Exception as e:
        # Log full error details
        frappe.log_error(
            message=f"Error creating WHT Certificate from Purchase Invoice {purchase_invoice.name}: {str(e)}",
            title="WHT Certificate Error"
        )
        # Show concise message to user
        frappe.throw(_("Failed to create WHT Certificate. Check error log for details."))


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
    Get PND form type and supplier classification based on supplier type.
    Returns the DocType name for linking, not display text.
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
            return ("PND3 Form", "Individual - Non-staff (PND.3)")

    except Exception as e:
        frappe.log_error(f"Error determining PND form type for supplier {supplier_name}: {str(e)}")
        # Default fallback - return the DocType name
        return ("PND3 Form", "Individual - Non-staff (PND.3)")