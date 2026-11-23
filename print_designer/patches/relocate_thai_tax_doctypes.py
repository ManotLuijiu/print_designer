# Copyright (c) 2026, MooCoding and contributors
# For license information, please see license.txt

"""The ownership of the Thai tax DocTypes.

The Thai Tax Settings belong to Print Designer since the relocation of the
Thai tax DocTypes.

Thai Business Suite carries the same DocType in its own source folder.  A
migration that imports the DocTypes of every app would let the two apps
fight over the same records, and the owner would be the app that is imported
last.  This patch puts the ownership back after the model synchronisation, so
that the records stay the ones of Print Designer, and so that a migration of
Thai Business Suite cannot take them back.

The ownership is only taken back from an owner that carries the DocType
without records of its own, the modules of the Thai Business Suite.  A fork
of a client carries the records of that client, and its DocType is kept; see
`print_designer/custom/doctype_ownership.py`.

The patch touches the metadata only.  It creates no record, it changes no
record, and it posts no entry to the ledger.
"""

from print_designer.custom.doctype_ownership import take_the_ownership_back

# The DocTypes of the tax of Print Designer, with the folder they live in.
TAX_DOCTYPES = (
    "Thai Tax Settings",
    "Thai WHT Rate Setting",
    "Thai Tax Invoice Intake",
)

# The DocTypes of the withholding tax of Print Designer.  The certificate of
# the withholding tax of Thailand and its incomes are the canonical DocTypes;
# the certificate that was deleted, `Withholding Tax Cert`, is not one of them.
WITHHOLDING_DOCTYPES = (
    "Withholding Tax Certificate",
    "Withholding Tax Item",
)


def execute() -> None:
    """Put the ownership of the Thai tax DocTypes back to Print Designer."""
    for doctype in TAX_DOCTYPES + WITHHOLDING_DOCTYPES:
        print(take_the_ownership_back(doctype))
