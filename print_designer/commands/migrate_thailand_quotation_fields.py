"""
Thailand Quotation Fields Migration Command
==========================================

This module handles migration from the current organic field structure
to the new organized programmatic field structure while preserving
all existing functionality and data.

Usage:
- bench execute print_designer.commands.migrate_thailand_quotation_fields.migrate_to_organized_structure
- bench execute print_designer.commands.migrate_thailand_quotation_fields.check_migration_status
"""

import frappe
from frappe import _
from print_designer.commands.install_quotation_fields import (
    get_quotation_custom_fields_definition,
    validate_quotation_fields_installation
)


def migrate_to_organized_structure():
    """
    Migrate current Quotation custom fields to the new organized structure
    
    This migration:
    1. Preserves all existing field data
    2. Reorganizes fields into logical sections
    3. Updates field properties to match new definition
    4. Maintains backward compatibility
    
    Returns:
        dict: Migration results
    """
    try:
        print("=" * 70)
        print("🔄 MIGRATING THAILAND QUOTATION FIELDS TO ORGANIZED STRUCTURE")
        print("=" * 70)
        
        # Step 1: Pre-migration analysis
        print("\n📊 Step 1: Pre-Migration Analysis...")
        current_status = analyze_current_field_structure()
        
        if not current_status["has_fields"]:
            print("❌ No existing fields found. Use fresh installation instead.")
            return {"migration_success": False, "error": "No fields to migrate"}
        
        # Step 2: Create backup info
        print("\n💾 Step 2: Creating Migration Backup Info...")
        backup_info = create_field_backup_info()
        
        # Step 3: Install new organized structure
        print("\n🏗️  Step 3: Installing New Organized Structure...")
        from print_designer.commands.install_quotation_fields import install_quotation_custom_fields
        install_result = install_quotation_custom_fields()
        
        if not install_result.get("success"):
            print(f"❌ Installation failed: {install_result.get('error')}")
            return {
                "migration_success": False,
                "error": f"New structure installation failed: {install_result.get('error')}",
                "backup_info": backup_info
            }
        
        # Step 4: Validate new structure
        print("\n✅ Step 4: Validating New Structure...")
        validation_result = validate_quotation_fields_installation()
        
        # Step 5: Post-migration verification
        print("\n🔍 Step 5: Post-Migration Verification...")
        post_migration_status = check_migration_completeness()
        
        success = (
            install_result.get("success", False) and
            post_migration_status.get("structure_valid", False)
        )
        
        if success:
            print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("   ✅ Fields reorganized into logical sections")
            print("   ✅ Field properties updated")
            print("   ✅ Structure validated")
            print("   ✅ Ready for production use")
        else:
            print("\n⚠️  Migration completed with warnings")
        
        return {
            "migration_success": success,
            "current_status": current_status,
            "install_result": install_result,
            "validation_result": validation_result,
            "post_migration_status": post_migration_status,
            "backup_info": backup_info
        }
        
    except Exception as e:
        error_msg = f"Error during migration: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "Thailand Quotation Fields Migration")
        return {
            "migration_success": False,
            "error": error_msg
        }


def check_migration_status():
    """
    Check if migration from old structure to new structure is needed
    
    Returns:
        dict: Migration status analysis
    """
    try:
        print("=" * 60)
        print("🔍 THAILAND QUOTATION FIELDS MIGRATION STATUS")
        print("=" * 60)
        
        # Current field analysis
        current_analysis = analyze_current_field_structure()
        
        # Expected structure validation
        validation_result = validate_quotation_fields_installation()
        
        # Determine migration need
        needs_migration = not validation_result.get("validation_passed", False)
        
        print(f"\n📊 Migration Analysis:")
        print(f"   Current fields: {current_analysis['field_count']}")
        print(f"   Structure organized: {'Yes' if validation_result.get('validation_passed') else 'No'}")
        print(f"   Migration needed: {'Yes' if needs_migration else 'No'}")
        
        if needs_migration:
            print(f"\n📋 Migration Requirements:")
            missing_count = len(validation_result.get("missing_fields", []))
            mismatch_count = len(validation_result.get("field_mismatches", []))
            print(f"   Missing organized fields: {missing_count}")
            print(f"   Field property mismatches: {mismatch_count}")
            
            print(f"\n💡 Recommendation:")
            print(f"   Run migration to organize fields into logical sections")
            print(f"   Command: bench execute print_designer.commands.migrate_thailand_quotation_fields.migrate_to_organized_structure")
        else:
            print(f"\n✅ Fields are already organized - no migration needed")
        
        return {
            "needs_migration": needs_migration,
            "current_analysis": current_analysis,
            "validation_result": validation_result,
            "migration_benefits": get_migration_benefits() if needs_migration else None
        }
        
    except Exception as e:
        error_msg = f"Error checking migration status: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "needs_migration": None,
            "error": error_msg
        }


