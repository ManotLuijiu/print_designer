import frappe
from frappe import _


def execute():
	"""
	Migration patch to enhance Signature Basic Information DocType with target field mapping
	This patch is safe to run multiple times (idempotent)
	"""
	try:
		frappe.log("Starting enhancement of Signature Basic Information DocType...")
		
		# Step 1: Install signature fields for core DocTypes (safe install)
		install_core_signature_fields()
		
		# Step 2: Enhance Signature Basic Information DocType
		enhance_signature_doctype()
		
		# Step 3: Migrate existing signature records
		migrate_existing_signatures()
		
		frappe.log("Successfully enhanced Signature Basic Information DocType")
		
	except Exception as e:
		frappe.log_error(f"Error in signature enhancement migration: {str(e)}")
		# Don't fail the migration, just log the error
		frappe.log(f"Warning: Signature enhancement failed: {str(e)}")


def install_core_signature_fields():
	"""Install signature fields for core DocTypes that are guaranteed to exist"""
	try:
		from print_designer.signature_fields import get_signature_fields
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
		
		# Only install for DocTypes that definitely exist in ERPNext/Frappe
		core_doctypes = ["Company", "User", "Employee"]
		
		signature_fields = get_signature_fields()
		safe_fields = {}
		
		for doctype in core_doctypes:
			if doctype in signature_fields and frappe.db.exists("DocType", doctype):
				# Check if fields are already installed
				existing_fields = frappe.get_all(
					"Custom Field",
					filters={"dt": doctype},
					fields=["fieldname"]
				)
				existing_fieldnames = [f.fieldname for f in existing_fields]
				
				# Only add fields that don't exist
				new_fields = []
				for field in signature_fields[doctype]:
					if field["fieldname"] not in existing_fieldnames:
						new_fields.append(field)
				
				if new_fields:
					safe_fields[doctype] = new_fields
					frappe.log(f"Installing {len(new_fields)} signature fields for {doctype}")
		
		if safe_fields:
			create_custom_fields(safe_fields, ignore_validate=True)
			frappe.log(f"Installed signature fields for {len(safe_fields)} DocTypes")
		else:
			frappe.log("All core signature fields already installed")
			
	except Exception as e:
		frappe.log_error(f"Error installing core signature fields: {str(e)}")
		# Continue with migration even if this fails


def enhance_signature_doctype():
	"""Add enhancement fields to Signature Basic Information DocType"""
	try:
		from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
		
		# Check if enhancement fields already exist
		existing_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "Signature Basic Information"},
			fields=["fieldname"]
		)
		existing_fieldnames = [f.fieldname for f in existing_fields]
		
		# Define enhancement fields
		enhancement_fields = [
			{
				"fieldname": "signature_target_field",
				"fieldtype": "Select",
				"label": "Target Signature Field",
				"description": "Select which document field this signature should populate",
				"insert_after": "signature_field_name",
				"options": "",  # Will be populated dynamically
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
		
		# Only add fields that don't exist
		new_fields = []
		for field in enhancement_fields:
			if field["fieldname"] not in existing_fieldnames:
				new_fields.append(field)
		
		if new_fields:
			custom_fields = {"Signature Basic Information": new_fields}
			create_custom_fields(custom_fields, ignore_validate=True)
			frappe.log(f"Added {len(new_fields)} enhancement fields to Signature Basic Information")
		else:
			frappe.log("Enhancement fields already exist for Signature Basic Information")
			
	except Exception as e:
		frappe.log_error(f"Error enhancing signature DocType: {str(e)}")
		# Continue with migration even if this fails


def migrate_existing_signatures():
	"""Migrate existing signature records to use new target field mapping"""
	try:
		# Get all existing signature records that don't have target field mapping
		existing_signatures = frappe.get_all(
			"Signature Basic Information",
			filters={
				"signature_category": "Signature",
				"target_doctype": ["is", "not set"]  # New field will be empty
			},
			fields=["name", "signature_title", "company", "user", "signature_field_name"]
		)
		
		if not existing_signatures:
			frappe.log("No existing signatures to migrate")
			return
		
		frappe.log(f"Migrating {len(existing_signatures)} existing signature records")
		
		for signature in existing_signatures:
			try:
				# Determine target DocType and field based on existing data
				target_doctype = None
				target_field = None
				
				# Try to guess target based on signature title and context
				if signature.signature_title and "CEO" in signature.signature_title.upper():
					target_doctype = "Company"
					target_field = "Company::ceo_signature"
				elif signature.user:
					target_doctype = "User"
					target_field = "User::signature_image"
				elif signature.company:
					target_doctype = "Company"
					target_field = "Company::authorized_signature_1"
				
				# Use legacy field name if available
				if signature.signature_field_name and not target_field:
					# Try to map legacy field name to new format
					legacy_mapping = {
						"ceo_signature": "Company::ceo_signature",
						"authorized_signature_1": "Company::authorized_signature_1",
						"authorized_signature_2": "Company::authorized_signature_2",
						"signature_image": "User::signature_image"
					}
					target_field = legacy_mapping.get(signature.signature_field_name)
					if target_field:
						target_doctype = target_field.split("::")[0]
				
				# Update the signature record if we have mapping
				if target_doctype and target_field:
					frappe.db.set_value(
						"Signature Basic Information",
						signature.name,
						{
							"target_doctype": target_doctype,
							"signature_target_field": target_field,
							"auto_populate_field": 1
						}
					)
					frappe.log(f"Migrated signature {signature.name} to {target_field}")
				else:
					frappe.log(f"Could not determine target mapping for signature {signature.name}")
					
			except Exception as e:
				frappe.log_error(f"Error migrating signature {signature.name}: {str(e)}")
				continue
		
		frappe.db.commit()
		frappe.log("Completed migration of existing signature records")
		
	except Exception as e:
		frappe.log_error(f"Error migrating existing signatures: {str(e)}")
		# Continue even if migration fails


def rollback():
	"""
	Optional rollback function (not typically called automatically)
	Customers can call this manually if needed
	"""
	try:
		frappe.log("Rolling back signature enhancement...")
		
		# Remove enhancement fields
		enhancement_fieldnames = ["signature_target_field", "target_doctype", "auto_populate_field"]
		
		for fieldname in enhancement_fieldnames:
			custom_field = frappe.db.exists("Custom Field", {
				"dt": "Signature Basic Information",
				"fieldname": fieldname
			})
			if custom_field:
				frappe.delete_doc("Custom Field", custom_field)
				frappe.log(f"Removed custom field: {fieldname}")
		
		frappe.db.commit()
		frappe.log("Rollback completed")
		
	except Exception as e:
		frappe.log_error(f"Error during rollback: {str(e)}")
		raise