# Copyright (c) 2026, Print Designer
# For license information, please see license.txt

"""
Thai WHT Tax Calculation for Sales Invoice

The actual calculation is done in JavaScript (thailand_wht_sales_invoice.js):
- pd_custom_withholding_tax_amount = net_total * wht_pct / 100
- pd_custom_net_total_after_wht = grand_total - withholding_tax_amount

This module is kept for reference but the calculation is handled client-side.
"""

# Note: The calculation logic has been moved to JS for better control
# See: thailand_wht_sales_invoice.js -> pd_calculate_wht_amounts()
