#!/usr/bin/env python3
"""
Force Install Construction Service Field - Production Fix Command

This command can be run directly in production to install the missing construction_service field.

Usage:
bench execute print_designer.commands.force_install_construction_service.force_install_construction_service

This fixes the critical issue where the construction_service field was not showing up in production
due to a missing emergency_fallback function in hooks.py.
"""

import frappe
import click
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


@click.command()
def force_install_construction_service():
    """Force install the construction service field and related fields."""
    click.echo("🚨 PRODUCTION FIX: Installing Construction Service Field...")
    
    try:
        # Check current status
        company_meta = frappe.get_meta("Company")
        construction_service_field = company_meta.get_field("construction_service")
        
        if construction_service_field:
            click.echo("✅ construction_service field already exists!")
            click.echo(f"   Field Type: {construction_service_field.fieldtype}")
            click.echo(f"   Label: {construction_service_field.label}")
            click.echo(f"   Insert After: {construction_service_field.insert_after}")
            
            # Check if it's visible in companies
            companies = frappe.get_all("Company", limit=3, fields=["name"])
            if companies:
                test_company = companies[0].name
                click.echo(f"\n🏢 Testing field access on company: {test_company}")
                
                try:
                    company_doc = frappe.get_doc("Company", test_company)
                    construction_enabled = getattr(company_doc, 'construction_service', None)
                    
                    if construction_enabled is None:
                        click.echo("❌ Field exists in meta but not accessible - may need cache clearing")
                        click.echo("   Running cache clear...")
                        frappe.clear_cache()
                        frappe.clear_cache(doctype="Company")
                        
                        # Test again after cache clear
                        company_doc.reload()
                        construction_enabled = getattr(company_doc, 'construction_service', None)
                        
                        if construction_enabled is not None:
                            click.echo("✅ Field is now accessible after cache clear")
                        else:
                            click.echo("❌ Field still not accessible - may need bench restart")
                    else:
                        status = "Enabled" if construction_enabled else "Disabled"  
                        click.echo(f"✅ Field is accessible and functional: {status}")
                        
                except Exception as e:
                    click.echo(f"❌ Error testing field access: {str(e)}")
            
            return
            
        click.echo("❌ construction_service field missing - installing now...")
        
        # Define the construction service field
        custom_fields = {
            "Company": [
                {
                    "fieldname": "construction_service",
                    "label": "Enable Construction Service",
                    "fieldtype": "Check",
                    "insert_after": "country",
                    "description": "Enable construction service features including retention calculations",
                    "default": 0,
                },
                {
                    "fieldname": "default_retention_rate",
                    "fieldtype": "Percent", 
                    "label": "Default Retention Rate (%)",
                    "insert_after": "construction_service",
                    "depends_on": "eval:doc.construction_service",
                    "description": "Default retention rate for construction projects (e.g., 5% for most projects)",
                    "default": 5.0,
                    "precision": 2,
                },
                {
                    "fieldname": "default_retention_account",
                    "fieldtype": "Link",
                    "label": "Default Retention Account", 
                    "options": "Account",
                    "insert_after": "default_retention_rate",
                    "depends_on": "eval:doc.construction_service",
                    "description": "Default account for retention liability (e.g., Construction Retention Payable)",
                }
            ]
        }
        
        # Install the fields
        create_custom_fields(custom_fields, update=True)
        
        click.echo("✅ Custom fields installed successfully!")
        click.echo("   - Company: construction_service (checkbox)")
        click.echo("   - Company: default_retention_rate (percentage)")  
        click.echo("   - Company: default_retention_account (link to Account)")
        
        # Clear caches to make fields immediately visible
        frappe.clear_cache()
        frappe.clear_cache(doctype="Company")
        
        # Commit changes
        frappe.db.commit()
        
        click.echo("\n🎯 INSTALLATION COMPLETED!")
        click.echo("✅ The 'Enable Construction Service' field should now be visible in Company form")
        click.echo("✅ Navigate to Company settings to enable the construction service feature")
        
        # Test the installation
        click.echo("\n🧪 Testing installation...")
        company_meta_new = frappe.get_meta("Company")
        test_field = company_meta_new.get_field("construction_service")
        
        if test_field:
            click.echo("✅ Field successfully installed and accessible!")
        else:
            click.echo("❌ Field installation may have failed - check error logs")
            
    except Exception as e:
        click.echo(f"❌ Installation failed: {str(e)}")
        frappe.log_error(
            message=f"Failed to install construction service field: {str(e)}",
            title="Construction Service Field Installation Failed"
        )
        frappe.db.rollback()
        raise


def force_install_construction_service_direct():
    """Direct function call version for bench execute."""
    return force_install_construction_service.callback()


if __name__ == "__main__":
    force_install_construction_service()