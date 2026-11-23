"""Regression tests for the export of a default template.

The export turns a saved Print Designer format into an installer-ready
``Print Format`` document.  The tests cover the properties that make the
document installable on another site:

* the sample document selection, the source thumbnail and the private file
  references are removed,
* the site-specific branding is replaced by the dynamic company logo,
* the transaction profile survives the export and the installation,
* the saved format is never modified by an export.
"""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.api.default_template_export import (
    build_template_document,
    export_as_default_template,
    get_categories,
)
from print_designer.custom.print_format_profile import (
    DIRECTION_FIELD,
    TYPE_FIELD,
    classify_transaction,
    validate_profile,
)
from print_designer.default_templates_installer import (
    collect_referenced_fields,
    insert_template,
    validate_template_document,
)


def _find_images(node):
    """The image elements of a design payload."""
    found = []
    if isinstance(node, dict):
        if node.get("type") == "image":
            found.append(node)
        for value in node.values():
            found.extend(_find_images(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_images(item))
    return found


def _design(*, branding: bool = True, sample_doc: str = "SINV-0001") -> str:
    """A small design payload with an optional branding image."""
    children = []
    if branding:
        children.append(
            {
                "id": "brand",
                "type": "image",
                "isDynamic": False,
                "image": {
                    "name": "file-abc",
                    "doctype": "File",
                    "fieldtype": "Attach Image",
                    "label": "Logo",
                    "value": "/files/logo.png",
                    "file_name": "logo.png",
                    "file_url": "/files/logo.png",
                    "modified": "2026-01-01 00:00:00",
                },
            }
        )

    children.append({"id": "text", "type": "text", "isDynamic": True, "text": "{{doc.name}}"})

    return json.dumps({"type": "page", "index": 0, "childrens": children})


def _settings(sample_doc: str = "SINV-0001") -> str:
    return json.dumps(
        {
            "currentDoc": sample_doc,
            "page": {"height": 1122.52, "width": 793.701},
            "schema_version": 1,
        }
    )


class TestDefaultTemplateExport(FrappeTestCase):
    """The export builds an installer-ready template."""

    def _source_format(self) -> dict:
        return {
            "doctype": "Print Format",
            "name": "Source Format",
            "doc_type": "Payment Entry",
            "module": "Accounts",
            "print_designer": 1,
            "print_format_type": "Jinja",
            "print_designer_body": _design(),
            "print_designer_header": "[]",
            "print_designer_footer": "[]",
            "print_designer_settings": _settings(),
            "print_designer_preview_img": "/files/thumbnail.jpg",
            "css": ".x { color: red; }",
        }

    def test_the_export_is_a_print_format_document(self):
        document = build_template_document(self._source_format(), "Public Name")

        self.assertEqual(document.get("doctype"), "Print Format")
        self.assertEqual(document.get("name"), "Public Name")
        self.assertEqual(document.get("doc_type"), "Payment Entry")

    def test_the_sample_document_selection_is_removed(self):
        document = build_template_document(self._source_format(), "Public Name")

        settings = json.loads(document["print_designer_settings"])
        self.assertIsNone(settings.get("currentDoc"))

    def test_the_source_thumbnail_is_removed(self):
        document = build_template_document(self._source_format(), "Public Name")

        self.assertEqual(document.get("print_designer_preview_img"), "")

    def test_the_branding_is_replaced_by_the_company_logo(self):
        document = build_template_document(self._source_format(), "Public Name")

        body = json.loads(document["print_designer_body"])
        image = body["childrens"][0]

        self.assertTrue(image["isDynamic"])
        self.assertEqual(image["image"]["doctype"], "Company")
        self.assertEqual(image["image"]["fieldname"], "company_logo")
        self.assertEqual(image["image"]["parentField"], "company")
        self.assertEqual(image["image"]["file_url"], "")

    def test_a_dynamic_company_logo_is_kept(self):
        source = self._source_format()
        source["print_designer_body"] = json.dumps(
            {
                "type": "page",
                "childrens": [
                    {
                        "id": "brand",
                        "type": "image",
                        "isDynamic": True,
                        "image": {
                            "name": "",
                            "doctype": "Company",
                            "fieldname": "company_logo",
                            "fieldtype": "Attach Image",
                            "label": "Company Logo",
                            "parentField": "company",
                            "value": "",
                            "file_name": "",
                            "file_url": "",
                            "modified": "",
                        },
                    }
                ],
            }
        )

        document = build_template_document(source, "Public Name")

        image = json.loads(document["print_designer_body"])["childrens"][0]
        self.assertTrue(image["isDynamic"])
        self.assertEqual(image["image"]["fieldname"], "company_logo")

    def test_the_export_passes_the_installer_validation(self):
        document = build_template_document(self._source_format(), "Public Name")

        candidate, error = validate_template_document(document, "receipt.json")

        self.assertIsNone(error)
        self.assertIsNotNone(candidate)
        self.assertEqual((candidate or {}).get("name"), "Public Name")

    def test_the_export_references_only_existing_fields(self):
        document = build_template_document(self._source_format(), "Public Name")

        references = collect_referenced_fields(document)

        # The dynamic company logo refers to the company of the document.
        self.assertIn("company", references)
        self.assertNotIn("company_logo", references)

        # Every reference of the export is a field of the DocType of the
        # format, so the template installs without a missing dependency.
        meta = frappe.get_meta(document["doc_type"])
        for fieldname in sorted(references):
            self.assertTrue(
                meta.has_field(fieldname),
                f"{fieldname} does not exist on {document['doc_type']}",
            )

    def test_the_endpoints_of_the_export_are_whitelisted(self):
        """The Desk calls the endpoints over HTTP.

        An endpoint that is not whitelisted is refused by the request
        handler before the function starts, so the call of the client
        never reaches the code.
        """
        for endpoint in (get_categories, export_as_default_template):
            self.assertIn(
                endpoint,
                frappe.whitelisted,
                f"{endpoint.__name__} is not whitelisted",
            )

    def test_the_export_keeps_the_generator_of_the_format(self):
        """The export keeps the renderer that the format was made with.

        Without the generator the installed template silently takes the
        default of the site, which is not the renderer of the design.
        """
        source = self._source_format()
        source["pdf_generator"] = "chrome"

        document = build_template_document(source, "Public Name")

        self.assertEqual(document.get("pdf_generator"), "chrome")

    def test_the_profile_is_persisted_with_the_template(self):
        document = build_template_document(
            self._source_format(),
            "Public Name",
            transaction_type="Services",
            transaction_direction="Receive",
        )

        self.assertEqual(document.get(TYPE_FIELD), "Services")
        self.assertEqual(document.get(DIRECTION_FIELD), "Receive")

    def test_a_format_without_a_profile_stays_general_purpose(self):
        document = build_template_document(self._source_format(), "Public Name")

        self.assertNotIn(TYPE_FIELD, document)
        self.assertNotIn(DIRECTION_FIELD, document)

    def test_the_saved_format_is_not_modified(self):
        source = self._source_format()
        before = json.dumps(source, sort_keys=True)

        build_template_document(source, "Public Name")

        self.assertEqual(json.dumps(source, sort_keys=True), before)

    def test_the_export_of_a_saved_format_keeps_the_source_unchanged(self):
        name = "PD Export Source Format"
        frappe.delete_doc("Print Format", name, ignore_permissions=True, force=True)

        doc = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": name,
                "doc_type": "Payment Entry",
                "module": "Accounts",
                "print_designer": 1,
                "print_format_type": "Jinja",
                "print_designer_body": _design(),
                "print_designer_settings": _settings(),
            }
        )
        doc.insert(ignore_permissions=True)

        body_before = doc.get("print_designer_body")
        settings_before = doc.get("print_designer_settings")

        result = export_as_default_template(name, template_name="Public Name")

        # The saved format still carries its own design.
        saved = frappe.get_doc("Print Format", name)
        self.assertEqual(saved.get("print_designer_body"), body_before)
        self.assertEqual(saved.get("print_designer_settings"), settings_before)

        # The export is a copy with the site specific parts removed.
        template = result["template"]
        self.assertEqual(template["name"], "Public Name")
        self.assertIsNone(json.loads(template["print_designer_settings"]).get("currentDoc"))

        frappe.delete_doc("Print Format", name, ignore_permissions=True, force=True)

    def test_the_export_rejects_a_non_print_designer_format(self):
        name = "PD Export Plain Format"
        frappe.delete_doc("Print Format", name, ignore_permissions=True, force=True)

        doc = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": name,
                "doc_type": "Payment Entry",
                "module": "Accounts",
                "print_format_type": "Jinja",
            }
        )
        doc.insert(ignore_permissions=True)

        with self.assertRaises(frappe.ValidationError):
            export_as_default_template(name)

        frappe.delete_doc("Print Format", name, ignore_permissions=True, force=True)

    def test_the_categories_are_the_folders_of_the_templates(self):
        categories = get_categories()

        values = [item["value"] for item in categories]
        self.assertIn("asean_business_suite", values)


