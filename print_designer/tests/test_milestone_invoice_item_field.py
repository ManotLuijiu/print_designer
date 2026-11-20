"""Tests for the percent column of the milestone Sales Invoice Item.

The column belongs to the lifecycle of the app: it is installed on a fresh
site, it is installed again on every migrate and it is removed again when
the app is uninstalled.
"""

import inspect
import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer import hooks, install, uninstall
from print_designer.commands import install_milestone_invoice_item_fields as milestone

FIELD = "pd_custom_invoice_portion"
DOCTYPE = "Sales Invoice Item"


class TestTheColumnDefinition(unittest.TestCase):
    """The shape of the column."""

    def test_the_column_is_a_read_only_percent_after_the_rate(self):
        field = milestone.get_milestone_invoice_item_fields()[DOCTYPE][0]

        self.assertEqual(field["fieldname"], FIELD)
        self.assertEqual(field["fieldtype"], "Percent")
        self.assertEqual(field["label"], "%")
        self.assertEqual(field["insert_after"], "rate")
        self.assertEqual(field["in_list_view"], 1)
        self.assertEqual(field["columns"], 1)
        self.assertEqual(field["read_only"], 1)

    def test_the_column_is_not_the_discount_of_the_line(self):
        field = milestone.get_milestone_invoice_item_fields()[DOCTYPE][0]

        self.assertNotEqual(field["fieldname"], "discount_percentage")


class TestTheLifecycle(unittest.TestCase):
    """The three points of the lifecycle of the app."""

    def test_the_after_install_hook_installs_the_column(self):
        source = inspect.getsource(install.after_install)

        self.assertIn("install_milestone_invoice_item_fields()", source)

    def test_the_after_migrate_hook_installs_the_column(self):
        self.assertIn(
            "print_designer.commands.install_milestone_invoice_item_fields."
            "install_milestone_invoice_item_fields",
            hooks.after_migrate,
        )

    def test_the_before_uninstall_hook_removes_the_column(self):
        source = inspect.getsource(uninstall.before_uninstall)

        self.assertIn("uninstall_milestone_invoice_item_fields()", source)

    def test_the_column_goes_before_the_bulk_cleanup(self):
        source = inspect.getsource(uninstall.before_uninstall)

        self.assertLess(
            source.index("uninstall_milestone_invoice_item_fields()"),
            source.index("delete_all_print_designer_custom_fields()"),
        )


class TestTheColumnOnTheSite(FrappeTestCase):
    """The column on a site that has the app installed."""

    def setUp(self):
        if not frappe.db.exists("Custom Field", {"dt": DOCTYPE, "fieldname": FIELD}):
            self.skipTest("the percent column is not installed on this site")

    def test_the_column_sits_right_after_the_rate(self):
        result = milestone.install_milestone_invoice_item_fields()

        self.assertTrue(result["success"], result)
        self.assertEqual(result["position"], 1)

    def test_the_installer_keeps_the_existing_column(self):
        name = str(frappe.db.get_value("Custom Field", {"dt": DOCTYPE, "fieldname": FIELD}, "name"))
        created = frappe.db.get_value("Custom Field", name, "creation")

        milestone.install_milestone_invoice_item_fields()

        self.assertEqual(frappe.db.get_value("Custom Field", name, "creation"), created)

    def test_the_installer_puts_the_column_back_after_the_rate(self):
        name = str(frappe.db.get_value("Custom Field", {"dt": DOCTYPE, "fieldname": FIELD}, "name"))
        frappe.db.set_value("Custom Field", name, "insert_after", "batch_no")

        milestone.install_milestone_invoice_item_fields()

        self.assertEqual(
            frappe.db.get_value("Custom Field", name, "insert_after"),
            "rate",
        )
        self.assertEqual(milestone.get_position(), 1)
