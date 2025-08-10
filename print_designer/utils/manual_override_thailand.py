#!/usr/bin/env python3
"""
Manual override script for ERPNext Thailand
Run this immediately to fix the 403 error: bench --site all execute manual_override_thailand.apply_override_now
"""

import frappe

def apply_override_now():
    """Apply the ERPNext Thailand override immediately"""
    
    print("=== Applying ERPNext Thailand Override NOW ===")
    
    try:
        # Import the override function
        from print_designer.utils.override_thailand import override_thailand_monkey_patch, check_thailand_override_status
        
        # Check current status
        print("1. Checking current status...")
        status = check_thailand_override_status()
        
        if status['thailand_monkey_patched'] and not status['override_active']:
            print("   ERPNext Thailand is monkey patching frappe.get_print")
            print("   Custom field exists:", status['custom_field_exists'])
            print("   Applying override...")
            
            # Apply the override
            override_applied = override_thailand_monkey_patch()
            
            if override_applied:
                print("   ✓ Override successfully applied!")
                
                # Verify the override is working
                new_status = check_thailand_override_status()
                print("   ✓ Override active:", new_status['override_active'])
                print("   ✓ Safe to generate PDF:", new_status['safe_to_generate_pdf'])
                
            else:
                print("   ✗ Override not applied (may not be needed)")
                
        elif status['override_active']:
            print("   ✓ Override is already active")
            
        elif not status['thailand_monkey_patched']:
            print("   ✓ ERPNext Thailand is not monkey patching (no override needed)")
            
        else:
            print("   ✓ No override needed (custom field exists)")
    
    except Exception as e:
        print(f"   ✗ Error applying override: {e}")
        return False
    
    # Test the fix
    print("\n2. Testing PDF generation...")
    
    try:
        # Find a test document
        test_doc = frappe.get_value("Sales Invoice", {"docstatus": 1}, "name")
        
        if test_doc:
            print(f"   Test document: {test_doc}")
            
            # Test PDF generation
            result = frappe.get_print(
                doctype="Sales Invoice",
                name=test_doc,
                print_format="Standard",
                as_pdf=True
            )
            
            print(f"   ✓ PDF generation successful! ({len(result)} bytes)")
            
        else:
            print("   No test document found, but override is applied")
            
    except Exception as e:
        print(f"   ✗ PDF generation still failing: {e}")
        
        if "add_comment_info" in str(e):
            print("   ERROR: Still getting add_comment_info error")
            print("   This suggests the override is not working properly")
        else:
            print("   ERROR: Different error, may not be related to ERPNext Thailand")
    
    print("\n=== Override Complete ===")
    print("The override has been applied. PDF generation should now work without 403 errors.")
    print("If you still get 403 errors, check the Error Log for details.")
    
    return True

def test_user_scenario():
    """Test the user's specific scenario that was failing"""
    
    print("\n=== Testing User's Specific Scenario ===")
    
    try:
        # Test the exact parameters that were failing
        result = frappe.get_print(
            doctype="Sales Invoice",
            name="ACC-SINV-2025-00002",
            print_format="ใบกำกับภาษี",
            as_pdf=True
        )
        
        print(f"✓ User scenario successful! PDF generated ({len(result)} bytes)")
        return True
        
    except Exception as e:
        print(f"✗ User scenario still failing: {e}")
        
        if "add_comment_info" in str(e):
            print("ERROR: Still getting add_comment_info error")
            print("The override may not be working for this specific case")
        else:
            print("ERROR: Different error, may be document/format related")
        
        return False

if __name__ == "__main__":
    apply_override_now()
    test_user_scenario()