"""The submitted Output VAT Report action of the Sales Invoice (SI-03, Task B).

The action of a submitted invoice sits in the "View" group of the form.
Print Designer registers it and the registration of Thai Business Suite in the
"Tools" group is retired, so the action is never shown twice.  The report
and its undue companion are owned by Print Designer. Availability is checked
against the report and ledger permissions.
"""

from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer import boot as pd_boot

OUTPUT_VAT_REPORT = "Output VAT Report"
CLIENT_SCRIPT = "public/js/sales_invoice/output_vat_report.js"


def sales_invoice_client_code() -> str:
    """The client code of the Sales Invoice form, as the desk assembles it.

    The hooks of every app are read fresh, so the result does not depend on
    the cache of the site.
    """
    from frappe.desk.form.meta import get_code_files_via_hooks

    code = []
    for path in get_code_files_via_hooks("doctype_js", "Sales Invoice"):
        code.append(frappe.read_file(path) or "")

    return "\n".join(code)


def custom_button_calls(code: str, label: str) -> list:
    """The arguments of every add_custom_button call that carries the label."""
    calls = []
    needle = "add_custom_button"
    index = code.find(needle)

    while index != -1:
        start = code.find("(", index)
        if start == -1:
            break

        depth = 0
        end = None
        for position in range(start, len(code)):
            if code[position] == "(":
                depth += 1
            elif code[position] == ")":
                depth -= 1
                if depth == 0:
                    end = position
                    break

        if end is None:
            break

        arguments = code[start + 1 : end]
        if label in arguments:
            calls.append(arguments)

        index = code.find(needle, end)

    return calls


def has_group(arguments: str, group: str) -> bool:
    return f'"{group}"' in arguments or f"'{group}'" in arguments


class TestOutputVatReportAction(FrappeTestCase):
    """The action of the submitted Sales Invoice."""

    def test_the_boot_names_the_report_of_the_output_vat(self):
        info = pd_boot.output_vat_report_info()

        self.assertEqual(info["report"], OUTPUT_VAT_REPORT)
        self.assertIsInstance(info["available"], bool)

    def test_the_button_is_absent_without_the_report(self):
        with patch("frappe.db.exists", return_value=None):
            info = pd_boot.output_vat_report_info()

        self.assertFalse(info["available"])

    def test_the_button_is_absent_without_the_report_permission(self):
        with patch("frappe.db.exists", return_value=OUTPUT_VAT_REPORT):
            with patch("frappe.has_permission", return_value=False):
                info = pd_boot.output_vat_report_info()

        self.assertFalse(info["available"])

    def test_an_empty_query_report_does_not_enable_the_action(self):
        report = Mock(module="Print Designer", disabled=0, report_type="Query Report")
        with (
            patch("frappe.has_permission", return_value=True),
            patch("frappe.db.exists", return_value=OUTPUT_VAT_REPORT),
            patch("frappe.get_cached_doc", return_value=report),
        ):
            self.assertFalse(pd_boot.output_vat_report_info()["available"])

    def test_the_undue_action_is_registered_in_view(self):
        calls = custom_button_calls(sales_invoice_client_code(), "Output VAT Undue Report")
        self.assertTrue(any(has_group(arguments, "View") for arguments in calls))

    def test_the_script_is_registered_for_the_sales_invoice(self):
        hooks = frappe.get_hooks("doctype_js", default={}, app_name="print_designer")

        self.assertIn(CLIENT_SCRIPT, hooks["Sales Invoice"])

    def test_the_action_is_registered_in_the_view_group(self):
        calls = custom_button_calls(sales_invoice_client_code(), "Output VAT Report")

        self.assertTrue(calls, "the action of the output VAT is not registered")
        self.assertTrue(any(has_group(arguments, "View") for arguments in calls))

    def test_the_action_is_not_registered_in_the_tools_group(self):
        calls = custom_button_calls(sales_invoice_client_code(), "Output VAT Report")

        self.assertTrue(calls)
        for arguments in calls:
            self.assertFalse(has_group(arguments, "Tools"))

    def test_the_other_tools_action_of_the_invoice_stays(self):
        calls = custom_button_calls(sales_invoice_client_code(), "Analyze in Grist")

        self.assertTrue(calls, "the Grist action of the invoice is gone")
        self.assertTrue(any(has_group(arguments, "Tools") for arguments in calls))
