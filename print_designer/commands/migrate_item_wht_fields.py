"""
Migrate pd_custom_wht_income_type to ERPNext standard fields.

ERPNext already has standard fields:
- sales_tax_withholding_category (for Sales transactions)
- purchase_tax_withholding_category (for Purchase transactions)

This script copies data from pd_custom_wht_income_type to both standard fields.
"""

import frappe


def execute():
    """Migrate pd_custom_wht_income_type to ERPNext standard fields."""
    
    print("Starting migration of pd_custom_wht_income_type to ERPNext standard fields...")
    
    # Get all items with pd_custom_wht_income_type set
    items = frappe.get_all(
        "Item",
        filters={"pd_custom_wht_income_type": ["is", "set"]},
        fields=["name", "pd_custom_wht_income_type"]
    )
    
    if not items:
        print("No items found with pd_custom_wht_income_type set.")
        return
    
    print(f"Found {len(items)} items with pd_custom_wht_income_type set.")
    
    migrated = 0
    for item in items:
        try:
            frappe.db.set_value(
                "Item",
                item.name,
                {
                    "sales_tax_withholding_category": item.pd_custom_wht_income_type,
                    "purchase_tax_withholding_category": item.pd_custom_wht_income_type
                }
            )
            migrated += 1
            print(f"  ✅ Migrated: {item.name} -> {item.pd_custom_wht_income_type}")
        except Exception as e:
            print(f"  ❌ Failed to migrate {item.name}: {str(e)}")
    
    frappe.db.commit()
    print(f"\nMigration complete: {migrated}/{len(items)} items migrated.")
    print("\nNOTE: After migration, you can safely delete the pd_custom_wht_income_type custom field.")
    print("Run: bench --site <site> remove-from-installed-apps print_designer (to trigger uninstall)")
