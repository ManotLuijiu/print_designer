"""The tests of the creation of the certificate of the withholding tax.

`print_designer.custom.wht_certificate_creator` is the single place that
creates the `Withholding Tax Certificate` of Print Designer.  Both entry
points of the app use it: the calculator of the tax of the site and the
generator of the certificate of a payment entry.

The tests create a disposable payment entry inside a savepoint that is
rolled back at the end, so that the site keeps no row of the test.
"""

import unittest
from typing import Any

import frappe
from frappe.utils import nowdate

from print_designer.custom import wht_canonical_mapping as mapping
from print_designer.custom import wht_certificate_creator as creator

SAVEPOINT = "wht_certificate_creator_test"

COMPANY = "_Test Company"
SUPPLIER = "_Test Supplier"

#: The service of the law of Thailand.  It is the income type of the site
#: when the site carries none.
SERVICE_INCOME = "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ"

#: The line of a service that is paid to a company.
COMPANY_SERVICE_LINE = "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service"

#: The line of the row of a service.
SERVICE_ITEM_LINE = "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ"

#: The classification of a company and the form of the tax of a company.
COMPANY_CLASSIFICATION = "Company/Juristic Person (PND.53)"
COMPANY_FORM = "PND53 Form"

#: The rent of the law of Thailand and the line of its row.
RENT_INCOME = "40(5) ค่าเช่า"
RENT_ITEM_LINE = "40(5) ค่าเช่า"


