from print_designer.patches.retire_payment_entry_tax_details import retire_fields

REPLACEMENTS = {
    "pd_custom_apply_withholding_tax": "pd_custom_subject_to_wht",
    "pd_custom_withholding_tax_rate": "pd_custom_withholding_tax_pct_details",
    "pd_custom_withholding_tax_amount": "pd_custom_withholding_tax_amount_details",
    "pd_custom_net_payment_amount": "pd_custom_net_after_wht_retention",
}


def execute():
    return retire_fields(REPLACEMENTS, layout_fields=("pd_custom_amounts_section_details",))
