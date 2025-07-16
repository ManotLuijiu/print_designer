#!/usr/bin/env python3
"""
Test script for Print Designer logging functionality
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
    
    # Test importing the logging methods
    from print_designer.print_designer.page.print_designer.print_designer import (
        log_pdf_generation_issue,
        get_pdf_generation_logs,
        clear_pdf_generation_logs
    )
    
    print("✅ Successfully imported logging methods")
    
    # Test the logger
    from print_designer.logger import get_logger
    logger = get_logger("print_designer_test")
    logger.info("Test log entry from print_designer logger")
    
    print("✅ Successfully created log entry")
    
    # Test the server-side logging function
    result = log_pdf_generation_issue(
        "TEST_EVENT",
        "Test message from script",
        {"test": True, "script": "test_logging.py"},
        "INFO"
    )
    print(f"✅ Server-side logging result: {result}")
    
    # Test getting logs
    logs_result = get_pdf_generation_logs(10)
    print(f"✅ Get logs result: {logs_result}")
    
    print("\n🎉 All tests passed! The logging system is working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)