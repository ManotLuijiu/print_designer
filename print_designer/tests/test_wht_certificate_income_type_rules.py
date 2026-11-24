"""The tests of the rules of the income type of the certificate.

The certificate of the withholding tax carries one income type of its own and
one income type for every row of its incomes.  These tests hold the rules
that decide them:

- the income type of the certificate is the type of the transaction, the name
  of a `Thai WHT Income Type` or the name of a `Tax Withholding Category` of
  ERPNext,
- a row of the incomes keeps its own type when it carries one,
- the rate of the certificate is the rate of the income type of the
  transaction, the rate of the catalogue of that income type, and an income
  type that carries no rate falls back to the rate of the first row,
- a party that is not a supplier has no tax id and no address.

The tests read the site.  The one test that needs a category of ERPNext
creates it inside a savepoint that is rolled back at the end, so that the
site keeps no row of the test.
"""

import unittest
from typing import Any

import frappe
from frappe.utils import nowdate

from print_designer.custom import wht_canonical_mapping as mapping
from print_designer.custom import wht_certificate_creator as creator

SAVEPOINT = "wht_income_type_rules_test"

#: The kind of the payee of the tests.
THE_ENTITY = "Company"

#: The line of a service that is paid to a company.
COMPANY_SERVICE_LINE = "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service"

#: The line of a rent that is paid to a company.
COMPANY_RENT_LINE = "9. ค่าเช่า - Rent"

#: The row of the income of a rent.
RENT_ITEM_LINE = "40(5) ค่าเช่า"

#: The row of the income of a service of a company.
COMPANY_SERVICE_ITEM_LINE = "40(8) ค่าบริการนิติบุคคล 3%"

#: The rows of a transaction that carries two kinds of income.
THE_ROWS = [
    {"tbs_income_type": None, "rate": 3, "tax_amount": 30, "gross_amount": 1000},
    {"tbs_income_type": None, "rate": 5, "tax_amount": 50, "gross_amount": 1000},
]


