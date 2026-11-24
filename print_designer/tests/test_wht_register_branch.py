"""The branch of the customer in the withholding tax register.

The patch of the register reads its rows with ``frappe.get_all()``, which
returns rows that are dictionaries and not documents. The branch of the
customer is written into such a row, so the helper has to work with a
dictionary as well as with a document.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.print_designer.doctype.receive_wht_register.receive_wht_register import (
    fill_customer_branch,
)

THE_CUSTOMER = "_Test Customer"


class TestTheBranchOfTheRegister(FrappeTestCase):
    """The branch of the customer of the register."""

    def _the_row(self) -> frappe._dict:
        """A row of the patch, the way frappe.get_all() returns it."""
        return frappe._dict(
            {
                "name": "RWD-TEST-0001",
                "customer": THE_CUSTOMER,
                "customer_branch_code": None,
                "customer_branch_name": None,
            }
        )

    def test_a_row_of_the_patch_carries_the_branch_of_the_customer(self):
        """A row of the patch is a dictionary, and the helper writes into it."""
        the_row = self._the_row()

        fill_customer_branch(the_row)

        self.assertEqual(the_row.get("customer_branch_code"), "00000")
        self.assertEqual(the_row.get("customer_branch_name"), "สำนักงานใหญ่")

    def test_a_document_carries_the_branch_of_the_customer(self):
        """A document of the register carries the branch of the customer as well."""
        the_register = frappe.get_doc(
            {
                "doctype": "Receive WHT Register",
                "customer": THE_CUSTOMER,
            }
        )

        fill_customer_branch(the_register)

        self.assertEqual(the_register.get("customer_branch_code"), "00000")
        self.assertEqual(the_register.get("customer_branch_name"), "สำนักงานใหญ่")
