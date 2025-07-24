# File location: print_designer/print_designer/custom/delivery_note_qr.py
# Enhanced QR Delivery Approval System with Token-based Security

import frappe
from frappe import _
import qrcode
from io import BytesIO
import base64

@frappe.whitelist()
def generate_delivery_approval_qr(delivery_note_name):
    """
    Generate QR code for delivery note approval with secure token system
    """
    # Get delivery note
    delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
    
    # Check if approval record already exists
    existing_approval = frappe.db.exists("Delivery Note Approval", {
        "delivery_note": delivery_note_name,
        "status": "Pending"
    })
    
    if existing_approval:
        approval = frappe.get_doc("Delivery Note Approval", existing_approval)
    else:
        # Create new approval record
        approval = frappe.get_doc({
            "doctype": "Delivery Note Approval",
            "delivery_note": delivery_note_name,
            "customer_mobile": delivery_note.get("contact_mobile"),
            "status": "Pending"
        })
        approval.insert()
    
    # Get approval URL
    approval_url = approval.get_approval_url()
    
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
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Update delivery note with QR data (both new and legacy fields for compatibility)
    delivery_note.custom_approval_qr_code = img_str  # Legacy field
    delivery_note.approval_qr_code = img_str  # New standardized field
    delivery_note.custom_approval_url = approval_url
    delivery_note.save()
    
    return {
        "qr_code": img_str,
        "approval_url": approval_url,
        "approval_token": approval.approval_token
    }

@frappe.whitelist()
def approve_delivery_goods(delivery_note_name, customer_name, customer_signature=None, remarks=None):
    """
    Approve goods received for delivery note using token-based system
    """
    # Find the pending approval record
    approval_name = frappe.db.get_value("Delivery Note Approval", {
        "delivery_note": delivery_note_name,
        "status": "Pending"
    })
    
    if not approval_name:
        frappe.throw("No pending approval found for this delivery note")
    
    approval = frappe.get_doc("Delivery Note Approval", approval_name)
    
    # Use the DocType's approval method
    return approval.approve_delivery(customer_name, customer_signature, remarks)

@frappe.whitelist() 
def reject_delivery_goods(delivery_note_name, customer_name, remarks):
    """
    Reject goods for delivery note
    """
    # Find the pending approval record
    approval_name = frappe.db.get_value("Delivery Note Approval", {
        "delivery_note": delivery_note_name,
        "status": "Pending"
    })
    
    if not approval_name:
        frappe.throw("No pending approval found for this delivery note")
    
    approval = frappe.get_doc("Delivery Note Approval", approval_name)
    
    # Use the DocType's rejection method
    return approval.reject_delivery(customer_name, remarks)

@frappe.whitelist()
def get_delivery_status(delivery_note_name):
    """
    Get current delivery status from approval records
    """
    delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
    
    # Get the latest approval record
    approval_data = frappe.db.get_value("Delivery Note Approval", {
        "delivery_note": delivery_note_name
    }, ["status", "approved_on", "customer_name", "remarks"], order_by="creation desc")
    
    if approval_data:
        return {
            "name": delivery_note.name,
            "customer": delivery_note.customer,
            "posting_date": delivery_note.posting_date,
            "grand_total": delivery_note.grand_total,
            "status": approval_data[0] or "Pending",
            "approval_date": approval_data[1],
            "approved_by": approval_data[2],
            "remarks": approval_data[3],
            "has_signature": bool(delivery_note.get("custom_customer_signature"))
        }
    else:
        return {
            "name": delivery_note.name,
            "customer": delivery_note.customer,
            "posting_date": delivery_note.posting_date,
            "grand_total": delivery_note.grand_total,
            "status": delivery_note.get("customer_approval_status") or delivery_note.custom_goods_received_status or "Pending",
            "approval_date": delivery_note.get("customer_approved_on") or delivery_note.custom_customer_approval_date,
            "approved_by": delivery_note.get("customer_approved_by") or delivery_note.custom_approved_by,
            "has_signature": bool(delivery_note.get("customer_signature") or delivery_note.get("custom_customer_signature"))
        }

@frappe.whitelist()
def get_qr_code_image(delivery_note_name):
    """
    Get QR code image for delivery note
    """
    delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
    
    # Check both new and legacy QR code fields
    qr_code = delivery_note.get("approval_qr_code") or delivery_note.custom_approval_qr_code
    if qr_code:
        return {
            "qr_code": qr_code,
            "approval_url": delivery_note.custom_approval_url,
            "data_url": f"data:image/png;base64,{qr_code}"
        }
    else:
        # Generate QR code if not exists
        qr_data = generate_delivery_approval_qr(delivery_note_name)
        return {
            "qr_code": qr_data["qr_code"],
            "approval_url": qr_data["approval_url"],
            "data_url": f"data:image/png;base64,{qr_data['qr_code']}"
        }

