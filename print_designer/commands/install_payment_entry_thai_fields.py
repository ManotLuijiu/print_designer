#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install Thai Tax Compliance Fields for Payment Entry
Adds Thai-specific tax fields for withholding tax and VAT compliance
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe import _


def execute():
    """Main installation function for Payment Entry Thai tax fields"""
    print("Installing Thai Tax Compliance fields for Payment Entry...")

    create_payment_entry_thai_fields()

    # Clear cache to ensure changes are reflected
    frappe.clear_cache()
    print("✅ Thai Tax Compliance fields installed successfully for Payment Entry")


def create_payment_entry_thai_fields():
    """Create Thai tax compliance fields in Payment Entry matching fixtures order"""

    custom_fields = {
        "Payment Entry": [
            # Thai Compliance Tab - placed after title field
            {
                "fieldname": "pd_custom_thai_compliance_tab",
                "fieldtype": "Tab Break",
                "label": "Thai Tax Compliance",
                "insert_after": "title",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            # Column 1 - Button first in fixtures order
            {
                "fieldname": "pd_custom_thai_tax_column_1",
                "fieldtype": "Column Break",
                "label": "",
                "insert_after": "pd_custom_thai_compliance_tab",
                "width": "50%",
            },
            {
                "fieldname": "pd_custom_get_invoices_from_purchase_billing",
                "fieldtype": "Button",
                "label": "Get Invoices from Purchase Billing",
                "insert_after": "pd_custom_thai_tax_column_1",
                "hidden": 0,
                "no_copy": 1,
                "print_hide": 1,
            },
            {
                "fieldname": "pd_custom_tax_invoice_number",
                "fieldtype": "Data",
                "label": "Tax Invoice Number",
                "insert_after": "pd_custom_get_invoices_from_purchase_billing",
                "translatable": 0,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_tax_invoice_date",
                "fieldtype": "Date",
                "label": "Tax Invoice Date",
                "insert_after": "pd_custom_tax_invoice_number",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_supplier",
                "fieldtype": "Link",
                "label": "Supplier",
                "options": "Supplier",
                "insert_after": "pd_custom_tax_invoice_date",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_supplier_name",
                "fieldtype": "Data",
                "label": "Supplier Name",
                "insert_after": "pd_custom_supplier",
                "fetch_from": "pd_custom_supplier.supplier_name",
                "read_only": 1,
                "translatable": 0,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_income_type",
                "fieldtype": "Select",
                "label": "Income Type",
                "insert_after": "pd_custom_supplier_name",
                "options": "\n1. เงินเดือน ค่าจ้าง ฯลฯ 40(1)\n2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)\n3. ค่าแห่งลิขสิทธิ์ ฯลฯ 40(3)\n4. ดอกเบี้ย ฯลฯ 40(4)ก\n5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส\n6. ค่าบริการ/ค่าสินค้าภาครัฐ",
                "translatable": 0,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_tax_base_amount",
                "fieldtype": "Currency",
                "label": "Tax Base Amount",
                "insert_after": "pd_custom_income_type",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "bold": 1,
            },
            {
                "fieldname": "pd_custom_company_tax_address",
                "fieldtype": "Small Text",
                "label": "Company Tax Address",
                "insert_after": "pd_custom_tax_base_amount",
                "read_only": 1,
                "translatable": 0,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            # Column 2
            {
                "fieldname": "pd_custom_thai_tax_column_2",
                "fieldtype": "Column Break",
                "label": "",
                "insert_after": "pd_custom_company_tax_address",
                "width": "50%",
            },
            {
                "fieldname": "pd_custom_apply_withholding_tax",
                "fieldtype": "Check",
                "label": "Apply Withholding Tax",
                "insert_after": "pd_custom_thai_tax_column_2",
                "default": "0",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_wht_certificate_no",
                "fieldtype": "Data",
                "label": "WHT Certificate No",
                "insert_after": "pd_custom_apply_withholding_tax",
                "translatable": 0,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_wht_certificate_date",
                "fieldtype": "Date",
                "label": "WHT Certificate Date",
                "insert_after": "pd_custom_wht_certificate_no",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_withholding_tax_rate",
                "fieldtype": "Percent",
                "label": "Withholding Tax Rate (%)",
                "insert_after": "pd_custom_wht_certificate_date",
                "default": "0",
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
            },
            {
                "fieldname": "pd_custom_withholding_tax_amount",
                "fieldtype": "Currency",
                "label": "Withholding Tax Amount",
                "insert_after": "pd_custom_withholding_tax_rate",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "bold": 1,
            },
            {
                "fieldname": "pd_custom_net_payment_amount",
                "fieldtype": "Currency",
                "label": "Net Payment Amount",
                "insert_after": "pd_custom_withholding_tax_amount",
                "options": "Company:company:default_currency",
                "read_only": 1,
                "hidden": 0,
                "no_copy": 0,
                "print_hide": 0,
                "bold": 1,
            },
        ]
    }

    # Create the custom fields
    create_custom_fields(custom_fields, update=True)

    print("✅ Created Thai Tax Compliance fields in Payment Entry")


def check_fields_exist():
    """Check if Thai tax compliance fields already exist in Payment Entry"""

    required_fields = [
        "pd_custom_thai_compliance_tab",
        "pd_custom_company_tax_address",
        "pd_custom_tax_base_amount",
        "pd_custom_tax_invoice_number",
        "pd_custom_supplier",
        "pd_custom_tax_invoice_date",
        "pd_custom_supplier_name",
        "pd_custom_income_type",
        "pd_custom_wht_certificate_no",
        "pd_custom_wht_certificate_date",
        "pd_custom_withholding_tax_amount",
        "pd_custom_withholding_tax_rate",
        "pd_custom_net_payment_amount",
        "pd_custom_apply_withholding_tax",
        "pd_custom_get_invoices_from_purchase_billing",
    ]

    existing_fields = []
    missing_fields = []

    for field in required_fields:
        if frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": field}):
            existing_fields.append(field)
        else:
            missing_fields.append(field)

    print("\n📋 Payment Entry Thai Tax Compliance Fields Status:")
    print(f"✅ Existing fields: {len(existing_fields)}/{len(required_fields)}")

    if missing_fields:
        print(f"❌ Missing fields ({len(missing_fields)}):")
        for field in missing_fields:
            print(f"   - {field}")

    return len(missing_fields) == 0


def remove_thai_fields():
    """Remove Thai tax compliance fields from Payment Entry (for uninstall)"""

    fields_to_remove = [
        "pd_custom_thai_compliance_tab",
        "pd_custom_thai_tax_column_1",
        "pd_custom_thai_tax_column_2",
        "pd_custom_company_tax_address",
        "pd_custom_tax_base_amount",
        "pd_custom_tax_invoice_number",
        "pd_custom_supplier",
        "pd_custom_tax_invoice_date",
        "pd_custom_supplier_name",
        "pd_custom_income_type",
        "pd_custom_wht_certificate_no",
        "pd_custom_wht_certificate_date",
        "pd_custom_withholding_tax_amount",
        "pd_custom_withholding_tax_rate",
        "pd_custom_net_payment_amount",
        "pd_custom_apply_withholding_tax",
        "pd_custom_get_invoices_from_purchase_billing",
    ]

    for field in fields_to_remove:
        frappe.db.delete("Custom Field", {"dt": "Payment Entry", "fieldname": field})

    frappe.clear_cache()
    print("✅ Removed Thai Tax Compliance fields from Payment Entry")


if __name__ == "__main__":
    execute()