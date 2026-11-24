"""The ownership of the DocTypes of the tax is put back safely.

Several DocTypes of the tax of Thailand live in more than one app: the
canonical DocTypes of Print Designer, the copies of the Thai Business Suite
and the copies of a fork of a client.  The model synchronisation imports the
metadata of every app, and the owner of a DocType is the app whose metadata
was imported last.

A fork of a client carries the records of the withholding tax of that
client.  A DocType that is taken from such an owner changes the metadata of
those records with it, so the ownership of a fork is never taken.

The tests here hold four things:

- the DocType of the modules of the Thai Business Suite is taken back,
- the DocType of a fork of a client is kept, with its records,
- the DocType of Print Designer and the DocType of an unknown owner stay,
- the guard covers every DocType of the tax of Thailand.
"""

import unittest
from unittest.mock import patch

import frappe

from print_designer.custom import doctype_ownership
from print_designer.patches import guard_thai_tax_doctype_ownership as guard_patch
from print_designer.patches import relocate_thai_tax_doctypes as relocate_patch

THE_DOCTYPE = "Withholding Tax Item"
THE_OWNER = "Print Designer"
THE_HISTORICAL = "Thai Tax"
THE_FORK = "A Fork Of A Client"


class TestTaxDocTypeOwnershipGuard(unittest.TestCase):
    """The ownership of the DocTypes of the tax is put back safely."""

    def _the_step(self, the_owner):
        """The step of the guard for a DocType owned by `the_owner`.

        Returns:
            The message of the step and the imports it made.
        """
        the_owners = [the_owner, THE_OWNER]
        the_imports = []

        def the_get_value(doctype, name, fieldname):
            return the_owners.pop(0) if the_owners else THE_OWNER

        def the_import(path, **kwargs):
            the_imports.append((path, kwargs))

        with patch.object(frappe.db, "get_value", side_effect=the_get_value):
            with patch.object(doctype_ownership, "import_file_by_path", side_effect=the_import):
                the_message = doctype_ownership.take_the_ownership_back(THE_DOCTYPE)

        return the_message, the_imports

    # ------------------------------------------------------------------
    # the owners
    # ------------------------------------------------------------------
    def test_the_owner_of_the_thai_business_suite_is_taken_back(self):
        """The DocType of the Thai Business Suite is taken back."""
        the_message, the_imports = self._the_step(THE_HISTORICAL)

        self.assertEqual(len(the_imports), 1)
        the_path, the_arguments = the_imports[0]
        self.assertTrue(the_path.endswith("withholding_tax_item/withholding_tax_item.json"))
        self.assertEqual(the_arguments.get("force"), True)
        self.assertEqual(the_arguments.get("ignore_version"), True)
        self.assertIn(f"owner {THE_HISTORICAL} -> {THE_OWNER}", the_message)

    def test_the_owner_of_a_fork_is_kept(self):
        """The DocType of a fork of a client is kept with its records."""
        the_message, the_imports = self._the_step(THE_FORK)

        self.assertEqual(the_imports, [])
        self.assertIn("is kept", the_message)
        self.assertIn(THE_FORK, the_message)

    def test_the_owner_of_print_designer_stays(self):
        """The DocType of Print Designer stays where it is."""
        the_message, the_imports = self._the_step(THE_OWNER)

        self.assertEqual(the_imports, [])
        self.assertIn(THE_OWNER, the_message)

    def test_an_unknown_owner_is_kept(self):
        """The DocType of an unknown owner is kept."""
        the_message, the_imports = self._the_step("An App of a Client")

        self.assertEqual(the_imports, [])
        self.assertIn("is kept", the_message)
        self.assertIn("An App of a Client", the_message)

    def test_a_doctype_without_metadata_is_created(self):
        """The DocType without metadata is created by Print Designer."""
        the_message, the_imports = self._the_step(None)

        self.assertEqual(len(the_imports), 1)
        self.assertIn(f"owner None -> {THE_OWNER}", the_message)

    # ------------------------------------------------------------------
    # the cover of the guard
    # ------------------------------------------------------------------
    def test_the_guard_covers_every_doctype_of_the_tax(self):
        """The guard covers the tax, the VAT and the withholding tax."""
        for the_doctype in (
            "Thai Tax Settings",
            "Thai WHT Rate Setting",
            "Thai Tax Invoice Intake",
            "Withholding Tax Certificate",
            "Withholding Tax Item",
            "VAT Offset Entry",
            "Thai Sales VAT",
            "VAT Type",
            "Thai VAT Recognition",
            "Thai VAT Recognition Item",
        ):
            self.assertIn(the_doctype, guard_patch.THE_DOCTYPES)

    def test_the_relocation_covers_the_canonical_withholding_tax(self):
        """The relocation covers the canonical certificate, not the deleted one."""
        self.assertIn("Withholding Tax Certificate", relocate_patch.WITHHOLDING_DOCTYPES)
        self.assertIn("Withholding Tax Item", relocate_patch.WITHHOLDING_DOCTYPES)
        self.assertNotIn(
            "Withholding Tax Cert",
            relocate_patch.TAX_DOCTYPES + relocate_patch.WITHHOLDING_DOCTYPES,
        )

    def test_an_owner_that_is_not_relocatable_is_never_taken(self):
        """Only the historical owners of the Thai tax are taken back."""
        self.assertNotIn(THE_FORK, doctype_ownership.RELOCATABLE_OWNERS)
        self.assertIn(THE_HISTORICAL, doctype_ownership.RELOCATABLE_OWNERS)
