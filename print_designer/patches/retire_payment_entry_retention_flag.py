from print_designer.patches.retire_payment_entry_tax_details import retire_fields

REPLACEMENTS = {
    "pd_custom_subject_to_retention_details": "pd_custom_subject_to_retention",
}


def execute():
    return retire_fields(REPLACEMENTS)
