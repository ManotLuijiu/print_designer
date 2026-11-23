# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The ownership of the DocTypes of the tax of Thailand is put back safely.

The patches `relocate_thai_tax_doctypes` and `relocate_thai_vat_doctypes`
put the ownership of the DocTypes of the tax back to Print Designer without
knowing who owned them.  A fork of a client carries the same DocTypes and the
records of that client; a DocType that is taken from such an owner changes
the metadata of the records of that client with it.

This patch applies the guard of the ownership to every DocType of the tax of
Thailand, of the VAT and of the withholding tax, so that the sites that
already ran the first patches are guarded as well:

- a DocType of the modules of the Thai Business Suite is taken back to Print
  Designer,
- a DocType of a fork of a client is kept, with the records of that client,
- a DocType of Print Designer stays where it is.

The patch touches the metadata only.  It creates no record, it changes no
record, and it posts no entry to the ledger.
"""

from print_designer.custom.doctype_ownership import take_the_ownership_back

#: The DocTypes of the tax of Thailand, of the VAT and of the withholding tax.
THE_DOCTYPES = (
    # The tax of Thailand
    "Thai Tax Settings",
    "Thai WHT Rate Setting",
    "Thai Tax Invoice Intake",
    # The withholding tax of Thailand
    "Withholding Tax Certificate",
    "Withholding Tax Item",
    "Receive WHT Register",
    # The VAT of Thailand
    "VAT Offset Entry",
    "Thai Sales VAT",
    "VAT Type",
    "Thai VAT Recognition",
    "Thai VAT Recognition Item",
)


def execute() -> None:
    """Put the ownership of the DocTypes of the tax back, when it is safe."""
    for the_doctype in THE_DOCTYPES:
        print(take_the_ownership_back(the_doctype))
