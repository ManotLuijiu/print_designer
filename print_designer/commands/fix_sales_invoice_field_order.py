#!/usr/bin/env python3
"""
Fix Sales Invoice field insertion order
The reinstall doesn't fix existing field order - we need to manually update insert_after values
"""

import frappe

def fix_sales_invoice_field_order():
    """Fix the insert_after chain for Sales Invoice WHT preview section fields"""
    print("=== Fixing Sales Invoice Field Order ===")
    
    # Define the correct insert_after chain
    field_order_fixes = [
        # WHT Chain - Left Column
        ("subject_to_wht", "vat_treatment"),
        ("wht_income_type", "subject_to_wht"), 
        ("wht_description", "wht_income_type"),
        ("wht_certificate_required", "wht_description"),
        ("net_total_after_wht", "wht_certificate_required"),
        ("net_total_after_wht_in_words", "net_total_after_wht"),
        ("wht_note", "net_total_after_wht_in_words"),
        # Right Column  
        ("wht_preview_column_break", "wht_note"),
        ("custom_subject_to_retention", "wht_preview_column_break"),
        ("custom_net_total_after_wht_retention", "custom_subject_to_retention"),
        ("custom_net_total_after_wht_retention_in_words", "custom_net_total_after_wht_retention"), 
        ("custom_retention_note", "custom_net_total_after_wht_retention_in_words"),
    ]
    
    try:
        fixed_count = 0
        for fieldname, correct_insert_after in field_order_fixes:
            # Find the custom field document
            field_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": fieldname})
            
            if field_exists:
                # Update the insert_after value using Frappe's ORM
                frappe.db.set_value("Custom Field", field_exists, "insert_after", correct_insert_after)
                print(f"✅ Fixed {fieldname} → after: {correct_insert_after}")
                fixed_count += 1
            else:
                print(f"⚠️ Field not found: {fieldname}")
        
        # Commit the changes
        frappe.db.commit()
        
        # Clear cache to ensure changes take effect
        frappe.clear_cache(doctype="Sales Invoice")
        
        print(f"\n✅ Fixed {fixed_count} field insertion orders")
        print("🔄 Cache cleared. Please reload the Sales Invoice form to see the corrected field order")
        
        return {"success": True, "fields_fixed": fixed_count}
        
    except Exception as e:
        frappe.db.rollback()
        error_msg = f"❌ Error fixing field order: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

def validate_field_order_fix():
    """Validate that the field order was fixed correctly"""
    print("\n=== Validating Fixed Field Order ===")
    
    try:
        fields = frappe.get_all("Custom Field", 
            filters={"dt": "Sales Invoice"},
            fields=["fieldname", "insert_after"], 
            order_by="idx"
        )
        
        print("🔍 Current field insertion chain:")
        wht_preview_fields = [
            "wht_amounts_column_break", "vat_treatment", "subject_to_wht", 
            "wht_income_type", "wht_description", "wht_certificate_required",
            "net_total_after_wht", "net_total_after_wht_in_words", "wht_note",
            "wht_preview_column_break", "custom_subject_to_retention",
            "custom_net_total_after_wht_retention", "custom_net_total_after_wht_retention_in_words",
            "custom_retention_note"
        ]
        
        for field in fields:
            if field.fieldname in wht_preview_fields:
                status = "✅" if field.insert_after else "⚠️"
                print(f"{status} {field.fieldname:<40} → after: {field.insert_after or 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating field order: {str(e)}")
        return False

if __name__ == "__main__":
    fix_sales_invoice_field_order()
    validate_field_order_fix()