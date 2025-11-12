"""
Data Migration Patch: Remove Percentage Symbols from VAT Treatment Values
===========================================================================

This patch updates existing VAT Treatment field values to remove percentage symbols
to fix Python string formatting issues (% being escaped to %% in validation).

Affected DocTypes:
- Purchase Invoice
- Purchase Order
- Quotation
- Sales Invoice
- Sales Order
- Payment Entry

Value Mapping:
- "Standard VAT (7%)" → "Standard VAT"
- "VAT Undue (7%)" → "VAT Undue"
- "Zero-rated for Export (0%)" → "Zero-rated for Export"
- "Exempt from VAT" → "Exempt from VAT" (no change)

Also updates Custom Field options to reflect new values.
"""

import frappe
from frappe import _


def execute():
	"""Execute the VAT Treatment migration patch"""

	frappe.logger().info("Starting VAT Treatment percentage removal migration...")

	try:
		# Step 1: Update Custom Field options
		update_custom_field_options()

		# Step 2: Migrate existing data in all affected doctypes
		migrate_doctype_data()

		frappe.db.commit()
		frappe.logger().info("✅ VAT Treatment migration completed successfully")

	except Exception as e:
		frappe.logger().error(f"❌ VAT Treatment migration failed: {str(e)}")
		frappe.db.rollback()
		raise


def update_custom_field_options():
	"""Update Custom Field options to remove percentages"""

	frappe.logger().info("Updating Custom Field options...")

	# New options without percentages
	new_options = "\nStandard VAT\nVAT Undue\nExempt from VAT\nZero-rated for Export"

	# Update vat_treatment field options for all affected doctypes
	doctypes = [
		"Purchase Invoice",
		"Purchase Order",
		"Quotation",
		"Sales Invoice",
		"Sales Order",
		"Payment Entry"
	]

	for doctype in doctypes:
		try:
			custom_field = frappe.db.get_value(
				"Custom Field",
				{"dt": doctype, "fieldname": "vat_treatment"},
				"name"
			)

			if custom_field:
				frappe.db.set_value("Custom Field", custom_field, "options", new_options)
				frappe.logger().info(f"  ✓ Updated {doctype}.vat_treatment options")
			else:
				frappe.logger().warning(f"  ⚠ {doctype}.vat_treatment field not found")

		except Exception as e:
			frappe.logger().error(f"  ✗ Error updating {doctype}: {str(e)}")

	frappe.logger().info("Custom Field options update complete")


def migrate_doctype_data():
	"""Migrate existing VAT Treatment data in all doctypes"""

	frappe.logger().info("Migrating existing VAT Treatment data...")

	# Mapping of old values to new values
	value_mapping = {
		"Standard VAT (7%)": "Standard VAT",
		"VAT Undue (7%)": "VAT Undue",
		"Zero-rated for Export (0%)": "Zero-rated for Export"
		# "Exempt from VAT" stays the same
	}

	# Doctypes with vat_treatment field
	doctypes = [
		"Purchase Invoice",
		"Purchase Order",
		"Quotation",
		"Sales Invoice",
		"Sales Order",
		"Payment Entry"
	]

	total_updated = 0

	for doctype in doctypes:
		try:
			# Check if doctype exists
			if not frappe.db.exists("DocType", doctype):
				frappe.logger().warning(f"  ⚠ {doctype} does not exist, skipping...")
				continue

			# Check if vat_treatment field exists
			if not frappe.db.has_column(f"tab{doctype}", "vat_treatment"):
				frappe.logger().warning(f"  ⚠ {doctype} does not have vat_treatment field, skipping...")
				continue

			# Migrate each old value to new value
			doctype_updated = 0
			for old_value, new_value in value_mapping.items():
				count = migrate_single_value(doctype, old_value, new_value)
				doctype_updated += count

			total_updated += doctype_updated
			frappe.logger().info(f"  ✓ Migrated {doctype_updated} records in {doctype}")

		except Exception as e:
			frappe.logger().error(f"  ✗ Error migrating {doctype}: {str(e)}")

	frappe.logger().info(f"Data migration complete: {total_updated} records updated across all doctypes")


def migrate_single_value(doctype, old_value, new_value):
	"""
	Migrate a single VAT Treatment value in a doctype

	Args:
		doctype: DocType name
		old_value: Old VAT Treatment value (with percentage)
		new_value: New VAT Treatment value (without percentage)

	Returns:
		int: Number of records updated
	"""
	try:
		# Use direct SQL for efficiency
		table_name = f"tab{doctype}"

		# Update the value
		frappe.db.sql(f"""
			UPDATE `{table_name}`
			SET vat_treatment = %s
			WHERE vat_treatment = %s
		""", (new_value, old_value))

		# Get count of updated rows
		count = frappe.db.sql(f"""
			SELECT COUNT(*) as count
			FROM `{table_name}`
			WHERE vat_treatment = %s
		""", (new_value,))[0][0]

		return count

	except Exception as e:
		frappe.logger().error(f"Error migrating {old_value} → {new_value} in {doctype}: {str(e)}")
		return 0


if __name__ == "__main__":
	# For testing the patch directly
	frappe.init()
	frappe.connect()
	execute()
	frappe.destroy()
