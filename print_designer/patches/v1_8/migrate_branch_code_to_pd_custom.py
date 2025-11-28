"""
One-time Data Migration Patch: Legacy branch_code fields to pd_custom_branch_code

This patch runs ONCE via Frappe's patch system and migrates:
1. Customer legacy branch_code fields → pd_custom_branch_code
2. Supplier legacy branch_code fields → pd_custom_branch_code

Legacy fields that are migrated:
- branch_code
- custom_branch_code
- dgs_custom_branch_code (from digisoft_erp app)
- customer_branch_code / supplier_branch_code
"""

import frappe


def execute():
    """Execute the one-time migration patch"""
    print("\n" + "=" * 80)
    print("ONE-TIME MIGRATION: Legacy branch_code → pd_custom_branch_code")
    print("=" * 80 + "\n")

    customer_stats = migrate_doctype_branch_codes("Customer")
    supplier_stats = migrate_doctype_branch_codes("Supplier")

    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE!")
    print(f"  Customers: {customer_stats['migrated']} migrated, {customer_stats['skipped']} skipped")
    print(f"  Suppliers: {supplier_stats['migrated']} migrated, {supplier_stats['skipped']} skipped")
    print("=" * 80 + "\n")


def migrate_doctype_branch_codes(doctype):
    """
    Migrate legacy branch_code fields for a specific DocType.

    Args:
        doctype: "Customer" or "Supplier"

    Returns:
        dict: Migration statistics
    """
    table_name = f"tab{doctype}"
    stats = {"migrated": 0, "skipped": 0, "errors": 0}

    print(f"📋 Migrating {doctype} branch codes...")

    # Check if pd_custom_branch_code field exists
    try:
        frappe.db.sql(f"SELECT pd_custom_branch_code FROM `{table_name}` LIMIT 1")
    except Exception:
        print(f"   ⚠️  Target field pd_custom_branch_code doesn't exist in {doctype} - skipping")
        return stats

    # Get all existing custom fields with 'branch' in name (excluding target field)
    existing_fields = frappe.db.sql("""
        SELECT fieldname, label
        FROM `tabCustom Field`
        WHERE dt = %s
        AND fieldname LIKE '%%branch%%'
        AND fieldname != 'pd_custom_branch_code'
    """, (doctype,), as_dict=True)

    if not existing_fields:
        print(f"   ℹ️  No legacy branch fields found for {doctype}")
        return stats

    print(f"   Found {len(existing_fields)} legacy branch field(s):")
    for field in existing_fields:
        print(f"      - {field.fieldname} ({field.label})")

    # Process each legacy field
    for legacy_field in existing_fields:
        fieldname = legacy_field["fieldname"]

        try:
            # Check if this legacy field column exists in database
            frappe.db.sql(f"SELECT `{fieldname}` FROM `{table_name}` LIMIT 1")
        except Exception:
            print(f"   ℹ️  Field {fieldname} has no database column - skipping")
            continue

        # Find records with values in legacy field but NOT yet migrated
        # Only migrate if pd_custom_branch_code is NULL or empty
        # Include '00000' values - user may have explicitly set head office code
        records_to_migrate = frappe.db.sql(f"""
            SELECT name, `{fieldname}` as legacy_value
            FROM `{table_name}`
            WHERE `{fieldname}` IS NOT NULL
            AND `{fieldname}` != ''
            AND (pd_custom_branch_code IS NULL OR pd_custom_branch_code = '')
        """, as_dict=True)

        if not records_to_migrate:
            stats["skipped"] += 1
            continue

        print(f"\n   🔄 Migrating {len(records_to_migrate)} records from {fieldname}...")

        for record in records_to_migrate:
            try:
                frappe.db.set_value(
                    doctype,
                    record.name,
                    "pd_custom_branch_code",
                    record.legacy_value,
                    update_modified=False
                )
                print(f"      ✓ {record.name}: '{record.legacy_value}' → pd_custom_branch_code")
                stats["migrated"] += 1
            except Exception as e:
                print(f"      ✗ {record.name}: Migration failed - {str(e)}")
                stats["errors"] += 1

        frappe.db.commit()

    print(f"\n   📊 {doctype} Summary: {stats['migrated']} migrated, {stats['skipped']} skipped, {stats['errors']} errors")
    return stats
