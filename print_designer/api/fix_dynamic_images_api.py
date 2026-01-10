import frappe
from frappe import _

@frappe.whitelist()
def diagnose_and_fix_dynamic_images():
    """
    API endpoint to diagnose and fix Dynamic Images issues
    Returns detailed status and applies fixes
    """
    try:
        results = {
            "timestamp": frappe.utils.now(),
            "diagnosis": {},
            "fixes_applied": [],
            "next_steps": [],
            "success": True
        }
        
        # Diagnosis Phase
        results["diagnosis"] = run_diagnosis()
        
        # Fix Phase - only if issues are found
        if results["diagnosis"]["issues_found"]:
            results["fixes_applied"] = apply_fixes()
        
        # Next Steps
        results["next_steps"] = [
            "Hard refresh your browser (Ctrl+F5)",
            "Go to Company DocType and upload signature images in the signature fields",
            "Check Print Designer > Dynamic Images again",
            "For Target Signature Field: Go to 'Signature Basic Information' DocType"
        ]
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Error in diagnose_and_fix_dynamic_images: {str(e)}")
        return {"success": False, "error": str(e)}

def run_diagnosis():
    """Run comprehensive diagnosis of Dynamic Images"""
    diagnosis = {
        "signature_fields_status": {},
        "image_fields_count": 0,
        "signature_fields_count": 0,
        "companies_with_signatures": 0,
        "enhancement_status": False,
        "issues_found": []
    }
    
    # Check signature field installation
    try:
        from print_designer.api.signature_field_installer import check_signature_fields_status
        status = check_signature_fields_status()
        
        if status.get("success"):
            diagnosis["signature_fields_status"] = status["results"]
            
            # Count missing fields
            missing_count = 0
            for doctype, info in status["results"].items():
                if info["status"] != "installed":
                    missing_fields = [f for f in info["fields"] if not f["installed"]]
                    missing_count += len(missing_fields)
            
            if missing_count > 0:
                diagnosis["issues_found"].append(f"{missing_count} signature fields not installed")
        else:
            diagnosis["issues_found"].append("Could not check signature field status")
    except Exception as e:
        diagnosis["issues_found"].append(f"Signature field check failed: {str(e)}")
    
    # Check image fields API
    try:
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        image_fields = get_image_docfields()
        diagnosis["image_fields_count"] = len(image_fields)
        
        signature_fields = [f for f in image_fields if 'signature' in f.get('fieldname', '').lower()]
        diagnosis["signature_fields_count"] = len(signature_fields)
        
        if len(signature_fields) == 0:
            diagnosis["issues_found"].append("No signature fields found in Dynamic Images")
    except Exception as e:
        diagnosis["issues_found"].append(f"Image fields API failed: {str(e)}")
    
    # Check companies with signatures
    try:
        companies = frappe.get_all("Company", limit=10)
        for company in companies:
            doc = frappe.get_doc("Company", company.name)
            signature_fields = ["ceo_signature", "authorized_signature_1", "authorized_signature_2"]
            
            has_signatures = any(hasattr(doc, field) and getattr(doc, field) for field in signature_fields)
            if has_signatures:
                diagnosis["companies_with_signatures"] += 1
    except Exception as e:
        diagnosis["issues_found"].append(f"Error checking company signatures: {str(e)}")
    
    # Check signature enhancements (Target Signature Field)
    try:
        enhanced_fields = frappe.db.get_all("Custom Field", {
            "dt": "Signature Basic Information",
            "fieldname": ["in", ["target_doctype", "target_signature_field"]]
        })
        
        diagnosis["enhancement_status"] = len(enhanced_fields) >= 2
        if not diagnosis["enhancement_status"]:
            diagnosis["issues_found"].append("Target Signature Field enhancement not installed")
    except Exception:
        diagnosis["issues_found"].append("Could not check signature enhancements")
    
    return diagnosis

def apply_fixes():
    """Apply fixes for identified issues"""
    fixes_applied = []
    
    # Fix 1: Install signature fields
    try:
        from print_designer.api.signature_field_installer import install_signature_fields
        result = install_signature_fields()
        
        if result.get("success"):
            fixes_applied.append(f"Installed signature fields for {len(result.get('doctypes', []))} DocTypes")
    except Exception as e:
        frappe.log_error(f"Error installing signature fields: {str(e)}")
    
    # Fix 2: Install signature enhancements (optional module)
    try:
        from print_designer.api.safe_install import safe_install_signature_enhancements
        result = safe_install_signature_enhancements()

        if result.get("success"):
            fixes_applied.append("Signature enhancements (Target Signature Field) installed")
    except ImportError:
        # safe_install module is disabled/removed - skip silently
        pass
    except Exception as e:
        frappe.log_error(f"Error installing signature enhancements: {str(e)}")
    
    # Fix 3: Clear cache
    try:
        frappe.clear_cache()
        fixes_applied.append("Cache cleared")
    except Exception as e:
        frappe.log_error(f"Error clearing cache: {str(e)}")
    
    # Fix 4: Refresh dynamic images
    try:
        from print_designer.api.refresh_dynamic_images import refresh_dynamic_images
        result = refresh_dynamic_images()
        
        if result.get("success"):
            fixes_applied.append("Dynamic images cache refreshed")
    except Exception as e:
        frappe.log_error(f"Error refreshing dynamic images: {str(e)}")
    
    return fixes_applied

@frappe.whitelist()
def get_signature_field_locations():
    """
    Help users find where Target Signature Field is located
    """
    return {
        "target_signature_field_location": {
            "doctype": "Signature Basic Information",
            "menu_path": "Settings > Print Designer > Signature Basic Information",
            "description": "Target Signature Field is in the Signature Basic Information form, not in Dynamic Images dialog",
            "fields_available": [
                "Target DocType - Select which DocType contains signature field",
                "Target Signature Field - Select specific signature field",
                "Auto-populate Target Field - Enable automatic sync"
            ]
        },
        "dynamic_images_purpose": {
            "location": "Print Designer > Add Image Element > Dynamic Images",
            "description": "Dynamic Images shows available image fields from documents for insertion into print formats",
            "shows": "All Attach Image and Image fields from linked DocTypes"
        },
        "how_to_upload_signatures": {
            "step_1": "Go to Company DocType",
            "step_2": "Open any company record",
            "step_3": "Look for signature fields (CEO Signature, Authorized Signature 1, etc.)",
            "step_4": "Upload signature images to these fields",
            "step_5": "Signatures will then appear in Dynamic Images as 'linked'"
        }
    }

@frappe.whitelist() 
def create_sample_company_signatures():
    """
    Create sample signature placeholders for testing
    """
    try:
        # Get first company
        company = frappe.get_all("Company", limit=1)
        if not company:
            return {"error": "No companies found"}
        
        company_doc = frappe.get_doc("Company", company[0].name)
        
        # Check if signature fields exist
        signature_fields = ["ceo_signature", "authorized_signature_1", "authorized_signature_2"]
        existing_signatures = {}
        
        for field in signature_fields:
            if hasattr(company_doc, field):
                existing_signatures[field] = getattr(company_doc, field)
        
        return {
            "success": True,
            "company": company_doc.name,
            "signature_fields_available": list(existing_signatures.keys()),
            "current_values": existing_signatures,
            "instructions": "Upload actual signature images to these fields to see them in Dynamic Images"
        }
        
    except Exception as e:
        return {"error": str(e)}