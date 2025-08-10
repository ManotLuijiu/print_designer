"""
Debug endpoint to test the 403 fix
"""

import frappe

@frappe.whitelist()
def test_403_fix_endpoint():
    """
    Test endpoint to verify the 403 fix is working
    
    This can be called directly from the browser:
    /api/method/print_designer.utils.debug_403_fix.test_403_fix_endpoint
    """
    
    result = {
        "status": "success",
        "message": "403 fix test endpoint working",
        "tests": []
    }
    
    # Test 1: Check if erpnext_thailand is installed and monkey patching
    try:
        import erpnext_thailand.custom.print_utils as thailand_print_utils
        
        # Check if frappe.get_print is monkey patched
        if hasattr(frappe, 'get_print') and frappe.get_print == thailand_print_utils.get_print:
            result["tests"].append({
                "name": "ERPNext Thailand monkey patching",
                "status": "detected",
                "message": "frappe.get_print is monkey patched by erpnext_thailand"
            })
            
            # Check if custom field exists
            try:
                field_exists = frappe.db.get_value(
                    "Custom Field", 
                    {"dt": "Print Format", "fieldname": "add_comment_info"}, 
                    "name"
                )
                if field_exists:
                    result["tests"].append({
                        "name": "Custom field check",
                        "status": "exists",
                        "message": f"add_comment_info field exists: {field_exists}"
                    })
                else:
                    result["tests"].append({
                        "name": "Custom field check",
                        "status": "missing",
                        "message": "add_comment_info field missing (likely cause of 403)"
                    })
            except Exception as e:
                result["tests"].append({
                    "name": "Custom field check",
                    "status": "error",
                    "message": f"Error checking custom field: {str(e)}"
                })
                
        else:
            result["tests"].append({
                "name": "ERPNext Thailand monkey patching",
                "status": "not_applied",
                "message": "frappe.get_print is not monkey patched"
            })
            
    except ImportError:
        result["tests"].append({
            "name": "ERPNext Thailand",
            "status": "not_installed",
            "message": "erpnext_thailand app not installed"
        })
    except Exception as e:
        result["tests"].append({
            "name": "ERPNext Thailand check",
            "status": "error",
            "message": f"Error checking erpnext_thailand: {str(e)}"
        })
    
    # Test 2: Test safe PDF endpoints
    try:
        from print_designer.utils.safe_pdf_api import safe_download_pdf
        result["tests"].append({
            "name": "Safe PDF endpoints",
            "status": "available",
            "message": "Safe PDF endpoints are available"
        })
    except Exception as e:
        result["tests"].append({
            "name": "Safe PDF endpoints",
            "status": "error",
            "message": f"Error loading safe PDF endpoints: {str(e)}"
        })
    
    # Test 3: Test conflict detection
    try:
        from print_designer.utils.safe_pdf_api import check_third_party_conflicts
        conflicts = check_third_party_conflicts()
        
        result["tests"].append({
            "name": "Conflict detection",
            "status": "success",
            "message": f"Conflicts found: {conflicts['conflicts_found']}",
            "details": conflicts
        })
        
    except Exception as e:
        result["tests"].append({
            "name": "Conflict detection",
            "status": "error",
            "message": f"Error in conflict detection: {str(e)}"
        })
    
    # Test 4: Test a simple document
    try:
        # Find any Sales Invoice
        sales_invoice = frappe.get_value("Sales Invoice", {"docstatus": 1}, "name")
        
        if sales_invoice:
            result["tests"].append({
                "name": "Test document",
                "status": "found",
                "message": f"Test document available: {sales_invoice}"
            })
            
            # Test safe PDF generation
            try:
                from print_designer.utils.safe_pdf_api import safe_get_print_html
                html_result = safe_get_print_html(
                    doctype="Sales Invoice",
                    name=sales_invoice,
                    print_format="Standard"
                )
                
                if html_result and 'html' in html_result:
                    result["tests"].append({
                        "name": "Safe PDF generation",
                        "status": "success",
                        "message": f"Safe PDF generation working (HTML length: {len(html_result['html'])})"
                    })
                else:
                    result["tests"].append({
                        "name": "Safe PDF generation",
                        "status": "failed",
                        "message": "Safe PDF generation returned no HTML"
                    })
                    
            except Exception as e:
                result["tests"].append({
                    "name": "Safe PDF generation",
                    "status": "error",
                    "message": f"Error in safe PDF generation: {str(e)}"
                })
                
        else:
            result["tests"].append({
                "name": "Test document",
                "status": "not_found",
                "message": "No Sales Invoice found for testing"
            })
            
    except Exception as e:
        result["tests"].append({
            "name": "Test document",
            "status": "error",
            "message": f"Error finding test document: {str(e)}"
        })
    
    # Summary
    has_conflicts = any(test.get("status") == "detected" for test in result["tests"] if test["name"] == "ERPNext Thailand monkey patching")
    has_safe_endpoints = any(test.get("status") == "available" for test in result["tests"] if test["name"] == "Safe PDF endpoints")
    
    if has_conflicts and has_safe_endpoints:
        result["conclusion"] = "Conflicts detected but safe endpoints available - 403 errors should be resolved"
    elif has_conflicts and not has_safe_endpoints:
        result["conclusion"] = "Conflicts detected but safe endpoints not available - 403 errors may occur"
    elif not has_conflicts:
        result["conclusion"] = "No conflicts detected - standard PDF generation should work"
    else:
        result["conclusion"] = "Test results inconclusive"
    
    return result

