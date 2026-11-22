# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The ownership of the Thai VAT DocTypes.

The five Thai VAT DocTypes belong to Print Designer since the relocation:

- VAT Offset Entry
- Thai Sales VAT
- VAT Type
- Thai VAT Recognition
- Thai VAT Recognition Item

Thai Business Suite carries the same DocTypes in its own source folder.  A
migration that imports the DocTypes of every app would let the two apps
fight over the same records, and the owner would be the app that is imported
last.  This patch puts the ownership back after the model synchronisation, so
that the records stay the ones of Print Designer, and so that a migration of
Thai Business Suite cannot take them back.

The patch touches the metadata only.  It creates no record, it changes no
record, and it posts no entry to the ledger.
"""

import os

import frappe
from frappe.modules.import_file import import_file_by_path

APP_PATH = frappe.get_app_path("print_designer")
DOCTYPE_PATH = os.path.join(APP_PATH, "print_designer", "doctype")

# The DocTypes of the VAT of Print Designer, with the folder they live in.
VAT_DOCTYPES = (
    "VAT Offset Entry",
    "Thai Sales VAT",
    "VAT Type",
    "Thai VAT Recognition",
    "Thai VAT Recognition Item",
)

OWNER = "Print Designer"


def execute():
    """Put the ownership of the Thai VAT DocTypes back to Print Designer."""
    for doctype in VAT_DOCTYPES:
        _relocate(doctype)


def _relocate(doctype: str) -> None:
    """Import the metadata of the DocType of Print Designer.

    Args:
            doctype: the name of the DocType.
    """
    before = frappe.db.get_value("DocType", doctype, "module")
    after = before

    if before != OWNER:
        folder = _the_folder_of(doctype)
        path = os.path.join(DOCTYPE_PATH, folder, f"{folder}.json")
        if not os.path.exists(path):
            print(f"  {doctype}: the file of Print Designer is missing, the owner stays {before}")
            return

        import_file_by_path(path, force=True, ignore_version=True)
        after = frappe.db.get_value("DocType", doctype, "module")

    print(f"  {doctype}: owner {before} -> {after}")


def _the_folder_of(doctype: str) -> str:
    """The folder of the DocType inside the app.

    Args:
            doctype: the name of the DocType.

    Returns:
            The name of the folder of the DocType.
    """
    return frappe.scrub(doctype)
