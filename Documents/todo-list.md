# Refactor print_designer Custom Fields — Todo List

Full plan: `/home/frappe/.claude/plans/breezy-roaming-narwhal.md`
Bulk rename script: `commands/rename_fields_bulk.py` (88 files, 451 replacements)

## Phase A: Install Script Field Definitions (SI + SO)
- [x] `commands/install_sales_invoice_fields.py` — renamed all to `pd_custom_*`
- [x] `commands/install_sales_order_fields.py` — renamed all to `pd_custom_*`

## Phase B: Other Install Scripts — DONE (bulk rename)
- [x] `commands/install_quotation_fields.py`
- [x] `commands/install_purchase_invoice_fields.py`
- [x] `commands/install_purchase_order_fields.py`
- [x] `commands/install_payment_entry_fields.py`
- [x] `commands/install_watermark_fields.py`
- [x] `commands/install_signature_fields.py`
- [x] `commands/restructure_retention_fields.py`
- [x] `commands/create_wht_amounts_column_break.py`
- [x] `commands/install_enhanced_retention_fields.py`
- [x] `commands/install_item_wht_fields.py`
- [x] `commands/fix_sales_invoice_field_order.py`
- [x] `commands/fix_sales_order_insertion.py`
- [x] `commands/fix_sales_invoice_insertion.py`
- [x] `commands/find_null_fieldnames.py`
- [x] `commands/uninstall_custom_fields.py`
- [x] `commands/test_print_designer_installation.py`
- [x] `commands/validate_construction_service_field.py`
- [x] Various other command files

## Phase C: Business Logic Python — DONE (bulk rename)
- [x] `custom/withholding_tax.py`
- [x] `custom/payment_entry_retention.py`
- [x] `custom/payment_entry_creation_hook.py`
- [x] `custom/payment_entry_thai_tax_population.py`
- [x] `custom/sales_invoice_calculations.py`
- [x] `custom/sales_order_calculations.py`
- [x] `custom/quotation_calculations.py`
- [x] `custom/sales_invoice_retention.py` + variants (_backend, _doctype, _enhanced)
- [x] `custom/sales_invoice_client_script.py`
- [x] `custom/customer_wht_config_handler.py`
- [x] `custom/purchase_invoice_wht_generator.py`
- [x] `regional/purchase_invoice_wht_override.py`
- [x] `regional/purchase_order_wht_override.py`
- [x] `regional/sales_invoice.py`
- [x] `regional/payment_entry.py`
- [x] `overrides/printview_watermark.py`
- [x] `overrides/quotation_mapper.py`
- [x] `accounting/thailand_wht_integration.py`
- [x] `api/withholding_tax_api.py`
- [x] `jinja/macros/watermark.html`
- [x] `hooks.py`
- [x] `uninstall.py`
- [x] `boot.py`
- [x] `install.py`

## Phase D: JavaScript — DONE (bulk rename)
- [x] `public/js/thailand_wht/thailand_wht_sales_invoice.js`
- [x] `public/js/thailand_wht/thailand_wht_sales_order.js`
- [x] `public/js/thailand_wht/thailand_wht_quotation.js`
- [x] `public/js/thailand_wht/thailand_wht_purchase_order.js`
- [x] `public/js/thailand_wht/thailand_wht_purchase_invoice.js`
- [x] `public/js/print_watermark.bundle.js`
- [x] `public/js/payment_entry_thai_tax.js`
- [x] `public/js/delivery_note/delivery_approval.js`

## Phase E: Cross-App References — DONE (bulk rename)
- [x] digisoft_erp: boot.py, dgs_thai_sales_vat.py, payment_entry.py, purchase_invoice.js, input_vat_undue_report.py/.js, install_sales_invoice_thai_fields.py
- [x] inpac_pharma: sales_invoice_template.html, boot.py
- [x] thai_business_suite: sales_invoice_list.js (`vat_treatment`→`pd_custom_vat_treatment`), boot.py, payment_entry.py

## Phase F: DB Migration Command
- [x] Create `thai_business_suite/commands/migrate_pd_fields.py` (156 field renames across 6 DocTypes)
- [x] Register bench commands in TBS hooks.py + `__init__.py`
- [x] Run migration on all 5 active sites (2026-03-08)
  - inpac-pharma: 144 renamed + 2 conflicts resolved
  - m-capital: 144 renamed + 2 conflicts resolved
  - aerocare: 146 renamed + 2 conflicts resolved
  - aksmarthome: 0 (no custom fields installed)
  - tipsiricons: 146 renamed + 2 conflicts resolved
  - Conflict: `custom_withholding_tax_amount` on PI/PE already had `pd_custom_withholding_tax_amount` — deleted old duplicates
- [x] Verify migration: all sites pass `verify-pd-migration`
- [ ] Rollback if needed: `bench --site <site> rollback-pd-migration`

## Phase G: Post-Rename Verification
- [x] `bench build --app print_designer --app thai_business_suite --app inpac_pharma --app digisoft_erp`
- [x] `bench --site [site] clear-cache` (all 5 sites)
- [ ] Verify grep for remaining old field names (exclude patches/)
- [ ] Test SI form — WHT section visible, all fields functional
- [ ] Test SO form — WHT + deposit sections functional
- [ ] Test PI/PO forms — WHT compliance section functional
- [ ] Test PE form — Thai tax population works
- [ ] Print SI — check Jinja template renders WHT/retention correctly

## Post-Migration Hotfixes

### Fix 1: Orphan `vat_treatment` DB columns on SI/SO (2026-03-08)
- **Symptom**: Migration skipped `vat_treatment` on SI/SO ("not found") because Custom Field record didn't exist, but old DB column remained
- **Root cause**: The Custom Field records `Sales Invoice-vat_treatment` and `Sales Order-vat_treatment` were already deleted before migration (likely manual cleanup), so the migration had nothing to rename — but the MariaDB column was left behind
- **Fix**: Copied data from old column → `pd_custom_vat_treatment` (0 rows needed — data already present), then `ALTER TABLE DROP COLUMN vat_treatment` on SI/SO
- **Sites affected**: inpac-pharma, m-capital (aerocare/aksmarthome/tipsiricons had no orphan columns)

### Fix 2: Duplicate `custom_vat_treatment` Custom Fields broke SO list view (2026-03-08)
- **Symptom**: `OperationalError: Unknown column 'tabSales Order.vat_treatment' in 'SELECT'` — SO list view 500 error
- **Root cause**: Two Custom Field records created via Frappe UI (`Sales Invoice-custom_vat_treatment` and `Sales Order-custom_vat_treatment`) with `fieldname=vat_treatment` and `in_list_view=1` coexisted alongside the migrated `pd_custom_vat_treatment` fields. The list view queried BOTH field columns, but the old DB column was already dropped.
- **Fix**: Deleted orphan Custom Fields `{SI,SO}-custom_vat_treatment` + Property Setter `Sales Invoice-vat_treatment-in_list_view` on inpac-pharma and m-capital, then `clear-cache`
- **Lesson**: Always search for `{DocType}-custom_{fieldname}` pattern (Frappe UI-created) in addition to `{DocType}-{fieldname}` (install-script-created) when migrating fields
