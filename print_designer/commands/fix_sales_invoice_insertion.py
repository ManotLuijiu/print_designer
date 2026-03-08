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
        
        # Fix 1: Move pd_custom_wht_certificate_required to proper position in chain
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-pd_custom_wht_certificate_required", 
                "insert_after", 
                "pd_custom_net_total_after_wht_words"
            )
            fixes_applied.append("pd_custom_wht_certificate_required: pd_custom_wht_description → pd_custom_net_total_after_wht_words")
        except Exception as e:
            print(f"⚠️ Failed to fix pd_custom_wht_certificate_required: {e}")
        
        # Fix 2: pd_custom_net_total_after_wht insertion point
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-pd_custom_net_total_after_wht", 
                "insert_after", 
                "pd_custom_wht_description"
            )
            fixes_applied.append("pd_custom_net_total_after_wht: pd_custom_wht_certificate_required → pd_custom_wht_description")
        except Exception as e:
            print(f"⚠️ Failed to fix pd_custom_net_total_after_wht: {e}")
            
        # Fix 3: pd_custom_net_total_after_wht_words field type change
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-pd_custom_net_total_after_wht_words", 
                "fieldtype", 
                "Data"
            )
            fixes_applied.append("pd_custom_net_total_after_wht_words: Small Text → Data")
        except Exception as e:
            print(f"⚠️ Failed to fix pd_custom_net_total_after_wht_words: {e}")
        
        # Fix 4: pd_custom_subject_to_wht proper position
        try:
            frappe.db.set_value(
                "Custom Field", 
                "Sales Invoice-pd_custom_subject_to_wht", 
                "insert_after", 
                "pd_custom_vat_treatment"
            )
            fixes_applied.append("pd_custom_subject_to_wht: taxes_and_charges → pd_custom_vat_treatment")
        except Exception as e:
            print(f"⚠️ Failed to fix pd_custom_subject_to_wht: {e}")
        
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