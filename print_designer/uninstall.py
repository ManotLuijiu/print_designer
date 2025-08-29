import frappe
from frappe import _

from print_designer.custom_fields import CUSTOM_FIELDS
from print_designer.install import set_pdf_generator_option


def delete_custom_fields(custom_fields):
	"""
	:param custom_fields: a dict like `{'Sales Invoice': [{fieldname: 'test', ...}]}`
	"""

	for doctypes, fields in custom_fields.items():
		if isinstance(fields, dict):
			# only one field
			fields = [fields]

		if isinstance(doctypes, str):
			# only one doctype
			doctypes = (doctypes,)

		for doctype in doctypes:
			frappe.db.delete(
				"Custom Field",
				{
					"fieldname": ("in", [field["fieldname"] for field in fields]),
					"dt": doctype,
				},
			)

			frappe.clear_cache(doctype=doctype)


def delete_all_print_designer_custom_fields():
	"""
	Comprehensive removal of ALL custom fields created by print_designer app
	This function discovers and removes all print_designer fields, not just those in CUSTOM_FIELDS
	"""
	print("🗑️ Starting comprehensive print_designer custom fields removal...")
	
	try:
		# Get all custom fields that were likely created by print_designer
		all_custom_fields = frappe.get_all(
			"Custom Field",
			fields=["name", "dt", "fieldname", "label", "owner"],
			order_by="dt, idx"
		)
		
		# Known print_designer SPECIFIC field patterns (exclude generic terms)
		print_designer_specific_patterns = [
			# Direct print_designer field names (very specific)
			"print_designer",
			# Print Designer specific field types (exact matches)
			"print_designer_print_format", "print_designer_body", "print_designer_header",
			"print_designer_footer", "print_designer_settings", "print_designer_preview",
			"print_designer_after_table", "print_designer_template_app", 
			# Watermark fields (print_designer specific)
			"watermark_settings", "watermark_font", "watermark_position", "watermark_per_page",
			# Copy/multiple copy system (print_designer feature)
			"enable_multiple_copies", "default_copy_count", "copy_labels", "show_copy_controls",
			"default_original_label", "default_copy_label",
			# Signature fields created by print_designer signature system
			"prepared_by_signature", "approved_by_signature",
			# Delivery approval QR system (print_designer feature)
			"custom_delivery_approval_section", "customer_approval_status", "customer_signature",
			"customer_approved_by", "customer_approved_on", "approval_qr_code", "custom_approval_url",
			"custom_goods_received_status", "custom_approval_qr_code", "custom_customer_approval_date",
			"custom_approved_by", "custom_customer_signature", "custom_rejection_reason",
			# Typography system (print_designer feature)
			"typography_section", "primary_font_family", "font_preferences_column", 
			"enable_thai_font_support", "custom_font_stack", "custom_typography_css",
		]
		
		# Sales Invoice fields SPECIFICALLY created by print_designer install_sales_invoice_fields.py
		print_designer_sales_invoice_fields = [
			# Watermark field
			"watermark_text",
			# Thai WHT Preview Section (print_designer specific)
			"thai_wht_preview_section", "wht_amounts_column_break", "wht_preview_column_break", 
			"vat_treatment", "subject_to_wht", "wht_income_type", "wht_description",
			"net_total_after_wht", "net_total_after_wht_in_words", "wht_certificate_required", "wht_note",
			# Retention fields (print_designer construction feature)
			"custom_subject_to_retention", "custom_net_total_after_wht_retention", 
			"custom_net_total_after_wht_retention_in_words", "custom_retention_note",
			"custom_retention", "custom_retention_amount",
			# Construction service (print_designer feature)
			"construction_service",
			# WHT calculation fields (print_designer calculations)
			"custom_withholding_tax", "custom_withholding_tax_amount", "custom_payment_amount",
			# Signature fields
			"prepared_by_signature", "approved_by_signature",
		]
		
		# Fields in hooks.py (fixtures) - these are definitely print_designer fields
		fixtures_fields = get_fixtures_field_names()
		
		# Collect fields to remove by pattern matching and fixtures
		fields_to_remove = []
		doctypes_affected = set()
		
		# Combine all print_designer specific field lists
		all_print_designer_fields = (
			print_designer_specific_patterns + 
			print_designer_sales_invoice_fields
		)
		
		for field in all_custom_fields:
			should_remove = False
			
			# Check if field is in fixtures (definitive print_designer fields)
			field_key = f"{field.dt}-{field.fieldname}"
			if field_key in fixtures_fields:
				should_remove = True
				print(f"📌 Fixtures field: {field.dt}.{field.fieldname}")
			
			# Check EXACT match for print_designer specific fields (no partial matching to avoid conflicts)
			elif field.fieldname in all_print_designer_fields:
				should_remove = True  
				print(f"🔍 Exact match: {field.dt}.{field.fieldname}")
			
			# Only check label for very specific print_designer terms (avoid generic terms)
			elif field.label and any(term in field.label.lower() for term in ["print designer", "watermark settings", "copy settings"]):
				should_remove = True
				print(f"🏷️ Label matched: {field.dt}.{field.fieldname} ({field.label})")
			
			if should_remove:
				fields_to_remove.append(field)
				doctypes_affected.add(field.dt)
		
		print(f"\n📊 Summary:")
		print(f"   Total custom fields found: {len(all_custom_fields)}")
		print(f"   Print Designer fields to remove: {len(fields_to_remove)}")
		print(f"   DocTypes affected: {len(doctypes_affected)}")
		
		if not fields_to_remove:
			print("✅ No print_designer custom fields found to remove")
			return
		
		# Group by DocType for organized removal
		fields_by_doctype = {}
		for field in fields_to_remove:
			if field.dt not in fields_by_doctype:
				fields_by_doctype[field.dt] = []
			fields_by_doctype[field.dt].append(field)
		
		# Remove fields DocType by DocType
		total_removed = 0
		for doctype, fields in fields_by_doctype.items():
			try:
				field_names = [f.name for f in fields]
				frappe.db.delete("Custom Field", {"name": ("in", field_names)})
				
				print(f"✅ Removed {len(fields)} fields from {doctype}")
				for field in fields:
					print(f"   - {field.fieldname} ({field.label or 'No label'})")
				
				total_removed += len(fields)
				
				# Clear cache for this DocType
				frappe.clear_cache(doctype=doctype)
				
			except Exception as e:
				print(f"❌ Error removing fields from {doctype}: {str(e)}")
		
		# Commit the changes
		frappe.db.commit()
		print(f"\n🎯 Successfully removed {total_removed} print_designer custom fields")
		print("✅ Print Designer custom fields cleanup completed")
		
	except Exception as e:
		frappe.db.rollback()
		print(f"❌ Error during comprehensive cleanup: {str(e)}")
		raise


