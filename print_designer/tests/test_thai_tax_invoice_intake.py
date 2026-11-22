# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The tests of the intake of a tax invoice of Print Designer.

The intake of a tax invoice belongs to Print Designer since the relocation
of the Thai tax DocTypes.  The tests prove that:

- the DocType belongs to Print Designer and the controller of the site is the
  controller of Print Designer;
- every step that changes the state of the site answers a POST only;
- a step that may not be taken is refused before it touches the site;
- the workflow of the intake creates the purchase invoice of the intake with
  the right data and copies the attachment of the invoice;
- a failure leaves the invoice of the purchase undone and writes the reason
  of the failure on the intake;
- the sweep of the site reaches only the intakes that are verified and still
  pending.

The tests write their documents inside a savepoint, so the transaction of the
test leaves the site as it was.  The write of a state of the intake asks for a
commit of its own, so the commit of the test is muted while the test runs:
the documents of the test stay inside the transaction of the test and the
savepoint of the test undoes them.
"""

import unittest
from typing import Any, cast
from unittest.mock import patch

import frappe
from frappe.model.base_document import import_controller

from print_designer.custom.document_permission import (
    has_document_permission,
    require_document_write,
)
from print_designer.print_designer.doctype.thai_tax_invoice_intake.thai_tax_invoice_intake import (  # noqa: E501
    INTAKE,
    ThaiTaxInvoiceIntake,
    sweep_pending_intakes,
)

# The steps of the workflow that change the state of the site.
THE_STEPS = (
    (ThaiTaxInvoiceIntake, "set_verification_status"),
    (ThaiTaxInvoiceIntake, "sync_to_purchase_invoice"),
    (None, "sweep_pending_intakes"),
)

# The address of the attachment of the invoice.  The address points to a
# remote file, so the test writes no file on the disk of the site.
THE_ATTACHMENT = "https://example.com/thai-tax-invoice-intake.pdf"


def _the_methods_of(function: object) -> list[str] | None:
    """The HTTP methods the framework recorded for a whitelisted function."""
    from collections.abc import Callable

    return frappe.allowed_http_methods_for_whitelisted_func.get(cast(Callable[..., Any], function))


def _the_permission_of(allowed: tuple[str, ...]):
    """A stand-in for the right of the caller.

    Args:
            allowed: the doctypes the caller may use.

    Returns:
            The stand-in of ``frappe.has_permission``.
    """

    def _has_permission(doctype, ptype="read", doc=None, user=None, **kwargs):
        return doctype in allowed

    return _has_permission


class TestTheOwnershipOfTheIntake(unittest.TestCase):
    """The intake of a tax invoice belongs to Print Designer."""

    def test_the_intake_belongs_to_print_designer(self):
        """The Thai Tax Invoice Intake belongs to Print Designer."""
        self.assertEqual(
            frappe.db.get_value("DocType", INTAKE, "module"),
            "Print Designer",
        )

    def test_the_controller_of_the_site_is_the_controller_of_print_designer(self):
        """The controller that the site loads is the one of Print Designer."""
        controller = import_controller(INTAKE)

        self.assertIs(controller, ThaiTaxInvoiceIntake)

    def test_the_old_path_holds_the_class_of_print_designer(self):
        """The old path of Thai Business Suite holds the class of Print Designer."""
        from thai_business_suite.thai_business_suite.doctype.thai_tax_invoice_intake import (  # noqa: E501
            thai_tax_invoice_intake,
        )

        self.assertIs(
            cast(Any, thai_tax_invoice_intake.ThaiTaxInvoiceIntake),
            ThaiTaxInvoiceIntake,
        )
        self.assertIs(
            cast(Any, thai_tax_invoice_intake.sweep_pending_intakes),
            sweep_pending_intakes,
        )

    def test_the_naming_of_the_intake_is_unchanged(self):
        """The naming series of the intake is the one it had."""
        self.assertEqual(
            frappe.db.get_value(
                "DocField",
                {"parent": INTAKE, "fieldname": "naming_series"},
                ["default", "options"],
            ),
            ("TTI-.DBEYY.DMM.-", "TTI-.DBEYY.DMM.-"),
        )

    def test_the_client_workflow_lives_in_print_designer(self):
        """The client script of the intake lives in Print Designer."""
        import os

        path = os.path.join(
            frappe.get_module_path("Print Designer"),
            "doctype",
            "thai_tax_invoice_intake",
            "thai_tax_invoice_intake.js",
        )

        self.assertTrue(os.path.exists(path), f"{path} does not exist")


class TestTheStepsOfTheIntake(unittest.TestCase):
    """Every step of the intake answers a POST only."""

    def test_every_step_of_the_intake_answers_a_post_only(self):
        """Every step of the workflow answers a POST and nothing else."""
        for holder, name in THE_STEPS:
            with self.subTest(step=name):
                function = (
                    getattr(holder, name, None)
                    if holder
                    else getattr(
                        __import__(
                            "print_designer.print_designer.doctype."
                            "thai_tax_invoice_intake.thai_tax_invoice_intake",
                            fromlist=["*"],
                        ),
                        name,
                    )
                )

                self.assertIsNotNone(function, f"{name} is missing")
                self.assertEqual(_the_methods_of(function), ["POST"])


class TestTheGuardsOfTheIntake(unittest.TestCase):
    """A step of the intake is refused before it touches the site."""

    def test_the_verification_is_refused_without_the_right_to_write_the_intake(self):
        """The verification of the state needs the right to write the intake."""
        with patch.object(frappe, "has_permission", _the_permission_of(())):
            with self.assertRaises(frappe.PermissionError):
                require_document_write(INTAKE, "TTI-6911-00001")

    def test_the_right_of_a_document_that_is_not_there_is_no_right(self):
        """A document that is not on the site is answered with no right."""

        def _the_missing_document(doctype, ptype="read", doc=None, user=None, **kwargs):
            raise frappe.DoesNotExistError(f"{doctype} {doc}")

        with patch.object(frappe, "has_permission", _the_missing_document):
            self.assertFalse(has_document_permission(INTAKE, "write", "TTI-6911-99999"))

    def test_the_sweep_is_refused_without_the_role_of_the_system_manager(self):
        """The sweep of the site needs the role of the System Manager."""
        with patch.object(frappe, "get_roles", return_value=["Accounts User"]):
            with patch.object(frappe, "get_all") as get_all:
                with self.assertRaises(frappe.PermissionError):
                    sweep_pending_intakes()

        # The refusal comes before the sweep reads a single intake.
        self.assertEqual(
            [call for call in get_all.call_args_list if call.args[0] == INTAKE],
            [],
        )


class TestTheWorkflowOfTheIntake(unittest.TestCase):
    """The workflow of the intake books the invoice of the supplier."""

    SAVEPOINT = "pd_intake_test"

    @classmethod
    def setUpClass(cls):
        cls.company = cls._the_company()
        cls.supplier = cls._the_supplier()
        cls.item = cls._the_item()
        cls.expense_account = cls._the_account("Expense Account")
        cls.tax_account = cls._the_account("Tax")

    @classmethod
    def _the_company(cls) -> str:
        """A company with a chart of accounts."""
        for company in frappe.get_all(
            "Company", filters={"name": ["like", "_Test%"]}, pluck="name", limit=20
        ):
            if frappe.db.get_value("Company", company, "default_receivable_account"):
                return company

        raise unittest.SkipTest("no test company with a chart of accounts")

    @classmethod
    def _the_supplier(cls) -> str:
        """A supplier of the site."""
        suppliers = frappe.get_all("Supplier", pluck="name", limit=100)

        if not suppliers:
            raise unittest.SkipTest("no supplier on this site")

        return suppliers[0]

    @classmethod
    def _the_item(cls) -> str:
        """An item that is not a stock item."""
        items = frappe.get_all(
            "Item",
            filters={"is_stock_item": 0, "disabled": 0},
            pluck="name",
            limit=50,
        )

        if not items:
            raise unittest.SkipTest("no non stock item on this site")

        return items[0]

    @classmethod
    def _the_account(cls, account_type: str) -> str:
        """A leaf account of the test company."""
        accounts = frappe.get_all(
            "Account",
            filters={
                "company": cls.company,
                "account_type": account_type,
                "is_group": 0,
                "disabled": 0,
            },
            pluck="name",
            limit=50,
        )

        if not accounts:
            raise unittest.SkipTest(f"no {account_type} account in {cls.company}")

        return accounts[0]

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.savepoint(self.SAVEPOINT)

        # The write of a state of the intake asks for a commit of its own.
        # The commit is muted while the test runs, so the documents of the
        # test stay inside the transaction of the test and the savepoint of
        # the test undoes them.
        self._muted_commit = patch.object(frappe.db, "commit", lambda *a, **k: None)
        self._muted_commit.start()

    def tearDown(self):
        self._muted_commit.stop()
        frappe.db.rollback(save_point=self.SAVEPOINT)
        frappe.set_user("Administrator")

    def _the_intake(self, **values: Any) -> Any:
        """An intake of the site, with the values of the test."""
        fields = {
            "company": self.company,
            "invoice_type": "Purchase Tax Invoice",
            "party_type": "Supplier",
            "party": self.supplier,
            "bill_no": "PD-INTAKE-0001",
            "bill_date": "2026-11-22",
            "net_amount": 1000,
            "vat_amount": 70,
            "total_amount": 1070,
            "invoice_attachment": THE_ATTACHMENT,
            "expense_item": self.item,
            "expense_account": self.expense_account,
            "tax_account": self.tax_account,
        }
        fields.update(values)

        intake: Any = frappe.get_doc({"doctype": INTAKE, **fields})
        intake.insert(ignore_permissions=True)

        # The file of the invoice.  The address is remote, so the test
        # writes no file on the disk of the site.
        frappe.get_doc(
            {
                "doctype": "File",
                "file_name": "thai-tax-invoice-intake.pdf",
                "file_url": THE_ATTACHMENT,
                "attached_to_doctype": INTAKE,
                "attached_to_name": intake.name,
                "is_private": 1,
            }
        ).insert(ignore_permissions=True)

        return intake

    def _the_state_of_the_intake(self, intake: Any) -> dict[str, Any]:
        """The state of the intake, as the database holds it."""
        return cast(
            dict[str, Any],
            frappe.db.get_value(
                INTAKE,
                intake.name,
                [
                    "verification_status",
                    "sync_status",
                    "sync_error",
                    "purchase_invoice",
                ],
                as_dict=True,
            ),
        )

    def test_the_intake_is_verified(self):
        """The verification of the intake is written on the intake."""
        intake = self._the_intake()

        result = intake.set_verification_status(status="Verified")

        self.assertEqual(result["verification_status"], "Verified")
        self.assertEqual(self._the_state_of_the_intake(intake)["verification_status"], "Verified")

    def test_the_intake_is_rejected_with_a_remark(self):
        """The rejection of the intake carries the remark of the accountant."""
        intake = self._the_intake()

        intake.set_verification_status(status="Rejected", remark="The amount is wrong")

        state = self._the_state_of_the_intake(intake)
        self.assertEqual(state["verification_status"], "Rejected")
        self.assertEqual(
            frappe.db.get_value(INTAKE, intake.name, "verification_remark"),
            "The amount is wrong",
        )

    def test_an_unknown_verification_is_refused(self):
        """A verification that is neither Verified nor Rejected is refused."""
        intake = self._the_intake()

        with self.assertRaises(frappe.ValidationError):
            intake.set_verification_status(status="Maybe")

        self.assertEqual(self._the_state_of_the_intake(intake)["verification_status"], "Pending")

    def test_the_verification_of_a_synchronized_intake_is_refused(self):
        """The verification of an intake that is already booked is refused."""
        intake = self._the_intake()
        # The purchase invoice of an intake that is already booked is a
        # purchase invoice of the site, so the link is not checked here.
        intake.purchase_invoice = "ACC-PINV-2026-00001"

        with self.assertRaises(frappe.ValidationError):
            intake.set_verification_status(status="Rejected")

        self.assertEqual(self._the_state_of_the_intake(intake)["verification_status"], "Pending")

    def test_the_intake_creates_the_purchase_invoice_of_the_supplier(self):
        """The intake creates the purchase invoice of the invoice of the supplier."""
        intake = self._the_intake()
        intake.set_verification_status(status="Verified")

        result = intake.sync_to_purchase_invoice()

        invoice: Any = frappe.get_doc("Purchase Invoice", result["purchase_invoice"])
        self.assertEqual(invoice.supplier, self.supplier)
        self.assertEqual(invoice.bill_no, "PD-INTAKE-0001")
        self.assertEqual(len(invoice.items), 1)
        self.assertEqual(invoice.items[0].item_code, self.item)
        self.assertEqual(invoice.items[0].expense_account, self.expense_account)
        self.assertEqual(len(invoice.taxes), 1)
        self.assertEqual(invoice.taxes[0].account_head, self.tax_account)

        state = self._the_state_of_the_intake(intake)
        self.assertEqual(state["purchase_invoice"], result["purchase_invoice"])
        self.assertEqual(state["sync_status"], "Synced")
        self.assertEqual(state["sync_error"], "")

    def test_the_attachment_of_the_invoice_is_copied_to_the_purchase_invoice(self):
        """The attachment of the invoice is copied to the purchase invoice."""
        intake = self._the_intake()
        intake.set_verification_status(status="Verified")

        result = intake.sync_to_purchase_invoice()

        copies = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Purchase Invoice",
                "attached_to_name": result["purchase_invoice"],
            },
            pluck="file_url",
        )

        self.assertEqual(copies, [THE_ATTACHMENT])

    def test_the_second_synchronization_of_the_intake_is_refused(self):
        """An intake that carries a purchase invoice refuses a second one."""
        intake = self._the_intake()
        intake.set_verification_status(status="Verified")
        intake.sync_to_purchase_invoice()

        with self.assertRaises(frappe.ValidationError):
            intake.sync_to_purchase_invoice()

    def test_the_intake_that_is_not_verified_is_refused(self):
        """An intake that is not verified is not synchronized."""
        intake = self._the_intake()

        with self.assertRaises(frappe.ValidationError):
            intake.sync_to_purchase_invoice()

        self.assertEqual(self._the_state_of_the_intake(intake)["sync_status"], "Pending")

    def test_the_sales_tax_invoice_is_refused(self):
        """The workflow synchronizes the purchase tax invoices only."""
        intake = self._the_intake(invoice_type="Sales Tax Invoice")
        intake.set_verification_status(status="Verified")

        with self.assertRaises(frappe.ValidationError):
            intake.sync_to_purchase_invoice()

    def test_the_party_must_be_a_supplier(self):
        """The party of the intake must be a supplier."""
        intake = self._the_intake(party_type="Customer")
        intake.set_verification_status(status="Verified")

        with self.assertRaises(frappe.ValidationError):
            intake.sync_to_purchase_invoice()

    def test_the_total_must_match_the_amounts_of_the_invoice(self):
        """The total of the intake must be the net amount and the VAT."""
        intake = self._the_intake(total_amount=1200)
        intake.set_verification_status(status="Verified")

        with self.assertRaises(frappe.ValidationError):
            intake.sync_to_purchase_invoice()

    def test_the_vat_account_is_required_when_the_invoice_carries_a_vat(self):
        """The VAT account of the intake is required when the invoice has a VAT."""
        intake = self._the_intake(tax_account=None)
        intake.set_verification_status(status="Verified")

        with self.assertRaises(frappe.ValidationError):
            intake.sync_to_purchase_invoice()

    def test_the_stock_item_is_refused(self):
        """The intake books a service, not a stock item."""
        stock_items = frappe.get_all(
            "Item", filters={"is_stock_item": 1, "disabled": 0}, pluck="name", limit=5
        )

        if not stock_items:
            raise unittest.SkipTest("no stock item on this site")

        intake = self._the_intake(expense_item=stock_items[0])
        intake.set_verification_status(status="Verified")

        with self.assertRaises(frappe.ValidationError):
            intake.sync_to_purchase_invoice()

    def test_the_site_that_asks_for_a_purchase_order_refuses_the_invoice(self):
        """A site that asks for a purchase order refuses the invoice."""
        intake = self._the_intake()
        intake.set_verification_status(status="Verified")

        with patch.object(
            frappe.db,
            "get_single_value",
            lambda doctype, fieldname, *a, **k: "Yes" if doctype == "Buying Settings" else None,
        ):
            with self.assertRaises(frappe.ValidationError):
                intake.sync_to_purchase_invoice()

    def test_the_failure_of_the_synchronization_leaves_no_invoice_behind(self):
        """A failure undoes the invoice of the purchase and writes the reason."""
        intake = self._the_intake()
        intake.set_verification_status(status="Verified")

        def _the_refusal(*args: Any, **kwargs: Any):
            raise frappe.ValidationError("The supplier is unknown.")

        with patch.object(ThaiTaxInvoiceIntake, "create_purchase_invoice", _the_refusal):
            with self.assertRaises(frappe.ValidationError):
                intake.sync_to_purchase_invoice()

        state = self._the_state_of_the_intake(intake)
        self.assertEqual(state["sync_status"], "Failed")
        self.assertIn("The supplier is unknown.", state["sync_error"])
        self.assertIsNone(state["purchase_invoice"])

    def test_the_sweep_reaches_the_verified_intakes_that_are_pending(self):
        """The sweep of the site reaches the verified intakes that are pending."""
        intake = self._the_intake()
        intake.set_verification_status(status="Verified")

        result = sweep_pending_intakes(company=self.company)

        self.assertGreaterEqual(result["processed"], 1)
        self.assertIn(
            intake.name,
            [row["name"] for row in result["results"]],
        )

        state = self._the_state_of_the_intake(intake)
        self.assertEqual(state["sync_status"], "Synced")

    def test_the_sweep_leaves_the_intake_that_is_not_verified_alone(self):
        """The sweep of the site leaves an intake that is not verified alone."""
        intake = self._the_intake()

        sweep_pending_intakes(company=self.company)

        self.assertEqual(self._the_state_of_the_intake(intake)["sync_status"], "Pending")
