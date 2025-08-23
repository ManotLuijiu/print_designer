#!/usr/bin/env python3
"""
Thailand WHT System Management Commands
======================================

This module provides command-line access to the comprehensive Thailand WHT system
for Print Designer. Merged and unified system from thailand_wht_fields.py.

Usage:
    bench execute print_designer.commands.thailand_wht_system.install_complete_system
    bench execute print_designer.commands.thailand_wht_system.check_complete_system
    bench execute print_designer.commands.thailand_wht_system.validate_system

Available Commands:
    - install_complete_system: Install all WHT fields for all DocTypes
    - check_complete_system: Check all WHT field installations
    - check_company_fields: Check Company WHT fields specifically
    - check_customer_fields: Check Customer WHT fields specifically
    - check_sales_documents: Check all sales document WHT fields
    - validate_system: Validate complete system configuration
    - reinstall_system: Reinstall/update all WHT fields
    - create_test_data: Create sample test data for testing
    - uninstall_system: Remove all WHT fields (cleanup)
"""

import frappe
from print_designer.thailand_wht_fields import (
    # Installation functions
    install_thailand_wht_fields,
    install_complete_thailand_wht_system,
    reinstall_thailand_wht_fields,
    uninstall_thailand_wht_fields,
    
    # Checking functions
    check_thailand_wht_fields,
    check_specific_doctype_wht_fields,
    check_company_wht_fields,
    check_customer_wht_fields,
    check_sales_document_wht_fields,
    
    # Utility functions
    validate_wht_setup,
    create_sample_wht_test_data,
    get_wht_income_type_description,
    get_standard_wht_rates,
    get_wht_rate_for_income_type,
    calculate_wht_amount,
    get_net_amount_after_wht,
    
    # Configuration functions
    get_thailand_wht_fields,
    get_wht_fields_for_doctype,
    has_wht_fields,
    get_doctypes_with_wht,
    migrate_sales_invoice_wht_fields,
)


def install_complete_system():
    """
    Install complete Thailand WHT system with all fields and configurations
    
    Command: bench execute print_designer.commands.thailand_wht_system.install_complete_system
    """
    print("=" * 80)
    print("🇹🇭 THAILAND WHT SYSTEM INSTALLATION")
    print("=" * 80)
    
    return install_complete_thailand_wht_system()


def check_complete_system():
    """
    Check complete Thailand WHT system installation across all DocTypes
    
    Command: bench execute print_designer.commands.thailand_wht_system.check_complete_system
    """
    print("=" * 80)
    print("🔍 THAILAND WHT SYSTEM VERIFICATION")
    print("=" * 80)
    
    return check_thailand_wht_fields()


def check_company_fields():
    """
    Check Company WHT configuration fields specifically
    
    Command: bench execute print_designer.commands.thailand_wht_system.check_company_fields
    """
    print("=" * 50)
    print("🏢 COMPANY WHT FIELDS CHECK")
    print("=" * 50)
    
    return check_company_wht_fields()


def check_customer_fields():
    """
    Check Customer WHT configuration fields specifically
    
    Command: bench execute print_designer.commands.thailand_wht_system.check_customer_fields
    """
    print("=" * 50)
    print("👥 CUSTOMER WHT FIELDS CHECK")
    print("=" * 50)
    
    return check_customer_wht_fields()


def check_sales_documents():
    """
    Check WHT fields across all sales documents (Quotation, Sales Order, Sales Invoice)
    
    Command: bench execute print_designer.commands.thailand_wht_system.check_sales_documents
    """
    print("=" * 60)
    print("📋 SALES DOCUMENTS WHT FIELDS CHECK")
    print("=" * 60)
    
    return check_sales_document_wht_fields()


def validate_system():
    """
    Validate complete Thailand WHT system configuration
    
    Command: bench execute print_designer.commands.thailand_wht_system.validate_system
    """
    print("=" * 60)
    print("✅ THAILAND WHT SYSTEM VALIDATION")
    print("=" * 60)
    
    return validate_wht_setup()


