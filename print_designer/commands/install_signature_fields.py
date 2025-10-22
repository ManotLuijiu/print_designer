"""
Signature Field Management Commands for Print Designer
Handles installation, verification, and removal of signature image fields across multiple DocTypes.

Signature fields enable digital signature capture and display in print formats for:
- HR documents (Employee, Appraisal, Job Offer)
- Sales transactions (Sales Invoice, Sales Order, Quotation)
- Purchase transactions (Purchase Invoice, Purchase Order, RFQ)
- Stock operations (Delivery Note, Purchase Receipt)
- Accounting (Company authorization signatures)
- Quality assurance (Quality Inspection)
- And more...

Usage:
    bench --site [site] install-signature-fields
    bench --site [site] check-signature-fields
    bench --site [site] uninstall-signature-fields
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Complete signature fields configuration for all DocTypes
SIGNATURE_CUSTOM_FIELDS = {
    # ============================================================
    # SECTION 1: USER MANAGEMENT & HR
    # ============================================================
    "User": [
        {
            "fieldname": "signature_image",
            "fieldtype": "Attach Image",
            "label": "Signature",
            "insert_after": "user_image",
            "description": "Upload signature image for documents and print formats",
        }
    ],
    "Employee": [
        {
            "fieldname": "signature_image",
            "fieldtype": "Attach Image",
            "label": "Signature",
            "insert_after": "image",
            "description": "Employee signature for HR documents and approvals",
        }
    ],
    "Designation": [
        {
            "fieldname": "designation_signature",
            "fieldtype": "Attach Image",
            "label": "Designation Signature",
            "insert_after": "description",
            "description": "Default signature for this designation/role",
        },
        {
            "fieldname": "signature_authority_level",
            "fieldtype": "Select",
            "label": "Signature Authority Level",
            "options": "None\nLow\nMedium\nHigh\nExecutive",
            "default": "None",
            "insert_after": "designation_signature",
            "description": "Level of signature authority for approval workflows",
        },
        {
            "fieldname": "max_approval_amount",
            "fieldtype": "Currency",
            "label": "Maximum Approval Amount",
            "insert_after": "signature_authority_level",
            "description": "Maximum amount this designation can approve with signature",
        },
    ],
    "Job Offer": [
        {
            "fieldname": "hr_signature",
            "fieldtype": "Attach Image",
            "label": "HR Signature",
            "insert_after": "offer_terms",
            "description": "HR representative signature",
        },
        {
            "fieldname": "candidate_signature",
            "fieldtype": "Attach Image",
            "label": "Candidate Signature",
            "insert_after": "hr_signature",
            "description": "Candidate acceptance signature",
        },
    ],
    "Appraisal": [
        {
            "fieldname": "appraiser_signature",
            "fieldtype": "Attach Image",
            "label": "Appraiser Signature",
            "insert_after": "appraisal_template",
            "description": "Signature of person conducting appraisal",
        },
        {
            "fieldname": "employee_signature",
            "fieldtype": "Attach Image",
            "label": "Employee Signature",
            "insert_after": "appraiser_signature",
            "description": "Employee acknowledgment signature",
        },
    ],
    # ============================================================
    # SECTION 2: CRM MODULE
    # ============================================================
    "Customer": [
        {
            "fieldname": "signature_image",
            "fieldtype": "Attach Image",
            "label": "Authorized Signature",
            "insert_after": "image",
            "description": "Authorized signatory signature for customer documents",
        }
    ],
    "Lead": [
        {
            "fieldname": "signature_image",
            "fieldtype": "Attach Image",
            "label": "Signature",
            "insert_after": "image",
            "description": "Lead signature for agreements and documents",
        }
    ],
    # ============================================================
    # SECTION 3: BUYING MODULE
    # ============================================================
    "Supplier": [
        {
            "fieldname": "signature_image",
            "fieldtype": "Attach Image",
            "label": "Authorized Signature",
            "insert_after": "image",
            "description": "Authorized signatory signature for supplier documents",
        }
    ],
    # ============================================================
    # SECTION 4: ACCOUNTING MODULE
    # ============================================================
    "Company": [
        {
            "fieldname": "company_stamps_section",
            "label": "Company Stamps & Signatures",
            "fieldtype": "Section Break",
            "insert_after": "address_html",
        },
        {
            "fieldname": "company_stamps_column_break",
            "fieldtype": "Column Break",
            "label": "",
            "insert_after": "company_stamps_section",
        },
        {
            "fieldname": "company_stamp_1",
            "fieldtype": "Attach Image",
            "label": "Company Stamp 1",
            "insert_after": "company_stamps_column_break",
            "description": "Primary company stamp for official documents",
        },
        {
            "fieldname": "company_stamp_2",
            "fieldtype": "Attach Image",
            "label": "Company Stamp 2",
            "insert_after": "company_stamp_1",
            "description": "Secondary company stamp for official documents",
        },
        {
            "fieldname": "official_seal",
            "fieldtype": "Attach Image",
            "label": "Official Seal",
            "insert_after": "company_stamp_2",
            "description": "Official company seal for legal documents",
        },
        {
            "fieldname": "custom_column_break_phyun",
            "fieldtype": "Column Break",
            "label": "",
            "insert_after": "official_seal",
        },
        {
            "fieldname": "authorized_signature_1",
            "fieldtype": "Attach Image",
            "label": "Authorized Signature 1",
            "insert_after": "custom_column_break_phyun",
            "description": "Primary authorized signatory for company documents",
        },
        {
            "fieldname": "authorized_signature_2",
            "fieldtype": "Attach Image",
            "label": "Authorized Signature 2",
            "insert_after": "authorized_signature_1",
            "description": "Secondary authorized signatory for company documents",
        },
        {
            "fieldname": "ceo_signature",
            "fieldtype": "Attach Image",
            "label": "CEO Signature",
            "insert_after": "authorized_signature_2",
            "description": "CEO signature for executive documents",
        },
    ],
    # ============================================================
    # SECTION 5: PROJECTS MODULE
    # ============================================================
    "Project": [
        {
            "fieldname": "project_manager_signature",
            "fieldtype": "Attach Image",
            "label": "Project Manager Signature",
            "insert_after": "project_name",
            "description": "Project manager signature for project documents",
        }
    ],
    # ============================================================
    # SECTION 6: MANUFACTURING & QUALITY
    # ============================================================
    "Item": [
        {
            "fieldname": "quality_inspector_signature",
            "fieldtype": "Attach Image",
            "label": "Quality Inspector Signature",
            "insert_after": "image",
            "description": "Quality inspector signature for item certification",
        }
    ],
    "Quality Inspection": [
        {
            "fieldname": "inspector_signature",
            "fieldtype": "Attach Image",
            "label": "Inspector Signature",
            "insert_after": "quality_inspection_template",
            "description": "Quality inspector signature",
        },
        {
            "fieldname": "supervisor_signature",
            "fieldtype": "Attach Image",
            "label": "Supervisor Signature",
            "insert_after": "inspector_signature",
            "description": "Supervisor approval signature",
        },
    ],
    # ============================================================
    # SECTION 7: SALES TRANSACTIONS
    # ============================================================
    "Sales Invoice": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "sales_team",
            "description": "Signature of person who prepared the invoice",
        },
        {
            "fieldname": "approved_by_signature",
            "fieldtype": "Attach Image",
            "label": "Approved By Signature",
            "insert_after": "prepared_by_signature",
            "description": "Signature of person who approved the invoice",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "sales_team",
            "description": "Signature of person who prepared the sales order",
        },
        {
            "fieldname": "approved_by_signature",
            "fieldtype": "Attach Image",
            "label": "Approved By Signature",
            "insert_after": "prepared_by_signature",
            "description": "Signature of person who approved the sales order",
        },
    ],
    "Quotation": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "sales_team",
            "description": "Signature of person who prepared the quotation",
        }
    ],
    # ============================================================
    # SECTION 8: PURCHASE TRANSACTIONS
    # ============================================================
    "Purchase Invoice": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "buying_price_list",
            "description": "Signature of person who prepared the purchase invoice",
        },
        {
            "fieldname": "approved_by_signature",
            "fieldtype": "Attach Image",
            "label": "Approved By Signature",
            "insert_after": "prepared_by_signature",
            "description": "Signature of person who approved the purchase invoice",
        },
    ],
    "Purchase Order": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "buying_price_list",
            "description": "Signature of person who prepared the purchase order",
        },
        {
            "fieldname": "approved_by_signature",
            "fieldtype": "Attach Image",
            "label": "Approved By Signature",
            "insert_after": "prepared_by_signature",
            "description": "Signature of person who approved the purchase order",
        },
    ],
    "Request for Quotation": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "buying_price_list",
            "description": "Signature of person who prepared the RFQ",
        }
    ],
    # ============================================================
    # SECTION 9: STOCK OPERATIONS
    # ============================================================
    "Delivery Note": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "shipping_address_name",
            "description": "Signature of person who prepared the delivery note",
        },
        {
            "fieldname": "delivered_by_signature",
            "fieldtype": "Attach Image",
            "label": "Delivered By Signature",
            "insert_after": "prepared_by_signature",
            "description": "Signature of delivery person",
        },
        {
            "fieldname": "received_by_signature",
            "fieldtype": "Attach Image",
            "label": "Received By Signature",
            "insert_after": "delivered_by_signature",
            "description": "Signature of person who received the delivery",
        },
    ],
    "Purchase Receipt": [
        {
            "fieldname": "prepared_by_signature",
            "fieldtype": "Attach Image",
            "label": "Prepared By Signature",
            "insert_after": "shipping_address",
            "description": "Signature of person who prepared the purchase receipt",
        },
        {
            "fieldname": "received_by_signature",
            "fieldtype": "Attach Image",
            "label": "Received By Signature",
            "insert_after": "prepared_by_signature",
            "description": "Signature of person who received the items",
        },
    ],
    # ============================================================
    # SECTION 10: ASSET MANAGEMENT
    # ============================================================
    "Asset": [
        {
            "fieldname": "custodian_signature",
            "fieldtype": "Attach Image",
            "label": "Custodian Signature",
            "insert_after": "image",
            "description": "Signature of asset custodian",
        }
    ],
    # ============================================================
    # SECTION 11: MAINTENANCE
    # ============================================================
    "Maintenance Schedule": [
        {
            "fieldname": "technician_signature",
            "fieldtype": "Attach Image",
            "label": "Technician Signature",
            "insert_after": "maintenance_schedule_details",
            "description": "Technician signature for maintenance completion",
        }
    ],
    # ============================================================
    # SECTION 12: CUSTOM DOCTYPES (Optional)
    # ============================================================
    "Contract": [
        {
            "fieldname": "party_signature",
            "fieldtype": "Attach Image",
            "label": "Party Signature",
            "insert_after": "contract_terms",
            "description": "Contracting party signature",
        },
        {
            "fieldname": "witness_signature",
            "fieldtype": "Attach Image",
            "label": "Witness Signature",
            "insert_after": "party_signature",
            "description": "Witness signature",
        },
    ],
}


def create_signature_fields():
    """
    Install signature fields for all configured DocTypes in Print Designer.

    Returns:
            bool: True if installation successful, False otherwise
    """
    try:
        print("🚀 Installing signature fields for Print Designer...")

        # Track installation progress
        installed_doctypes = []
        skipped_doctypes = []
        total_fields = 0

        for doctype, fields in SIGNATURE_CUSTOM_FIELDS.items():
            # Check if DocType exists
            if not frappe.db.exists("DocType", doctype):
                print(f"⚠️  DocType '{doctype}' not found, skipping...")
                skipped_doctypes.append(doctype)
                continue

            # Check existing fields to avoid duplicates
            existing_fields = frappe.get_all(
                "Custom Field", filters={"dt": doctype}, fields=["fieldname"]
            )
            existing_fieldnames = [f.fieldname for f in existing_fields]

            # Only add fields that don't exist
            new_fields = []
            for field in fields:
                if field["fieldname"] not in existing_fieldnames:
                    new_fields.append(field)

            # Install new fields
            if new_fields:
                create_custom_fields({doctype: new_fields}, update=True, ignore_validate=True)
                installed_doctypes.append(doctype)
                total_fields += len(new_fields)
                print(f"   ✓ Installed {len(new_fields)} field(s) for {doctype}")
            else:
                print(f"   ℹ All fields already exist for {doctype}")

        frappe.db.commit()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Installation Summary:")
        print(f"   ✅ DocTypes with new fields installed: {len(installed_doctypes)}")
        print(f"   📝 Total new fields installed: {total_fields}")
        print(f"   ⚠️  DocTypes skipped (not found): {len(skipped_doctypes)}")

        if skipped_doctypes:
            print("\n⚠️  Skipped DocTypes:")
            for dt in skipped_doctypes:
                print(f"   - {dt}")

        print("\n✅ Signature fields installation completed!")
        print("=" * 60)

        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"\n❌ Error installing signature fields: {str(e)}")
        frappe.log_error("Signature Fields Installation Error", str(e))
        return False


def check_signature_fields():
    """
    Verify that signature fields are properly installed across all DocTypes.

    Returns:
            bool: True if all fields exist, False otherwise
    """
    try:
        print("🔍 Checking signature fields installation status...")
        print("=" * 60)

        total_doctypes = 0
        complete_doctypes = 0
        partial_doctypes = 0
        missing_doctypes = 0
        total_fields_expected = 0
        total_fields_installed = 0

        for doctype, fields in SIGNATURE_CUSTOM_FIELDS.items():
            total_doctypes += 1
            total_fields_expected += len(fields)

            # Check if DocType exists
            if not frappe.db.exists("DocType", doctype):
                print(f"❌ {doctype}: DocType not found")
                missing_doctypes += 1
                continue

            # Check each field
            installed_fields = []
            missing_fields = []

            for field in fields:
                fieldname = field["fieldname"]
                if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
                    installed_fields.append(fieldname)
                    total_fields_installed += 1
                else:
                    missing_fields.append(fieldname)

            # Report status
            if not missing_fields:
                print(f"✅ {doctype}: All {len(installed_fields)} field(s) installed")
                complete_doctypes += 1
            else:
                print(f"⚠️  {doctype}: {len(installed_fields)}/{len(fields)} field(s) installed")
                for field in missing_fields:
                    print(f"   ✗ Missing: {field}")
                partial_doctypes += 1

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Verification Summary:")
        print(f"   Total DocTypes: {total_doctypes}")
        print(f"   ✅ Complete: {complete_doctypes}")
        print(f"   ⚠️  Partial: {partial_doctypes}")
        print(f"   ❌ Missing: {missing_doctypes}")
        print(f"\n   Total fields expected: {total_fields_expected}")
        print(f"   Total fields installed: {total_fields_installed}")
        print(f"   Coverage: {(total_fields_installed/total_fields_expected*100):.1f}%")
        print("=" * 60)

        return partial_doctypes == 0 and missing_doctypes == 0

    except Exception as e:
        print(f"\n❌ Error checking signature fields: {str(e)}")
        frappe.log_error("Signature Fields Check Error", str(e))
        return False


def uninstall_signature_fields():
    """
    Remove all signature fields created by Print Designer.

    Returns:
            bool: True if removal successful, False otherwise
    """
    try:
        print("🗑️  Removing signature fields from Print Designer...")

        removed_count = 0
        skipped_count = 0

        for doctype, fields in SIGNATURE_CUSTOM_FIELDS.items():
            # Check if DocType exists
            if not frappe.db.exists("DocType", doctype):
                skipped_count += len(fields)
                continue

            # Remove each field
            for field in fields:
                fieldname = field["fieldname"]
                custom_field = frappe.db.exists(
                    "Custom Field", {"dt": doctype, "fieldname": fieldname}
                )

                if custom_field:
                    frappe.delete_doc("Custom Field", custom_field, force=1)
                    removed_count += 1
                    print(f"   ✓ Removed {doctype}.{fieldname}")

        frappe.db.commit()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Uninstallation Summary:")
        print(f"   ✅ Fields removed: {removed_count}")
        print(f"   ⚠️  Fields skipped (DocType not found): {skipped_count}")
        print("\n✅ Signature fields uninstallation completed!")
        print("=" * 60)

        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"\n❌ Error removing signature fields: {str(e)}")
        frappe.log_error("Signature Fields Uninstall Error", str(e))
        return False


# ============================================================
# CLICK CLI COMMANDS FOR BENCH INTEGRATION
# ============================================================


@click.command("install-signature-fields")
@click.pass_context
def install_signature_fields_cmd(context):
    """Install signature fields for Print Designer"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        create_signature_fields()
        frappe.destroy()


@click.command("check-signature-fields")
@click.pass_context
def check_signature_fields_cmd(context):
    """Verify signature fields installation"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        check_signature_fields()
        frappe.destroy()


@click.command("uninstall-signature-fields")
@click.pass_context
def uninstall_signature_fields_cmd(context):
    """Remove signature fields from Print Designer"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        uninstall_signature_fields()
        frappe.destroy()


# Commands are registered in hooks.py as string paths
