"""
Thai Account Translation Fields Installer for Print Designer

This module installs custom fields to enable Thai translation for Chart of Accounts.
Supports automatic translation of common accounting terms and manual translation for custom accounts.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Main entry point for bench command"""
    install_account_thai_translation_fields()


def install_account_thai_fields():
    """Wrapper function for hooks.py compatibility"""
    return install_account_thai_translation_fields()


def install_account_thai_translation_fields():
    """Install Thai translation fields for Account and Company DocTypes"""

    print("Installing Thai Account Translation Fields...")

    try:
        # Install custom fields
        custom_fields = get_account_thai_custom_fields()
        create_custom_fields(custom_fields, update=True)

        # Fix idx conflicts by positioning fields after all DocFields
        _fix_account_field_positioning()

        # Clear cache to ensure fields appear in UI immediately
        frappe.clear_cache(doctype="Account")
        frappe.clear_cache()

        print("✓ Thai Account Translation fields installed successfully")

        # Auto-populate translations for existing accounts
        print("Auto-populating Thai translations for common accounts...")
        populate_common_thai_account_names()

        print("✓ Thai Account Translation system installation completed")

    except Exception as e:
        print(f"✗ Error installing Thai Account Translation fields: {str(e)}")
        frappe.log_error(f"Thai Account Translation installation error: {str(e)}")


def _fix_account_field_positioning():
    """Fix idx conflicts by positioning Thai fields after all standard DocFields."""

    print("   Fixing Account field positioning to avoid idx conflicts...")

    # Find the highest DocField idx for Account
    max_docfield_idx = frappe.db.sql("""
        SELECT MAX(idx) as max_idx FROM `tabDocField` WHERE parent = 'Account'
    """)[0][0] or 0

    # Account Thai fields in correct order
    account_fields_order = [
        ("account_name_th", "account_name"),
        ("auto_translate_thai", "account_name_th"),
        ("thai_notes", "account_currency")
    ]

    # Position Account fields starting after max DocField idx
    current_idx = max_docfield_idx + 1

    for fieldname, insert_after in account_fields_order:
        custom_field_name = f"Account-{fieldname}"

        if frappe.db.exists('Custom Field', custom_field_name):
            frappe.db.set_value('Custom Field', custom_field_name, {
                'idx': current_idx,
                'insert_after': insert_after
            })
            current_idx += 1

    print(f"   ✓ Positioned Account Thai fields at idx {max_docfield_idx + 1}+ (after DocField max of {max_docfield_idx})")


def get_account_thai_custom_fields():
    """Get custom field definitions for Thai account translation"""

    return {
        "Account": [
            {
                "fieldname": "account_name_th",
                "fieldtype": "Data",
                "label": "Account Name (TH)",
                "insert_after": "account_name",
                "translatable": 1,
                "in_list_view": 1,
                "description": "Thai translation of account name for localized Chart of Accounts display",
            },
            {
                "fieldname": "auto_translate_thai",
                "fieldtype": "Check",
                "label": "Auto Translate to Thai",
                "insert_after": "account_name_th",
                "default": 1,
                "description": "Automatically populate Thai name based on common accounting terms",
            },
            {
                "fieldname": "thai_notes",
                "fieldtype": "Small Text",
                "label": "Thai Translation Notes",
                "insert_after": "account_currency",
                "description": "Notes about Thai translation or accounting context",
            },
        ],
        # "Company": [
        #     {
        #         "fieldname": "accounts_thai_tab",
        #         "fieldtype": "Tab Break",
        #         "label": "Thai Compliance",
        #         "insert_after": "asset_received_but_not_billed",
        #     },
        #     {
        #         "fieldname": "thai_accounting_section",
        #         "fieldtype": "Section Break",
        #         "label": "Thai Accounting Settings",
        #         "insert_after": "accounts_thai_tab",
        #     },
        #     {
        #         "fieldname": "thai_accounting_column_left",
        #         "fieldtype": "Column Break",
        #         "insert_after": "thai_accounting_section",
        #     },
        #     {
        #         "fieldname": "enable_thai_accounting_translation",
        #         "fieldtype": "Check",
        #         "label": "Enable Thai Chart of Accounts Translation",
        #         "insert_after": "thai_accounting_column_left",
        #         "default": 0,
        #         "description": "Show Thai account names in Chart of Accounts tree view",
        #     },
        #     {
        #         "fieldname": "auto_populate_thai_accounts",
        #         "fieldtype": "Button",
        #         "label": "Auto-populate Thai Account Names",
        #         "insert_after": "enable_thai_accounting_translation",
        #         "description": "Automatically translate common account names to Thai",
        #     },
        #     {
        #         "fieldname": "thai_accounting_column_right",
        #         "fieldtype": "Column Break",
        #         "insert_after": "auto_populate_thai_accounts",
        #     },
        # ],
    }