def reinstall_system():
    """
    Reinstall/update Thailand WHT fields (removes and reinstalls)
    
    Command: bench execute print_designer.commands.thailand_wht_system.reinstall_system
    """
    print("=" * 60)
    print("🔄 THAILAND WHT SYSTEM REINSTALLATION")
    print("=" * 60)
    
    return reinstall_thailand_wht_fields()


def uninstall_system():
    """
    Remove all Thailand WHT fields (cleanup operation)
    
    Command: bench execute print_designer.commands.thailand_wht_system.uninstall_system
    """
    print("=" * 60)
    print("🗑️  THAILAND WHT SYSTEM REMOVAL")
    print("=" * 60)
    
    confirm = input("⚠️  This will remove ALL Thailand WHT fields. Are you sure? (type 'YES' to confirm): ")
    if confirm != 'YES':
        print("❌ Operation cancelled")
        return False
    
    return uninstall_thailand_wht_fields()


def create_test_data():
    """
    Create sample test data for Thailand WHT system testing
    
    Command: bench execute print_designer.commands.thailand_wht_system.create_test_data
    """
    print("=" * 60)
    print("🧪 THAILAND WHT TEST DATA CREATION")
    print("=" * 60)
    
    return create_sample_wht_test_data()


def show_system_info():
    """
    Display information about the Thailand WHT system
    
    Command: bench execute print_designer.commands.thailand_wht_system.show_system_info
    """
    print("=" * 80)
    print("📊 THAILAND WHT SYSTEM INFORMATION")
    print("=" * 80)
    
    # Get field definitions
    wht_fields = get_thailand_wht_fields()
    doctypes = get_doctypes_with_wht()
    
    print(f"\n🏗️  System Configuration:")
    print(f"   - Total DocTypes configured: {len(doctypes)}")
    print(f"   - DocTypes: {', '.join(doctypes)}")
    
    print(f"\n📝 Field Summary:")
    total_fields = 0
    for doctype, fields in wht_fields.items():
        field_count = len(fields)
        total_fields += field_count
        print(f"   - {doctype}: {field_count} fields")
    
    print(f"\n📊 Total fields across all DocTypes: {total_fields}")
    
    print(f"\n🔧 Standard WHT Rates:")
    rates = get_standard_wht_rates()
    for income_type, rate in rates.items():
        description = get_wht_income_type_description(income_type)
        print(f"   - {income_type}: {rate}% ({description})")
    
    print(f"\n🎯 Available Commands:")
    commands = [
        "install_complete_system - Install all WHT fields",
        "check_complete_system - Verify installation",
        "check_company_fields - Check Company fields",
        "check_customer_fields - Check Customer fields", 
        "check_sales_documents - Check sales document fields",
        "validate_system - Validate configuration",
        "reinstall_system - Reinstall/update fields",
        "create_test_data - Create test data",
        "uninstall_system - Remove all fields",
        "show_system_info - Show this information",
    ]
    
    for cmd in commands:
        print(f"   - {cmd}")
    
    print(f"\n📚 Usage Example:")
    print(f"   bench execute print_designer.commands.thailand_wht_system.install_complete_system")


def migrate_existing_installations():
    """
    Migrate existing installations to new field structure
    
    Command: bench execute print_designer.commands.thailand_wht_system.migrate_existing_installations
    """
    print("=" * 70)
    print("🔄 THAILAND WHT SYSTEM MIGRATION")
    print("=" * 70)
    
    return migrate_sales_invoice_wht_fields()


# Quick access aliases for common operations
def install():
    """Quick alias for install_complete_system"""
    return install_complete_system()


def check():
    """Quick alias for check_complete_system"""
    return check_complete_system()


def validate():
    """Quick alias for validate_system"""
    return validate_system()


if __name__ == "__main__":
    show_system_info()