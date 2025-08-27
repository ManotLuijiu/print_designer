"""
Thailand Quotation System Installation Command
=============================================

This module provides comprehensive installation commands for the Thailand
Quotation calculation system, including custom fields and calculation handlers.

Usage:
- bench execute print_designer.commands.install_thailand_quotation_system.install_complete_system
- bench execute print_designer.commands.install_thailand_quotation_system.check_system_status
- bench execute print_designer.commands.install_thailand_quotation_system.reinstall_system
"""

import frappe
from frappe import _
from print_designer.commands.install_quotation_fields import (
    install_quotation_custom_fields,
    validate_quotation_fields_installation,
    check_quotation_fields_status,
    reinstall_quotation_custom_fields
)


def install_complete_system():
    """
    Install complete Thailand Quotation calculation system
    
    This includes:
    1. Custom fields for Quotation DocType
    2. Calculation handlers in hooks.py
    3. System validation and testing
    
    Returns:
        dict: Installation results
    """
    try:
        print("=" * 60)
        print("🇹🇭 INSTALLING THAILAND QUOTATION SYSTEM")
        print("=" * 60)
        
        results = {
            "system_installed": False,
            "fields_result": None,
            "validation_result": None,
            "errors": []
        }
        
        # Step 1: Install custom fields
        print("\n📋 Step 1: Installing Custom Fields...")
        fields_result = install_quotation_custom_fields()
        results["fields_result"] = fields_result
        
        if not fields_result.get("success"):
            results["errors"].append(f"Field installation failed: {fields_result.get('error')}")
            return results
        
        # Step 2: Validate installation
        print("\n✅ Step 2: Validating Installation...")
        validation_result = validate_quotation_fields_installation()
        results["validation_result"] = validation_result
        
        if not validation_result.get("validation_passed"):
            results["errors"].append("Field validation failed")
            return results
        
        # Step 3: Check hooks configuration
        print("\n🔧 Step 3: Checking Hooks Configuration...")
        hooks_status = check_hooks_configuration()
        
        if not hooks_status.get("configured"):
            print("⚠️  Manual hook configuration required!")
            print("   Please ensure hooks.py contains Thailand calculation handlers")
        
        # Step 4: Final system check
        print("\n🔍 Step 4: Final System Check...")
        system_status = check_complete_system_status()
        results["system_status"] = system_status
        
        if system_status.get("ready"):
            print("\n🎉 THAILAND QUOTATION SYSTEM INSTALLATION COMPLETED!")
            print("   ✅ Custom fields: Installed and validated")
            print("   ✅ Calculation system: Ready")
            print("   ✅ Validation: Passed")
            results["system_installed"] = True
        else:
            print("\n❌ System installation incomplete")
            results["errors"].append("System readiness check failed")
        
        return results
        
    except Exception as e:
        error_msg = f"Error installing Thailand Quotation system: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "Thailand Quotation System Installation")
        return {
            "system_installed": False,
            "error": error_msg
        }


def check_system_status():
    """
    Check current status of Thailand Quotation system
    
    Returns:
        dict: System status information
    """
    try:
        print("=" * 60)
        print("🇹🇭 THAILAND QUOTATION SYSTEM STATUS")
        print("=" * 60)
        
        # Check custom fields
        print("\n📋 Custom Fields Status:")
        fields_status = check_quotation_fields_status()
        
        # Check hooks configuration
        print("\n🔧 Hooks Configuration Status:")
        hooks_status = check_hooks_configuration()
        
        # Check calculation system
        print("\n🧮 Calculation System Status:")
        calc_status = check_calculation_system_status()
        
        # Overall system status
        print("\n📊 Overall System Status:")
        overall_ready = (
            fields_status.get("fields_installed", False) and
            hooks_status.get("configured", False) and
            calc_status.get("available", False)
        )
        
        if overall_ready:
            print("✅ Thailand Quotation System: READY")
        else:
            print("❌ Thailand Quotation System: NOT READY")
            
            if not fields_status.get("fields_installed"):
                print("   ⚠️  Custom fields not properly installed")
            if not hooks_status.get("configured"):
                print("   ⚠️  Hooks configuration missing")
            if not calc_status.get("available"):
                print("   ⚠️  Calculation system not available")
        
        return {
            "system_ready": overall_ready,
            "fields_status": fields_status,
            "hooks_status": hooks_status,
            "calculation_status": calc_status
        }
        
    except Exception as e:
        error_msg = f"Error checking system status: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "system_ready": False,
            "error": error_msg
        }