class TestTheCreatorOfTheCertificate(unittest.TestCase):
    """The creation of the certificate of the withholding tax."""

    def setUp(self):
        frappe.db.savepoint(SAVEPOINT)

    def tearDown(self):
        frappe.db.rollback(save_point=SAVEPOINT)

    def _the_account(self, account_type: str) -> str:
        """An account of the company of the test."""
        accounts = frappe.get_all(
            "Account",
            filters={
                "company": COMPANY,
                "account_type": account_type,
                "is_group": 0,
                "disabled": 0,
            },
            pluck="name",
        )
        if not accounts:
            self.skipTest(f"the site has no {account_type} account")

        return accounts[0]

    def _the_options(self, doctype: str) -> set[str]:
        """The options of the income type of a document."""
        field = frappe.get_meta(doctype).get_field("income_type")
        if not field:
            raise AssertionError(f"{doctype} has no income_type field")

        return {option.strip() for option in field.options.split("\n") if option.strip()}

    def _the_payment_entry(self, **overrides: Any) -> Any:
        """A disposable payment entry that pays a supplier.

        The payment entry carries the amounts of the withholding tax in its
        own fields.  It carries no `pd_custom_subject_to_wht`, so that the
        automatic creation of the certificate of the payment entry does not
        run and the test holds the path of the creator alone.
        """
        values: dict[str, Any] = {
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "company": COMPANY,
            "posting_date": nowdate(),
            "party_type": "Supplier",
            "party": SUPPLIER,
            "paid_from": self._the_account("Payable"),
            "paid_to": self._the_account("Bank"),
            "paid_amount": 1000,
            "received_amount": 1000,
            "source_exchange_rate": 1,
            "target_exchange_rate": 1,
            "paid_to_account_currency": frappe.db.get_value(
                "Account", self._the_account("Bank"), "account_currency"
            ),
            "reference_no": "TEST-WHT-CREATOR",
            "reference_date": nowdate(),
            "pd_custom_withholding_tax_amount_details": 30,
            "pd_custom_withholding_tax_pct_details": 3,
            "pd_custom_tax_base_amount": 1000,
        }
        values.update(overrides)

        payment_entry = frappe.get_doc(values)
        payment_entry.insert(ignore_permissions=True)

        return payment_entry

    def test_the_payment_entry_names_its_certificate(self):
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertEqual(
            frappe.db.get_value(
                "Payment Entry", payment_entry.name, "pd_custom_wht_certificate"
            ),
            certificate.name,
        )

    def test_the_link_of_the_payment_entry_is_kept_when_the_certificate_exists(self):
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)
        frappe.db.set_value(
            "Payment Entry", payment_entry.name, "pd_custom_wht_certificate", None
        )

        again = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertEqual(again.name, certificate.name)
        self.assertEqual(
            frappe.db.get_value(
                "Payment Entry", payment_entry.name, "pd_custom_wht_certificate"
            ),
            certificate.name,
        )

    def test_a_pay_payment_entry_creates_one_submitted_certificate(self):
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertIsNotNone(certificate)
        self.assertEqual(certificate.doctype, creator.CERTIFICATE_DOCTYPE)
        self.assertEqual(certificate.docstatus, 1)
        self.assertEqual(certificate.payment_entry, payment_entry.name)
        self.assertEqual(certificate.status, "Issued")
        self.assertTrue(certificate.certificate_number.startswith("WHTC-"))
        self.assertEqual(len(certificate.income_items), 1)

    def test_the_amounts_of_the_certificate_come_from_the_withholding_tax(self):
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertAlmostEqual(certificate.tax_base_amount, 1000.0, places=2)
        self.assertAlmostEqual(certificate.wht_amount, 30.0, places=2)
        self.assertAlmostEqual(certificate.net_payment_amount, 970.0, places=2)
        self.assertAlmostEqual(certificate.total_payment_amount, 1000.0, places=2)
        self.assertAlmostEqual(certificate.wht_rate, 3.0, places=2)

        item = certificate.income_items[0]
        self.assertAlmostEqual(item.gross_amount, 1000.0, places=2)
        self.assertAlmostEqual(item.tax_rate, 3.0, places=2)
        self.assertAlmostEqual(item.tax_amount, 30.0, places=2)
        self.assertAlmostEqual(item.net_amount, 970.0, places=2)

    def test_the_classification_of_the_certificate_names_its_form_of_the_tax(self):
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertEqual(certificate.supplier_type_classification, COMPANY_CLASSIFICATION)
        self.assertEqual(certificate.pnd_form_type, COMPANY_FORM)
        self.assertEqual(certificate.wht_condition, mapping.WHT_CONDITION)

    def test_the_line_of_a_service_of_a_company_is_the_line_of_a_company(self):
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertEqual(certificate.income_type, COMPANY_SERVICE_LINE)
        self.assertEqual(certificate.income_items[0].income_type, SERVICE_ITEM_LINE)

    def test_every_line_of_the_certificate_is_an_option_of_the_certificate(self):
        payment_entry = self._the_payment_entry()
        certificate = creator.create_certificate_for_payment_entry(payment_entry)

        parent_options = self._the_options(creator.CERTIFICATE_DOCTYPE)
        item_options = self._the_options(mapping.CERTIFICATE_ITEM_INCOME_TYPE)

        self.assertIn(certificate.income_type, parent_options)
        for item in certificate.income_items:
            self.assertIn(item.income_type, item_options)

    def test_a_second_call_reuses_the_certificate_of_the_payment_entry(self):
        payment_entry = self._the_payment_entry()
        first = creator.create_certificate_for_payment_entry(payment_entry)
        second = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertEqual(first.name, second.name)
        self.assertEqual(
            frappe.db.count(
                "Withholding Tax Certificate", {"payment_entry": payment_entry.name}
            ),
            1,
        )

    def test_a_receive_payment_entry_creates_no_certificate(self):
        certificate = creator.create_certificate_for_payment_entry(
            {"name": "PE-STUB", "payment_type": "Receive", "party_type": "Supplier"}
        )

        self.assertIsNone(certificate)

    def test_a_payment_entry_of_another_party_creates_no_certificate(self):
        certificate = creator.create_certificate_for_payment_entry(
            {"name": "PE-STUB", "payment_type": "Pay", "party_type": "Customer"}
        )

        self.assertIsNone(certificate)

    def test_a_payment_entry_without_withholding_tax_creates_no_certificate(self):
        payment_entry = self._the_payment_entry(
            pd_custom_withholding_tax_amount_details=0,
            pd_custom_withholding_tax_pct_details=0,
            pd_custom_tax_base_amount=0,
        )
        certificate = creator.create_certificate_for_payment_entry(payment_entry)

        self.assertIsNone(certificate)

    def test_every_row_of_the_withholding_tax_becomes_a_row_of_the_certificate(self):
        payment_entry = {
            "name": "PE-STUB",
            "payment_type": "Pay",
            "party_type": "Supplier",
            "posting_date": nowdate(),
        }
        rows = [
            {
                "tbs_income_type": SERVICE_INCOME,
                "rate": 3,
                "tax_amount": 30,
                "gross_amount": 1000,
            },
            {
                "tbs_income_type": RENT_INCOME,
                "rate": 5,
                "tax_amount": 50,
                "gross_amount": 1000,
            },
        ]

        items = creator.build_income_items(payment_entry, rows, "Company")

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["income_type"], SERVICE_ITEM_LINE)
        self.assertEqual(items[1]["income_type"], RENT_ITEM_LINE)
        self.assertAlmostEqual(items[0]["gross_amount"], 1000.0, places=2)
        self.assertAlmostEqual(items[0]["tax_amount"], 30.0, places=2)
        self.assertAlmostEqual(items[0]["net_amount"], 970.0, places=2)
        self.assertAlmostEqual(items[1]["tax_amount"], 50.0, places=2)
        self.assertAlmostEqual(items[1]["net_amount"], 950.0, places=2)
