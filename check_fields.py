#!/usr/bin/env python3
"""
Check if the WHT Certificate fields exist and are properly configured
"""

import frappe

def check_wht_fields():
    # Check if Withholding Tax Certificate DocType exists
    if frappe.db.exists("DocType", "Withholding Tax Certificate"):
        print("✅ Withholding Tax Certificate DocType exists")

        # Get the DocType meta
        meta = frappe.get_meta("Withholding Tax Certificate")
        print(f"   Total fields: {len(meta.fields)}")
        print(f"   Field order: {meta.field_order[:10]}...")  # First 10 fields
    else:
        print("❌ Withholding Tax Certificate DocType does NOT exist")

    # Check Payment Entry custom fields
    print("\n📋 Payment Entry WHT Certificate Fields:")

    # Check pd_custom_wht_certificate (Link field for Pay)
    if frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "pd_custom_wht_certificate"}):
        field = frappe.get_doc("Custom Field", {"dt": "Payment Entry", "fieldname": "pd_custom_wht_certificate"})
        print(f"✅ pd_custom_wht_certificate exists")
        print(f"   - fieldtype: {field.fieldtype}")
        print(f"   - options: {field.options}")
        print(f"   - depends_on: {field.depends_on}")
        print(f"   - read_only: {field.read_only}")
    else:
        print("❌ pd_custom_wht_certificate does NOT exist")

    # Check pd_custom_wht_certificate_no (Data field for Receive)
    if frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "pd_custom_wht_certificate_no"}):
        field = frappe.get_doc("Custom Field", {"dt": "Payment Entry", "fieldname": "pd_custom_wht_certificate_no"})
        print(f"✅ pd_custom_wht_certificate_no exists")
        print(f"   - fieldtype: {field.fieldtype}")
        print(f"   - depends_on: {field.depends_on}")
    else:
        print("❌ pd_custom_wht_certificate_no does NOT exist")

    # Check if there are any WHT Certificates
    count = frappe.db.count("Withholding Tax Certificate")
    print(f"\n📊 Total WHT Certificates in system: {count}")

    if count > 0:
        # Show latest certificate
        latest = frappe.get_last_doc("Withholding Tax Certificate")
        print(f"   Latest certificate: {latest.name}")
        print(f"   - Status: {latest.status}")
        print(f"   - Date: {latest.certificate_date}")

if __name__ == "__main__":
    check_wht_fields()