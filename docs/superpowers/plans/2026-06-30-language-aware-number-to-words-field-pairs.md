# Language-Aware Number-to-Words Field Pairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render configured numeric source fields through separate, draggable words target fields in Design View and PDF using the effective print language, without persisting translated output.

**Architecture:** Store declarative pairs in each Print Format's existing `print_designer_settings` JSON. A focused Python resolver validates pairs, resolves language, converts values, and mutates only the in-memory render document; PDF and a permission-checked Design View endpoint share it. The Vue/Pinia editor edits and persists pairs, then overlays preview values into `docData`.

**Tech Stack:** Frappe/ERPNext Python, Vue 3.5.12, Pinia 2.3.1, Frappe Desk controls, Python unittest/Frappe tests.

---

### Task 1: Shared field-pair resolver

**Files:**
- Create: `print_designer/utils/number_to_words_fields.py`
- Create: `print_designer/tests/test_number_to_words_fields.py`

- [ ] **Step 1: Write failing tests for validation and conversion**

Test this public API with fake metadata and documents:

```python
def test_validates_multiple_pairs():
    pairs = [
        {"source_field": "amount", "target_field": "amount_words"},
        {"source_field": "tax", "target_field": "tax_words"},
    ]
    assert validate_number_to_words_pairs(fake_meta, pairs) == pairs

def test_thai_replaces_stored_english_on_temporary_doc():
    doc = SimpleNamespace(amount=100, amount_words="One Hundred", currency="THB")
    values = apply_number_to_words_pairs(doc, fake_meta, PAIRS, language="th")
    assert values == {"amount_words": "หนึ่งร้อยบาทถ้วน"}
    assert doc.amount_words == "หนึ่งร้อยบาทถ้วน"

def test_empty_source_clears_temporary_target():
    doc = SimpleNamespace(amount=None, amount_words="old")
    assert apply_number_to_words_pairs(doc, fake_meta, PAIRS, "th") == {"amount_words": ""}
```

Also test rejection of missing fields, same source/target, nonnumeric sources, and nontext targets.

- [ ] **Step 2: Run tests and verify RED**

```bash
bench --site aws-solution.bunchee.online run-tests --app print_designer --module print_designer.tests.test_number_to_words_fields
```

Expected: FAIL because `print_designer.utils.number_to_words_fields` does not exist.

- [ ] **Step 3: Implement the minimal resolver**

Expose:

```python
NUMERIC_FIELD_TYPES = frozenset({"Currency", "Float", "Int", "Percent"})
TEXT_FIELD_TYPES = frozenset({"Data", "Small Text", "Text", "Long Text"})

def validate_number_to_words_pairs(meta, pairs): ...
def convert_amount_to_words(amount, language, currency="THB"): ...
def apply_number_to_words_pairs(doc, meta, pairs, language): ...
```

Thai calls `thai_money_in_words`. Other languages call Frappe `money_in_words` inside a helper that temporarily sets and always restores `frappe.local.lang`. Currency resolution order is configured `currency_field`, `currency`, `paid_from_account_currency`, `paid_to_account_currency`, system default, then `THB`. Empty source returns an empty target. No database write APIs are permitted.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add print_designer/utils/number_to_words_fields.py print_designer/tests/test_number_to_words_fields.py
git commit -m "feat: add number-to-words field pair resolver"
```

### Task 2: Configuration and PDF integration

**Files:**
- Modify: `print_designer/utils/number_to_words_fields.py`
- Modify: `print_designer/pdf.py:13-76,425-530`
- Modify: `print_designer/tests/test_number_to_words_fields.py`

- [ ] **Step 1: Add failing settings and language tests**

```python
def test_reads_pairs_from_designer_settings():
    pf = SimpleNamespace(print_designer_settings=json.dumps({
        "numberToWordsFieldPairs": [{"source_field": "amount", "target_field": "amount_words"}]
    }))
    assert get_number_to_words_pairs(pf)[0]["source_field"] == "amount"

def test_explicit_language_wins():
    assert resolve_print_language(SimpleNamespace(default_print_language="th"), "en", None, "th") == "en"

def test_format_default_wins_over_english_menu():
    assert resolve_print_language(SimpleNamespace(default_print_language="th"), None, None, "en") == "th"
