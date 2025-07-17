#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/home/frappe/frappe-bench')

# Set up Frappe environment
os.environ['FRAPPE_SITE'] = 'all'

import frappe
from frappe.utils import get_sites

# Test the override
def test_override():
    try:
        # Import ERPNext install module
        import erpnext.setup.install
        
        # Check if the function has been overridden
        func = erpnext.setup.install.create_print_setting_custom_fields
        
        # Check if it's our function
        if hasattr(func, '__module__') and 'print_designer' in func.__module__:
            print("✅ SUCCESS: Function has been overridden by print_designer")
            print(f"Function module: {func.__module__}")
            print(f"Function name: {func.__name__}")
        else:
            print("❌ FAIL: Function has not been overridden")
            print(f"Function module: {func.__module__}")
            print(f"Function name: {func.__name__}")
            
        return True
        
    except ImportError as e:
        print(f"❌ FAIL: Cannot import ERPNext: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error testing override: {e}")
        return False

if __name__ == "__main__":
    # Initialize Frappe
    frappe.init('')
    
    print("Testing ERPNext function override...")
    test_override()