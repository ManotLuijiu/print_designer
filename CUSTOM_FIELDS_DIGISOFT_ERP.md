# Analysis Complete: Sales Invoice Fields Comparison

  🔍 Key Finding: Why digisoft_erp fields are in print_designer fixtures

  ROOT CAUSE: The export-fixtures command exports ALL custom fields from the database, regardless of
  which app created them. When you run bench --site erpnext-dev-server.bunchee.online export-fixtures 
  --app print_designer, it exports:
  - Fields created by print_designer app ✅
  - Fields created by digisoft_erp app ❌ (shouldn't be here)
  - Fields created manually in GUI ✅/❌ (depends on purpose)

  📋 Current Situation:

  Install File (install_sales_invoice_fields.py): 32 fields
  Fixtures: 34 fields

  ❌ Problematic Fields in Fixtures (belong to digisoft_erp):

  These 11 fields should NOT be in print_designer:
  1. digisoft_erp_tab - Digisoft ERP Tab
  2. thai_tax_information_section - Thai Tax Information Section
  3. thai_invoice_type - Invoice Type
  4. thai_tax_invoice_number - Thai Tax Invoice Number
  5. thai_tax_invoice_date - Tax Invoice Date
  6. thai_customer_tax_id - Customer Tax ID
  7. thai_customer_branch_code - Customer Branch Code
  8. thai_compliance_section - Tax Compliance Section
  9. thai_vat_eligible - VAT Eligible
  10. thai_export_eligible - Export Eligible
  11. thai_cash_receipt - Cash Receipt

  ✅ Fields that belong in print_designer (23 fields):

  - WHT-related fields (preview, calculations)
  - Retention fields
  - Signature fields
  - Watermark field
  - VAT treatment

  💡 Solution:

  1. Remove digisoft_erp fields from print_designer install file
  2. Keep only print_designer specific fields (23 fields)
  3. Move digisoft_erp fields to their proper app: apps/digisoft_erp/digisoft_erp/fixtures/

  🎯 Recommendations:

  1. Immediate Fix: Remove the 11 digisoft_erp fields from the install file
  2. Long-term Fix: Configure hooks.py fixtures filter to exclude specific field names that belong to
  other apps
  3. Best Practice: Each app should only manage its own custom fields

  Would you like me to:
  1. Remove the digisoft_erp fields from the install file?
  2. Show the exact differences between install file and fixtures after cleanup?