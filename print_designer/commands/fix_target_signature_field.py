import frappe
import click
from frappe.commands import pass_context


@click.command('fix-target-signature-field')
@pass_context
def fix_target_signature_field(context):
	"""
	Fix the Target Signature Field dropdown by populating it with proper values.
	This command fixes installations where the dropdown is empty.
	"""
	site = context.obj['sites'][0]
	
	with frappe.init_site(site):
		frappe.connect()
		result = fix_signature_target_field_options()
		
		if result.get('success'):
			click.echo(f"✅ Successfully fixed Target Signature Field dropdown")
			click.echo(f"   - Options populated: {result.get('options_count', 0)}")
			click.echo(f"   - Fields updated: {result.get('fields_updated', 0)}")
			if result.get('message'):
				click.echo(f"   - {result['message']}")
		else:
			click.echo(f"❌ Failed to fix Target Signature Field dropdown")
			click.echo(f"   - Error: {result.get('error', 'Unknown error')}")
		
		frappe.destroy()


@frappe.whitelist()
def fix_signature_target_field_options():
	"""
	Fix the signature_target_field Custom Field by populating it with proper options.
	
	Returns:
		dict: Fix results
	"""
	try:
		# Get signature field options
		from print_designer.api.signature_field_options import get_signature_field_options_string
		
		options_string = get_signature_field_options_string()
		
		if not options_string:
			return {
				"error": "Could not generate signature field options. Make sure signature fields are installed first."
			}
		
		options_count = len(options_string.split('\n'))
		frappe.log(f"Generated {options_count} signature field options")
		
		# Find the signature_target_field Custom Field
		custom_field = frappe.db.get_value(
			"Custom Field",
			{"dt": "Signature Basic Information", "fieldname": "signature_target_field"},
			["name", "options"]
		)
		
		if not custom_field:
			return {
				"error": "Target Signature Field custom field not found. Run signature enhancement installation first."
			}
		
		field_name, current_options = custom_field
		
		# Check if field needs updating
		if current_options and current_options.strip() and len(current_options.split('\n')) > 1:
			return {
				"success": True,
				"message": "Target Signature Field already has options populated",
				"options_count": len(current_options.split('\n')),
				"fields_updated": 0
			}
		
		# Update the field with proper options
		frappe.db.set_value("Custom Field", field_name, "options", options_string)
		frappe.db.commit()
		
		# Clear cache to ensure the new options are loaded
		frappe.clear_cache()
		
		return {
			"success": True,
			"message": "Target Signature Field options updated successfully",
			"options_count": options_count,
			"fields_updated": 1,
			"field_name": field_name
		}
		
	except Exception as e:
		frappe.log_error(f"Error fixing signature target field options: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def check_target_signature_field_status():
	"""
	Check the current status of the Target Signature Field dropdown.
	
	Returns:
		dict: Status information
	"""
	try:
		# Check if the custom field exists
		custom_field = frappe.db.get_value(
			"Custom Field",
			{"dt": "Signature Basic Information", "fieldname": "signature_target_field"},
			["name", "options", "label"]
		)
		
		if not custom_field:
			return {
				"success": False,
				"status": "missing",
				"message": "Target Signature Field custom field not found"
			}
		
		field_name, options, label = custom_field
		
		# Analyze options
		options_count = 0
		if options and options.strip():
			options_count = len(options.split('\n'))
			# Remove empty first option if it exists
			if options.startswith('\n'):
				options_count -= 1
		
		# Check if signature field options API works
		api_status = "unknown"
		try:
			from print_designer.api.signature_field_options import get_signature_field_options_string
			api_options = get_signature_field_options_string()
			api_status = "working" if api_options else "empty"
		except Exception as e:
			api_status = f"error: {str(e)}"
		
		status = "populated" if options_count > 0 else "empty"
		
		return {
			"success": True,
			"status": status,
			"field_name": field_name,
			"label": label,
			"options_count": options_count,
			"current_options": options[:200] + "..." if options and len(options) > 200 else options,
			"api_status": api_status,
			"needs_fix": status == "empty"
		}
		
	except Exception as e:
		frappe.log_error(f"Error checking target signature field status: {str(e)}")
		return {"error": str(e)}


def execute():
	"""
	Patch execution function - can be called during migration
	"""
	result = fix_signature_target_field_options()
	if result.get('success'):
		frappe.log(f"Target Signature Field fix applied: {result.get('message')}")
	else:
		frappe.log(f"Target Signature Field fix failed: {result.get('error')}")


commands = [fix_target_signature_field]