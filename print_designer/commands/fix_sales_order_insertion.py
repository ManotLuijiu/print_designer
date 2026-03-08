#!/usr/bin/env python3
"""
Quick fix for Sales Order field insertion points
"""

import frappe

def fix_sales_order_insertion_points():
    """Fix the critical Sales Order field insertion points"""
    try:
        print("=== Fixing Sales Order field insertion points ===")
        
        fixes_applied = []
        
        # Fix 1: pd_custom_subject_to_wht insertion point
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Order-pd_custom_subject_to_wht", 
                "insert_after", 
                "pd_custom_vat_treatment"
            )
            fixes_applied.append("pd_custom_subject_to_wht: wht_section → pd_custom_vat_treatment")
        except Exception as e:
            print(f"⚠️ Failed to fix pd_custom_subject_to_wht: {e}")
        
        # Fix 2: pd_custom_net_total_after_wht insertion point
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Order-pd_custom_net_total_after_wht", 
                "insert_after", 
                "pd_custom_wht_description"
            )
            fixes_applied.append("pd_custom_net_total_after_wht: Fixed field reference")
        except Exception as e:
            print(f"⚠️ Failed to fix pd_custom_net_total_after_wht: {e}")
            
        # Fix 3: pd_custom_net_total_after_wht_words field type change
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Order-pd_custom_net_total_after_wht_words", 
                "fieldtype", 
                "Data"
            )
            fixes_applied.append("pd_custom_net_total_after_wht_words: Small Text → Data")
        except Exception as e:
            print(f"⚠️ Failed to fix pd_custom_net_total_after_wht_words: {e}")
        
        # Fix 4: has_deposit typo fix
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Order-has_deposit", 
                "label", 
                "Deposit on 1st Invoice"
            )
            fixes_applied.append("has_deposit: Desposit → Deposit")
        except Exception as e:
            print(f"⚠️ Failed to fix has_deposit label: {e}")
        
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
    fix_sales_order_insertion_points()