def get_thai_account_translation_map():
    """Pre-defined Thai translations for common account names"""

    return {
        # Assets (สินทรัพย์)
        "Application of Funds (Assets)": "การใช้เงินทุน (สินทรัพย์)",
        "Current Assets": "สินทรัพย์หมุนเวียน",
        "Accounts Receivable": "ลูกหนี้การค้า",
        "Bank": "เงินฝากธนาคาร",
        "Cash": "เงินสด",
        "Cash In Hand": "เงินสดในมือ",
        "Loans and Advances (Assets)": "เงินให้กู้ยืมและเงินทดรองจ่าย",
        "Securities and Deposits": "หลักทรัพย์และเงินมัดจำ",
        "Stock Assets": "สินทรัพย์สินค้า",
        "Stock in Hand": "สินค้าคงเหลือ",
        "Fixed Assets": "สินทรัพย์ถาวร",
        "Capital Equipments": "อุปกรณ์ทุน",
        "Electronic Equipments": "อุปกรณ์อิเล็กทรอนิกส์",
        "Furnitures and Fixtures": "เฟอร์นิเจอร์และติดตั้ง",
        "Office Equipments": "อุปกรณ์สำนักงาน",
        "Plants and Machineries": "โรงงานและเครื่องจักร",
        "Buildings": "อาคาร",
        "Softwares": "ซอฟต์แวร์",
        "Accumulated Depreciation": "ค่าเสื่อมราคาสะสม",
        # Liabilities (หนี้สิน)
        "Source of Funds (Liabilities)": "แหล่งที่มาของเงินทุน (หนี้สิน)",
        "Current Liabilities": "หนี้สินหมุนเวียน",
        "Accounts Payable": "เจ้าหนี้การค้า",
        "Stock Liabilities": "หนี้สินสินค้า",
        "Duties and Taxes": "อากรและภาษี",
        "Output VAT": "ภาษีมูลค่าเพิ่มขาออก",
        "Input VAT": "ภาษีมูลค่าเพิ่มขาเข้า",
        "VAT": "ภาษีมูลค่าเพิ่ม",
        "Payroll Payable": "เงินเดือนค้างจ่าย",
        "Loans (Liabilities)": "เงินกู้ยืม (หนี้สิน)",
        "Secured Loans": "เงินกู้ที่มีหลักประกัน",
        "Unsecured Loans": "เงินกู้ที่ไม่มีหลักประกัน",
        "Bank Overdraft Account": "บัญชีเบิกเกินบัญชีธนาคาร",
        # Income (รายได้)
        "Income": "รายได้",
        "Direct Income": "รายได้ทางตรง",
        "Sales": "ขาย",
        "Service": "บริการ",
        "Sales Income": "รายได้จากการขาย",
        "Service Income": "รายได้จากการให้บริการ",
        "Indirect Income": "รายได้ทางอ้อม",
        "Other Income": "รายได้อื่น",
        # Expenses (ค่าใช้จ่าย)
        "Expenses": "ค่าใช้จ่าย",
        "Direct Expenses": "ค่าใช้จ่ายทางตรง",
        "Cost of Goods Sold": "ต้นทุนขาย",
        "Stock Expenses": "ค่าใช้จ่ายสินค้า",
        "Indirect Expenses": "ค่าใช้จ่ายทางอ้อม",
        "Administrative Expenses": "ค่าใช้จ่ายในการบริหาร",
        "Office Maintenance Expenses": "ค่าใช้จ่ายในการบำรุงรักษาสำนักงาน",
        "Office Rent": "ค่าเช่าสำนักงาน",
        "Postal Expenses": "ค่าไปรษณีย์",
        "Print and Stationery": "ค่าพิมพ์และเครื่องเขียน",
        "Rent": "ค่าเช่า",
        "Salary": "เงินเดือน",
        "Telephone Expenses": "ค่าโทรศัพท์",
        "Travel Expenses": "ค่าเดินทาง",
        "Utility Expenses": "ค่าสาธารณูปโภค",
        "Marketing Expenses": "ค่าใช้จ่ายการตลาด",
        "Legal Expenses": "ค่าใช้จ่ายทางกฎหมาย",
        "Entertainment Expenses": "ค่าใช้จ่ายการรับรอง",
        "Freight and Forwarding Charges": "ค่าขนส่งและค่าบริการขนส่งต่อ",
        "Round Off": "ปัดเศษ",
        "Depreciation": "ค่าเสื่อมราคา",
        "Bank Charges": "ค่าธรรมเนียมธนาคาร",
        "Write Off": "ตัดจำหน่าย",
        "Exchange Gain/Loss": "กำไร/ขาดทุนจากอัตราแลกเปลี่ยน",
        "Gain/Loss on Asset Disposal": "กำไร/ขาดทุนจากการจำหน่ายสินทรัพย์",
        # Equity (ส่วนของเจ้าของ)
        "Equity": "ส่วนของเจ้าของ",
        "Capital Stock": "ทุนจดทะเบียน",
        "Reserves and Surplus": "เงินสำรองทุนและกำไรสะสม",
        "Retained Earnings": "กำไรสะสม",
        "Shareholders Fund": "เงินทุนผู้ถือหุ้น",
        # Thai-specific Accounts
        "Withholding Tax Payable": "ภาษีหัก ณ ที่จ่าย ค้างจ่าย",
        "Withholding Tax Receivable": "ภาษีหัก ณ ที่จ่าย ลูกหนี้",
        "Corporate Income Tax": "ภาษีเงินได้นิติบุคคล",
        "Personal Income Tax": "ภาษีเงินได้บุคคลธรรมดา",
        "VAT Undue": "ภาษีมูลค่าเพิ่มยังไม่ถึงกำหนด",
        "VAT Due": "ภาษีมูลค่าเพิ่มถึงกำหนด",
        "Social Security Fund": "กองทุนประกันสังคม",
        "Provident Fund": "กองทุนสำรองเลี้ยงชีพ",
    }


