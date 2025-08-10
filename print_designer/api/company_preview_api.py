"""
Company Preview API - Get stamps and signatures for company preview
"""

import frappe


@frappe.whitelist()
def get_company_stamps_and_signatures(company):
    """
    Get all stamps and signatures related to a company for preview.
    Uses Signature Basic Information as the primary source for both stamps and signatures.
    
    Args:
        company (str): Company name
        
    Returns:
        dict: Company stamps and signatures data
    """
    if not company:
        return {"stamps": [], "signatures": []}
    
    # Get Company Stamps from Signature Basic Information with category "Company Stamp"
    signature_stamps = frappe.get_all("Signature Basic Information", 
        filters={
            "company": company, 
            "is_active": 1, 
            "signature_category": "Company Stamp"
        },
        fields=[
            "name", "signature_name", "signature_image", "stamp_type", 
            "stamp_authority", "stamp_number", "creation", "signature_title"
        ],
        order_by="stamp_type, creation desc"
    )
    
    # Format stamps for consistent response
    stamps = []
    for stamp in signature_stamps:
        stamps.append({
            "name": stamp.name,
            "title": stamp.signature_name,
            "stamp_image": stamp.signature_image,
            "stamp_type": stamp.stamp_type or "Company Stamp",
            "usage_purpose": stamp.stamp_authority or "General",
            "description": f"Stamp #{stamp.stamp_number}" if stamp.stamp_number else "",
            "creation": stamp.creation
        })
    
    # Get Digital Signatures (if DocType exists)
    digital_signatures = []
    if frappe.db.exists("DocType", "Digital Signature"):
        try:
            digital_signatures = frappe.get_all("Digital Signature", 
                filters={"company": company, "is_active": 1},
                fields=["name", "title", "signature_image", "department", "designation", "description", "creation"],
                order_by="creation desc"
            )
        except Exception:
            # DocType might not exist or have different fields
            digital_signatures = []
    
    # Get Basic Signatures (category "Signature")
    basic_signatures = frappe.get_all("Signature Basic Information", 
        filters={
            "company": company, 
            "is_active": 1, 
            "signature_category": "Signature"
        },
        fields=["name", "signature_name", "signature_title", "signature_image", "creation"],
        order_by="creation desc"
    )
    
    # Format signatures for consistent response
    all_signatures = []
    
    # Add digital signatures (if any)
    for sig in digital_signatures:
        subtitle_parts = []
        if sig.get('designation'):
            subtitle_parts.append(sig.designation)
        if sig.get('department'):
            subtitle_parts.append(sig.department)
        subtitle = " - ".join(subtitle_parts)
        
        all_signatures.append({
            "name": sig.name,
            "title": sig.title,
            "subtitle": subtitle,
            "signature_image": sig.signature_image,
            "source_type": "Digital Signature",
            "creation": sig.creation
        })
    
    # Add basic signatures
    for sig in basic_signatures:
        subtitle = sig.signature_title if sig.signature_title else ""
        all_signatures.append({
            "name": sig.name,
            "title": sig.signature_name,
            "subtitle": subtitle,
            "signature_image": sig.signature_image,
            "source_type": "Signature Basic Information",
            "creation": sig.creation
        })
    
    # Sort signatures by creation date
    all_signatures.sort(key=lambda x: x["creation"], reverse=True)
    
    return {
        "stamps": stamps,
        "signatures": all_signatures,
        "summary": {
            "total_stamps": len(stamps),
            "total_signatures": len(all_signatures),
            "company": company
        }
    }


@frappe.whitelist()
def get_stamp_preview_html(stamp_name):
    """
    Get HTML preview for a stamp from Signature Basic Information.
    
    Args:
        stamp_name (str): Signature Basic Information name (for Company Stamp category)
        
    Returns:
        str: HTML preview
    """
    try:
        stamp = frappe.get_doc("Signature Basic Information", stamp_name)
        
        # Verify this is actually a company stamp
        if stamp.signature_category != "Company Stamp":
            return "<p>This is not a company stamp</p>"
        
        if not stamp.signature_image:
            return "<p>No image available</p>"
        
        html = f"""
        <div class="stamp-preview" style="text-align: center; padding: 15px;">
            <div class="stamp-image-container" style="margin-bottom: 10px;">
                <img src="{stamp.signature_image}" 
                     alt="{stamp.signature_name}" 
                     style="max-width: 150px; max-height: 150px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />
            </div>
            <div class="stamp-info">
                <h5 style="margin: 8px 0 4px 0; color: #333;">{stamp.signature_name}</h5>
                <p style="margin: 4px 0; color: #666; font-size: 12px;">
                    <strong>Type:</strong> {stamp.stamp_type or 'N/A'} | 
                    <strong>Authority:</strong> {stamp.stamp_authority or 'General'}
                </p>
                {f'<p style="margin: 4px 0; color: #888; font-size: 11px; font-style: italic;">Stamp #{stamp.stamp_number}</p>' if stamp.stamp_number else ''}
                {f'<p style="margin: 4px 0; color: #888; font-size: 11px;">Title: {stamp.signature_title}</p>' if stamp.signature_title else ''}
            </div>
        </div>
        """
        
        return html
    except frappe.DoesNotExistError:
        return "<p>Stamp not found</p>"
    except Exception as e:
        frappe.log_error(f"Error in get_stamp_preview_html: {str(e)}")
        return "<p>Error loading stamp preview</p>"


@frappe.whitelist()
def get_signature_preview_html(signature_name, source_type):
    """
    Get HTML preview for a signature.
    
    Args:
        signature_name (str): Signature document name
        source_type (str): Source DocType ('Digital Signature' or 'Signature Basic Information')
        
    Returns:
        str: HTML preview
    """
    signature = frappe.get_doc(source_type, signature_name)
    
    # Get image field based on DocType
    image_field = "signature_image"
    title_field = "title" if source_type == "Digital Signature" else "signature_name"
    
    signature_image = getattr(signature, image_field, None)
    signature_title = getattr(signature, title_field, "Untitled")
    
    if not signature_image:
        return "<p>No signature image available</p>"
    
    # Build subtitle based on DocType
    if source_type == "Digital Signature":
        subtitle_parts = []
        if signature.designation:
            subtitle_parts.append(signature.designation)
        if signature.department:
            subtitle_parts.append(signature.department)
        subtitle = " - ".join(subtitle_parts)
    else:
        subtitle_parts = []
        if signature.signature_title:
            subtitle_parts.append(signature.signature_title)
        if signature.signature_category:
            subtitle_parts.append(f"({signature.signature_category})")
        subtitle = " ".join(subtitle_parts)
    
    html = f"""
    <div class="signature-preview" style="text-align: center; padding: 15px;">
        <div class="signature-image-container" style="margin-bottom: 10px;">
            <img src="{signature_image}" 
                 alt="{signature_title}" 
                 style="max-width: 200px; max-height: 100px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background: white; padding: 5px;" />
        </div>
        <div class="signature-info">
            <h5 style="margin: 8px 0 4px 0; color: #333;">{signature_title}</h5>
            {f'<p style="margin: 4px 0; color: #666; font-size: 12px;">{subtitle}</p>' if subtitle else ''}
            <p style="margin: 4px 0; color: #888; font-size: 11px;">
                <strong>Source:</strong> {source_type}
            </p>
            {f'<p style="margin: 4px 0; color: #888; font-size: 11px; font-style: italic;">{signature.description}</p>' if hasattr(signature, 'description') and signature.description else ''}
        </div>
    </div>
    """
    
    return html