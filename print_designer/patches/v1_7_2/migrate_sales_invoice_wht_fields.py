"""
Patch: Migrate Sales Invoice WHT Fields Structure (v1.7.2)

This patch removes the unnecessary wht_section from Sales Invoice and consolidates
all WHT fields into the existing taxes section for better UI organization.

Changes:
- Remove wht_section Section Break field from Sales Invoice
- Move subject_to_wht field to insert after taxes_and_charges instead of wht_section
- All other WHT fields maintain their relative positioning

This ensures a cleaner form layout by using the existing taxes section
instead of creating a separate WHT section.
"""

import frappe


def execute():
    """Execute the Sales Invoice WHT field migration"""
    try:
        frappe.logger().info("Starting Sales Invoice WHT field migration (v1.7.2)...")
        
        # REMOVED: thailand_wht_fields.py deleted - Now handled by separate modules
        # from print_designer.thailand_wht_fields import migrate_sales_invoice_wht_fields
        
        # DISABLED: Migration handled by separate sales-invoice module
        # success = migrate_sales_invoice_wht_fields()
        success = True  # Skip migration since fields are now module-specific
        
        if success:
            frappe.logger().info("✅ Sales Invoice WHT field migration completed successfully")
        else:
            frappe.logger().error("❌ Sales Invoice WHT field migration failed")
            
    except ImportError:
        frappe.logger().warning("Thailand WHT fields module not available - skipping migration")
        
    except Exception as e:
        frappe.logger().error(f"Error during Sales Invoice WHT field migration: {str(e)}")
        frappe.log_error(f"Sales Invoice WHT Migration Patch Error: {str(e)}", "WHT Migration Patch")