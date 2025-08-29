#!/usr/bin/env python3
import frappe

def check_migration_status():
    """Check if the migration completed successfully"""
    
    print("🔍 Checking migration status...")
    
    # Check if the patch was applied
    patch_log = frappe.get_value("Patch Log", {
        "patch": "print_designer.patches.v1_2.force_install_construction_service_field"
    })
    
    if patch_log:
        print("✅ Construction service field patch was applied")
    else:
        print("❌ Construction service field patch was NOT applied")
        return False
    
    # Check if the fields were actually created
    construction_fields = []
    expected_fields = ['construction_service', 'default_retention_rate', 'default_retention_account']
    
    for field_name in expected_fields:
        field = frappe.get_value("Custom Field", {
            "dt": "Company",
            "fieldname": field_name
        })
        if field:
            construction_fields.append(field_name)
    
    print(f"\n📋 Construction service fields status:")
    for field_name in expected_fields:
        status = "✅ Installed" if field_name in construction_fields else "❌ Missing"
        print(f"   - {field_name}: {status}")
    
    # Check overall status
    if len(construction_fields) == len(expected_fields):
        print(f"\n✅ Migration completed successfully! All {len(expected_fields)} fields installed.")
        return True
    else:
        print(f"\n❌ Migration incomplete: {len(construction_fields)}/{len(expected_fields)} fields installed.")
        return False