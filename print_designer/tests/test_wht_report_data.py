"""The reader of the report data of the withholding tax of Thailand.

The reader `print_designer.custom.wht_report_data` owns the reading of the
canonical certificate of the withholding tax, of its incomes and of the
register of the incoming withholding tax.  The reports of the Thai Business
Suite read the data of the withholding tax through it, so the knowledge of the
schema of the certificate lives in one place.

The tests here hold the reading of the reader:

- every income of a certificate is a row of its own,
- a certificate without an income is still reported,
- the filters of the payment reach the query,
- the form of the withholding tax is mapped exactly,
- a certificate whose tax does not agree with its rate is invalid,
- the code of the income of Thailand is read from the description of the
  income, wherever the description carries it,
- the register of the incoming withholding tax is read as well.
"""

import unittest
from typing import Any, Dict, List
from unittest.mock import patch

import frappe

from print_designer.custom import wht_report_data as the_reader

THE_COMPANY = "The Company of the Test"


def _a_certificate(
    the_name: str = "WHTC-TEST-0001",
    the_tax: float = 200.0,
    the_rate: float = 2.0,
    the_gross: float = 10000.0,
) -> Dict[str, Any]:
    return {
        "name": the_name,
        "certificate_number": the_name,
        "certificate_date": "2026-01-15",
        "payment_date": "2026-01-14",
        "company": THE_COMPANY,
        "supplier": "SUP-TEST-0001",
        "supplier_name": "The Supplier of the Test",
        "supplier_tax_id": "0105556000001",
        "supplier_type_classification": "Company/Juristic Person (PND.53)",
        "pnd_form_type": "PND53 Form",
        "income_type": "8. ค่าโฆษณา - Advertising",
        "income_description": "The advertising of the test",
        "wht_rate": the_rate,
        "tax_base_amount": the_gross,
        "wht_amount": the_tax,
        "net_payment_amount": the_gross - the_tax,
        "total_payment_amount": the_gross,
        "tax_year": "2026",
        "tax_month": "01 - มกราคม (January)",
        "status": "Issued",
        "payment_entry": "PE-TEST-0001",
    }


def _an_income(
    the_parent: str = "WHTC-TEST-0001",
    the_type: str = "40(8) ค่าโฆษณา 2%",
    the_gross: float = 10000.0,
    the_tax: float = 200.0,
) -> Dict[str, Any]:
    return {
        "parent": the_parent,
        "payment_date": "2026-01-14",
        "income_type": the_type,
        "income_type_description": "The advertising of the test",
        "tax_rate": 2.0,
        "gross_amount": the_gross,
        "tax_amount": the_tax,
        "net_amount": the_gross - the_tax,
        "remarks": "",
    }


def _a_register() -> Dict[str, Any]:
    return {
        "name": "RWR-TEST-0001",
        "wht_certificate_no": "RWR-TEST-0001",
        "wht_certificate_date": "2026-02-10",
        "customer": "CUS-TEST-0001",
        "customer_name": "The Customer of the Test",
        "customer_tax_id": "0105556000002",
        "payment_entry": "PE-TEST-0002",
        "payment_date": "2026-02-09",
        "company": THE_COMPANY,
        "income_type": "1. เงินเดือน ค่าจ้าง ฯลฯ 40(1) - Salary",
        "wht_rate": 3.0,
        "tax_base_amount": 5000.0,
        "wht_amount": 150.0,
        "status": "Issued",
    }


class _TheReader:
    """The reader of the reader, with the rows of the canonical documents."""

    def __init__(
        self,
        the_certificates: List[Dict[str, Any]] | None = None,
        the_incomes: List[Dict[str, Any]] | None = None,
        the_registers: List[Dict[str, Any]] | None = None,
    ) -> None:
        self.certificates = the_certificates if the_certificates is not None else []
        self.incomes = the_incomes if the_incomes is not None else []
        self.registers = the_registers if the_registers is not None else []
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, doctype: str, *args: Any, **kwargs: Any) -> List[frappe._dict]:
        self.calls.append({"doctype": doctype, "filters": kwargs.get("filters")})

        if doctype == the_reader.CERTIFICATE_DOCTYPE:
            return [frappe._dict(the_row) for the_row in self.certificates]
        if doctype == the_reader.ITEM_DOCTYPE:
            return [frappe._dict(the_row) for the_row in self.incomes]
        if doctype == the_reader.RECEIVE_REGISTER_DOCTYPE:
            return [frappe._dict(the_row) for the_row in self.registers]

        return []

    def the_filters_of(self, doctype: str) -> List[Dict[str, Any]]:
        return [the_call["filters"] for the_call in self.calls if the_call["doctype"] == doctype]


