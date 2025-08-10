import frappe
from frappe import _


def execute():
	"""
	Fix Target Signature Field dropdown options for existing installations.
	This patch ensures that the signature_target_field Custom Field has proper options populated.
	"""
	try:
		frappe.log("Starting Target Signature Field options fix...")
		
		# Import the fix function
		from print_designer.commands.fix_target_signature_field import fix_signature_target_field_options
		
		# Execute the fix
		result = fix_signature_target_field_options()
		
		if result.get('success'):
			frappe.log(f"Target Signature Field fix successful: {result.get('message')}")
			frappe.log(f"Options populated: {result.get('options_count', 0)}")
			frappe.log(f"Fields updated: {result.get('fields_updated', 0)}")
		else:
			frappe.log(f"Target Signature Field fix failed: {result.get('error')}")
			# Don't fail the migration completely, just log the error
			frappe.log_error(f"Target Signature Field fix error: {result.get('error')}")
		
	except Exception as e:
		frappe.log_error(f"Error in Target Signature Field options fix patch: {str(e)}")
		frappe.log(f"Warning: Target Signature Field options fix failed: {str(e)}")