"""Tests for the audit of the Thai VAT and WHT calculation modules.

The audit covered the three calculation modules of Print Designer
(``sales_invoice_calculations``, ``sales_order_calculations`` and
``quotation_calculations``) and the background tax contract of a Sales
Invoice (``sales_invoice_tax_contract``).

The tests cover the two defects that the audit confirmed:

* the wording of the calculated amounts named the default currency of the
  site instead of the currency of the document,
* a VAT row of a document in another currency kept an empty base amount, so
  the VAT of the invoice was not available in the currency of the company.

They also pin the shared wording helper, so that the Sales Invoice, the Sales
Order and the Quotation describe their amounts in the same way.
"""

import unittest
from unittest import mock

from print_designer.custom.sales_invoice_tax_contract import (
    get_service_tax_snapshot,
    harmonise_base_amounts,
    rows_without_base_amount,
)
from print_designer.custom.thai_calculation_words import (
    NET_AFTER_WHT_RETENTION_WORDS,
    NET_TOTAL_AFTER_WHT_WORDS,
    amount_in_words,
    apply_amount_wording,
)
from print_designer.custom.thai_company_registration import (
    VAT_STATUS_REGISTERED,
    CompanyRegistration,
)

SERVICE_ITEM = "SERVICE-001"
VAT_ACCOUNT = "Output VAT - 7% - Test Company"


class DocStub:
    """A document stub with the API of a Frappe document.

    A ``frappe._dict`` is not enough: its attribute lookup never fails, so
    ``hasattr`` cannot tell a document that carries a field from one that does
    not.
    """

    def __init__(self, **fields):
        self.__dict__.update(fields)

    def get(self, field, default=None):
        return self.__dict__.get(field, default)

    def set(self, field, value):
        self.__dict__[field] = value


def make_doc(**kwargs):
    """Return a document stub that carries the fields of the calculation."""
    doc = DocStub(
        doctype="Sales Invoice",
        name="SINV-0001",
        currency="THB",
        company="Test Company",
        pd_custom_subject_to_retention=0,
        pd_custom_net_total_after_wht=1000.0,
        pd_custom_net_total_after_wht_words="",
        pd_custom_net_after_wht_retention=0,
        pd_custom_net_after_wht_retention_words="",
    )
    doc.__dict__.update(kwargs)
    return doc


def make_registration():
    return CompanyRegistration(
        company="Test Company",
        status="Registered",
        kind=VAT_STATUS_REGISTERED,
        effective_from="2024-01-01",
        is_effective=True,
        source="thai_company_settings",
        warning=None,
    )


class TestAmountInWords(unittest.TestCase):
    """The wording names the currency of the document."""

    def test_the_wording_names_the_currency_of_the_document(self):
        doc = make_doc(currency="USD")

        wording = amount_in_words(doc, 1000.0)

        self.assertIn("USD", wording)
        self.assertNotIn("THB", wording)

    def test_the_wording_of_the_default_currency_of_the_site_is_not_used(self):
        """The default currency of the site must not decide the wording."""
        doc = make_doc(currency="EUR")

        wording = amount_in_words(doc, 2500.0)

        self.assertIn("EUR", wording)

    def test_an_amount_of_zero_has_no_wording(self):
        self.assertEqual(amount_in_words(make_doc(), 0), "")
        self.assertEqual(amount_in_words(make_doc(), None), "")
        self.assertEqual(amount_in_words(make_doc(), ""), "")


class TestApplyAmountWording(unittest.TestCase):
    """The helper writes the wording of the calculated amounts."""

    def test_the_wording_of_the_net_total_is_written(self):
        doc = make_doc()

        apply_amount_wording(doc)

        self.assertTrue(doc.get(NET_TOTAL_AFTER_WHT_WORDS))
        self.assertIn("THB", str(doc.get(NET_TOTAL_AFTER_WHT_WORDS)))

    def test_the_wording_of_the_retention_is_written_when_the_retention_is_enabled(self):
        doc = make_doc(
            pd_custom_subject_to_retention=1,
            pd_custom_net_after_wht_retention=900.0,
        )

        apply_amount_wording(doc)

        self.assertTrue(doc.get(NET_AFTER_WHT_RETENTION_WORDS))

    def test_the_wording_of_the_retention_is_cleared_without_a_retention(self):
        doc = make_doc()
        doc.set(NET_AFTER_WHT_RETENTION_WORDS, "a stale wording")

        apply_amount_wording(doc)

        self.assertEqual(doc.get(NET_AFTER_WHT_RETENTION_WORDS), "")

    def test_a_document_without_the_wording_fields_does_not_break(self):
        doc = DocStub(
            doctype="Sales Invoice",
            name="SINV-0002",
            currency="THB",
            pd_custom_net_total_after_wht=1000.0,
        )

        apply_amount_wording(doc)

        self.assertFalse(hasattr(doc, NET_TOTAL_AFTER_WHT_WORDS))


