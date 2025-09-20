#!/usr/bin/env python3
"""
Cleanup pd_custom_has_thai_taxes Field

Removes the obsolete pd_custom_has_thai_taxes field from Payment Entry DocType.
This field is no longer used after refactoring field visibility to use depends_on conditions.
"""

import frappe
import click


def execute():
    """Main entry point for bench command"""
    cleanup_has_thai_taxes_field()


@click.command()
def cleanup_has_thai_taxes_field():
    """Remove pd_custom_has_thai_taxes field from Payment Entry"""

    click.echo("🧹 Cleaning up obsolete pd_custom_has_thai_taxes field...")

    try:
        # Step 1: Check if Custom Field record exists
        custom_field_exists = frappe.db.exists("Custom Field", {
            "dt": "Payment Entry",
            "fieldname": "pd_custom_has_thai_taxes"
        })

        if custom_field_exists:
            click.echo("📋 Found Custom Field record - removing...")
            frappe.delete_doc("Custom Field", custom_field_exists)
            click.echo("✅ Custom Field record deleted")
        else:
            click.echo("📋 Custom Field record not found (already deleted)")

        # Step 2: Check if database column exists
        column_exists = frappe.db.has_column("tabPayment Entry", "pd_custom_has_thai_taxes")

        if column_exists:
            click.echo("🗄️ Found database column - removing...")

            # Verify no records are using this field (safety check)
            count = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabPayment Entry`
                WHERE pd_custom_has_thai_taxes = 1
            """, as_dict=True)[0].count

            if count > 0:
                click.echo(f"⚠️ WARNING: {count} Payment Entry records have this field set to 1")
                click.echo("❌ Aborting cleanup - field is still in use")
                return

            # Safe to drop the column
            frappe.db.sql("ALTER TABLE `tabPayment Entry` DROP COLUMN pd_custom_has_thai_taxes")
            click.echo("✅ Database column dropped")
        else:
            click.echo("🗄️ Database column not found (already dropped)")

        # Step 3: Clear cache to ensure changes take effect
        frappe.clear_cache()
        click.echo("🔄 Cache cleared")

        click.echo("✅ Cleanup completed successfully!")
        click.echo("📝 Summary:")
        click.echo("   - Custom Field record: removed")
        click.echo("   - Database column: removed")
        click.echo("   - Field visibility now controlled by depends_on conditions")

    except Exception as e:
        click.echo(f"❌ Error during cleanup: {str(e)}")
        frappe.log_error(
            message=f"Error cleaning up pd_custom_has_thai_taxes field: {str(e)}",
            title="Field Cleanup Error"
        )


@click.command()
def check_has_thai_taxes_field_status():
    """Check the current status of pd_custom_has_thai_taxes field"""

    click.echo("🔍 Checking pd_custom_has_thai_taxes field status...")

    try:
        # Check Custom Field record
        custom_field_exists = frappe.db.exists("Custom Field", {
            "dt": "Payment Entry",
            "fieldname": "pd_custom_has_thai_taxes"
        })

        if custom_field_exists:
            click.echo("📋 Custom Field record: ✅ EXISTS")
            field_doc = frappe.get_doc("Custom Field", custom_field_exists)
            click.echo(f"   - Name: {field_doc.name}")
            click.echo(f"   - Label: {field_doc.label}")
            click.echo(f"   - Hidden: {field_doc.hidden}")
        else:
            click.echo("📋 Custom Field record: ❌ NOT FOUND")

        # Check database column
        column_exists = frappe.db.has_column("tabPayment Entry", "pd_custom_has_thai_taxes")
        if column_exists:
            click.echo("🗄️ Database column: ✅ EXISTS")

            # Check usage
            count = frappe.db.sql("""
                SELECT COUNT(*) as count
                FROM `tabPayment Entry`
                WHERE pd_custom_has_thai_taxes = 1
            """, as_dict=True)[0].count

            click.echo(f"📊 Records using field: {count}")
        else:
            click.echo("🗄️ Database column: ❌ NOT FOUND")

        # Check DocType meta
        meta = frappe.get_meta("Payment Entry")
        field_in_meta = None
        for field in meta.fields:
            if field.fieldname == "pd_custom_has_thai_taxes":
                field_in_meta = field
                break

        if field_in_meta:
            click.echo("📄 DocType meta: ✅ FIELD FOUND")
        else:
            click.echo("📄 DocType meta: ❌ FIELD NOT FOUND")

    except Exception as e:
        click.echo(f"❌ Error checking status: {str(e)}")


if __name__ == "__main__":
    execute()