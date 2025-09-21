#!/usr/bin/env python3

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_employee_thai_tax_fields():
    """Install Thai Tax ID field in Employee DocType"""

    # Check if field already exists
    existing_field = frappe.db.get_value(
        "Custom Field", {"dt": "Employee", "fieldname": "pd_custom_thai_tax_id"}
    )

    if existing_field:
        print("✅ Employee Thai Tax ID field already exists")
        return

    # Define custom field for Employee
    custom_fields = {
        "Employee": [
            {
                "fieldname": "pd_custom_thai_tax_id",
                "label": "Thai Tax ID",
                "fieldtype": "Data",
                "insert_after": "marital_status",
                "description": "Thai Personal Income Tax ID Number (13 digits)",
                "length": 13,
                "unique": 0,
                "translatable": 0,
            },
        ]
    }

    # Create the custom field
    create_custom_fields(custom_fields, update=True)

    print("✅ Created Thai Tax ID field in Employee DocType")
    print("   Field name: pd_custom_thai_tax_id")
    print("   Location: After health_details section")


def remove_employee_thai_tax_fields():
    """Remove all Thai tax-related custom fields from Employee doctype during uninstallation."""
    print("Removing Employee Thai Tax Fields...")

    # List of all Employee Thai tax fields to remove
    fields_to_remove = [
        "pd_custom_thai_tax_id",
    ]

    try:
        removed_count = 0
        for field_name in fields_to_remove:
            try:
                # Check if custom field exists
                custom_field_name = f"Employee-{field_name}"
                if frappe.db.exists("Custom Field", custom_field_name):
                    frappe.delete_doc("Custom Field", custom_field_name)
                    print(f"✅ Removed Employee.{field_name}")
                    removed_count += 1
                else:
                    print(f"⏭️ Employee.{field_name} not found (already removed)")
            except Exception as e:
                print(f"❌ Error removing Employee.{field_name}: {str(e)}")

        frappe.db.commit()
        print(f"✅ Successfully removed {removed_count} Employee Thai tax fields")

    except Exception as e:
        print(f"❌ Error removing Employee Thai tax fields: {str(e)}")
        frappe.db.rollback()


def check_employee_thai_tax_fields():
    """Check if Employee Thai Tax ID field exists"""

    existing_field = frappe.db.get_value(
        "Custom Field", {"dt": "Employee", "fieldname": "pd_custom_thai_tax_id"}
    )

    if existing_field:
        print("✅ Employee Thai Tax ID field exists")
        print(f"   Field ID: {existing_field}")
        return True
    else:
        print("❌ Employee Thai Tax ID field not found")
        print("   Run: bench install-employee-thai-tax-fields")
        return False


if __name__ == "__main__":
    install_employee_thai_tax_fields()
