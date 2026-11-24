#!/usr/bin/env python3
"""Set up the signature of the designations of a site.

The script installs the signature fields of the designations, syncs the
signatures of the designations to the employees and the users, and prints the
coverage of the signatures.

The script writes to the site, so it needs a site and it needs the consent of
the caller: without `--apply` it only prints what it would do.

    python harness/test/setup_designation_signatures.py --site your_site
    python harness/test/setup_designation_signatures.py --site your_site --apply
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, cast

THE_BENCH = Path(__file__).resolve().parents[3]


def the_parser() -> argparse.ArgumentParser:
    """The arguments of the setup."""
    the_parser = argparse.ArgumentParser(description=__doc__)
    the_parser.add_argument(
        "--site",
        default=os.environ.get("FRAPPE_SITE"),
        help="the site of the setup",
    )
    the_parser.add_argument(
        "--apply",
        action="store_true",
        help="write to the site, without this flag the setup only prints its plan",
    )

    return the_parser


def setup_designation_signatures(the_apply: bool = False) -> dict[str, Any]:
    """Main setup function for designation signature system.

    Args:
        the_apply: whether the setup writes to the site. Without it the setup
            only reports what it would do.
    """
    print("🎯 SETTING UP DESIGNATION SIGNATURE SYNC SYSTEM")
    print("=" * 60)

    setup_results: dict[str, Any] = {
        "steps_completed": [],
        "errors": [],
        "success": True,
    }

    # Step 1: Install Designation signature fields
    print("\n1. INSTALLING DESIGNATION SIGNATURE FIELDS")
    if not the_apply:
        print("   ⏭️  the fields are not installed, the setup only reads")
    else:
        try:
            from print_designer.commands.install_signature_fields import (
                create_signature_fields,
            )

            if create_signature_fields():
                print("   ✅ Installed the designation signature fields")
                setup_results["steps_completed"].append("Designation fields installed")
            else:
                print("   ❌ Failed: the signature fields were not installed")
                setup_results["errors"].append("Designation field installation failed")
        except Exception as e:
            error_msg = f"Error installing designation fields: {str(e)}"
            print(f"   ❌ {error_msg}")
            setup_results["errors"].append(error_msg)

    # Step 2: Run initial signature sync
    print("\n2. RUNNING INITIAL SIGNATURE SYNC")
    if not the_apply:
        print("   ⏭️  the signatures are not synced, the setup only reads")
    else:
        try:
            from print_designer.api.designation_signature_sync import (
                sync_designation_signatures,
            )

            sync_result = cast(dict[str, Any], sync_designation_signatures())

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
        from print_designer.api.designation_signature_sync import (
            get_designation_signature_report,
        )

        report = cast(dict[str, Any], get_designation_signature_report())

        if not report.get("error"):
            print("   📊 COVERAGE SUMMARY:")
            summary = cast(dict[str, Any], report["summary"])
            print(f"      🏢 Total Designations: {summary['total_designations']}")
            print(f"      ✅ With Signatures: {summary['designations_with_signatures']}")
            print(f"      👥 Total Employees: {summary['total_employees']}")
            print(f"      🖋️  Employees with Signatures: {summary['employees_with_signatures']}")
            print(f"      📈 Overall Coverage: {summary['coverage_percentage']}%")

            if report.get("missing_signatures"):
                print(f"\n   ⚠️  MISSING SIGNATURES ({len(report['missing_signatures'])}):")
                for missing in cast(list[dict[str, Any]], report["missing_signatures"])[:5]:
                    print(
                        f"      • {missing['designation']}: {missing['employee_count']} employees"
                    )

            setup_results["steps_completed"].append("Coverage report generated")
        else:
            print(f"   ❌ Report generation failed: {report.get('error')}")
    except Exception as e:
        print(f"   ❌ Error generating report: {str(e)}")

    # Step 4: Setup instructions
    print("\n4. SETUP COMPLETE - NEXT STEPS")
    print("   📝 Manual Steps Required:")
    print("   1. Go to the Designation DocType of your site")
    print("   2. Open each designation (Consultant, Manager, etc.)")
    print("   3. Upload signature images to 'Designation Signature' field")
    print("   4. Set 'Signature Authority Level' (Low/Medium/High/Executive)")
    print("   5. Set 'Maximum Approval Amount' if needed")
    print("")
    print("   🔄 Automatic Sync:")
    print("   - Signatures will auto-sync between Employee, User, and Designation")
    print("   - Priority: Employee > User > Designation")
    print(
        "   - Run sync manually: bench execute "
        "print_designer.api.designation_signature_sync.sync_designation_signatures"
    )

    setup_results["success"] = not setup_results["errors"]

    return setup_results


def demonstrate_usage() -> None:
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


def main() -> int:
    """Main execution function"""
    the_arguments = the_parser().parse_args()
    if not the_arguments.site:
        print("the site of the setup is not known")
        print("use --site or set FRAPPE_SITE")
        return 1

    sys.path.insert(0, str(THE_BENCH / "apps" / "frappe"))
    sys.path.insert(0, str(THE_BENCH / "apps" / "print_designer"))

    import frappe

    frappe.init(the_arguments.site)
    frappe.connect()

    print("🎨 PRINT DESIGNER - DESIGNATION SIGNATURE SETUP")
    print("=" * 50)
    print("This script sets up signature syncing between Designation, Employee, and User DocTypes")
    print("It enables role-based signature management for your organization")
    if not the_arguments.apply:
        print("the setup only reads the site, use --apply to write to it")

    # Run setup
    results = setup_designation_signatures(the_apply=the_arguments.apply)

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
    print("1. Go to the designation of your site in the desk")
    print("2. Upload signature image to 'Designation Signature' field")
    print("3. Set authority level and approval limits")
    print("4. Repeat for other designations")
    print("5. Run sync to propagate signatures to employees and users")

    if the_arguments.apply:
        frappe.db.commit()
    else:
        frappe.db.rollback()
    frappe.destroy()

    return 0 if results["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
