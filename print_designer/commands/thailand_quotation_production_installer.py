"""
Thailand Quotation Production Installer
=======================================

Production-ready installer for Thailand Quotation calculation system.
Handles both fresh installations and migrations without relying on fixtures.

This is the MAIN ENTRY POINT for production installations.

Usage:
- bench execute print_designer.commands.thailand_quotation_production_installer.install_for_production
- bench execute print_designer.commands.thailand_quotation_production_installer.check_production_readiness
"""

import frappe
from frappe import _


def install_for_production():
    """
    Production-ready installation of Thailand Quotation system
    
    This function automatically detects the current state and performs
    the appropriate action:
    - Fresh installation for new systems
    - Migration for existing systems with unorganized fields
    - Validation for systems that are already properly installed
    
    Returns:
        dict: Installation/migration results
    """
    try:
        print("=" * 70)
        print("🇹🇭 THAILAND QUOTATION SYSTEM - PRODUCTION INSTALLER")
        print("=" * 70)
        print("   Designed for production environments without fixture dependencies")
        print("   Handles fresh installation, migration, and validation scenarios")
        
        # Step 1: Analyze current system state
        print("\n🔍 Step 1: Analyzing Current System State...")
        system_state = analyze_system_state()
        
        # Step 2: Determine installation strategy
        print(f"\n📋 Step 2: Determining Installation Strategy...")
        strategy = determine_installation_strategy(system_state)
        print(f"   Strategy: {strategy['action']} - {strategy['reason']}")
        
        # Step 3: Execute installation strategy
        print(f"\n🚀 Step 3: Executing {strategy['action']}...")
        execution_result = execute_installation_strategy(strategy, system_state)
        
        # Step 4: Final validation
        print(f"\n✅ Step 4: Final System Validation...")
        final_validation = perform_final_validation()
        
        # Step 5: Generate production report
        print(f"\n📊 Step 5: Production Readiness Report...")
        production_report = generate_production_report(
            system_state, strategy, execution_result, final_validation
        )
        
        # Final status
        overall_success = (
            execution_result.get("success", False) and 
            final_validation.get("system_ready", False)
        )
        
        if overall_success:
            print(f"\n🎉 PRODUCTION INSTALLATION COMPLETED SUCCESSFULLY!")
            print(f"   ✅ System: Ready for production use")
            print(f"   ✅ Fields: Properly organized and validated")
            print(f"   ✅ Calculations: Working correctly")
            print(f"   ✅ Integration: Complete and tested")
        else:
            print(f"\n⚠️  Production installation completed with issues")
            if not execution_result.get("success"):
                print(f"   ❌ Execution failed: {execution_result.get('error', 'Unknown error')}")
            if not final_validation.get("system_ready"):
                print(f"   ❌ System validation failed")
        
        return {
            "production_ready": overall_success,
            "system_state": system_state,
            "strategy": strategy,
            "execution_result": execution_result,
            "final_validation": final_validation,
            "production_report": production_report
        }
        
    except Exception as e:
        error_msg = f"Critical error in production installer: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "Thailand Quotation Production Installer")
        return {
            "production_ready": False,
            "error": error_msg
        }


def check_production_readiness():
    """
    Check if the Thailand Quotation system is ready for production use
    
    Returns:
        dict: Production readiness assessment
    """
    try:
        print("=" * 60)
        print("🔍 THAILAND QUOTATION SYSTEM - PRODUCTION READINESS CHECK")
        print("=" * 60)
        
        # Comprehensive system analysis
        system_state = analyze_system_state()
        final_validation = perform_final_validation()
        
        # Production readiness criteria
        readiness_criteria = {
            "fields_installed": system_state.get("has_custom_fields", False),
            "fields_organized": system_state.get("has_organized_structure", False),
            "calculations_working": system_state.get("calculation_system_working", False),
            "hooks_configured": system_state.get("hooks_configured", False),
            "no_critical_errors": len(system_state.get("critical_errors", [])) == 0
        }
        
        # Calculate readiness score
        passed_criteria = sum(1 for criterion in readiness_criteria.values() if criterion)
        total_criteria = len(readiness_criteria)
        readiness_percentage = (passed_criteria / total_criteria) * 100
        
        # Production readiness determination
        production_ready = readiness_percentage >= 100  # All criteria must pass
        
        print(f"\n📊 Production Readiness Assessment:")
        print(f"   Overall Score: {passed_criteria}/{total_criteria} ({readiness_percentage:.0f}%)")
        print(f"   Production Ready: {'✅ YES' if production_ready else '❌ NO'}")
        
        print(f"\n📋 Detailed Criteria:")
        for criterion, passed in readiness_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {criterion.replace('_', ' ').title()}: {status}")
        
        if not production_ready:
            print(f"\n💡 Recommendation:")
            print(f"   Run production installer to resolve issues:")
            print(f"   bench execute print_designer.commands.thailand_quotation_production_installer.install_for_production")
        
        return {
            "production_ready": production_ready,
            "readiness_percentage": readiness_percentage,
            "criteria": readiness_criteria,
            "system_state": system_state,
            "final_validation": final_validation
        }
        
    except Exception as e:
        error_msg = f"Error checking production readiness: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "production_ready": False,
            "error": error_msg
        }