class TestTheModulesUseTheSharedWording(unittest.TestCase):
    """The three calculation modules describe their amounts in one way."""

    def _wording(self, module, function_name):
        module = __import__(module, fromlist=[function_name])
        function = getattr(module, function_name)
        doc = make_doc()
        function(doc)
        return doc.get(NET_TOTAL_AFTER_WHT_WORDS)

    def test_the_sales_invoice_module(self):
        wording = self._wording(
            "print_designer.custom.sales_invoice_calculations",
            "convert_amounts_to_words_for_sales_invoice",
        )
        self.assertTrue(wording)
        self.assertIn("THB", str(wording))

    def test_the_sales_order_module(self):
        wording = self._wording(
            "print_designer.custom.sales_order_calculations",
            "convert_amounts_to_words_for_sales_order",
        )
        self.assertTrue(wording)
        self.assertIn("THB", str(wording))

    def test_the_quotation_module(self):
        wording = self._wording(
            "print_designer.custom.quotation_calculations",
            "convert_amounts_to_words",
        )
        self.assertTrue(wording)
        self.assertIn("THB", str(wording))


class TestHarmoniseBaseAmounts(unittest.TestCase):
    """The base amount of a VAT row is available in the currency of the company."""

    def test_a_row_in_the_currency_of_the_company_keeps_the_tax_amount(self):
        rows = [{"tax_amount": 70.0, "base_tax_amount": 0.0}]

        harmonise_base_amounts(rows, "THB", "THB")

        self.assertEqual(rows[0]["base_tax_amount"], 70.0)

    def test_a_row_in_another_currency_is_converted_with_the_rate_of_the_document(self):
        rows = [{"tax_amount": 100.0, "base_tax_amount": 0.0}]

        harmonise_base_amounts(rows, "USD", "THB", 35.5)

        self.assertEqual(rows[0]["base_tax_amount"], 3550.0)

    def test_a_row_without_a_rate_keeps_its_empty_base_amount(self):
        rows = [{"tax_amount": 100.0, "base_tax_amount": 0.0}]

        harmonise_base_amounts(rows, "USD", "THB")

        self.assertEqual(rows[0]["base_tax_amount"], 0.0)
        self.assertEqual(len(rows_without_base_amount(rows)), 1)

    def test_a_row_that_carries_a_base_amount_is_never_touched(self):
        rows = [{"tax_amount": 100.0, "base_tax_amount": 3550.0}]

        harmonise_base_amounts(rows, "USD", "THB", 35.5)

        self.assertEqual(rows[0]["base_tax_amount"], 3550.0)
        self.assertEqual(rows_without_base_amount(rows), [])

    def test_a_row_without_a_tax_amount_is_not_a_row_without_a_base_amount(self):
        rows = [{"tax_amount": 0.0, "base_tax_amount": 0.0}]

        self.assertEqual(rows_without_base_amount(rows), [])


class TestTheSnapshotReportsAMissingBaseAmount(unittest.TestCase):
    """The snapshot warns when the VAT of the invoice has no base amount."""

    def _snapshot(self, base_tax_amount):
        doc = make_doc(
            taxes=[
                {
                    "account_head": VAT_ACCOUNT,
                    "description": "VAT",
                    "charge_type": "On Net Total",
                    "rate": 7.0,
                    "tax_amount": 70.0,
                    "base_tax_amount": base_tax_amount,
                }
            ],
            items=[
                {
                    "item_code": SERVICE_ITEM,
                    "base_net_amount": 1000.0,
                    "net_amount": 1000.0,
                }
            ],
            currency="USD",
            company_currency="THB",
            conversion_rate=0,
        )

        # The company configures the VAT account, so the row of the invoice is
        # read as a VAT row without reading the master data of the account.
        with mock.patch(
            "print_designer.custom.sales_invoice_tax_contract.get_company_vat_accounts",
            return_value=[VAT_ACCOUNT],
        ):
            return get_service_tax_snapshot(doc, registration=make_registration())

    def test_a_row_without_a_base_amount_is_reported(self):
        snapshot = self._snapshot(0.0)

        self.assertTrue(
            any("base amount" in warning for warning in snapshot.warnings),
            f"expected a warning about the base amount, got {snapshot.warnings}",
        )
        self.assertEqual(snapshot.vat_amount, 0.0)

    def test_a_row_with_a_base_amount_is_not_reported(self):
        snapshot = self._snapshot(3550.0)

        self.assertFalse(any("base amount" in warning for warning in snapshot.warnings))
        self.assertEqual(snapshot.vat_amount, 3550.0)
