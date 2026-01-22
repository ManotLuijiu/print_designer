"""
Sales Invoice QR Code Jinja Macros for Print Designer
Provides Jinja macro functions for Thai e-Tax QR codes in print formats
"""

import frappe
from frappe.utils import flt


def render_sales_invoice_qr(invoice_name, position="bottom-right", size=100):
    """
    Render Sales Invoice QR code for print format

    Usage in Jinja: {{ render_sales_invoice_qr(doc.name) }}

    Args:
        invoice_name: Sales Invoice document name
        position: 'bottom-right', 'bottom-left', 'inline' (default: 'bottom-right')
        size: QR code size in pixels (default: 100)

    Returns:
        HTML string with QR code and positioning styles
    """
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_name)

        # Check if QR display is enabled
        show_qr = invoice.get("custom_show_qr_on_print")
        if show_qr is not None and not show_qr:
            return ""

        # Get QR code
        qr_code = invoice.get("custom_invoice_qr_code")
        if not qr_code and invoice.docstatus == 1:
            # Generate if not exists
            from print_designer.custom.sales_invoice_qr import generate_sales_invoice_qr
            qr_data = generate_sales_invoice_qr(invoice_name)
            qr_code = qr_data.get("qr_code")

        if not qr_code:
            return ""

        # Position styles
        position_styles = {
            "bottom-right": "position: fixed; bottom: 20mm; right: 20mm; z-index: 1000;",
            "bottom-left": "position: fixed; bottom: 20mm; left: 20mm; z-index: 1000;",
            "inline": "display: inline-block; margin: 10px 0;"
        }

        pos_style = position_styles.get(position, position_styles["bottom-right"])

        return f'''
        <div class="sales-invoice-qr-code" style="{pos_style} text-align: center;">
            <img src="data:image/png;base64,{qr_code}"
                 alt="Invoice QR Code"
                 style="width: {size}px; height: {size}px; border: 1px solid #ddd; padding: 3px; background: white;">
            <div style="font-size: 8px; color: #666; margin-top: 3px;">
                Scan for invoice data
            </div>
        </div>
        '''
    except Exception as e:
        frappe.log_error(f"Error rendering Sales Invoice QR: {str(e)}")
        return ""


def render_sales_invoice_qr_footer(invoice_name, size=80):
    """
    Render Sales Invoice QR code for footer placement

    Usage in Jinja: {{ render_sales_invoice_qr_footer(doc.name) }}

    Args:
        invoice_name: Sales Invoice document name
        size: QR code size in pixels (default: 80)

    Returns:
        HTML string suitable for footer placement
    """
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_name)

        # Check if QR display is enabled
        show_qr = invoice.get("custom_show_qr_on_print")
        if show_qr is not None and not show_qr:
            return ""

        # Get QR code
        qr_code = invoice.get("custom_invoice_qr_code")
        if not qr_code and invoice.docstatus == 1:
            from print_designer.custom.sales_invoice_qr import generate_sales_invoice_qr
            qr_data = generate_sales_invoice_qr(invoice_name)
            qr_code = qr_data.get("qr_code")

        if not qr_code:
            return ""

        return f'''
        <div class="sales-invoice-qr-footer" style="float: right; text-align: center; margin-left: 15px;">
            <img src="data:image/png;base64,{qr_code}"
                 alt="Invoice QR"
                 style="width: {size}px; height: {size}px;">
            <div style="font-size: 7px; color: #888; margin-top: 2px;">e-Tax QR</div>
        </div>
        '''
    except Exception as e:
        frappe.log_error(f"Error rendering Sales Invoice QR footer: {str(e)}")
        return ""