class TestTransactionProfile(FrappeTestCase):
    """The profile of a format is validated against its DocType."""

    @staticmethod
    def _item_group() -> str:
        """An item group that exists on the site."""
        group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
        if group and isinstance(group, str):
            return group

        frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": "PD Profile Group",
                "parent_item_group": "All Item Groups",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

        return "PD Profile Group"

    def test_a_payment_entry_carries_a_direction(self):
        validate_profile("Payment Entry", "Receive", "Services")
        validate_profile("Payment Entry", "Pay", "Goods")

    def test_a_sales_invoice_has_no_direction(self):
        with self.assertRaises(frappe.ValidationError):
            validate_profile("Sales Invoice", "Receive", "Services")

    def test_a_sales_invoice_carries_a_type(self):
        validate_profile("Sales Invoice", None, "Services")
        validate_profile("Sales Invoice", None, "Goods")

    def test_another_doctype_carries_no_profile(self):
        with self.assertRaises(frappe.ValidationError):
            validate_profile("Quotation", None, "Services")

    def test_an_unknown_value_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            validate_profile("Payment Entry", "Sideways", "Services")

        with self.assertRaises(frappe.ValidationError):
            validate_profile("Payment Entry", "Receive", "Services Extended")

    def test_a_goods_transaction_is_classified_as_goods(self):
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": "PD-PROFILE-GOODS",
                "item_name": "PD Profile Goods",
                "item_group": self._item_group(),
            }
        )
        item.set("is_stock_item", 1)
        item.insert(ignore_permissions=True)

        doc = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "items": [{"item_code": "PD-PROFILE-GOODS"}],
            }
        )

        profile = classify_transaction(doc)

        self.assertEqual(profile["direction"], "Receive")
        self.assertEqual(profile["transaction_type"], "Goods")

        frappe.delete_doc("Item", "PD-PROFILE-GOODS", ignore_permissions=True, force=True)

    def test_a_service_transaction_is_classified_as_services(self):
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": "PD-PROFILE-SERVICE",
                "item_name": "PD Profile Service",
                "item_group": self._item_group(),
            }
        )
        # The tax workflow calls an item a service when the service flag or
        # the service item group says so.
        item.set("is_stock_item", 0)
        item.set("pd_custom_is_service_item", 1)
        item.insert(ignore_permissions=True)

        doc = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Pay",
                "items": [{"item_code": "PD-PROFILE-SERVICE"}],
            }
        )

        profile = classify_transaction(doc)

        self.assertEqual(profile["direction"], "Pay")
        self.assertEqual(profile["transaction_type"], "Services")

        frappe.delete_doc("Item", "PD-PROFILE-SERVICE", ignore_permissions=True, force=True)

    def test_an_item_that_is_neither_service_nor_stock_stays_unclassified(self):
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": "PD-PROFILE-NEUTRAL",
                "item_name": "PD Profile Neutral",
                "item_group": self._item_group(),
            }
        )
        item.set("is_stock_item", 0)
        item.set("pd_custom_is_service_item", 0)
        item.insert(ignore_permissions=True)

        doc = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Pay",
                "items": [{"item_code": "PD-PROFILE-NEUTRAL"}],
            }
        )

        profile = classify_transaction(doc)

        self.assertIsNone(profile["transaction_type"])

        frappe.delete_doc("Item", "PD-PROFILE-NEUTRAL", ignore_permissions=True, force=True)

    def test_a_transaction_without_items_stays_unclassified(self):
        doc = frappe.get_doc({"doctype": "Payment Entry", "payment_type": "Receive"})

        profile = classify_transaction(doc)

        self.assertEqual(profile["direction"], "Receive")
        self.assertIsNone(profile["transaction_type"])


