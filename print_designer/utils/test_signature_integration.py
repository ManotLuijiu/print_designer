"""
Test script to verify signature field integration with Print Designer
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from print_designer.signature_fields import get_signature_fields

@frappe.whitelist()
def test_signature_integration():
    """Test if signature fields are properly integrated"""
    
    results = {
        "signature_fields_available": False,
        "image_fields_include_signatures": False,
        "test_company_signatures": False,
        "test_sales_invoice_signatures": False,
        "recommendations": []
    }
    
    try:
        # 1. Check if signature fields are defined
        signature_fields = get_signature_fields()
        results["signature_fields_available"] = len(signature_fields) > 0
        
        # 2. Check if image fields API includes signatures
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        image_fields = get_image_docfields()
        
        # Look for signature fields in image fields
        signature_image_fields = [field for field in image_fields if 'signature' in field.get('fieldname', '').lower()]
        results["image_fields_include_signatures"] = len(signature_image_fields) > 0
        
        # 3. Test specific doctype fields
        company_signature_fields = [field for field in image_fields if field.get('parent') == 'Company' and 'signature' in field.get('fieldname', '').lower()]
        results["test_company_signatures"] = len(company_signature_fields) > 0
        
        sales_invoice_signature_fields = [field for field in image_fields if field.get('parent') == 'Sales Invoice' and 'signature' in field.get('fieldname', '').lower()]
        results["test_sales_invoice_signatures"] = len(sales_invoice_signature_fields) > 0
        
        # 4. Provide recommendations
        if not results["signature_fields_available"]:
            results["recommendations"].append("Signature fields configuration not found")
        
        if not results["image_fields_include_signatures"]:
            results["recommendations"].append("Signature fields not appearing in image fields API - may need migration")
        
        if not results["test_company_signatures"]:
            results["recommendations"].append("Company signature fields not found in image fields")
            
        if not results["test_sales_invoice_signatures"]:
            results["recommendations"].append("Sales Invoice signature fields not found in image fields")
        
        # 5. Additional info
        results["total_signature_fields_defined"] = len(signature_fields)
        results["total_image_fields_found"] = len(image_fields)
        results["signature_fields_in_image_api"] = len(signature_image_fields)
        
        # List available signature fields
        results["available_signature_fields"] = []
        for doctype, fields in signature_fields.items():
            for field in fields:
                results["available_signature_fields"].append({
                    "doctype": doctype,
                    "fieldname": field["fieldname"],
                    "label": field["label"]
                })
        
        # List found signature image fields
        results["found_signature_image_fields"] = signature_image_fields
        
    except Exception as e:
        results["error"] = str(e)
    
    return results

@frappe.whitelist()
def enhance_signature_ui():
    """Enhance the signature UI by adding signature-specific features"""
    
    suggestions = {
        "vue_component_enhancements": [
            "Add signature icon to toolbar",
            "Filter signature fields in AppImageModal",
            "Add signature-specific styling options",
            "Create signature selection helper"
        ],
        "backend_enhancements": [
            "Ensure signature fields are properly discovered by get_image_docfields()",
            "Add signature field validation",
            "Create signature management API endpoints"
        ],
        "template_enhancements": [
            "Improve signature rendering in Jinja templates",
            "Add signature positioning helpers",
            "Support for multiple signature workflows"
        ]
    }
    
    return suggestions

@frappe.whitelist()
def get_signature_fields_for_doctype(doctype):
    """Get signature fields for a specific doctype"""
    
    try:
        from print_designer.signature_fields import get_signature_fields_for_doctype
        return get_signature_fields_for_doctype(doctype)
    except Exception as e:
        return {"error": str(e)}