import frappe
from frappe import _

def get_signature_fields():
    """Get all signature fields for Print Designer integration"""
    
    # Base signature fields that should be available in print formats
    signature_fields = []
    
    # Get all active signatures
    signatures = frappe.get_all("Signature Basic Information", 
                               filters={"is_active": 1},
                               fields=["name", "signature_label", "signature_category", "user_id", "signature_data"])
    
    for signature in signatures:
        signature_fields.append({
            "fieldname": f"signature_{signature.name.lower().replace('-', '_')}",
            "label": signature.signature_label,
            "fieldtype": "Attach Image",
            "value": signature.signature_data,
            "signature_id": signature.name,
            "signature_type": signature.signature_category,
            "user_id": signature.user_id
        })
    
    return signature_fields

def get_signature_data_for_print(signature_id):
    """Get signature data for print format"""
    
    if not signature_id:
        return None
    
    signature = frappe.get_doc("Signature Basic Information", signature_id)
    
    if not signature or not signature.is_active:
        return None
    
    return {
        "signature_data": signature.signature_data,
        "signature_label": signature.signature_label,
        "signature_category": signature.signature_category,
        "width": signature.width or 150,
        "height": signature.height or 75,
        "user_id": signature.user_id
    }

def get_company_signatures(company):
    """Get signatures associated with a company"""
    
    signatures = frappe.get_all("Signature Basic Information",
                               filters={
                                   "is_active": 1,
                                   "company": company
                               },
                               fields=["name", "signature_label", "signature_category", "signature_data"])
    
    return signatures

def get_user_signatures(user_id):
    """Get signatures for a specific user"""
    
    signatures = frappe.get_all("Signature Basic Information",
                               filters={
                                   "is_active": 1,
                                   "user_id": user_id
                               },
                               fields=["name", "signature_label", "signature_category", "signature_data"])
    
    return signatures

def log_signature_usage(signature_id, document_type, document_name, print_format=None):
    """Log signature usage for tracking"""
    
    if not signature_id:
        return
    
    try:
        # Find existing usage record
        usage_filters = {
            "parent": signature_id,
            "document_type": document_type,
            "document_name": document_name
        }
        
        if print_format:
            usage_filters["print_format"] = print_format
        
        existing_usage = frappe.db.exists("Signature Usage", usage_filters)
        
        if existing_usage:
            # Update usage count
            frappe.db.sql("""
                UPDATE `tabSignature Usage` 
                SET usage_count = usage_count + 1, 
                    last_used = NOW()
                WHERE name = %s
            """, existing_usage)
        else:
            # Create new usage record
            signature_doc = frappe.get_doc("Signature Basic Information", signature_id)
            usage_doc = frappe.new_doc("Signature Usage")
            usage_doc.parent = signature_id
            usage_doc.parenttype = "Signature Basic Information"
            usage_doc.parentfield = "usage_tracking"
            usage_doc.document_type = document_type
            usage_doc.document_name = document_name
            usage_doc.print_format = print_format or "Standard"
            usage_doc.usage_count = 1
            usage_doc.last_used = frappe.utils.now()
            usage_doc.insert()
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error logging signature usage: {str(e)}", "Signature Usage Error")

@frappe.whitelist()
def get_signature_for_document(doctype, docname, signature_type="Signature"):
    """Get appropriate signature for a document"""
    
    # Get document
    doc = frappe.get_doc(doctype, docname)
    
    # Try to get signature based on user or company
    signatures = []
    
    # Check if document has owner/user field
    if hasattr(doc, 'owner'):
        signatures = get_user_signatures(doc.owner)
    
    # Check if document has company field
    if hasattr(doc, 'company') and not signatures:
        signatures = get_company_signatures(doc.company)
    
    # Filter by signature type
    if signature_type:
        signatures = [s for s in signatures if s.signature_category == signature_type]
    
    # Return first active signature
    if signatures:
        return signatures[0]
    
    return None

@frappe.whitelist()
def get_available_signatures():
    """Get all available signatures for print designer"""
    
    signatures = frappe.get_all("Signature Basic Information",
                               filters={"is_active": 1},
                               fields=["name", "signature_label", "signature_category", 
                                      "signature_data", "width", "height", "user_id"])
    
    return signatures