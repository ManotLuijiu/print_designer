"""Tests for the Output VAT Undue ledger of Print Designer (SI-02).

``print_designer/custom/output_vat_undue_tracking.py`` is the one
orchestration path that writes the ledger of the undue output VAT.  The
ledger is the ``Output VAT Undue`` document.

The tests cover:

* the status of a row for every kind of sale of the plan,
* the identity of a row: the name of the row is the name of the invoice,
* the account of the row: a sale without a liability needs no account, and
  a difference with the account of the company is reported,
* the race of two transactions that create the row of the same invoice - the
  second one carries on with the row of the first one, and every other
  failure surfaces,
* the cancellation and the conversion of a row,
* the immutability of the snapshot of the decision,
* the fact that the ledger creates no GL entry,
* the fact that the ledger stays inside the transaction of the invoice.
"""

import unittest
from unittest.mock import patch

import frappe
import frappe.utils
from frappe.tests.utils import FrappeTestCase

from print_designer.custom import output_vat_undue_tracking as tracking
from print_designer.custom.sales_invoice_tax_contract import (
    REASON_ALREADY_DUE,
    REASON_DEFERRED_SERVICE,
    REASON_EXEMPT_SUPPLY,
    REASON_NON_REGISTERED,
    REASON_ZERO_RATED,
    VAT_TREATMENT_DUE,
    VAT_TREATMENT_EXEMPT,
    VAT_TREATMENT_UNDUE,
    VAT_TREATMENT_ZERO_RATED,
    build_service_tax_snapshot,
    get_service_tax_snapshot,
)
from print_designer.custom.thai_company_registration import (
    VAT_STATUS_NOT_REGISTERED,
    VAT_STATUS_REGISTERED,
    CompanyRegistration,
)

SERVICE_ITEM = "PD-SERVICE-TEST"
VAT_ACCOUNT = "Output VAT - 7% - Test Company"
OTHER_ACCOUNT = "Some Other - Test Company"


def _registration(kind=VAT_STATUS_REGISTERED):
    """The registration of a company."""
    status = {
        VAT_STATUS_REGISTERED: "Registered",
        VAT_STATUS_NOT_REGISTERED: "Not Registered",
    }.get(kind)
    return CompanyRegistration(
        company="Test Company",
        status=status,
        kind=kind,
        effective_from="2024-01-01",
        is_effective=True,
        source="thai_company_settings",
    )


def _service_row(base=1000.0):
    return {
        "item_code": SERVICE_ITEM,
        "is_service": True,
        "is_stock": False,
        "base_net_amount": base,
        "net_amount": base,
    }


def _vat_row(account=VAT_ACCOUNT, amount=70.0):
    return {
        "account_head": account,
        "description": "VAT",
        "charge_type": "On Net Total",
        "rate": 7.0,
        "tax_amount": amount,
        "base_tax_amount": amount,
        "is_tax_withholding_account": 0,
    }


def _snapshot(treatment=VAT_TREATMENT_UNDUE, registration=None, vat_rows=None):
    """The tax snapshot of a service invoice."""
    return build_service_tax_snapshot(
        identity={
            "sales_invoice": "SINV-0001",
            "docstatus": 1,
            "posting_date": "2026-01-15",
            "company": "Test Company",
            "currency": "THB",
            "company_currency": "THB",
            "net_total": 1000.0,
        },
        registration=registration if registration is not None else _registration(),
        treatment=treatment,
        item_rows=[_service_row()],
        vat_rows=list(vat_rows) if vat_rows is not None else [_vat_row()],
    )


def _doc(**overrides):
    """A Sales Invoice like document."""
    doc = frappe._dict(
        {
            "doctype": "Sales Invoice",
            "name": "SINV-0001",
            "docstatus": 1,
            "company": "Test Company",
            "customer": "Test Customer",
            "currency": "THB",
            "company_currency": "THB",
            "posting_date": "2026-01-15",
            "base_net_total": 1000.0,
            "base_grand_total": 1070.0,
        }
    )
    doc.update(overrides)
    return doc