```

- [ ] **Step 2: Run focused tests and verify RED**

Expected: FAIL because `get_number_to_words_pairs` and `resolve_print_language` are absent.

- [ ] **Step 3: Implement settings and language helpers**

```python
def get_number_to_words_pairs(print_format):
    settings = frappe.parse_json(print_format.print_designer_settings or "{}") or {}
    return settings.get("numberToWordsFieldPairs") or []

def resolve_print_language(print_format, explicit_language=None, document_language=None, user_language=None):
    return explicit_language or print_format.get("default_print_language") or document_language or user_language or "en"
```

Normalize Thai aliases (`ไทย`, `thai`, `th-TH`) to `th`.

- [ ] **Step 4: Replace PDF's hardcoded pair tuple**

In `_handle_thai_amount_enhancement`, call the shared resolver using `doc`, `frappe.get_meta(doc.doctype)`, Print Format pairs, and effective language. Remove `words_field_to_source`; retain standard `doc.in_words` handling. Update `get_effective_language` to explicit selection → format default → document language → user language.

- [ ] **Step 5: Verify focused and render regression tests**

```bash
bench --site aws-solution.bunchee.online run-tests --app print_designer --module print_designer.tests.test_number_to_words_fields
bench --site aws-solution.bunchee.online run-tests --app print_designer --module print_designer.tests.test_print_designer_render_correctness
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

```bash
git add print_designer/utils/number_to_words_fields.py print_designer/pdf.py print_designer/tests/test_number_to_words_fields.py
git commit -m "fix: render configured words fields in print language"
```

### Task 3: Design View resolver endpoint

**Files:**
- Modify: `print_designer/print_designer/page/print_designer/print_designer.py:119-160`
- Modify: `print_designer/tests/test_number_to_words_fields.py`

- [ ] **Step 1: Write a failing permission-checked endpoint test**

Patch document/format retrieval and assert:

```python
result = get_number_to_words_preview(
    doctype="Payment Entry",
    docname="ACC-PAY-2606-00001",
    print_format="Receipt",
)
assert result == {"pd_custom_net_total_after_wht_words_details": "หนึ่งแสน...บาทถ้วน"}
doc.check_permission.assert_called_once_with("read")
doc.save.assert_not_called()
```

- [ ] **Step 2: Run focused tests and verify RED**

Expected: FAIL because `get_number_to_words_preview` is absent.

- [ ] **Step 3: Implement the endpoint**

```python
@frappe.whitelist(allow_guest=False)
def get_number_to_words_preview(doctype, docname, print_format, language=None):
    doc = frappe.get_doc(doctype, docname)
    doc.check_permission("read")
    format_doc = frappe.get_doc("Print Format", print_format)
    if format_doc.doc_type != doctype:
        frappe.throw(_("Print Format does not belong to this document type"))
    lang = resolve_print_language(format_doc, language, doc.get("language"), frappe.local.lang)
    return apply_number_to_words_pairs(doc, frappe.get_meta(doctype), get_number_to_words_pairs(format_doc), lang)
```

Do not save the request-scoped document.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run Task 1's test command. Expected: PASS.

- [ ] **Step 5: Commit Task 3**

```bash
git add print_designer/print_designer/page/print_designer/print_designer.py print_designer/tests/test_number_to_words_fields.py
git commit -m "feat: expose words fields to design preview"
```

### Task 4: Editor configuration and preview overlay

**Files:**
- Modify: `print_designer/public/js/print_designer/store/MainStore.js:1-105`
- Modify: `print_designer/public/js/print_designer/store/ElementStore.js:530-578,1526-1585`
- Modify: `print_designer/public/js/print_designer/store/fetchMetaAndData.js:109-150`
- Modify: `print_designer/public/js/print_designer/PropertiesPanelState.js:317-485`
- Create: `print_designer/tests/test_number_to_words_editor_contract.py`

- [ ] **Step 1: Write failing source-contract tests**

Assert the editor contains all contracts:

```python
assert "numberToWordsFieldPairs: MainStore.numberToWordsFieldPairs" in ELEMENT_STORE.read_text()
assert "settings.numberToWordsFieldPairs || []" in ELEMENT_STORE.read_text()
assert "get_number_to_words_preview" in FETCH_META.read_text()
assert "Object.assign(doc, previewValues)" in FETCH_META.read_text()
assert 'fieldname: "source_field"' in PROPERTIES_PANEL.read_text()
assert 'fieldname: "target_field"' in PROPERTIES_PANEL.read_text()
```

- [ ] **Step 2: Run contract tests and verify RED**