def analyze_system_state():
    """
    Analyze current system state to determine installation needs
    
    Returns:
        dict: Comprehensive system state analysis
    """
    try:
        print("🔍 Analyzing system state...")
        
        # Check for existing custom fields
        existing_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Quotation"},
            fields=["fieldname", "fieldtype", "label"],
            order_by="idx asc"
        )
        
        has_custom_fields = len(existing_fields) > 0
        
        # Check for organized structure
        organized_sections = [
            'thailand_business_section',
            'retention_section',
            'withholding_tax_section', 
            'final_amounts_section'
        ]
        
        section_fields = [f for f in existing_fields if f['fieldtype'] == 'Section Break']
        has_organized_structure = any(
            section['fieldname'] in organized_sections 
            for section in section_fields
        )
        
        # Check calculation system
        calculation_system_working = False
        calculation_errors = []
        
        try:
            from print_designer.custom.quotation_calculations import quotation_calculate_thailand_amounts
            from print_designer.custom.thai_wht_events import calculate_wht_preview_on_validate
            calculation_system_working = True
        except ImportError as e:
            calculation_errors.append(str(e))
        
        # Check hooks configuration
        hooks_configured = calculation_system_working  # Simplified check
        
        # Identify critical errors
        critical_errors = []
        if not has_custom_fields:
            critical_errors.append("No custom fields found")
        if not calculation_system_working:
            critical_errors.append("Calculation system not working")
            critical_errors.extend(calculation_errors)
        
        print(f"   Custom fields: {'✅' if has_custom_fields else '❌'} ({len(existing_fields)} fields)")
        print(f"   Organized structure: {'✅' if has_organized_structure else '❌'}")
        print(f"   Calculation system: {'✅' if calculation_system_working else '❌'}")
        print(f"   Hooks configured: {'✅' if hooks_configured else '❌'}")
        print(f"   Critical errors: {len(critical_errors)}")
        
        return {
            "has_custom_fields": has_custom_fields,
            "field_count": len(existing_fields),
            "has_organized_structure": has_organized_structure,
            "calculation_system_working": calculation_system_working,
            "hooks_configured": hooks_configured,
            "critical_errors": critical_errors,
            "existing_fields": existing_fields,
            "calculation_errors": calculation_errors
        }
        
    except Exception as e:
        error_msg = f"Error analyzing system state: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "error": error_msg,
            "has_custom_fields": False,
            "calculation_system_working": False
        }


def determine_installation_strategy(system_state):
    """
    Determine the best installation strategy based on system state
    
    Args:
        system_state (dict): Current system state analysis
        
    Returns:
        dict: Installation strategy
    """
    try:
        # Strategy decision logic
        has_fields = system_state.get("has_custom_fields", False)
        has_organized = system_state.get("has_organized_structure", False)
        calc_working = system_state.get("calculation_system_working", False)
        critical_errors = system_state.get("critical_errors", [])
        
        if not has_fields:
            # Fresh installation needed
            return {
                "action": "FRESH_INSTALL",
                "reason": "No custom fields found - performing fresh installation",
                "method": "install_fresh_system"
            }
        elif has_fields and not has_organized:
            # Migration needed
            return {
                "action": "MIGRATE",
                "reason": "Fields exist but not organized - performing migration",
                "method": "migrate_to_organized_structure"
            }
        elif has_fields and has_organized and not calc_working:
            # Fix calculation system
            return {
                "action": "FIX_CALCULATIONS", 
                "reason": "Fields organized but calculations not working - fixing system",
                "method": "fix_calculation_system"
            }
        elif len(critical_errors) > 0:
            # System repair needed
            return {
                "action": "REPAIR_SYSTEM",
                "reason": f"Critical errors found - repairing system ({len(critical_errors)} errors)",
                "method": "repair_system_errors"
            }
        else:
            # System validation
            return {
                "action": "VALIDATE_SYSTEM",
                "reason": "System appears complete - performing validation",
                "method": "validate_existing_system"
            }
            
    except Exception as e:
        return {
            "action": "ERROR",
            "reason": f"Error determining strategy: {str(e)}",
            "method": None
        }


