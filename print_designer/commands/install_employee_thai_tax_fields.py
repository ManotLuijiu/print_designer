#!/usr/bin/env python3

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def install_employee_thai_tax_fields():
    """Install Thai Tax ID field in Employee DocType with Buddhist Era awareness"""

    print("🔍 Checking Employee DocType for Thai tax field compatibility...")

    # 1. Check if our custom field already exists
    existing_custom_field = frappe.db.get_value(
        "Custom Field", {"dt": "Employee", "fieldname": "pd_custom_thai_tax_id"}
    )

    if existing_custom_field:
        print("✅ Employee Thai Tax ID field already exists (Print Designer)")
        print(f"   Field ID: {existing_custom_field}")
        return

    # 2. Check for potential conflicts with HRMS or other apps
    potential_conflicts = [
        "thai_tax_id",           # Common naming
        "tax_id",                # Generic naming
        "thai_tax_number",       # Descriptive naming
        "personal_tax_id",       # HRMS potential
        "income_tax_id",         # HRMS potential
        "pan_number"             # ERPNext India (we already handle this)
    ]

    conflicts_found = []
    for field_name in potential_conflicts:
        # Check both custom fields and standard fields
        custom_conflict = frappe.db.get_value("Custom Field", {
            "dt": "Employee",
            "fieldname": field_name
        })

        # Check if it exists as standard field in meta
        try:
            employee_meta = frappe.get_meta("Employee")
            standard_conflict = employee_meta.get_field(field_name)
        except:
            standard_conflict = None

        if custom_conflict or standard_conflict:
            field_type = "standard" if standard_conflict else "custom"
            conflicts_found.append({
                "fieldname": field_name,
                "type": field_type,
                "source": custom_conflict if custom_conflict else "Employee DocType"
            })

    # 3. Report conflicts but continue (our field has unique prefix)
    if conflicts_found:
        print("⚠️ Found potential Thai tax field conflicts:")
        for conflict in conflicts_found:
            print(f"   - {conflict['fieldname']} ({conflict['type']} field from {conflict['source']})")
        print("✅ No conflicts expected - our field uses unique prefix: pd_custom_thai_tax_id")
    else:
        print("✅ No Thai tax field conflicts detected")

    # 4. Check for existing Employee records with potential Thai tax data
    employee_count = frappe.db.count("Employee")
    print(f"📊 Found {employee_count} existing Employee records")

    if employee_count > 0:
        print("ℹ️ Existing Employee records will have empty Thai Tax ID initially")
        print("   Users can manually populate or import Thai Tax ID data")

    # 5. Proceed with field creation
    print("🚀 Creating Print Designer Thai Tax ID field...")

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
    """Check if Employee Thai Tax ID field exists with Buddhist Era compatibility"""

    print("🔍 Checking Employee Thai Tax ID field status...")

    # 1. Check our custom field
    existing_field = frappe.db.get_value(
        "Custom Field", {"dt": "Employee", "fieldname": "pd_custom_thai_tax_id"}
    )

    if existing_field:
        print("✅ Employee Thai Tax ID field exists (Print Designer)")
        print(f"   Field ID: {existing_field}")

        # 2. Check Employee Tax Ledger integration
        try:
            etl_meta = frappe.get_meta("Employee Tax Ledger")
            employee_tax_id_field = etl_meta.get_field("employee_tax_id")

            if employee_tax_id_field and employee_tax_id_field.fetch_from == "employee.pd_custom_thai_tax_id":
                print("✅ Employee Tax Ledger integration working")
            else:
                print("⚠️ Employee Tax Ledger may need fetch_from update")
                print("   Expected: employee.pd_custom_thai_tax_id")
                current_fetch = getattr(employee_tax_id_field, 'fetch_from', 'Not set')
                print(f"   Current: {current_fetch}")

        except Exception as e:
            print(f"⚠️ Could not verify Employee Tax Ledger integration: {str(e)}")

        # 3. Check for Buddhist Era support in Employee Tax Ledger Entry
        try:
            etle_meta = frappe.get_meta("Employee Tax Ledger Entry")
            year_buddhist_field = etle_meta.get_field("year_buddhist")

            if year_buddhist_field:
                print("✅ Buddhist Era support available in Employee Tax Ledger Entry")
            else:
                print("⚠️ Buddhist Era field missing in Employee Tax Ledger Entry")
                print("   Run: bench migrate to add year_buddhist field")

        except Exception as e:
            print(f"⚠️ Could not verify Buddhist Era support: {str(e)}")

        return True

    else:
        print("❌ Employee Thai Tax ID field not found")
        print("   Run: bench install-employee-thai-tax-fields")

        # Check if there are alternative Thai tax fields
        alternative_fields = ["thai_tax_id", "tax_id", "thai_tax_number"]
        for alt_field in alternative_fields:
            alt_exists = frappe.db.get_value("Custom Field", {
                "dt": "Employee",
                "fieldname": alt_field
            })
            if alt_exists:
                print(f"ℹ️ Found alternative field: {alt_field}")
                print("   Consider using Print Designer's standardized field instead")

        return False


if __name__ == "__main__":
    install_employee_thai_tax_fields()