def populate_common_thai_account_names():
    """Auto-populate Thai account names for common accounts"""

    try:
        translation_map = get_thai_account_translation_map()
        accounts_updated = 0

        # Get all accounts that match our translation map
        for english_name, thai_name in translation_map.items():
            accounts = frappe.get_all(
                "Account",
                filters={
                    "account_name": english_name,
                    "account_name_th": ["in", ["", None]],  # Only update if Thai name is empty
                },
                fields=["name", "account_name"],
            )

            for account in accounts:
                try:
                    frappe.db.set_value(
                        "Account",
                        account.name,
                        {"account_name_th": thai_name, "auto_translate_thai": 1},
                    )
                    accounts_updated += 1
                except Exception as e:
                    print(f"   Warning: Could not update {account.account_name}: {str(e)}")

        frappe.db.commit()
        print(f"✓ Auto-populated Thai names for {accounts_updated} accounts")

    except Exception as e:
        print(f"✗ Error auto-populating Thai account names: {str(e)}")
        frappe.log_error(f"Thai account auto-population error: {str(e)}")


def check_account_thai_fields():
    """Check if Thai account translation fields are installed"""

    print("Checking Thai Account Translation fields installation...")

    try:
        # Check Account fields only (Company fields moved to install_company_thai_tax_fields.py)
        account_fields = [
            "account_name_th",
            "auto_translate_thai",
            "thai_notes",
        ]

        all_fields_exist = True
        for field in account_fields:
            if frappe.db.exists("Custom Field", f"Account-{field}"):
                print(f"✓ Account.{field} - Installed")
            else:
                print(f"✗ Account.{field} - Missing")
                all_fields_exist = False

        # Check for Thai translations
        thai_accounts = frappe.db.count("Account", {"account_name_th": ["!=", ""]})
        print(f"ℹ {thai_accounts} accounts have Thai translations")

        return all_fields_exist

    except Exception as e:
        print(f"✗ Error checking Thai account fields: {str(e)}")
        return False


