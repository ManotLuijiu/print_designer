#!/usr/bin/env python3
"""
Fix Sales Invoice field index ordering issues in production
Addresses the problem where fields have conflicting index numbers

This patch fixes the issue where custom_net_total_after_wht_retention_in_words 
(lower index) was trying to insert after custom_net_total_after_wht_retention 
(higher index), creating logical inconsistencies in field ordering.
"""

import frappe
from frappe import _

def execute():
    """
    Fix field index ordering by reassigning proper sequential indices
    Production-safe with validation and rollback capability
    """
    try:
        print("🔧 Starting Sales Invoice field index ordering fix...")
        
        # Pre-patch validation
        if not pre_patch_validation():
            print("❌ Pre-patch validation failed. Aborting patch.")
            return
        
        # Backup current state
        backup_data = backup_current_field_indices()
        
        # Apply the field index fix
        result = fix_field_index_ordering()
        
        # Post-patch validation
        if post_patch_validation():
            print("✅ Sales Invoice field index ordering fix completed successfully")
            print("📊 Fields reordered:", result.get('fields_reordered', 0))
        else:
            print("❌ Post-patch validation failed. Rolling back...")
            rollback_field_indices(backup_data)
            frappe.throw(_("Patch failed validation and was rolled back"))
            
    except Exception as e:
        print(f"❌ Patch execution failed: {str(e)}")
        # Auto-rollback on any error
        if 'backup_data' in locals():
            rollback_field_indices(backup_data)
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
            
        # Count problematic fields
        problematic_fields = [
            "custom_subject_to_retention",
            "custom_net_total_after_wht_retention", 
            "custom_net_total_after_wht_retention_in_words",
            "custom_retention_note"
        ]
        
        existing_count = 0
        for field in problematic_fields:
            if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field}):
                existing_count += 1
                
        print(f"✅ Found {existing_count}/{len(problematic_fields)} retention fields")
        
        if existing_count < 3:  # At least 3 fields should exist
            print(f"⚠️ Only {existing_count} retention fields found, expected at least 3")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Pre-patch validation error: {str(e)}")
        return False


def backup_current_field_indices():
    """Backup current field indices for rollback capability"""
    print("💾 Backing up current field indices...")
    
    try:
        current_fields = frappe.get_all("Custom Field",
            filters={"dt": "Sales Invoice"},
            fields=["name", "fieldname", "idx", "insert_after"],
            order_by="idx"
        )
        
        # Focus on WHT preview section fields
        wht_fields = [
            "thai_wht_preview_section", "wht_amounts_column_break", "vat_treatment", 
            "subject_to_wht", "wht_income_type", "wht_description", "wht_certificate_required",
            "net_total_after_wht", "net_total_after_wht_in_words", "wht_note",
            "wht_preview_column_break", "custom_subject_to_retention",
            "custom_net_total_after_wht_retention", "custom_net_total_after_wht_retention_in_words",
            "custom_retention_note"
        ]
        
        backup = {}
        for field in current_fields:
            if field.fieldname in wht_fields:
                backup[field.fieldname] = {
                    'idx': field.idx,
                    'insert_after': field.insert_after,
                    'name': field.name
                }
                
        print(f"💾 Backed up {len(backup)} field configurations")
        return backup
        
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}")
        return {}


