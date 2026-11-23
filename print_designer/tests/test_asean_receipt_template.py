"""Acceptance tests of the ASEAN Receipt default template.

The package is the first template of the Phase 2 export: a Print Format
document of Print Designer that the missing-only installer imports on a
fresh site.

The tests cover the properties of the package and of the installer:

* the package is a valid template and the installer discovers it,
* the package carries the dynamic company logo and no source branding, no
  sample document selection and no thumbnail,
* the package carries the transaction profile of a receipt,
* a fresh site installs the package,
* a site that already has the name keeps its own format,
* a template that refers to a field that does not exist yet is deferred,
* the companion manifest records the pre-release review of the plan.
"""

import json
import pathlib
import re
import tempfile
from unittest.mock import patch

import frappe
import yaml
from frappe.tests.utils import FrappeTestCase

from print_designer.default_templates_installer import (
    discover_template_files,
    install_missing_default_formats,
    validate_template_document,
)

TEMPLATE_PATH = (
    pathlib.Path(frappe.get_app_path("print_designer"))
    / "default_templates"
    / "asean_business_suite"
    / "receipt.json"
)

ASSETS_PATH = TEMPLATE_PATH.with_suffix(".assets.yaml")

TEMPLATE_NAME = "ASEAN Receipt"


class TestTheAseanReceiptPackage(FrappeTestCase):
    """The ASEAN Receipt package and the installer that imports it."""

    def setUp(self):
        self.data = json.loads(TEMPLATE_PATH.read_text())

    @staticmethod
    def _remove_the_format():
        """Remove the package from the site, if it is installed."""
        if frappe.db.exists("Print Format", TEMPLATE_NAME):
            frappe.delete_doc("Print Format", TEMPLATE_NAME, ignore_permissions=True, force=True)

    def tearDown(self):
        if frappe.db.exists("Print Format", TEMPLATE_NAME):
            frappe.delete_doc("Print Format", TEMPLATE_NAME, ignore_permissions=True, force=True)

    def test_the_package_is_a_valid_template(self):
        candidate, error = validate_template_document(self.data, "receipt.json")

        self.assertIsNone(error)
        self.assertIsNotNone(candidate)
        self.assertEqual((candidate or {}).get("name"), TEMPLATE_NAME)
        self.assertEqual((candidate or {}).get("doc_type"), "Payment Entry")

    def test_the_installer_discovers_the_package(self):
        discovered = [relative for relative, _ in discover_template_files("print_designer")]

        self.assertIn("asean_business_suite/receipt.json", discovered)

    def test_the_package_uses_the_dynamic_company_logo(self):
        body = json.loads(self.data["print_designer_body"])
        header = json.loads(self.data["print_designer_header"])

        images = []
        for payload in (body, header):
            images.extend(_find_images(payload))

        self.assertTrue(images)

        for image in images:
            self.assertTrue(image["isDynamic"])
            binding = image.get("image") or {}
            self.assertEqual(binding.get("doctype"), "Company")
            self.assertEqual(binding.get("fieldname"), "company_logo")
            self.assertEqual(binding.get("parentField"), "company")
            self.assertEqual(binding.get("file_url"), "")

    def test_the_package_has_no_source_branding(self):
        serialized = json.dumps(self.data)

        self.assertNotIn("/files/", serialized)

        # No image binding carries a file of the site that saved the format.
        for image in _find_images(json.loads(self.data["print_designer_body"])):
            binding = image.get("image") or {}
            for key in ("value", "name", "file_name", "file_url", "modified"):
                self.assertFalse(binding.get(key))

    def test_the_package_has_no_sample_document_and_no_thumbnail(self):
        settings = json.loads(self.data["print_designer_settings"])

        self.assertIsNone(settings.get("currentDoc"))
        self.assertEqual(self.data.get("print_designer_preview_img"), "")

    def test_the_package_carries_a_renderable_layout(self):
        """The package must carry a layout the renderer can lay out.

        A stub payload renders an empty page, so the payload of the
        package is checked for the structure that the renderer reads.
        """
        payload = json.loads(self.data["print_designer_print_format"])

        self.assertIn("header", payload)
        self.assertIn("body", payload)
        self.assertIn("footer", payload)

        for variant in ("firstPage", "oddPage", "evenPage", "lastPage"):
            self.assertIn(variant, payload["header"], variant)
            self.assertIn(variant, payload["footer"], variant)

        # The header carries the logo, the title and the company.
        self.assertTrue(payload["header"]["firstPage"])

        # The body is a list of page wrappers, each with its children.
        self.assertTrue(payload["body"])
        for page in payload["body"]:
            self.assertTrue(page.get("childrens"))

        # The leaves carry the geometry that positions them on the page.
        leaves = _find_leaves(payload["body"])
        self.assertTrue(leaves)
        for leaf in leaves:
            self.assertIn("startX", leaf)
            self.assertIn("startY", leaf)
            self.assertIsNotNone(leaf.get("width"))
            self.assertIsNotNone(leaf.get("height"))

    def test_the_installed_package_renders_its_content(self):
        """The package must render, not produce a blank page.

        This is the only proof that the package carries a usable layout:
        every other check of the package looks at its parts, and the
        renderer is what turns the parts into a page.
        """
        self._remove_the_format()
        install_missing_default_formats(dry_run=False)

        print_format = frappe.get_doc("Print Format", TEMPLATE_NAME)
        html = _render(print_format, _receipt_document())

        self.assertGreater(len(html), 5000)

        for label in (
            "Payment Receipt",
            "Reference No",
            "Posting Date",
            "Party Name",
            "Mode of Payment",
            "Received Amount",
            "In Words",
            "Remarks",
        ):
            self.assertIn(label, html, f"the receipt does not render {label}")

        # The values of the document reach the page.
        self.assertIn("PD-RCPT-0001", html)
        self.assertIn("PD Receipt Customer", html)
        self.assertIn("12,500", html)
        self.assertIn("Twelve Thousand Five Hundred Only", html)
        self.assertIn("Receipt for services rendered", html)

    def test_the_installed_package_keeps_the_dynamic_logo_binding(self):
        """The installed format keeps the logo of the destination company."""
        self._remove_the_format()
        install_missing_default_formats(dry_run=False)

        installed = frappe.get_doc("Print Format", TEMPLATE_NAME)
        images = _find_images(json.loads(str(installed.get("print_designer_header") or "[]")))

        self.assertTrue(images)
        for image in images:
            binding = image.get("image") or {}
            self.assertEqual(binding.get("doctype"), "Company")
            self.assertEqual(binding.get("fieldname"), "company_logo")
            self.assertEqual(binding.get("parentField"), "company")

    def test_the_package_carries_the_profile_of_a_receipt(self):
        self.assertEqual(self.data.get("pd_custom_transaction_direction"), "Receive")
        self.assertEqual(self.data.get("pd_custom_transaction_type"), "Services")

    def test_the_amount_in_words_is_the_pair_of_a_receipt(self):
        settings = json.loads(self.data["print_designer_settings"])
        pairs = settings.get("numberToWordsFieldPairs") or []

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["source_field"], "received_amount")
        self.assertEqual(pairs[0]["target_field"], "in_words")

    def test_a_fresh_site_installs_the_package(self):
        # The package is not installed on this site yet.
        self._remove_the_format()

        results = install_missing_default_formats(dry_run=False)

        imported = [entry for entry in results["imported"] if entry.get("name") == TEMPLATE_NAME]
        self.assertTrue(imported, results)

        installed = frappe.get_doc("Print Format", TEMPLATE_NAME)
        self.assertEqual(installed.get("doc_type"), "Payment Entry")
        self.assertEqual(installed.get("pd_custom_transaction_direction"), "Receive")
        self.assertEqual(installed.get("pd_custom_transaction_type"), "Services")

    def test_a_site_that_has_the_name_keeps_its_own_format(self):
        existing = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": TEMPLATE_NAME,
                "doc_type": "Payment Entry",
                "module": "Accounts",
                "print_designer": 1,
                "print_format_type": "Jinja",
                "print_designer_body": "[]",
            }
        )
        existing.insert(ignore_permissions=True)

        results = install_missing_default_formats(dry_run=False)

        skipped = [entry for entry in results["existing"] if entry.get("name") == TEMPLATE_NAME]
        self.assertTrue(skipped, results)

        # The format of the site is untouched.
        self.assertEqual(
            frappe.get_doc("Print Format", TEMPLATE_NAME).get("print_designer_body"),
            "[]",
        )

    def test_a_dry_run_lists_the_package_without_installing_it(self):
        self._remove_the_format()

        results = install_missing_default_formats(dry_run=True)

        pending = [entry for entry in results["pending"] if entry.get("name") == TEMPLATE_NAME]
        self.assertTrue(pending, results)
        self.assertFalse(frappe.db.exists("Print Format", TEMPLATE_NAME))

    def test_a_package_of_a_missing_dependency_is_deferred(self):
        """The defer result of a template that needs a field that is missing.

        The plan of Phase 2 asks for a missing-dependency defer result next
        to the fresh install and the same-name skip.  A template that names
        a custom field of Print Designer that does not exist yet waits for
        the field instead of landing half filled on the site.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "asean_business_suite").mkdir(parents=True, exist_ok=True)

            deferred = json.loads(TEMPLATE_PATH.read_text())
            deferred["name"] = "ASEAN Receipt Deferred"
            deferred["print_designer_body"] = json.dumps(
                {
                    "type": "page",
                    "index": 0,
                    "childrens": [
                        {
                            "id": "text",
                            "type": "text",
                            "isDynamic": True,
                            "dynamicContent": [
                                {
                                    "fieldname": "pd_custom_field_that_is_missing",
                                    "fieldtype": "Data",
                                    "label": "Missing",
                                    "is_static": False,
                                    "value": "",
                                }
                            ],
                        }
                    ],
                }
            )
            (root / "asean_business_suite" / "receipt.json").write_text(
                json.dumps(deferred, indent=1)
            )

            with patch(
                "print_designer.default_templates_installer.get_templates_root",
                return_value=root,
            ):
                results = install_missing_default_formats(dry_run=False)

            self.assertEqual(results["imported"], [])

            entries = [
                entry for entry in results["deferred"] if entry["name"] == "ASEAN Receipt Deferred"
            ]
            self.assertEqual(len(entries), 1)
            self.assertIn("missing_fields", entries[0]["reason"])
            self.assertIn("pd_custom_field_that_is_missing", entries[0]["missing_fields"])

            # The template waits for its field, it does not land on the site.
            self.assertFalse(frappe.db.exists("Print Format", "ASEAN Receipt Deferred"))

    def test_the_manifest_ships_no_static_asset(self):
        """The plan asks for a companion manifest and no privacy risk.

        The plan of Phase 2 says that the privacy preserving asset
        creation and its rollback are only verified for the templates that
        actually ship static files.  The ASEAN Receipt ships none: its
        only image is the dynamic company logo.
        """
        manifest = yaml.safe_load(ASSETS_PATH.read_text())

        self.assertEqual(manifest["kind"], "print_designer_template_assets")
        self.assertEqual(manifest["template_file"], "receipt.json")
        self.assertEqual(manifest["template_name"], TEMPLATE_NAME)

        self.assertEqual(manifest["assets"], [])
        self.assertEqual(manifest["missing_assets"], [])

        logos = [
            image
            for image in manifest["dynamic_images"]
            if image["doctype"] == "Company" and image["fieldname"] == "company_logo"
        ]
        self.assertEqual(len(logos), 1)

    def test_the_manifest_records_the_review_before_the_release(self):
        """The plan asks for a review before an export is accepted.

        The plan of Phase 2 lists the parts of an export that are reviewed
        before it is accepted for a release: the remaining static text,
        the Jinja, the assets, the DocType fields and the renderer
        dependencies.  The manifest records the outcome of that review, so
        it may not lose one of them.
        """
        manifest = yaml.safe_load(ASSETS_PATH.read_text())

        review = manifest.get("review_before_release") or []

        self.assertTrue(review, "the manifest records no review before the release")

        # Every subject has a finding of its own.  A word scan over the
        # joined text could not tell five findings from one sentence that
        # names all of them.
        for subject in ("static text", "jinja", "assets", "doctype fields", "renderer"):
            self.assertTrue(
                any(subject in item.lower() for item in review),
                f"no finding covers {subject}",
            )

    def test_the_review_of_the_manifest_agrees_with_the_package(self):
        """The findings of the review must be true of the package.

        The review is a text, so a finding could describe a package that
        the site does not ship.  The findings that name the fields and the
        images are checked against the package and against the DocType.
        """
        manifest = yaml.safe_load(ASSETS_PATH.read_text())
        review = " ".join(manifest.get("review_before_release") or []).lower()

        # The finding names the fields that the design refers to, and
        # every one of them exists on the standard Payment Entry.
        named = set(re.findall(r"\b[a-z_]+\b", review)) & {
            "reference_no",
            "posting_date",
            "party_name",
            "mode_of_payment",
            "received_amount",
            "in_words",
            "remarks",
        }

        self.assertTrue(named, "the review names no field of the design")

        meta = frappe.get_meta("Payment Entry")
        for fieldname in sorted(named):
            self.assertTrue(
                meta.has_field(fieldname),
                f"{fieldname} does not exist on the standard Payment Entry",
            )

        # The finding says that the only image is the dynamic company
        # logo, so the package carries no other image.
        images = _find_images(json.loads(self.data["print_designer_body"] or "[]"))
        images += _find_images(json.loads(self.data["print_designer_header"] or "[]"))

        self.assertTrue(images)
        for image in images:
            binding = image.get("image") or {}
            self.assertEqual(binding.get("doctype"), "Company")
            self.assertEqual(binding.get("fieldname"), "company_logo")

    def test_the_package_carries_no_jinja(self):
        """The review of the Jinja is a finding, so it is proven here."""
        settings = json.loads(self.data.get("print_designer_settings") or "{}")

        self.assertEqual(settings.get("userProvidedJinja"), "")

        body = json.loads(self.data.get("print_designer_body") or "[]")
        self.assertNotIn("{{", json.dumps(body))
        self.assertNotIn("{%", json.dumps(body))


def _receipt_document():
    """A Payment Entry that carries the fields the receipt reads."""
    company = frappe.get_all("Company", pluck="name", limit=1)
    company = company[0] if company else None

    return frappe.get_doc(
        {
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "company": company,
            "posting_date": "2026-01-15",
            "paid_amount": 12500,
            "received_amount": 12500,
            "paid_to_account_currency": "THB",
            "party_type": "Customer",
            "party": "PD Receipt Customer",
            "party_name": "PD Receipt Customer",
            "mode_of_payment": "Cheque",
            "reference_no": "PD-RCPT-0001",
            "in_words": "Twelve Thousand Five Hundred Only",
            "remarks": "Receipt for services rendered",
        }
    )


def _render(print_format, doc):
    """Render a Print Designer format the way the print view renders it."""
    from frappe.utils.jinja import get_jenv

    jenv = get_jenv()
    template = frappe.call(
        frappe.get_hooks("get_print_format_template")[-1],
        jenv=jenv,
        print_format=print_format,
    )

    return frappe.get_attr(frappe.get_hooks("pdf_body_html")[-1])(
        jenv=jenv,
        template=template,
        print_format=print_format,
        args={"doc": doc, "doc_data": json.dumps(doc.as_dict(), default=str)},
    )


def _find_leaves(node):
    """The elements that carry content, without their containers."""
    found = []
    if isinstance(node, dict):
        if node.get("type") in ("text", "image", "table", "barcode"):
            found.append(node)
        for value in node.values():
            found.extend(_find_leaves(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_leaves(item))
    return found


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
