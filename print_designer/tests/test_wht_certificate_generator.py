"""The tests of the generator of the certificate of the withholding tax.

`print_designer.custom.wht_certificate_generator` creates the certificate of
a payment entry that pays a purchase invoice.  It reads the same canonical
mapping as the creator of the certificate, so that the certificate and the
preview of the generator agree with the certificate of the creator.

The tests create a disposable payment entry inside a savepoint that is
rolled back at the end, so that the site keeps no row of the test.
"""

import unittest
from typing import Any

import frappe
from frappe.utils import nowdate

from print_designer.custom import wht_canonical_mapping as mapping
from print_designer.custom import wht_certificate_generator as generator

SAVEPOINT = "wht_certificate_generator_test"

COMPANY = "_Test Company"
SUPPLIER = "_Test Supplier"

#: The line of a service that is paid to a company.
COMPANY_SERVICE_LINE = "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service"

#: The line of the row of a service.
SERVICE_ITEM_LINE = "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ"

#: The classification of a company and the form of the tax of a company.
COMPANY_CLASSIFICATION = "Company/Juristic Person (PND.53)"
COMPANY_FORM = "PND53 Form"


class _Item:
    """A row of a purchase invoice of a test."""

    def __init__(self, description: str):
        self.description = description


class _PurchaseInvoice:
    """A purchase invoice of a test, without a row in the site."""

    def __init__(self, descriptions: tuple[str, ...] = ()):
        self.items = [_Item(description) for description in descriptions]
        self.tax_id = None
        self.total_taxes_and_charges = 0


class _PaymentEntry:
    """A payment entry of a test, without a row in the site."""

    def __init__(self, rate: float = 3.0):
        self.pd_custom_withholding_tax_pct_details = rate


class TestTheGeneratorOfTheCertificate(unittest.TestCase):
    """The creation of the certificate of the withholding tax."""

    def setUp(self):
        frappe.db.savepoint(SAVEPOINT)

    def tearDown(self):
        frappe.db.rollback(save_point=SAVEPOINT)

    def _the_account(self, account_type: str) -> str:
        """An account of the company of the test, in the currency of the company."""
        accounts = frappe.get_all(
            "Account",
            filters={
                "company": COMPANY,
                "account_type": account_type,
                "account_currency": frappe.db.get_value("Company", COMPANY, "default_currency"),
                "is_group": 0,
                "disabled": 0,
            },
            pluck="name",
            order_by="name",
        )
        if not accounts:
            self.skipTest(f"the site has no {account_type} account")

        return accounts[0]

    def _the_payment_entry(self, **overrides: Any) -> Any:
        """A disposable payment entry that pays a supplier."""
        values: dict[str, Any] = {
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "company": COMPANY,
            "posting_date": nowdate(),
            "party_type": "Supplier",
            "party": SUPPLIER,
            "paid_from": self._the_account("Bank"),
            "paid_to": self._the_account("Payable"),
            "paid_amount": 1000,
            "received_amount": 1000,
            "source_exchange_rate": 1,
            "target_exchange_rate": 1,
            "paid_to_account_currency": frappe.db.get_value(
                "Account", self._the_account("Payable"), "account_currency"
            ),
            "reference_no": "TEST-WHT-GENERATOR",
            "reference_date": nowdate(),
            "pd_custom_withholding_tax_amount_details": 30,
            "pd_custom_withholding_tax_pct_details": 3,
            "pd_custom_tax_base_amount": 1000,
        }
        values.update(overrides)

        payment_entry = frappe.get_doc(values)
        payment_entry.insert(ignore_permissions=True)

        return payment_entry

    def test_the_fallback_of_the_generator_carries_no_taxonomy(self):
        fallback = generator._fallback_income_type(_PurchaseInvoice(), _PaymentEntry())

        self.assertEqual(set(fallback), {"rate", "description"})
        self.assertEqual(fallback["rate"], 3.0)

    def test_the_description_of_the_fallback_comes_from_the_purchase_invoice(self):
        purchase_invoice = _PurchaseInvoice(("ค่าที่ปรึกษา", "ค่าเดินทาง"))

        fallback = generator._fallback_income_type(purchase_invoice, _PaymentEntry())

        self.assertEqual(fallback["description"], "ค่าที่ปรึกษา, ค่าเดินทาง")

    def test_the_certificate_of_the_generator_uses_the_canonical_mapping(self):
        payment_entry = self._the_payment_entry()

        certificate = generator._create_the_certificate(
            payment_entry, _PurchaseInvoice(("ค่าที่ปรึกษา",)), None
        )

        self.assertEqual(certificate.income_type, COMPANY_SERVICE_LINE)
        self.assertEqual(certificate.income_items[0].income_type, SERVICE_ITEM_LINE)
        self.assertEqual(certificate.supplier_type_classification, COMPANY_CLASSIFICATION)
        self.assertEqual(certificate.pnd_form_type, COMPANY_FORM)
        self.assertEqual(certificate.income_description, "ค่าที่ปรึกษา")

    def test_the_amounts_of_the_certificate_of_the_generator_come_from_the_tax(self):
        payment_entry = self._the_payment_entry()

        certificate = generator._create_the_certificate(payment_entry, _PurchaseInvoice(), None)

        self.assertAlmostEqual(certificate.tax_base_amount, 1000.0, places=2)
        self.assertAlmostEqual(certificate.wht_amount, 30.0, places=2)
        self.assertAlmostEqual(certificate.net_payment_amount, 970.0, places=2)

    def test_a_second_call_reuses_the_certificate_of_the_payment_entry(self):
        payment_entry = self._the_payment_entry()

        first = generator._create_the_certificate(payment_entry, _PurchaseInvoice(), None)
        second = generator._create_the_certificate(payment_entry, _PurchaseInvoice(), None)

        self.assertEqual(first.name, second.name)
        self.assertEqual(
            frappe.db.count("Withholding Tax Certificate", {"payment_entry": payment_entry.name}),
            1,
        )

    def test_the_line_of_every_certificate_is_an_option_of_the_certificate(self):
        payment_entry = self._the_payment_entry()

        certificate = generator._create_the_certificate(payment_entry, _PurchaseInvoice(), None)

        parent_field = frappe.get_meta(mapping.CERTIFICATE_INCOME_TYPE).get_field("income_type")
        item_field = frappe.get_meta(mapping.CERTIFICATE_ITEM_INCOME_TYPE).get_field("income_type")
        if not parent_field or not item_field:
            raise AssertionError("the certificate has no income_type field")

        parent_options = {
            option.strip() for option in parent_field.options.split("\n") if option.strip()
        }
        item_options = {
            option.strip() for option in item_field.options.split("\n") if option.strip()
        }

        self.assertIn(certificate.income_type, parent_options)
        for item in certificate.income_items:
            self.assertIn(item.income_type, item_options)
