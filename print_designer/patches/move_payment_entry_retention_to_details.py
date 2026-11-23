from print_designer.patches.retire_payment_entry_tax_details import retire_fields

REPLACEMENTS = {
    "pd_custom_retention_pct": "pd_custom_retention_pct_details",
    "pd_custom_retention_amount": "pd_custom_retention_amount_details",
}


def execute():
    return retire_fields(REPLACEMENTS, layout_fields=("pd_custom_amounts_section_details",))
