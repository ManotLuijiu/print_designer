#!/usr/bin/env python3

"""
Install Retention Client Script Command
Installs the retention client script to eliminate API flooding
"""

import click
import frappe
from frappe.commands import pass_context, get_site


@click.command('install-retention-client-script')
@click.option('--site', help='Site name')
@pass_context
def install_retention_client_script(context, site=None):
    """Install retention client script to eliminate API flooding from Sales Invoice forms"""
    
    if not site:
        site = get_site(context)
    
    with frappe.init_site(site):
        frappe.connect()
        
        try:
            from print_designer.custom.sales_invoice_retention import install_retention_client_script
            
            print("📦 Installing retention client script...")
            install_retention_client_script()
            print("✅ Retention client script installation completed!")
            
        except Exception as e:
            print(f"❌ Error installing retention client script: {str(e)}")
            frappe.log_error(frappe.get_traceback(), "Retention Client Script Installation Error")
            raise
        finally:
            frappe.destroy()


@click.command('check-retention-client-script')
@click.option('--site', help='Site name')
@pass_context  
def check_retention_client_script(context, site=None):
    """Check if retention client script is installed and active"""
    
    if not site:
        site = get_site(context)
        
    with frappe.init_site(site):
        frappe.connect()
        
        try:
            # Check if client script exists
            client_script = frappe.db.get_value('Client Script', 
                {'name': 'Sales Invoice Retention Fields'},
                ['enabled', 'dt', 'view', 'script'], as_dict=True)
                
            if client_script:
                print("✅ Retention client script found:")
                print(f"   - Enabled: {client_script.enabled}")
                print(f"   - DocType: {client_script.dt}")  
                print(f"   - View: {client_script.view}")
                print(f"   - Script Length: {len(client_script.script)} characters")
                
                if client_script.enabled:
                    print("✅ Retention client script is active and working")
                else:
                    print("⚠️ Retention client script exists but is disabled")
            else:
                print("❌ Retention client script not found")
                print("Run: bench execute print_designer.commands.install_retention_client_script.install_retention_client_script")
                
        except Exception as e:
            print(f"❌ Error checking retention client script: {str(e)}")
            raise
        finally:
            frappe.destroy()


commands = [install_retention_client_script, check_retention_client_script]