@frappe.whitelist()
def test_user_specific_403():
    """
    Test the specific user's 403 error scenario
    
    This can be called directly from the browser:
    /api/method/print_designer.utils.debug_403_fix.test_user_specific_403
    """
    
    result = {
        "status": "success",
        "message": "Testing user's specific 403 error scenario",
        "url": "https://soeasy.bunchee.online/api/method/frappe.utils.print_format.download_pdf",
        "params": {
            "doctype": "Sales Invoice",
            "name": "ACC-SINV-2025-00002", 
            "format": "ใบกำกับภาษี",
            "_lang": "en"
        },
        "tests": []
    }
    
    # Test 1: Check if document exists
    try:
        doc_exists = frappe.db.exists("Sales Invoice", "ACC-SINV-2025-00002")
        result["tests"].append({
            "name": "Document exists",
            "status": "exists" if doc_exists else "not_found",
            "message": f"Document ACC-SINV-2025-00002 {'exists' if doc_exists else 'not found'}"
        })
    except Exception as e:
        result["tests"].append({
            "name": "Document exists",
            "status": "error",
            "message": f"Error checking document: {str(e)}"
        })
    
    # Test 2: Check if print format exists
    try:
        pf_exists = frappe.db.exists("Print Format", "ใบกำกับภาษี")
        result["tests"].append({
            "name": "Print format exists",
            "status": "exists" if pf_exists else "not_found",
            "message": f"Print format 'ใบกำกับภาษี' {'exists' if pf_exists else 'not found'}"
        })
    except Exception as e:
        result["tests"].append({
            "name": "Print format exists",
            "status": "error",
            "message": f"Error checking print format: {str(e)}"
        })
    
    # Test 3: Test direct PDF generation (this might cause 403)
    try:
        result_pdf = frappe.get_print(
            doctype="Sales Invoice",
            name="ACC-SINV-2025-00002",
            print_format="ใบกำกับภาษี",
            as_pdf=True
        )
        
        result["tests"].append({
            "name": "Direct PDF generation",
            "status": "success",
            "message": "Direct PDF generation successful"
        })
        
    except Exception as e:
        result["tests"].append({
            "name": "Direct PDF generation",
            "status": "error",
            "message": f"Direct PDF generation failed: {str(e)}"
        })
        
        # Check if this is the specific 403 error
        if "add_comment_info" in str(e):
            result["tests"].append({
                "name": "Error analysis",
                "status": "identified",
                "message": "Error is related to missing add_comment_info field - this confirms the 403 issue"
            })
    
    # Test 4: Test safe PDF generation
    try:
        from print_designer.utils.safe_pdf_api import safe_get_print_html
        
        safe_result = safe_get_print_html(
            doctype="Sales Invoice",
            name="ACC-SINV-2025-00002",
            print_format="ใบกำกับภาษี"
        )
        
        if safe_result and 'html' in safe_result:
            result["tests"].append({
                "name": "Safe PDF generation",
                "status": "success",
                "message": f"Safe PDF generation successful (HTML length: {len(safe_result['html'])})"
            })
        else:
            result["tests"].append({
                "name": "Safe PDF generation",
                "status": "failed",
                "message": "Safe PDF generation returned no HTML"
            })
            
    except Exception as e:
        result["tests"].append({
            "name": "Safe PDF generation",
            "status": "error",
            "message": f"Safe PDF generation failed: {str(e)}"
        })
    
    return result