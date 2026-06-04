"""
Thai Address Formatter - Utility for formatting Thai addresses correctly.

This module provides functions to format addresses in Thai administrative hierarchy:
- ตำบล (Tambon/Sub-district) -> city field
- อำเภอ (Amphoe/District) -> county field
- จังหวัด (Province) -> state field

Smart country detection:
- If country == "Thailand": Show Thai labels (ตำบล, อำเภอ, จังหวัด, รหัสไปรษณีย์)
- If country != "Thailand": Show default format (no Thai labels)

Usage in Print Designer Jinja:
    {{ frappe.utils.thai_format_address(doc.address_name) }}

Or in Python:
    from print_designer.utils.thai_address_formatter import thai_address_display
    address_html = thai_address_display(address_name)
"""

import frappe


def thai_address_display(address_name: str) -> str:
    """
    Get formatted Thai address with Thai labels (for Thailand) or default format.
    
    Args:
        address_name: Name of the Address document
        
    Returns:
        HTML formatted address string with Thai labels for Thailand addresses
    """
    if not address_name:
        return ""
    
    addr = frappe.get_doc("Address", address_name)
    return thai_render_address(addr.as_dict())


def thai_render_address(address_dict: dict) -> str:
    """
    Render address dict with Thai administrative hierarchy and labels.
    
    Output format (if country == "Thailand"):
        142/191 หมู่ 7
        ตำบล: กะทู้
        อำเภอ: กะทู้
        จังหวัด: ภูเก็ต
        รหัสไปรษณีย์: 83120
        Thailand
    
    Output format (if country != "Thailand"):
        123 Main Street
        Suite 100
        California
        90210
        United States
    
    Args:
        address_dict: Dictionary with Address fields
        
    Returns:
        HTML formatted address string with Thai labels (for Thailand) or default format
    """
    if not address_dict:
        return ""
    
    is_thailand = address_dict.get("country") == "Thailand"
    
    lines = []
    
    # Address lines (no label)
    if address_dict.get("address_line1"):
        lines.append(address_dict["address_line1"])
    
    if address_dict.get("address_line2"):
        lines.append(address_dict["address_line2"])
    
    if is_thailand:
        # Thai format with labels
        if address_dict.get("city"):
            lines.append(f"ตำบล: {address_dict['city']}")
        if address_dict.get("county"):
            lines.append(f"อำเภอ: {address_dict['county']}")
        if address_dict.get("state"):
            lines.append(f"จังหวัด: {address_dict['state']}")
        if address_dict.get("pincode"):
            lines.append(f"รหัสไปรษณีย์: {address_dict['pincode']}")
    else:
        # Default format (no Thai labels)
        if address_dict.get("city"):
            lines.append(address_dict["city"])
        if address_dict.get("county"):
            lines.append(address_dict["county"])
        if address_dict.get("state"):
            lines.append(address_dict["state"])
        if address_dict.get("pincode"):
            lines.append(address_dict["pincode"])
    
    # Country
    if address_dict.get("country"):
        lines.append(address_dict["country"])
    
    # Contact info
    contact_parts = []
    if address_dict.get("phone"):
        contact_parts.append(f"Phone: {address_dict['phone']}")
    if address_dict.get("fax"):
        contact_parts.append(f"Fax: {address_dict['fax']}")
    if address_dict.get("email_id"):
        contact_parts.append(f"Email: {address_dict['email_id']}")
    
    # Build HTML output
    html = "<br>".join(lines)
    
    if contact_parts:
        html += "<br><br>" + "<br>".join(contact_parts)
    
    return html


def get_thai_address_components(address_name: str) -> dict:
    """
    Get address components as a dictionary with Thai labels.
    
    Args:
        address_name: Name of the Address document
        
    Returns:
        Dictionary with Thai labels and values
    """
    if not address_name:
        return {}
    
    addr = frappe.get_doc("Address", address_name)
    
    return {
        "address_line1": addr.address_line1,
        "address_line2": addr.address_line2,
        "tambon": addr.city,        # ตำบล
        "amphoe": addr.county,     # อำเภอ
        "province": addr.state,    # จังหวัด
        "postal_code": addr.pincode,
        "country": addr.country,
        "phone": addr.phone,
        "fax": addr.fax,
        "email": addr.email_id,
    }