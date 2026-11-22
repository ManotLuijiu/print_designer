# Copyright (c) 2026, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

"""The settings of the Thai tax.

The behaviour of this controller comes from the controller of Thai Business
Suite.  Two parts of the old behaviour could not work against the metadata of
the doctype, and they are written differently here:

- the accounts of the tax are not fields of the doctype, so the check of
  their type only runs when the doctype carries the fields, and the creation
  of the accounts refuses when the created account could not be remembered,
- the row of a rate of the withholding tax has no field named ``rate``, so
  the rates are read from the fields that the row really has.

The dependency on Thai Business Suite is not there: the authorization of the
endpoints is the one of Print Designer.
"""

from collections.abc import Callable
from typing import Any, cast

import frappe
from frappe import _
from frappe.defaults import get_user_default
from frappe.model.document import Document
from frappe.utils import cint, flt

from print_designer.custom.document_permission import require_doctype_permission
from print_designer.custom.maintenance_access import require_system_manager

CACHE_KEY = "thai_tax_settings"

# The accounts of the tax, the types they may have and the label of the
# message of a wrong type.
ACCOUNT_VALIDATIONS = (
    (
        "default_wht_payable_account",
        ("Payable", "Tax"),
        _("Default WHT Payable Account"),
    ),
    (
        "default_wht_receivable_account",
        ("Receivable", "Tax"),
        _("Default WHT Receivable Account"),
    ),
    ("default_vat_input_account", ("Tax",), _("Default VAT Input Account")),
    ("default_vat_output_account", ("Tax",), _("Default VAT Output Account")),
)

# The accounts that are created when the settings ask for it, with the type
# of the account and the field that remembers it.
ACCOUNTS_TO_CREATE = (
    ("WHT Payable", "Tax", "default_wht_payable_account"),
    ("WHT Receivable", "Tax", "default_wht_receivable_account"),
    ("VAT Input", "Tax", "default_vat_input_account"),
    ("VAT Output", "Tax", "default_vat_output_account"),
)

# The rate of the withholding tax of an income type, when the settings carry
# no rate for that income type.
DEFAULT_WHT_RATES = {
    "Service Income": 3.0,
    "Professional Service": 5.0,
    "Rental Income": 5.0,
    "Transport Service": 1.0,
    "Construction Service": 3.0,
    "Other Service": 3.0,
}

# The rate that is used when nothing else is known about the income type.
FALLBACK_WHT_RATE = 3.0

# The fields of a row of a rate that hold a percentage.
RATE_FIELDS = ("tax_rate", "individual_rate", "company_rate", "government_rate")

# The installers of the fields of the Thai tax.  Every one of them is
# idempotent, so the list may be run again.
THAI_TAX_FIELD_INSTALLERS = (
    (
        "print_designer.commands.install_company_thai_tax_fields",
        "install_company_thai_tax_fields",
    ),
    (
        "print_designer.commands.install_employee_thai_tax_fields",
        "install_employee_thai_tax_fields",
    ),
    (
        "print_designer.commands.install_sales_invoice_fields",
        "install_sales_invoice_custom_fields",
    ),
    (
        "print_designer.commands.install_purchase_invoice_fields",
        "install_purchase_invoice_thai_tax_fields",
    ),
    ("print_designer.commands.install_purchase_order_fields", "execute"),
    (
        "print_designer.commands.install_sales_order_fields",
        "install_sales_order_custom_fields",
    ),
    (
        "print_designer.commands.install_quotation_fields",
        "install_quotation_custom_fields",
    ),
)

# The doctypes that carry the fields of the Thai tax.
THAI_TAX_DOCTYPES = (
    "Company",
    "Employee",
    "Item",
    "Payment Entry",
    "Purchase Invoice",
    "Purchase Order",
    "Quotation",
    "Sales Invoice",
    "Sales Order",
)


