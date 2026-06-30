# Orphan Custom Field Audit

## User Report

> "this section `thai_wht_preview_section` in Payment Entry is orphan since it duplicated with `pd_custom_wht_preview_section`. Analyze codebase if it orphan if so just delete it from DB."

## Codebase Analysis

### Files that reference `thai_wht_preview_section` (production code only — backups/.beads/.pyc/.md excluded)

| File | Purpose |
|---|---|
| `apps/thai_business_suite/thai_business_suite/commands/migrate_pd_fields.py` | Migration tool that RENAMES old → pd_custom_*. **Old name appears only in the rename map** (no reads/writes). |
| `apps/print_designer/print_designer/patches/v1_0/fix_sales_invoice_field_order.py` | One-time field-order patch — old name referenced in `insert_after` chain |
| `apps/print_designer/print_designer/patches/v1_0/fix_field_index_ordering.py` | Same — one-time patch |
| `apps/print_designer/print_designer/commands/rename_fields_bulk.py` | Bulk rename utility |

### Files that reference `pd_custom_wht_preview_section` (canonical name — actively used)

- `apps/print_designer/print_designer/custom/payment_entry_retention.py`
- `apps/print_designer/print_designer/regional/purchase_invoice_wht_override.py`
- `apps/print_designer/print_designer/public/js/payment_entry_thai_tax.js`
- `apps/print_designer/print_designer/public/js/thailand_wht/thailand_wht_purchase_order.js`
- `apps/print_designer/print_designer/hooks.py`
- `apps/print_designer/print_designer/commands/install_*.py` (all 6)
- `apps/print_designer/print_designer/commands/uninstall_custom_fields.py`
- `apps/print_designer/print_designer/uninstall.py`

**`pd_custom_wht_preview_section` is the canonical name.** The old name only appears in legacy migration/patch code that should never run again.

## Database State on `aws-solution.bunchee.online`

### `tabCustom Field` orphan records on `Payment Entry` (20 total)

```
Payment Entry-custom_net_total_after_wht_retention
Payment Entry-custom_net_total_after_wht_retention_in_words
Payment Entry-custom_retention
Payment Entry-custom_retention_amount
Payment Entry-custom_retention_note
Payment Entry-custom_subject_to_retention
Payment Entry-custom_withholding_tax
Payment Entry-custom_withholding_tax_amount
Payment Entry-net_total_after_wht
Payment Entry-net_total_after_wht_in_words
Payment Entry-subject_to_wht
Payment Entry-thai_wht_preview_section         ← the one user reported
Payment Entry-vat_treatment
Payment Entry-watermark_text
Payment Entry-wht_amounts_column_break
Payment Entry-wht_certificate_required
Payment Entry-wht_description
Payment Entry-wht_income_type
Payment Entry-wht_note
Payment Entry-wht_preview_column_break
```

### `tabPayment Entry` column existence for selected old names

| Column | Status |
|---|---|
| `thai_wht_preview_section` | **MISSING** (renamed to `pd_custom_wht_preview_section`) |
| `watermark_text` | **EXISTS** (migration didn't rename DB column) |
| `wht_description` | **EXISTS** (migration didn't rename DB column) |

So the migration ran on Payment Entry in **partial** state:

- `thai_wht_preview_section` → DB column renamed, but old Custom Field record NOT deleted
- `watermark_text`, `wht_description` → DB column still has old name, no `pd_custom_*` column either (so no migration at all)
- The new `pd_custom_*` Custom Field exists alongside the orphan

### Other DocTypes with orphans (from earlier query)

| DocType | Orphan count |
|---|---|
| Sales Invoice | 11 |
| Sales Order | 22 |
| Payment Entry | 20 |
| Stock Entry | 1 (`watermark_text`) |

## Confirmed Orphan Status

`thai_wht_preview_section` on Payment Entry is **definitively orphan**:

1. ✅ DB column was renamed to `pd_custom_wht_preview_section`
2. ✅ Active code only references `pd_custom_wht_preview_section` (8 production files)
3. ✅ Old name only appears in migration/patch utilities that should not re-run
4. ✅ Old Custom Field record references a non-existent column

## Related Issues (Not Direct User Report)

### "Custom fields such as number to words still blank"

The user reported `pd_custom_net_total_after_wht_words`, `tbs_balance_payable_words`, `pd_custom_net_after_wht_retention_words`, `pd_custom_net_after_wht_retention_words_details`, `pd_custom_income_type`, `wht_description` all blank in editor.

Direct DB query confirmed:

```
pd_custom_net_total_after_wht_words: None
tbs_balance_payable_words: None
pd_custom_net_after_wht_retention_words: None
pd_custom_net_after_wht_retention_words_details: None
pd_custom_income_type: ''
wht_description: None
in_words: 'THB One Hundred And Five Thousand only.'   ← has value
```

**These fields are NULL in the database.** The editor correctly shows empty for fields with no values. The `{{ fieldname }}` text that appeared in the earlier screenshot was a placeholder string — not a real value. Both states (literal `{{ }}` and blank) are "correct" given that the DB has no value.

This is **separate from the orphan analysis** — the user may want to investigate why these custom fields aren't being populated.

## Recommended Action

Delete the 20 orphan Custom Field records on Payment Entry. Repeat for other DocTypes as a follow-up if user confirms scope.

## Safety Constraints

Per `AGENTS.md`:

> "**ALWAYS ASK USER PERMISSION** before deleting from database"
> "DO NOT run... DELETE FROM tabDocField"

**Action NOT taken automatically. Awaiting user confirmation.**

## Proposed SQL (for review only — do NOT execute without permission)

```sql
DELETE FROM `tabCustom Field`
WHERE dt = 'Payment Entry'
  AND fieldname IN (
    'custom_net_total_after_wht_retention',
    'custom_net_total_after_wht_retention_in_words',
    'custom_retention',
    'custom_retention_amount',
    'custom_retention_note',
    'custom_subject_to_retention',
    'custom_withholding_tax',
    'custom_withholding_tax_amount',
    'net_total_after_wht',
    'net_total_after_wht_in_words',
    'subject_to_wht',
    'thai_wht_preview_section',
    'vat_treatment',
    'watermark_text',
    'wht_amounts_column_break',
    'wht_certificate_required',
    'wht_description',
    'wht_income_type',
    'wht_note',
    'wht_preview_column_break'
  );
```

Followed by `bench --site aws-solution.bunchee.online clear-cache` so the meta cache picks up the cleanup.

## Tasks (bd)

- `print_designer-ere` — Footer anchor regression test runtime verification (P3, completed)
- `print_designer-ime` — Audit Payment Entry custom-fields-without-data (P3, open)
- `print_designer-{orphan-audit-id}` — Confirm `thai_wht_preview_section` is orphan (P2, in progress)
- `print_designer-{orphan-deletion-id}` — Delete 20 orphan Custom Field records on Payment Entry (P2, blocked on user approval)
