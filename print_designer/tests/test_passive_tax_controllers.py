"""The tests of the four passive controllers of the relocated tax.

`Thai Sales VAT`, `VAT Type`, `Thai VAT Recognition Item` and `Thai WHT Rate
Setting` carry no behaviour of their own: they are documents whose fields are
filled by the modules that use them.  The port of them is therefore the
ownership of the DocType and the delegation of the old path of Thai Business
Suite to Print Designer.

The tests check that the DocType belongs to Print Designer, that the old path
holds the same class as Print Designer, and that the controller really carries
no behaviour of its own.
"""

import unittest
from typing import Any, cast

import frappe

from print_designer.print_designer.doctype.thai_sales_vat.thai_sales_vat import ThaiSalesVAT
from print_designer.print_designer.doctype.thai_vat_recognition_item.thai_vat_recognition_item import (  # noqa: E501
    ThaiVATRecognitionItem,
)
from print_designer.print_designer.doctype.thai_wht_rate_setting.thai_wht_rate_setting import (
    ThaiWHTRateSetting,
)
from print_designer.print_designer.doctype.vat_type.vat_type import VATType

# The four DocTypes and the controller of Print Designer.
THE_FOUR = (
    ("Thai Sales VAT", ThaiSalesVAT),
    ("VAT Type", VATType),
    ("Thai VAT Recognition Item", ThaiVATRecognitionItem),
    ("Thai WHT Rate Setting", ThaiWHTRateSetting),
)

# The old path of Thai Business Suite for every one of them.
THE_OLD_PATHS = (
    ("Thai Sales VAT", "thai_business_suite.thai_tax.doctype.thai_sales_vat.thai_sales_vat"),
    ("VAT Type", "thai_business_suite.thai_business_suite.doctype.vat_type.vat_type"),
    (
        "Thai VAT Recognition Item",
        "thai_business_suite.thai_business_suite.doctype.thai_vat_recognition_item.thai_vat_recognition_item",
    ),
    (
        "Thai WHT Rate Setting",
        "thai_business_suite.thai_tax.doctype.thai_wht_rate_setting.thai_wht_rate_setting",
    ),
)


class TestThePassiveControllers(unittest.TestCase):
    """The four passive controllers of the relocated tax."""

    def test_every_doctype_belongs_to_print_designer(self):
        """Every one of the four DocTypes belongs to Print Designer."""
        for doctype, _ in THE_FOUR:
            self.assertEqual(
                frappe.db.get_value("DocType", doctype, "module"),
                "Print Designer",
                f"{doctype} does not belong to Print Designer",
            )

    def test_the_old_path_holds_the_class_of_print_designer(self):
        """The old path of Thai Business Suite holds the class of Print Designer."""
        for doctype, controller in THE_FOUR:
            old_path = dict(THE_OLD_PATHS)[doctype]
            module = cast(Any, __import__(old_path, fromlist=["*"]))
            self.assertIs(
                cast(Any, getattr(module, controller.__name__)),
                controller,
                f"the old path of {doctype} is not the class of Print Designer",
            )

    def test_the_controllers_carry_no_behaviour_of_their_own(self):
        """The controllers define no method of their own."""
        for doctype, controller in THE_FOUR:
            own = [
                name
                for name in vars(controller)
                if not name.startswith("__") and callable(getattr(controller, name, None))
            ]
            self.assertEqual(own, [], f"{doctype} defines a behaviour of its own")

    def test_the_doctypes_keep_their_fields(self):
        """The four DocTypes keep the fields they had."""
        for doctype, _ in THE_FOUR:
            fields = frappe.get_meta(doctype).fields
            self.assertTrue(fields, f"{doctype} has no field")
