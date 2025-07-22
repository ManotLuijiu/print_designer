# Watermark Fields Configuration for Print Designer
# This file defines watermark text fields to be added to various DocTypes
# Following the same pattern as signature_fields.py for consistency

WATERMARK_FIELDS = {
	# Sales Module - Transaction Documents
	"Sales Invoice": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nCancelled\nPaid\nDuplicate",
			"default": "None",
			"insert_after": "is_return",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Sales Order": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark", 
			"options": "None\nOriginal\nCopy\nDraft\nConfirmed\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "order_type",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Quotation": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nOrdered\nExpired\nDuplicate",
			"default": "None",
			"insert_after": "quotation_to",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Delivery Note": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
			"default": "None", 
			"insert_after": "is_return",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Purchase Module - Transaction Documents
	"Purchase Invoice": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nPaid\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "is_return",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Purchase Order": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate", 
			"default": "None",
			"insert_after": "order_type",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Purchase Receipt": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "is_return",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Request for Quotation": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "transaction_date",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Stock Module
	"Stock Entry": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "stock_entry_type",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Accounting Module  
	"Payment Entry": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "payment_type",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Journal Entry": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "voucher_type",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# HR Module
	"Salary Slip": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nPaid\nDuplicate",
			"default": "None",
			"insert_after": "employee",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Offer Letter": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSent\nAccepted\nRejected\nDuplicate",
			"default": "None",
			"insert_after": "applicant_name",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	"Appraisal": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCompleted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "employee",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Project Module
	"Project": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nActive\nCompleted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "status",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Quality Module
	"Quality Inspection": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nAccepted\nRejected\nDuplicate",
			"default": "None",
			"insert_after": "quality_inspection_template",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Maintenance Module
	"Maintenance Schedule": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nActive\nCompleted\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "maintenance_schedule_details",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Asset Module
	"Asset": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nSubmitted\nActive\nSold\nScrapped\nDuplicate",
			"default": "None",
			"insert_after": "asset_name",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	],
	
	# Custom DocTypes (if they exist)
	"Contract": [
		{
			"fieldname": "watermark_text",
			"fieldtype": "Select",
			"label": "Document Watermark",
			"options": "None\nOriginal\nCopy\nDraft\nActive\nExpired\nCancelled\nDuplicate",
			"default": "None",
			"insert_after": "contract_terms",
			"print_hide": 1,
			"allow_on_submit": 1,
			"translatable": 1,
			"description": "Watermark text to display on printed document"
		}
	]
}

# Function to get all watermark fields for installation
def get_watermark_fields():
	"""
	Returns all watermark fields in the format expected by Frappe's custom fields system
	"""
	return WATERMARK_FIELDS

# Function to get watermark fields for a specific DocType
def get_watermark_fields_for_doctype(doctype):
	"""
	Returns watermark fields for a specific DocType
	"""
	return WATERMARK_FIELDS.get(doctype, [])

# Function to check if a DocType has watermark fields
def has_watermark_fields(doctype):
	"""
	Check if a DocType has watermark fields configured
	"""
	return doctype in WATERMARK_FIELDS

# Function to get all DocTypes with watermark fields
def get_doctypes_with_watermarks():
	"""
	Returns list of all DocTypes that have watermark fields
	"""
	return list(WATERMARK_FIELDS.keys())

# Function to get watermark options for a specific DocType
def get_watermark_options_for_doctype(doctype):
	"""
	Returns available watermark options for a specific DocType
	"""
	fields = get_watermark_fields_for_doctype(doctype)
	if fields:
		for field in fields:
			if field.get("fieldname") == "watermark_text":
				return field.get("options", "").split("\n")
	return []

# Legacy compatibility function (for existing code)
def get_watermark_custom_fields():
	"""
	Generate custom field definitions for watermark fields
	Returns fields in the format expected by create_custom_fields()
	"""
	return WATERMARK_FIELDS

# Function to install watermark fields
def install_watermark_fields():
	"""
	Install watermark custom fields for all configured DocTypes
	"""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	
	try:
		custom_fields = get_watermark_custom_fields()
		create_custom_fields(custom_fields, update=True)
		print("✅ Watermark custom fields installed successfully")
		return True
	except Exception as e:
		print(f"❌ Error installing watermark fields: {str(e)}")
		return False

# Function to uninstall watermark fields
def uninstall_watermark_fields():
	"""
	Remove watermark custom fields from all configured DocTypes
	"""
	import frappe
	
	try:
		for doctype, fields in WATERMARK_FIELDS.items():
			for field_config in fields:
				fieldname = field_config["fieldname"]
				
				# Delete custom field if it exists
				if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
					frappe.delete_doc("Custom Field", frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname}, "name"))
		
		print("✅ Watermark custom fields removed successfully")
		return True
	except Exception as e:
		print(f"❌ Error removing watermark fields: {str(e)}")
		return False

# Function to get watermark text from document
def get_watermark_text_from_doc(doctype, docname):
	"""
	Get watermark text from a specific document
	"""
	import frappe
	
	if not has_watermark_fields(doctype):
		return None
		
	try:
		doc = frappe.get_doc(doctype, docname)
		return doc.get("watermark_text")
	except:
		return None

# Function to set watermark text for document  
def set_watermark_text_for_doc(doctype, docname, watermark_text):
	"""
	Set watermark text for a specific document
	"""
	import frappe
	
	if not has_watermark_fields(doctype):
		return False
		
	try:
		doc = frappe.get_doc(doctype, docname)
		doc.watermark_text = watermark_text
		doc.save()
		return True
	except:
		return False