class TestTheRulesOfTheIncomeType(unittest.TestCase):
    """The rules that decide the income type of the certificate."""

    def setUp(self):
        frappe.db.savepoint(SAVEPOINT)

    def tearDown(self):
        frappe.db.rollback(save_point=SAVEPOINT)

    def _the_supplier(self) -> str:
        """A supplier of the site."""
        the_supplier = frappe.db.get_value("Supplier", {}, "name")
        if not the_supplier:
            self.skipTest("the site has no supplier")

        return str(the_supplier)

    def _the_income_type(self, the_category: str, the_form: str = "PND53") -> str:
        """The record of an income type of the site.

        The kind of the recipient is part of the key of the map of the
        certificate, so the record is looked for with it.
        """
        the_name = frappe.db.get_value(
            "Thai WHT Income Type",
            {
                "income_category": the_category,
                "form_type": the_form,
                "recipient_type": "Corporation",
            },
            "name",
        )
        if not the_name:
            self.skipTest(f"the site has no income type of {the_category}")

        return str(the_name)

    def _the_payment_entry(self, **overrides: Any) -> Any:
        """A payment entry that pays a supplier."""
        the_values: dict[str, Any] = {
            "doctype": "Payment Entry",
            "name": "PE-THE-RULES",
            "posting_date": nowdate(),
            "company": frappe.db.get_value("Company", {"is_group": 0}, "name"),
            "party_type": "Supplier",
            "party": self._the_supplier(),
            "party_name": frappe.db.get_value("Supplier", {}, "supplier_name"),
        }
        the_values.update(overrides)

        return frappe._dict(the_values)

    def _the_certificate(self, the_payment_entry: Any, the_rows: list[Any] | None = None):
        """The values of the certificate of a payment entry."""
        the_items = creator.build_income_items(the_payment_entry, the_rows or THE_ROWS, THE_ENTITY)

        return creator.build_certificate_values(the_payment_entry, the_items, THE_ENTITY)

    def _the_options(self) -> set[str]:
        """The options of the income type of the certificate."""
        field = frappe.get_meta(creator.CERTIFICATE_DOCTYPE).get_field("income_type")
        if not field:
            raise AssertionError("the certificate has no income_type field")

        return {option.strip() for option in field.options.split("\n") if option.strip()}

    # ------------------------------------------------------------------
    # the income type of the certificate
    # ------------------------------------------------------------------
    def test_the_income_type_of_the_certificate_is_the_type_of_the_transaction(self):
        """The type of the transaction decides the type of the certificate."""
        the_rental = self._the_income_type("Rental Income")
        the_payment_entry = self._the_payment_entry(pd_custom_wht_income_type=the_rental)

        the_values = self._the_certificate(the_payment_entry)

        self.assertEqual(the_values.get("income_type"), COMPANY_RENT_LINE)
        self.assertEqual(the_values.get("pnd_form_type"), "PND53 Form")

    def test_the_category_of_erpn_ext_decides_the_type_of_the_certificate(self):
        """The category of ERPNext decides the type of the certificate."""
        if not frappe.get_meta("Tax Withholding Category").has_field(
            "pd_custom_thai_wht_income_type"
        ):
            self.skipTest("the site has no link to the income type of the category")

        the_service = self._the_income_type("Service Fees")
        the_category = frappe.get_doc(
            {
                "doctype": "Tax Withholding Category",
                "name": "The Category Of The Rules",
                "category_name": "The Category Of The Rules",
                "pd_custom_thai_wht_income_type": the_service,
            }
        )
        the_category.flags.ignore_mandatory = True
        the_category.insert()

        the_payment_entry = self._the_payment_entry(pd_custom_wht_income_type=the_category.name)
        the_values = self._the_certificate(the_payment_entry)

        self.assertEqual(the_values.get("income_type"), COMPANY_SERVICE_LINE)
        self.assertEqual(the_values.get("pnd_form_type"), "PND53 Form")

    def test_without_a_type_of_the_transaction_the_line_is_the_default(self):
        """Without a type of the transaction the line is the default."""
        the_payment_entry = self._the_payment_entry()

        the_values = self._the_certificate(the_payment_entry)

        self.assertEqual(the_values.get("income_type"), COMPANY_SERVICE_LINE)

    def test_every_record_of_the_catalogue_has_a_line_of_the_certificate(self):
        """Every record of the catalogue of the site has a line."""
        the_options = self._the_options()
        the_records = frappe.get_all("Thai WHT Income Type", pluck="name", limit=200)

        if not the_records:
            self.skipTest("the site has no income type")

        for the_name in the_records:
            the_resolved = mapping.resolve_income_type(str(the_name), THE_ENTITY)
            self.assertTrue(
                the_resolved.get("income_type"),
                f"the record {the_name} has no line of the certificate",
            )
            self.assertIn(
                the_resolved.get("income_type"),
                the_options,
                f"the line of {the_name} is not an option of the certificate",
            )

    # ------------------------------------------------------------------
    # the rows of the incomes
    # ------------------------------------------------------------------
    def test_a_row_keeps_its_own_type(self):
        """A row of the incomes keeps the type that it carries."""
        the_rental = self._the_income_type("Rental Income")
        the_payment_entry = self._the_payment_entry(pd_custom_wht_income_type=the_rental)

        the_items = creator.build_income_items(
            the_payment_entry,
            [
                {"tbs_income_type": None, "rate": 3, "tax_amount": 30, "gross_amount": 1000},
                {
                    "tbs_income_type": "40(8) ค่าโฆษณา 2%",
                    "rate": 2,
                    "tax_amount": 20,
                    "gross_amount": 1000,
                },
            ],
            THE_ENTITY,
        )

        self.assertEqual(the_items[0].get("income_type"), RENT_ITEM_LINE)
        self.assertEqual(the_items[1].get("income_type"), "40(8) ค่าโฆษณา 2%")

    def test_the_rate_of_the_certificate_is_the_rate_of_its_income_type(self):
        """The rate of the certificate is the rate of the type of the transaction.

        The rule of the legacy model wrote the rate of the document out of a
        map of the income types, with the income type of the document as its
        key.  The rows keep the rate that the payment entry carries.
        """
        the_rental = self._the_income_type("Rental Income")
        the_payment_entry = self._the_payment_entry(pd_custom_wht_income_type=the_rental)

        the_values = self._the_certificate(the_payment_entry)

        self.assertEqual(the_values.get("wht_rate"), 5.0)

    def test_a_mixed_transaction_keeps_the_rate_of_every_row(self):
        """The rows of a mixed transaction keep their own rate."""
        the_service = self._the_income_type("Service Fees")
        the_payment_entry = self._the_payment_entry(pd_custom_wht_income_type=the_service)

        the_items = creator.build_income_items(the_payment_entry, THE_ROWS, THE_ENTITY)
        the_values = creator.build_certificate_values(the_payment_entry, the_items, THE_ENTITY)

        self.assertEqual([item.get("tax_rate") for item in the_items], [3.0, 5.0])
        self.assertEqual(the_values.get("wht_rate"), 3.0)

    def test_without_a_rate_of_the_income_type_the_first_row_keeps_the_rate(self):
        """An income type that carries no rate falls back to the first row.

        The statutory sections of the legacy model carry no rate of their own,
        so the rate of the first row of the incomes remains the rate of the
        certificate.
        """
        the_payment_entry = self._the_payment_entry()

        the_values = self._the_certificate(the_payment_entry)

        self.assertEqual(the_values.get("wht_rate"), 3.0)

    # ------------------------------------------------------------------
    # the party that is not a supplier
    # ------------------------------------------------------------------
    def test_a_party_that_is_not_a_supplier_has_no_tax_id_and_no_address(self):
        """A party that is not a supplier has no tax id and no address."""
        the_payment_entry = self._the_payment_entry(
            party_type="Employee", party="Employee-Of-The-Rules", party_name="Employee Of The Rules"
        )

        the_values = self._the_certificate(the_payment_entry)

        self.assertFalse(the_values.get("supplier_tax_id"))
        self.assertFalse(the_values.get("supplier_address"))

    def test_a_supplier_keeps_its_tax_id(self):
        """A supplier keeps the tax id that it carries."""
        the_supplier = self._the_supplier()
        the_tax_id = frappe.db.get_value("Supplier", the_supplier, "tax_id")
        if not the_tax_id:
            self.skipTest("the supplier of the site has no tax id")

        the_payment_entry = self._the_payment_entry(party=the_supplier)
        the_values = self._the_certificate(the_payment_entry)

        self.assertEqual(the_values.get("supplier_tax_id"), the_tax_id)
