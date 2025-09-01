#!/usr/bin/env python3
"""
Fix Payment Entry Reference field visibility
Makes Thai tax fields visible in the Payment Entry references table
"""

import frappe
import click

@click.command()
def fix_payment_entry_reference_display():
    """Update Payment Entry Reference custom fields to show in list view."""
    click.echo("🔧 Fixing Payment Entry Reference field visibility...")
    
    try:
        # Fields that should be visible in the table
        fields_to_show = [
            "pd_custom_has_retention",
            "pd_custom_retention_amount", 
            "pd_custom_retention_percentage",
            "pd_custom_wht_amount",
            "pd_custom_wht_percentage",
            "pd_custom_vat_undue_amount",
            "pd_custom_net_payable_amount"
        ]
        
        updated_count = 0
        
        for fieldname in fields_to_show:
            # Get the custom field
            custom_field = frappe.get_all("Custom Field",
                filters={
                    "dt": "Payment Entry Reference",
                    "fieldname": fieldname
                },
                fields=["name"]
            )
            
            if custom_field:
                field_doc = frappe.get_doc("Custom Field", custom_field[0]["name"])
                
                # Set in_list_view to 1 and adjust column width
                field_doc.in_list_view = 1
                
                # Set appropriate column widths
                if fieldname in ["pd_custom_has_retention"]:
                    field_doc.columns = 1  # Checkbox - narrow
                elif fieldname in ["pd_custom_retention_percentage", "pd_custom_wht_percentage"]:
                    field_doc.columns = 1  # Percentage - narrow
                else:
                    field_doc.columns = 2  # Amount fields - wider
                
                field_doc.save()
                updated_count += 1
                click.echo(f"   ✅ {fieldname}: Set to show in list view (columns: {field_doc.columns})")
            else:
                click.echo(f"   ⚠️ {fieldname}: Custom field not found")
        
        if updated_count > 0:
            # Clear cache to ensure changes are reflected
            frappe.clear_cache(doctype="Payment Entry Reference")
            frappe.db.commit()
            
            click.echo(f"\n✅ Updated {updated_count} fields successfully!")
            click.echo("\n📌 Note: You may need to:")
            click.echo("   1. Refresh the Payment Entry form")
            click.echo("   2. Clear browser cache (Ctrl+Shift+R)")
            click.echo("   3. Reload the page if fields don't appear immediately")
        else:
            click.echo("\n⚠️ No fields were updated")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        frappe.log_error(
            message=f"Failed to fix Payment Entry Reference display: {str(e)}",
            title="Payment Entry Reference Display Fix Failed"
        )
        frappe.db.rollback()
        raise

def fix_payment_entry_reference_display_direct():
    """Direct function call version for bench execute."""
    return fix_payment_entry_reference_display.callback()

if __name__ == "__main__":
    fix_payment_entry_reference_display()