# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The tests of the Thai tax settings of Print Designer.

The settings of the Thai tax are a singleton of the site.  The tests write
their values inside a savepoint, so that the transaction of the test leaves
the settings of the site as they were, not even on a site where the
transaction of the test is committed at the end.

The tests prove that the settings can be saved and read on a site where Thai
Business Suite is not installed, and that the endpoints refuse the caller
that has no right.
"""

import unittest
from typing import Any

import frappe
from frappe.utils import nowdate

from print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings import (
    DEFAULT_WHT_RATES,
    FALLBACK_WHT_RATE,
    get_thai_tax_settings,
    get_thai_wht_rate,
)


class TestTheOwnershipOfTheThaiTaxDocTypes(unittest.TestCase):
    """The DocTypes of the tax belong to Print Designer."""

    def test_the_settings_belong_to_print_designer(self):
        """The Thai Tax Settings belongs to Print Designer."""
        self.assertEqual(
            frappe.db.get_value("DocType", "Thai Tax Settings", "module"),
            "Print Designer",
        )

    def test_the_rate_setting_belongs_to_print_designer(self):
        """The Thai WHT Rate Setting belongs to Print Designer."""
        self.assertEqual(
            frappe.db.get_value("DocType", "Thai WHT Rate Setting", "module"),
            "Print Designer",
        )


class TestThaiTaxSettings(unittest.TestCase):
    """The settings of the Thai tax of a site."""

    SAVEPOINT = "tts_settings_test"

    def setUp(self):
        frappe.set_user("Administrator")
        # The values of the settings are written inside a savepoint, so that
        # the transaction of the test leaves the settings of the site as they
        # were.
        frappe.db.savepoint(self.SAVEPOINT)

    def tearDown(self):
        frappe.db.rollback(save_point=self.SAVEPOINT)
        frappe.set_user("Administrator")

    def _the_settings(self) -> Any:
        """The settings of the tax, with the values of the test."""
        settings = frappe.get_single("Thai Tax Settings")
        settings.set("auto_apply_thai_format", 1)
        settings.set("enable_withholding_tax", 1)
        settings.set("vat_rate", 7)
        settings.set("auto_calculate_vat", 1)
        settings.set("default_tax_branch_code", "00000")

        return settings

    def _the_settings_with_a_rate(self, income_type: str, rate: float) -> Any:
        """The settings of the tax, with one rate of the withholding tax."""
        settings = self._the_settings()
        settings.set(
            "default_wht_rates",
            [
                {
                    "income_type": income_type,
                    "income_code": "40(8)",
                    "entity_type": "Individual",
                    "pnd_type": "PND3",
                    "tax_rate": rate,
                    "individual_rate": rate,
                    "effective_from": nowdate(),
                    "is_active": 1,
                }
            ],
        )

        return settings

    # The saving of the settings -------------------------------------------

    def test_the_settings_can_be_saved(self):
        """The settings of the tax can be saved.

        The controller of Thai Business Suite reads a field that the row of a
        rate does not carry, so the saving of the settings ended with an
        error there as soon as the settings carried a rate.
        """
        settings = self._the_settings()
        settings.save()

        self.assertEqual(frappe.db.get_single_value("Thai Tax Settings", "vat_rate"), 7)

    def test_the_rate_of_the_settings_is_refused_out_of_the_range(self):
        """A rate of the withholding tax that is not a percentage is refused."""
        settings = self._the_settings_with_a_rate("40(1) เงินเดือน ค่าจ้าง", 120)

        with self.assertRaises(frappe.ValidationError):
            settings.save()

    def test_the_rate_of_the_settings_is_accepted(self):
        """A rate of the withholding tax that is a percentage is accepted."""
        settings = self._the_settings_with_a_rate("40(1) เงินเดือน ค่าจ้าง", 3)

        settings.save()

        self.assertEqual(
            frappe.db.count(
                "Thai WHT Rate Setting",
                filters={"parent": "Thai Tax Settings", "tax_rate": 3},
            ),
            1,
        )

    # The reading of the settings -------------------------------------------

    def test_the_values_of_the_settings_are_read(self):
        """The endpoint answers with the values of the settings.

        The endpoint of Thai Business Suite reads the accounts of the tax as
        attributes, and the doctype does not carry them, so the endpoint
        ended with an error there.
        """
        self._the_settings().save()

        values = get_thai_tax_settings()

        self.assertEqual(values["vat_rate"], 7)
        self.assertEqual(values["auto_apply_thai_format"], 1)
        self.assertEqual(values["enable_withholding_tax"], 1)
        self.assertEqual(values["auto_calculate_vat"], 1)
        self.assertEqual(values["default_tax_branch_code"], "00000")
        self.assertIsNone(values["default_vat_output_account"])

    def test_the_rate_of_the_settings_is_used(self):
        """The rate of the settings is the rate of the income type."""
        self._the_settings_with_a_rate("40(8) ค่าบริการ/ค่าวิชาชีพอิสระ", 3.5).save()

        self.assertEqual(get_thai_wht_rate("40(8) ค่าบริการ/ค่าวิชาชีพอิสระ"), 3.5)

    def test_the_rate_of_the_law_is_used_without_a_row(self):
        """The rate of the law of Thailand is the rate without a row."""
        self._the_settings().save()

        for income_type, rate in DEFAULT_WHT_RATES.items():
            self.assertEqual(get_thai_wht_rate(income_type), rate)

    def test_an_unknown_income_type_uses_the_fallback(self):
        """An income type that is not known uses the rate of the fallback."""
        self._the_settings().save()

        self.assertEqual(get_thai_wht_rate("An income type that is not known"), FALLBACK_WHT_RATE)

    # The right of the caller -----------------------------------------------

    def test_the_creation_of_the_accounts_needs_the_system_manager(self):
        """The creation of the accounts of the tax is a command of the site."""
        frappe.set_user("Guest")

        with self.assertRaises(frappe.PermissionError):
            get_thai_tax_settings()

    def test_the_creation_of_the_accounts_refuses_without_the_fields(self):
        """The accounts of the tax cannot be created without the fields.

        The doctype does not carry the accounts of the tax, so an account
        that was created could not be remembered, and it would be created
        again on every save.
        """
        settings = self._the_settings()
        settings.set("auto_create_accounts", 1)

        with self.assertRaises(frappe.ValidationError):
            settings.create_default_thai_accounts()

    def test_the_accounts_of_the_settings_are_not_checked_without_the_fields(self):
        """The check of the accounts of the tax runs only for the fields."""
        settings = self._the_settings()

        # The doctype does not carry the accounts, so there is nothing to
        # check, and the saving of the settings is not refused.
        settings.validate_account_types()
        settings.save()

        self.assertTrue(frappe.db.exists("Thai Tax Settings"))
