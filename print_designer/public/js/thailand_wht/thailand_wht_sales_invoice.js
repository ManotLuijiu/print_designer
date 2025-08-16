// Thailand Withholding Tax Client Script for Sales Invoice
// DISABLED: Causing excessive API calls to thailand_service_business field
// All functionality commented out to prevent API spam and save/submit button issues

/*
Original functionality disabled to prevent excessive API calls to:
- frappe.db.get_value('Company', company, 'thailand_service_business')

This was causing performance issues and interfering with form operations.
The Thailand WHT integration needs to be properly configured before re-enabling.
*/