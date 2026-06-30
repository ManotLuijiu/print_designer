# Language-Aware Number-to-Words Field Pairs

## Goal

Allow Print Designer to display a numeric document field as words through a separate, draggable target field. The rendered words must follow the print language, independently of the Desk user's preferred language, without saving translated preview or print values back to the business document.

The first required pair is:

```text
source: pd_custom_net_total_after_wht_details
target: pd_custom_net_total_after_wht_words_details
```

## Required behavior

The public operation is conceptually:

```python
number_to_words(source_field, target_field)
```

For a Payment Entry whose source value is `101850.00`:

- The target remains an actual DocField, so it is available in the Print Designer field menu and can be positioned like any other Design element.
- A Thai effective print language produces Thai amount words in the target element.
- An English effective print language produces English amount words in the target element.
- Existing English text stored in the target must not prevent a Thai print from rendering Thai words.
- Rendering must not write the computed value to the database.

## Language resolution

Use the print context rather than the Desk interface language. Resolution follows Frappe's print behavior:

1. An explicitly selected language in the Print sidebar.
2. The selected Print Format's `default_print_language`.
3. The document language, when applicable.
4. The current user's language as the final fallback.

Frappe's Print page normally expresses the resolved choice through `_lang`. Direct rendering code must also receive the Print Format name so its default remains available when no explicit language was supplied.

Changing the Desk menu language must not override a Thai default on the Receipt Print Format.

## Configuration

Field relationships are data, not hardcoded branches in the PDF renderer. Print Designer will support declarative pairs containing:

```json
{
  "source_field": "pd_custom_net_total_after_wht_details",
  "target_field": "pd_custom_net_total_after_wht_words_details",
  "currency_field": "paid_from_account_currency"
}
```

`currency_field` is optional. When absent, the resolver uses the document's applicable transaction currency and finally the system default currency.

The pair list belongs to Print Designer configuration associated with the Print Format. Adding another pair must require configuration only, not another Python `if` statement or tuple entry. Configuration is validated when loaded:

- source and target must exist in the Print Format's DocType metadata;
- source must be numeric (`Currency`, `Float`, `Int`, or `Percent`);
- target must be text-compatible (`Data`, `Small Text`, `Text`, or `Long Text`);
- source and target must differ;
- malformed entries are ignored and logged without breaking the print.

The existing Receipt pair will be installed as the initial configuration. A small API accepts `source_field` and `target_field` so configuration UI and future setup scripts use one validation path.

## Shared resolver

A focused server-side service will:

1. Resolve and validate configured field pairs.
2. Resolve the effective print language.
3. Read the numeric value from each source field.
4. Convert it with the language-appropriate converter.
5. Assign the result only to the in-memory document used for rendering.

Thai uses the existing `thai_money_in_words` implementation. Other languages use Frappe's `money_in_words` under the resolved language context. Conversion failure leaves the original target value intact and records a diagnostic log entry.

The service must not call `db_set`, `frappe.db.set_value`, or `save`.

## PDF flow

The existing `before_print` integration invokes the shared resolver after the document and Print Format are known but before Jinja renders Design elements. Consequently the normal dynamic-field macro can continue using `doc.get_formatted(target_field)`; no field-specific Jinja is required.

The current hardcoded `words_field_to_source` logic will be replaced by the configured-pair resolver. Existing supported pairs must be migrated into configuration or covered through a backward-compatible configuration source before that tuple is removed.

## Design View flow

Design View continues loading ordinary document fields, including the target field. After it knows the selected document and Print Format, it requests computed preview values from the shared server-side resolver. The response contains target-field/value pairs only. Those values overlay the in-memory preview data and are never saved to the Payment Entry.

Changing the selected document, Print Format language, or pair configuration refreshes the computed preview. If the source value is empty, the target preview is empty rather than a raw Jinja placeholder.

## Tests

Regression coverage must prove:

- Thai Print Format default overrides an English Desk preference when no explicit print selection is supplied.
- An explicit print-language selection is respected.
- The configured Payment Entry source produces Thai text in its target.
- The same pair produces English text under English print language.
- Stored English target text is replaced only on the temporary Thai render document.
- The original document value and database record remain unchanged.
- Multiple configured pairs are resolved without adding field-specific code.
- Invalid configurations are skipped safely.
- Design View receives the same computed value as PDF rendering.
- Empty numeric sources do not display `{{ fieldname }}`.

Frontend dependency versions and lockfiles are outside this change. If implementation unexpectedly changes Vue, Pinia, build tooling, or `yarn.lock`, the repository's full dependency regression, build, cache-clear, and authenticated Playwright policy becomes mandatory.

## Non-goals

- Translating arbitrary stored text fields.
- Persisting one language's words into Payment Entry.
- Inferring field relationships solely from field names.
- Changing Frappe's standard Print sidebar URL behavior.
