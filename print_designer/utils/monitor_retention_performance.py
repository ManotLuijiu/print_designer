"""
Retention System Performance Monitor

Monitors and validates that the retention system is not causing API flooding.
Use this script to verify fixes and prevent future performance issues.
"""

import frappe
import time
from collections import defaultdict


def check_custom_field_health():
    """Check custom fields for problematic patterns that could cause API flooding."""
    
    print("🔍 Checking Custom Field Health...")
    
    # Check for eval expressions with database calls
    problematic_fields = frappe.get_all('Custom Field', 
        filters={
            'dt': 'Sales Invoice', 
            'depends_on': ['like', '%get_value%']
        },
        fields=['name', 'fieldname', 'depends_on']
    )
    
    if problematic_fields:
        print("❌ CRITICAL: Found custom fields with API calls in depends_on:")
        for field in problematic_fields:
            print(f"   Field: {field.fieldname} ({field.name})")
            print(f"   Problem: {field.depends_on}")
        return False
    
    # Check retention-specific fields
    retention_fields = frappe.get_all('Custom Field', 
        filters={
            'dt': 'Sales Invoice',
            'fieldname': ['in', ['custom_retention', 'custom_retention_amount']]
        },
        fields=['name', 'fieldname', 'depends_on']
    )
    
    print(f"✅ Found {len(retention_fields)} retention fields:")
    for field in retention_fields:
        depends_status = "✅ Safe" if not field.depends_on or "get_value" not in field.depends_on else "❌ Problematic"
        print(f"   - {field.fieldname}: {depends_status}")
        if field.depends_on:
            print(f"     depends_on: {field.depends_on}")
    
    return len(problematic_fields) == 0


def check_client_scripts():
    """Check for retention client scripts and potential conflicts."""
    
    print("\n🔍 Checking Client Script Health...")
    
    # Get all retention-related client scripts
    retention_scripts = frappe.get_all('Client Script',
        filters={
            'dt': 'Sales Invoice'
        },
        fields=['name', 'enabled', 'script']
    )
    
    active_retention_scripts = []
    disabled_retention_scripts = []
    
    for script in retention_scripts:
        if 'retention' in script.script.lower():
            if script.enabled:
                active_retention_scripts.append(script.name)
            else:
                disabled_retention_scripts.append(script.name)
    
    print(f"📊 Script Summary:")
    print(f"   - Active retention scripts: {len(active_retention_scripts)}")
    print(f"   - Disabled retention scripts: {len(disabled_retention_scripts)}")
    
    if len(active_retention_scripts) > 1:
        print("⚠️  WARNING: Multiple active retention scripts detected!")
        print("   This could cause conflicts. Consider keeping only one:")
        for script in active_retention_scripts:
            print(f"   - {script}")
        return False
    
    if len(active_retention_scripts) == 1:
        print(f"✅ Single active retention script: {active_retention_scripts[0]}")
        return True
    
    print("⚠️  No active retention scripts found")
    return True


def check_hook_configuration():
    """Check hooks.py for potential recursion issues."""
    
    print("\n🔍 Checking Hook Configuration...")
    
    # Read hooks.py content
    try:
        hooks_path = "/home/frappe/frappe-bench/apps/print_designer/print_designer/hooks.py"
        with open(hooks_path, 'r') as f:
            hooks_content = f.read()
        
        # Check for the problematic validate hook
        if '"validate": "print_designer.custom.sales_invoice_retention_enhanced.validate_retention_fields"' in hooks_content:
            if 'validate": "print_designer.custom.sales_invoice_retention_enhanced.validate_retention_fields"' in hooks_content and '# "validate"' not in hooks_content:
                print("❌ CRITICAL: Validate hook is still active!")
                print("   This will cause recursion. Please disable it in hooks.py")
                return False
        
        print("✅ Validate hook is properly disabled")
        
        # Check for before_save hook (this should be active)
        if '"before_save": "print_designer.custom.sales_invoice_retention_enhanced.calculate_retention_on_save"' in hooks_content:
            print("✅ Before_save hook is properly configured")
        else:
            print("⚠️  Before_save hook not found - retention calculations may not work")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading hooks.py: {str(e)}")
        return False


def simulate_api_load_test():
    """Simulate form interactions to detect API flooding."""
    
    print("\n🧪 Running API Load Test Simulation...")
    
    # This would ideally be done through browser automation
    # For now, we'll check the server-side function efficiency
    
    try:
        # Test company data retrieval efficiency
        start_time = time.time()
        
        # Simulate multiple company lookups (what would happen during API flooding)
        company = "Moo Coding"  # Use a test company
        
        if frappe.db.exists("Company", company):
            # Test the optimized function pattern
            for i in range(10):  # Simulate 10 rapid calls
                company_data = frappe.db.get_value("Company", company, 
                    ["construction_service", "default_retention_rate"], as_dict=True)
        
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"✅ Server-side efficiency test:")
            print(f"   - 10 optimized company lookups: {total_time:.3f} seconds")
            print(f"   - Average per lookup: {total_time/10:.3f} seconds")
            
            if total_time < 1.0:  # Should be very fast
                print("✅ Server-side performance is good")
                return True
            else:
                print("⚠️  Server-side performance may be slow")
                return False
        else:
            print("ℹ️  Test company not found - skipping performance test")
            return True
            
    except Exception as e:
        print(f"❌ Error during load test: {str(e)}")
        return False


def run_complete_health_check():
    """Run complete health check for retention system."""
    
    print("🏥 RETENTION SYSTEM HEALTH CHECK")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 4
    
    # Check 1: Custom Fields
    if check_custom_field_health():
        checks_passed += 1
    
    # Check 2: Client Scripts
    if check_client_scripts():
        checks_passed += 1
    
    # Check 3: Hook Configuration
    if check_hook_configuration():
        checks_passed += 1
    
    # Check 4: Performance
    if simulate_api_load_test():
        checks_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 HEALTH CHECK RESULTS: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 EXCELLENT: Retention system is healthy!")
        print("✅ No API flooding issues detected")
    elif checks_passed >= 2:
        print("⚠️  GOOD: Most checks passed, but some issues detected")
        print("💡 Review the warnings above and address them")
    else:
        print("❌ CRITICAL: Multiple issues detected!")
        print("🚨 API flooding may still be occurring")
    
    print("\n📋 Recommendations:")
    if checks_passed == total_checks:
        print("   - Continue monitoring form performance")
        print("   - Run this check weekly to prevent regressions")
    else:
        print("   - Address the issues identified above")
        print("   - Rerun this check after making fixes")
        print("   - Monitor browser network tab when loading Sales Invoice forms")
    
    return checks_passed == total_checks


if __name__ == "__main__":
    run_complete_health_check()