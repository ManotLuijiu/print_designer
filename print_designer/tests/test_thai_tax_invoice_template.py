"""The shipped Payment Entry Thai Tax Invoice package.

The package is a print format of the print format builder.  Frappe stores
the ``format_data`` of such a format as its JSON string, because the field
is a ``Code`` field and a list is not a value it can store.  The package
carried the value as a list, so the file could not be inserted at all and
only survived because the installer rewrote the value before the insert.

These tests prove that the package carries the shape that Frappe stores,
that it can be inserted without the help of the installer, that it renders
its content, and that the installer still normalizes a list that comes
from another source.
"""

import datetime
import json
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.default_templates_installer import (
    normalize_stored_values,
    validate_template_document,
)

APP_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = (
    APP_ROOT / "print_designer" / "default_templates" / "payment_entry_thai_tax_invoice.json"
)
TEMPLATE_NAME = "Payment Entry Thai Tax Invoice"


class TestTheThaiTaxInvoicePackage(FrappeTestCase):
    """The shipped package and the shape of its format data."""

    def setUp(self):
        self.data = json.loads(TEMPLATE_PATH.read_text())

    @staticmethod
    def _remove_the_format():
        """Remove the package from the site, if it is installed."""
        if frappe.db.exists("Print Format", TEMPLATE_NAME):
            frappe.delete_doc("Print Format", TEMPLATE_NAME, ignore_permissions=True, force=True)

    def tearDown(self):
        self._remove_the_format()

    def test_the_package_is_a_valid_template(self):
        candidate, error = validate_template_document(
            self.data, "payment_entry_thai_tax_invoice.json"
        )

        self.assertIsNone(error)
        self.assertIsNotNone(candidate)
        self.assertEqual((candidate or {}).get("name"), TEMPLATE_NAME)
        self.assertEqual((candidate or {}).get("doc_type"), "Payment Entry")

    def test_the_package_carries_the_shape_that_frappe_stores(self):
        """The format data is the JSON string that Frappe stores."""
        format_data = self.data.get("format_data")

        self.assertIsInstance(format_data, str)

        rows = json.loads(format_data)

        self.assertIsInstance(rows, list)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("fieldname"), "main_div")
        self.assertEqual(rows[0].get("fieldtype"), "HTML")
        self.assertIn("Tax Invoice", rows[0].get("options") or "")

    def test_the_package_is_insertable_without_the_help_of_the_installer(self):
        """The file is a valid document on its own.

        Without the shape that Frappe stores, the insert of the raw file
        fails with "Value for Format Data cannot be a list".
        """
        self._remove_the_format()

        frappe.flags.in_import = True
        try:
            doc = frappe.get_doc(json.loads(TEMPLATE_PATH.read_text()))
            doc.flags.ignore_validate = True
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.insert()
        finally:
            frappe.flags.in_import = False

        doc.reload()

        self.assertIsInstance(getattr(doc, "format_data"), str)
        self.assertIsInstance(json.loads(getattr(doc, "format_data")), list)

    def test_the_installed_package_renders_its_content(self):
        """The package prints the Thai tax invoice."""
        self._remove_the_format()

        frappe.flags.in_import = True
        try:
            doc = frappe.get_doc(json.loads(TEMPLATE_PATH.read_text()))
            doc.flags.ignore_validate = True
            doc.flags.ignore_permissions = True
            doc.flags.ignore_mandatory = True
            doc.insert()
        finally:
            frappe.flags.in_import = False

        doc.reload()

        html = _render_through_the_print_view(doc)

        self.assertIn("Tax Invoice", html)
        self.assertIn("Payment Details", html)
        self.assertIn("Received by", html)
        self.assertIn("Sarabun", html)

        # The placeholder of the designer is not the content of the format.
        self.assertNotIn("This will be populated by Print Designer", html)

    def test_the_installer_still_normalizes_a_list_of_another_source(self):
        """The installer stays the safety net for the templates of others."""
        data = {
            "doctype": "Print Format",
            "name": "PD Legacy Template",
            "doc_type": "Payment Entry",
            "module": "Print Designer",
            "format_data": [
                {"fieldname": "main_div", "fieldtype": "HTML", "options": "<div>x</div>"}
            ],
        }

        normalized = normalize_stored_values(data)

        self.assertIsInstance(normalized["format_data"], str)
        self.assertEqual(json.loads(normalized["format_data"]), data["format_data"])

    def test_the_package_carries_no_private_file_of_the_site(self):
        """The package holds nothing that belongs to the site that saved it."""
        serialized = json.dumps(self.data)

        self.assertNotIn("/files/", serialized)


def _render_through_the_print_view(print_format):
    """Render a format the way the print view renders it.

    The package is a format of the print format builder and carries no
    design of the designer, so the print view renders it with the
    standard template of the builder.  This helper follows the branches of
    ``frappe/www/printview.py`` so the proof is the real behaviour.
    """
    from frappe.utils.jinja import get_jenv
    from frappe.www.printview import make_layout, standard_format

    doc = _payment_entry()
    print_settings = frappe.get_single("Print Settings").as_dict()
    doc.flags.print_settings = print_settings

    jenv = get_jenv()

    template = None
    if hook_func := frappe.get_hooks("get_print_format_template"):
        template = frappe.call(hook_func[-1], jenv=jenv, print_format=print_format)

    if template:
        args = {"doc": doc, "doc_data": json.dumps(doc.as_dict(), default=str)}
    else:
        format_data = json.loads(getattr(print_format, "format_data"))
        setattr(doc, "format_data_map", {row.get("fieldname"): row for row in format_data})
        template = jenv.get_template(standard_format)
        args = {
            "doc": doc,
            "meta": frappe.get_meta(doc.doctype),
            "layout": make_layout(doc, frappe.get_meta(doc.doctype), format_data),
            "no_letterhead": 0,
            "trigger_print": 0,
            "letter_head": "",
            "footer": "",
            "print_settings": print_settings,
        }

    return frappe.get_attr(frappe.get_hooks("pdf_body_html")[-1])(
        jenv=jenv,
        template=template,
        print_format=print_format,
        args=args,
    )


def _payment_entry():
    """A Payment Entry that carries the fields the invoice reads."""
    company = frappe.get_all("Company", pluck="name", limit=1)
    company = company[0] if company else None

    return frappe.get_doc(
        {
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "company": company,
            "posting_date": datetime.date(2026, 1, 15),
            "paid_amount": 12500,
            "received_amount": 12500,
            "paid_to_account_currency": "THB",
            "party_type": "Customer",
            "party": "PD Tax Invoice Customer",
            "party_name": "PD Tax Invoice Customer",
            "mode_of_payment": "Cheque",
            "reference_no": "PD-TAXINV-0001",
            "remarks": "Probe",
        }
    )
