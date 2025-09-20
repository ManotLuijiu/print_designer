import frappe

def execute():
	"""Fix all PND Form tax_period_month field types from Select to Int"""

	pnd_forms = ["PND1 Form", "PND53 Form", "PND54 Form"]

	for doctype in pnd_forms:
		try:
			# Update the database column type for each PND form
			table_name = f"tab{doctype}"
			frappe.db.sql(f"""
				ALTER TABLE `{table_name}`
				MODIFY COLUMN tax_period_month INT(11)
			""")

			# Update existing records to convert string values to integers
			frappe.db.sql(f"""
				UPDATE `{table_name}`
				SET tax_period_month = CAST(tax_period_month AS UNSIGNED)
				WHERE tax_period_month IS NOT NULL
			""")

			# Reload the DocType to apply JSON changes
			module = "print_designer"
			doctype_name = doctype.replace(" ", "_").lower()
			frappe.reload_doc(module, "doctype", doctype_name)

			print(f"✅ {doctype} field type migration completed")

		except Exception as e:
			print(f"❌ Error migrating {doctype}: {e}")
			# Continue with other forms even if one fails
			continue

	frappe.db.commit()
	print("✅ All PND Form field type migrations completed")