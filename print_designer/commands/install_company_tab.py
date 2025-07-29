# File: print_designer/commands/install_company_tab.py

import click
import frappe
from frappe.commands import pass_context

@click.command('install-company-tab')
@pass_context
def install_company_tab(context):
    """Install Company Stamps & Signatures tab"""
    
    site = context.obj['sites'][0] if context.obj.get('sites') else None
    if not site:
        click.echo("Please specify a site")
        return
        
    frappe.init(site=site)
    frappe.connect()
    
    try:
        from print_designer.custom.company_tab import create_company_stamps_signatures_tab
        
        click.echo("🚀 Installing Company Stamps & Signatures tab...")
        create_company_stamps_signatures_tab()
        click.echo("✅ Company tab installation completed!")
        
    except Exception as e:
        click.echo(f"❌ Error during installation: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()

@click.command('remove-company-tab')
@pass_context 
def remove_company_tab(context):
    """Remove Company Stamps & Signatures tab"""
    
    site = context.obj['sites'][0] if context.obj.get('sites') else None
    if not site:
        click.echo("Please specify a site")
        return
        
    frappe.init(site=site)
    frappe.connect()
    
    try:
        from print_designer.custom.company_tab import remove_company_stamps_signatures_tab
        
        click.echo("🗑️ Removing Company Stamps & Signatures tab...")
        remove_company_stamps_signatures_tab()
        click.echo("✅ Company tab removal completed!")
        
    except Exception as e:
        click.echo(f"❌ Error during removal: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()

commands = [install_company_tab, remove_company_tab]