import frappe
from frappe import _


@frappe.whitelist()
def run_complete_signature_diagnostics(company_name="Moo Coding"):
	"""
	Run complete diagnostics to understand why signatures are not working
	
	Args:
		company_name (str): Company to test with
		
	Returns:
		dict: Complete diagnostic report
	"""
	try:
		report = {
			"company": company_name,
			"timestamp": frappe.utils.now(),
			"steps": []
		}
		
		# Step 1: Check if company exists
		step1 = _check_company_exists(company_name)
		report["steps"].append(step1)
		
		if not step1["success"]:
			return report
		
		# Step 2: Check signature fields installation
		step2 = _check_signature_fields_installation()
		report["steps"].append(step2)
		
		# Step 3: Check current company signature values
		step3 = _check_company_signature_values(company_name)
		report["steps"].append(step3)
		
		# Step 4: Check signature registry
		step4 = _check_signature_registry(company_name)
		report["steps"].append(step4)
		
		# Step 5: Check Target Signature Field status
		step5 = _check_target_signature_field_status()
		report["steps"].append(step5)
		
		# Step 6: Test original API endpoints
		step6 = _test_original_api_endpoints(company_name)
		report["steps"].append(step6)
		
		# Step 7: Generate recommendations
		step7 = _generate_recommendations(report["steps"])
		report["steps"].append(step7)
		
		return report
		
	except Exception as e:
		frappe.log_error(f"Error running signature diagnostics: {str(e)}")
		return {"error": str(e)}


def _check_company_exists(company_name):
	"""Step 1: Check if company exists"""
	try:
		exists = frappe.db.exists("Company", company_name)
		return {
			"step": 1,
			"title": "Company Existence Check",
			"success": bool(exists),
			"message": f"Company '{company_name}' {'exists' if exists else 'does not exist'}",
			"data": {"company_exists": bool(exists)}
		}
	except Exception as e:
		return {
			"step": 1,
			"title": "Company Existence Check",
			"success": False,
			"error": str(e)
		}


def _check_signature_fields_installation():
	"""Step 2: Check signature fields installation"""
	try:
		from print_designer.api.signature_field_installer import check_signature_fields_status
		
		status = check_signature_fields_status()
		
		if status.get("error"):
			return {
				"step": 2,
				"title": "Signature Fields Installation Check",
				"success": False,
				"error": status["error"]
			}
		
		company_status = status["results"].get("Company", {})
		
		return {
			"step": 2,
			"title": "Signature Fields Installation Check",
			"success": company_status.get("status") == "installed",
			"message": f"Company signature fields status: {company_status.get('status', 'unknown')}",
			"data": {
				"company_fields": company_status,
				"overall_summary": status["summary"]
			}
		}
		
	except Exception as e:
		return {
			"step": 2,
			"title": "Signature Fields Installation Check",
			"success": False,
			"error": str(e)
		}


def _check_company_signature_values(company_name):
	"""Step 3: Check current company signature field values"""
	try:
		from print_designer.api.signature_field_installer import get_company_signature_field_value
		
		fields_to_check = ["ceo_signature", "authorized_signature_1", "authorized_signature_2"]
		results = {}
		
		for field in fields_to_check:
			result = get_company_signature_field_value(company_name, field)
			results[field] = result
		
		has_any_values = any(r.get("has_value", False) for r in results.values())
		
		return {
			"step": 3,
			"title": "Company Signature Field Values",
			"success": has_any_values,
			"message": f"Company has {'some' if has_any_values else 'no'} signature field values",
			"data": results
		}
		
	except Exception as e:
		return {
			"step": 3,
			"title": "Company Signature Field Values",
			"success": False,
			"error": str(e)
		}


def _check_signature_registry(company_name):
	"""Step 4: Check signature basic information registry"""
	try:
		from print_designer.api.signature_sync import get_company_signatures_from_registry
		
		registry_data = get_company_signatures_from_registry(company_name)
		
		if registry_data.get("error"):
			return {
				"step": 4,
				"title": "Signature Registry Check",
				"success": False,
				"error": registry_data["error"]
			}
		
		has_signatures = registry_data.get("total_signatures", 0) > 0
		
		return {
			"step": 4,
			"title": "Signature Registry Check",
			"success": has_signatures,
			"message": f"Found {registry_data.get('total_signatures', 0)} signatures in registry",
			"data": registry_data
		}
		
	except Exception as e:
		return {
			"step": 4,
			"title": "Signature Registry Check",
			"success": False,
			"error": str(e)
		}


def _test_original_api_endpoints(company_name):
	"""Step 5: Test the original API endpoints that were failing"""
	try:
		# Test Company ceo_signature
		company_result = frappe.client.get_value("Company", company_name, "ceo_signature")
		
		# Test Letter Head image (for comparison)
		letterhead_result = None
		try:
			letterhead_result = frappe.client.get_value("Letter Head", company_name, "image")
		except:
			letterhead_result = "Not found or error"
		
		return {
			"step": 5,
			"title": "Original API Endpoints Test",
			"success": True,
			"message": "API endpoints tested",
			"data": {
				"company_ceo_signature": company_result,
				"letterhead_image": letterhead_result,
				"company_signature_has_value": bool(company_result and company_result != "null"),
				"letterhead_has_value": bool(letterhead_result and letterhead_result != "Not found or error")
			}
		}
		
	except Exception as e:
		return {
			"step": 5,
			"title": "Original API Endpoints Test",
			"success": False,
			"error": str(e)
		}