def analyze_current_field_structure():
    """
    Analyze the current field structure to understand organization
    
    Returns:
        dict: Current structure analysis
    """
    try:
        # Get current fields
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Quotation"},
            fields=["fieldname", "fieldtype", "label", "insert_after", "depends_on"],
            order_by="idx asc, modified asc"
        )
        
        # Analyze field organization
        section_breaks = [f for f in current_fields if f['fieldtype'] == 'Section Break']
        column_breaks = [f for f in current_fields if f['fieldtype'] == 'Column Break']
        data_fields = [f for f in current_fields if f['fieldtype'] not in ['Section Break', 'Column Break']]
        
        # Check for organized sections
        organized_sections = [
            'thailand_business_section',
            'retention_section',
            'withholding_tax_section',
            'final_amounts_section'
        ]
        
        has_organized_sections = any(
            field['fieldname'] in organized_sections 
            for field in section_breaks
        )
        
        print(f"📊 Current Structure Analysis:")
        print(f"   Total fields: {len(current_fields)}")
        print(f"   Section breaks: {len(section_breaks)}")
        print(f"   Column breaks: {len(column_breaks)}")
        print(f"   Data fields: {len(data_fields)}")
        print(f"   Organized structure: {'Yes' if has_organized_sections else 'No'}")
        
        return {
            "has_fields": len(current_fields) > 0,
            "field_count": len(current_fields),
            "section_breaks": len(section_breaks),
            "column_breaks": len(column_breaks),
            "data_fields": len(data_fields),
            "has_organized_sections": has_organized_sections,
            "current_sections": [f['fieldname'] for f in section_breaks]
        }
        
    except Exception as e:
        print(f"❌ Error analyzing current structure: {str(e)}")
        return {
            "has_fields": False,
            "error": str(e)
        }


def create_field_backup_info():
    """
    Create backup information about current field structure
    
    Returns:
        dict: Backup information for rollback if needed
    """
    try:
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Quotation"},
            fields=["fieldname", "fieldtype", "label", "insert_after", "depends_on", 
                   "default", "options", "precision", "read_only", "mandatory_depends_on"],
            order_by="idx asc, modified asc"
        )
        
        backup_info = {
            "backup_timestamp": frappe.utils.now(),
            "field_count": len(current_fields),
            "field_details": current_fields
        }
        
        print(f"💾 Backup Info Created:")
        print(f"   Fields backed up: {len(current_fields)}")
        print(f"   Timestamp: {backup_info['backup_timestamp']}")
        
        return backup_info
        
    except Exception as e:
        print(f"❌ Error creating backup info: {str(e)}")
        return {
            "error": str(e)
        }


def check_migration_completeness():
    """
    Verify that migration completed successfully
    
    Returns:
        dict: Migration completeness check
    """
    try:
        # Validate new structure
        validation_result = validate_quotation_fields_installation()
        structure_valid = validation_result.get("validation_passed", False)
        
        # Check for expected organized sections
        expected_sections = [
            'thailand_business_section',
            'retention_section', 
            'withholding_tax_section',
            'final_amounts_section'
        ]
        
        current_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Quotation", "fieldtype": "Section Break"},
            fields=["fieldname"],
            order_by="idx asc"
        )
        
        current_section_names = [f['fieldname'] for f in current_fields]
        sections_present = sum(1 for section in expected_sections if section in current_section_names)
        
        print(f"🔍 Migration Completeness Check:")
        print(f"   Structure validation: {'✅ Passed' if structure_valid else '❌ Failed'}")
        print(f"   Organized sections: {sections_present}/{len(expected_sections)}")
        
        return {
            "structure_valid": structure_valid,
            "sections_present": sections_present,
            "expected_sections": len(expected_sections),
            "sections_complete": sections_present == len(expected_sections),
            "validation_details": validation_result
        }
        
    except Exception as e:
        print(f"❌ Error checking migration completeness: {str(e)}")
        return {
            "structure_valid": False,
            "error": str(e)
        }


def get_migration_benefits():
    """
    Get list of benefits from migrating to organized structure
    
    Returns:
        list: Migration benefits
    """
    return [
        "Logical field grouping (Thailand Business, Retention, WHT, Final Amounts)",
        "Improved form UI organization and user experience", 
        "Better field dependencies and conditional display",
        "Standardized field naming and labeling",
        "Enhanced maintainability for future development",
        "Production-ready programmatic installation system",
        "Proper field ordering and section structure",
        "Better integration with calculation system"
    ]


# Convenience functions
def main():
    """Main function for direct execution"""
    return check_migration_status()


if __name__ == "__main__":
    main()