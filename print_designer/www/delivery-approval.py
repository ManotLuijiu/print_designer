import frappe
from frappe import _

no_cache = 1

def get_context(context):
    """
    Context for delivery approval page
    """
    # Get parameters from query string
    delivery_note_name = frappe.form_dict.get('dn')
    token = frappe.form_dict.get('token')

    context.delivery_note_name = delivery_note_name
    context.token = token
    context.title = _("Delivery Approval")
    context.show_sidebar = False
    context.no_cache = 1

    # Validate token and get approval details if available
    if token:
        try:
            approval = frappe.get_all("Delivery Note Approval",
                filters={"approval_token": token, "delivery_note": delivery_note_name},
                fields=["name", "status", "delivery_note", "customer_mobile"],
                limit=1
            )

            if approval:
                context.approval_data = approval[0]
                context.has_valid_token = True
            else:
                context.has_valid_token = False
                context.error_message = _("Invalid or expired approval link")
        except Exception as e:
            frappe.log_error(f"Approval validation error: {str(e)}")
            context.has_valid_token = False
            context.error_message = _("Error validating approval link")
    else:
        context.has_valid_token = False
        context.error_message = _("Missing approval token")

    return context