def _generate_recommendations(steps):
	"""Step 6: Generate recommendations based on diagnostic results"""
	recommendations = []
	
	# Analyze the steps
	company_exists = steps[0]["success"] if len(steps) > 0 else False
	fields_installed = steps[1]["success"] if len(steps) > 1 else False
	has_field_values = steps[2]["success"] if len(steps) > 2 else False
	has_registry_data = steps[3]["success"] if len(steps) > 3 else False
	
	if not company_exists:
		recommendations.append({
			"priority": "high",
			"action": "Create the company record first",
			"method": "Go to Company list and create 'Moo Coding' company"
		})
	
	if not fields_installed:
		recommendations.append({
			"priority": "high", 
			"action": "Install signature custom fields",
			"method": "Call: print_designer.api.signature_field_installer.install_signature_fields_for_doctype",
			"params": {"doctype": "Company"}
		})
	
	if not has_field_values and not has_registry_data:
		recommendations.append({
			"priority": "medium",
			"action": "Create signature records",
			"method": "Go to 'Signature Basic Information' and create signature records for the company"
		})
	
	if not has_field_values and has_registry_data:
		recommendations.append({
			"priority": "medium",
			"action": "Sync signature data to company fields",
			"method": "Call: print_designer.api.signature_sync.sync_company_signatures",
			"params": {"company_name": "Moo Coding"}
		})
	
	if has_field_values:
		recommendations.append({
			"priority": "low",
			"action": "Signatures are working correctly",
			"method": "No action needed - system is properly configured"
		})
	
	return {
		"step": 6,
		"title": "Recommendations",
		"success": True,
		"message": f"Generated {len(recommendations)} recommendations",
		"data": {
			"recommendations": recommendations,
			"next_steps": "Follow recommendations in order of priority"
		}
	}


@frappe.whitelist()
def fix_signature_setup_for_company(company_name="Moo Coding"):
	"""
	Automated fix for signature setup issues
	
	Args:
		company_name (str): Company to fix
		
	Returns:
		dict: Fix results
	"""
	try:
		results = {
			"company": company_name,
			"actions_taken": [],
			"success": True
		}
		
		# Action 1: Install signature fields if needed
		from print_designer.api.signature_field_installer import install_signature_fields_for_doctype, check_signature_fields_status
		
		status = check_signature_fields_status()
		company_status = status["results"].get("Company", {})
		
		if company_status.get("status") != "installed":
			install_result = install_signature_fields_for_doctype("Company")
			results["actions_taken"].append({
				"action": "install_signature_fields",
				"result": install_result
			})
		
		# Action 2: Check if there are signature records to sync
		from print_designer.api.signature_sync import get_company_signatures_from_registry, sync_company_signatures
		
		registry_data = get_company_signatures_from_registry(company_name)
		
		if not registry_data.get("error") and registry_data.get("total_signatures", 0) > 0:
			# Sync existing signatures
			sync_result = sync_company_signatures(company_name)
			results["actions_taken"].append({
				"action": "sync_signatures",
				"result": sync_result
			})
		else:
			# No signatures in registry, suggest manual creation
			results["actions_taken"].append({
				"action": "manual_signature_creation_needed",
				"message": "No signatures found in registry. Please create signature records manually in 'Signature Basic Information'"
			})
		
		return results
		
	except Exception as e:
		frappe.log_error(f"Error fixing signature setup: {str(e)}")
		return {"error": str(e), "success": False}


def _check_target_signature_field_status():
	"""
	Check if the Target Signature Field dropdown is properly populated
	
	Returns:
		dict: Status check results
	"""
	try:
		from print_designer.commands.fix_target_signature_field import check_target_signature_field_status
		
		status = check_target_signature_field_status()
		
		if status.get("error"):
			return {
				"step": 5,
				"title": "Target Signature Field Status",
				"success": False,
				"error": status["error"],
				"message": "Failed to check Target Signature Field status"
			}
		
		needs_fix = status.get("needs_fix", False)
		options_count = status.get("options_count", 0)
		
		return {
			"step": 5,
			"title": "Target Signature Field Status", 
			"success": not needs_fix,
			"status": status.get("status"),
			"options_count": options_count,
			"needs_fix": needs_fix,
			"message": f"Target Signature Field has {options_count} options" if not needs_fix else "Target Signature Field dropdown is empty and needs to be populated",
			"field_name": status.get("field_name"),
			"api_status": status.get("api_status"),
			"fix_command": "bench execute print_designer.commands.fix_target_signature_field.fix_signature_target_field_options" if needs_fix else None
		}
		
	except Exception as e:
		frappe.log_error(f"Error checking Target Signature Field status: {str(e)}")
		return {
			"step": 5,
			"title": "Target Signature Field Status",
			"success": False,
			"error": str(e),
			"message": "Failed to check Target Signature Field status"
		}