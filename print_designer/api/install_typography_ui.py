"""
Install Typography UI in Global Defaults

This module handles the installation of typography custom fields
directly into the Global Defaults DocType.
"""

import frappe
from frappe import _


@frappe.whitelist()
def install_typography_fields_manually():
	"""
	Manually install typography fields to Global Defaults.
	This function can be called via bench execute or API.
	"""
	try:
		# Typography Section
		if not frappe.db.exists("Custom Field", {"dt": "Global Defaults", "fieldname": "typography_section"}):
			typography_section = frappe.new_doc("Custom Field")
			typography_section.dt = "Global Defaults"
			typography_section.fieldname = "typography_section"
			typography_section.fieldtype = "Section Break"
			typography_section.label = "Typography Settings"
			typography_section.insert_after = "disable_in_words"
			typography_section.collapsible = 1
			typography_section.description = "Configure system-wide font preferences"
			typography_section.insert()
			print("✓ Typography section created")
		
		# Primary Font Family
		if not frappe.db.exists("Custom Field", {"dt": "Global Defaults", "fieldname": "primary_font_family"}):
			primary_font = frappe.new_doc("Custom Field")
			primary_font.dt = "Global Defaults"
			primary_font.fieldname = "primary_font_family"
			primary_font.fieldtype = "Select"
			primary_font.label = "Primary Font Family"
			primary_font.options = "System Default\nSarabun (Thai)\nNoto Sans Thai\nIBM Plex Sans Thai\nKanit (Thai)\nPrompt (Thai)\nMitr (Thai)\nPridi (Thai)\nInter\nRoboto\nOpen Sans\nLato\nNunito Sans"
			primary_font.default = "Sarabun (Thai)"
			primary_font.insert_after = "typography_section"
			primary_font.description = "Primary font family for the system interface and documents. Thai fonts provide optimal Unicode support for Thai text."
			primary_font.insert()
			print("✓ Primary font family field created")
		
		# Column Break
		if not frappe.db.exists("Custom Field", {"dt": "Global Defaults", "fieldname": "font_preferences_column"}):
			column_break = frappe.new_doc("Custom Field")
			column_break.dt = "Global Defaults"
			column_break.fieldname = "font_preferences_column"
			column_break.fieldtype = "Column Break"
			column_break.insert_after = "primary_font_family"
			column_break.insert()
			print("✓ Font preferences column break created")
		
		# Enable Thai Font Support
		if not frappe.db.exists("Custom Field", {"dt": "Global Defaults", "fieldname": "enable_thai_font_support"}):
			thai_support = frappe.new_doc("Custom Field")
			thai_support.dt = "Global Defaults"
			thai_support.fieldname = "enable_thai_font_support"
			thai_support.fieldtype = "Check"
			thai_support.label = "Enable Thai Font Support"
			thai_support.default = "1"
			thai_support.insert_after = "font_preferences_column"
			thai_support.description = "Enable system-wide Thai font support and optimizations"
			thai_support.insert()
			print("✓ Thai font support field created")
		
		# Custom Font Stack
		if not frappe.db.exists("Custom Field", {"dt": "Global Defaults", "fieldname": "custom_font_stack"}):
			custom_stack = frappe.new_doc("Custom Field")
			custom_stack.dt = "Global Defaults"
			custom_stack.fieldname = "custom_font_stack"
			custom_stack.fieldtype = "Small Text"
			custom_stack.label = "Custom Font Stack"
			custom_stack.insert_after = "enable_thai_font_support"
			custom_stack.depends_on = "eval:doc.primary_font_family == 'System Default'"
			custom_stack.description = "Comma-separated list of font families for custom font stack. Example: 'Sarabun', 'Noto Sans Thai', 'Arial', sans-serif"
			custom_stack.insert()
			print("✓ Custom font stack field created")
		
		# CSS Storage (Hidden)
		if not frappe.db.exists("Custom Field", {"dt": "Global Defaults", "fieldname": "custom_typography_css"}):
			css_storage = frappe.new_doc("Custom Field")
			css_storage.dt = "Global Defaults"
			css_storage.fieldname = "custom_typography_css"
			css_storage.fieldtype = "Long Text"
			css_storage.label = "Custom Typography CSS"
			css_storage.insert_after = "custom_font_stack"
			css_storage.hidden = 1
			css_storage.read_only = 1
			css_storage.description = "Generated CSS for typography override - managed automatically"
			css_storage.insert()
			print("✓ CSS storage field created")
		
		frappe.db.commit()
		
		# Set default values in Global Defaults
		global_defaults = frappe.get_single("Global Defaults")
		if not global_defaults.get("primary_font_family"):
			global_defaults.primary_font_family = "Sarabun (Thai)"
			global_defaults.enable_thai_font_support = 1
			global_defaults.save(ignore_permissions=True)
			print("✓ Default typography values set")
		
		return {
			"success": True,
			"message": "Typography fields installed successfully"
		}
		
	except Exception as e:
		frappe.log_error(f"Typography field installation error: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def check_typography_installation():
	"""
	Check if typography fields are properly installed.
	"""
	required_fields = [
		"typography_section",
		"primary_font_family", 
		"font_preferences_column",
		"enable_thai_font_support",
		"custom_font_stack",
		"custom_typography_css"
	]
	
	installed_fields = []
	missing_fields = []
	
	for field in required_fields:
		if frappe.db.exists("Custom Field", {"dt": "Global Defaults", "fieldname": field}):
			installed_fields.append(field)
		else:
			missing_fields.append(field)
	
	return {
		"installed_fields": installed_fields,
		"missing_fields": missing_fields,
		"installation_complete": len(missing_fields) == 0
	}


def setup_typography_on_install():
	"""
	Called during app installation to setup typography fields.
	"""
	print("Setting up typography fields...")
	result = install_typography_fields_manually()
	
	if result.get("success"):
		print("Typography fields setup complete!")
	else:
		print(f"Typography setup failed: {result.get('error')}")