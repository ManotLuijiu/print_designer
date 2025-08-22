#!/usr/bin/env python3
"""
Restructure Sales Invoice retention fields to eliminate infinite API loops.

This command removes problematic section-based custom fields and creates optimized 
fields in the Totals section based on the design in:
apps/print_designer/print_designer/public/images/local/retention_custom_field.jpg
"""

import frappe
import click

@click.command("restructure-retention-fields", help="Restructure Sales Invoice retention fields to eliminate API loops")
def restructure_retention_fields():
    """
    Delete problematic section fields and implement retention fields in Totals section
    """
    
    print("🚀 Starting retention fields restructure...")
    
    # Step 1: Delete problematic section-based custom fields
    print("\n📝 Step 1: Removing problematic custom field sections...")
    
    problematic_fields = [
        # Withholding Tax Details section
        'withholding_tax_details_section',
        'withholding_tax_details_column',
        'subjects_to_withholding_tax',
        
        # Retention Details section  
        'retention_section',
        'custom_retention',
        'custom_retention_amount'
    ]
    
    removed_count = 0
    for field_name in problematic_fields:
        if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field_name}):
            frappe.delete_doc("Custom Field", {"dt": "Sales Invoice", "fieldname": field_name})
            print(f"  ✅ Deleted: {field_name}")
            removed_count += 1
        else:
            print(f"  ℹ️  Not found: {field_name}")
    
    frappe.db.commit()
    print(f"  🗑️  Removed {removed_count} problematic fields")
    
    # Step 2: Create new fields in Totals section
    print("\n📝 Step 2: Creating optimized retention fields in Totals section...")
    
    # Fields to be created in order, inserted after 'total_taxes_and_charges'
    fields_config = [
        {
            "fieldname": "custom_retention_percent",
            "label": "Retention %",
            "fieldtype": "Percent",
            "insert_after": "total_taxes_and_charges",
            "depends_on": "eval:doc.company", 
            "description": "Retention percentage to be withheld from payment"
        },
        {
            "fieldname": "custom_retention_amount", 
            "label": "Retention Amount",
            "fieldtype": "Currency",
            "insert_after": "custom_retention_percent",
            "depends_on": "eval:doc.company && doc.custom_retention_percent",
            "read_only": 1,
            "description": "Calculated retention amount based on percentage"
        },
        {
            "fieldname": "custom_withholding_tax_percent",
            "label": "Withholding Tax (%)",
            "fieldtype": "Percent",
            "insert_after": "custom_retention_amount", 
            "depends_on": "eval:doc.company",
            "description": "Withholding tax percentage"
        },
        {
            "fieldname": "custom_withholding_tax_amount",
            "label": "Withholding Tax Amount",
            "fieldtype": "Currency", 
            "insert_after": "custom_withholding_tax_percent",
            "depends_on": "eval:doc.company && doc.custom_withholding_tax_percent",
            "read_only": 1,
            "description": "Calculated withholding tax amount"
        },
        {
            "fieldname": "custom_payment_amount",
            "label": "Payment Amount", 
            "fieldtype": "Currency",
            "insert_after": "custom_withholding_tax_amount",
            "depends_on": "eval:doc.company",
            "read_only": 1,
            "bold": 1,
            "description": "Final payment amount after retention and withholding tax deductions"
        }
    ]
    
    created_count = 0
    for field_config in fields_config:
        # Check if field already exists
        if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field_config["fieldname"]}):
            print(f"  ⚠️  Field {field_config['fieldname']} already exists - skipping")
            continue
            
        # Create the custom field
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            **field_config
        })
        
        custom_field.insert()
        print(f"  ✅ Created: {field_config['fieldname']} - {field_config['label']}")
        created_count += 1
    
    frappe.db.commit()
    
    print(f"\n✨ Created {created_count} new fields in Totals section")
    
    # Step 3: Clear cache to apply changes immediately
    print("\n📝 Step 3: Clearing cache to apply changes...")
    frappe.clear_cache()
    print("  ✅ Cache cleared")
    
    print("\n🎉 Retention fields restructure completed!")
    print("\n📋 New field structure in Totals section:")
    print("  1. Retention % - User input percentage") 
    print("  2. Retention Amount - Auto-calculated from percentage")
    print("  3. Withholding Tax (%) - User input percentage") 
    print("  4. Withholding Tax Amount - Auto-calculated from percentage")
    print("  5. Payment Amount - Final payment after deductions")
    
    print("\n✅ Benefits:")
    print("  - No more problematic section dependencies")
    print("  - Simple eval: expressions instead of API calls")  
    print("  - Fields logically grouped in Totals section")
    print("  - Eliminates infinite API loop issue")
    
    return {
        "removed_fields": removed_count,
        "created_fields": created_count,
        "status": "success"
    }


def check_restructure_status():
    """Check if the restructure has been applied"""
    
    print("🔍 Checking retention fields restructure status...")
    
    # Check for old problematic fields
    problematic_fields = [
        'withholding_tax_details_section',
        'retention_section', 
        'custom_retention'
    ]
    
    old_fields_exist = []
    for field_name in problematic_fields:
        if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field_name}):
            old_fields_exist.append(field_name)
    
    # Check for new Totals fields
    new_fields = [
        'custom_retention_percent',
        'custom_retention_amount',
        'custom_withholding_tax_percent', 
        'custom_withholding_tax_amount',
        'custom_payment_amount'
    ]
    
    new_fields_exist = []
    for field_name in new_fields:
        if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field_name}):
            new_fields_exist.append(field_name)
    
    print(f"\n📊 Status Report:")
    print(f"  Old problematic fields remaining: {len(old_fields_exist)}")
    if old_fields_exist:
        print(f"    - {', '.join(old_fields_exist)}")
    
    print(f"  New Totals fields present: {len(new_fields_exist)}/{len(new_fields)}")
    if new_fields_exist:
        print(f"    - {', '.join(new_fields_exist)}")
    
    if not old_fields_exist and len(new_fields_exist) == len(new_fields):
        print("\n✅ Restructure completed successfully!")
        return {"status": "completed", "message": "All fields properly restructured"}
    elif old_fields_exist:
        print("\n⚠️  Restructure needed - old problematic fields still present")
        return {"status": "needs_restructure", "message": "Old problematic fields detected"}
    else:
        print("\n⚠️  Partial restructure - some new fields missing")
        return {"status": "partial", "message": "Some new fields missing"}


if __name__ == "__main__":
    restructure_retention_fields()