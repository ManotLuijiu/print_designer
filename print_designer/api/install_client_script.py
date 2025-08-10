import frappe
import os
from frappe import _


@frappe.whitelist()
def install_signature_client_script():
    """
    Install the client script for Signature Basic Information DocType
    This script populates the Target Signature Field dropdown options
    
    Returns:
        dict: Installation result
    """
    try:
        # Get the client script content
        script_path = frappe.get_app_path('print_designer', 'client_scripts', 'signature_basic_information.js')
        
        if not os.path.exists(script_path):
            return {"error": f"Client script file not found at {script_path}"}
        
        with open(script_path, 'r') as f:
            script_content = f.read()

        # Check if client script already exists
        existing_script = frappe.db.exists('Client Script', {
            'dt': 'Signature Basic Information',
            'view': 'Form'
        })

        if existing_script:
            # Update existing script
            doc = frappe.get_doc('Client Script', existing_script)
            doc.script = script_content
            doc.enabled = 1
            doc.save()
            message = f"Updated existing client script: {existing_script}"
        else:
            # Create new client script
            doc = frappe.new_doc('Client Script')
            doc.name = 'Signature Basic Information - Form Script'
            doc.dt = 'Signature Basic Information'
            doc.view = 'Form'
            doc.script = script_content
            doc.enabled = 1
            doc.insert()
            message = f"Created new client script: {doc.name}"

        frappe.db.commit()
        
        return {
            "success": True,
            "message": message,
            "client_script_name": doc.name,
            "doctype": "Signature Basic Information"
        }

    except Exception as e:
        frappe.log_error(f"Error installing signature client script: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def check_client_script_status():
    """
    Check if the client script is properly installed
    
    Returns:
        dict: Status information
    """
    try:
        # Check if client script exists
        client_scripts = frappe.get_all(
            'Client Script',
            filters={'dt': 'Signature Basic Information'},
            fields=['name', 'enabled', 'view', 'modified']
        )
        
        return {
            "success": True,
            "client_scripts_found": len(client_scripts),
            "client_scripts": client_scripts,
            "status": "installed" if client_scripts else "missing"
        }
        
    except Exception as e:
        frappe.log_error(f"Error checking client script status: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def fix_signature_dropdown():
    """
    Complete fix for the signature dropdown issue
    This function:
    1. Installs the client script
    2. Clears cache
    3. Verifies the fix
    
    Returns:
        dict: Fix results
    """
    try:
        results = {
            "timestamp": frappe.utils.now(),
            "steps": [],
            "success": True
        }
        
        # Step 1: Install client script
        script_result = install_signature_client_script()
        results["steps"].append({
            "step": "Install Client Script",
            "result": script_result
        })
        
        # Step 2: Clear cache
        frappe.clear_cache()
        results["steps"].append({
            "step": "Clear Cache",
            "result": {"success": True, "message": "Cache cleared successfully"}
        })
        
        # Step 3: Verify API still works
        from print_designer.api.signature_field_options import get_signature_field_options_string
        options_string = get_signature_field_options_string()
        options_count = len(options_string.split('\n')) if options_string else 0
        
        results["steps"].append({
            "step": "Verify API",
            "result": {
                "success": True,
                "message": f"API returns {options_count} signature field options",
                "options_available": options_count > 0
            }
        })
        
        # Overall success
        results["success"] = all(
            step["result"].get("success", False) for step in results["steps"]
        )
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Error fixing signature dropdown: {str(e)}")
        return {"error": str(e), "success": False}