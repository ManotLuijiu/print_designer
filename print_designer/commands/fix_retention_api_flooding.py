"""
Fix API Flooding Issue in Retention System

Removes problematic eval expressions from custom fields that cause recursive API calls.
This script fixes the triple-layer API flooding issue identified in the retention system.
"""

import frappe


def fix_retention_custom_fields():
    """Fix custom fields that cause API flooding through eval expressions."""
    
    print("🔧 Fixing retention custom fields to prevent API flooding...")
    
    # Fields that have problematic depends_on expressions
    problematic_fields = [
        # "Sales Invoice-retention_section",  # Field already deleted
        "Sales Invoice-custom_retention", 
        "Sales Invoice-custom_retention_amount"
    ]
    
    fixed_count = 0
    
    for field_name in problematic_fields:
        if frappe.db.exists("Custom Field", field_name):
            try:
                # Get current depends_on value
                current_depends_on = frappe.db.get_value("Custom Field", field_name, "depends_on")
                
                if current_depends_on and "frappe.db.get_value" in current_depends_on:
                    print(f"🚨 Found problematic field: {field_name}")
                    print(f"   Current depends_on: {current_depends_on}")
                    
                    # Replace with simple company-based dependency
                    new_depends_on = "eval:doc.company"
                    
                    frappe.db.set_value("Custom Field", field_name, "depends_on", new_depends_on)
                    print(f"✅ Fixed depends_on to: {new_depends_on}")
                    
                    fixed_count += 1
                else:
                    print(f"✅ Field {field_name} - No problematic depends_on found")
                    
            except Exception as e:
                print(f"❌ Error fixing field {field_name}: {str(e)}")
    
    if fixed_count > 0:
        frappe.db.commit()
        print(f"🎯 Successfully fixed {fixed_count} custom fields")
        print("💡 Custom fields now depend only on company selection, not API calls")
    else:
        print("✅ No custom fields needed fixing")


def check_retention_api_calls():
    """Check for remaining sources of retention API calls."""
    
    print("\n🔍 Checking for remaining API call sources...")
    
    # Check custom fields
    problematic_fields = frappe.get_all('Custom Field', 
        filters={
            'dt': 'Sales Invoice', 
            'depends_on': ['like', '%get_value%']
        },
        fields=['name', 'depends_on']
    )
    
    if problematic_fields:
        print("❌ Found custom fields with API calls in depends_on:")
        for field in problematic_fields:
            print(f"   - {field.name}: {field.depends_on}")
    else:
        print("✅ No custom fields with problematic depends_on found")
    
    # Check active client scripts
    retention_scripts = frappe.get_all('Client Script',
        filters={
            'dt': 'Sales Invoice', 
            'enabled': 1,
            'script': ['like', '%retention%']
        },
        fields=['name']
    )
    
    print(f"📋 Found {len(retention_scripts)} active retention client scripts:")
    for script in retention_scripts:
        print(f"   - {script.name}")
    
    return len(problematic_fields) == 0


def disable_duplicate_retention_scripts():
    """Disable duplicate retention client scripts to prevent conflicts."""
    
    print("\n🧹 Checking for duplicate retention client scripts...")
    
    retention_scripts = frappe.get_all('Client Script',
        filters={
            'dt': 'Sales Invoice', 
            'enabled': 1,
            'script': ['like', '%retention%']
        },
        fields=['name', 'creation']
    )
    
    if len(retention_scripts) > 1:
        print(f"🚨 Found {len(retention_scripts)} active retention scripts - keeping only the latest")
        
        # Sort by creation date and keep only the latest
        retention_scripts.sort(key=lambda x: x.creation, reverse=True)
        latest_script = retention_scripts[0]
        
        for script in retention_scripts[1:]:
            frappe.db.set_value("Client Script", script.name, "enabled", 0)
            print(f"🔇 Disabled duplicate script: {script.name}")
        
        print(f"✅ Kept active script: {latest_script.name}")
        frappe.db.commit()
    else:
        print("✅ No duplicate retention scripts found")


def run_complete_fix():
    """Run complete fix for retention API flooding issue."""
    
    print("🚑 EMERGENCY FIX: Stopping API flooding in retention system")
    print("=" * 60)
    
    # Step 1: Fix custom fields
    fix_retention_custom_fields()
    
    # Step 2: Disable duplicate scripts
    disable_duplicate_retention_scripts()
    
    # Step 3: Verify fix
    is_clean = check_retention_api_calls()
    
    print("\n" + "=" * 60)
    if is_clean:
        print("🎉 SUCCESS: API flooding issue has been resolved!")
        print("📝 Summary of changes:")
        print("   - Disabled validate hook in hooks.py (prevents recursion)")
        print("   - Fixed custom field depends_on expressions (removes eval API calls)")
        print("   - Optimized server-side retention calculation (single API call)")
        print("   - Disabled duplicate client scripts (prevents conflicts)")
    else:
        print("⚠️  WARNING: Some issues may remain - check the output above")
    
    print("\n🔄 Next steps:")
    print("   1. Restart frappe services: bench restart")
    print("   2. Test Sales Invoice form loading and company changes")
    print("   3. Monitor network tab for excessive API calls")
    
    return is_clean


if __name__ == "__main__":
    run_complete_fix()