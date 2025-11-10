"""
Custom Field Management Commands for Supplier DocType
Handles installation, verification, and removal of Print Designer-specific Supplier custom fields.

Features:
- Branch Code for Thai tax invoice compliance (00000 default for head office)
- Smart data migration from legacy branch_code fields
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Field configuration for Supplier DocType
SUPPLIER_CUSTOM_FIELDS = {
    "Supplier": [
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
    "supplier_branch_code",
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

        # Get all existing custom fields for Supplier with 'branch' in name
        existing_fields = frappe.db.sql("""
            SELECT fieldname, label
            FROM `tabCustom Field`
            WHERE dt = 'Supplier'
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
            frappe.db.sql("SELECT pd_custom_branch_code FROM `tabSupplier` LIMIT 1")
            target_field_exists = True
        except Exception:
            target_field_exists = False
            print("   ⚠️  Target field pd_custom_branch_code doesn't exist yet - will migrate after field creation")
            return {"migrated": 0, "skipped": 0, "errors": 0, "deferred": True}

        # Get all suppliers that need migration
        migration_stats = {"migrated": 0, "skipped": 0, "errors": 0}

        for legacy_field in existing_fields:
            fieldname = legacy_field["fieldname"]

            try:
                # Check if this legacy field column exists in database
                frappe.db.sql(f"SELECT {fieldname} FROM `tabSupplier` LIMIT 1")

                # Find suppliers with values in legacy field but empty pd_custom_branch_code
                suppliers_to_migrate = frappe.db.sql(f"""
                    SELECT name, {fieldname} as legacy_value
                    FROM `tabSupplier`
                    WHERE {fieldname} IS NOT NULL
                    AND {fieldname} != ''
                    AND (pd_custom_branch_code IS NULL OR pd_custom_branch_code = '' OR pd_custom_branch_code = '00000')
                """, as_dict=True)

                if suppliers_to_migrate:
                    print(f"\n   🔄 Migrating from {fieldname}...")

                    for supplier in suppliers_to_migrate:
                        try:
                            # Update pd_custom_branch_code with legacy value
                            frappe.db.set_value(
                                "Supplier",
                                supplier.name,
                                "pd_custom_branch_code",
                                supplier.legacy_value,
                                update_modified=False  # Don't update modified timestamp
                            )

                            print(f"      ✓ {supplier.name}: '{supplier.legacy_value}' → pd_custom_branch_code")
                            migration_stats["migrated"] += 1

                        except Exception as e:
                            print(f"      ✗ {supplier.name}: Migration failed - {str(e)}")
                            migration_stats["errors"] += 1

                    # Commit after each field migration
                    frappe.db.commit()

            except Exception as e:
                # Legacy field column doesn't exist in database - skip
                print(f"   ℹ️  Field {fieldname} defined in Custom Field but no database column - skipping")
                continue

        # Summary
        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Successfully migrated: {migration_stats['migrated']} suppliers")
        print(f"   ⏭️  Skipped: {migration_stats['skipped']} suppliers")
        print(f"   ❌ Errors: {migration_stats['errors']} suppliers")

        if migration_stats['migrated'] > 0:
            print("\n💡 Tip: Legacy fields are preserved. You can safely delete them after verifying data.")

        return migration_stats

    except Exception as e:
        print(f"❌ Error during legacy data migration: {str(e)}")
        frappe.log_error("Supplier Legacy Branch Data Migration Error", str(e))
        return {"migrated": 0, "skipped": 0, "errors": 1}


def create_supplier_fields():
    """
    Install Supplier custom fields for Print Designer with smart data migration.

    Returns:
        bool: True if installation successful, False otherwise
    """
    try:
        print("🚀 Installing Print Designer Supplier custom fields...")

        # Step 1: Create the field definition
        create_custom_fields(SUPPLIER_CUSTOM_FIELDS, update=True)
        frappe.db.commit()

        print("✅ Supplier custom fields installed successfully!")
        print("   - pd_custom_branch_code (Branch Code for Thai tax invoices)")

        # Step 2: Migrate legacy data
        print("\n🔄 Running smart data migration...")
        migration_stats = migrate_legacy_branch_data()

        # Step 3: Verify field exists
        field_exists = frappe.db.exists("Custom Field", {
            "dt": "Supplier",
            "fieldname": "pd_custom_branch_code"
        })

        if field_exists:
            print("\n✅ Installation completed successfully!")
            if migration_stats.get("migrated", 0) > 0:
                print(f"   📦 Migrated {migration_stats['migrated']} existing branch codes")

        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error installing Supplier custom fields: {str(e)}")
        frappe.log_error("Supplier Custom Fields Installation Error", str(e))
        return False