def remove_account_thai_fields():
    """Remove Thai account translation fields (for testing/cleanup)"""

    print("Removing Thai Account Translation fields...")

    try:
        # Remove Account custom fields only (Company fields removed via install_company_thai_tax_fields.py)
        account_fields = [
            "Account-account_name_th",
            "Account-auto_translate_thai",
            "Account-thai_notes",
        ]

        removed_count = 0
        for field_name in account_fields:
            if frappe.db.exists("Custom Field", field_name):
                frappe.delete_doc("Custom Field", field_name)
                print(f"✓ Removed {field_name}")
                removed_count += 1
            else:
                print(f"⏭️ {field_name} not found (already removed)")

        frappe.db.commit()
        print(f"✓ Successfully removed {removed_count} Thai Account Translation fields")

    except Exception as e:
        print(f"✗ Error removing Thai account fields: {str(e)}")
        frappe.db.rollback()
        raise


# API Methods for Company form button
@frappe.whitelist()
def auto_populate_company_thai_accounts(company):
    """API method to auto-populate Thai account names for a specific company"""

    try:
        translation_map = get_thai_account_translation_map()
        accounts_updated = 0

        # Get accounts for this company only
        for english_name, thai_name in translation_map.items():
            accounts = frappe.get_all("Account",
                filters={
                    "company": company,
                    "account_name": english_name
                },
                fields=["name", "account_name", "account_name_th"]
            )

            for account in accounts:
                # Update if Thai name is empty or user wants to refresh
                frappe.db.set_value("Account", account.name, {
                    "account_name_th": thai_name,
                    "auto_translate_thai": 1,
                    "thai_notes": "Auto-populated by Print Designer"
                })
                accounts_updated += 1

        frappe.db.commit()

        frappe.msgprint(
            _("Successfully updated Thai names for {0} accounts").format(accounts_updated),
            title=_("Thai Translation Complete"),
            indicator="green"
        )

        return {"status": "success", "accounts_updated": accounts_updated}

    except Exception as e:
        frappe.throw(_("Error auto-populating Thai account names: {0}").format(str(e)))


# Thai Accounting Translation Manager Class
class ThaiAccountTranslationManager:
    """Manager class for Thai account translation functionality"""

    @staticmethod
    def enable_thai_translation(company):
        """Enable Thai translation for accounts in a company"""

        # Set company preference
        frappe.db.set_value("Company", company, "enable_thai_accounting_translation", 1)

        # Auto-populate if not already done
        ThaiAccountTranslationManager.populate_thai_account_names(company)

        frappe.msgprint(
            _("Thai account translation enabled for {0}").format(company),
            title=_("Thai Translation Enabled"),
            indicator="green"
        )

    @staticmethod
    def disable_thai_translation(company):
        """Disable Thai translation for accounts in a company"""

        # Set company preference
        frappe.db.set_value("Company", company, "enable_thai_accounting_translation", 0)

        frappe.msgprint(
            _("Thai account translation disabled for {0}").format(company),
            title=_("Thai Translation Disabled"),
            indicator="blue"
        )

    @staticmethod
    def populate_thai_account_names(company):
        """Auto-populate Thai account names for a specific company"""

        translation_map = get_thai_account_translation_map()
        accounts_updated = 0

        for english_name, thai_name in translation_map.items():
            accounts = frappe.get_all("Account",
                filters={
                    "company": company,
                    "account_name": english_name,
                    "account_name_th": ["in", ["", None]]
                },
                fields=["name", "account_name"]
            )

            for account in accounts:
                frappe.db.set_value("Account", account.name, {
                    "account_name_th": thai_name,
                    "auto_translate_thai": 1
                })
                accounts_updated += 1

        frappe.db.commit()
        return accounts_updated


# Bench Commands
def install_account_thai_fields():
    """Bench command: install-account-thai-fields"""
    install_account_thai_translation_fields()


def check_account_thai_fields_status():
    """Bench command: check-account-thai-fields"""
    check_account_thai_fields()


def remove_account_thai_translation_fields():
    """Bench command: remove-account-thai-fields (for testing)"""
    remove_account_thai_fields()
