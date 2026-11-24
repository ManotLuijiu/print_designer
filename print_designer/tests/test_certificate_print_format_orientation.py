import unittest

import frappe

from print_designer.patches import set_certificate_print_format_orientation as orientation_patch

CERTIFICATE_DOCTYPE = "Withholding Tax Certificate"
ORIENTATION_FIELD = "page_orientation"


class TestCertificatePrintFormatOrientation(unittest.TestCase):
    """The certificate print formats default to A4 Portrait."""

    def setUp(self):
        if not frappe.db.exists(
            "Custom Field", {"dt": "Print Format", "fieldname": ORIENTATION_FIELD}
        ):
            self.skipTest("page_orientation custom field is not installed on this site")
        self.created = []

    def tearDown(self):
        for name in self.created:
            if frappe.db.exists("Print Format", name):
                frappe.delete_doc("Print Format", name, force=True, ignore_permissions=True)
        self.created = []

    def _make_print_format(self, name, doc_type, orientation=None):
        print_format = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": name,
                "doc_type": doc_type,
                "print_format_type": "Jinja",
                "standard": "No",
                "disabled": 0,
            }
        )
        print_format.insert(ignore_permissions=True)
        # A new Print Format picks up the custom field default, so the legacy
        # state (no orientation stored) has to be written explicitly.
        frappe.db.sql(
            "UPDATE `tabPrint Format` SET page_orientation = %s WHERE name = %s",
            (orientation, name),
        )
        self.created.append(name)
        return name

    def _orientation_of(self, name):
        return frappe.db.get_value("Print Format", name, ORIENTATION_FIELD)

    def test_empty_certificate_format_gets_portrait(self):
        name = self._make_print_format("_Test Certificate Format Portrait", CERTIFICATE_DOCTYPE)

        orientation_patch.execute()

        self.assertEqual(self._orientation_of(name), "Portrait")

    def test_explicit_orientation_is_preserved(self):
        name = self._make_print_format(
            "_Test Certificate Format Landscape", CERTIFICATE_DOCTYPE, "Landscape"
        )

        orientation_patch.execute()

        self.assertEqual(self._orientation_of(name), "Landscape")

    def test_other_doctypes_are_not_touched(self):
        name = self._make_print_format("_Test Other Format Portrait", "Sales Invoice")

        orientation_patch.execute()

        self.assertFalse(self._orientation_of(name))

    def test_patch_is_idempotent(self):
        name = self._make_print_format("_Test Certificate Format Idempotent", CERTIFICATE_DOCTYPE)

        orientation_patch.execute()
        orientation_patch.execute()

        self.assertEqual(self._orientation_of(name), "Portrait")
