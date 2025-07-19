import frappe
from frappe import _
from print_designer.signature_fields import get_signature_fields


@frappe.whitelist()
def get_signature_field_options():
	"""
	Get all available signature field options from signature_fields.py
	
	Returns:
		list: List of signature field options for Select field
	"""
	try:
		signature_fields = get_signature_fields()
		options = []
		
		for doctype, fields in signature_fields.items():
			for field in fields:
				option_value = f"{doctype}::{field['fieldname']}"
				option_label = f"{doctype} - {field['label']}"
				options.append({
					"value": option_value,
					"label": option_label,
					"doctype": doctype,
					"fieldname": field["fieldname"],
					"field_label": field["label"],
					"description": field.get("description", "")
				})
		
		# Sort by DocType then by field label
		options.sort(key=lambda x: (x["doctype"], x["field_label"]))
		
		return options
		
	except Exception as e:
		frappe.log_error(f"Error getting signature field options: {str(e)}")
		return []


@frappe.whitelist()
def get_signature_field_options_string():
	"""
	Get signature field options as a newline-separated string for Select field options
	
	Returns:
		str: Options string for Frappe Select field
	"""
	try:
		options = get_signature_field_options()
		
		# Convert to Frappe Select field format: "value\nlabel"
		option_strings = []
		for option in options:
			option_strings.append(f"{option['value']}")
		
		return "\n".join(option_strings)
		
	except Exception as e:
		frappe.log_error(f"Error getting signature field options string: {str(e)}")
		return ""


@frappe.whitelist()
def get_signature_fields_for_doctype_select(doctype):
	"""
	Get signature fields for a specific DocType as Select options
	
	Args:
		doctype (str): DocType name
		
	Returns:
		str: Options string for Select field
	"""
	try:
		from print_designer.signature_fields import get_signature_fields_for_doctype
		
		fields = get_signature_fields_for_doctype(doctype)
		
		if not fields:
			return ""
		
		options = []
		for field in fields:
			options.append(f"{field['fieldname']}")
		
		return "\n".join(options)
		
	except Exception as e:
		frappe.log_error(f"Error getting signature fields for DocType: {str(e)}")
		return ""


@frappe.whitelist()
def parse_signature_field_mapping(field_mapping):
	"""
	Parse signature field mapping from format "DocType::fieldname"
	
	Args:
		field_mapping (str): Field mapping in format "DocType::fieldname"
		
	Returns:
		dict: Parsed mapping with doctype and fieldname
	"""
	try:
		if not field_mapping or "::" not in field_mapping:
			return {"error": "Invalid field mapping format. Expected 'DocType::fieldname'"}
		
		parts = field_mapping.split("::")
		if len(parts) != 2:
			return {"error": "Invalid field mapping format. Expected 'DocType::fieldname'"}
		
		doctype, fieldname = parts
		
		# Validate that this mapping exists in signature_fields.py
		from print_designer.signature_fields import get_signature_fields_for_doctype
		
		available_fields = get_signature_fields_for_doctype(doctype)
		field_names = [f["fieldname"] for f in available_fields]
		
		if fieldname not in field_names:
			return {
				"error": f"Field '{fieldname}' not found in {doctype} signature fields",
				"available_fields": field_names
			}
		
		return {
			"success": True,
			"doctype": doctype,
			"fieldname": fieldname,
			"mapping": field_mapping
		}
		
	except Exception as e:
		frappe.log_error(f"Error parsing signature field mapping: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def get_signature_field_info(field_mapping):
	"""
	Get detailed information about a signature field mapping
	
	Args:
		field_mapping (str): Field mapping in format "DocType::fieldname"
		
	Returns:
		dict: Detailed field information
	"""
	try:
		parsed = parse_signature_field_mapping(field_mapping)
		
		if parsed.get("error"):
			return parsed
		
		doctype = parsed["doctype"]
		fieldname = parsed["fieldname"]
		
		# Get field definition
		from print_designer.signature_fields import get_signature_fields_for_doctype
		
		fields = get_signature_fields_for_doctype(doctype)
		field_def = next((f for f in fields if f["fieldname"] == fieldname), None)
		
		if not field_def:
			return {"error": f"Field definition not found for {field_mapping}"}
		
		# Check if field is installed
		field_installed = frappe.db.exists("Custom Field", {
			"dt": doctype,
			"fieldname": fieldname
		})
		
		return {
			"success": True,
			"mapping": field_mapping,
			"doctype": doctype,
			"fieldname": fieldname,
			"field_definition": field_def,
			"field_installed": bool(field_installed),
			"usage_info": {
				"label": field_def.get("label"),
				"description": field_def.get("description"),
				"insert_after": field_def.get("insert_after")
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting signature field info: {str(e)}")
		return {"error": str(e)}