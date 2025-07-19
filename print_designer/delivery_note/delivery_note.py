import frappe
import qrcode
import io
import base64
from frappe.utils import get_url


def generate_approval_qr_code(delivery_note_name):
    """Generate QR code for delivery note approval"""

    # Create approval URL
    approval_url = f"{get_url()}/api/method/custom_app.delivery_note.approve_delivery?dn={delivery_note_name}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(approval_url)
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


@frappe.whitelist(allow_guest=True)
def approve_delivery(dn):
    """API endpoint for delivery note approval"""
    try:
        doc = frappe.get_doc("Delivery Note", dn)
        doc.custom_approval_status = "Approved"
        doc.custom_approved_on = frappe.utils.now()
        doc.save()

        return {"status": "success", "message": "Delivery Note approved successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
