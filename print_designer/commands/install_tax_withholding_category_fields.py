"""
Custom Field: pd_custom_apply_wht_to_contract_installments on Tax Withholding Category
Adds Thai contract installment WHT flag to each WHT category.
"""

import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

TAX_WITHHOLDING_CATEGORY_CUSTOM_FIELDS = {
    "Tax Withholding Category": [
        {
            "fieldname": "pd_custom_apply_wht_to_contract_installments",
            "fieldtype": "Check",
            "label": "Apply WHT to All Contract Installments >= 1,000 THB",
            "insert_after": "tax_on_excess_amount",
            "translatable": 0,
            "description": "When enabled, WHT is deducted from every installment once the total contract value exceeds 1,000 THB, even if individual installments are below 1,000 THB. Per Thai Revenue Department regulations.",
            "module": "Print Designer",
        },
        {
            "fieldname": "pd_custom_thai_wht_income_type",
            "fieldtype": "Link",
            "label": "Thai WHT Income Type",
            "insert_after": "tax_deduction_basis",
            "options": "Thai WHT Income Type",
            "translatable": 0,
            "read_only": 1,
            "module": "Print Designer",
        },
    ]
}

TAX_WHITHOLDING_CATEGORY_INSTALL_LIST = [
    "pd_custom_apply_wht_to_contract_installments",
    "pd_custom_thai_wht_income_type",
]


def create_tax_withholding_category_fields():
    """Install custom fields on Tax Withholding Category."""
    try:
        print("Installing Tax Withholding Category custom fields...")
        create_custom_fields(TAX_WITHHOLDING_CATEGORY_CUSTOM_FIELDS, update=True)
        frappe.db.commit()
        for field in TAX_WHITHOLDING_CATEGORY_INSTALL_LIST:
            print(f"   ✅ {field} installed on Tax Withholding Category!")
        return True
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error installing Tax Withholding Category field: {str(e)}")
        frappe.log_error("Tax Withholding Category Field Installation Error", str(e))
        return False


def check_tax_withholding_category_fields():
    """Verify that the custom fields are properly installed."""
    try:
        print("Checking Tax Withholding Category custom fields...")
        all_ok = True
        for fieldname in TAX_WHITHOLDING_CATEGORY_INSTALL_LIST:
            if not frappe.db.exists(
                "Custom Field", {"dt": "Tax Withholding Category", "fieldname": fieldname}
            ):
                print(f"❌ Missing field: {fieldname}")
                all_ok = False
            else:
                print(f"✅ {fieldname} installed")
        return all_ok
    except Exception as e:
        print(f"❌ Error checking Tax Withholding Category field: {str(e)}")
        frappe.log_error("Tax Withholding Category Field Check Error", str(e))
        return False


def uninstall_tax_withholding_category_fields():
    """Remove custom fields from Tax Withholding Category."""
    try:
        print("Removing Tax Withholding Category custom fields...")
        for fieldname in TAX_WHITHOLDING_CATEGORY_INSTALL_LIST:
            custom_field = frappe.db.exists(
                "Custom Field", {"dt": "Tax Withholding Category", "fieldname": fieldname}
            )
            if custom_field:
                frappe.delete_doc("Custom Field", custom_field, force=1)
                print(f"   ✓ Removed {fieldname}")
        frappe.db.commit()
        print(f"✅ Tax Withholding Category custom fields removed!")
        return True
    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error removing Tax Withholding Category field: {str(e)}")
        frappe.log_error("Tax Withholding Category Field Uninstall Error", str(e))
        return False


@click.command("install-tax-withholding-category-fields")
@click.pass_context
def install_tax_withholding_category_fields_cmd(context):
    """Install pd_custom_apply_wht_to_contract_installments field on Tax Withholding Category"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        create_tax_withholding_category_fields()
        frappe.destroy()


@click.command("check-tax-withholding-category-fields")
@click.pass_context
def check_tax_withholding_category_fields_cmd(context):
    """Verify pd_custom_apply_wht_to_contract_installments field installation"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        check_tax_withholding_category_fields()
        frappe.destroy()


@click.command("uninstall-tax-withholding-category-fields")
@click.pass_context
def uninstall_tax_withholding_category_fields_cmd(context):
    """Remove pd_custom_apply_wht_to_contract_installments field from Tax Withholding Category"""
    site = context.obj["sites"][0] if context.obj.get("sites") else None
    if site:
        frappe.init(site=site)
        frappe.connect()
        uninstall_tax_withholding_category_fields()
        frappe.destroy()