def check_supplier_fields():
    """
    Verify that all Supplier custom fields are properly installed.
    Also checks for legacy fields and potential data migration needs.

    Returns:
        bool: True if all fields exist, False otherwise
    """
    try:
        print("🔍 Checking Supplier custom fields...")

        # Check if pd_custom_branch_code exists
        missing_fields = []
        for field_config in SUPPLIER_CUSTOM_FIELDS["Supplier"]:
            fieldname = field_config["fieldname"]
            if not frappe.db.exists("Custom Field", {"dt": "Supplier", "fieldname": fieldname}):
                missing_fields.append(fieldname)

        if missing_fields:
            print(f"❌ Missing {len(missing_fields)} field(s) in Supplier:")
            for field in missing_fields:
                print(f"   - {field}")
            return False

        print(f"✅ All {len(SUPPLIER_CUSTOM_FIELDS['Supplier'])} Supplier custom fields are installed!")

        # Check for legacy fields that might need migration
        legacy_fields = frappe.db.sql("""
            SELECT fieldname, label
            FROM `tabCustom Field`
            WHERE dt = 'Supplier'
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
                        FROM `tabSupplier`
                        WHERE {legacy_field['fieldname']} IS NOT NULL
                        AND {legacy_field['fieldname']} != ''
                    """, as_dict=True)[0].count

                    if count > 0:
                        print(f"      💡 {legacy_field['fieldname']} has data in {count} suppliers")
                        print(f"         Run: bench execute 'print_designer.commands.install_supplier_fields.migrate_legacy_branch_data()'")
                except Exception:
                    pass

        return True

    except Exception as e:
        print(f"❌ Error checking Supplier custom fields: {str(e)}")
        frappe.log_error("Supplier Custom Fields Check Error", str(e))
        return False


def uninstall_supplier_fields():
    """
    Remove all Supplier custom fields created by Print Designer.

    Note: This does NOT remove legacy fields (branch_code, custom_branch_code, etc.)
    Those should be manually removed after verifying data migration.

    Returns:
        bool: True if removal successful, False otherwise
    """
    try:
        print("🗑️  Removing Supplier custom fields...")
        removed_count = 0

        for field_config in SUPPLIER_CUSTOM_FIELDS["Supplier"]:
            fieldname = field_config["fieldname"]
            custom_field = frappe.db.exists(
                "Custom Field", {"dt": "Supplier", "fieldname": fieldname}
            )

            if custom_field:
                frappe.delete_doc("Custom Field", custom_field, force=1)
                removed_count += 1
                print(f"   ✓ Removed {fieldname}")

        frappe.db.commit()
        print(f"✅ Successfully removed {removed_count} Supplier custom field(s)!")

        # Check for legacy fields
        legacy_fields = frappe.db.sql("""
            SELECT fieldname
            FROM `tabCustom Field`
            WHERE dt = 'Supplier'
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
        print(f"❌ Error removing Supplier custom fields: {str(e)}")
        frappe.log_error("Supplier Custom Fields Uninstall Error", str(e))
        return False


# Click CLI Commands for bench integration


@click.command("install-pd-supplier-fields")
@click.pass_context
def install_supplier_fields_cmd(context):
    """Install Supplier custom fields for Print Designer with smart data migration"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        create_supplier_fields()
        frappe.destroy()


@click.command("check-pd-supplier-fields")
@click.pass_context
def check_supplier_fields_cmd(context):
    """Verify Print Designer Supplier custom fields installation and check for migration needs"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        check_supplier_fields()
        frappe.destroy()


@click.command("uninstall-pd-supplier-fields")
@click.pass_context
def uninstall_supplier_fields_cmd(context):
    """Remove Print Designer Supplier custom fields (legacy fields preserved)"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        uninstall_supplier_fields()
        frappe.destroy()


# Commands are registered in hooks.py as string paths
