import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from print_designer.signature_fields import get_signature_fields


@frappe.whitelist()
def install_signature_fields():
	"""
	Install all signature fields defined in signature_fields.py
	
	Returns:
		dict: Installation results
	"""
	try:
		signature_fields = get_signature_fields()
		
		# Convert to format expected by create_custom_fields
		custom_fields = {}
		for doctype, fields in signature_fields.items():
			custom_fields[doctype] = fields
		
		# Install the custom fields
		create_custom_fields(custom_fields, ignore_validate=frappe.flags.in_patch)
		
		return {
			"success": True,
			"message": f"Installed signature fields for {len(custom_fields)} DocTypes",
			"doctypes": list(custom_fields.keys())
		}
		
	except Exception as e:
		frappe.log_error(f"Error installing signature fields: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def check_signature_fields_status():
	"""
	Check which signature fields are installed and which are missing
	
	Returns:
		dict: Status of signature fields installation
	"""
	try:
		from print_designer.signature_fields import get_signature_fields
		
		signature_fields = get_signature_fields()
		results = {}
		
		for doctype, fields in signature_fields.items():
			if not frappe.db.exists("DocType", doctype):
				results[doctype] = {"status": "doctype_not_found", "fields": []}
				continue
			
			field_status = []
			for field in fields:
				field_exists = frappe.db.exists("Custom Field", {
					"dt": doctype,
					"fieldname": field["fieldname"]
				})
				
				field_status.append({
					"fieldname": field["fieldname"],
					"label": field["label"],
					"installed": bool(field_exists)
				})
			
			all_installed = all(f["installed"] for f in field_status)
			results[doctype] = {
				"status": "installed" if all_installed else "partial" if any(f["installed"] for f in field_status) else "not_installed",
				"fields": field_status
			}
		
		return {
			"success": True,
			"results": results,
			"summary": {
				"total_doctypes": len(results),
				"fully_installed": len([r for r in results.values() if r["status"] == "installed"]),
				"partially_installed": len([r for r in results.values() if r["status"] == "partial"]),
				"not_installed": len([r for r in results.values() if r["status"] == "not_installed"])
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Error checking signature fields status: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def install_signature_fields_for_doctype(doctype):
	"""
	Install signature fields for a specific DocType
	
	Args:
		doctype (str): DocType name
		
	Returns:
		dict: Installation result
	"""
	try:
		from print_designer.signature_fields import get_signature_fields_for_doctype
		
		fields = get_signature_fields_for_doctype(doctype)
		
		if not fields:
			return {"error": f"No signature fields defined for DocType '{doctype}'"}
		
		if not frappe.db.exists("DocType", doctype):
			return {"error": f"DocType '{doctype}' not found"}
		
		# Install fields for this DocType
		custom_fields = {doctype: fields}
		create_custom_fields(custom_fields, ignore_validate=frappe.flags.in_patch)
		
		return {
			"success": True,
			"doctype": doctype,
			"fields_installed": len(fields),
			"field_names": [f["fieldname"] for f in fields]
		}
		
	except Exception as e:
		frappe.log_error(f"Error installing signature fields for {doctype}: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def get_company_signature_field_value(company_name, field_name="ceo_signature"):
	"""
	Get current value of a signature field for a company
	
	Args:
		company_name (str): Company name
		field_name (str): Field name to check
		
	Returns:
		dict: Field value and status
	"""
	try:
		if not frappe.db.exists("Company", company_name):
			return {"error": f"Company '{company_name}' not found"}
		
		# Check if field exists
		field_exists = frappe.db.exists("Custom Field", {
			"dt": "Company",
			"fieldname": field_name
		})
		
		if not field_exists:
			return {
				"company": company_name,
				"field_name": field_name,
				"field_exists": False,
				"value": None,
				"message": f"Custom field '{field_name}' not installed for Company DocType"
			}
		
		# Get field value
		value = frappe.get_value("Company", company_name, field_name)
		
		return {
			"company": company_name,
			"field_name": field_name,
			"field_exists": True,
			"value": value,
			"has_value": bool(value)
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting company signature field value: {str(e)}")
		return {"error": str(e)}