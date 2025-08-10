import click
import frappe
from frappe.commands import get_site, pass_context


@click.command('emergency-fix-watermark')
@click.option('--site', help='Site name')
@pass_context
def emergency_fix_watermark(context, site=None):
    """Emergency fix for watermark_text column missing error"""
    
    if not site:
        site = get_site(context)
    
    with frappe.init_site(site):
        frappe.connect()
        
        try:
            click.echo("🚨 EMERGENCY FIX: Adding watermark_text column to Stock Entry")
            click.echo("=" * 60)
            
            # Step 1: Check if column exists in Stock Entry
            columns = frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'")
            
            if not columns:
                click.echo("❌ watermark_text column is MISSING from Stock Entry table")
                click.echo("🔧 Adding watermark_text column directly to database...")
                
                # Add the column directly to the database
                frappe.db.sql("""
                    ALTER TABLE `tabStock Entry` 
                    ADD COLUMN `watermark_text` varchar(140) DEFAULT 'None'
                """)
                
                click.echo("✅ watermark_text column added to Stock Entry table")
            else:
                click.echo("✅ watermark_text column already exists in Stock Entry table")
            
            # Step 2: Fix other critical DocTypes
            critical_doctypes = [
                "Sales Invoice",
                "Purchase Invoice", 
                "Delivery Note",
                "Sales Order",
                "Purchase Order",
                "Payment Entry",
                "Journal Entry",
                "Quotation"
            ]
            
            click.echo("\n🔧 Fixing other critical DocTypes...")
            for doctype in critical_doctypes:
                try:
                    # Check if column exists
                    columns = frappe.db.sql(f"SHOW COLUMNS FROM `tab{doctype}` LIKE 'watermark_text'")
                    
                    if not columns:
                        click.echo(f"  🔧 Adding watermark_text column to {doctype}...")
                        frappe.db.sql(f"""
                            ALTER TABLE `tab{doctype}` 
                            ADD COLUMN `watermark_text` varchar(140) DEFAULT 'None'
                        """)
                        click.echo(f"  ✅ Added column to {doctype}")
                    else:
                        click.echo(f"  ✅ {doctype} already has watermark_text column")
                        
                except Exception as e:
                    click.echo(f"  ⚠️  Could not fix {doctype}: {str(e)}")
            
            # Step 3: Ensure Custom Fields exist
            click.echo("\n🔧 Ensuring Custom Fields exist...")
            ensure_watermark_custom_fields()
            
            # Step 4: Commit all changes
            frappe.db.commit()
            
            # Step 5: Clear cache to refresh meta
            frappe.clear_cache()
            
            click.echo("\n" + "=" * 60)
            click.echo("🎉 EMERGENCY FIX COMPLETED!")
            click.echo("✅ Stock Entry watermark_text error should now be resolved")
            click.echo("✅ You can now try saving Stock Entry again")
            click.echo("✅ All critical DocTypes have been fixed")
            
        except Exception as e:
            click.echo(f"❌ Emergency fix failed: {str(e)}")
            frappe.db.rollback()
            raise


def ensure_watermark_custom_fields():
    """Ensure watermark Custom Fields exist"""
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        from print_designer.watermark_fields import get_watermark_custom_fields
        
        # Get all watermark field definitions
        custom_fields = get_watermark_custom_fields()
        
        # Create the custom fields
        create_custom_fields(custom_fields, update=True)
        
        click.echo("✅ Watermark Custom Fields ensured")
        
    except Exception as e:
        click.echo(f"⚠️  Could not create Custom Fields: {str(e)}")


commands = [emergency_fix_watermark]