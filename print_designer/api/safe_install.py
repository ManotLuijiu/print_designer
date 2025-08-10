import frappe
from frappe import _


@frappe.whitelist()
def safe_install_signature_enhancements():
	"""
	Safe installation of signature enhancements that can be run multiple times
	Used for both development and production migrations
	
	Returns:
		dict: Installation results
	"""
	try:
		results = {
			"timestamp": frappe.utils.now(),
			"steps": [],
			"success": True,
			"mode": "development" if frappe.conf.get("developer_mode") else "production"
		}
		
		# Step 1: Install core signature fields (safe)
		step1 = _safe_install_core_signature_fields()
		results["steps"].append(step1)
		
		# Step 2: Enhance Signature Basic Information DocType
		step2 = _safe_enhance_signature_doctype()
		results["steps"].append(step2)
		
		# Step 3: Update existing signature records (optional)
		step3 = _safe_migrate_existing_signatures()
		results["steps"].append(step3)
		
		# Step 4: Clear cache to refresh DocTypes
		frappe.clear_cache()
		step4 = {
			"step": 4,
			"title": "Clear Cache",
			"success": True,
			"message": "Cache cleared successfully"
		}
		results["steps"].append(step4)
		
		# Check if all steps succeeded
		results["success"] = all(step["success"] for step in results["steps"])
		
		return results
		
	except Exception as e:
		frappe.log_error(f"Error in safe signature installation: {str(e)}")
		return {"error": str(e), "success": False}


