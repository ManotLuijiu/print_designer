#!/usr/bin/env python3
"""
Quick fix for Sales Invoice field insertion points and field type changes
"""

import frappe

def fix_sales_invoice_insertion_points():
    """Fix the critical Sales Invoice field insertion points"""
    try:
        print("=== Fixing Sales Invoice field insertion points ===")
        
        fixes_applied = []
        
        # Fix 1: Move wht_certificate_required to proper position in chain
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-wht_certificate_required", 
                "insert_after", 
                "net_total_after_wht_in_words"
            )
            fixes_applied.append("wht_certificate_required: wht_description → net_total_after_wht_in_words")
        except Exception as e:
            print(f"⚠️ Failed to fix wht_certificate_required: {e}")
        
        # Fix 2: net_total_after_wht insertion point
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-net_total_after_wht", 
                "insert_after", 
                "wht_description"
            )
            fixes_applied.append("net_total_after_wht: wht_certificate_required → wht_description")
        except Exception as e:
            print(f"⚠️ Failed to fix net_total_after_wht: {e}")
            
        # Fix 3: net_total_after_wht_in_words field type change
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-net_total_after_wht_in_words", 
                "fieldtype", 
                "Data"
            )
            fixes_applied.append("net_total_after_wht_in_words: Small Text → Data")
        except Exception as e:
            print(f"⚠️ Failed to fix net_total_after_wht_in_words: {e}")
        
        # Fix 4: subject_to_wht proper position
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-subject_to_wht", 
                "insert_after", 
                "vat_treatment"
            )
            fixes_applied.append("subject_to_wht: taxes_and_charges → vat_treatment")
        except Exception as e:
            print(f"⚠️ Failed to fix subject_to_wht: {e}")
        
        # Commit all changes
        frappe.db.commit()
        
        print(f"✅ Applied {len(fixes_applied)} fixes:")
        for fix in fixes_applied:
            print(f"   - {fix}")
        
        return {"success": True, "fixes_applied": fixes_applied}
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    fix_sales_invoice_insertion_points()