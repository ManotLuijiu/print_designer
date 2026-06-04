#!/usr/bin/env python3
"""
Fix documents with invalid pd_custom_income_type values.

This script clears pd_custom_income_type fields that contain invalid values
(e.g., "WHT 3% Service Fees - Corporate (PND53)") which were incorrectly
set by copying pd_custom_wht_income_type (Tax Withholding Category) to
pd_custom_income_type (Select field with Thai income type codes).

Root cause: The field mapping copied Tax Withholding Category names to
pd_custom_income_type Select field which only accepts Thai income type codes.

Fix: Clear pd_custom_income_type for documents with invalid values.
"""

import frappe


def fix_invalid_pd_custom_income_type():
    """
    Clear pd_custom_income_type for documents where it's set to an invalid value.
    
    Invalid values are those that look like Tax Withholding Category names
    (e.g., "WHT 3% Service Fees - Corporate (PND53)") rather than Thai income type codes.
    """
    
    # Valid Thai income type codes (what pd_custom_income_type should contain)
    valid_income_types = [
        "1. เงินเดือน ค่าจ้าง ฯลฯ 40(1)",
        "2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)",
        "3. ค่าแห่งลิขสิทธิ์ ฯลฯ 40(3)",
        "4. ดอกเบี้ย ฯลฯ 40(4)ก",
        "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส",
        "6. ค่าบริการ/ค่าสินค้าภาครัฐ",
    ]
    
    doctypes = [
        "Payment Entry",
        "Purchase Invoice",
        "Purchase Order",
        "Sales Invoice",
        "Sales Order",
        "Quotation",
    ]
    
    total_fixed = 0
    
    for dt in doctypes:
        # Check if pd_custom_income_type field exists
        field_exists = frappe.db.exists("Custom Field", f"{dt}-pd_custom_income_type")
        if not field_exists:
            print(f"⏭️  {dt}: pd_custom_income_type field does not exist")
            continue
        
        # Find documents with invalid pd_custom_income_type values
        # Invalid = contains "WHT" or "(" which indicates Tax Withholding Category name
        invalid_docs = frappe.get_all(
            dt,
            filters={
                "pd_custom_income_type": ["like", "%WHT%"],
            },
            fields=["name", "pd_custom_income_type"],
        )
        
        if invalid_docs:
            print(f"\n📋 {dt}: Found {len(invalid_docs)} document(s) with invalid pd_custom_income_type")
            for doc in invalid_docs:
                print(f"   - {doc.name}: '{doc.pd_custom_income_type}'")
                # Clear the invalid value
                frappe.db.set_value(dt, doc.name, "pd_custom_income_type", None)
                print(f"     ✅ Cleared pd_custom_income_type")
                total_fixed += 1
        else:
            print(f"✅ {dt}: No documents with invalid pd_custom_income_type")
    
    if total_fixed > 0:
        frappe.db.commit()
        print(f"\n✅ Fixed {total_fixed} document(s)")
        print("   Clear cache and test to verify the fix.")
    else:
        print("\n✅ No documents needed fixing")
    
    return total_fixed


@frappe.whitelist()
def execute():
    """Run the fix"""
    frappe.init("")
    frappe.set_user("Administrator")
    count = fix_invalid_pd_custom_income_type()
    return {"fixed": count}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/frappe/frappe-bench/apps/frappe")
    frappe.init("digisoft-erp.bunchee.online")
    frappe.set_user("Administrator")
    count = fix_invalid_pd_custom_income_type()
    print(f"\n{'='*60}")
    print(f"Total fixed: {count}")