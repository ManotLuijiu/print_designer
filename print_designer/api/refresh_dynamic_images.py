import frappe


@frappe.whitelist()
def refresh_dynamic_images():
    """
    Clear cache and refresh dynamic images for Print Designer
    This forces the frontend to reload the imageDocFields
    """
    try:
        # Clear relevant caches
        frappe.clear_cache()
        
        # Get fresh image fields
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        image_fields = get_image_docfields()
        
        # Count signature fields for verification
        signature_fields = [
            f for f in image_fields 
            if 'signature' in f.get('fieldname', '').lower()
        ]
        
        return {
            "success": True,
            "message": "Dynamic images cache refreshed",
            "total_image_fields": len(image_fields),
            "signature_fields_available": len(signature_fields),
            "refresh_instructions": "Please hard refresh your browser (Ctrl+F5) to see updated Dynamic Images",
            "signature_examples": [
                f"{f.get('parent')}.{f.get('fieldname')} ({f.get('label')})" 
                for f in signature_fields[:5]
            ]
        }
        
    except Exception as e:
        frappe.log_error(f"Error refreshing dynamic images: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def verify_signatures_in_print_designer():
    """
    Complete verification that signatures will show in Print Designer
    """
    try:
        results = {
            "timestamp": frappe.utils.now(),
            "checks": [],
            "success": True
        }
        
        # Check 1: Custom fields installed
        company_sigs = frappe.db.count("Custom Field", {
            "dt": "Company", 
            "fieldtype": "Attach Image",
            "fieldname": ["like", "%signature%"]
        })
        
        results["checks"].append({
            "check": "Company Signature Fields",
            "status": "✅ PASS" if company_sigs > 0 else "❌ FAIL",
            "count": company_sigs
        })
        
        # Check 2: Image fields API working
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        image_fields = get_image_docfields()
        signature_fields = [f for f in image_fields if 'signature' in f.get('fieldname', '').lower()]
        
        results["checks"].append({
            "check": "API Returns Signature Fields", 
            "status": "✅ PASS" if len(signature_fields) > 0 else "❌ FAIL",
            "count": len(signature_fields)
        })
        
        # Check 3: Sample signature data
        sample_signature_data = []
        for field in signature_fields[:3]:
            try:
                # Try to get sample data from the parent DocType
                parent_doctype = field.get('parent')
                if parent_doctype == 'Company':
                    sample_docs = frappe.get_all(parent_doctype, limit=1)
                    if sample_docs:
                        doc = frappe.get_doc(parent_doctype, sample_docs[0].name)
                        field_value = getattr(doc, field.get('fieldname'), None)
                        sample_signature_data.append({
                            "doctype": parent_doctype,
                            "field": field.get('fieldname'),
                            "has_value": bool(field_value),
                            "value_preview": field_value[:100] if field_value else None
                        })
            except Exception:
                continue
        
        results["checks"].append({
            "check": "Sample Signature Data",
            "status": "ℹ️ INFO",
            "data": sample_signature_data
        })
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Error verifying signatures in print designer: {str(e)}")
        return {"error": str(e)}