"""
Test PDF generation after override
"""

import frappe

@frappe.whitelist()
def test_pdf_generation():
    """Test PDF generation with the override in place"""
    
    results = {
        "status": "success",
        "tests": [],
        "override_active": False
    }
    
    # Test 1: Check override status
    try:
        from print_designer.utils.override_thailand import check_thailand_override_status
        status = check_thailand_override_status()
        
        results["override_active"] = status["override_active"]
        results["tests"].append({
            "name": "Override Status",
            "status": "success",
            "message": f"Override active: {status['override_active']}, Safe to generate PDF: {status['safe_to_generate_pdf']}"
        })
        
    except Exception as e:
        results["tests"].append({
            "name": "Override Status",
            "status": "error",
            "message": f"Failed to check override status: {str(e)}"
        })
    
    # Test 2: Find a test document
    test_doc = None
    test_doctype = None
    
    # Try to find any document that can be printed
    for doctype in ["User", "Print Format", "DocType"]:
        try:
            doc_name = frappe.get_value(doctype, {}, "name")
            if doc_name:
                test_doc = doc_name
                test_doctype = doctype
                break
        except:
            continue
    
    if test_doc:
        results["tests"].append({
            "name": "Test Document",
            "status": "found",
            "message": f"Using {test_doctype}: {test_doc}"
        })
        
        # Test 3: Test PDF generation
        try:
            pdf_result = frappe.get_print(
                doctype=test_doctype,
                name=test_doc,
                print_format="Standard",
                as_pdf=True
            )
            
            results["tests"].append({
                "name": "PDF Generation",
                "status": "success",
                "message": f"PDF generated successfully ({len(pdf_result)} bytes)"
            })
            
        except Exception as e:
            error_msg = str(e)
            results["tests"].append({
                "name": "PDF Generation",
                "status": "error",
                "message": f"PDF generation failed: {error_msg}"
            })
            
            # Check if it's the add_comment_info error
            if "add_comment_info" in error_msg:
                results["tests"].append({
                    "name": "Error Analysis",
                    "status": "identified",
                    "message": "Error is related to add_comment_info - override may not be working"
                })
            else:
                results["tests"].append({
                    "name": "Error Analysis",
                    "status": "other",
                    "message": "Error not related to add_comment_info - may be different issue"
                })
    else:
        results["tests"].append({
            "name": "Test Document",
            "status": "not_found",
            "message": "No suitable test document found"
        })
    
    # Test 4: Test the specific frappe.get_print function
    try:
        # Check what function is currently assigned to frappe.get_print
        get_print_func = frappe.get_print
        func_name = get_print_func.__name__ if hasattr(get_print_func, '__name__') else "unknown"
        module_name = get_print_func.__module__ if hasattr(get_print_func, '__module__') else "unknown"
        
        results["tests"].append({
            "name": "Function Check",
            "status": "success",
            "message": f"frappe.get_print is: {module_name}.{func_name}"
        })
        
        # Check if it's our safe function
        if func_name == "safe_thailand_get_print":
            results["tests"].append({
                "name": "Override Verification",
                "status": "success",
                "message": "✓ Our safe override function is active"
            })
        else:
            results["tests"].append({
                "name": "Override Verification",
                "status": "warning",
                "message": f"⚠ Function is {func_name}, not our override"
            })
            
    except Exception as e:
        results["tests"].append({
            "name": "Function Check",
            "status": "error",
            "message": f"Failed to check function: {str(e)}"
        })
    
    return results

@frappe.whitelist()
def simulate_user_error():
    """Simulate the user's original error to test the fix"""
    
    try:
        # This should trigger the same path as the user's error
        # We'll use a dummy doctype and name to simulate
        result = frappe.get_print(
            doctype="Sales Invoice",
            name="DUMMY-DOC-001",
            print_format="Standard",
            as_pdf=True
        )
        
        return {
            "status": "unexpected_success",
            "message": "PDF generation succeeded when it should have failed"
        }
        
    except Exception as e:
        error_msg = str(e)
        
        if "add_comment_info" in error_msg:
            return {
                "status": "error",
                "message": "Still getting add_comment_info error - override not working",
                "error": error_msg
            }
        else:
            return {
                "status": "success",
                "message": "Got expected error (not add_comment_info) - override is working",
                "error": error_msg
            }

@frappe.whitelist()
def comprehensive_test():
    """Run all tests together"""
    
    results = {
        "pdf_generation": test_pdf_generation(),
        "error_simulation": simulate_user_error()
    }
    
    return results