def render_sales_invoice_verification_info(invoice_name):
    """
    Render complete verification block with QR code and invoice summary

    Usage in Jinja: {{ render_sales_invoice_verification_info(doc.name) }}

    Args:
        invoice_name: Sales Invoice document name

    Returns:
        HTML string with QR code and invoice summary for verification
    """
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_name)

        # Check if QR display is enabled
        show_qr = invoice.get("custom_show_qr_on_print")
        if show_qr is not None and not show_qr:
            return ""

        # Get QR code
        qr_code = invoice.get("custom_invoice_qr_code")
        if not qr_code and invoice.docstatus == 1:
            from print_designer.custom.sales_invoice_qr import generate_sales_invoice_qr
            qr_data = generate_sales_invoice_qr(invoice_name)
            qr_code = qr_data.get("qr_code")

        if not qr_code:
            return ""

        # Get company tax ID
        company_tax_id = ""
        if invoice.company:
            company_tax_id = frappe.db.get_value("Company", invoice.company, "tax_id") or ""

        # Format amounts
        grand_total = flt(invoice.grand_total, 2)
        vat_amount = flt(invoice.total_taxes_and_charges, 2)
        net_total = flt(invoice.net_total, 2)

        return f'''
        <div class="invoice-verification-block" style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; display: flex; align-items: center; background: #fafafa;">
            <div style="flex: 0 0 120px; text-align: center;">
                <img src="data:image/png;base64,{qr_code}"
                     alt="Invoice QR Code"
                     style="width: 100px; height: 100px; border: 1px solid #ccc; padding: 3px; background: white;">
                <div style="font-size: 8px; color: #666; margin-top: 5px;">Thai e-Tax QR</div>
            </div>
            <div style="flex: 1; padding-left: 20px; font-size: 11px;">
                <div style="font-weight: bold; font-size: 12px; margin-bottom: 8px; color: #333;">
                    Invoice Verification Data
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 2px 10px 2px 0; color: #666;">Invoice No:</td>
                        <td style="padding: 2px 0; font-weight: bold;">{invoice.name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 2px 10px 2px 0; color: #666;">Date:</td>
                        <td style="padding: 2px 0;">{invoice.posting_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 2px 10px 2px 0; color: #666;">Tax ID:</td>
                        <td style="padding: 2px 0;">{company_tax_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 2px 10px 2px 0; color: #666;">Net Amount:</td>
                        <td style="padding: 2px 0;">{invoice.currency} {net_total:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 2px 10px 2px 0; color: #666;">VAT:</td>
                        <td style="padding: 2px 0;">{invoice.currency} {vat_amount:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 2px 10px 2px 0; color: #666;">Grand Total:</td>
                        <td style="padding: 2px 0; font-weight: bold; font-size: 12px;">{invoice.currency} {grand_total:,.2f}</td>
                    </tr>
                </table>
            </div>
        </div>
        '''
    except Exception as e:
        frappe.log_error(f"Error rendering Sales Invoice verification info: {str(e)}")
        return ""


def render_sales_invoice_qr_compact(invoice_name, size=60):
    """
    Render compact QR code for space-constrained print formats

    Usage in Jinja: {{ render_sales_invoice_qr_compact(doc.name) }}

    Args:
        invoice_name: Sales Invoice document name
        size: QR code size in pixels (default: 60)

    Returns:
        HTML string with minimal QR code display
    """
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_name)

        # Check if QR display is enabled
        show_qr = invoice.get("custom_show_qr_on_print")
        if show_qr is not None and not show_qr:
            return ""

        # Get QR code
        qr_code = invoice.get("custom_invoice_qr_code")
        if not qr_code and invoice.docstatus == 1:
            from print_designer.custom.sales_invoice_qr import generate_sales_invoice_qr
            qr_data = generate_sales_invoice_qr(invoice_name)
            qr_code = qr_data.get("qr_code")

        if not qr_code:
            return ""

        return f'''
        <div style="display: inline-block; text-align: center;">
            <img src="data:image/png;base64,{qr_code}"
                 alt="QR"
                 style="width: {size}px; height: {size}px;">
        </div>
        '''
    except Exception as e:
        frappe.log_error(f"Error rendering compact Sales Invoice QR: {str(e)}")
        return ""


def get_sales_invoice_qr_data_url(invoice_name):
    """
    Get just the data URL for QR code image
    Useful for custom Jinja templates that need direct image source

    Usage in Jinja:
        <img src="{{ get_sales_invoice_qr_data_url(doc.name) }}" style="width: 100px;">

    Args:
        invoice_name: Sales Invoice document name

    Returns:
        Data URL string or empty string if QR not available
    """
    try:
        invoice = frappe.get_doc("Sales Invoice", invoice_name)

        show_qr = invoice.get("custom_show_qr_on_print")
        if show_qr is not None and not show_qr:
            return ""

        qr_code = invoice.get("custom_invoice_qr_code")
        if not qr_code and invoice.docstatus == 1:
            from print_designer.custom.sales_invoice_qr import generate_sales_invoice_qr
            qr_data = generate_sales_invoice_qr(invoice_name)
            qr_code = qr_data.get("qr_code")

        if qr_code:
            return f"data:image/png;base64,{qr_code}"

        return ""
    except Exception as e:
        frappe.log_error(f"Error getting Sales Invoice QR data URL: {str(e)}")
        return ""
