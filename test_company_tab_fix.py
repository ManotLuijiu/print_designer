#!/usr/bin/env python3

"""
Test script to check if Company Stamps & Signatures tab is properly configured
"""

import frappe

def test_company_tab():
    """Test if the Company tab is properly installed and configured"""
    
    # Check if Custom Field exists
    custom_field = frappe.db.get_value(
        "Custom Field",
        {"dt": "Company", "fieldname": "stamps_signatures_tab"},
        ["name", "label", "fieldtype", "insert_after", "idx"],
        as_dict=True
    )
    
    if custom_field:
        print("✅ Company Stamps & Signatures Custom Field found:")
        print(f"   - Name: {custom_field.name}")
        print(f"   - Label: {custom_field.label}")
        print(f"   - Field Type: {custom_field.fieldtype}")
        print(f"   - Insert After: {custom_field.insert_after}")
        print(f"   - Index: {custom_field.idx}")
        
        # Check if it's properly positioned after stock_tab
        if custom_field.insert_after == "stock_tab":
            print("✅ Tab is configured to appear after Stock tab")
        else:
            print(f"⚠️  Tab insert_after is '{custom_field.insert_after}', expected 'stock_tab'")
            
        return True
    else:
        print("❌ Company Stamps & Signatures Custom Field not found!")
        return False

def install_tab_if_missing():
    """Install the tab if it's missing"""
    if not test_company_tab():
        print("\n🔧 Installing Company Stamps & Signatures tab...")
        try:
            from print_designer.custom.company_tab import create_company_stamps_signatures_tab
            result = create_company_stamps_signatures_tab()
            if result:
                print("✅ Tab installation completed!")
                test_company_tab()  # Verify installation
            else:
                print("❌ Tab installation failed!")
        except Exception as e:
            print(f"❌ Error during installation: {str(e)}")

if __name__ == "__main__":
    import os
    import sys
    
    # Add the bench to the path
    bench_path = "/home/frappe/frappe-bench"
    if bench_path not in sys.path:
        sys.path.insert(0, bench_path)
    
    # Change to bench directory for Frappe context
    original_cwd = os.getcwd()
    os.chdir(bench_path)
    
    try:
        frappe.init(site="erpnext-dev-server.bunchee.online")
        frappe.connect()
        
        print("🔍 Testing Company Stamps & Signatures Tab Configuration\n")
        install_tab_if_missing()
        
        frappe.destroy()
    finally:
        os.chdir(original_cwd)