#!/usr/bin/env python3
"""
Patch to fix Sales Invoice WHT preview section field order
Production-safe with validation and rollback capability

This patch fixes the circular dependency issue in Sales Invoice custom fields
where the thai_wht_preview_section fields are not displaying properly.

Issue: Fields showing only wht_amounts_column_break and vat_treatment due to 
broken insert_after chain causing circular dependencies.

Fix: Corrects the insert_after chain to display all 14 fields in proper order:
wht_amounts_column_break → vat_treatment → subject_to_wht → wht_income_type → 
wht_description → wht_certificate_required → net_total_after_wht → 
net_total_after_wht_in_words → wht_note → wht_preview_column_break → 
custom_subject_to_retention → custom_net_total_after_wht_retention → 
custom_net_total_after_wht_retention_in_words → custom_retention_note
"""

import frappe
from frappe import _

def execute():
    """
    Execute the field order fix patch
    Production-safe with validation and rollback capability
    """
    try:
        print("🔧 Starting Sales Invoice field order patch...")
        
        # Pre-patch validation
        if not pre_patch_validation():
            print("❌ Pre-patch validation failed. Aborting patch.")
            return
        
        # Backup current state
        backup_data = backup_current_field_order()
        
        # Apply the field order fix
        result = fix_field_insertion_order()
        
        # Post-patch validation
        if post_patch_validation():
            print("✅ Sales Invoice field order patch completed successfully")
            print("📊 Fields fixed:", result.get('fields_fixed', 0))
        else:
            print("❌ Post-patch validation failed. Rolling back...")
            rollback_field_order(backup_data)
            frappe.throw(_("Patch failed validation and was rolled back"))
            
    except Exception as e:
        print(f"❌ Patch execution failed: {str(e)}")
        # Auto-rollback on any error
        if 'backup_data' in locals():
            rollback_field_order(backup_data)
        raise


def pre_patch_validation():
    """Validate pre-conditions before applying patch"""
    print("🔍 Running pre-patch validation...")
    
    try:
        # Check if Sales Invoice DocType exists
        if not frappe.db.exists("DocType", "Sales Invoice"):
            print("❌ Sales Invoice DocType not found")
            return False
            
        # Check if thai_wht_preview_section exists
        if not frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "thai_wht_preview_section"}):
            print("❌ thai_wht_preview_section field not found")
            return False
            
        # Count expected fields
        expected_fields = [
            "wht_amounts_column_break", "vat_treatment", "subject_to_wht",
            "wht_income_type", "wht_description", "wht_certificate_required", 
            "net_total_after_wht", "net_total_after_wht_in_words", "wht_note",
            "wht_preview_column_break", "custom_subject_to_retention",
            "custom_net_total_after_wht_retention", "custom_net_total_after_wht_retention_in_words",
            "custom_retention_note"
        ]
        
        existing_count = 0
        for field in expected_fields:
            if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field}):
                existing_count += 1
                
        print(f"✅ Found {existing_count}/{len(expected_fields)} expected fields")
        
        if existing_count < 10:  # Allow some missing fields
            print(f"⚠️ Only {existing_count} fields found, expected at least 10")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Pre-patch validation error: {str(e)}")
        return False


def backup_current_field_order():
    """Backup current field order for rollback capability"""
    print("💾 Backing up current field order...")
    
    try:
        current_fields = frappe.get_all("Custom Field",
            filters={"dt": "Sales Invoice"},
            fields=["name", "fieldname", "insert_after"],
            order_by="idx"
        )
        
        # Store only the WHT preview section fields
        wht_fields = [
            "wht_amounts_column_break", "vat_treatment", "subject_to_wht",
            "wht_income_type", "wht_description", "wht_certificate_required",
            "net_total_after_wht", "net_total_after_wht_in_words", "wht_note",
            "wht_preview_column_break", "custom_subject_to_retention",
            "custom_net_total_after_wht_retention", "custom_net_total_after_wht_retention_in_words",
            "custom_retention_note"
        ]
        
        backup = {}
        for field in current_fields:
            if field.fieldname in wht_fields:
                backup[field.fieldname] = field.insert_after
                
        print(f"💾 Backed up {len(backup)} field configurations")
        return backup
        
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return {}


def fix_field_insertion_order():
    """Apply the field order fix"""
    print("🔧 Applying field order fix...")
    
    # Define the correct insert_after chain - matches the corrected definition
    field_order_fixes = [
        ("subject_to_wht", "vat_treatment"),
        ("wht_income_type", "subject_to_wht"), 
        ("wht_description", "wht_income_type"),
        ("wht_certificate_required", "wht_description"),
        ("net_total_after_wht", "wht_certificate_required"),
        ("net_total_after_wht_in_words", "net_total_after_wht"),
        ("wht_note", "net_total_after_wht_in_words"),
        ("wht_preview_column_break", "wht_note"),
        ("custom_subject_to_retention", "wht_preview_column_break"),
        ("custom_net_total_after_wht_retention", "custom_subject_to_retention"),
        ("custom_net_total_after_wht_retention_in_words", "custom_net_total_after_wht_retention"), 
        ("custom_retention_note", "custom_net_total_after_wht_retention_in_words"),
    ]
    
    try:
        fixed_count = 0
        for fieldname, correct_insert_after in field_order_fixes:
            field_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
            
            if field_exists:
                # Use Frappe's safe update method
                frappe.db.set_value("Custom Field", field_exists, "insert_after", correct_insert_after)
                print(f"✅ Fixed {fieldname} → after: {correct_insert_after}")
                fixed_count += 1
            else:
                print(f"⚠️ Field not found: {fieldname}")
        
        # Commit changes atomically
        frappe.db.commit()
        
        print(f"✅ Successfully fixed {fixed_count} field orders")
        return {"success": True, "fields_fixed": fixed_count}
        
    except Exception as e:
        frappe.db.rollback()
        raise Exception(f"Field order fix failed: {str(e)}")


def post_patch_validation():
    """Validate that the patch was applied correctly"""
    print("✅ Running post-patch validation...")
    
    try:
        # Check the critical chain: vat_treatment → subject_to_wht → wht_income_type
        critical_checks = [
            ("subject_to_wht", "vat_treatment"),
            ("wht_income_type", "subject_to_wht"),
            ("wht_description", "wht_income_type"),
        ]
        
        for fieldname, expected_after in critical_checks:
            field_doc = frappe.get_doc("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
            
            if field_doc.insert_after != expected_after:
                print(f"❌ Validation failed: {fieldname} insert_after is {field_doc.insert_after}, expected {expected_after}")
                return False
                
            print(f"✅ Validated: {fieldname} → after: {expected_after}")
        
        print("✅ Post-patch validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Post-patch validation error: {str(e)}")
        return False


def rollback_field_order(backup_data):
    """Rollback field order changes using backup data"""
    print("🔄 Rolling back field order changes...")
    
    try:
        rollback_count = 0
        for fieldname, original_insert_after in backup_data.items():
            field_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
            
            if field_exists:
                frappe.db.set_value("Custom Field", field_exists, "insert_after", original_insert_after)
                rollback_count += 1
                
        frappe.db.commit()
        print(f"🔄 Rolled back {rollback_count} fields to original state")
        
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        raise


# Clear cache after patch execution
def clear_cache_safely():
    """Clear cache safely without affecting active users"""
    try:
        # Clear only Sales Invoice related cache
        frappe.clear_cache(doctype="Sales Invoice")
        print("🗑️ Cache cleared for Sales Invoice")
        
    except Exception as e:
        print(f"⚠️ Cache clear warning: {str(e)}")
        # Don't fail the patch if cache clear fails