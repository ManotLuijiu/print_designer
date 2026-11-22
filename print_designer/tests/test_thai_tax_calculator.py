"""The tests of the calculator of the Thai withholding tax.

The calculator of Print Designer holds the behaviour of the tax calculator of
Thai Business Suite.  The tests create a disposable rate and a disposable
supplier inside a savepoint that is rolled back at the end, so that the site
keeps no row of the test.
"""

import unittest
from typing import Any, cast

import frappe
from frappe.utils import today

from print_designer.custom.thai_tax_calculator import (
    calculate_withholding_tax,
    get_party_address,
    get_pnd_type_from_income_type,
    get_wht_rate_from_setting,
    get_wht_settings_for_party,
    get_withholding_tax_rate,
    validate_thai_tax_data,
    validate_thai_tax_id,
)

SAVEPOINT = "tvr_tax_calculator_test"

# The income types of the law of Thailand, with the rate and the form.
SERVICE_INCOME = "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ"
SALARY_INCOME = "40(1) เงินเดือน ค่าจ้าง"
ADVERTISING_INCOME = "40(8) ค่าโฆษณา 2%"


class TestTheThaiTaxCalculator(unittest.TestCase):
    """The calculator of the withholding tax of Thailand."""

    def setUp(self):
        frappe.db.savepoint(SAVEPOINT)

    def tearDown(self):
        frappe.db.rollback(save_point=SAVEPOINT)

    def _the_rate_row(self, income_type: str, tax_rate: float, **extra: Any) -> Any:
        """A disposable row of the rates of the withholding tax.

        The `Thai WHT Rate Setting` is a table of the settings of the tax, so
        the row is added to the settings of the site and the savepoint of the
        test takes it away again.
        """
        settings = frappe.get_single("Thai Tax Settings")
        row = settings.append("default_wht_rates", None)
        row.income_type = income_type
        row.income_code = "TEST"
        row.entity_type = "All"
        row.pnd_type = "PND3"
        row.tax_rate = tax_rate
        row.is_active = 1
        row.effective_from = today()
        for key, value in extra.items():
            row.set(key, value)
        settings.save()
        return row

    def test_the_rate_of_the_law_is_the_fallback_of_a_site_without_a_rate(self):
        """A site without a rate uses the rate of the law of Thailand."""
        self.assertEqual(get_withholding_tax_rate(SERVICE_INCOME), 3.0)
        self.assertEqual(get_withholding_tax_rate(SALARY_INCOME), 5.0)
        self.assertEqual(get_withholding_tax_rate(ADVERTISING_INCOME), 2.0)

    def test_the_rate_of_the_site_wins_over_the_rate_of_the_law(self):
        """The rate of the `Thai WHT Rate Setting` is the rate of the site."""
        self._the_rate_row(SERVICE_INCOME, 7.5)
        self.assertEqual(get_withholding_tax_rate(SERVICE_INCOME), 7.5)

    def test_the_rate_of_an_income_type_without_a_rate_is_zero(self):
        """An income type without a rate has no rate."""
        self.assertEqual(get_withholding_tax_rate(""), 0.0)
        self.assertEqual(get_withholding_tax_rate("40(9) unknown"), 0.0)

    def test_the_amount_of_the_withholding_tax(self):
        """The amount of the withholding tax is the rate of the amount."""
        self.assertEqual(calculate_withholding_tax(1000, SERVICE_INCOME), 30.0)
        self.assertEqual(calculate_withholding_tax(1000, SERVICE_INCOME, 5), 50.0)

    def test_the_amount_of_the_withholding_tax_of_nothing_is_zero(self):
        """An amount of nothing has no withholding tax."""
        self.assertEqual(calculate_withholding_tax(0, SERVICE_INCOME), 0.0)
        self.assertEqual(calculate_withholding_tax(None, SERVICE_INCOME), 0.0)
        self.assertEqual(calculate_withholding_tax(-100, SERVICE_INCOME), 0.0)

    def test_the_form_of_the_withholding_tax_of_an_income_type(self):
        """The form of the withholding tax follows the income type."""
        self.assertEqual(get_pnd_type_from_income_type(SALARY_INCOME), "PND1")
        self.assertEqual(get_pnd_type_from_income_type(SERVICE_INCOME), "PND3")
        self.assertEqual(get_pnd_type_from_income_type(ADVERTISING_INCOME), "PND53")
        self.assertIsNone(get_pnd_type_from_income_type("40(9) unknown"))
        self.assertIsNone(get_pnd_type_from_income_type(""))

    def test_the_tax_identification_number_of_thailand(self):
        """The check digit of the tax identification number is checked."""
        self.assertTrue(validate_thai_tax_id("1101700111113"))
        self.assertFalse(validate_thai_tax_id("1101700111112"))
        self.assertFalse(validate_thai_tax_id("110170011111"))
        self.assertFalse(validate_thai_tax_id("110170011111a"))
        self.assertFalse(validate_thai_tax_id(""))

    def test_the_rate_of_a_setting_that_is_not_yet_effective(self):
        """A rate that is not yet effective is not the rate of the site."""
        self._the_rate_row(SERVICE_INCOME, 9.0, effective_from="2999-01-01")
        self.assertEqual(get_wht_rate_from_setting(SERVICE_INCOME, "Company", None), 3.0)

    def test_the_rate_of_a_setting_that_is_effective(self):
        """A rate that is effective is the rate of the site."""
        self._the_rate_row(SERVICE_INCOME, 8.0, effective_from="2000-01-01")
        self.assertEqual(get_wht_rate_from_setting(SERVICE_INCOME, "Company", None), 8.0)

    def test_the_rate_of_the_kind_of_the_party(self):
        """The rate of the row follows the kind of the party."""
        self._the_rate_row(
            SERVICE_INCOME,
            1.0,
            individual_rate=2.0,
            company_rate=3.0,
            government_rate=4.0,
            effective_from="2000-01-01",
        )
        self.assertEqual(get_wht_rate_from_setting(SERVICE_INCOME, "Individual", None), 2.0)
        self.assertEqual(get_wht_rate_from_setting(SERVICE_INCOME, "Company", None), 3.0)
        self.assertEqual(get_wht_rate_from_setting(SERVICE_INCOME, "Government", None), 4.0)

    def test_the_settings_of_a_supplier_of_the_government(self):
        """The group of the supplier carries the kind of the party."""
        group = frappe.get_doc(
            {"doctype": "Supplier Group", "supplier_group_name": "Calculator Test Government"}
        ).insert(ignore_permissions=True)

        supplier = frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": "Calculator Test Government",
                "supplier_group": group.name,
                "tax_id": "1101700111113",
            }
        ).insert(ignore_permissions=True)

        settings = get_wht_settings_for_party("Supplier", supplier.name, None)
        self.assertEqual(settings["entity_type"], "Government")
        self.assertEqual(settings["wht_rate"], 0.0)

    def test_the_settings_of_a_supplier_without_a_group(self):
        """A supplier without a group is a company."""
        supplier = frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": "Calculator Test Company",
                "tax_id": "1101700111113",
            }
        ).insert(ignore_permissions=True)

        settings = get_wht_settings_for_party("Supplier", supplier.name, None)
        self.assertEqual(settings["entity_type"], "Company")

    def test_the_settings_of_nothing_are_the_settings_of_a_company(self):
        """A party of nothing has the settings of a company."""
        settings = get_wht_settings_for_party("Supplier", None, None)
        self.assertEqual(settings["entity_type"], "Company")
        self.assertEqual(settings["wht_rate"], 0.0)
        self.assertIsNone(settings["income_type"])

    def test_the_address_of_a_party(self):
        """The address of a party is the text of its address."""
        address = frappe.get_doc(
            {
                "doctype": "Address",
                "address_title": "Calculator Test Address",
                "address_type": "Billing",
                "address_line1": "1 Test Road",
                "city": "Bangkok",
                "country": "Thailand",
            }
        )

        supplier = frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": "Calculator Test Address Supplier",
                "tax_id": "1101700111113",
            }
        ).insert(ignore_permissions=True)

        address.append("links", {"link_doctype": "Supplier", "link_name": supplier.name})
        address.insert(ignore_permissions=True)

        supplier.set("supplier_primary_address", address.name)
        supplier.save()

        self.assertEqual(
            get_party_address("Supplier", supplier.name), "1 Test Road, Bangkok, Thailand"
        )
        self.assertEqual(get_party_address("Supplier", None), "")
        self.assertEqual(get_party_address("Supplier", "no-such-supplier"), "")

    def test_the_check_of_the_tax_of_a_document(self):
        """The amount of the withholding tax of a document is checked."""
        document = frappe._dict(
            {
                "tax_id": "1101700111113",
                "apply_wht": 1,
                "paid_amount": 1000,
                "income_type": SERVICE_INCOME,
                "wht_rate": 3,
                "wht_amount": 30,
            }
        )
        self.assertTrue(validate_thai_tax_data(document))

    def test_the_check_of_the_tax_of_a_document_refuses_a_wrong_amount(self):
        """A document whose withholding tax is wrong is refused."""
        document = frappe._dict(
            {
                "tax_id": "1101700111113",
                "apply_wht": 1,
                "paid_amount": 1000,
                "income_type": SERVICE_INCOME,
                "wht_rate": 3,
                "wht_amount": 10,
            }
        )
        with self.assertRaises(frappe.ValidationError):
            validate_thai_tax_data(document)

    def test_the_check_of_the_tax_of_a_document_refuses_a_wrong_tax_id(self):
        """A document whose tax identification number is wrong is refused."""
        document = frappe._dict({"tax_id": "1101700111112"})
        with self.assertRaises(frappe.ValidationError):
            validate_thai_tax_data(document)

    def test_the_old_path_of_thai_business_suite_is_the_path_of_print_designer(self):
        """The old path of Thai Business Suite holds no behaviour of its own."""
        from thai_business_suite.thai_tax.utils import tax_calculator

        self.assertIs(
            cast(Any, tax_calculator.get_withholding_tax_rate),
            get_withholding_tax_rate,
        )
        self.assertIs(
            cast(Any, tax_calculator.calculate_withholding_tax),
            calculate_withholding_tax,
        )

    def test_the_old_path_carries_every_name_of_the_callers(self):
        """Every name that the callers of Thai Business Suite use is there."""
        from thai_business_suite.thai_tax.utils import tax_calculator

        for name in (
            "calculate_withholding_tax",
            "create_withholding_tax_certificate",
            "get_party_address",
            "get_pnd_type_from_income_type",
            "get_thai_tax_settings",
            "get_withholding_tax_rate",
            "get_wht_rate_from_setting",
            "get_wht_settings_for_party",
            "validate_thai_tax_data",
            "validate_thai_tax_id",
        ):
            self.assertTrue(hasattr(tax_calculator, name), f"the old path has no {name}")