def _safe_install_core_signature_fields():
	"""Safely install signature fields for core DocTypes"""
	try:
		from print_designer.signature_fields import get_signature_fields
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
		
		# Only install for DocTypes that definitely exist
		core_doctypes = ["Company", "User"]
		if frappe.db.exists("DocType", "Employee"):
			core_doctypes.append("Employee")
		
		signature_fields = get_signature_fields()
		safe_fields = {}
		installed_count = 0
		
		for doctype in core_doctypes:
			if doctype in signature_fields:
				# Check existing fields
				existing_fields = frappe.get_all(
					"Custom Field",
					filters={"dt": doctype},
					fields=["fieldname"]
				)
				existing_fieldnames = [f.fieldname for f in existing_fields]
				
				# Only add fields that don't exist
				new_fields = []
				for field in signature_fields[doctype]:
					if field["fieldname"] not in existing_fieldnames:
						new_fields.append(field)
				
				if new_fields:
					safe_fields[doctype] = new_fields
					installed_count += len(new_fields)
		
		if safe_fields:
			create_custom_fields(safe_fields, ignore_validate=True)
		
		return {
			"step": 1,
			"title": "Install Core Signature Fields",
			"success": True,
			"message": f"Installed {installed_count} fields for {len(safe_fields)} DocTypes",
			"data": {
				"doctypes_processed": len(core_doctypes),
				"fields_installed": installed_count,
				"doctypes_with_new_fields": list(safe_fields.keys())
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Error installing core signature fields: {str(e)}")
		return {
			"step": 1,
			"title": "Install Core Signature Fields",
			"success": False,
			"error": str(e)
		}


def _safe_enhance_signature_doctype():
	"""Safely enhance Signature Basic Information DocType"""
	try:
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
		
		# Check existing enhancement fields
		existing_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "Signature Basic Information"},
			fields=["fieldname"]
		)
		existing_fieldnames = [f.fieldname for f in existing_fields]
		
		# Define enhancement fields
		enhancement_fields = [
			{
				"fieldname": "signature_target_field",
				"fieldtype": "Select",
				"label": "Target Signature Field",
				"description": "Select which document field this signature should populate",
				"insert_after": "signature_field_name",
				"options": "",  # Dynamically populated by client script
				"depends_on": "eval:doc.signature_category=='Signature'",
				"allow_on_submit": 0,
				"bold": 0,
				"collapsible": 0,
				"collapsible_depends_on": "",
				"columns": 0,
				"fetch_from": "",
				"fetch_if_empty": 0,
				"hidden": 0,
				"hide_border": 0,
				"hide_days": 0,
				"hide_seconds": 0,
				"ignore_user_permissions": 0,
				"ignore_xss_filter": 0,
				"in_global_search": 0,
				"in_list_view": 0,
				"in_preview": 0,
				"in_standard_filter": 0,
				"length": 0,
				"mandatory_depends_on": "",
				"no_copy": 0,
				"non_negative": 0,
				"permlevel": 0,
				"precision": "",
				"print_hide": 0,
				"print_hide_if_no_value": 0,
				"print_width": "",
				"read_only": 0,
				"read_only_depends_on": "",
				"report_hide": 0,
				"reqd": 0,
				"search_index": 0,
				"translatable": 0,
				"unique": 0,
				"width": ""
			},
			{
				"fieldname": "target_doctype",
				"fieldtype": "Select",
				"label": "Target DocType",
				"description": "DocType that contains the signature field",
				"insert_after": "signature_target_field",
				"options": "\nCompany\nUser\nEmployee\nCustomer\nSupplier\nSales Invoice\nPurchase Invoice\nSales Order\nPurchase Order\nDelivery Note\nPurchase Receipt\nQuotation\nRequest for Quotation",
				"depends_on": "eval:doc.signature_category=='Signature'",
				"allow_on_submit": 0,
				"bold": 0,
				"collapsible": 0,
				"columns": 0,
				"hidden": 0,
				"in_list_view": 0,
				"mandatory_depends_on": "",
				"permlevel": 0,
				"print_hide": 0,
				"read_only": 0,
				"reqd": 0,
				"translatable": 0,
				"unique": 0
			},
			{
				"fieldname": "auto_populate_field",
				"fieldtype": "Check",
				"label": "Auto-populate Target Field",
				"description": "Automatically update the target field when this signature is saved",
				"insert_after": "target_doctype",
				"default": "1",
				"depends_on": "eval:doc.signature_target_field",
				"allow_on_submit": 0,
				"bold": 0,
				"collapsible": 0,
				"columns": 0,
				"hidden": 0,
				"in_list_view": 0,
				"permlevel": 0,
				"print_hide": 0,
				"read_only": 0,
				"reqd": 0,
				"translatable": 0,
				"unique": 0
			}
		]
		
		# Only add fields that don't exist
		new_fields = []
		for field in enhancement_fields:
			if field["fieldname"] not in existing_fieldnames:
				new_fields.append(field)
		
		if new_fields:
			custom_fields = {"Signature Basic Information": new_fields}
			create_custom_fields(custom_fields, ignore_validate=True)
			frappe.db.commit()
		
		return {
			"step": 2,
			"title": "Enhance Signature DocType",
			"success": True,
			"message": f"Added {len(new_fields)} enhancement fields" if new_fields else "Enhancement fields already exist",
			"data": {
				"fields_added": len(new_fields),
				"new_field_names": [f["fieldname"] for f in new_fields],
				"total_existing_fields": len(existing_fieldnames)
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Error enhancing signature DocType: {str(e)}")
		return {
			"step": 2,
			"title": "Enhance Signature DocType",
			"success": False,
			"error": str(e)
		}


def _safe_migrate_existing_signatures():
	"""Safely migrate existing signature records"""
	try:
		# Only migrate if enhancement fields exist
		enhancement_field_exists = frappe.db.exists("Custom Field", {
			"dt": "Signature Basic Information",
			"fieldname": "target_doctype"
		})
		
		if not enhancement_field_exists:
			return {
				"step": 3,
				"title": "Migrate Existing Signatures",
				"success": True,
				"message": "Skipped - enhancement fields not available",
				"data": {"migrated_count": 0}
			}
		
		# Get signatures that need migration
		signatures_to_migrate = frappe.get_all(
			"Signature Basic Information",
			filters={
				"signature_category": "Signature"
			},
			fields=["name", "signature_title", "company", "user", "signature_field_name", "target_doctype"]
		)
		
		migrated_count = 0
		
		for signature in signatures_to_migrate:
			try:
				# Skip if already has target_doctype
				if signature.target_doctype:
					continue
				
				# Determine target mapping
				target_doctype = None
				target_field = None
				
				# Smart mapping based on context
				if signature.signature_title and "CEO" in signature.signature_title.upper():
					target_doctype = "Company"
					target_field = "Company::ceo_signature"
				elif signature.user:
					target_doctype = "User"
					target_field = "User::signature_image"
				elif signature.company:
					target_doctype = "Company" 
					target_field = "Company::authorized_signature_1"
				
				# Legacy field name mapping
				if signature.signature_field_name and not target_field:
					legacy_mapping = {
						"ceo_signature": "Company::ceo_signature",
						"authorized_signature_1": "Company::authorized_signature_1",
						"authorized_signature_2": "Company::authorized_signature_2",
						"signature_image": "User::signature_image"
					}
					target_field = legacy_mapping.get(signature.signature_field_name)
					if target_field:
						target_doctype = target_field.split("::")[0]
				
				# Update if we have valid mapping
				if target_doctype and target_field:
					frappe.db.set_value(
						"Signature Basic Information",
						signature.name,
						{
							"target_doctype": target_doctype,
							"signature_target_field": target_field,
							"auto_populate_field": 1
						}
					)
					migrated_count += 1
					
			except Exception as e:
				frappe.log_error(f"Error migrating individual signature {signature.name}: {str(e)}")
				continue
		
		if migrated_count > 0:
			frappe.db.commit()
		
		return {
			"step": 3,
			"title": "Migrate Existing Signatures",
			"success": True,
			"message": f"Migrated {migrated_count} existing signature records",
			"data": {
				"total_signatures": len(signatures_to_migrate),
				"migrated_count": migrated_count
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Error migrating existing signatures: {str(e)}")
		return {
			"step": 3,
			"title": "Migrate Existing Signatures",
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def check_installation_status():
	"""Check current installation status"""
	try:
		status = {
			"timestamp": frappe.utils.now(),
			"checks": []
		}
		
		# Check 1: Core signature fields
		company_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "Company", "fieldname": ["like", "%signature%"]},
			fields=["fieldname", "label"]
		)
		
		status["checks"].append({
			"component": "Company Signature Fields",
			"installed": len(company_fields) > 0,
			"details": company_fields
		})
		
		# Check 2: Enhancement fields
		enhancement_fields = frappe.get_all(
			"Custom Field",
			filters={
				"dt": "Signature Basic Information",
				"fieldname": ["in", ["target_doctype", "signature_target_field", "auto_populate_field"]]
			},
			fields=["fieldname", "label"]
		)
		
		status["checks"].append({
			"component": "Enhancement Fields",
			"installed": len(enhancement_fields) >= 3,
			"details": enhancement_fields
		})
		
		# Check 3: Signature records
		signature_count = frappe.db.count("Signature Basic Information")
		
		status["checks"].append({
			"component": "Signature Records",
			"installed": signature_count > 0,
			"details": {"count": signature_count}
		})
		
		# Overall status
		status["overall_installed"] = all(check["installed"] for check in status["checks"])
		
		return status
		
	except Exception as e:
		frappe.log_error(f"Error checking installation status: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def force_reinstall():
	"""Force reinstall (for development only)"""
	if not frappe.conf.get("developer_mode"):
		return {"error": "Force reinstall only available in developer mode"}
	
	try:
		# Remove existing custom fields
		frappe.db.delete("Custom Field", {
			"dt": "Signature Basic Information",
			"fieldname": ["in", ["target_doctype", "signature_target_field", "auto_populate_field"]]
		})
		
		# Reinstall
		result = safe_install_signature_enhancements()
		
		return {
			"success": True,
			"message": "Force reinstall completed",
			"install_result": result
		}
		
	except Exception as e:
		return {"error": str(e)}