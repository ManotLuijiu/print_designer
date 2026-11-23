"""Regression tests of the profile-aware print format suggestion.

The suggestion is advisory: it preselects a format in the print selector
of the print view.  It never changes the default print format of a
DocType and it never touches the tax workflow.

The tests cover the matching rules:

* a format without a profile is a general purpose template and is never
  suggested,
* a format with a profile matches only a document that carries the same
  profile,
* a transaction that the workflow could not classify keeps the manual
  selection.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.api.print_format_suggestion import (
    get_print_format_suggestions,
    get_profile_aware_formats,
    matches_profile,
    suggest_formats,
)
from print_designer.custom.print_format_profile import (
    DIRECTION_FIELD,
    TYPE_FIELD,
    classify_transaction,
    install_profile_fields,
)


class TestProfileSuggestion(FrappeTestCase):
    """The suggestion matches a format against the profile of a document."""

    SERVICE_ITEM = "PD-SUGGESTION-SERVICE"
    COMPANY = "_Test Company"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        install_profile_fields()

    def setUp(self):
        self.created_items: list[str] = []
        self.created_invoices: list[str] = []

    def tearDown(self):
        for name in self.created_invoices:
            if frappe.db.exists("Sales Invoice", name):
                frappe.delete_doc("Sales Invoice", name, ignore_permissions=True, force=True)
        for name in self.created_items:
            if frappe.db.exists("Item", name):
                frappe.delete_doc("Item", name, ignore_permissions=True, force=True)

    def _make_service_item(self) -> None:
        """An item that the tax workflow calls a service."""
        doc = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": self.SERVICE_ITEM,
                "item_name": "PD Suggestion Service",
                "item_group": "All Item Groups",
            }
        )
        doc.set("is_stock_item", 0)
        doc.set("pd_custom_is_service_item", 1)
        doc.insert(ignore_permissions=True)
        self.created_items.append(self.SERVICE_ITEM)

    def _make_services_invoice(self):
        """A Sales Invoice of a service item."""
        self._make_service_item()

        doc = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "customer": "_Test Customer",
                "company": self.COMPANY,
                "items": [{"item_code": self.SERVICE_ITEM, "qty": 1, "rate": 100}],
            }
        )
        doc.insert(ignore_permissions=True)
        self.created_invoices.append(str(doc.name))
        return doc

    def _make_format(
        self,
        name: str,
        doc_type: str = "Payment Entry",
        direction: str | None = None,
        transaction_type: str | None = None,
    ) -> None:
        frappe.delete_doc("Print Format", name, ignore_permissions=True, force=True)

        doc = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": name,
                "doc_type": doc_type,
                "module": "Accounts",
                "print_designer": 1,
                "print_format_type": "Jinja",
                "print_designer_body": json_body(),
            }
        )
        if direction:
            doc.set(DIRECTION_FIELD, direction)
        if transaction_type:
            doc.set(TYPE_FIELD, transaction_type)

        doc.insert(ignore_permissions=True)

    def test_a_format_without_a_profile_is_never_suggested(self):
        self._make_format("PD Suggestion General")

        result = get_profile_aware_formats("Payment Entry")

        self.assertNotIn("PD Suggestion General", result["suggestions"])

    def test_a_format_without_a_profile_remains_selectable(self):
        """A general purpose template stays in the list of the formats.

        The plan of Phase 2 asks that the existing formats without a
        profile remain selectable: they are general purpose templates,
        they are simply never suggested.
        """
        self._make_format("PD Suggestion General Selectable")

        result = get_profile_aware_formats("Payment Entry")

        entries = {item["name"]: item for item in result["formats"]}

        self.assertIn("PD Suggestion General Selectable", entries)
        self.assertIsNone(entries["PD Suggestion General Selectable"]["direction"])
        self.assertIsNone(entries["PD Suggestion General Selectable"]["transaction_type"])
        self.assertNotIn("PD Suggestion General Selectable", result["suggestions"])

    def test_a_new_format_does_not_get_a_profile(self):
        """A format that nobody profiled stays without a profile.

        Frappe fills the value of a new Select with its first option.  A
        profile field that started with "Pay" or with "Services" would
        give every new format a profile, and a general purpose template
        would be suggested as if it were transaction specific.
        """
        self._make_format("PD Suggestion No Profile")

        stored = frappe.db.get_value(
            "Print Format",
            "PD Suggestion No Profile",
            [DIRECTION_FIELD, TYPE_FIELD],
        ) or [None, None]

        self.assertFalse(stored[0])
        self.assertFalse(stored[1])

    def test_a_matching_profile_is_suggested(self):
        self._make_format(
            "PD Suggestion Receive Services",
            direction="Receive",
            transaction_type="Services",
        )

        result = get_profile_aware_formats("Payment Entry")
        suggestions = suggest_formats(
            result["formats"], {"direction": "Receive", "transaction_type": "Services"}
        )

        self.assertIn("PD Suggestion Receive Services", suggestions)

    def test_a_format_of_another_direction_is_not_suggested(self):
        self._make_format(
            "PD Suggestion Pay Services", direction="Pay", transaction_type="Services"
        )

        result = get_profile_aware_formats("Payment Entry")
        suggestions = suggest_formats(
            result["formats"], {"direction": "Receive", "transaction_type": "Services"}
        )

        self.assertNotIn("PD Suggestion Pay Services", suggestions)

    def test_the_profile_of_the_format_is_reported(self):
        self._make_format(
            "PD Suggestion Receive Goods",
            direction="Receive",
            transaction_type="Goods",
        )

        result = get_profile_aware_formats("Payment Entry")

        entries = {item["name"]: item for item in result["formats"]}
        self.assertEqual(entries["PD Suggestion Receive Goods"]["direction"], "Receive")
        self.assertEqual(entries["PD Suggestion Receive Goods"]["transaction_type"], "Goods")

    def test_a_document_without_a_profile_suggests_nothing(self):
        self._make_format(
            "PD Suggestion Receive Services 2",
            direction="Receive",
            transaction_type="Services",
        )

        result = get_profile_aware_formats("Payment Entry", "does-not-exist")

        self.assertEqual(result["suggestions"], [])
        self.assertIsNone(result["profile"]["direction"])

    def test_the_endpoint_returns_the_profile_of_the_document(self):
        """The endpoint classifies the document that it is given.

        The endpoint is called with the name of a document of the site, so
        the proof uses a real document: a Sales Invoice of a service item
        carries the profile that the suggestion matches.
        """
        self._make_format(
            "PD Suggestion Sales Services",
            doc_type="Sales Invoice",
            transaction_type="Services",
        )
        invoice = self._make_services_invoice()

        result = get_print_format_suggestions("Sales Invoice", invoice.name)

        self.assertTrue(result["available"])
        self.assertEqual(result["profile"]["transaction_type"], "Services")
        self.assertIn("PD Suggestion Sales Services", result["suggestions"])

    def test_the_endpoint_of_the_suggestion_is_whitelisted(self):
        """The print view calls the endpoint over HTTP.

        An endpoint that is not whitelisted is refused by the request
        handler before the function starts, so the call of the client
        never reaches the code.
        """
        self.assertIn(get_print_format_suggestions, frappe.whitelisted)

    def test_the_matching_rules(self):
        profile = {"direction": "Receive", "transaction_type": "Services"}

        self.assertTrue(
            matches_profile({"direction": "Receive", "transaction_type": "Services"}, profile)
        )
        self.assertTrue(
            matches_profile({"direction": "Receive", "transaction_type": None}, profile)
        )
        self.assertFalse(matches_profile({"direction": None, "transaction_type": None}, profile))
        self.assertFalse(matches_profile({"direction": "Pay", "transaction_type": None}, profile))

    def test_an_unclassified_transaction_matches_nothing(self):
        profile = {"direction": None, "transaction_type": None}

        self.assertFalse(
            matches_profile({"direction": "Receive", "transaction_type": "Services"}, profile)
        )
        self.assertFalse(
            matches_profile({"direction": None, "transaction_type": "Services"}, profile)
        )

    def test_a_mixed_transaction_matches_nothing(self):
        profile = {"direction": "Receive", "transaction_type": None}

        self.assertFalse(
            matches_profile({"direction": None, "transaction_type": "Services"}, profile)
        )

    def test_the_suggestion_leaves_the_tax_and_ledger_data_unchanged(self):
        """The profile guides the layout, it never touches the transaction.

        The plan of Phase 2 asks for a Pay and a Receive example with
        actual WHT and retention values, and for the proof that the tax
        and the ledger data of the document stay unchanged.
        """
        for payment_type in ("Receive", "Pay"):
            with self.subTest(payment_type=payment_type):
                doc = frappe.get_doc(
                    {
                        "doctype": "Payment Entry",
                        "payment_type": payment_type,
                        "paid_amount": 1000,
                        "received_amount": 1000,
                        "deductions": [
                            {"description": "Withholding tax", "amount": 30},
                            {"description": "Retention", "amount": 50},
                        ],
                        "taxes": [
                            {"description": "VAT", "tax_amount": 70, "total": 70},
                        ],
                    }
                )

                before = self._transaction_snapshot(doc)

                profile = classify_transaction(doc)

                after = self._transaction_snapshot(doc)

                # The classification reads the transaction, it does not
                # change a value of it and it does not save it.
                self.assertEqual(before, after)
                self.assertEqual(doc.get("docstatus"), 0)
                self.assertFalse(frappe.db.exists("Payment Entry", doc.get("name")))

                # The direction of the profile comes from the transaction.
                self.assertEqual(profile["direction"], payment_type)

    def _transaction_snapshot(self, doc) -> dict:
        """The values of a transaction that a classification may not touch."""
        return {
            "payment_type": doc.get("payment_type"),
            "paid_amount": doc.get("paid_amount"),
            "received_amount": doc.get("received_amount"),
            "deductions": [
                (row.get("description"), row.get("amount")) for row in (doc.get("deductions") or [])
            ],
            "taxes": [
                (row.get("description"), row.get("tax_amount")) for row in (doc.get("taxes") or [])
            ],
        }


def json_body() -> str:
    """A minimal Print Designer design payload."""
    import json

    return json.dumps(
        {
            "type": "page",
            "index": 0,
            "childrens": [
                {"id": "text", "type": "text", "isDynamic": True, "text": "{{doc.name}}"}
            ],
        }
    )