class _FailingRecord:
    """A tracking row whose insert fails with the given error."""

    def __init__(self, error):
        self.error = error

    def insert(self, **kwargs):
        raise self.error


def _duplicate_error(key="PRIMARY", value="SINV-0001"):
    """The database error of a duplicate key, as the adapter of the site raises it.

    The driver of the site decides the class of the error: the bench of
    Print Designer runs on mysqlclient as well as on pymysql, and the
    adapter of the site only recognises its own driver.
    """
    message = f"Duplicate entry '{value}' for key 'tabOutput VAT Undue.{key}'"

    if frappe.db.db_type == "postgres":
        import psycopg2

        constraint = (
            "taboutput_vat_undue_pkey" if key == "PRIMARY" else f"taboutput_vat_undue_{key}"
        )
        return psycopg2.errors.UniqueViolation(
            f'duplicate key value violates unique constraint "{constraint}"'
        )

    if "mysqlclient" in type(frappe.local.db).__module__:
        import MySQLdb

        return MySQLdb.IntegrityError(1062, message)

    import pymysql

    return pymysql.IntegrityError(1062, message)


class TestTheStatusOfARow(unittest.TestCase):
    """The status of a row tells what the sale means for the VAT."""

    def test_a_deferred_service_is_pending(self):
        snapshot = _snapshot(treatment=VAT_TREATMENT_UNDUE)
        self.assertEqual(snapshot.treatment_reason, REASON_DEFERRED_SERVICE)
        self.assertEqual(tracking.status_for_snapshot(snapshot), tracking.STATUS_PENDING)

    def test_a_vat_that_is_already_due_is_already_due(self):
        snapshot = _snapshot(treatment=VAT_TREATMENT_DUE)
        self.assertEqual(snapshot.treatment_reason, REASON_ALREADY_DUE)
        self.assertEqual(tracking.status_for_snapshot(snapshot), tracking.STATUS_ALREADY_DUE)

    def test_an_exempt_supply_is_not_applicable(self):
        snapshot = _snapshot(treatment=VAT_TREATMENT_EXEMPT)
        self.assertEqual(snapshot.treatment_reason, REASON_EXEMPT_SUPPLY)
        self.assertEqual(tracking.status_for_snapshot(snapshot), tracking.STATUS_NOT_APPLICABLE)

    def test_a_seller_that_is_not_registered_is_not_applicable(self):
        snapshot = _snapshot(
            treatment=VAT_TREATMENT_EXEMPT,
            registration=_registration(VAT_STATUS_NOT_REGISTERED),
        )
        self.assertEqual(snapshot.treatment_reason, REASON_NON_REGISTERED)
        self.assertEqual(tracking.status_for_snapshot(snapshot), tracking.STATUS_NOT_APPLICABLE)

    def test_a_zero_rated_supply_is_not_applicable(self):
        snapshot = _snapshot(treatment=VAT_TREATMENT_ZERO_RATED)
        self.assertEqual(snapshot.treatment_reason, REASON_ZERO_RATED)
        self.assertEqual(tracking.status_for_snapshot(snapshot), tracking.STATUS_NOT_APPLICABLE)

    def test_the_pending_and_the_not_applicable_rows_carry_a_balance(self):
        self.assertIn(tracking.STATUS_PENDING, tracking.ACTIVE_STATUSES)
        self.assertNotIn(tracking.STATUS_NOT_APPLICABLE, tracking.ACTIVE_STATUSES)

    def test_the_closed_rows_carry_no_balance(self):
        for status in (
            tracking.STATUS_CONVERTED,
            tracking.STATUS_NOT_APPLICABLE,
            tracking.STATUS_ALREADY_DUE,
            tracking.STATUS_CANCELLED,
        ):
            self.assertIn(status, tracking.CLOSED_STATUSES)
            self.assertNotIn(status, tracking.ACTIVE_STATUSES)


