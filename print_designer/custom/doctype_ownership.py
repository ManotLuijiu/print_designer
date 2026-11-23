# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The ownership of the DocTypes that more than one app carries.

Several DocTypes of the tax of Thailand live in more than one app: the
canonical DocTypes of Print Designer, the copies of the Thai Business Suite
and the copies of a fork of a client.  The model synchronisation imports the
metadata of every app, and the owner of a DocType is the app whose metadata
was imported last.

A migration that puts the ownership back must therefore know who owns the
DocType:

- the owner that carries the DocType only, the modules of the Thai Business
  Suite, may be taken back to Print Designer,
- the owner of a fork of a client is never taken.  A fork carries the records
  of the withholding tax of that client; a DocType that is taken from such an
  owner changes the metadata of those records with it.

The module reads the metadata of a DocType and nothing else.  It creates no
record, it changes no record, and it posts no entry to the ledger.
"""

import os

import frappe
from frappe.modules.import_file import import_file_by_path

APP_PATH = frappe.get_app_path("print_designer")
DOCTYPE_PATH = os.path.join(APP_PATH, "print_designer", "doctype")

#: The owner of the canonical DocTypes of Print Designer.
OWNER = "Print Designer"

#: The owners whose DocType may be taken back to Print Designer.  They are the
#: modules of the Thai Business Suite that carried the DocTypes of the tax of
#: Thailand before the relocation.
RELOCATABLE_OWNERS = ("Thai Tax", "Thai Business Suite")

#: The owners whose DocType is never taken.  A fork of a client carries the
#: records of that client.
PROTECTED_OWNERS = ("Digisoft Erp",)


def the_owner_of(doctype: str) -> str | None:
    """The module that owns the DocType.

    Args:
            doctype: the name of the DocType.

    Returns:
            The name of the module that owns the DocType, or None when the
            DocType has no metadata yet.
    """
    the_owner = frappe.db.get_value("DocType", doctype, "module")
    return the_owner if isinstance(the_owner, str) else None


def the_path_of(doctype: str) -> str:
    """The path of the file of the DocType of Print Designer.

    Args:
            doctype: the name of the DocType.

    Returns:
            The path of the file of the DocType inside the app.
    """
    folder = frappe.scrub(doctype)
    return os.path.join(DOCTYPE_PATH, folder, f"{folder}.json")


def take_the_ownership_back(doctype: str) -> str:
    """Put the ownership of the DocType back to Print Designer when it is safe.

    The ownership of a DocType of a fork of a client is kept, with the
    records of that client.

    Args:
            doctype: the name of the DocType.

    Returns:
            The message of the step, for the log of the migration.
    """
    before = the_owner_of(doctype)

    if before == OWNER:
        return f"  {doctype}: owner {before}"

    if before in PROTECTED_OWNERS:
        return f"  {doctype}: owner {before} is kept, the records of that app are never taken"

    if before and before not in RELOCATABLE_OWNERS:
        return f"  {doctype}: owner {before} is not an owner of the Thai tax, the owner stays"

    path = the_path_of(doctype)
    if not os.path.exists(path):
        return f"  {doctype}: the file of Print Designer is missing, the owner stays {before}"

    import_file_by_path(path, force=True, ignore_version=True)
    after = the_owner_of(doctype)

    return f"  {doctype}: owner {before} -> {after}"