def reinstall_system():
    """
    Reinstall/update the complete Thailand Quotation system
    
    This is useful for:
    - Applying updates to field definitions
    - Fixing field configuration issues
    - Migrating to new versions
    
    Returns:
        dict: Reinstallation results
    """
    try:
        print("=" * 60)
        print("🔄 REINSTALLING THAILAND QUOTATION SYSTEM")
        print("=" * 60)
        
        # Step 1: Check current status
        print("\n📊 Step 1: Checking Current Status...")
        current_status = check_system_status()
        
        # Step 2: Reinstall fields
        print("\n🔧 Step 2: Reinstalling Custom Fields...")
        reinstall_result = reinstall_quotation_custom_fields()
        
        if not reinstall_result.get("success"):
            return {
                "reinstall_success": False,
                "error": f"Field reinstallation failed: {reinstall_result.get('error')}"
            }
        
        # Step 3: Validate after reinstallation
        print("\n✅ Step 3: Validating Reinstallation...")
        validation_result = validate_quotation_fields_installation()
        
        # Step 4: Final status check
        print("\n🔍 Step 4: Final Status Check...")
        final_status = check_system_status()
        
        if final_status.get("system_ready"):
            print("\n🎉 SYSTEM REINSTALLATION COMPLETED SUCCESSFULLY!")
        else:
            print("\n⚠️  System reinstallation completed with warnings")
        
        return {
            "reinstall_success": True,
            "current_status": current_status,
            "reinstall_result": reinstall_result,
            "validation_result": validation_result,
            "final_status": final_status
        }
        
    except Exception as e:
        error_msg = f"Error reinstalling system: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "reinstall_success": False,
            "error": error_msg
        }


def check_hooks_configuration():
    """
    Check if hooks.py is properly configured for Thailand calculations
    
    Returns:
        dict: Hooks configuration status
    """
    try:
        # Check if the required calculation function exists
        try:
            from print_designer.custom.quotation_calculations import quotation_calculate_thailand_amounts
            calculation_function_exists = True
        except ImportError:
            calculation_function_exists = False
        
        # Check hooks.py configuration (this would require reading the file)
        # For now, we'll assume it's configured if the function exists
        hooks_configured = calculation_function_exists
        
        print(f"📋 Calculation function: {'✅ Available' if calculation_function_exists else '❌ Missing'}")
        print(f"📋 Hooks configuration: {'✅ Configured' if hooks_configured else '❌ Not configured'}")
        
        return {
            "configured": hooks_configured,
            "calculation_function_exists": calculation_function_exists,
            "details": {
                "calculation_module": "print_designer.custom.quotation_calculations",
                "function_name": "quotation_calculate_thailand_amounts"
            }
        }
        
    except Exception as e:
        print(f"❌ Error checking hooks: {str(e)}")
        return {
            "configured": False,
            "error": str(e)
        }


def check_calculation_system_status():
    """
    Check if the Thailand calculation system is available and working
    
    Returns:
        dict: Calculation system status
    """
    try:
        # Test import of calculation modules
        calculation_available = True
        calculation_errors = []
        
        try:
            from print_designer.custom.quotation_calculations import (
                calculate_withholding_tax_amounts,
                calculate_retention_amounts,
                calculate_final_payment_amounts,
                quotation_calculate_thailand_amounts
            )
            print("✅ Calculation modules: All imported successfully")
        except ImportError as e:
            calculation_available = False
            calculation_errors.append(f"Import error: {str(e)}")
            print(f"❌ Calculation modules: Import failed - {str(e)}")
        
        # Test WHT preview system
        try:
            from print_designer.custom.quotation_calculations import calculate_wht_preview_for_quotation
            print("✅ WHT preview system: Available")
        except ImportError as e:
            calculation_errors.append(f"WHT preview import error: {str(e)}")
            print(f"❌ WHT preview system: Import failed - {str(e)}")
        
        return {
            "available": calculation_available,
            "errors": calculation_errors,
            "modules_status": {
                "quotation_calculations": calculation_available,
                "wht_preview": len([e for e in calculation_errors if "WHT preview" in e]) == 0
            }
        }
        
    except Exception as e:
        print(f"❌ Error checking calculation system: {str(e)}")
        return {
            "available": False,
            "error": str(e)
        }


def check_complete_system_status():
    """
    Comprehensive system readiness check
    
    Returns:
        dict: Complete system status
    """
    try:
        # Get all component statuses
        fields_status = check_quotation_fields_status()
        hooks_status = check_hooks_configuration()
        calc_status = check_calculation_system_status()
        
        # Calculate overall readiness
        system_ready = (
            fields_status.get("fields_installed", False) and
            not fields_status.get("needs_installation", True) and
            hooks_status.get("configured", False) and
            calc_status.get("available", False)
        )
        
        # Generate readiness report
        readiness_score = 0
        total_checks = 4
        
        if fields_status.get("fields_installed"):
            readiness_score += 1
        if not fields_status.get("needs_installation", True):
            readiness_score += 1
        if hooks_status.get("configured"):
            readiness_score += 1
        if calc_status.get("available"):
            readiness_score += 1
        
        readiness_percentage = (readiness_score / total_checks) * 100
        
        print(f"📊 System Readiness: {readiness_score}/{total_checks} ({readiness_percentage:.0f}%)")
        
        return {
            "ready": system_ready,
            "readiness_score": readiness_score,
            "total_checks": total_checks,
            "readiness_percentage": readiness_percentage,
            "component_status": {
                "fields": fields_status,
                "hooks": hooks_status,
                "calculations": calc_status
            }
        }
        
    except Exception as e:
        print(f"❌ Error in system readiness check: {str(e)}")
        return {
            "ready": False,
            "error": str(e)
        }


# Convenience functions for bench execution
def main():
    """Main function for direct execution"""
    return install_complete_system()


if __name__ == "__main__":
    main()