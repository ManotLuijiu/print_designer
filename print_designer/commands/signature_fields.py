#!/usr/bin/env python3
"""
Command-line interface for managing signature fields in Print Designer
"""

import click
import frappe
from frappe.commands import get_site, pass_context

def init_frappe_context(site):
    """Initialize Frappe context for the given site"""
    frappe.init(site)
    frappe.connect()

@click.group()
@click.option('--site', default=None, help='Site name')
@pass_context
def signature_fields(context, site):
    """Manage signature fields for Print Designer"""
    if not site:
        # Try to get default site
        try:
            site = get_site(context)
        except:
            click.echo("Error: Please specify a site using --site option")
            return
    
    context.site = site
    init_frappe_context(site)

@signature_fields.command()
@pass_context
def install(context):
    """Install signature fields to all configured DocTypes"""
    from ..install_signature_fields import install_signature_fields
    
    click.echo("Installing signature fields...")
    result = install_signature_fields()
    
    if result['failed'] == 0:
        click.echo("✅ Signature fields installed successfully!")
    else:
        click.echo(f"⚠️  Installation completed with {result['failed']} failures")

@signature_fields.command()
@pass_context
def verify(context):
    """Verify that signature fields are properly installed"""
    from ..install_signature_fields import verify_signature_fields
    
    click.echo("Verifying signature fields installation...")
    verify_signature_fields()

@signature_fields.command()
@pass_context
def uninstall(context):
    """Remove signature fields from all DocTypes"""
    from ..install_signature_fields import uninstall_signature_fields
    
    if click.confirm("Are you sure you want to remove all signature fields?"):
        click.echo("Removing signature fields...")
        result = uninstall_signature_fields()
        
        if result['failed'] == 0:
            click.echo("✅ Signature fields removed successfully!")
        else:
            click.echo(f"⚠️  Removal completed with {result['failed']} failures")

@signature_fields.command()
@pass_context
def status(context):
    """Check the status of signature fields installation"""
    from ..install_signature_fields import status as check_status
    
    check_status()

@signature_fields.command()
@pass_context
def list_doctypes(context):
    """List all DocTypes that will have signature fields"""
    from ..signature_fields import get_doctypes_with_signatures
    
    doctypes = get_doctypes_with_signatures()
    click.echo("DocTypes with signature fields:")
    click.echo("=" * 40)
    
    for doctype in sorted(doctypes):
        click.echo(f"  • {doctype}")
    
    click.echo(f"\nTotal: {len(doctypes)} DocTypes")

if __name__ == '__main__':
    signature_fields()