def add_qr_to_delivery_note(doc, method):
    """
    Automatically add QR code when delivery note is submitted
    """
    if doc.docstatus == 1:  # Only when submitted
        try:
            # Generate QR code automatically
            generate_delivery_approval_qr(doc.name)
        except Exception as e:
            frappe.log_error(f"Error generating QR code for {doc.name}: {str(e)}")

@frappe.whitelist(allow_guest=True)
def get_approval_by_token(token):
    """
    Get approval details by token for guest access
    """
    from print_designer.print_designer.doctype.delivery_note_approval.delivery_note_approval import get_approval_details
    return get_approval_details(token)

@frappe.whitelist(allow_guest=True) 
def submit_token_approval(token, decision, customer_name, digital_signature=None, remarks=None):
    """
    Submit approval decision using token
    """
    from print_designer.print_designer.doctype.delivery_note_approval.delivery_note_approval import submit_approval_decision
    return submit_approval_decision(token, decision, customer_name, digital_signature, remarks)

@frappe.whitelist()
def regenerate_qr_code(delivery_note_name):
    """
    Regenerate QR code for existing delivery note
    """
    delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
    if delivery_note.docstatus == 1:  # Only for submitted delivery notes
        qr_data = generate_delivery_approval_qr(delivery_note.name)
        return {"success": True, "message": "QR code regenerated successfully", "qr_data": qr_data}
    else:
        frappe.throw(_("QR code can only be generated for submitted delivery notes"))

# Legacy compatibility functions
@frappe.whitelist()
def approve_delivery_legacy(delivery_note_name, customer_signature=None):
    """
    Legacy approval function for backwards compatibility
    """
    return approve_delivery_goods(
        delivery_note_name, 
        frappe.session.user, 
        customer_signature, 
        "Legacy approval"
    )

@frappe.whitelist()
def reject_delivery_legacy(delivery_note_name, rejection_reason=None):
    """
    Legacy rejection function for backwards compatibility
    """
    return reject_delivery_goods(
        delivery_note_name,
        frappe.session.user,
        rejection_reason or "No reason provided"
    )

# Custom fields installation (called from setup system)
def add_custom_fields():
    """
    Add custom fields for QR code functionality
    """
    custom_fields = [
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_delivery_approval_section",
            "label": "Delivery Approval",
            "fieldtype": "Section Break",
            "insert_after": "status",
            "collapsible": 1
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_goods_received_status",
            "label": "Goods Received Status",
            "fieldtype": "Select",
            "options": "Pending\nApproved\nRejected",
            "default": "Pending",
            "insert_after": "custom_delivery_approval_section"
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_approval_qr_code",
            "label": "Approval QR Code",
            "fieldtype": "Long Text",
            "read_only": 1,
            "insert_after": "custom_goods_received_status"
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_approval_url",
            "label": "Approval URL",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "custom_approval_qr_code"
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_customer_approval_column_break",
            "label": "",
            "fieldtype": "Column Break",
            "insert_after": "custom_approval_url"
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_customer_approval_date",
            "label": "Customer Approval Date",
            "fieldtype": "Datetime",
            "read_only": 1,
            "insert_after": "custom_customer_approval_column_break"
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_approved_by",
            "label": "Approved By",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "custom_customer_approval_date"
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_customer_signature",
            "label": "Customer Signature",
            "fieldtype": "Long Text",
            "read_only": 1,
            "insert_after": "custom_approved_by"
        },
        {
            "doctype": "Delivery Note",
            "fieldname": "custom_rejection_reason",
            "label": "Rejection Reason",
            "fieldtype": "Small Text",
            "read_only": 1,
            "depends_on": "eval:doc.custom_goods_received_status == 'Rejected'",
            "insert_after": "custom_customer_signature"
        }
    ]
    
    for field in custom_fields:
        if not frappe.db.exists("Custom Field", {"dt": field["doctype"], "fieldname": field["fieldname"]}):
            try:
                custom_field = frappe.new_doc("Custom Field")
                custom_field.update(field)
                custom_field.insert()
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error creating custom field {field['fieldname']}: {str(e)}")

# Web page creation for approval interface
def create_delivery_approval_page():
    """
    Create web page for delivery approval
    """
    if not frappe.db.exists("Web Page", "delivery-approval"):
        web_page = frappe.new_doc("Web Page")
        web_page.title = "Delivery Approval"
        web_page.route = "delivery-approval"
        web_page.published = 1
        web_page.content_type = "Rich Text"
        web_page.main_section = """
        <div id="delivery-approval-app">
            <div class="container">
                <div class="row">
                    <div class="col-md-8 col-md-offset-2">
                        <h2>Delivery Approval</h2>
                        <p>Loading approval details...</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        // Delivery approval interface will be loaded here
        // This integrates with the client-side JavaScript
        </script>
        """
        web_page.insert()
        return web_page
    
    return frappe.get_doc("Web Page", "delivery-approval")