#!/usr/bin/env python3
"""
Test script for the new PDF logging module
"""
import sys
import os

# Add the frappe-bench path to Python path
sys.path.insert(0, '/home/frappe/frappe-bench/apps/frappe')
sys.path.insert(0, '/home/frappe/frappe-bench/apps/print_designer')

try:
    import frappe
    
    # Initialize Frappe
    frappe.init('soeasy.bunchee.online')
    frappe.connect()
    
    # Test importing the new logging module
    from print_designer.pdf_logging import (
        log_pdf_generation_issue,
        get_pdf_generation_logs,
        clear_pdf_generation_logs,
        test_pdf_logging
    )
    
    print("✅ Successfully imported new PDF logging module")
    
    # Test the test function
    result = test_pdf_logging()
    print(f"✅ Test function result: {result}")
    
    # Test direct logging
    log_result = log_pdf_generation_issue(
        "DIRECT_TEST",
        "Direct test from script",
        {"test": True, "method": "direct"},
        "INFO"
    )
    print(f"✅ Direct logging result: {log_result}")
    
    # Test getting logs
    logs_result = get_pdf_generation_logs(5)
    print(f"✅ Get logs result: {logs_result}")
    
    print("\n🎉 New PDF logging module is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)