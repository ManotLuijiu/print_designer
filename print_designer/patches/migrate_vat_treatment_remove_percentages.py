"""
Data Migration Patch: VAT Treatment values without percentage symbols
===========================================================================

This patch updates existing VAT Treatment field values to remove percentage
symbols to fix Python string formatting issues (% being escaped to %% in
validation) and to apply the rename of the canonical value.

Affected DocTypes:
- Purchase Invoice
- Purchase Order
- Quotation
- Sales Invoice
- Sales Order
- Payment Entry

Value Mapping:
- "Standard VAT (7%)" → "VAT Due" (the taxable supply, renamed)
- "VAT Undue (7%)" → "VAT Undue"
- "Zero-rated for Export (0%)" → "Zero-rated for Export"
- "Exempt from VAT" → "Exempt from VAT" (no change)

The plain legacy value "Standard VAT" is NOT rewritten: it stays readable in
the historical documents (it is one of the options of the field) and the code
treats it like "VAT Due". Rewriting the history is not part of the rename.

Also updates Custom Field options to reflect the new values.
"""

import frappe
from frappe import _

#: The current name of the field and the name it had before it was renamed.
VAT_TREATMENT_FIELDS = ("pd_custom_vat_treatment", "vat_treatment")

#: The options of the field after the rename.
#: The legacy value "Standard VAT" stays an option, so that the historical
#: documents that carry it remain readable. It is never written any more.
NEW_OPTIONS = (
	"\nVAT Due\nVAT Undue\nExempt from VAT\nZero-rated for Export\nStandard VAT"
)

#: The doctypes that carry the VAT Treatment field.
AFFECTED_DOCTYPES = [
	"Purchase Invoice",
	"Purchase Order",
	"Quotation",
	"Sales Invoice",
	"Sales Order",
	"Payment Entry",
]


def get_vat_treatment_field(doctype):
	"""Return the name of the VAT Treatment column of a doctype.

	The field was renamed (``vat_treatment`` -> ``pd_custom_vat_treatment``),
	so both names are checked.
	"""
	for fieldname in VAT_TREATMENT_FIELDS:
		if frappe.db.has_column(f"tab{doctype}", fieldname):
			return fieldname

	return None


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

	for doctype in AFFECTED_DOCTYPES:
		try:
			custom_field = None
			for fieldname in VAT_TREATMENT_FIELDS:
				custom_field = frappe.db.get_value(
					"Custom Field",
					{"dt": doctype, "fieldname": fieldname},
					"name",
				)
				if custom_field:
					break

			if custom_field:
				frappe.db.set_value("Custom Field", custom_field, "options", NEW_OPTIONS)
				frappe.logger().info(f"  ✓ Updated {doctype} VAT Treatment options")
			else:
				frappe.logger().warning(f"  ⚠ {doctype} VAT Treatment field not found")

		except Exception as e:
			frappe.logger().error(f"  ✗ Error updating {doctype}: {str(e)}")

	frappe.logger().info("Custom Field options update complete")


def migrate_doctype_data():
	"""Migrate existing VAT Treatment data in all doctypes"""

	frappe.logger().info("Migrating existing VAT Treatment data...")

	# Mapping of old values to new values
	# Note: Handle both single % and double %% (escaped) formats
	value_mapping = {
		# The percentage variants of the legacy "Standard VAT" value. The
		# plain "Standard VAT" is kept - the history is not rewritten.
		("Standard VAT (7%)", "Standard VAT (7%%)"): "VAT Due",
		# VAT Undue variations
		("VAT Undue (7%)", "VAT Undue (7%%)"): "VAT Undue",
		# Zero-rated variations
		("Zero-rated for Export (0%)", "Zero-rated for Export (0%%)"): "Zero-rated for Export"
		# "Exempt from VAT" stays the same
	}

	total_updated = 0

	for doctype in AFFECTED_DOCTYPES:
		try:
			# Check if doctype exists
			if not frappe.db.exists("DocType", doctype):
				frappe.logger().warning(f"  ⚠ {doctype} does not exist, skipping...")
				continue

			fieldname = get_vat_treatment_field(doctype)
			if not fieldname:
				frappe.logger().warning(f"  ⚠ {doctype} has no VAT Treatment field, skipping...")
				continue

			# Migrate each old value to new value
			doctype_updated = 0
			for old_value, new_value in value_mapping.items():
				count = migrate_single_value(doctype, fieldname, old_value, new_value)
				doctype_updated += count

			total_updated += doctype_updated
			frappe.logger().info(f"  ✓ Migrated {doctype_updated} records in {doctype}")

		except Exception as e:
			frappe.logger().error(f"  ✗ Error migrating {doctype}: {str(e)}")

	frappe.logger().info(f"Data migration complete: {total_updated} records updated across all doctypes")


def migrate_single_value(doctype, fieldname, old_values, new_value):
	"""
	Migrate VAT Treatment values in a doctype (handles multiple old value formats)

	Args:
		doctype: DocType name
		fieldname: the column of the VAT Treatment field
		old_values: Tuple of old VAT Treatment values (handles both % and %% formats)
		new_value: New VAT Treatment value (without percentage)

	Returns:
		int: Number of records updated
	"""
	try:
		# Use direct SQL for efficiency
		table_name = f"tab{doctype}"

		# Build IN clause for multiple old value formats
		placeholders = ', '.join(['%s'] * len(old_values))

		# Update all variations to the new value
		frappe.db.sql(
			f"""
			UPDATE `{table_name}`
			SET `{fieldname}` = %s
			WHERE `{fieldname}` IN ({placeholders})
		""",
			(new_value, *old_values),
		)

		frappe.db.commit()

		# Get count of updated rows
		count = frappe.db.sql(
			f"""
			SELECT COUNT(*) as count
			FROM `{table_name}`
			WHERE `{fieldname}` = %s
		""",
			(new_value,),
		)[0][0]

		return count

	except Exception as e:
		frappe.logger().error(
			f"Error migrating {old_values} → {new_value} in {doctype}: {str(e)}"
		)
		return 0


if __name__ == "__main__":
	# For testing the patch directly
	frappe.init()
	frappe.connect()
	execute()
	frappe.destroy()
