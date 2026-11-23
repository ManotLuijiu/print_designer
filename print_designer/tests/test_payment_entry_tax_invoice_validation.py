"""The VAT of a Payment Entry and the mandatory Thai tax invoice fields.

The row of the taxes of a Payment Entry is an ``Advance Taxes and Charges``
row.  It carries the amount of the tax in ``tax_amount``; it has no
``amount`` field.

The two functions of the server events of the Payment Entry read the
amount of a tax row, so a read of ``amount`` is always zero:

* ``_validate_mandatory_tax_invoice_fields()`` never saw a VAT, so the
  mandatory tax invoice fields of a payment were never validated,
* ``_auto_fill_tax_base_amount()`` never saw a VAT, so the tax base of a
  payment without a Purchase Invoice reference was never filled.

The tests cover the behaviour of both functions, and the false positive
that a read of a real amount may cause: the fields are the fields of an
**input** tax invoice, so a receipt of a customer may not be refused by
them.
"""

from typing import Any

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.custom.payment_entry_server_events import (
    _auto_fill_tax_base_amount,
    _validate_mandatory_tax_invoice_fields,
    validate,
)

VAT_ROW = {
    "description": "VAT",
    "charge_type": "Actual",
    "rate": 7,
    "tax_amount": 70,
    "total": 70,
}


class TestThePaymentEntryVatValidation(FrappeTestCase):
    """The VAT of a Payment Entry and the mandatory tax invoice fields."""

    def _payment_entry(self, payment_type: str = "Pay", taxes=None, **extra) -> Any:
        """A Payment Entry that is not saved."""
        return frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": payment_type,
                "paid_amount": 1070,
                "received_amount": 1070,
                "total_allocated_amount": 1070,
                "taxes": taxes if taxes is not None else [],
                **extra,
            }
        )

    def test_a_tax_row_carries_its_amount_in_tax_amount(self):
        """The premise of the two functions.

        A row of the taxes of a Payment Entry is an "Advance Taxes and
        Charges" row.  It has no "amount" field, so a read of "amount" is
        always zero.
        """
        row = self._payment_entry(taxes=[dict(VAT_ROW)]).taxes[0]

        self.assertTrue(hasattr(row, "tax_amount"))
        self.assertFalse(hasattr(row, "amount"))
        self.assertEqual(row.tax_amount, 70)

    def test_a_pay_with_a_vat_row_and_no_tax_invoice_is_refused(self):
        """A payment with a VAT needs the tax invoice of the VAT."""
        doc = self._payment_entry(taxes=[dict(VAT_ROW)])

        with self.assertRaises(frappe.ValidationError) as caught:
            _validate_mandatory_tax_invoice_fields(doc)

        message = str(caught.exception)
        self.assertIn("pd_custom_tax_invoice_number", message)
        self.assertIn("pd_custom_tax_invoice_date", message)

    def test_a_pay_with_a_vat_row_and_a_tax_invoice_is_accepted(self):
        """A payment that carries the tax invoice is accepted."""
        doc = self._payment_entry(
            taxes=[dict(VAT_ROW)],
            pd_custom_tax_invoice_number="TAX-0001",
            pd_custom_tax_invoice_date="2026-01-01",
        )

        _validate_mandatory_tax_invoice_fields(doc)

    def test_a_pay_without_a_tax_row_is_not_refused(self):
        """A payment without a VAT needs no tax invoice."""
        doc = self._payment_entry()

        _validate_mandatory_tax_invoice_fields(doc)

    def test_a_pay_with_a_tax_row_of_another_rate_is_not_refused(self):
        """Only the VAT of 7 percent makes the tax invoice mandatory."""
        doc = self._payment_entry(taxes=[{**VAT_ROW, "rate": 0, "tax_amount": 0, "total": 0}])

        _validate_mandatory_tax_invoice_fields(doc)

    def test_a_receive_with_a_vat_row_is_not_refused(self):
        """A receipt of a customer is not an input tax invoice.

        The mandatory fields are the fields of the tax invoice of a
        purchase, so a receipt may not be refused by them.
        """
        doc = self._payment_entry(payment_type="Receive", taxes=[dict(VAT_ROW)])

        validate(doc, None)

    def test_the_tax_base_is_the_allocated_amount_without_the_vat(self):
        """The tax base of a payment without a reference is filled.

        Without a Purchase Invoice reference the only source of the tax
        base is the allocated amount of the payment without its VAT.
        """
        doc = self._payment_entry(taxes=[dict(VAT_ROW)])

        _auto_fill_tax_base_amount(doc)

        self.assertEqual(doc.pd_custom_tax_base_amount, 1000)

    def test_the_tax_base_is_not_overwritten(self):
        """A tax base that a person filled is kept."""
        doc = self._payment_entry(taxes=[dict(VAT_ROW)], pd_custom_tax_base_amount=500)

        _auto_fill_tax_base_amount(doc)

        self.assertEqual(doc.pd_custom_tax_base_amount, 500)

    def test_the_tax_base_stays_empty_without_a_vat(self):
        """A payment without a VAT has no tax base to fill."""
        doc = self._payment_entry()

        _auto_fill_tax_base_amount(doc)

        # The field keeps the value that it had, which is empty.  The
        # function only fills a base that it could compute.
        self.assertFalse(doc.pd_custom_tax_base_amount)