class TestWhReportData(unittest.TestCase):
    """The reader of the report data reads the canonical documents."""

    def _the_lines(
        self,
        the_certificates: List[Dict[str, Any]] | None = None,
        the_incomes: List[Dict[str, Any]] | None = None,
        **the_filters: Any,
    ) -> List[Any]:
        the_reader_of_the_reader = _TheReader(the_certificates, the_incomes)

        with patch("frappe.get_all", side_effect=the_reader_of_the_reader):
            with patch("frappe.has_permission", return_value=True):
                return the_reader.get_certificate_lines(**the_filters)

    # ------------------------------------------------------------------
    # the incomes of a certificate
    # ------------------------------------------------------------------
    def test_every_income_of_a_certificate_is_a_row_of_its_own(self):
        """A certificate with two incomes is reported with two rows."""
        the_lines = self._the_lines(
            [_a_certificate()],
            [_an_income(), _an_income(the_type="40(4)ก ดอกเบี้ย 2%")],
        )

        self.assertEqual(len(the_lines), 2)
        self.assertEqual(
            [the_line.get("line_income_type") for the_line in the_lines],
            ["40(8) ค่าโฆษณา 2%", "40(4)ก ดอกเบี้ย 2%"],
        )

    def test_a_certificate_without_an_income_is_still_reported(self):
        """A certificate without an income is reported with its own totals."""
        the_lines = self._the_lines([_a_certificate()], [])

        self.assertEqual(len(the_lines), 1)
        the_line = the_lines[0]
        self.assertEqual(the_line.get("certificate"), "WHTC-TEST-0001")
        self.assertEqual(the_line.get("line_income_type"), "8. ค่าโฆษณา - Advertising")
        self.assertEqual(the_line.get("tax_base_amount"), 10000.0)
        self.assertEqual(the_line.get("wht_amount"), 200.0)

    def test_the_income_of_a_certificate_keeps_its_own_amounts(self):
        """The row of an income carries the amounts of the income."""
        the_lines = self._the_lines(
            [_a_certificate()],
            [_an_income(the_gross=4000.0, the_tax=80.0)],
        )

        self.assertEqual(len(the_lines), 1)
        the_line = the_lines[0]
        self.assertEqual(the_line.get("line_gross_amount"), 4000.0)
        self.assertEqual(the_line.get("line_tax_amount"), 80.0)
        self.assertEqual(the_line.get("line_net_amount"), 3920.0)

    def test_the_income_type_of_the_report_keeps_only_its_incomes(self):
        """The filter of the income type keeps only the incomes of that type."""
        the_lines = self._the_lines(
            [_a_certificate()],
            [_an_income(), _an_income(the_type="40(4)ก ดอกเบี้ย 2%")],
            income_type_contains="40(4)",
        )

        self.assertEqual(len(the_lines), 1)
        self.assertEqual(the_lines[0].get("line_income_type"), "40(4)ก ดอกเบี้ย 2%")

    # ------------------------------------------------------------------
    # the filters
    # ------------------------------------------------------------------
    def test_the_filter_of_the_payment_reaches_the_query(self):
        """The dates of the payment filter the certificates by their payment."""
        the_reader_of_the_reader = _TheReader([_a_certificate()], [])

        with patch("frappe.get_all", side_effect=the_reader_of_the_reader):
            with patch("frappe.has_permission", return_value=True):
                the_reader.get_certificates(
                    payment_from_date="2026-01-01",
                    payment_to_date="2026-01-31",
                )

        the_filters = the_reader_of_the_reader.the_filters_of(the_reader.CERTIFICATE_DOCTYPE)
        self.assertEqual(len(the_filters), 1)
        self.assertEqual(
            the_filters[0].get("payment_date"),
            [">=", "2026-01-01", "<=", "2026-01-31"],
        )

    def test_the_form_of_the_withholding_tax_reaches_the_query_exactly(self):
        """The form of the report is the name of the form of the certificate."""
        the_reader_of_the_reader = _TheReader([_a_certificate()], [])

        with patch("frappe.get_all", side_effect=the_reader_of_the_reader):
            with patch("frappe.has_permission", return_value=True):
                the_reader.get_certificates(pnd_form_types=["PND53 Form"])

        the_filters = the_reader_of_the_reader.the_filters_of(the_reader.CERTIFICATE_DOCTYPE)
        self.assertEqual(the_filters[0].get("pnd_form_type"), ["in", ["PND53 Form"]])

    # ------------------------------------------------------------------
    # the form of the withholding tax
    # ------------------------------------------------------------------
    def test_the_form_of_the_report_is_mapped_to_the_form_of_the_certificate(self):
        """The report names the form of the withholding tax as ``PND53``."""
        self.assertEqual(
            the_reader.get_pnd_form_type_names(["PND53"]),
            ["PND53 Form"],
        )
        self.assertEqual(
            the_reader.get_pnd_form_type_names(["PND1", "PND3", "PND53", "PND54"]),
            ["PND1 Form", "PND3 Form", "PND53 Form", "PND54 Form"],
        )
        self.assertIsNone(the_reader.get_pnd_form_type_names(None))

    def test_the_form_of_the_certificate_is_mapped_to_the_form_of_the_report(self):
        """The certificate names the form of the withholding tax as ``PND53 Form``."""
        self.assertEqual(the_reader.get_pnd_type_of_form("PND53 Form"), "PND53")
        self.assertEqual(the_reader.get_pnd_type_of_form("PND1 Form"), "PND1")
        self.assertEqual(the_reader.get_pnd_type_of_form(""), "")

    # ------------------------------------------------------------------
    # the invalid certificates
    # ------------------------------------------------------------------
    def test_a_certificate_whose_tax_does_not_agree_with_its_rate_is_invalid(self):
        """The tax of the certificate has to be the tax of its base amount."""
        the_reader_of_the_reader = _TheReader(
            [
                _a_certificate(the_name="WHTC-VALID-0001", the_tax=200.0),
                _a_certificate(the_name="WHTC-WRONG-0001", the_tax=150.0),
            ],
            [],
        )

        with patch("frappe.get_all", side_effect=the_reader_of_the_reader):
            with patch("frappe.has_permission", return_value=True):
                the_invalid = the_reader.get_invalid_certificates()

        self.assertEqual(
            [the_certificate.name for the_certificate in the_invalid],
            ["WHTC-WRONG-0001"],
        )

    def test_a_certificate_without_an_amount_is_invalid(self):
        """A certificate without a tax carries no valid withholding."""
        the_reader_of_the_reader = _TheReader(
            [_a_certificate(the_name="WHTC-EMPTY-0001", the_tax=0.0)],
            [],
        )

        with patch("frappe.get_all", side_effect=the_reader_of_the_reader):
            with patch("frappe.has_permission", return_value=True):
                the_invalid = the_reader.get_invalid_certificates()

        self.assertEqual(
            [the_certificate.name for the_certificate in the_invalid],
            ["WHTC-EMPTY-0001"],
        )

    # ------------------------------------------------------------------
    # the code of the income of Thailand
    # ------------------------------------------------------------------
    def test_the_code_of_the_income_is_read_from_the_beginning_of_its_type(self):
        """The income type of a row carries its code at its beginning."""
        self.assertEqual(the_reader.get_income_code("40(8) ค่าบริการ 3%"), "40(8)")
        self.assertEqual(the_reader.get_income_code("40(4)ก ดอกเบี้ย 2%"), "40(4)ก")
        self.assertEqual(the_reader.get_income_code("8. ค่าโฆษณา - Advertising"), "")
        self.assertEqual(the_reader.get_income_code(None), "")

    def test_the_code_of_the_income_is_read_from_a_description_that_carries_it(self):
        """The income type of a certificate carries its code around it."""
        self.assertEqual(
            the_reader.find_income_code("1. เงินเดือน ค่าจ้าง ฯลฯ 40(1) - Salary"),
            "40(1)",
        )
        self.assertEqual(
            the_reader.find_income_code("4. (ข) เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ 40(4)ข - Dividend"),
            "40(4)ข",
        )
        self.assertEqual(
            the_reader.find_income_code("4. (ก) ดอกเบี้ย ฯลฯ 40(4)ก - Interest"),
            "40(4)ก",
        )
        self.assertEqual(the_reader.find_income_code("8. ค่าโฆษณา - Advertising"), "")
        self.assertEqual(the_reader.find_income_code(None), "")

    # ------------------------------------------------------------------
    # the register of the incoming withholding tax
    # ------------------------------------------------------------------
    def test_the_register_of_the_incoming_withholding_tax_is_read(self):
        """The register of the incoming withholding tax is its counterpart."""
        the_reader_of_the_reader = _TheReader([], [], [_a_register()])

        with patch("frappe.get_all", side_effect=the_reader_of_the_reader):
            with patch("frappe.has_permission", return_value=True):
                the_registers = the_reader.get_receive_registers(company=THE_COMPANY)

        self.assertEqual(len(the_registers), 1)
        self.assertEqual(the_registers[0].get("name"), "RWR-TEST-0001")
        self.assertEqual(the_registers[0].get("wht_amount"), 150.0)

        the_filters = the_reader_of_the_reader.the_filters_of(the_reader.RECEIVE_REGISTER_DOCTYPE)
        self.assertEqual(the_filters[0].get("company"), THE_COMPANY)

    def test_the_reader_refuses_a_caller_without_the_right(self):
        """The reader asks for the right of reading the certificate."""
        with patch("frappe.get_all", side_effect=_TheReader()):
            with patch("frappe.has_permission", return_value=False):
                with self.assertRaises(Exception):
                    the_reader.get_certificates()

                with self.assertRaises(Exception):
                    the_reader.get_receive_registers()
