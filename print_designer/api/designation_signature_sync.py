import frappe
from frappe import _
from typing import Dict, List, Optional

@frappe.whitelist()
def sync_designation_signatures():
    """
    Sync signatures between Designation, Employee, and User DocTypes
    This creates a comprehensive signature management system
    """
    try:
        results = {
            "designations_updated": 0,
            "employees_synced": 0,
            "users_synced": 0,
            "sync_mappings": [],
            "errors": [],
            "success": True
        }
        
        # Get all employees with designations
        employees = frappe.db.sql("""
            SELECT 
                e.name as employee_name,
                e.designation,
                e.user_id,
                e.signature_image as employee_signature,
                d.designation_signature,
                u.signature_image as user_signature
            FROM `tabEmployee` e
            LEFT JOIN `tabDesignation` d ON e.designation = d.name
            LEFT JOIN `tabUser` u ON e.user_id = u.name
            WHERE e.designation IS NOT NULL
        """, as_dict=True)
        
        for emp in employees:
            sync_mapping = {
                "employee": emp.employee_name,
                "designation": emp.designation,
                "user_id": emp.user_id,
                "actions_taken": []
            }
            
            try:
                # Priority order for signature sync:
                # 1. Employee signature (highest priority)
                # 2. User signature 
                # 3. Designation signature (fallback)
                
                primary_signature = None
                signature_source = None
                
                if emp.employee_signature:
                    primary_signature = emp.employee_signature
                    signature_source = "employee"
                elif emp.user_signature:
                    primary_signature = emp.user_signature
                    signature_source = "user"
                elif emp.designation_signature:
                    primary_signature = emp.designation_signature
                    signature_source = "designation"
                
                if primary_signature:
                    # Sync to designation if empty
                    if not emp.designation_signature and signature_source != "designation":
                        frappe.db.set_value("Designation", emp.designation, "designation_signature", primary_signature)
                        sync_mapping["actions_taken"].append(f"Updated designation signature from {signature_source}")
                        results["designations_updated"] += 1
                    
                    # Sync to employee if empty
                    if not emp.employee_signature and signature_source != "employee":
                        frappe.db.set_value("Employee", emp.employee_name, "signature_image", primary_signature)
                        sync_mapping["actions_taken"].append(f"Updated employee signature from {signature_source}")
                        results["employees_synced"] += 1
                    
                    # Sync to user if empty and user exists
                    if emp.user_id and not emp.user_signature and signature_source != "user":
                        frappe.db.set_value("User", emp.user_id, "signature_image", primary_signature)
                        sync_mapping["actions_taken"].append(f"Updated user signature from {signature_source}")
                        results["users_synced"] += 1
                
                if sync_mapping["actions_taken"]:
                    results["sync_mappings"].append(sync_mapping)
                    
            except Exception as e:
                error_msg = f"Error syncing {emp.employee_name}: {str(e)}"
                results["errors"].append(error_msg)
                frappe.log_error(error_msg, "Signature Sync Error")
        
        # Commit all changes
        frappe.db.commit()
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Error in sync_designation_signatures: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_signature_hierarchy(employee_name=None, user_id=None, designation=None):
    """
    Get signature hierarchy for a specific employee, user, or designation
    Shows which signatures are available and their priority order
    """
    try:
        if employee_name:
            # Get by employee
            emp = frappe.get_doc("Employee", employee_name)
            user_id = emp.user_id
            designation = emp.designation
        elif user_id:
            # Get by user
            emp = frappe.db.get_value("Employee", {"user_id": user_id}, 
                                     ["name", "designation"], as_dict=True)
            if emp:
                employee_name = emp.name
                designation = emp.designation
        
        hierarchy = {
            "employee_name": employee_name,
            "user_id": user_id,
            "designation": designation,
            "signatures": {},
            "priority_order": [],
            "recommended_signature": None
        }
        
        # Get signatures from each source
        if employee_name:
            emp_sig = frappe.db.get_value("Employee", employee_name, "signature_image")
            if emp_sig:
                hierarchy["signatures"]["employee"] = emp_sig
                hierarchy["priority_order"].append("employee")
        
        if user_id:
            user_sig = frappe.db.get_value("User", user_id, "signature_image")
            if user_sig:
                hierarchy["signatures"]["user"] = user_sig
                hierarchy["priority_order"].append("user")
        
        if designation:
            des_sig = frappe.db.get_value("Designation", designation, "designation_signature")
            if des_sig:
                hierarchy["signatures"]["designation"] = des_sig
                hierarchy["priority_order"].append("designation")
        
        # Set recommended signature (highest priority available)
        if hierarchy["priority_order"]:
            hierarchy["recommended_signature"] = hierarchy["signatures"][hierarchy["priority_order"][0]]
        
        return hierarchy
        
    except Exception as e:
        frappe.log_error(f"Error in get_signature_hierarchy: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def auto_populate_signature_from_designation(doc, method=None):
    """
    Auto-populate signature fields in documents based on designation
    This can be called as a hook when documents are created
    """
    try:
        # Only process if document has signature fields
        signature_fields = [field for field in doc.meta.fields 
                          if field.fieldtype == "Attach Image" and "signature" in field.fieldname.lower()]
        
        if not signature_fields:
            return
        
        # Try to get signature from various sources
        signature_value = None
        
        # Method 1: If document has employee field
        if hasattr(doc, 'employee') and doc.employee:
            hierarchy = get_signature_hierarchy(employee_name=doc.employee)
            if hierarchy.get("recommended_signature"):
                signature_value = hierarchy["recommended_signature"]
        
        # Method 2: If document has user field
        elif hasattr(doc, 'owner') and doc.owner:
            hierarchy = get_signature_hierarchy(user_id=doc.owner)
            if hierarchy.get("recommended_signature"):
                signature_value = hierarchy["recommended_signature"]
        
        # Method 3: If document has designation field
        elif hasattr(doc, 'designation') and doc.designation:
            hierarchy = get_signature_hierarchy(designation=doc.designation)
            if hierarchy.get("recommended_signature"):
                signature_value = hierarchy["recommended_signature"]
        
        # Populate empty signature fields
        if signature_value:
            for field in signature_fields:
                if not getattr(doc, field.fieldname):
                    setattr(doc, field.fieldname, signature_value)
        
    except Exception as e:
        frappe.log_error(f"Error in auto_populate_signature_from_designation: {str(e)}")

@frappe.whitelist()
def setup_designation_signature_sync():
    """
    Setup automatic signature syncing system
    Installs designation fields and creates sync rules
    """
    try:
        results = {
            "setup_steps": [],
            "success": True
        }
        
        # Step 1: Install designation signature fields
        from print_designer.api.signature_field_installer import install_signature_fields_for_doctype
        
        designation_result = install_signature_fields_for_doctype("Designation")
        if designation_result.get("success"):
            results["setup_steps"].append("Designation signature fields installed")
        else:
            results["setup_steps"].append(f"Designation field installation failed: {designation_result.get('error')}")
        
        # Step 2: Run initial sync
        sync_result = sync_designation_signatures()
        if sync_result.get("success"):
            results["setup_steps"].append(f"Initial sync completed: {sync_result['designations_updated']} designations, {sync_result['employees_synced']} employees, {sync_result['users_synced']} users updated")
        else:
            results["setup_steps"].append(f"Initial sync failed: {sync_result.get('error')}")
        
        # Step 3: Setup automatic sync hooks (would need to be added to hooks.py)
        results["setup_steps"].append("Manual sync available via API - consider adding to hooks.py for automatic syncing")
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Error in setup_designation_signature_sync: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_designation_signature_report():
    """
    Generate a comprehensive report of signature coverage across designations
    """
    try:
        report = {
            "timestamp": frappe.utils.now(),
            "summary": {
                "total_designations": 0,
                "designations_with_signatures": 0,
                "total_employees": 0,
                "employees_with_signatures": 0,
                "coverage_percentage": 0
            },
            "designations": [],
            "missing_signatures": []
        }
        
        # Get all designations with employee counts
        designations_data = frappe.db.sql("""
            SELECT 
                d.name as designation_name,
                d.designation_signature,
                d.signature_authority_level,
                d.max_approval_amount,
                COUNT(e.name) as employee_count,
                COUNT(e.signature_image) as employees_with_signatures
            FROM `tabDesignation` d
            LEFT JOIN `tabEmployee` e ON d.name = e.designation
            GROUP BY d.name
            ORDER BY employee_count DESC
        """, as_dict=True)
        
        report["summary"]["total_designations"] = len(designations_data)
        
        for designation in designations_data:
            des_info = {
                "name": designation.designation_name,
                "has_signature": bool(designation.designation_signature),
                "authority_level": designation.signature_authority_level or "None",
                "max_approval_amount": designation.max_approval_amount or 0,
                "employee_count": designation.employee_count,
                "employees_with_signatures": designation.employees_with_signatures,
                "coverage_rate": round((designation.employees_with_signatures / max(designation.employee_count, 1)) * 100, 1)
            }
            
            report["designations"].append(des_info)
            
            if des_info["has_signature"]:
                report["summary"]["designations_with_signatures"] += 1
            
            report["summary"]["total_employees"] += designation.employee_count
            report["summary"]["employees_with_signatures"] += designation.employees_with_signatures
            
            # Track missing signatures
            if not des_info["has_signature"] and des_info["employee_count"] > 0:
                report["missing_signatures"].append({
                    "designation": designation.designation_name,
                    "employee_count": designation.employee_count,
                    "priority": "High" if designation.employee_count > 5 else "Medium"
                })
        
        # Calculate overall coverage
        if report["summary"]["total_employees"] > 0:
            report["summary"]["coverage_percentage"] = round(
                (report["summary"]["employees_with_signatures"] / report["summary"]["total_employees"]) * 100, 1
            )
        
        return report
        
    except Exception as e:
        frappe.log_error(f"Error in get_designation_signature_report: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def bulk_update_designation_signatures(designation_mappings):
    """
    Bulk update multiple designation signatures
    
    Args:
        designation_mappings: List of {designation: signature_url} mappings
    """
    try:
        results = {
            "updated_count": 0,
            "errors": [],
            "success": True
        }
        
        mappings = frappe.parse_json(designation_mappings)
        
        for mapping in mappings:
            try:
                designation = mapping.get("designation")
                signature_url = mapping.get("signature_url")
                authority_level = mapping.get("authority_level", "None")
                max_amount = mapping.get("max_approval_amount", 0)
                
                if designation and signature_url:
                    frappe.db.set_value("Designation", designation, {
                        "designation_signature": signature_url,
                        "signature_authority_level": authority_level,
                        "max_approval_amount": max_amount
                    })
                    results["updated_count"] += 1
                    
            except Exception as e:
                results["errors"].append(f"Error updating {mapping.get('designation', 'unknown')}: {str(e)}")
        
        frappe.db.commit()
        return results
        
    except Exception as e:
        frappe.log_error(f"Error in bulk_update_designation_signatures: {str(e)}")
        return {"success": False, "error": str(e)}