def get_fixtures_field_names():
	"""Get all field names from hooks.py fixtures configuration"""
	try:
		from print_designer.hooks import fixtures
		
		if not fixtures or "Custom Field" not in fixtures:
			return set()
		
		# Get the filter for Custom Field fixtures
		custom_field_filter = fixtures["Custom Field"]
		
		# Extract field names from the filter
		field_names = set()
		
		if isinstance(custom_field_filter, dict) and "filters" in custom_field_filter:
			# If it's a more complex filter structure, parse it
			filters = custom_field_filter["filters"]
			if isinstance(filters, list):
				for filter_item in filters:
					if isinstance(filter_item, str) and "-" in filter_item:
						# Format: "DocType-fieldname"
						field_names.add(filter_item)
		elif isinstance(custom_field_filter, list):
			# Simple list of "DocType-fieldname" strings
			field_names.update(custom_field_filter)
		
		print(f"📋 Found {len(field_names)} fields in fixtures configuration")
		return field_names
		
	except Exception as e:
		print(f"⚠️ Could not load fixtures: {str(e)}")
		return set()


def remove_pdf_generator_option():
	set_pdf_generator_option("remove")


def remove_print_designer_doctypes():
	"""Remove custom DocTypes created by print_designer"""
	print("🗑️ Removing print_designer custom DocTypes...")
	
	try:
		# Known print_designer DocTypes
		print_designer_doctypes = [
			"Print Designer Signature", "Print Designer Company Stamp", 
			"Print Designer User Signature", "Company Retention Settings"
		]
		
		removed_count = 0
		for doctype_name in print_designer_doctypes:
			if frappe.db.exists("DocType", doctype_name):
				try:
					# Delete all documents of this type first
					frappe.db.delete(doctype_name)
					
					# Then delete the DocType itself
					frappe.delete_doc("DocType", doctype_name, force=1)
					print(f"✅ Removed DocType: {doctype_name}")
					removed_count += 1
				except Exception as e:
					print(f"❌ Error removing DocType {doctype_name}: {str(e)}")
		
		if removed_count > 0:
			frappe.db.commit()
			print(f"🎯 Successfully removed {removed_count} print_designer DocTypes")
		else:
			print("✅ No print_designer DocTypes found to remove")
			
	except Exception as e:
		print(f"❌ Error removing DocTypes: {str(e)}")


def remove_print_designer_print_formats():
	"""Remove print formats created by print_designer"""
	print("🗑️ Removing print_designer Print Formats...")
	
	try:
		# Find print formats that use print_designer
		print_formats = frappe.get_all(
			"Print Format",
			filters={"print_designer": 1},
			fields=["name", "doc_type"]
		)
		
		if not print_formats:
			print("✅ No print_designer Print Formats found to remove")
			return
		
		removed_count = 0
		for pf in print_formats:
			try:
				frappe.delete_doc("Print Format", pf.name, force=1)
				print(f"✅ Removed Print Format: {pf.name} ({pf.doc_type})")
				removed_count += 1
			except Exception as e:
				print(f"❌ Error removing Print Format {pf.name}: {str(e)}")
		
		if removed_count > 0:
			frappe.db.commit()
			print(f"🎯 Successfully removed {removed_count} print_designer Print Formats")
			
	except Exception as e:
		print(f"❌ Error removing Print Formats: {str(e)}")


def before_uninstall():
	"""Comprehensive print_designer app cleanup"""
	print("🚀 Starting print_designer app uninstallation...")
	
	try:
		# 1. Remove all custom fields (comprehensive approach)
		delete_all_print_designer_custom_fields()
		
		# 2. Also remove fields defined in CUSTOM_FIELDS (fallback)
		print("\n🔄 Running fallback cleanup for CUSTOM_FIELDS...")
		delete_custom_fields(CUSTOM_FIELDS)
		
		# 3. Remove custom DocTypes
		print("\n🗑️ Removing custom DocTypes...")
		remove_print_designer_doctypes()
		
		# 4. Remove print formats
		print("\n🖨️ Removing Print Formats...")
		remove_print_designer_print_formats()
		
		# 5. Remove PDF generator option
		print("\n⚙️ Removing PDF generator settings...")
		remove_pdf_generator_option()
		
		# 6. Final cleanup
		print("\n🧹 Final cleanup...")
		frappe.clear_cache()
		
		print("\n✅ Print Designer app uninstallation completed successfully!")
		print("🔄 Please restart your Frappe services to complete the cleanup")
		
	except Exception as e:
		print(f"❌ Error during uninstallation: {str(e)}")
		frappe.db.rollback()
		raise