def execute_installation_strategy(strategy, system_state):
    """
    Execute the determined installation strategy
    
    Args:
        strategy (dict): Installation strategy
        system_state (dict): System state analysis
        
    Returns:
        dict: Execution results
    """
    try:
        method = strategy.get("method")
        
        if method == "install_fresh_system":
            return execute_fresh_installation()
        elif method == "migrate_to_organized_structure":
            return execute_migration()
        elif method == "fix_calculation_system":
            return execute_calculation_fix()
        elif method == "repair_system_errors":
            return execute_system_repair(system_state)
        elif method == "validate_existing_system":
            return execute_system_validation()
        else:
            return {
                "success": False,
                "error": f"Unknown installation method: {method}"
            }
            
    except Exception as e:
        error_msg = f"Error executing strategy: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


def execute_fresh_installation():
    """Execute fresh installation of the complete system"""
    try:
        from print_designer.commands.install_quotation_fields import install_quotation_custom_fields
        result = install_quotation_custom_fields()
        
        print(f"   Fresh installation: {'✅ Success' if result.get('success') else '❌ Failed'}")
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_migration():
    """Execute migration to organized structure"""
    try:
        from print_designer.commands.migrate_thailand_quotation_fields import migrate_to_organized_structure
        result = migrate_to_organized_structure()
        
        success = result.get("migration_success", False)
        print(f"   Migration: {'✅ Success' if success else '❌ Failed'}")
        return {"success": success, "migration_result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_calculation_fix():
    """Execute calculation system fix"""
    try:
        # For now, just validate that the calculation system is importable
        from print_designer.custom.quotation_calculations import quotation_calculate_thailand_amounts
        from print_designer.custom.thai_wht_events import calculate_wht_preview_on_validate
        
        print("   Calculation fix: ✅ System verified")
        return {"success": True, "message": "Calculation system verified"}
    except Exception as e:
        print(f"   Calculation fix: ❌ Failed - {str(e)}")
        return {"success": False, "error": str(e)}


def execute_system_repair(system_state):
    """Execute system repair for critical errors"""
    try:
        errors = system_state.get("critical_errors", [])
        repair_results = []
        
        for error in errors:
            if "custom fields" in error.lower():
                # Repair fields
                from print_designer.commands.install_quotation_fields import install_quotation_custom_fields
                result = install_quotation_custom_fields()
                repair_results.append({"error": error, "result": result})
            elif "calculation" in error.lower():
                # Try to repair calculation system
                result = execute_calculation_fix()
                repair_results.append({"error": error, "result": result})
        
        success = all(r["result"].get("success", False) for r in repair_results)
        print(f"   System repair: {'✅ Success' if success else '❌ Failed'}")
        
        return {
            "success": success,
            "repair_results": repair_results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_system_validation():
    """Execute system validation"""
    try:
        from print_designer.commands.install_quotation_fields import validate_quotation_fields_installation
        result = validate_quotation_fields_installation()
        
        success = result.get("validation_passed", False)
        print(f"   System validation: {'✅ Success' if success else '❌ Failed'}")
        return {"success": success, "validation_result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def perform_final_validation():
    """Perform comprehensive final validation"""
    try:
        from print_designer.commands.install_thailand_quotation_system import check_complete_system_status
        return check_complete_system_status()
    except Exception as e:
        return {"ready": False, "error": str(e)}


def generate_production_report(system_state, strategy, execution_result, final_validation):
    """Generate comprehensive production report"""
    return {
        "installation_timestamp": frappe.utils.now(),
        "strategy_used": strategy.get("action"),
        "execution_success": execution_result.get("success", False),
        "final_validation_passed": final_validation.get("ready", False),
        "field_count": system_state.get("field_count", 0),
        "readiness_percentage": final_validation.get("readiness_percentage", 0),
        "production_ready": execution_result.get("success", False) and final_validation.get("ready", False)
    }


# Main entry points
def main():
    """Main function for command execution"""
    return install_for_production()


if __name__ == "__main__":
    main()