class TestTheLinkedInvoiceClassification(FrappeTestCase):
    """A transaction is classified through the invoices that it pays.

    The plan of Phase 2 asks for a Goods Sales Invoice and for a Services
    receipt with a valid VAT point.  Both follow the real path of the
    workflow: a Sales Invoice through its own item rows, a receipt through
    the Sales Invoice that it pays, a supplier payment through its
    Purchase Invoice.
    """

    SERVICE_ITEM = "PD-PROFILE-LINKED-SERVICE"
    COMPANY = "_Test Company"
    WAREHOUSE = "_Test Warehouse - _TC"

    def setUp(self):
        self.created_items: list[str] = []
        self.created_invoices: list[tuple[str, str]] = []
        self._make_service_item()

    def tearDown(self):
        for doctype, name in self.created_invoices:
            if frappe.db.exists(doctype, name):
                frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
        for name in self.created_items:
            if frappe.db.exists("Item", name):
                frappe.delete_doc("Item", name, ignore_permissions=True, force=True)

    def _make_service_item(self) -> None:
        """An item that the tax workflow calls a service."""
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": self.SERVICE_ITEM,
                "item_name": "PD Profile Linked Service",
                "item_group": "All Item Groups",
            }
        )
        item.set("is_stock_item", 0)
        item.set("pd_custom_is_service_item", 1)
        item.insert(ignore_permissions=True)
        self.created_items.append(self.SERVICE_ITEM)

    def _make_sales_invoice(self, item_code: str, warehouse: str | None = None):
        """A draft Sales Invoice with one item row."""
        row = {"item_code": item_code, "qty": 1, "rate": 100}
        if warehouse:
            row["warehouse"] = warehouse

        doc = frappe.get_doc(
            {
                "doctype": "Sales Invoice",
                "customer": "_Test Customer",
                "company": self.COMPANY,
                "items": [row],
            }
        )
        doc.insert(ignore_permissions=True)
        self.created_invoices.append(("Sales Invoice", str(doc.name)))
        return doc

    def _make_purchase_invoice(self, item_code: str):
        """A draft Purchase Invoice with one item row."""
        doc = frappe.get_doc(
            {
                "doctype": "Purchase Invoice",
                "supplier": "_Test Supplier",
                "company": self.COMPANY,
                "bill_no": "PD-PROFILE-BILL-1",
                "bill_date": "2026-01-01",
                "items": [
                    {
                        "item_code": item_code,
                        "qty": 1,
                        "rate": 100,
                        "warehouse": self.WAREHOUSE,
                    }
                ],
            }
        )
        doc.insert(ignore_permissions=True)
        self.created_invoices.append(("Purchase Invoice", str(doc.name)))
        return doc

    def _make_receipt(self, reference_name: str):
        """A receipt that pays the Sales Invoice of the reference."""
        return frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "references": [
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": reference_name,
                    }
                ],
            }
        )

    def test_a_goods_sales_invoice_is_classified_as_goods(self):
        invoice = self._make_sales_invoice("_Test Stock Item", self.WAREHOUSE)

        profile = classify_transaction(invoice)

        # A Sales Invoice is a sale, it carries no direction.
        self.assertIsNone(profile["direction"])
        self.assertEqual(profile["transaction_type"], "Goods")

    def test_a_services_receipt_follows_the_invoice_that_it_pays(self):
        invoice = self._make_sales_invoice(self.SERVICE_ITEM)

        profile = classify_transaction(self._make_receipt(str(invoice.name)))

        self.assertEqual(profile["direction"], "Receive")
        self.assertEqual(profile["transaction_type"], "Services")

    def test_a_supplier_payment_follows_the_invoice_that_it_pays(self):
        invoice = self._make_purchase_invoice("_Test Stock Item")

        payment = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Pay",
                "references": [
                    {
                        "reference_doctype": "Purchase Invoice",
                        "reference_name": invoice.name,
                    }
                ],
            }
        )

        profile = classify_transaction(payment)

        self.assertEqual(profile["direction"], "Pay")
        self.assertEqual(profile["transaction_type"], "Goods")

    def test_a_receipt_with_invoices_that_disagree_stays_unclassified(self):
        """Mixed transactions keep the manual selection."""
        service_invoice = self._make_sales_invoice(self.SERVICE_ITEM)
        goods_invoice = self._make_sales_invoice("_Test Stock Item", self.WAREHOUSE)

        receipt = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "references": [
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": service_invoice.name,
                    },
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": goods_invoice.name,
                    },
                ],
            }
        )

        profile = classify_transaction(receipt)

        self.assertEqual(profile["direction"], "Receive")
        self.assertIsNone(profile["transaction_type"])

    def test_a_services_receipt_with_a_valid_vat_point(self):
        """A receipt that shows VAT due at payment keeps its tax data.

        The plan of Phase 2 asks for a Services receipt with a valid VAT
        point.  The receipt pays a Sales Invoice of a service, it carries
        the VAT row and the tax identity of the point, and the
        classification leaves all of it untouched.
        """
        invoice = self._make_sales_invoice(self.SERVICE_ITEM)

        receipt = frappe.get_doc(
            {
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "references": [
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": invoice.name,
                    }
                ],
                "taxes": [
                    {
                        "charge_type": "Actual",
                        "description": "VAT 7%",
                        "rate": 7,
                        "tax_amount": 7,
                        "total": 7,
                    }
                ],
                "pd_custom_tax_invoice_number": "PD-PROFILE-TAX-1",
                "pd_custom_tax_invoice_date": "2026-01-01",
            }
        )

        before = self._tax_snapshot(receipt)

        profile = classify_transaction(receipt)

        after = self._tax_snapshot(receipt)

        self.assertEqual(profile["direction"], "Receive")
        self.assertEqual(profile["transaction_type"], "Services")

        # The VAT point of the receipt is untouched by the classification.
        self.assertEqual(before, after)
        self.assertEqual(receipt.get("pd_custom_tax_invoice_number"), "PD-PROFILE-TAX-1")
        self.assertEqual(receipt.get("pd_custom_tax_invoice_date"), "2026-01-01")

        rows = receipt.get("taxes") or []
        self.assertEqual(rows[0].get("rate"), 7)
        self.assertEqual(rows[0].get("tax_amount"), 7)

        # The receipt is not saved by the classification.
        self.assertEqual(receipt.get("docstatus"), 0)
        self.assertFalse(frappe.db.exists("Payment Entry", receipt.get("name")))

    def _tax_snapshot(self, doc) -> dict:
        """The values of a receipt that a classification may not touch."""
        return {
            "taxes": [
                (row.get("description"), row.get("rate"), row.get("tax_amount"))
                for row in (doc.get("taxes") or [])
            ],
            "tax_invoice_number": doc.get("pd_custom_tax_invoice_number"),
            "tax_invoice_date": doc.get("pd_custom_tax_invoice_date"),
        }


