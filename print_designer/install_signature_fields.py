#!/usr/bin/env python3
"""
Installation script for signature fields in Print Designer
This script adds signature image fields to various DocTypes for use in print formats
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from .signature_fields import get_signature_fields, get_doctypes_with_signatures

def install_signature_fields():
	"""
	Install signature fields for all configured DocTypes
	"""
	print("Installing signature fields for Print Designer...")
	
	# Get signature fields configuration
	signature_fields = get_signature_fields()
	
	# Track installation progress
	installed_count = 0
	failed_count = 0
	skipped_count = 0
	
	for doctype, fields in signature_fields.items():
		try:
			# Check if DocType exists
			if not frappe.db.exists("DocType", doctype):
				print(f"⚠️  DocType '{doctype}' not found, skipping signature fields")
				skipped_count += 1
				continue
			
			# Create custom fields for this DocType
			create_custom_fields({doctype: fields})
			
			print(f"✅ Installed {len(fields)} signature field(s) for '{doctype}'")
			installed_count += 1
			
		except Exception as e:
			print(f"❌ Failed to install signature fields for '{doctype}': {str(e)}")
			failed_count += 1
	
	# Print summary
	print(f"\n📊 Installation Summary:")
	print(f"   ✅ Successfully installed: {installed_count} DocTypes")
	print(f"   ❌ Failed installations: {failed_count} DocTypes")
	print(f"   ⚠️  Skipped (DocType not found): {skipped_count} DocTypes")
	
	if failed_count == 0:
		print("🎉 All signature fields installed successfully!")
	else:
		print(f"⚠️  {failed_count} installations failed. Check the error messages above.")
	
	# Commit the transaction
	frappe.db.commit()
	
	return {
		"installed": installed_count,
		"failed": failed_count,
		"skipped": skipped_count
	}

def verify_signature_fields():
	"""
	Verify that signature fields are properly installed and discoverable
	"""
	print("\nVerifying signature field installation...")
	
	# Import the get_image_docfields function
	from .print_designer.page.print_designer.print_designer import get_image_docfields
	
	# Get all image fields (including signature fields)
	image_fields = get_image_docfields()
	
	# Filter for signature fields
	signature_field_names = [
		'signature_image', 'authorized_signature_1', 'authorized_signature_2', 
		'ceo_signature', 'project_manager_signature', 'quality_inspector_signature',
		'prepared_by_signature', 'approved_by_signature', 'delivered_by_signature',
		'received_by_signature', 'custodian_signature', 'hr_signature',
		'candidate_signature', 'appraiser_signature', 'employee_signature',
		'inspector_signature', 'supervisor_signature', 'technician_signature',
		'party_signature', 'witness_signature'
	]
	
	discovered_signatures = [
		field for field in image_fields 
		if field.get('fieldname') in signature_field_names
	]
	
	print(f"🔍 Found {len(discovered_signatures)} signature fields in image field discovery")
	
	# Group by DocType for better readability
	signatures_by_doctype = {}
	for field in discovered_signatures:
		doctype = field.get('parent')
		if doctype not in signatures_by_doctype:
			signatures_by_doctype[doctype] = []
		signatures_by_doctype[doctype].append(field.get('fieldname'))
	
	# Print discovered signature fields
	for doctype, field_names in signatures_by_doctype.items():
		print(f"   📄 {doctype}: {', '.join(field_names)}")
	
	return discovered_signatures

def uninstall_signature_fields():
	"""
	Uninstall signature fields from all DocTypes
	"""
	print("Uninstalling signature fields...")
	
	signature_fields = get_signature_fields()
	removed_count = 0
	failed_count = 0
	
	for doctype, fields in signature_fields.items():
		try:
			# Check if DocType exists
			if not frappe.db.exists("DocType", doctype):
				continue
			
			# Remove each field
			for field in fields:
				field_name = field.get('fieldname')
				if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
					frappe.delete_doc("Custom Field", {"dt": doctype, "fieldname": field_name})
					removed_count += 1
			
			print(f"✅ Removed signature fields from '{doctype}'")
			
		except Exception as e:
			print(f"❌ Failed to remove signature fields from '{doctype}': {str(e)}")
			failed_count += 1
	
	print(f"\n📊 Uninstallation Summary:")
	print(f"   ✅ Successfully removed: {removed_count} fields")
	print(f"   ❌ Failed removals: {failed_count} fields")
	
	# Commit the transaction
	frappe.db.commit()
	
	return {
		"removed": removed_count,
		"failed": failed_count
	}

# CLI interface functions
@frappe.whitelist()
def install():
	"""
	Install signature fields (callable from Frappe console)
	"""
	return install_signature_fields()

@frappe.whitelist()
def verify():
	"""
	Verify signature fields installation (callable from Frappe console)
	"""
	return verify_signature_fields()

@frappe.whitelist()
def uninstall():
	"""
	Uninstall signature fields (callable from Frappe console)
	"""
	return uninstall_signature_fields()

@frappe.whitelist()
def status():
	"""
	Check status of signature fields installation
	"""
	print("Signature Fields Status:")
	print("=" * 50)
	
	# Check each DocType
	signature_fields = get_signature_fields()
	
	for doctype, fields in signature_fields.items():
		if not frappe.db.exists("DocType", doctype):
			print(f"❌ {doctype}: DocType not found")
			continue
		
		installed_fields = []
		missing_fields = []
		
		for field in fields:
			field_name = field.get('fieldname')
			if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_name}):
				installed_fields.append(field_name)
			else:
				missing_fields.append(field_name)
		
		if missing_fields:
			print(f"⚠️  {doctype}: {len(missing_fields)} missing, {len(installed_fields)} installed")
		else:
			print(f"✅ {doctype}: All {len(installed_fields)} fields installed")
	
	return True

if __name__ == "__main__":
	# This allows the script to be run directly
	import sys
	
	if len(sys.argv) > 1:
		command = sys.argv[1]
		if command == "install":
			install_signature_fields()
		elif command == "verify":
			verify_signature_fields()
		elif command == "uninstall":
			uninstall_signature_fields()
		elif command == "status":
			status()
		else:
			print("Usage: python install_signature_fields.py [install|verify|uninstall|status]")
	else:
		print("Available commands:")
		print("  install   - Install signature fields")
		print("  verify    - Verify installation")
		print("  uninstall - Remove signature fields")
		print("  status    - Check installation status")