def fix_field_index_ordering():
    """Apply the field index ordering fix"""
    print("🔧 Applying field index ordering fix...")
    
    try:
        # Get current thai_wht_preview_section index as base
        preview_section = frappe.get_doc("Custom Field", 
            {"dt": "Sales Invoice", "fieldname": "thai_wht_preview_section"})
        base_idx = preview_section.idx
        
        print(f"📍 Base index for thai_wht_preview_section: {base_idx}")
        
        # Define the correct sequential ordering starting from base_idx
        field_sequence = [
            ("thai_wht_preview_section", base_idx),
            ("wht_amounts_column_break", base_idx + 1),
            ("vat_treatment", base_idx + 2), 
            ("subject_to_wht", base_idx + 3),
            ("wht_income_type", base_idx + 4),
            ("wht_description", base_idx + 5),
            ("wht_certificate_required", base_idx + 6),
            ("net_total_after_wht", base_idx + 7),
            ("net_total_after_wht_in_words", base_idx + 8),
            ("wht_note", base_idx + 9),
            ("wht_preview_column_break", base_idx + 10),
            ("custom_subject_to_retention", base_idx + 11),
            ("custom_net_total_after_wht_retention", base_idx + 12),
            ("custom_net_total_after_wht_retention_in_words", base_idx + 13),
            ("custom_retention_note", base_idx + 14),
        ]
        
        reordered_count = 0
        for fieldname, new_idx in field_sequence:
            field_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
            
            if field_exists:
                # Update both idx and insert_after to ensure proper ordering
                current_field = frappe.get_doc("Custom Field", field_exists)
                old_idx = current_field.idx
                
                if old_idx != new_idx:
                    frappe.db.set_value("Custom Field", field_exists, "idx", new_idx)
                    print(f"✅ Reordered {fieldname}: {old_idx} → {new_idx}")
                    reordered_count += 1
                else:
                    print(f"✓ {fieldname} already has correct index: {new_idx}")
            else:
                print(f"⚠️ Field not found: {fieldname}")
        
        # Also fix insert_after chain to be consistent
        insert_after_fixes = [
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
        
        for fieldname, correct_insert_after in insert_after_fixes:
            field_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
            
            if field_exists:
                frappe.db.set_value("Custom Field", field_exists, "insert_after", correct_insert_after)
                print(f"✅ Fixed insert_after for {fieldname} → after: {correct_insert_after}")
        
        # Commit changes atomically
        frappe.db.commit()
        
        print(f"✅ Successfully reordered {reordered_count} field indices")
        return {"success": True, "fields_reordered": reordered_count}
        
    except Exception as e:
        frappe.db.rollback()
        raise Exception(f"Field index ordering fix failed: {str(e)}")


def post_patch_validation():
    """Validate that the patch was applied correctly"""
    print("✅ Running post-patch validation...")
    
    try:
        # Check the critical retention field ordering
        retention_fields = [
            ("custom_subject_to_retention", "wht_preview_column_break"),
            ("custom_net_total_after_wht_retention", "custom_subject_to_retention"), 
            ("custom_net_total_after_wht_retention_in_words", "custom_net_total_after_wht_retention"),
            ("custom_retention_note", "custom_net_total_after_wht_retention_in_words")
        ]
        
        indices = []
        for fieldname, expected_after in retention_fields:
            try:
                field_doc = frappe.get_doc("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
                indices.append((fieldname, field_doc.idx))
                
                # Validate insert_after is correct
                if field_doc.insert_after != expected_after:
                    print(f"❌ Insert_after issue: {fieldname} → {field_doc.insert_after}, expected: {expected_after}")
                    return False
                    
                print(f"✅ {fieldname}: index {field_doc.idx}, after: {field_doc.insert_after}")
            except Exception as e:
                print(f"❌ Field validation error for {fieldname}: {str(e)}")
                return False
        
        # Validate indices are in ascending order
        for i in range(1, len(indices)):
            if indices[i][1] <= indices[i-1][1]:
                print(f"❌ Index ordering issue: {indices[i-1][0]} ({indices[i-1][1]}) >= {indices[i][0]} ({indices[i][1]})")
                return False
        
        print("✅ Post-patch validation passed - all indices and insert_after values correct")
        return True
        
    except Exception as e:
        print(f"❌ Post-patch validation error: {str(e)}")
        return False


def rollback_field_indices(backup_data):
    """Rollback field indices using backup data"""
    print("🔄 Rolling back field indices...")
    
    try:
        rollback_count = 0
        for fieldname, backup_info in backup_data.items():
            field_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
            
            if field_exists:
                frappe.db.set_value("Custom Field", field_exists, "idx", backup_info['idx'])
                frappe.db.set_value("Custom Field", field_exists, "insert_after", backup_info['insert_after'])
                rollback_count += 1
                
        frappe.db.commit()
        print(f"🔄 Rolled back {rollback_count} field indices to original state")
        
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