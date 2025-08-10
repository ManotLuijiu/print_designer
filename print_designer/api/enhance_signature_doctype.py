import frappe
from frappe import _


@frappe.whitelist()
def enhance_signature_basic_information_doctype():
	"""
	Enhance the Signature Basic Information DocType with better field mapping
	
	Returns:
		dict: Enhancement results
	"""
	try:
		# Remove the old free-text field and add a proper Select field
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
		
		# First, get all signature field options
		from print_designer.api.signature_field_options import get_signature_field_options_string
		
		options_string = get_signature_field_options_string()
		
		custom_fields = {
			"Signature Basic Information": [
				{
					"fieldname": "signature_target_field",
					"fieldtype": "Select",
					"label": "Target Signature Field",
					"description": "Select which document field this signature should populate",
					"insert_after": "signature_field_name",
					"options": options_string,
					"depends_on": "eval:doc.signature_category=='Signature'"
				},
				{
					"fieldname": "target_doctype",
					"fieldtype": "Select", 
					"label": "Target DocType",
					"description": "DocType that contains the signature field",
					"insert_after": "signature_target_field",
					"options": "\nCompany\nUser\nEmployee\nCustomer\nSupplier\nSales Invoice\nPurchase Invoice\nSales Order\nPurchase Order\nDelivery Note\nPurchase Receipt\nQuotation\nRequest for Quotation",
					"depends_on": "eval:doc.signature_category=='Signature'"
				},
				{
					"fieldname": "auto_populate_field",
					"fieldtype": "Check",
					"label": "Auto-populate Target Field",
					"description": "Automatically update the target field when this signature is saved",
					"insert_after": "target_doctype",
					"default": "1",
					"depends_on": "eval:doc.signature_target_field"
				}
			]
		}
		
		# Install the custom fields
		create_custom_fields(custom_fields, ignore_validate=frappe.flags.in_patch)
		
		return {
			"success": True,
			"message": "Enhanced Signature Basic Information DocType with proper field mapping",
			"fields_added": ["signature_target_field", "target_doctype", "auto_populate_field"],
			"available_options": len(options_string.split("\n")) if options_string else 0
		}
		
	except Exception as e:
		frappe.log_error(f"Error enhancing signature DocType: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def get_target_doctype_options():
	"""
	Get available target DocTypes that have signature fields
	
	Returns:
		list: Available DocTypes with signature fields
	"""
	try:
		from print_designer.signature_fields import get_signature_fields
		
		signature_fields = get_signature_fields()
		doctypes = list(signature_fields.keys())
		doctypes.sort()
		
		return {
			"success": True,
			"doctypes": doctypes,
			"options_string": "\n".join([""] + doctypes)  # Empty option first
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting target DocType options: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def get_fields_for_target_doctype(target_doctype):
	"""
	Get available signature fields for a target DocType
	
	Args:
		target_doctype (str): Target DocType name
		
	Returns:
		dict: Available fields for the DocType
	"""
	try:
		from print_designer.signature_fields import get_signature_fields_for_doctype
		
		fields = get_signature_fields_for_doctype(target_doctype)
		
		if not fields:
			return {
				"success": True,
				"fields": [],
				"options_string": "",
				"message": f"No signature fields defined for {target_doctype}"
			}
		
		field_options = []
		for field in fields:
			field_options.append({
				"fieldname": field["fieldname"],
				"label": field["label"],
				"description": field.get("description", "")
			})
		
		options_string = "\n".join([""] + [f["fieldname"] for f in fields])
		
		return {
			"success": True,
			"target_doctype": target_doctype,
			"fields": field_options,
			"options_string": options_string
		}
		
	except Exception as e:
		frappe.log_error(f"Error getting fields for target DocType: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def create_signature_with_target_field(signature_data):
	"""
	Create a new signature record with proper target field mapping
	
	Args:
		signature_data (dict): Signature record data
		
	Returns:
		dict: Created signature record
	"""
	try:
		# Validate required fields
		required_fields = ["signature_name", "company", "target_doctype", "signature_target_field"]
		for field in required_fields:
			if not signature_data.get(field):
				return {"error": f"Required field '{field}' is missing"}
		
		# Parse target field
		from print_designer.api.signature_field_options import parse_signature_field_mapping
		
		target_field = signature_data["signature_target_field"]
		parsed = parse_signature_field_mapping(target_field)
		
		if parsed.get("error"):
			return {"error": f"Invalid target field: {parsed['error']}"}
		
		# Create the signature record
		signature_doc = frappe.get_doc({
			"doctype": "Signature Basic Information",
			"signature_name": signature_data["signature_name"],
			"signature_title": signature_data.get("signature_title", ""),
			"company": signature_data["company"],
			"user": signature_data.get("user"),
			"signature_category": "Signature",
			"signature_type": signature_data.get("signature_type", "Uploaded Image"),
			"signature_image": signature_data.get("signature_image"),
			"signature_data": signature_data.get("signature_data"),
			"is_active": 1,
			"is_default": signature_data.get("is_default", 0),
			
			# Enhanced fields
			"signature_target_field": target_field,
			"target_doctype": parsed["doctype"],
			"auto_populate_field": signature_data.get("auto_populate_field", 1),
			
			# Legacy field for compatibility
			"signature_field_name": parsed["fieldname"]
		})
		
		signature_doc.insert()
		frappe.db.commit()
		
		# Auto-populate target field if enabled
		if signature_data.get("auto_populate_field", 1):
			from print_designer.api.signature_sync import sync_signature_to_target_field
			sync_result = sync_signature_to_target_field(signature_doc.name)
		else:
			sync_result = {"message": "Auto-populate disabled"}
		
		return {
			"success": True,
			"signature_record": signature_doc.name,
			"target_mapping": parsed,
			"sync_result": sync_result
		}
		
	except Exception as e:
		frappe.log_error(f"Error creating signature with target field: {str(e)}")
		return {"error": str(e)}