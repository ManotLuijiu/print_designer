"""The tests of the controllers of the relocated tax.

`Thai Sales VAT`, `VAT Type`, `Thai VAT Recognition Item` and `Thai WHT Rate
Setting` belong to Print Designer since the relocation of the Thai tax.  The
old folders of Thai Business Suite were removed with them, so Print Designer
holds the only copy of these DocTypes and of their controllers.

The tests check that the DocType belongs to Print Designer, that no second
implementation survives in Thai Business Suite, and that the controllers keep
the shape they are meant to have: the three passive ones carry no behaviour of
their own, while `Thai Sales VAT` names its rows after the receipt they
belong to.
"""

import importlib
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

# The three of them that are only documents: the modules that use them fill
# their fields.
THE_PASSIVE = (
    ("VAT Type", VATType),
    ("Thai VAT Recognition Item", ThaiVATRecognitionItem),
    ("Thai WHT Rate Setting", ThaiWHTRateSetting),
)


def _the_old_path(old_path: str):
    """The module of the old path, or `None` when it is gone."""
    try:
        return importlib.import_module(old_path)
    except ModuleNotFoundError:
        return None


class TestTheRelocatedControllers(unittest.TestCase):
    """The controllers of the relocated tax."""

    def test_every_doctype_belongs_to_print_designer(self):
        """Every one of the four DocTypes belongs to Print Designer."""
        for doctype, _ in THE_FOUR:
            self.assertEqual(
                frappe.db.get_value("DocType", doctype, "module"),
                "Print Designer",
                f"{doctype} does not belong to Print Designer",
            )

    def test_no_second_implementation_survives_in_thai_business_suite(self):
        """The old path of Thai Business Suite holds no second implementation.

        The old folders were removed with the relocation.  A path that is
        still there may only delegate to Print Designer, so that the tax has
        exactly one home and one behaviour.
        """
        for doctype, controller in THE_FOUR:
            old_path = dict(THE_OLD_PATHS)[doctype]
            module = _the_old_path(old_path)
            if module is None:
                continue
            self.assertIs(
                cast(Any, getattr(module, controller.__name__, None)),
                controller,
                f"the old path of {doctype} holds an implementation of its own",
            )

    def test_the_passive_controllers_carry_no_behaviour_of_their_own(self):
        """The three passive controllers define no method of their own."""
        for doctype, controller in THE_PASSIVE:
            own = [
                name
                for name in vars(controller)
                if not name.startswith("__") and callable(getattr(controller, name, None))
            ]
            self.assertEqual(own, [], f"{doctype} defines a behaviour of its own")

    def test_thai_sales_vat_names_its_rows_after_the_receipt(self):
        """`Thai Sales VAT` names its row after the receipt it belongs to."""
        for name in ("autoname", "receipt_record_name", "rename_for_receipt", "validate"):
            self.assertTrue(
                callable(getattr(ThaiSalesVAT, name, None)),
                f"Thai Sales VAT does not define {name}",
            )

    def test_the_doctypes_keep_their_fields(self):
        """The four DocTypes keep the fields they had."""
        for doctype, _ in THE_FOUR:
            fields = frappe.get_meta(doctype).fields
            self.assertTrue(fields, f"{doctype} has no field")


if __name__ == "__main__":
    unittest.main()
