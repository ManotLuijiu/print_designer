#!/usr/bin/env python3
"""
Setup Designation Signature Sync System
This script sets up comprehensive signature management across Employee, User, and Designation DocTypes
"""


def setup_designation_signatures():
    """Main setup function for designation signature system"""
    print("🎯 SETTING UP DESIGNATION SIGNATURE SYNC SYSTEM")
    print("=" * 60)
    
    setup_results = {
        "steps_completed": [],
        "errors": [],
        "success": True
    }
    
    # Step 1: Install Designation signature fields
    print("\n1. INSTALLING DESIGNATION SIGNATURE FIELDS")
    try:
        from print_designer.api.signature_field_installer import (
            install_signature_fields_for_doctype,
        )
        result = install_signature_fields_for_doctype("Designation")
        
        if result.get("success"):
            print(f"   ✅ Installed {result['fields_installed']} designation signature fields")
            setup_results["steps_completed"].append("Designation fields installed")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
            setup_results["errors"].append(f"Designation field installation: {result.get('error')}")
    except Exception as e:
        error_msg = f"Error installing designation fields: {str(e)}"
        print(f"   ❌ {error_msg}")
        setup_results["errors"].append(error_msg)
    
    # Step 2: Run initial signature sync
    print("\n2. RUNNING INITIAL SIGNATURE SYNC")
    try:
        from print_designer.api.designation_signature_sync import sync_designation_signatures
        sync_result = sync_designation_signatures()
        
        if sync_result.get("success"):
            print("   ✅ Synced signatures:")
            print(f"      📋 Designations updated: {sync_result['designations_updated']}")
            print(f"      👥 Employees synced: {sync_result['employees_synced']}")
            print(f"      👤 Users synced: {sync_result['users_synced']}")
            setup_results["steps_completed"].append("Initial signature sync completed")
        else:
            print(f"   ❌ Sync failed: {sync_result.get('error')}")
            setup_results["errors"].append(f"Signature sync: {sync_result.get('error')}")
    except Exception as e:
        error_msg = f"Error during signature sync: {str(e)}"
        print(f"   ❌ {error_msg}")
        setup_results["errors"].append(error_msg)
    
    # Step 3: Generate signature coverage report
    print("\n3. GENERATING SIGNATURE COVERAGE REPORT")
    try:
        from print_designer.api.designation_signature_sync import get_designation_signature_report
        report = get_designation_signature_report()
        
        if not report.get("error"):
            print("   📊 COVERAGE SUMMARY:")
            print(f"      🏢 Total Designations: {report['summary']['total_designations']}")
            print(f"      ✅ With Signatures: {report['summary']['designations_with_signatures']}")
            print(f"      👥 Total Employees: {report['summary']['total_employees']}")
            print(f"      🖋️  Employees with Signatures: {report['summary']['employees_with_signatures']}")
            print(f"      📈 Overall Coverage: {report['summary']['coverage_percentage']}%")
            
            if report.get("missing_signatures"):
                print(f"\n   ⚠️  MISSING SIGNATURES ({len(report['missing_signatures'])}):")
                for missing in report["missing_signatures"][:5]:  # Show top 5
                    print(f"      • {missing['designation']}: {missing['employee_count']} employees")
            
            setup_results["steps_completed"].append("Coverage report generated")
        else:
            print(f"   ❌ Report generation failed: {report.get('error')}")
    except Exception as e:
        print(f"   ❌ Error generating report: {str(e)}")
    
    # Step 4: Setup instructions
    print("\n4. SETUP COMPLETE - NEXT STEPS")
    print("   📝 Manual Steps Required:")
    print("   1. Go to Designation DocType (e.g., http://your-site.com/app/designation)")
    print("   2. Open each designation (Consultant, Manager, etc.)")
    print("   3. Upload signature images to 'Designation Signature' field")
    print("   4. Set 'Signature Authority Level' (Low/Medium/High/Executive)")
    print("   5. Set 'Maximum Approval Amount' if needed")
    print("")
    print("   🔄 Automatic Sync:")
    print("   - Signatures will auto-sync between Employee, User, and Designation")
    print("   - Priority: Employee > User > Designation")
    print("   - Run sync manually: bench execute print_designer.api.designation_signature_sync.sync_designation_signatures")
    
    return setup_results

def demonstrate_usage():
    """Show usage examples for the designation signature system"""
    print("\n🚀 USAGE EXAMPLES")
    print("=" * 30)
    
    examples = """
# 1. Setup designation signatures (run once)
bench --site your-site execute print_designer.api.designation_signature_sync.setup_designation_signature_sync

# 2. Sync signatures between Employee, User, and Designation
frappe.call({
    method: 'print_designer.api.designation_signature_sync.sync_designation_signatures',
    callback: (r) => console.log(r.message)
});

# 3. Get signature hierarchy for an employee
frappe.call({
    method: 'print_designer.api.designation_signature_sync.get_signature_hierarchy',
    args: { employee_name: 'EMP-001' },
    callback: (r) => console.log('Available signatures:', r.message)
});

# 4. Generate signature coverage report
frappe.call({
    method: 'print_designer.api.designation_signature_sync.get_designation_signature_report',
    callback: (r) => console.log('Coverage report:', r.message)
});

# 5. Bulk update designation signatures
frappe.call({
    method: 'print_designer.api.designation_signature_sync.bulk_update_designation_signatures',
    args: {
        designation_mappings: JSON.stringify([
            {
                designation: 'Consultant',
                signature_url: '/files/consultant_signature.png',
                authority_level: 'Medium',
                max_approval_amount: 50000
            },
            {
                designation: 'Manager', 
                signature_url: '/files/manager_signature.png',
                authority_level: 'High',
                max_approval_amount: 200000
            }
        ])
    },
    callback: (r) => console.log('Bulk update result:', r.message)
});
"""
    print(examples)

def main():
    """Main execution function"""
    print("🎨 PRINT DESIGNER - DESIGNATION SIGNATURE SETUP")
    print("=" * 50)
    print("This script sets up signature syncing between Designation, Employee, and User DocTypes")
    print("It enables role-based signature management for your organization")
    
    # Run setup
    results = setup_designation_signatures()
    
    # Show results summary
    print("\n📋 SETUP SUMMARY")
    print("=" * 25)
    
    if results["steps_completed"]:
        print("✅ COMPLETED STEPS:")
        for step in results["steps_completed"]:
            print(f"   • {step}")
    
    if results["errors"]:
        print("\n❌ ERRORS ENCOUNTERED:")
        for error in results["errors"]:
            print(f"   • {error}")
    
    # Show usage examples
    demonstrate_usage()
    
    print("\n🎯 QUICK START:")
    print("1. Go to http://[site]:8000/app/designation/Consultant")
    print("2. Upload signature image to 'Designation Signature' field")
    print("3. Set authority level and approval limits")
    print("4. Repeat for other designations")
    print("5. Run sync to propagate signatures to employees and users")

if __name__ == "__main__":
    main()