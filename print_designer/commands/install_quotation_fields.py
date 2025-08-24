"""
Programmatic Custom Field Installation for Quotation
====================================================

This module provides programmatic installation of custom fields for Quotation DocType,
maintaining exact field order and section grouping as defined in custom_field.json.

This system is designed to work in production environments where fixture-based
installation may not be reliable.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import flt, cint


def install_quotation_custom_fields():
	"""
	Install all custom fields for Quotation DocType programmatically
	
	This function creates custom fields in the exact order and structure
	as defined in the custom_field.json fixture file.
	
	Returns:
		dict: Installation status and results
	"""
	try:
		print("=== Installing Quotation Custom Fields ===")
		
		# Define custom fields in exact order from custom_field.json
		custom_fields = get_quotation_custom_fields_definition()
		
		# Install fields using Frappe's standard method
		create_custom_fields(custom_fields, update=True)
		
		# Validate installation
		validation_result = validate_quotation_fields_installation()
		
		print("✅ Quotation custom fields installation completed successfully")
		
		return {
			"success": True,
			"fields_installed": len(custom_fields["Quotation"]),
			"validation": validation_result
		}
		
	except Exception as e:
		error_msg = f"Error installing Quotation custom fields: {str(e)}"
		print(f"❌ {error_msg}")
		frappe.log_error(error_msg, "Quotation Fields Installation Error")
		return {
			"success": False,
			"error": error_msg
		}


def get_quotation_custom_fields_definition():
	"""
	Define all Quotation custom fields in exact order from custom_field.json
	
	This maintains the precise field ordering and section grouping:
	1. Thailand Business Section (fields 1-3)
	2. Retention Section (fields 4-8) 
	3. Withholding Tax Section (fields 9-14)
	4. Final Amounts Section (fields 15-22)
	
	Returns:
		dict: Custom fields definition for create_custom_fields()
	"""
	
	return {
		"Quotation": [
			# === THAILAND BUSINESS SECTION ===
			{
				"fieldname": "thailand_business_section",
				"label": "Thailand Business",
				"fieldtype": "Section Break",
				"insert_after": "tax_category",
				"collapsible": 1,
				"depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'country') === 'Thailand'"
			},
			{
				"fieldname": "custom_item_service_type",
				"label": "Service Type",
				"fieldtype": "Select",
				"options": "Service\nProduct\nBoth",
				"default": "Service",
				"insert_after": "thailand_business_section"
			},
			{
				"fieldname": "thailand_column_break_1",
				"fieldtype": "Column Break",
				"insert_after": "custom_item_service_type"
			},
			
			# === RETENTION SECTION ===
			{
				"fieldname": "retention_section",
				"label": "Retention",
				"fieldtype": "Section Break",
				"insert_after": "thailand_column_break_1",
				"collapsible": 1,
				"depends_on": "eval:doc.thailand_business_section && doc.custom_item_service_type === 'Service'"
			},
			{
				"fieldname": "custom_enable_retention",
				"label": "Enable Retention",
				"fieldtype": "Check",
				"default": 0,
				"insert_after": "retention_section"
			},
			{
				"fieldname": "custom_retention_percentage",
				"label": "Retention (%)",
				"fieldtype": "Float",
				"precision": 2,
				"default": 5.0,
				"insert_after": "custom_enable_retention",
				"depends_on": "custom_enable_retention",
				"mandatory_depends_on": "custom_enable_retention"
			},
			{
				"fieldname": "custom_retention_amount",
				"label": "Retention Amount",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "custom_retention_percentage",
				"depends_on": "custom_enable_retention"
			},
			{
				"fieldname": "retention_column_break",
				"fieldtype": "Column Break",
				"insert_after": "custom_retention_amount"
			},
			{
				"fieldname": "custom_net_total_after_retention",
				"label": "Net Total After Retention",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "retention_column_break",
				"depends_on": "custom_enable_retention"
			},
			
			# === WITHHOLDING TAX SECTION ===
			{
				"fieldname": "withholding_tax_section",
				"label": "Withholding Tax",
				"fieldtype": "Section Break",
				"insert_after": "custom_net_total_after_retention",
				"collapsible": 1,
				"depends_on": "eval:doc.thailand_business_section"
			},
			{
				"fieldname": "custom_withholding_tax",
				"label": "Withholding Tax (%)",
				"fieldtype": "Float",
				"precision": 2,
				"default": 3.0,
				"insert_after": "withholding_tax_section"
			},
			{
				"fieldname": "custom_withholding_tax_amount",
				"label": "Withholding Tax Amount",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "custom_withholding_tax"
			},
			{
				"fieldname": "custom_net_total_after_wht",
				"label": "Net Total After WHT",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "custom_withholding_tax_amount"
			},
			{
				"fieldname": "withholding_column_break",
				"fieldtype": "Column Break",
				"insert_after": "custom_net_total_after_wht"
			},
			{
				"fieldname": "custom_wht_base_amount",
				"label": "WHT Base Amount",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "withholding_column_break"
			},
			{
				"fieldname": "custom_subject_to_wht",
				"label": "Subject to WHT",
				"fieldtype": "Check",
				"default": 1,
				"insert_after": "custom_wht_base_amount"
			},
			
			# === FINAL AMOUNTS SECTION ===
			{
				"fieldname": "final_amounts_section",
				"label": "Final Payment Amounts",
				"fieldtype": "Section Break",
				"insert_after": "custom_subject_to_wht",
				"collapsible": 1,
				"depends_on": "eval:doc.thailand_business_section"
			},
			{
				"fieldname": "custom_payment_amount",
				"label": "Net Cash to be Paid",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "final_amounts_section",
				"bold": 1
			},
			{
				"fieldname": "final_amounts_column_break",
				"fieldtype": "Column Break",
				"insert_after": "custom_payment_amount"
			},
			{
				"fieldname": "custom_total_withholding_retention",
				"label": "Total Retention + WHT",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "final_amounts_column_break"
			},
			{
				"fieldname": "custom_payment_breakdown_html",
				"label": "Payment Breakdown",
				"fieldtype": "HTML",
				"insert_after": "custom_total_withholding_retention",
				"depends_on": "eval:doc.custom_enable_retention || doc.custom_withholding_tax > 0"
			},
			{
				"fieldname": "custom_contract_value_display",
				"label": "Contract Value (Display)",
				"fieldtype": "Currency",
				"read_only": 1,
				"insert_after": "custom_payment_breakdown_html"
			}
		]
	}


def validate_quotation_fields_installation():
	"""
	Validate that all Quotation custom fields are properly installed
	
	Returns:
		dict: Validation results
	"""
	try:
		print("\n=== Validating Quotation Fields Installation ===")
		
		# Get installed fields from database
		installed_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "Quotation"},
			fields=["fieldname", "fieldtype", "label", "insert_after", "depends_on"],
			order_by="idx asc, modified asc"
		)
		
		# Expected fields from definition
		expected_fields_def = get_quotation_custom_fields_definition()
		expected_fields = expected_fields_def["Quotation"]
		
		# Create lookup for validation
		installed_lookup = {field['fieldname']: field for field in installed_fields}
		expected_lookup = {field['fieldname']: field for field in expected_fields}
		
		# Validation checks
		missing_fields = []
		field_mismatches = []
		
		for field_def in expected_fields:
			fieldname = field_def['fieldname']
			
			if fieldname not in installed_lookup:
				missing_fields.append(fieldname)
			else:
				# Check key properties match
				installed_field = installed_lookup[fieldname]
				
				# Compare essential properties
				essential_props = ['fieldtype', 'label', 'insert_after']
				for prop in essential_props:
					expected_val = field_def.get(prop)
					installed_val = installed_field.get(prop)
					
					if expected_val and expected_val != installed_val:
						field_mismatches.append({
							'fieldname': fieldname,
							'property': prop,
							'expected': expected_val,
							'installed': installed_val
						})
		
		# Report results
		print(f"📊 Expected fields: {len(expected_fields)}")
		print(f"📊 Installed fields: {len(installed_fields)}")
		print(f"📊 Missing fields: {len(missing_fields)}")
		print(f"📊 Field mismatches: {len(field_mismatches)}")
		
		if missing_fields:
			print(f"❌ Missing fields: {missing_fields}")
		
		if field_mismatches:
			print(f"⚠️  Field mismatches found:")
			for mismatch in field_mismatches:
				print(f"   {mismatch['fieldname']}.{mismatch['property']}: expected='{mismatch['expected']}', installed='{mismatch['installed']}'")
		
		if not missing_fields and not field_mismatches:
			print("✅ All fields validated successfully!")
		
		return {
			"expected_count": len(expected_fields),
			"installed_count": len(installed_fields),
			"missing_fields": missing_fields,
			"field_mismatches": field_mismatches,
			"validation_passed": len(missing_fields) == 0 and len(field_mismatches) == 0
		}
		
	except Exception as e:
		error_msg = f"Error validating Quotation fields: {str(e)}"
		print(f"❌ {error_msg}")
		return {
			"validation_passed": False,
			"error": error_msg
		}


def check_quotation_fields_status():
	"""
	Check current status of Quotation custom fields installation
	
	Returns:
		dict: Current status information
	"""
	try:
		print("=== Checking Quotation Fields Status ===")
		
		# Get current fields
		current_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "Quotation"},
			fields=["fieldname", "fieldtype", "label", "insert_after"],
			order_by="idx asc, modified asc"
		)
		
		# Expected fields count
		expected_def = get_quotation_custom_fields_definition()
		expected_count = len(expected_def["Quotation"])
		
		print(f"📊 Current fields: {len(current_fields)}")
		print(f"📊 Expected fields: {expected_count}")
		
		# Show field summary
		if current_fields:
			print("\n📋 Current Field Order:")
			for i, field in enumerate(current_fields, 1):
				insert_after = f" | after: {field['insert_after']}" if field['insert_after'] else ""
				print(f"{i:2d}. {field['fieldname']:<35} | {field['fieldtype']:<15}{insert_after}")
		else:
			print("❌ No Quotation custom fields found")
		
		return {
			"current_count": len(current_fields),
			"expected_count": expected_count,
			"fields_installed": len(current_fields) > 0,
			"needs_installation": len(current_fields) != expected_count
		}
		
	except Exception as e:
		error_msg = f"Error checking Quotation fields status: {str(e)}"
		print(f"❌ {error_msg}")
		return {
			"error": error_msg,
			"fields_installed": False
		}


def reinstall_quotation_custom_fields():
	"""
	Reinstall all Quotation custom fields (useful for updates/fixes)
	
	This will update existing fields and add any missing ones.
	
	Returns:
		dict: Reinstallation results
	"""
	try:
		print("=== Reinstalling Quotation Custom Fields ===")
		
		# Get current status
		status = check_quotation_fields_status()
		print(f"Current status: {status['current_count']}/{status['expected_count']} fields")
		
		# Perform installation (with update=True to modify existing fields)
		result = install_quotation_custom_fields()
		
		if result['success']:
			print("✅ Quotation custom fields reinstallation completed")
		else:
			print(f"❌ Reinstallation failed: {result.get('error')}")
		
		return result
		
	except Exception as e:
		error_msg = f"Error reinstalling Quotation custom fields: {str(e)}"
		print(f"❌ {error_msg}")
		return {
			"success": False,
			"error": error_msg
		}


# Convenience functions for command execution
def main():
	"""Main execution function for command line usage"""
	return install_quotation_custom_fields()


if __name__ == "__main__":
	main()