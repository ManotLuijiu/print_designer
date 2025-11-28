"""
Custom Field Management Commands for Customer DocType
Handles installation, verification, and removal of Print Designer-specific Customer custom fields.

Features:
- Branch Code for Thai tax invoice compliance (00000 default for head office)
- Smart data migration from legacy branch_code fields
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Field configuration for Customer DocType
CUSTOMER_CUSTOM_FIELDS = {
    "Customer": [
        {
            "fieldname": "pd_custom_branch_code",
            "label": "Branch Code",
            "fieldtype": "Data",
            "insert_after": "tax_id",
            "default": "00000",
            "module": "Print Designer",
            "description": "Branch code for Thai tax invoice compliance (00000 = head office)",
        },
    ]
}

# Legacy field names that might exist on production servers
LEGACY_BRANCH_FIELDS = [
    "branch_code",
    "custom_branch_code",
    "dgs_custom_branch_code",  # From digisoft_erp app
    "customer_branch_code",
]


def migrate_legacy_branch_data():
    """
    Smart data migration from legacy branch_code fields to pd_custom_branch_code.

    This function:
    1. Identifies existing legacy branch fields
    2. Migrates data from those fields to pd_custom_branch_code
    3. Preserves existing values
    4. Logs all migrations for audit trail

    Returns:
        dict: Migration statistics
    """
    try:
        print("\n🔍 Checking for legacy branch_code fields to migrate...")

        # Get all existing custom fields for Customer with 'branch' in name
        existing_fields = frappe.db.sql("""
            SELECT fieldname, label
            FROM `tabCustom Field`
            WHERE dt = 'Customer'
            AND fieldname LIKE '%branch%'
            AND fieldname != 'pd_custom_branch_code'
        """, as_dict=True)

        if not existing_fields:
            print("   ℹ️  No legacy branch fields found - fresh installation")
            return {"migrated": 0, "skipped": 0, "errors": 0}

        print(f"   📋 Found {len(existing_fields)} legacy branch field(s):")
        for field in existing_fields:
            print(f"      - {field.fieldname} ({field.label})")

        # Check if pd_custom_branch_code field exists in database
        try:
            frappe.db.sql("SELECT pd_custom_branch_code FROM `tabCustomer` LIMIT 1")
        except Exception:
            print("   ⚠️  Target field pd_custom_branch_code doesn't exist yet - will migrate after field creation")
            return {"migrated": 0, "skipped": 0, "errors": 0, "deferred": True}

        # Get all customers that need migration
        migration_stats = {"migrated": 0, "skipped": 0, "errors": 0}

        for legacy_field in existing_fields:
            fieldname = legacy_field["fieldname"]

            try:
                # Check if this legacy field column exists in database
                frappe.db.sql(f"SELECT {fieldname} FROM `tabCustomer` LIMIT 1")

                # Find customers with values in legacy field but empty pd_custom_branch_code
                customers_to_migrate = frappe.db.sql(f"""
                    SELECT name, {fieldname} as legacy_value
                    FROM `tabCustomer`
                    WHERE {fieldname} IS NOT NULL
                    AND {fieldname} != ''
                    AND (pd_custom_branch_code IS NULL OR pd_custom_branch_code = '' OR pd_custom_branch_code = '00000')
                """, as_dict=True)

                if customers_to_migrate:
                    print(f"\n   🔄 Migrating from {fieldname}...")

                    for customer in customers_to_migrate:
                        try:
                            # Update pd_custom_branch_code with legacy value
                            frappe.db.set_value(
                                "Customer",
                                customer.name,
                                "pd_custom_branch_code",
                                customer.legacy_value,
                                update_modified=False  # Don't update modified timestamp
                            )

                            print(f"      ✓ {customer.name}: '{customer.legacy_value}' → pd_custom_branch_code")
                            migration_stats["migrated"] += 1

                        except Exception as e:
                            print(f"      ✗ {customer.name}: Migration failed - {str(e)}")
                            migration_stats["errors"] += 1

                    # Commit after each field migration
                    frappe.db.commit()

            except Exception:
                # Legacy field column doesn't exist in database - skip
                print(f"   ℹ️  Field {fieldname} defined in Custom Field but no database column - skipping")
                continue

        # Summary
        print("\n📊 Migration Summary:")
        print(f"   ✅ Successfully migrated: {migration_stats['migrated']} customers")
        print(f"   ⏭️  Skipped: {migration_stats['skipped']} customers")
        print(f"   ❌ Errors: {migration_stats['errors']} customers")

        if migration_stats['migrated'] > 0:
            print("\n💡 Tip: Legacy fields are preserved. You can safely delete them after verifying data.")

        return migration_stats

    except Exception as e:
        print(f"❌ Error during legacy data migration: {str(e)}")
        frappe.log_error("Customer Legacy Branch Data Migration Error", str(e))
        return {"migrated": 0, "skipped": 0, "errors": 1}


def create_customer_fields():
    """
    Install Customer custom fields for Print Designer.

    Note: Legacy data migration is now handled by a one-time Frappe patch:
    print_designer.patches.v1_8.migrate_branch_code_to_pd_custom

    Returns:
        bool: True if installation successful, False otherwise
    """
    try:
        print("🚀 Installing Print Designer Customer custom fields...")

        # Create the field definition
        create_custom_fields(CUSTOMER_CUSTOM_FIELDS, update=True)
        frappe.db.commit()

        print("✅ Customer custom fields installed successfully!")
        print("   - pd_custom_branch_code (Branch Code for Thai tax invoices)")

        # Verify field exists
        field_exists = frappe.db.exists("Custom Field", {
            "dt": "Customer",
            "fieldname": "pd_custom_branch_code"
        })

        if field_exists:
            print("✅ Installation completed successfully!")

        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error installing Customer custom fields: {str(e)}")
        frappe.log_error("Customer Custom Fields Installation Error", str(e))
        return False


def check_customer_fields():
    """
    Verify that all Customer custom fields are properly installed.
    Also checks for legacy fields and potential data migration needs.

    Returns:
        bool: True if all fields exist, False otherwise
    """
    try:
        print("🔍 Checking Customer custom fields...")

        # Check if pd_custom_branch_code exists
        missing_fields = []
        for field_config in CUSTOMER_CUSTOM_FIELDS["Customer"]:
            fieldname = field_config["fieldname"]
            if not frappe.db.exists("Custom Field", {"dt": "Customer", "fieldname": fieldname}):
                missing_fields.append(fieldname)

        if missing_fields:
            print(f"❌ Missing {len(missing_fields)} field(s) in Customer:")
            for field in missing_fields:
                print(f"   - {field}")
            return False

        print(f"✅ All {len(CUSTOMER_CUSTOM_FIELDS['Customer'])} Customer custom fields are installed!")

        # Check for legacy fields that might need migration
        legacy_fields = frappe.db.sql("""
            SELECT fieldname, label
            FROM `tabCustom Field`
            WHERE dt = 'Customer'
            AND fieldname LIKE '%branch%'
            AND fieldname != 'pd_custom_branch_code'
        """, as_dict=True)

        if legacy_fields:
            print(f"\n⚠️  Found {len(legacy_fields)} legacy branch field(s):")
            for field in legacy_fields:
                print(f"   - {field.fieldname} ({field.label})")

            # Check if any have data
            for legacy_field in legacy_fields:
                try:
                    count = frappe.db.sql(f"""
                        SELECT COUNT(*) as count
                        FROM `tabCustomer`
                        WHERE {legacy_field['fieldname']} IS NOT NULL
                        AND {legacy_field['fieldname']} != ''
                    """, as_dict=True)[0].count

                    if count > 0:
                        print(f"      💡 {legacy_field['fieldname']} has data in {count} customers")
                        print("         Run: bench execute 'print_designer.commands.install_customer_fields.migrate_legacy_branch_data()'")
                except Exception:
                    pass

        return True

    except Exception as e:
        print(f"❌ Error checking Customer custom fields: {str(e)}")
        frappe.log_error("Customer Custom Fields Check Error", str(e))
        return False


def uninstall_customer_fields():
    """
    Remove all Customer custom fields created by Print Designer.

    Note: This does NOT remove legacy fields (branch_code, custom_branch_code, etc.)
    Those should be manually removed after verifying data migration.

    Returns:
        bool: True if removal successful, False otherwise
    """
    try:
        print("🗑️  Removing Customer custom fields...")
        removed_count = 0

        for field_config in CUSTOMER_CUSTOM_FIELDS["Customer"]:
            fieldname = field_config["fieldname"]
            custom_field = frappe.db.exists(
                "Custom Field", {"dt": "Customer", "fieldname": fieldname}
            )

            if custom_field:
                frappe.delete_doc("Custom Field", custom_field, force=1)
                removed_count += 1
                print(f"   ✓ Removed {fieldname}")

        frappe.db.commit()
        print(f"✅ Successfully removed {removed_count} Customer custom field(s)!")

        # Check for legacy fields
        legacy_fields = frappe.db.sql("""
            SELECT fieldname
            FROM `tabCustom Field`
            WHERE dt = 'Customer'
            AND fieldname LIKE '%branch%'
        """, as_dict=True)

        if legacy_fields:
            print(f"\n⚠️  {len(legacy_fields)} legacy branch field(s) remain:")
            for field in legacy_fields:
                print(f"   - {field.fieldname}")
            print("\n💡 These are legacy fields from other apps/installations.")
            print("   You may want to manually remove them after verifying data migration.")

        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error removing Customer custom fields: {str(e)}")
        frappe.log_error("Customer Custom Fields Uninstall Error", str(e))
        return False


# Click CLI Commands for bench integration


@click.command("install-pd-customer-fields")
@click.pass_context
def install_customer_fields_cmd(context):
    """Install Customer custom fields for Print Designer with smart data migration"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        create_customer_fields()
        frappe.destroy()


@click.command("check-pd-customer-fields")
@click.pass_context
def check_customer_fields_cmd(context):
    """Verify Print Designer Customer custom fields installation and check for migration needs"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        check_customer_fields()
        frappe.destroy()


@click.command("uninstall-pd-customer-fields")
@click.pass_context
def uninstall_customer_fields_cmd(context):
    """Remove Print Designer Customer custom fields (legacy fields preserved)"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        uninstall_customer_fields()
        frappe.destroy()


# Commands are registered in hooks.py as string paths
