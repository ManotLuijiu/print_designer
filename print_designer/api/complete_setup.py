import frappe
from frappe import _


@frappe.whitelist()
def complete_signature_setup():
	"""
	Complete setup for the enhanced signature system
	
	Returns:
		dict: Setup results
	"""
	try:
		results = {
			"timestamp": frappe.utils.now(),
			"steps": [],
			"success": True
		}
		
		# Step 1: Install signature fields
		step1 = _install_signature_fields()
		results["steps"].append(step1)
		
		# Step 2: Enhance Signature Basic Information DocType
		step2 = _enhance_signature_doctype()
		results["steps"].append(step2)
		
		# Step 3: Run diagnostics
		step3 = _run_diagnostics()
		results["steps"].append(step3)
		
		# Step 4: Create sample data if requested
		# step4 = _create_sample_signature_data()
		# results["steps"].append(step4)
		
		return results
		
	except Exception as e:
		frappe.log_error(f"Error in complete signature setup: {str(e)}")
		return {"error": str(e), "success": False}


def _install_signature_fields():
	"""Install all signature fields"""
	try:
		from print_designer.api.signature_field_installer import install_signature_fields
		
		result = install_signature_fields()
		
		return {
			"step": 1,
			"title": "Install Signature Fields", 
			"success": result.get("success", False),
			"message": result.get("message", ""),
			"data": result
		}
		
	except Exception as e:
		return {
			"step": 1,
			"title": "Install Signature Fields",
			"success": False,
			"error": str(e)
		}


def _enhance_signature_doctype():
	"""Enhance Signature Basic Information DocType"""
	try:
		from print_designer.api.enhance_signature_doctype import enhance_signature_basic_information_doctype
		
		result = enhance_signature_basic_information_doctype()
		
		return {
			"step": 2,
			"title": "Enhance Signature DocType",
			"success": result.get("success", False),
			"message": result.get("message", ""),
			"data": result
		}
		
	except Exception as e:
		return {
			"step": 2,
			"title": "Enhance Signature DocType", 
			"success": False,
			"error": str(e)
		}


def _run_diagnostics():
	"""Run system diagnostics"""
	try:
		from print_designer.api.signature_diagnostics import run_complete_signature_diagnostics
		
		result = run_complete_signature_diagnostics("Moo Coding")
		
		return {
			"step": 3,
			"title": "System Diagnostics",
			"success": True,
			"message": "Diagnostics completed",
			"data": result
		}
		
	except Exception as e:
		return {
			"step": 3,
			"title": "System Diagnostics",
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def create_sample_signature_for_company(company_name="Moo Coding"):
	"""
	Create a sample signature record for testing
	
	Args:
		company_name (str): Company name
		
	Returns:
		dict: Creation result
	"""
	try:
		signature_data = {
			"signature_name": f"CEO Signature - {company_name}",
			"signature_title": "CEO", 
			"company": company_name,
			"signature_category": "Signature",
			"signature_type": "Uploaded Image",
			"target_doctype": "Company",
			"signature_target_field": "Company::ceo_signature",
			"auto_populate_field": 1,
			"is_default": 1,
			"is_active": 1
		}
		
		from print_designer.api.enhance_signature_doctype import create_signature_with_target_field
		
		result = create_signature_with_target_field(signature_data)
		
		if result.get("success"):
			return {
				"success": True,
				"message": f"Sample signature created for {company_name}",
				"signature_record": result["signature_record"],
				"note": "Upload a signature image to complete the setup"
			}
		else:
			return result
		
	except Exception as e:
		frappe.log_error(f"Error creating sample signature: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def get_setup_status():
	"""
	Get current setup status
	
	Returns:
		dict: Setup status
	"""
	try:
		status = {
			"timestamp": frappe.utils.now(),
			"checks": []
		}
		
		# Check 1: Signature fields installed
		try:
			from print_designer.api.signature_field_installer import check_signature_fields_status
			field_status = check_signature_fields_status()
			company_status = field_status["results"].get("Company", {})
			
			status["checks"].append({
				"check": "Signature Fields Installation",
				"status": company_status.get("status", "unknown"),
				"success": company_status.get("status") == "installed",
				"details": company_status
			})
		except Exception as e:
			status["checks"].append({
				"check": "Signature Fields Installation",
				"status": "error",
				"success": False,
				"error": str(e)
			})
		
		# Check 2: Enhanced DocType fields
		try:
			enhanced_fields_exist = frappe.db.exists("Custom Field", {
				"dt": "Signature Basic Information",
				"fieldname": "signature_target_field"
			})
			
			status["checks"].append({
				"check": "Enhanced DocType Fields",
				"status": "installed" if enhanced_fields_exist else "not_installed",
				"success": bool(enhanced_fields_exist),
				"details": {"enhanced_fields_installed": bool(enhanced_fields_exist)}
			})
		except Exception as e:
			status["checks"].append({
				"check": "Enhanced DocType Fields",
				"status": "error", 
				"success": False,
				"error": str(e)
			})
		
		# Check 3: Sample data exists
		try:
			sample_signatures = frappe.get_all(
				"Signature Basic Information",
				filters={"company": "Moo Coding"},
				limit=1
			)
			
			status["checks"].append({
				"check": "Sample Signature Data",
				"status": "exists" if sample_signatures else "not_exists",
				"success": bool(sample_signatures),
				"details": {"sample_signatures_count": len(sample_signatures)}
			})
		except Exception as e:
			status["checks"].append({
				"check": "Sample Signature Data",
				"status": "error",
				"success": False,
				"error": str(e)
			})
		
		# Overall status
		all_success = all(check["success"] for check in status["checks"])
		status["overall_status"] = "ready" if all_success else "needs_setup"
		status["ready"] = all_success
		
		return status
		
	except Exception as e:
		frappe.log_error(f"Error getting setup status: {str(e)}")
		return {"error": str(e)}