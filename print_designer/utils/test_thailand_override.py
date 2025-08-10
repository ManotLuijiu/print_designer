#!/usr/bin/env python3
"""
Test script to verify the ERPNext Thailand override is working
Run this with: bench --site all execute test_thailand_override.test_thailand_override
"""

import frappe

def test_thailand_override():
    """Test that the ERPNext Thailand override is working correctly"""
    
    print("=== Testing ERPNext Thailand Override ===")
    
    # Test 1: Check override status
    try:
        from print_designer.utils.override_thailand import check_thailand_override_status
        status = check_thailand_override_status()
        
        print("1. Override Status:")
        print(f"   Thailand installed: {status['thailand_installed']}")
        print(f"   Thailand monkey patched: {status['thailand_monkey_patched']}")
        print(f"   Override active: {status['override_active']}")
        print(f"   Custom field exists: {status['custom_field_exists']}")
        print(f"   Safe to generate PDF: {status['safe_to_generate_pdf']}")
        
    except Exception as e:
        print(f"1. Override status check failed: {e}")
        return
    
    # Test 2: Apply override manually (if not already applied)
    if not status['override_active'] and status['thailand_monkey_patched']:
        try:
            from print_designer.utils.override_thailand import override_thailand_monkey_patch
            override_applied = override_thailand_monkey_patch()
            
            if override_applied:
                print("2. Override application: ✓ Successfully applied")
                
                # Check status again
                status = check_thailand_override_status()
                print(f"   Override now active: {status['override_active']}")
                print(f"   Safe to generate PDF: {status['safe_to_generate_pdf']}")
            else:
                print("2. Override application: ✗ Not applied (may not be needed)")
                
        except Exception as e:
            print(f"2. Override application failed: {e}")
    else:
        print("2. Override application: ✓ Already active or not needed")
    
    # Test 3: Test PDF generation with the override
    try:
        # Find a test document
        test_doc = frappe.get_value("Sales Invoice", {"docstatus": 1}, "name")
        
        if test_doc:
            print(f"3. Test document found: {test_doc}")
            
            # Test PDF generation
            try:
                result = frappe.get_print(
                    doctype="Sales Invoice",
                    name=test_doc,
                    print_format="Standard",
                    as_pdf=True
                )
                
                print("   PDF generation: ✓ SUCCESS")
                print(f"   PDF size: {len(result)} bytes")
                
            except Exception as e:
                print(f"   PDF generation: ✗ FAILED - {e}")
                
                # Check if this is still the add_comment_info error
                if "add_comment_info" in str(e):
                    print("   ERROR: Still getting add_comment_info error - override may not be working")
                else:
                    print("   ERROR: Different error - may not be related to ERPNext Thailand")
                    
        else:
            print("3. Test document: ✗ No Sales Invoice found for testing")
            
    except Exception as e:
        print(f"3. Test document search failed: {e}")
    
    # Test 4: Test specific user scenario
    try:
        print("4. Testing user's specific scenario...")
        
        # Check if user's document exists
        user_doc = "ACC-SINV-2025-00002"
        user_format = "ใบกำกับภาษี"
        
        doc_exists = frappe.db.exists("Sales Invoice", user_doc)
        format_exists = frappe.db.exists("Print Format", user_format)
        
        print(f"   User document exists: {doc_exists}")
        print(f"   User format exists: {format_exists}")
        
        if doc_exists and format_exists:
            # Test the exact scenario that was failing
            try:
                result = frappe.get_print(
                    doctype="Sales Invoice",
                    name=user_doc,
                    print_format=user_format,
                    as_pdf=True
                )
                
                print("   User scenario: ✓ SUCCESS")
                print(f"   PDF size: {len(result)} bytes")
                
            except Exception as e:
                print(f"   User scenario: ✗ FAILED - {e}")
                
                if "add_comment_info" in str(e):
                    print("   ERROR: Still getting add_comment_info error - override not working for user scenario")
                else:
                    print("   ERROR: Different error - may not be related to ERPNext Thailand")
                    
        else:
            print("   User scenario: ✗ Cannot test - document or format not found")
            
    except Exception as e:
        print(f"4. User scenario test failed: {e}")
    
    print("\n=== Test Results ===")
    
    # Final status check
    try:
        final_status = check_thailand_override_status()
        
        if final_status['safe_to_generate_pdf']:
            print("✓ PDF generation should work without 403 errors")
            
            if final_status['override_active']:
                print("✓ Print Designer override is active and protecting against ERPNext Thailand conflicts")
            elif not final_status['thailand_monkey_patched']:
                print("✓ ERPNext Thailand is not monkey patching (no conflict)")
            else:
                print("✓ ERPNext Thailand custom field exists (no conflict)")
                
        else:
            print("✗ PDF generation may still cause 403 errors")
            print("  Recommended actions:")
            
            if final_status['thailand_monkey_patched'] and not final_status['override_active']:
                print("  - Apply the Print Designer override")
            if not final_status['custom_field_exists']:
                print("  - Install ERPNext Thailand custom fields")
                print("  - Or use Print Designer safe endpoints")
                
    except Exception as e:
        print(f"Final status check failed: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_thailand_override()