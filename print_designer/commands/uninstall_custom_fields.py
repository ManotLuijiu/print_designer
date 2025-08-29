#!/usr/bin/env python3
"""
Comprehensive Print Designer Custom Fields Uninstall Command
Allows testing and executing the complete custom field removal process
"""

import click
import frappe
from frappe import _

# Import the comprehensive uninstall functions
from print_designer.uninstall import (
    delete_all_print_designer_custom_fields,
    remove_print_designer_doctypes,
    remove_print_designer_print_formats,
    delete_custom_fields
)
from print_designer.custom_fields import CUSTOM_FIELDS


@click.group()
def cli():
    """Print Designer Custom Fields Management Commands"""
    pass


@cli.command('list-fields')
def list_print_designer_fields():
    """List all custom fields that would be removed by print_designer uninstall"""
    click.echo("🔍 Scanning for print_designer custom fields...")
    
    try:
        # Get all custom fields that were likely created by print_designer
        all_custom_fields = frappe.get_all(
            "Custom Field",
            fields=["name", "dt", "fieldname", "label", "owner"],
            order_by="dt, idx"
        )
        
        # Known print_designer SPECIFIC field patterns (exact matches only)
        print_designer_specific_patterns = [
            # Direct print_designer field names (very specific)
            "print_designer",
            # Print Designer specific field types (exact matches)
            "print_designer_print_format", "print_designer_body", "print_designer_header",
            "print_designer_footer", "print_designer_settings", "print_designer_preview",
            "print_designer_after_table", "print_designer_template_app", 
            # Watermark fields (print_designer specific)
            "watermark_settings", "watermark_font_size", "watermark_position", "watermark_font_family",
            # Copy/multiple copy system (print_designer feature)
            "enable_multiple_copies", "default_copy_count", "copy_labels_column", "show_copy_controls_in_toolbar",
            "default_original_label", "default_copy_label", "copy_settings_section", "watermark_settings_section",
            # Signature fields created by print_designer signature system
            "prepared_by_signature", "approved_by_signature",
            # Delivery approval QR system (print_designer feature)
            "custom_delivery_approval_section", "customer_approval_status", "customer_signature",
            "customer_approved_by", "customer_approved_on", "approval_qr_code", "custom_approval_url",
            "custom_goods_received_status", "custom_approval_qr_code", "custom_customer_approval_date",
            "custom_approved_by", "custom_customer_signature", "custom_rejection_reason",
            # Typography system (print_designer feature)
            "typography_section", "primary_font_family", "font_preferences_column", 
            "enable_thai_font_support", "custom_font_stack", "custom_typography_css",
        ]
        
        # Sales Invoice fields SPECIFICALLY created by print_designer install_sales_invoice_fields.py
        print_designer_sales_invoice_fields = [
            # Watermark field
            "watermark_text",
            # Thai WHT Preview Section (print_designer specific)
            "thai_wht_preview_section", "wht_amounts_column_break", "wht_preview_column_break", 
            "vat_treatment", "subject_to_wht", "wht_income_type", "wht_description",
            "net_total_after_wht", "net_total_after_wht_in_words", "wht_certificate_required", "wht_note",
            # Retention fields (print_designer construction feature)
            "custom_subject_to_retention", "custom_net_total_after_wht_retention", 
            "custom_net_total_after_wht_retention_in_words", "custom_retention_note",
            "custom_retention", "custom_retention_amount",
            # Construction service (print_designer feature)
            "construction_service",
            # WHT calculation fields (print_designer calculations)
            "custom_withholding_tax", "custom_withholding_tax_amount", "custom_payment_amount",
            # Signature fields
            "prepared_by_signature", "approved_by_signature",
        ]
        
        # Combine all print_designer specific field lists
        all_print_designer_fields = (
            print_designer_specific_patterns + 
            print_designer_sales_invoice_fields
        )
        
        # Collect fields to remove by pattern matching
        fields_to_remove = []
        doctypes_affected = set()
        
        for field in all_custom_fields:
            should_remove = False
            
            # Check EXACT match for print_designer specific fields (no partial matching)
            if field.fieldname in all_print_designer_fields:
                should_remove = True  
                click.echo(f"🔍 Exact match: {field.dt}.{field.fieldname}")
            
            # Only check label for very specific print_designer terms
            elif field.label and any(term in field.label.lower() for term in ["print designer", "watermark settings", "copy settings"]):
                should_remove = True
                click.echo(f"🏷️ Label matched: {field.dt}.{field.fieldname} ({field.label})")
            
            if should_remove:
                fields_to_remove.append(field)
                doctypes_affected.add(field.dt)
        
        click.echo(f"\n📊 Summary:")
        click.echo(f"   Total custom fields found: {len(all_custom_fields)}")
        click.echo(f"   Print Designer fields to remove: {len(fields_to_remove)}")
        click.echo(f"   DocTypes affected: {len(doctypes_affected)}")
        
        if fields_to_remove:
            click.echo(f"\n📋 Affected DocTypes:")
            for doctype in sorted(doctypes_affected):
                doctype_fields = [f for f in fields_to_remove if f.dt == doctype]
                click.echo(f"   {doctype}: {len(doctype_fields)} fields")
                for field in doctype_fields:
                    click.echo(f"      - {field.fieldname} ({field.label or 'No label'})")
        
    except Exception as e:
        click.echo(f"❌ Error listing fields: {str(e)}")