class ThaiTaxSettings(Document):
    """The settings of the Thai tax of a site."""

    def validate(self) -> None:
        """Check the accounts and the rates of the settings."""
        self.validate_account_types()
        self.validate_wht_rates()

    def on_update(self) -> None:
        """Create the accounts of the tax and forget the cached settings."""
        if _the_value(self, "auto_create_accounts"):
            self.create_default_thai_accounts()

        cache = frappe.cache

        if cache:
            cache.delete_key(CACHE_KEY)

    def validate_account_types(self) -> None:
        """The accounts of the tax must have the type that they may have.

        The doctype does not carry the accounts on every site, so the check
        only runs for the fields that the doctype really has.
        """
        for fieldname, account_types, label in ACCOUNT_VALIDATIONS:
            account = _the_value(self, fieldname)

            if not account:
                continue

            account_type = frappe.db.get_value("Account", account, "account_type")

            if account_type not in account_types:
                frappe.throw(
                    _("{0} must be of account type: {1}").format(label, ", ".join(account_types))
                )

    def validate_wht_rates(self) -> None:
        """The rates of the withholding tax are percentages."""
        for rate in _the_value(self, "default_wht_rates") or []:
            for value in _the_rates_of_the_row(rate):
                if value < 0 or value > 100:
                    frappe.throw(_("WHT rate must be between 0 and 100 percent"))

    def create_default_thai_accounts(self) -> None:
        """Create the accounts of the tax and remember them in the settings.

        The account can only be remembered when the doctype carries the
        field of the account.  Without that field the account would be
        created again on every save, so the creation refuses instead.
        """
        company = get_user_default("Company") or frappe.db.get_single_value(
            "Global Defaults", "default_company"
        )

        if not company:
            frappe.throw(_("Please set a default company to create Thai tax accounts"))

        created_accounts = []

        for account_name, account_type, fieldname in ACCOUNTS_TO_CREATE:
            if _the_value(self, fieldname):
                continue

            if not self._carries(fieldname):
                frappe.throw(
                    _(
                        "The settings do not carry the field {0}. The accounts of "
                        "the tax cannot be created."
                    ).format(fieldname)
                )

            account = self.create_account(cast(str, company), account_name, account_type)

            if account:
                self.db_set(fieldname, account.name, update_modified=False)
                created_accounts.append(account.name)

        if created_accounts:
            frappe.msgprint(
                _("Created Thai tax accounts: {0}").format(", ".join(created_accounts)),
                title=_("Thai Tax Accounts Created"),
                indicator="green",
            )

    def _carries(self, fieldname: str) -> bool:
        """Whether the doctype carries the field."""
        return bool(frappe.get_meta(self.doctype).has_field(fieldname))

    def get_parent_account(self, company: str, account_type: str) -> str | None:
        """The account of the company that may hold the accounts of the tax."""
        parent_account = frappe.db.get_value(
            "Account",
            {
                "company": company,
                "account_type": account_type,
                "is_group": 1,
                "parent_account": ("!=", ""),
            },
            "name",
            order_by="name",
        )

        if parent_account:
            return cast(str, parent_account)

        return cast(
            "str | None",
            frappe.db.get_value(
                "Account",
                {"company": company, "parent_account": "", "is_group": 1},
                "name",
            ),
        )

    def create_account(self, company: str, account_name: str, account_type: str) -> Any:
        """The account of the tax of the company, created when it is missing."""
        full_name = f"{account_name} - {company}"

        if frappe.db.exists("Account", full_name):
            return frappe.get_doc("Account", full_name)

        parent_account = self.get_parent_account(company, account_type)

        if not parent_account:
            frappe.log_error(
                f"Error creating account {full_name}: no parent account",
                "Thai Tax Settings",
            )
            return None

        try:
            account = frappe.get_doc(
                {
                    "doctype": "Account",
                    "account_name": account_name,
                    "parent_account": parent_account,
                    "company": company,
                    "account_type": account_type,
                    "is_group": 0,
                    "freeze_account": 0,
                    "account_currency": frappe.db.get_value("Company", company, "default_currency")
                    or "THB",
                }
            )
            account.insert(ignore_permissions=True)
            return account
        except Exception as error:
            frappe.log_error(
                f"Error creating account {full_name}: {str(error)}",
                "Thai Tax Settings",
            )
            return None


def _the_value(document: Any, fieldname: str) -> Any:
    """The value of a field of a document.

    The fields of a document are added by the doctype, so the type checker
    cannot know the shape of a value of a field.  The cast narrows the value
    for the type checker; it changes nothing at runtime.

    Args:
        document: the document that carries the field.
        fieldname: the name of the field.

    Returns:
        The value of the field, or nothing when the document does not carry
        the field.
    """
    return cast(Any, document.get(fieldname))


def _the_value_of(row: Any, fieldname: str) -> Any:
    """The value of a field of a row.

    A row of a table is a document of Frappe, and a document is not a
    mapping, so the value is read with the ``get`` of the row itself.

    Args:
        row: the row that carries the field.
        fieldname: the name of the field.

    Returns:
        The value of the field, or nothing when the row does not carry the
        field.
    """
    getter = getattr(row, "get", None)

    if not callable(getter):
        return None

    return getter(fieldname)


def _the_rates_of_the_row(rate: Any) -> list[float]:
    """The percentages that the row of a rate carries."""
    return [flt(_the_value_of(rate, fieldname)) for fieldname in RATE_FIELDS]


def _the_rate_of_the_row(rate: Any) -> float:
    """The rate of the row, the rate of the row first, then the rate of the
    individual."""
    for fieldname in ("tax_rate", "individual_rate"):
        value = flt(_the_value_of(rate, fieldname))

        if value:
            return value

    return 0.0


