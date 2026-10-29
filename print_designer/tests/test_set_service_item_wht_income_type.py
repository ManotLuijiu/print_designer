"""Unit tests for the "set the WHT income type of the service items" command.

The command fills the master data gap of the ``Services`` Item Group: an item
without ``pd_custom_wht_income_type`` produces a document whose withholding
tax flag is on but whose income type, rate and amount stay empty.

Run standalone (no site required):

    cd /home/frappe/frappe-bench
    env/bin/python -m unittest apps.print_designer.print_designer.tests.test_set_service_item_wht_income_type
"""

import unittest

from print_designer.commands.set_service_item_wht_income_type import (
    build_plan,
    resolve_income_type,
)
from print_designer.custom.item_wht_config import ITEM_INCOME_TYPE_FIELD
from print_designer.custom.service_item_wht import SERVICE_ITEM_GROUP


class TestBuildPlan(unittest.TestCase):
    """The plan must only contain the items that have no income type."""

    def test_items_without_an_income_type_are_planned(self):
        items = [
            {"item_code": "A", ITEM_INCOME_TYPE_FIELD: ""},
            {"item_code": "B", ITEM_INCOME_TYPE_FIELD: None},
        ]

        plan = build_plan(items)

        self.assertEqual([item["item_code"] for item in plan], ["A", "B"])

    def test_an_existing_income_type_is_never_planned(self):
        items = [
            {"item_code": "A", ITEM_INCOME_TYPE_FIELD: "Service Fees 3% (PND53)"},
            {"item_code": "B", ITEM_INCOME_TYPE_FIELD: ""},
        ]

        plan = build_plan(items)

        self.assertEqual([item["item_code"] for item in plan], ["B"])

    def test_a_blank_value_counts_as_missing(self):
        items = [{"item_code": "A", ITEM_INCOME_TYPE_FIELD: "   "}]

        self.assertEqual(len(build_plan(items)), 1)

    def test_items_without_the_field_are_planned(self):
        """An item that does not carry the field at all is missing the value."""

        items = [{"item_code": "A"}]

        self.assertEqual(len(build_plan(items)), 1)


class TestResolveIncomeType(unittest.TestCase):
    """The category is either requested explicitly or derived from the group."""

    def test_an_explicit_category_wins(self):
        items = [{"item_code": "A", ITEM_INCOME_TYPE_FIELD: "Service Fees 3% (PND53)"}]

        resolved = resolve_income_type(items, requested="Services 3% (PND3)")

        self.assertEqual(resolved, "Services 3% (PND3)")

    def test_the_category_is_derived_from_the_group(self):
        items = [
            {"item_code": "A", ITEM_INCOME_TYPE_FIELD: "Service Fees 3% (PND53)"},
            {"item_code": "B", ITEM_INCOME_TYPE_FIELD: ""},
        ]

        resolved = resolve_income_type(items)

        self.assertEqual(resolved, "Service Fees 3% (PND53)")

    def test_conflicting_categories_require_an_explicit_choice(self):
        items = [
            {"item_code": "A", ITEM_INCOME_TYPE_FIELD: "Service Fees 3% (PND53)"},
            {"item_code": "B", ITEM_INCOME_TYPE_FIELD: "Services 3% (PND3)"},
        ]

        with self.assertRaises(ValueError) as context:
            resolve_income_type(items)

        self.assertIn("Service Fees 3% (PND53)", str(context.exception))

    def test_a_group_without_any_category_requires_an_explicit_choice(self):
        items = [{"item_code": "A", ITEM_INCOME_TYPE_FIELD: ""}]

        with self.assertRaises(ValueError):
            resolve_income_type(items)


class TestCommandRegistration(unittest.TestCase):
    """The command must be reachable through the Frappe v16 command list."""

    def test_the_command_is_exported(self):
        from print_designer.commands import commands

        names = [command.name for command in commands]

        self.assertIn("set-service-item-wht-income-type", names)

    def test_the_command_uses_the_service_item_group_of_the_rule(self):
        """The command and the withholding rule must agree on the group."""

        from print_designer.commands.set_service_item_wht_income_type import (
            set_service_item_wht_income_type_cmd,
        )

        defaults = {
            option.name: option.default for option in set_service_item_wht_income_type_cmd.params
        }

        self.assertEqual(defaults["item_group"], SERVICE_ITEM_GROUP)


if __name__ == "__main__":
    unittest.main()