@cli.command('remove-all')
@click.option('--dry-run', is_flag=True, help='Show what would be removed without actually removing')
@click.option('--force', is_flag=True, help='Force removal without confirmation prompts')
def remove_all_custom_fields(dry_run, force):
    """Remove ALL custom fields created by print_designer"""
    
    if dry_run:
        click.echo("🧪 DRY RUN MODE - No actual changes will be made")
        # Run list command to show what would be removed
        list_print_designer_fields()
        return
    
    if not force:
        click.confirm(
            "⚠️ This will remove ALL custom fields created by print_designer. "
            "This action cannot be undone. Are you sure?",
            abort=True
        )
    
    try:
        # Execute comprehensive removal
        click.echo("🚀 Starting comprehensive print_designer custom fields removal...")
        delete_all_print_designer_custom_fields()
        click.echo("✅ Custom fields removal completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Error during removal: {str(e)}")
        raise


@cli.command('remove-doctypes')
@click.option('--dry-run', is_flag=True, help='Show what would be removed without actually removing')
@click.option('--force', is_flag=True, help='Force removal without confirmation prompts')
def remove_doctypes(dry_run, force):
    """Remove custom DocTypes created by print_designer"""
    
    print_designer_doctypes = [
        "Print Designer Signature", "Print Designer Company Stamp", 
        "Print Designer User Signature", "Company Retention Settings"
    ]
    
    if dry_run:
        click.echo("🧪 DRY RUN MODE - Checking for print_designer DocTypes...")
        existing_count = 0
        for doctype_name in print_designer_doctypes:
            if frappe.db.exists("DocType", doctype_name):
                click.echo(f"✅ Found: {doctype_name}")
                existing_count += 1
            else:
                click.echo(f"❌ Not found: {doctype_name}")
        
        click.echo(f"\n📊 Would remove {existing_count} DocTypes")
        return
    
    if not force:
        click.confirm(
            "⚠️ This will remove custom DocTypes and all their data. "
            "This action cannot be undone. Are you sure?",
            abort=True
        )
    
    try:
        click.echo("🗑️ Starting DocTypes removal...")
        remove_print_designer_doctypes()
        click.echo("✅ DocTypes removal completed!")
        
    except Exception as e:
        click.echo(f"❌ Error during DocTypes removal: {str(e)}")
        raise


@cli.command('remove-print-formats')
@click.option('--dry-run', is_flag=True, help='Show what would be removed without actually removing')
@click.option('--force', is_flag=True, help='Force removal without confirmation prompts')
def remove_print_formats(dry_run, force):
    """Remove print formats created by print_designer"""
    
    try:
        # Find print formats that use print_designer
        print_formats = frappe.get_all(
            "Print Format",
            filters={"print_designer": 1},
            fields=["name", "doc_type"]
        )
        
        if dry_run:
            click.echo("🧪 DRY RUN MODE - Checking for print_designer Print Formats...")
            if not print_formats:
                click.echo("❌ No print_designer Print Formats found")
                return
            
            click.echo(f"📊 Found {len(print_formats)} Print Formats to remove:")
            for pf in print_formats:
                click.echo(f"   - {pf.name} ({pf.doc_type})")
            return
        
        if not print_formats:
            click.echo("✅ No print_designer Print Formats found to remove")
            return
        
        if not force:
            click.confirm(
                f"⚠️ This will remove {len(print_formats)} Print Formats. "
                "This action cannot be undone. Are you sure?",
                abort=True
            )
        
        click.echo("🖨️ Starting Print Formats removal...")
        remove_print_designer_print_formats()
        click.echo("✅ Print Formats removal completed!")
        
    except Exception as e:
        click.echo(f"❌ Error during Print Formats removal: {str(e)}")
        raise


@cli.command('full-uninstall')
@click.option('--dry-run', is_flag=True, help='Show what would be removed without actually removing')
@click.option('--force', is_flag=True, help='Force removal without confirmation prompts')
def full_uninstall(dry_run, force):
    """Complete print_designer uninstall (fields, DocTypes, Print Formats)"""
    
    if dry_run:
        click.echo("🧪 DRY RUN MODE - Showing complete uninstall preview...")
        click.echo("\n=== CUSTOM FIELDS ===")
        list_print_designer_fields()
        click.echo("\n=== DOCTYPES ===")
        remove_doctypes(dry_run=True, force=True)
        click.echo("\n=== PRINT FORMATS ===")
        remove_print_formats(dry_run=True, force=True)
        return
    
    if not force:
        click.confirm(
            "⚠️ This will perform a COMPLETE print_designer uninstall removing:\n"
            "- All custom fields\n"
            "- All custom DocTypes and their data\n"
            "- All Print Formats\n"
            "This action cannot be undone. Are you sure?",
            abort=True
        )
    
    try:
        click.echo("🚀 Starting COMPLETE print_designer uninstall...")
        
        # Execute all removal operations
        remove_all_custom_fields(dry_run=False, force=True)
        remove_doctypes(dry_run=False, force=True)  
        remove_print_formats(dry_run=False, force=True)
        
        click.echo("\n✅ COMPLETE print_designer uninstall completed successfully!")
        click.echo("🔄 Please restart your Frappe services to complete the cleanup")
        
    except Exception as e:
        click.echo(f"❌ Error during complete uninstall: {str(e)}")
        raise


if __name__ == "__main__":
    cli()