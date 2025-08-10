import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	"""Add watermark_settings field to Print Format"""
	
	custom_fields = {
		"Print Format": [
			{
				"depends_on": "eval:doc.print_designer",
				"fieldname": "watermark_settings",
				"fieldtype": "Select",
				"label": "Watermark per Page",
				"options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
				"default": "None",
				"insert_after": "print_designer_template_app",
				"description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'"
			}
		]
	}
	
	create_custom_fields(custom_fields, ignore_validate=True)
	frappe.db.commit()