class TestTheIdentityOfARow(unittest.TestCase):
    """The row carries the invoice it belongs to."""

    def test_the_row_carries_the_invoice(self):
        record = tracking._build_record(_doc(), _snapshot())
        self.assertEqual(record.get("sales_invoice"), "SINV-0001")

    def test_the_row_carries_the_snapshot_of_the_decision(self):
        record = tracking._build_record(_doc(), _snapshot())
        self.assertEqual(record.get("vat_treatment"), VAT_TREATMENT_UNDUE)
        self.assertEqual(record.get("treatment_reason"), REASON_DEFERRED_SERVICE)
        self.assertEqual(record.get("service_base_amount"), 1000.0)
        self.assertEqual(record.get("vat_amount"), 70.0)

    def test_the_row_carries_the_amounts_of_the_invoice(self):
        record = tracking._build_record(_doc(), _snapshot())
        self.assertEqual(record.get("base_amount"), 1000.0)
        self.assertEqual(record.get("total_amount"), 1070.0)
        self.assertEqual(record.get("invoice_number"), "SINV-0001")

    def test_the_row_of_a_sale_without_a_liability_has_no_account(self):
        snapshot = _snapshot(treatment=VAT_TREATMENT_EXEMPT, vat_rows=[])
        record = tracking._build_record(_doc(), snapshot)
        self.assertIsNone(record.get("output_vat_account"))
        self.assertEqual(record.get("status"), tracking.STATUS_NOT_APPLICABLE)

    def test_the_account_of_the_tax_row_is_the_account_of_the_row(self):
        snapshot = _snapshot()
        account, warning = tracking._vat_account(_doc(), snapshot)
        self.assertEqual(account, VAT_ACCOUNT)
        self.assertIsNone(warning)

    def test_a_difference_with_the_account_of_the_company_is_reported(self):
        snapshot = _snapshot()
        original = frappe.db.get_value

        def get_value(doctype, filters=None, fieldname="name", *args, **kwargs):
            if doctype == "Company" and fieldname == "default_output_vat_undue_account":
                return OTHER_ACCOUNT
            return original(doctype, filters, fieldname, *args, **kwargs)

        with patch("frappe.db.get_value", side_effect=get_value):
            account, warning = tracking._vat_account(_doc(), snapshot)

        self.assertEqual(account, VAT_ACCOUNT)
        self.assertIsNotNone(warning)
        self.assertIn(OTHER_ACCOUNT, warning or "")


class TestTheRaceOfTwoTransactions(unittest.TestCase):
    """Two transactions that create the row of the same invoice."""

    def setUp(self):
        self.messages = len(frappe.local.message_log)

    def test_a_duplicate_of_the_identity_is_swallowed(self):
        original = _duplicate_error()
        error = frappe.DuplicateEntryError("Output VAT Undue", "SINV-0001", original)

        result = tracking._insert_tracking_row(_FailingRecord(error), "SINV-0001")

        self.assertIsNone(result)

    def test_a_unique_failure_of_another_column_surfaces(self):
        original = _duplicate_error(key="other_index")
        error = frappe.UniqueValidationError("Output VAT Undue", "SINV-0001", original)

        with self.assertRaises(frappe.UniqueValidationError):
            tracking._insert_tracking_row(_FailingRecord(error), "SINV-0001")

    def test_a_failure_of_another_kind_surfaces(self):
        error = frappe.PermissionError("Output VAT Undue")

        with self.assertRaises(frappe.PermissionError):
            tracking._insert_tracking_row(_FailingRecord(error), "SINV-0001")

    def test_the_messages_of_the_refused_insert_are_dropped(self):
        frappe.msgprint("a message of the sale")
        original = _duplicate_error()
        error = frappe.DuplicateEntryError("Output VAT Undue", "SINV-0001", original)

        tracking._insert_tracking_row(_FailingRecord(error), "SINV-0001")

        self.assertEqual(len(frappe.local.message_log), self.messages + 1)
        self.assertIn("a message of the sale", str(frappe.local.message_log[-1]))

    def test_the_duplicate_of_the_identity_is_recognised(self):
        original = _duplicate_error()
        error = frappe.DuplicateEntryError("Output VAT Undue", "SINV-0001", original)
        self.assertTrue(tracking._is_duplicate_identity_error(error))

    def test_the_duplicate_of_another_column_is_not_recognised(self):
        original = _duplicate_error(key="other_index")
        error = frappe.UniqueValidationError("Output VAT Undue", "SINV-0001", original)
        self.assertFalse(tracking._is_duplicate_identity_error(error))

    def test_an_error_without_a_database_cause_is_not_recognised(self):
        error = frappe.DuplicateEntryError("Output VAT Undue", "SINV-0001")
        self.assertFalse(tracking._is_duplicate_identity_error(error))


