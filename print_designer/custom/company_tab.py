# File: print_designer/custom/company_tab.py

import frappe


def create_company_stamps_signatures_tab():
    """Create the Stamps & Signatures tab for Company DocType"""

    try:
        # Check if the custom field already exists
        existing_field = frappe.db.exists(
            "Custom Field", {"dt": "Company", "fieldname": "stamps_signatures_tab"}
        )
        print("🔍 Existing field:", existing_field)
        if existing_field:
            print("✅ Company 'Stamps & Signatures' tab already exists")
            return True

        # Verify Company DocType exists
        if not frappe.db.exists("DocType", "Company"):
            print("⚠️  Company DocType not found, skipping tab creation")
            return False

        # Create the tab break custom field
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Company"
        custom_field.label = "Stamps & Signatures"
        custom_field.fieldname = "stamps_signatures_tab"
        custom_field.fieldtype = "Tab Break"
        custom_field.insert_after = "stock_tab"  # Insert after Stock tab
        custom_field.idx = 100  # Set a high index to ensure it appears last

        custom_field.insert()
        frappe.db.commit()
        print("✅ Created 'Stamps & Signatures' tab for Company DocType")
        return True

    except Exception as e:
        print(f"❌ Error creating Company tab: {e}")
        frappe.db.rollback()
        return False


def remove_company_stamps_signatures_tab():
    """Remove the Stamps & Signatures tab from Company DocType"""

    try:
        custom_field_name = frappe.db.get_value(
            "Custom Field",
            {"dt": "Company", "fieldname": "stamps_signatures_tab"},
            "name",
        )

        if custom_field_name:
            frappe.delete_doc("Custom Field", custom_field_name)
            frappe.db.commit()
            print("✅ Removed 'Stamps & Signatures' tab from Company DocType")
            return True
        else:
            print("⚠️  Company 'Stamps & Signatures' tab not found")
            return True

    except Exception as e:
        print(f"❌ Error removing Company tab: {e}")
        frappe.db.rollback()
        return False
