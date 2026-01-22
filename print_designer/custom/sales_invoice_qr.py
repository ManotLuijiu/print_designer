"""
Sales Invoice QR Code Generation System
Thai e-Tax Format QR codes for B2B document exchange
"""

import json
import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, flt
import qrcode
from io import BytesIO
import base64


def build_invoice_qr_data(doc):
    """
    Build Thai e-Tax format JSON payload for QR code

    Format:
    {
        "inv": "SINV-2024-00001",      # Invoice number
        "dt": "2024-01-15",            # Invoice date
        "tid": "0105555000001",        # Company Tax ID
        "ctid": "0105555000002",       # Customer Tax ID
        "tot": 107000.00,              # Grand total
        "vat": 7000.00,                # VAT amount
        "net": 100000.00,              # Net amount
        "cur": "THB",                  # Currency
        "v": "1.0"                     # Data version
    }
    """
    # Get company tax ID
    company_tax_id = ""
    company = doc.get("company")
    if company:
        company_tax_id = frappe.db.get_value("Company", company, "tax_id") or ""

    # Get customer tax ID
    customer_tax_id = ""
    customer = doc.get("customer")
    if customer:
        customer_tax_id = frappe.db.get_value("Customer", customer, "tax_id") or ""

    # Build QR data
    posting_date = doc.get("posting_date")
    grand_total = doc.get("grand_total") or 0
    total_taxes = doc.get("total_taxes_and_charges") or 0
    net_total = doc.get("net_total") or 0
    currency = doc.get("currency") or "THB"

    qr_data = {
        "inv": doc.name,
        "dt": str(getdate(posting_date)) if posting_date else "",
        "tid": str(company_tax_id).replace("-", "").replace(" ", ""),
        "ctid": str(customer_tax_id).replace("-", "").replace(" ", ""),
        "tot": flt(grand_total, 2),
        "vat": flt(total_taxes, 2),
        "net": flt(net_total, 2),
        "cur": currency,
        "v": "1.0"
    }

    return qr_data


@frappe.whitelist()
def generate_sales_invoice_qr(invoice_name):
    """
    Generate QR code for Sales Invoice with Thai e-Tax format data
    """
    # Get Sales Invoice
    invoice = frappe.get_doc("Sales Invoice", invoice_name)

    # Build QR data
    qr_data = build_invoice_qr_data(invoice)
    qr_json = json.dumps(qr_data, ensure_ascii=False, separators=(',', ':'))

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_json)
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    # Build verification URL (optional - can be customized per deployment)
    site_url = frappe.utils.get_url()
    verification_url = f"{site_url}/api/method/print_designer.custom.sales_invoice_qr.verify_invoice?invoice={invoice_name}"

    # Build full data URL for Print Designer Image element
    data_url = f"data:image/png;base64,{img_str}"

    # Save to invoice using db_set for submitted documents
    try:
        invoice.db_set('custom_invoice_qr_code', img_str, update_modified=False)
        invoice.db_set('custom_invoice_qr_image', data_url, update_modified=False)  # For Print Designer drag & drop
        invoice.db_set('custom_invoice_qr_url', verification_url, update_modified=False)
        invoice.db_set('custom_invoice_qr_generated_on', now_datetime(), update_modified=False)
        invoice.db_set('custom_invoice_qr_data_version', '1.0', update_modified=False)
    except Exception as e:
        frappe.log_error(f"QR Save Error: {invoice_name} - {str(e)}", "Sales Invoice QR Generation")

    return {
        "qr_code": img_str,
        "qr_data": qr_data,
        "verification_url": verification_url,
        "data_url": f"data:image/png;base64,{img_str}"
    }


def add_qr_to_sales_invoice(doc, method):
    """
    Automatically add QR code when Sales Invoice is submitted
    Hook for doc_events on_submit
    """
    if doc.docstatus == 1:  # Only when submitted
        try:
            # Check if QR should be generated
            show_qr = doc.get("custom_show_qr_on_print")
            if show_qr is None or show_qr:  # Default to True if not set
                generate_sales_invoice_qr(doc.name)
        except Exception as e:
            frappe.log_error(f"QR Error: {doc.name} - {str(e)}", "Sales Invoice QR Hook")


@frappe.whitelist()
def get_qr_code_for_print(invoice_name):
    """
    Get QR code image for print format, generating if needed
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name)

    # Check if QR display is enabled
    show_qr = invoice.get("custom_show_qr_on_print")
    if show_qr is not None and not show_qr:
        return None

    # Check if QR code already exists
    qr_code = invoice.get("custom_invoice_qr_code")
    if qr_code:
        return {
            "qr_code": qr_code,
            "data_url": f"data:image/png;base64,{qr_code}",
            "verification_url": invoice.get("custom_invoice_qr_url")
        }

    # Generate QR code if not exists and document is submitted
    if invoice.docstatus == 1:
        qr_data = generate_sales_invoice_qr(invoice_name)
        return {
            "qr_code": qr_data["qr_code"],
            "data_url": qr_data["data_url"],
            "verification_url": qr_data["verification_url"]
        }

    return None


@frappe.whitelist()
def regenerate_qr_code(invoice_name):
    """
    Regenerate QR code for existing Sales Invoice
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    if invoice.docstatus == 1:  # Only for submitted invoices
        qr_data = generate_sales_invoice_qr(invoice_name)
        return {"success": True, "message": "QR code regenerated successfully", "qr_data": qr_data}
    else:
        frappe.throw(_("QR code can only be generated for submitted Sales Invoices"))


@frappe.whitelist(allow_guest=True)
def verify_invoice(invoice):
    """
    Verify invoice data via QR code scan
    Returns invoice details for verification
    """
    if not invoice:
        return {"valid": False, "error": "No invoice specified"}

    try:
        if not frappe.db.exists("Sales Invoice", invoice):
            return {"valid": False, "error": "Invoice not found"}

        doc = frappe.get_doc("Sales Invoice", invoice)

        # Build verification response
        return {
            "valid": True,
            "invoice": doc.name,
            "date": str(doc.posting_date),
            "customer": doc.customer_name,
            "grand_total": flt(doc.grand_total, 2),
            "currency": doc.currency,
            "status": doc.status,
            "company": doc.company
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


@frappe.whitelist()
def get_invoice_qr_data(invoice_name):
    """
    Get the QR data structure for an invoice (without generating QR image)
    Useful for debugging or external integrations
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    return build_invoice_qr_data(invoice)
