"""
Migration patch to fix Delivery Note approval URLs from old format to new format.

Old format: /app/delivery-approval/{dn}?token={token}
New format: /delivery-approval?dn={dn}&token={token}
"""

import frappe
import re


def execute():
	"""Update all Delivery Note approval URLs to new web page format."""

	# Check if the custom field exists in the Delivery Note table
	if not frappe.db.has_column("Delivery Note", "custom_approval_url"):
		print("ℹ️  custom_approval_url column not found in Delivery Note table")
		print("ℹ️  Skipping approval URL migration (field needs to be created first)")
		return

	# Get all Delivery Notes with approval URLs
	delivery_notes = frappe.get_all(
		"Delivery Note",
		filters={
			"custom_approval_url": ["!=", ""]
		},
		fields=["name", "custom_approval_url"]
	)

	updated_count = 0

	for dn in delivery_notes:
		old_url = dn.custom_approval_url

		if not old_url:
			continue

		# Check if URL is in old format: /app/delivery-approval/{id}?token=...
		old_pattern = r'/app/delivery-approval/([^?]+)\?token=(.+)'
		match = re.match(old_pattern, old_url)

		if match:
			dn_name = match.group(1)
			token = match.group(2)

			# Extract base URL
			base_url = old_url.split('/app/delivery-approval/')[0]

			# Create new URL format
			new_url = f"{base_url}/delivery-approval?dn={dn_name}&token={token}"

			# Update in database
			frappe.db.set_value(
				"Delivery Note",
				dn.name,
				"custom_approval_url",
				new_url,
				update_modified=False
			)

			updated_count += 1
			print(f"✓ Updated {dn.name}: {new_url}")

	frappe.db.commit()

	print(f"\n✅ Migration complete: Updated {updated_count} Delivery Note approval URLs")
