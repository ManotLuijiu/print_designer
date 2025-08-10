"""
Field Synchronization Utilities for Delivery Note QR System
Ensures compatibility between legacy and standardized field names
"""

import frappe

def sync_delivery_note_fields(doc, method=None):
    """
    Synchronize between legacy and standardized delivery note fields
    Called via hooks to ensure data consistency
    """
    if doc.doctype != "Delivery Note":
        return
    
    # Sync approval status
    if doc.get("customer_approval_status") and not doc.get("custom_goods_received_status"):
        doc.custom_goods_received_status = doc.customer_approval_status
    elif doc.get("custom_goods_received_status") and not doc.get("customer_approval_status"):
        doc.customer_approval_status = doc.custom_goods_received_status
    
    # Sync signature fields
    if doc.get("customer_signature") and not doc.get("custom_customer_signature"):
        doc.custom_customer_signature = doc.customer_signature
    elif doc.get("custom_customer_signature") and not doc.get("customer_signature"):
        doc.customer_signature = doc.custom_customer_signature
    
    # Sync approved by fields
    if doc.get("customer_approved_by") and not doc.get("custom_approved_by"):
        doc.custom_approved_by = doc.customer_approved_by
    elif doc.get("custom_approved_by") and not doc.get("customer_approved_by"):
        doc.customer_approved_by = doc.custom_approved_by
    
    # Sync approval date fields
    if doc.get("customer_approved_on") and not doc.get("custom_customer_approval_date"):
        doc.custom_customer_approval_date = doc.customer_approved_on
    elif doc.get("custom_customer_approval_date") and not doc.get("customer_approved_on"):
        doc.customer_approved_on = doc.custom_customer_approval_date
    
    # Sync QR code fields
    if doc.get("approval_qr_code") and not doc.get("custom_approval_qr_code"):
        doc.custom_approval_qr_code = doc.approval_qr_code
    elif doc.get("custom_approval_qr_code") and not doc.get("approval_qr_code"):
        doc.approval_qr_code = doc.custom_approval_qr_code

def get_standardized_field_value(doc, field_mapping):
    """
    Get field value using standardized field names with legacy fallback
    
    Args:
        doc: Document object
        field_mapping: dict with 'new' and 'legacy' field names
        
    Returns:
        Field value from new field name, or legacy field name as fallback
    """
    return doc.get(field_mapping["new"]) or doc.get(field_mapping["legacy"])

def set_field_values(doc, field_mapping, value):
    """
    Set value to both standardized and legacy field names
    
    Args:
        doc: Document object  
        field_mapping: dict with 'new' and 'legacy' field names
        value: Value to set
    """
    if field_mapping.get("new"):
        doc.set(field_mapping["new"], value)
    if field_mapping.get("legacy"):
        doc.set(field_mapping["legacy"], value)

# Field mapping between standardized and legacy names
DELIVERY_NOTE_FIELD_MAPPING = {
    "approval_status": {
        "new": "customer_approval_status",
        "legacy": "custom_goods_received_status"
    },
    "digital_signature": {
        "new": "customer_signature", 
        "legacy": "custom_customer_signature"
    },
    "approved_by": {
        "new": "customer_approved_by",
        "legacy": "custom_approved_by"
    },
    "approved_on": {
        "new": "customer_approved_on",
        "legacy": "custom_customer_approval_date"
    },
    "qr_code": {
        "new": "approval_qr_code",
        "legacy": "custom_approval_qr_code"
    },
    "approval_url": {
        "new": "custom_approval_url",  # This stays the same
        "legacy": "custom_approval_url"
    }
}

def get_delivery_approval_status(delivery_note):
    """Get approval status using field mapping"""
    return get_standardized_field_value(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["approval_status"])

def get_delivery_signature(delivery_note):
    """Get digital signature using field mapping"""
    return get_standardized_field_value(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["digital_signature"])

def get_delivery_approved_by(delivery_note):
    """Get approved by using field mapping"""
    return get_standardized_field_value(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["approved_by"])

def get_delivery_approved_on(delivery_note):
    """Get approved on using field mapping"""
    return get_standardized_field_value(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["approved_on"])

def get_delivery_qr_code(delivery_note):
    """Get QR code using field mapping"""
    return get_standardized_field_value(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["qr_code"])

def set_delivery_approval_status(delivery_note, status):
    """Set approval status to both standardized and legacy fields"""
    set_field_values(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["approval_status"], status)

def set_delivery_signature(delivery_note, signature):
    """Set digital signature to both standardized and legacy fields"""
    set_field_values(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["digital_signature"], signature)

def set_delivery_approved_by(delivery_note, approved_by):
    """Set approved by to both standardized and legacy fields"""
    set_field_values(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["approved_by"], approved_by)

def set_delivery_approved_on(delivery_note, approved_on):
    """Set approved on to both standardized and legacy fields"""
    set_field_values(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["approved_on"], approved_on)

def set_delivery_qr_code(delivery_note, qr_code):
    """Set QR code to both standardized and legacy fields"""
    set_field_values(delivery_note, DELIVERY_NOTE_FIELD_MAPPING["qr_code"], qr_code)