@frappe.whitelist()
def get_thai_tax_settings() -> dict[str, Any]:
    """The values of the settings of the Thai tax.

    The values are read with ``get``, so that a doctype that does not carry
    every field answers with the value it has and with nothing for the rest.
    """
    require_doctype_permission("Thai Tax Settings", "read")

    settings = frappe.get_cached_doc("Thai Tax Settings")

    return {
        "auto_apply_thai_format": cint(_the_value(settings, "auto_apply_thai_format")),
        "enable_withholding_tax": cint(_the_value(settings, "enable_withholding_tax")),
        "auto_create_accounts": cint(_the_value(settings, "auto_create_accounts")),
        "auto_calculate_vat": cint(_the_value(settings, "auto_calculate_vat")),
        "auto_generate_pnd_reports": cint(_the_value(settings, "auto_generate_pnd_reports")),
        "enable_pnd1": cint(_the_value(settings, "enable_pnd1")),
        "enable_pnd3": cint(_the_value(settings, "enable_pnd3")),
        "enable_pnd53": cint(_the_value(settings, "enable_pnd53")),
        "vat_rate": flt(_the_value(settings, "vat_rate")),
        "default_tax_branch_code": _the_value(settings, "default_tax_branch_code"),
        "wht_certificate_numbering_series": _the_value(
            settings, "wht_certificate_numbering_series"
        ),
        "default_wht_payable_account": _the_value(settings, "default_wht_payable_account"),
        "default_wht_receivable_account": _the_value(settings, "default_wht_receivable_account"),
        "default_vat_input_account": _the_value(settings, "default_vat_input_account"),
        "default_vat_output_account": _the_value(settings, "default_vat_output_account"),
    }


@frappe.whitelist(methods=["POST"])
def create_thai_tax_accounts(company: str | None = None) -> str:
    """Create the accounts of the Thai tax of a company."""
    require_system_manager("create the accounts of the tax")

    if not company:
        company = cast("str | None", get_user_default("Company"))

    if not company:
        frappe.throw(_("Please specify a company"))

    settings = cast(ThaiTaxSettings, frappe.get_doc("Thai Tax Settings"))
    settings.set("auto_create_accounts", 1)
    settings.create_default_thai_accounts()

    return _("Thai tax accounts created successfully")


@frappe.whitelist()
def get_thai_wht_rate(income_type: str) -> float:
    """The rate of the withholding tax of an income type.

    The rate of the settings is used when the settings carry one for the
    income type, and the rate of the law of Thailand is used otherwise.
    """
    require_doctype_permission("Thai Tax Settings", "read")

    settings = frappe.get_cached_doc("Thai Tax Settings")

    for rate_setting in _the_value(settings, "default_wht_rates") or []:
        if _the_value_of(rate_setting, "income_type") == income_type:
            return _the_rate_of_the_row(rate_setting)

    return DEFAULT_WHT_RATES.get(income_type, FALLBACK_WHT_RATE)


@frappe.whitelist(methods=["POST"])
def install_thai_tax_fields() -> str:
    """Install the fields of the Thai tax.

    Every installer of the list is idempotent, so the command may be run
    again.
    """
    require_system_manager("install the fields of the tax")

    for module_name, function_name in THAI_TAX_FIELD_INSTALLERS:
        _the_installer(module_name, function_name)()

    return _("Thai tax fields installation completed successfully")


def _the_installer(module_name: str, function_name: str) -> Callable[[], Any]:
    """The installer of the fields, imported when it is needed."""
    module = __import__(module_name, fromlist=[function_name])

    return getattr(module, function_name)


@frappe.whitelist()
def check_thai_tax_system() -> dict[str, Any]:
    """The state of the Thai tax of the site.

    The answer carries the state of the settings and the number of the
    fields of the Thai tax that every doctype carries.
    """
    require_doctype_permission("Thai Tax Settings", "read")

    settings = frappe.get_single("Thai Tax Settings")

    result: dict[str, Any] = {
        "thai_tax_settings_exists": frappe.db.exists("Thai Tax Settings"),
        "total_fields": 0,
        "installed_fields": 0,
        "missing_fields": [],
        "configured_accounts": {},
        "fields_per_doctype": {},
        "status": "checking",
    }

    result["configured_accounts"] = {
        "wht_payable": _the_value(settings, "default_wht_payable_account") or None,
        "wht_receivable": _the_value(settings, "default_wht_receivable_account") or None,
        "vat_input": _the_value(settings, "default_vat_input_account") or None,
        "vat_output": _the_value(settings, "default_vat_output_account") or None,
    }

    for doctype in THAI_TAX_DOCTYPES:
        installed = frappe.db.count(
            "Custom Field",
            filters={"dt": doctype, "fieldname": ("like", "pd_custom%")},
        )

        result["fields_per_doctype"][doctype] = installed
        result["total_fields"] += installed
        result["installed_fields"] += installed

    result["status"] = "complete"
    result["all_fields_installed"] = result["total_fields"] > 0
    result["accounts_configured"] = all(result["configured_accounts"].values())

    return result
