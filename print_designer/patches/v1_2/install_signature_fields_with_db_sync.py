"""
Patch to install signature fields with proper database synchronization.

This patch ensures that:
1. Custom fields are created for all signature fields defined in signature_fields.py
2. Database columns are properly created via updatedb()
3. All existing sites get signature fields even if they were missed during installation
4. The patch is idempotent and safe to run multiple times

This addresses the issue where signature_image column was missing from User table
and similar issues with other signature fields.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Main patch execution function that installs signature fields with database synchronization
    """
    try:
        frappe.logger().info(
            "🔧 Starting signature fields installation with database sync patch"
        )

        # Import signature fields configuration
        from print_designer.signature_fields import get_signature_fields

        signature_fields = get_signature_fields()

        if not signature_fields:
            frappe.logger().info("No signature fields defined, skipping patch")
            return

        # Track installation progress
        doctypes_processed = 0
        fields_created = 0
        doctypes_synced = 0

        for doctype, fields in signature_fields.items():
            try:
                # Check if DocType exists
                if not frappe.db.exists("DocType", doctype):
                    frappe.logger().info(f"⚠️  DocType '{doctype}' not found, skipping")
                    continue

                # Create custom fields for this DocType
                custom_fields = {doctype: fields}
                create_custom_fields(custom_fields, ignore_validate=True)

                # Force database synchronization for this DocType
                # This ensures that database columns are created for all custom fields
                frappe.db.updatedb(doctype)

                frappe.logger().info(
                    f"✅ Processed {len(fields)} signature field(s) for '{doctype}'"
                )
                doctypes_processed += 1
                fields_created += len(fields)
                doctypes_synced += 1

            except Exception as e:
                frappe.logger().error(
                    f"❌ Failed to process signature fields for '{doctype}': {str(e)}"
                )
                # Continue with other DocTypes even if one fails
                continue

        # Commit all changes
        frappe.db.commit()

        # Log summary
        frappe.logger().info(f"🎉 Signature fields patch completed successfully:")
        frappe.logger().info(f"   📊 DocTypes processed: {doctypes_processed}")
        frappe.logger().info(f"   🖋️  Fields created/verified: {fields_created}")
        frappe.logger().info(f"   🔄 DocTypes database-synced: {doctypes_synced}")

        # Clear cache to ensure immediate availability
        frappe.clear_cache()

        frappe.logger().info("✅ Signature fields patch completed and cache cleared")

    except Exception as e:
        frappe.logger().error(f"❌ Critical error in signature fields patch: {str(e)}")
        # Re-raise to ensure patch fails and can be retried
        raise


def get_signature_fields_summary():
    """
    Get a summary of signature fields that should be installed by this patch.
    Useful for verification and logging purposes.

    Returns:
        dict: Summary information about signature fields
    """
    try:
        from print_designer.signature_fields import get_signature_fields

        signature_fields = get_signature_fields()

        summary = {
            "total_doctypes": len(signature_fields),
            "total_fields": sum(len(fields) for fields in signature_fields.values()),
            "doctypes": list(signature_fields.keys()),
            "field_counts": {
                doctype: len(fields) for doctype, fields in signature_fields.items()
            },
        }

        return summary

    except Exception as e:
        frappe.logger().error(f"Error getting signature fields summary: {str(e)}")
        return {"error": str(e)}


def verify_signature_fields_installation():
    """
    Verify that signature fields are properly installed with database columns.
    This can be called after the patch to ensure everything is working.

    Returns:
        dict: Verification results
    """
    try:
        from print_designer.signature_fields import get_signature_fields

        signature_fields = get_signature_fields()
        verification_results = {}

        for doctype, fields in signature_fields.items():
            if not frappe.db.exists("DocType", doctype):
                verification_results[doctype] = {"status": "doctype_missing"}
                continue

            doctype_results = {"status": "verified", "fields": {}, "issues": []}

            for field in fields:
                fieldname = field["fieldname"]

                # Check if Custom Field exists
                custom_field_exists = frappe.db.exists(
                    "Custom Field", {"dt": doctype, "fieldname": fieldname}
                )

                # Check if database column exists
                db_column_exists = False
                try:
                    result = frappe.db.sql(
                        f"SHOW COLUMNS FROM `tab{doctype}` LIKE %s", (fieldname,)
                    )
                    db_column_exists = bool(result)
                except Exception:
                    db_column_exists = False

                field_status = {
                    "custom_field_exists": bool(custom_field_exists),
                    "db_column_exists": db_column_exists,
                    "fully_installed": bool(custom_field_exists and db_column_exists),
                }

                doctype_results["fields"][fieldname] = field_status

                if not field_status["fully_installed"]:
                    issue = f"Field '{fieldname}' incomplete: "
                    if not custom_field_exists:
                        issue += "Custom Field missing, "
                    if not db_column_exists:
                        issue += "Database column missing"
                    doctype_results["issues"].append(issue.rstrip(", "))

            # Update overall status
            all_fields_ok = all(
                f["fully_installed"] for f in doctype_results["fields"].values()
            )
            if not all_fields_ok:
                doctype_results["status"] = "incomplete"

            verification_results[doctype] = doctype_results

        return {
            "success": True,
            "results": verification_results,
            "summary": {
                "total_doctypes": len(verification_results),
                "fully_verified": len(
                    [
                        r
                        for r in verification_results.values()
                        if r.get("status") == "verified"
                    ]
                ),
                "incomplete": len(
                    [
                        r
                        for r in verification_results.values()
                        if r.get("status") == "incomplete"
                    ]
                ),
                "missing_doctypes": len(
                    [
                        r
                        for r in verification_results.values()
                        if r.get("status") == "doctype_missing"
                    ]
                ),
            },
        }

    except Exception as e:
        frappe.logger().error(f"Error verifying signature fields: {str(e)}")
        return {"success": False, "error": str(e)}