class TestTheExportRoundTrip(FrappeTestCase):
    """A saved format is exported, shipped and installed on another site.

    The round trip is the proof that the export produces a template that
    the installer can import: the insert is the only step that can show a
    value that the column of a Print Format does not accept.
    """

    def setUp(self):
        self.source_name = "PD Round Trip Source"
        self.template_name = "PD Round Trip Template"

    def tearDown(self):
        for name in (self.source_name, self.template_name):
            if frappe.db.exists("Print Format", name):
                frappe.delete_doc("Print Format", name, ignore_permissions=True, force=True)

    def test_an_exported_format_is_installed_on_another_site(self):
        frappe.delete_doc("Print Format", self.source_name, ignore_permissions=True, force=True)

        doc = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": self.source_name,
                "doc_type": "Payment Entry",
                "module": "Accounts",
                "print_designer": 1,
                "print_format_type": "Jinja",
                "print_designer_body": _design(),
                "print_designer_header": "[]",
                "print_designer_footer": "[]",
                "print_designer_settings": _settings(),
                "print_designer_preview_img": "/files/thumbnail.jpg",
            }
        )
        doc.insert(ignore_permissions=True)

        result = export_as_default_template(
            self.source_name,
            template_name=self.template_name,
            category="asean_business_suite",
            transaction_type="Services",
            transaction_direction="Receive",
        )

        # The exported file is what the Desk action downloads.
        template = result["template"]
        self.assertEqual(result["filename"], "pd_round_trip_template.json")
        self.assertEqual(result["category"], "asean_business_suite")

        # The file passes the validation of the installer.
        candidate, error = validate_template_document(template, "round_trip.json")
        self.assertIsNone(error)
        self.assertIsNotNone(candidate)

        # The file survives the JSON round trip of the download.
        shipped = json.loads(json.dumps(template))
        self.assertEqual(shipped.get("name"), self.template_name)

        # The installer imports it.
        insert_template(candidate or {})
        installed = frappe.get_doc("Print Format", self.template_name)

        self.assertEqual(installed.get("doc_type"), "Payment Entry")
        self.assertEqual(installed.get("pd_custom_transaction_direction"), "Receive")
        self.assertEqual(installed.get("pd_custom_transaction_type"), "Services")
        self.assertEqual(installed.get("print_designer_preview_img"), "")

        # The branding of the source site is gone, the company logo is there.
        body = json.loads(installed.get("print_designer_body") or "[]")  # type: ignore[arg-type]
        images = _find_images(body)
        self.assertTrue(images)
        for image in images:
            binding = image.get("image") or {}
            self.assertEqual(binding.get("doctype"), "Company")
            self.assertEqual(binding.get("fieldname"), "company_logo")
            self.assertEqual(binding.get("file_url"), "")

        # The sample document of the source site is gone.
        settings = json.loads(installed.get("print_designer_settings") or "{}")  # type: ignore[arg-type]
        self.assertIsNone(settings.get("currentDoc"))

    def test_every_profile_of_the_plan_survives_the_round_trip(self):
        """Sales Invoice and Payment Entry, every combination of the plan.

        The plan of Phase 2 asks for both Sales Invoice transaction types
        and all four Payment Entry direction and type combinations.  Each
        of them has to survive the export and the installation unchanged.
        """
        combinations = [
            ("Sales Invoice", "Selling", None, "Services"),
            ("Sales Invoice", "Selling", None, "Goods"),
            ("Payment Entry", "Accounts", "Pay", "Services"),
            ("Payment Entry", "Accounts", "Pay", "Goods"),
            ("Payment Entry", "Accounts", "Receive", "Services"),
            ("Payment Entry", "Accounts", "Receive", "Goods"),
        ]

        for doc_type, module, direction, transaction_type in combinations:
            with self.subTest(
                doc_type=doc_type,
                direction=direction,
                transaction_type=transaction_type,
            ):
                self._round_trip_keeps_the_profile(doc_type, module, direction, transaction_type)

    def _round_trip_keeps_the_profile(self, doc_type, module, direction, transaction_type):
        """Export a format with a profile and install it again."""
        for name in (self.source_name, self.template_name):
            if frappe.db.exists("Print Format", name):
                frappe.delete_doc("Print Format", name, ignore_permissions=True, force=True)

        doc = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": self.source_name,
                "doc_type": doc_type,
                "module": module,
                "print_designer": 1,
                "print_format_type": "Jinja",
                "print_designer_body": _design(),
                "print_designer_settings": _settings(),
            }
        )
        doc.insert(ignore_permissions=True)

        result = export_as_default_template(
            self.source_name,
            template_name=self.template_name,
            category="asean_business_suite",
            transaction_type=transaction_type,
            transaction_direction=direction,
        )

        candidate, error = validate_template_document(result["template"], "round_trip.json")
        self.assertIsNone(error)

        insert_template(candidate or {})
        installed = frappe.get_doc("Print Format", self.template_name)

        self.assertEqual(installed.get("doc_type"), doc_type)
        self.assertEqual(installed.get("pd_custom_transaction_type"), transaction_type)
        self.assertEqual(installed.get("pd_custom_transaction_direction") or None, direction)

    def test_a_profile_that_does_not_belong_to_the_doctype_is_refused(self):
        """The plan validates the profile against the DocType of the format."""
        frappe.delete_doc("Print Format", self.source_name, ignore_permissions=True, force=True)

        doc = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": self.source_name,
                "doc_type": "Sales Invoice",
                "module": "Selling",
                "print_designer": 1,
                "print_format_type": "Jinja",
                "print_designer_body": _design(),
                "print_designer_settings": _settings(),
            }
        )
        doc.insert(ignore_permissions=True)

        # A Sales Invoice is always a sale, it has no direction.
        with self.assertRaises(frappe.ValidationError):
            export_as_default_template(
                self.source_name,
                template_name=self.template_name,
                transaction_direction="Pay",
                transaction_type="Services",
            )

        # A format of another DocType has no profile at all.
        frappe.delete_doc("Print Format", self.source_name, ignore_permissions=True, force=True)

        other = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": self.source_name,
                "doc_type": "Quotation",
                "module": "Selling",
                "print_designer": 1,
                "print_format_type": "Jinja",
                "print_designer_body": _design(),
                "print_designer_settings": _settings(),
            }
        )
        other.insert(ignore_permissions=True)

        with self.assertRaises(frappe.ValidationError):
            export_as_default_template(
                self.source_name,
                template_name=self.template_name,
                transaction_type="Services",
            )