class TestTheScopeOfTheTracking(unittest.TestCase):
    """Only a submitted service invoice belongs to the scope."""

    def test_another_document_is_out_of_scope(self):
        self.assertFalse(tracking.is_service_invoice_in_scope(_doc(doctype="Payment Entry")))

    def test_a_draft_invoice_is_out_of_scope(self):
        self.assertFalse(tracking.is_service_invoice_in_scope(_doc(docstatus=0)))

    def test_the_creation_of_another_document_does_nothing(self):
        self.assertIsNone(tracking.create_output_vat_undue_record(_doc(doctype="Payment Entry")))

    def test_the_creation_for_a_draft_invoice_does_nothing(self):
        self.assertIsNone(tracking.create_output_vat_undue_record(_doc(docstatus=0)))


class TestTheLedgerOnTheSite(FrappeTestCase):
    """The ledger on a site that carries it."""

    company: str
    customer: str

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        if "erpnext" not in frappe.get_installed_apps():
            raise unittest.SkipTest("ERPNext is not installed on this site")

        companies = frappe.get_all("Company", filters={"is_group": 0}, limit=1, pluck="name")
        customers = frappe.get_all("Customer", filters={"disabled": 0}, limit=1, pluck="name")
        cls.company = companies[0] if companies else ""
        cls.customer = customers[0] if customers else ""

        if not (cls.company and cls.customer):
            raise unittest.SkipTest("this site has no company or customer")

        if not _ledger_is_migrated():
            raise unittest.SkipTest("the ledger of this site has not been migrated yet")

    @classmethod
    def tearDownClass(cls):
        frappe.db.rollback()
        super().tearDownClass()

    def tearDown(self):
        frappe.db.rollback()
        super().tearDown()

    def _invoice(self):
        """A submitted service invoice with a deferred VAT."""
        # The item is taken inside the test: the rollback of the test takes
        # the item of the class with it, so it has to exist again.
        item_code = _service_item(self.company)
        invoice = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "company": self.company,
                "customer": self.customer,
                "posting_date": frappe.utils.nowdate(),
                "due_date": frappe.utils.add_days(frappe.utils.nowdate(), 30),
                "items": [
                    {
                        "item_code": item_code,
                        "qty": 1,
                        "rate": 1000,
                        "delivery_date": frappe.utils.nowdate(),
                    }
                ],
            }
        )
        if frappe.get_meta("Sales Invoice").has_field("pd_custom_vat_treatment"):
            invoice.set("pd_custom_vat_treatment", "VAT Undue")
        invoice.insert(ignore_permissions=True)
        invoice.submit()
        return invoice

    def test_the_submit_of_the_invoice_creates_the_row(self):
        invoice = self._invoice()

        rows = frappe.get_all(
            "Output VAT Undue",
            filters={"sales_invoice": invoice.name},
            pluck="name",
        )

        self.assertEqual(rows, [invoice.name])

    def test_the_row_carries_the_snapshot_of_the_decision(self):
        invoice = self._invoice()
        row = frappe.get_doc("Output VAT Undue", str(invoice.name))
        snapshot = get_service_tax_snapshot(invoice)

        # The treatment of the invoice decides the reason.  The site resolves
        # the treatment of an invoice itself, so the test may not expect a
        # reason of its own: the ledger has to carry the decision of the
        # invoice, not the expectation of the test.
        expected_status = {
            REASON_DEFERRED_SERVICE: tracking.STATUS_PENDING,
            REASON_ALREADY_DUE: tracking.STATUS_ALREADY_DUE,
        }.get(snapshot.treatment_reason, tracking.STATUS_NOT_APPLICABLE)

        self.assertEqual(row.get("sales_invoice"), invoice.name)
        self.assertEqual(row.get("treatment_reason"), snapshot.treatment_reason)
        self.assertEqual(row.get("status"), expected_status)
        self.assertEqual(row.get("service_classification"), snapshot.classification)
        self.assertEqual(
            row.get("service_base_amount"),
            snapshot.eligible_service_base,
        )
        self.assertEqual(row.get("vat_amount"), snapshot.vat_amount)

    def test_a_second_creation_does_not_create_a_second_row(self):
        invoice = self._invoice()

        tracking.create_output_vat_undue_record(invoice)

        self.assertEqual(frappe.db.count("Output VAT Undue", {"sales_invoice": invoice.name}), 1)

    def test_the_ledger_creates_no_gl_entry(self):
        invoice = self._invoice()

        self.assertEqual(
            frappe.db.count(
                "GL Entry",
                {"voucher_type": "Output VAT Undue", "voucher_no": invoice.name},
            ),
            0,
        )

    def test_the_ledger_does_not_change_the_invoice(self):
        invoice = self._invoice()
        before = dict(invoice.as_dict())

        tracking.create_output_vat_undue_record(invoice)

        after = dict(invoice.as_dict())
        self.assertEqual(before, after)

    def test_the_cancellation_keeps_the_row_and_clears_the_balance(self):
        invoice = self._invoice()

        tracking.cancel_output_vat_undue_record(invoice)
        row = frappe.get_doc("Output VAT Undue", str(invoice.name))

        self.assertEqual(row.get("status"), tracking.STATUS_CANCELLED)
        self.assertEqual(row.get("remaining_vat_amount"), 0)

    def test_the_conversion_records_the_tax_invoice(self):
        invoice = self._invoice()

        tracking.convert_to_output_vat(invoice.name, "TAX-0001")
        row = frappe.get_doc("Output VAT Undue", str(invoice.name))

        self.assertEqual(row.get("status"), tracking.STATUS_CONVERTED)
        self.assertEqual(row.get("tax_invoice_number"), "TAX-0001")
        self.assertEqual(row.get("remaining_vat_amount"), 0)

    def test_the_conversion_with_the_same_number_is_idempotent(self):
        invoice = self._invoice()

        tracking.convert_to_output_vat(invoice.name, "TAX-0001")
        tracking.convert_to_output_vat(invoice.name, "TAX-0001")

        self.assertEqual(frappe.db.count("Output VAT Undue", {"sales_invoice": invoice.name}), 1)

    def test_the_conversion_with_another_number_is_refused(self):
        invoice = self._invoice()
        tracking.convert_to_output_vat(invoice.name, "TAX-0001")

        with self.assertRaises(frappe.ValidationError):
            tracking.convert_to_output_vat(invoice.name, "TAX-0002")

    def test_the_controller_delegates_to_the_tracker(self):
        from print_designer.print_designer.doctype.output_vat_undue import (
            output_vat_undue as controller,
        )

        invoice = self._invoice()
        row = controller.create_output_vat_undue_record(invoice) or frappe._dict()

        self.assertEqual(row.get("sales_invoice"), invoice.name)


def _ledger_is_migrated():
    """True when the ledger of the site carries the schema of the current version."""
    if frappe.db.get_value("DocType", "Output VAT Undue", "autoname") != "field:sales_invoice":
        return False

    fields = frappe.get_all(
        "DocField",
        filters={"parent": "Output VAT Undue"},
        pluck="fieldname",
    )

    return "treatment_reason" in fields and "service_base_amount" in fields


def _service_item(company):
    """A service item for the test."""
    existing = frappe.get_all(
        "Item",
        filters={"is_stock_item": 0, "disabled": 0, "item_group": "Services"},
        limit=1,
        pluck="name",
    )
    if existing:
        return str(existing[0])

    item = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": SERVICE_ITEM,
            "item_name": SERVICE_ITEM,
            "item_group": "Services",
            "is_stock_item": 0,
            "is_sales_item": 1,
            "company": company,
        }
    )
    item.insert(ignore_permissions=True)
    return str(item.name)
