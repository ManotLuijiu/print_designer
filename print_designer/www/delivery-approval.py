import frappe

def get_context(context):
    """
    Context for delivery approval page
    """
    # Get delivery note name from path
    path_parts = frappe.request.path.strip('/').split('/')
    if len(path_parts) >= 2:
        delivery_note_name = path_parts[-1]
        context.delivery_note_name = delivery_note_name
    else:
        context.delivery_note_name = None
    
    context.title = "Delivery Approval"
    context.show_sidebar = False
    
    return context