```bash
python -m unittest print_designer.tests.test_number_to_words_editor_contract -v
```

Expected: FAIL.

- [ ] **Step 3: Add state and persistence**

Add `numberToWordsFieldPairs: []` to `MainStore`; save it in `settingsForSave`; restore it in `loadSettings` with `settings.numberToWordsFieldPairs || []`.

- [ ] **Step 4: Add a Page Settings pair dialog**

Add a `Number to Words Fields` button opening a `frappe.ui.Dialog` Table with required `source_field` and `target_field`, plus optional `currency_field`. Populate source options from numeric meta fields and target options from text meta fields. Copy sanitized rows to `MainStore.numberToWordsFieldPairs` on confirm.

- [ ] **Step 5: Overlay preview values**

After `frappe.db.get_doc` and metadata filtering, call `get_number_to_words_preview` when pairs exist, then:

```javascript
const previewValues = response.message || {};
Object.assign(doc, previewValues);
MainStore.docData = doc;
```

Do not call document save APIs.

- [ ] **Step 6: Run editor and backend tests**

Run Task 4's unittest command and Task 1's bench command. Expected: PASS.

- [ ] **Step 7: Commit Task 4**

```bash
git add print_designer/public/js/print_designer/store/MainStore.js print_designer/public/js/print_designer/store/ElementStore.js print_designer/public/js/print_designer/store/fetchMetaAndData.js print_designer/public/js/print_designer/PropertiesPanelState.js print_designer/tests/test_number_to_words_editor_contract.py
git commit -m "feat: configure words fields in print designer"
```

### Task 5: Seed Receipt and verify end to end

**Files:**
- Create: `print_designer/patches/v1_8/add_receipt_number_to_words_pair.py`
- Modify: `print_designer/patches.txt`
- Modify: `print_designer/tests/test_number_to_words_fields.py`

- [ ] **Step 1: Write a failing idempotent merge test**

```python
settings = {"numberToWordsFieldPairs": []}
pair = {"source_field": "pd_custom_net_total_after_wht_details", "target_field": "pd_custom_net_total_after_wht_words_details"}
merge_number_to_words_pair(settings, pair)
merge_number_to_words_pair(settings, pair)
assert settings["numberToWordsFieldPairs"] == [pair]
```

- [ ] **Step 2: Run focused tests and verify RED**

Expected: FAIL because the merge helper is absent.

- [ ] **Step 3: Implement merge helper and migration patch**

The patch loads `Receipt` only when present, verifies `doc_type == "Payment Entry"`, verifies both Custom Fields exist, parses settings, merges by `(source_field, target_field)`, and updates only changed settings. Sites without this format or fields are skipped safely.

- [ ] **Step 4: Run quality gates**

```bash
bench --site aws-solution.bunchee.online run-tests --app print_designer --module print_designer.tests.test_number_to_words_fields
python -m unittest print_designer.tests.test_number_to_words_editor_contract -v
bench --site aws-solution.bunchee.online run-tests --app print_designer --module print_designer.tests.test_print_designer_render_correctness
ruff check print_designer/utils/number_to_words_fields.py print_designer/print_designer/page/print_designer/print_designer.py print_designer/tests/test_number_to_words_fields.py
bench build --app print_designer
```

Expected: every command exits 0. No Vue, Pinia, build-tool, package, or lockfile change is expected.

- [ ] **Step 5: Apply patch and clear target cache**

```bash
bench --site aws-solution.bunchee.online migrate
bench --site aws-solution.bunchee.online clear-cache
```

Expected: exit 0. Obtain deployment authorization before this state-changing step.

- [ ] **Step 6: Authenticated browser verification**

Verify `/desk/print-designer/Receipt` shows the configured pair and Thai preview while Desk menus remain English; Thai and English Print sidebar choices produce corresponding PDF words; Payment Entry `ACC-PAY-2606-00001` remains unchanged after preview/PDF generation.

- [ ] **Step 7: Commit, close issue, and push**

```bash
git add print_designer/patches/v1_8/add_receipt_number_to_words_pair.py print_designer/patches.txt print_designer/tests/test_number_to_words_fields.py
git commit -m "fix: configure Receipt amount words rendering"
bd close print_designer-nx8 --reason="Implemented and verified language-aware number-to-words field pairs"
git pull --rebase
bd dolt push
git push
git status --short --branch
```

Expected: branch is up to date with its remote; unrelated pre-existing changes remain untouched.
