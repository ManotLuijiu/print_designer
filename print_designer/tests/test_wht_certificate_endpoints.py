"""The tests of the endpoints of the withholding tax certificate.

The certificate of the withholding tax of Thailand is a document of the
accounting of the site.  The endpoints that create it, and the endpoint that
shows what it would hold, ask the caller for the right to read the payment
entry and, for the creation, for the right to create the certificate.  The
refusal is made before the payment entry is loaded, and it is raised out of
the endpoint instead of being reported as a failure of the work.

The tests here check the shape of the endpoints and their refusal.  They do
not create a certificate; the creation is covered by the tests of the
creator of the certificate.
"""

import unittest
from unittest import mock

import frappe

from print_designer.custom import payment_entry_server_events, wht_certificate_generator

CERTIFICATE = "Withholding Tax Certificate"


def _the_methods_of(the_function) -> list:
    """The http methods that the endpoint accepts."""
    return frappe.allowed_http_methods_for_whitelisted_func.get(the_function) or []


class TestTheCertificateEndpoints(unittest.TestCase):
    """The endpoints of the certificate of the withholding tax."""

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_the_creation_endpoint_accepts_only_a_post(self):
        self.assertEqual(
            _the_methods_of(payment_entry_server_events.create_wht_certificate_from_payment_entry),
            ["POST"],
        )

    def test_the_manual_creation_endpoint_accepts_only_a_post(self):
        self.assertEqual(
            _the_methods_of(wht_certificate_generator.create_wht_certificate_manually),
            ["POST"],
        )

    def test_the_refresh_of_the_pnd_form_accepts_only_a_post(self):
        self.assertEqual(
            _the_methods_of(wht_certificate_generator.auto_refresh_pnd_form_job),
            ["POST"],
        )

    def test_the_preview_endpoint_stays_a_read(self):
        methods = _the_methods_of(payment_entry_server_events.get_wht_certificate_preview)

        self.assertIn("GET", methods)

    def test_the_creation_endpoint_refuses_a_caller_without_the_right(self):
        frappe.set_user("Guest")

        with self.assertRaises(frappe.PermissionError):
            payment_entry_server_events.create_wht_certificate_from_payment_entry("PE-WITHOUT-RIGHT")

    def test_the_manual_creation_endpoint_refuses_a_caller_without_the_right(self):
        frappe.set_user("Guest")

        with self.assertRaises(frappe.PermissionError):
            wht_certificate_generator.create_wht_certificate_manually("PE-WITHOUT-RIGHT")

    def test_the_preview_endpoint_refuses_a_caller_without_the_right(self):
        frappe.set_user("Guest")

        with self.assertRaises(frappe.PermissionError):
            payment_entry_server_events.get_wht_certificate_preview("PE-WITHOUT-RIGHT")

    def test_the_refresh_of_the_pnd_form_refuses_a_caller_without_the_right(self):
        frappe.set_user("Guest")

        with self.assertRaises(frappe.PermissionError):
            wht_certificate_generator.auto_refresh_pnd_form_job("CERT-WITHOUT-RIGHT", {})

    def test_the_creation_endpoint_needs_the_right_to_create_the_certificate(self):
        with mock.patch.object(
            payment_entry_server_events,
            "require_doctype_permission",
            side_effect=frappe.PermissionError("not permitted"),
        ) as the_check:
            with self.assertRaises(frappe.PermissionError):
                payment_entry_server_events.create_wht_certificate_from_payment_entry(
                    "PE-WITHOUT-THE-RIGHT-TO-CREATE"
                )

        the_check.assert_called_once_with(CERTIFICATE, "create")

    def test_the_manual_creation_endpoint_needs_the_right_to_create_the_certificate(self):
        with mock.patch.object(
            wht_certificate_generator,
            "require_doctype_permission",
            side_effect=frappe.PermissionError("not permitted"),
        ) as the_check:
            with self.assertRaises(frappe.PermissionError):
                wht_certificate_generator.create_wht_certificate_manually(
                    "PE-WITHOUT-THE-RIGHT-TO-CREATE"
                )

        the_check.assert_called_once_with(CERTIFICATE, "create")

    def test_the_creation_endpoint_refuses_before_it_loads_the_payment_entry(self):
        """The refusal of a caller without the right tells nothing about the
        payment entry, so it happens before the payment entry is loaded."""
        frappe.set_user("Guest")

        with self.assertRaises(frappe.PermissionError):
            payment_entry_server_events.create_wht_certificate_from_payment_entry("PE-NOT-ON-THE-SITE")
