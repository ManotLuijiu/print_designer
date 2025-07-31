"""
Command to verify and fix signature fields installation.

This command provides functionality to:
1. Check the status of signature fields across all sites
2. Fix missing signature fields and database columns
3. Verify that signature fields are working properly

Usage:
- bench execute print_designer.commands.fix_signature_fields.check_status
- bench execute print_designer.commands.fix_signature_fields.fix_all_sites
- bench execute print_designer.commands.fix_signature_fields.fix_current_site
"""

import frappe
from frappe import _
import click


@frappe.whitelist()
def check_status():
    """
    Check the status of signature fields for the current site.
    Shows which fields are properly installed with database columns.
    """
    try:
        from print_designer.signature_fields import get_signature_fields

        signature_fields = get_signature_fields()

        if not signature_fields:
            print("No signature fields defined in signature_fields.py")
            return {"success": True, "message": "No signature fields defined"}

        print("🔍 Checking signature fields status...")
        print("=" * 60)

        total_doctypes = 0
        fully_installed = 0
        partially_installed = 0
        missing_doctypes = 0
        issues_found = []

        for doctype, fields in signature_fields.items():
            total_doctypes += 1

            # Check if DocType exists
            if not frappe.db.exists("DocType", doctype):
                print(f"❌ {doctype}: DocType not found")
                missing_doctypes += 1
                continue

            doctype_issues = []
            fields_ok = 0

            for field in fields:
                fieldname = field["fieldname"]
                label = field.get("label", fieldname)

                # Check Custom Field
                custom_field_exists = frappe.db.exists(
                    "Custom Field", {"dt": doctype, "fieldname": fieldname}
                )

                # Check database column
                db_column_exists = False
                try:
                    result = frappe.db.sql(
                        f"SHOW COLUMNS FROM `tab{doctype}` LIKE %s", (fieldname,)
                    )
                    db_column_exists = bool(result)
                except Exception:
                    db_column_exists = False

                if custom_field_exists and db_column_exists:
                    fields_ok += 1
                else:
                    issue = f"  ⚠️  {fieldname} ({label}): "
                    if not custom_field_exists:
                        issue += "Custom Field missing"
                    if not db_column_exists:
                        if not custom_field_exists:
                            issue += ", Database column missing"
                        else:
                            issue += "Database column missing"
                    doctype_issues.append(issue)

            # Print DocType status
            if fields_ok == len(fields):
                print(f"✅ {doctype}: All {len(fields)} fields OK")
                fully_installed += 1
            elif fields_ok > 0:
                print(f"⚠️  {doctype}: {fields_ok}/{len(fields)} fields OK")
                for issue in doctype_issues:
                    print(issue)
                partially_installed += 1
                issues_found.extend(doctype_issues)
            else:
                print(f"❌ {doctype}: 0/{len(fields)} fields OK")
                for issue in doctype_issues:
                    print(issue)
                issues_found.extend(doctype_issues)

        # Print summary
        print("\n📊 Summary:")
        print(f"   Total DocTypes: {total_doctypes}")
        print(f"   ✅ Fully installed: {fully_installed}")
        print(f"   ⚠️  Partially installed: {partially_installed}")
        print(f"   ❌ Missing DocTypes: {missing_doctypes}")
        print(f"   🔧 Issues found: {len(issues_found)}")

        if issues_found:
            print(
                f"\n💡 Run 'bench execute print_designer.commands.fix_signature_fields.fix_current_site' to fix issues"
            )
        else:
            print(f"\n🎉 All signature fields are properly installed!")

        return {
            "success": True,
            "total_doctypes": total_doctypes,
            "fully_installed": fully_installed,
            "partially_installed": partially_installed,
            "missing_doctypes": missing_doctypes,
            "issues_count": len(issues_found),
            "issues": issues_found,
        }

    except Exception as e:
        print(f"❌ Error checking signature fields status: {str(e)}")
        frappe.log_error(f"Error checking signature fields status: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def fix_current_site():
    """
    Fix signature fields for the current site.
    Installs missing Custom Fields and synchronizes database columns.
    """
    try:
        from print_designer.signature_fields import get_signature_fields
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

        signature_fields = get_signature_fields()

        if not signature_fields:
            print("No signature fields defined in signature_fields.py")
            return {"success": True, "message": "No signature fields to fix"}

        print("🔧 Fixing signature fields for current site...")
        print("=" * 60)

        # Track what needs to be fixed
        fields_to_install = {}
        doctypes_to_sync = []
        total_fields_installed = 0
        total_columns_synced = 0

        for doctype, fields in signature_fields.items():
            # Check if DocType exists
            if not frappe.db.exists("DocType", doctype):
                print(f"⚠️  Skipping {doctype}: DocType not found")
                continue

            missing_fields = []
            needs_db_sync = False

            for field in fields:
                fieldname = field["fieldname"]

                # Check Custom Field
                custom_field_exists = frappe.db.exists(
                    "Custom Field", {"dt": doctype, "fieldname": fieldname}
                )

                # Check database column
                db_column_exists = False
                try:
                    result = frappe.db.sql(
                        f"SHOW COLUMNS FROM `tab{doctype}` LIKE %s", (fieldname,)
                    )
                    db_column_exists = bool(result)
                except Exception:
                    db_column_exists = False

                # Add to installation list if Custom Field is missing
                if not custom_field_exists:
                    missing_fields.append(field)
                    total_fields_installed += 1

                # Mark for DB sync if column is missing
                if custom_field_exists and not db_column_exists:
                    needs_db_sync = True
                    total_columns_synced += 1

            # Track what needs to be done for this DocType
            if missing_fields:
                fields_to_install[doctype] = missing_fields
                print(
                    f"📝 {doctype}: Will install {len(missing_fields)} missing Custom Fields"
                )

            if needs_db_sync:
                doctypes_to_sync.append(doctype)
                print(f"🔄 {doctype}: Will synchronize database columns")

        # Install missing Custom Fields
        if fields_to_install:
            print(f"\n🔧 Installing {total_fields_installed} missing Custom Fields...")
            create_custom_fields(fields_to_install, ignore_validate=True)
            print("✅ Custom Fields installation completed")

        # Synchronize database columns
        if doctypes_to_sync:
            print(
                f"\n🔄 Synchronizing database columns for {len(doctypes_to_sync)} DocTypes..."
            )
            for doctype in doctypes_to_sync:
                try:
                    frappe.db.updatedb(doctype)
                    print(f"   ✅ {doctype}: Database synchronized")
                except Exception as e:
                    print(f"   ❌ {doctype}: Database sync failed - {str(e)}")

        # Commit changes
        if fields_to_install or doctypes_to_sync:
            frappe.db.commit()
            frappe.clear_cache()
            print(f"\n💾 Changes committed and cache cleared")

        print(f"\n🎉 Signature fields fix completed!")
        print(f"   📝 Custom Fields installed: {total_fields_installed}")
        print(f"   🔄 DocTypes database-synced: {len(doctypes_to_sync)}")

        return {
            "success": True,
            "fields_installed": total_fields_installed,
            "doctypes_synced": len(doctypes_to_sync),
            "doctypes_processed": len(fields_to_install) + len(doctypes_to_sync),
        }

    except Exception as e:
        print(f"❌ Error fixing signature fields: {str(e)}")
        frappe.log_error(f"Error fixing signature fields: {str(e)}")
        return {"success": False, "error": str(e)}


def fix_all_sites():
    """
    Fix signature fields across all sites in the bench.
    This is a bench-level command that should be run with proper site context.
    """
    try:
        print("🌐 Fixing signature fields across all sites...")
        print("=" * 60)

        # Get all sites
        sites = frappe.utils.get_sites()

        if not sites:
            print("No sites found in this bench")
            return

        total_sites = len(sites)
        sites_fixed = 0
        sites_failed = 0

        for site in sites:
            try:
                print(f"\n🔧 Processing site: {site}")
                print("-" * 40)

                # Initialize site context
                frappe.init(site=site)
                frappe.connect()

                # Fix signature fields for this site
                result = fix_current_site()

                if result.get("success"):
                    sites_fixed += 1
                    print(f"✅ {site}: Fixed successfully")
                else:
                    sites_failed += 1
                    print(
                        f"❌ {site}: Fix failed - {result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                sites_failed += 1
                print(f"❌ {site}: Error - {str(e)}")

            finally:
                # Clean up site context
                try:
                    frappe.destroy()
                except:
                    pass

        print(f"\n📊 Multi-site fix summary:")
        print(f"   Total sites: {total_sites}")
        print(f"   ✅ Sites fixed: {sites_fixed}")
        print(f"   ❌ Sites failed: {sites_failed}")

        return {
            "success": True,
            "total_sites": total_sites,
            "sites_fixed": sites_fixed,
            "sites_failed": sites_failed,
        }

    except Exception as e:
        print(f"❌ Error in multi-site fix: {str(e)}")
        frappe.log_error(f"Error in multi-site signature fields fix: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def test_signature_field(doctype="User", fieldname="signature_image"):
    """
    Test a specific signature field to ensure it's working properly.

    Args:
        doctype (str): DocType to test
        fieldname (str): Field name to test
    """
    try:
        print(f"🧪 Testing signature field: {doctype}.{fieldname}")
        print("=" * 50)

        # Check if DocType exists
        if not frappe.db.exists("DocType", doctype):
            print(f"❌ DocType '{doctype}' not found")
            return {"success": False, "error": f"DocType '{doctype}' not found"}

        # Check Custom Field
        custom_field = frappe.db.get_value(
            "Custom Field",
            {"dt": doctype, "fieldname": fieldname},
            ["name", "label", "fieldtype", "insert_after"],
            as_dict=True,
        )

        if not custom_field:
            print(f"❌ Custom Field '{fieldname}' not found for {doctype}")
            return {"success": False, "error": f"Custom Field '{fieldname}' not found"}

        print(f"✅ Custom Field found:")
        print(f"   Name: {custom_field.name}")
        print(f"   Label: {custom_field.label}")
        print(f"   Type: {custom_field.fieldtype}")
        print(f"   Insert After: {custom_field.insert_after}")

        # Check database column
        try:
            result = frappe.db.sql(
                f"SHOW COLUMNS FROM `tab{doctype}` LIKE %s", (fieldname,)
            )
            if result:
                column_info = result[0]
                print(f"✅ Database column found:")
                print(f"   Column: {column_info[0]}")
                print(f"   Type: {column_info[1]}")
                print(f"   Null: {column_info[2]}")
                print(f"   Default: {column_info[4]}")
            else:
                print(f"❌ Database column '{fieldname}' not found in tab{doctype}")
                return {
                    "success": False,
                    "error": f"Database column '{fieldname}' missing",
                }
        except Exception as e:
            print(f"❌ Error checking database column: {str(e)}")
            return {"success": False, "error": f"Database check failed: {str(e)}"}

        # Test field access (try to read/write)
        try:
            # Get a test record (first available record)
            test_record = frappe.db.get_value(doctype, {}, "name")
            if test_record:
                current_value = frappe.db.get_value(doctype, test_record, fieldname)
                print(f"✅ Field access test passed:")
                print(f"   Test record: {test_record}")
                print(f"   Current value: {current_value or 'None'}")
            else:
                print(f"⚠️  No records found in {doctype} for field access test")
        except Exception as e:
            print(f"❌ Field access test failed: {str(e)}")
            return {"success": False, "error": f"Field access test failed: {str(e)}"}

        print(f"\n🎉 Signature field test passed! '{fieldname}' is working properly.")

        return {
            "success": True,
            "doctype": doctype,
            "fieldname": fieldname,
            "custom_field": custom_field,
            "database_column_exists": True,
            "field_accessible": True,
        }

    except Exception as e:
        print(f"❌ Error testing signature field: {str(e)}")
        frappe.log_error(
            f"Error testing signature field {doctype}.{fieldname}: {str(e)}"
        )
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            check_status()
        elif command == "fix":
            fix_current_site()
        elif command == "fix-all":
            fix_all_sites()
        elif command == "test":
            doctype = sys.argv[2] if len(sys.argv) > 2 else "User"
            fieldname = sys.argv[3] if len(sys.argv) > 3 else "signature_image"
            test_signature_field(doctype, fieldname)
        else:
            print("Usage: python fix_signature_fields.py [check|fix|fix-all|test]")
    else:
        print("Available commands:")
        print("  check    - Check signature fields status")
        print("  fix      - Fix signature fields for current site")
        print("  fix-all  - Fix signature fields for all sites")
        print("  test     - Test a specific signature field")
