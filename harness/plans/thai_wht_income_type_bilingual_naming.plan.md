# Thai WHT Income Type + Tax Withholding Category — Bilingual Naming & Bidirectional Link

## Context

### Current State

```
Thai WHT Income Type
  ├── Doc name:  "PND3-Advertising Income"         ← from CSV Form + Income Category (English)
  ├── Fields:    income_category_th = "ค่าโฆษณา"  ← Thai (translate_to_thai dict)
  │              income_description_th
  │              conditions_th
  └── Link:      tax_withholding_category → Tax Withholding Category ✅

Tax Withholding Category (27 records)
  ├── Doc name:  "WHT 2% Advertising - Individual (PND3)"  ← English
  ├── Fields:    category_name = "ค่าโฆษณา 2% (ภงด.3)"     ← Thai + rate + PND form (seeded)
  │              category_name_en = "Advertising Income"
  └── Link:      (nothing linking back to Thai WHT Income Type)  ← MISSING

Item.pd_custom_wht_income_type  → Tax Withholding Category
  └── Currently shows: English doc name in input field  ← PROBLEM
```

### Problem

Link field (`Item.pd_custom_wht_income_type`) stores **doc name**. Currently:

- Input field → shows English doc name ❌
- Dropdown → shows Thai `category_name` ✅
- Subtitle → shows Thai via `title_field` ✅

### Goal

- Input field → show **Thai** doc name ✅
- Dropdown → show Thai ✅
- Subtitle → show Thai ✅
- Both doctypes use Thai doc names, both feed Thai-language UX

### Data Audit

| Check                          | Result                                                               |
| ------------------------------ | -------------------------------------------------------------------- |
| TWC `category_name` uniqueness | ✅ All 27 unique (rate + PND form makes them unique)                 |
| Orphan TWC                     | ✅ `Services 3%` will be deleted before migration                    |
| CSV                            | ✅ All English, Thai via `translate_to_thai()` dict — **keep as-is** |

---

## Task 1 — Add Reverse Link: Tax Withholding Category → Thai WHT Income Type

### Implementation

User already drafted the field in `install_tax_withholding_category_fields.py` (lines 21-29). Review notes:

- ✅ `fieldname`: `pd_custom_thai_wht_income_type`
- ✅ `options`: `Thai WHT Income Type`
- ✅ `module`: `Print Designer`
- ✅ `fieldname`: `pd_custom_thai_wht_income_type`
- ✅ `options`: `Thai WHT Income Type`
- ✅ `module`: `Print Designer`

```python
{
    "fieldname": "pd_custom_thai_wht_income_type",
    "fieldtype": "Link",
    "label": "Thai WHT Income Type",
    "insert_after": "tax_deduction_basis",
    "options": "Thai WHT Income Type",
    "translatable": 0,
    "read_only": 1,
    "module": "Print Designer",
},
```

#### 1a. Populate field via migration (one-time)

```python
def migrate_twc_thai_wht_links():
    """One-time migration: populate pd_custom_thai_wht_income_type on existing TWCs."""
    twcs = frappe.get_all("Tax Withholding Category", fields=["name"])
    linked = skipped = 0
    for twc in twcs:
        # Thai WHT Income Type stores TWC name in its tax_withholding_category field
        thai_wht = frappe.db.get_value(
            "Thai WHT Income Type",
            {"tax_withholding_category": twc.name},
            "name"
        )
        if thai_wht:
            frappe.db.set_value(
                "Tax Withholding Category",
                twc.name,
                "pd_custom_thai_wht_income_type",
                thai_wht
            )
            linked += 1
        else:
            skipped += 1
            print(f"  Skipped (no link): {twc.name}")
    frappe.db.commit()
    print(f"Linked {linked} TWCs, skipped {skipped}")
```

#### 1b. Install hook (already in user's draft)

```python
# hooks.py
after_install = [
    "print_designer.commands.install_tax_withholding_category_fields.create_tax_withholding_category_fields",
]
after_migrate = [
    "print_designer.commands.install_tax_withholding_category_fields.create_tax_withholding_category_fields",
]
```

Add to `uninstall.py`:

```python
frappe.db.delete("Custom Field", {"dt": "Tax Withholding Category", "fieldname": "pd_custom_thai_wht_income_type"})
```

### Outcome

- Both doctypes now link bidirectionally
- `pd_custom_thai_wht_income_type` is **read-only** — populated by system

---

## Task 2 — Change Doc Names to Thai (Two Doctypes)

### 2a. Thai WHT Income Type → `income_category_th` (Thai)

```
"PND3-Advertising Income"  →  "PND3-ค่าโฆษณา"
```

**Change `autoname`:**

```python
def set_thai_wht_autoname():
    make_property_setter(
        "Thai WHT Income Type",
        "",
        "autoname",
        "field:income_category_th",  # e.g., "PND3-ค่าโฆษณา"
        "Data",
    )
    frappe.db.commit()
```

**One-time rename (26 records):**

```python
def migrate_thai_wht_doc_names():
    """
    Rename: "{form_type}-{income_category}"  →  "{form_type}-{income_category_th}"
    e.g., "PND3-Prize & Awards" → "PND3-รางวัล/ชิงโชค"

    Frappe rename_doc() auto-updates all Link field references.
    """
    records = frappe.get_all(
        "Thai WHT Income Type",
        fields=["name", "form_type", "income_category", "income_category_th", "tax_withholding_category"]
    )
    renamed = 0
    for rec in records:
        old_name = rec.name
        new_name = f"{rec.form_type}-{rec.income_category_th}"
        if old_name == new_name:
            continue
        try:
            frappe.rename_doc("Thai WHT Income Type", old_name, new_name, force=True)
            renamed += 1
        except Exception as e:
            print(f"  Failed: {old_name} → {new_name}: {e}")
    frappe.db.commit()
    print(f"Renamed {renamed} Thai WHT Income Type records")
```

**Update seed script** (`install_thai_wht_income_type.py`):

```python
# Before:
doc_name = f"{record['form_type']}-{record['income_category']}"  # English

# After:
doc_name = f"{record['form_type']}-{translate_to_thai(record['Income Category'])}"  # Thai
```

---

### 2b. Tax Withholding Category → `category_name` (Thai)

```
"WHT 2% Advertising - Individual (PND3)"  →  "ค่าโฆษณา 2% (ภงด.3)"
```

**Why safe:** All 27 TWCs have **unique** `category_name` values (rate + PND form differentiates them, no recipient suffix needed).

**Change `autoname`:**

```python
def set_twc_autoname():
    make_property_setter(
        "Tax Withholding Category",
        "",
        "autoname",
        "field:category_name",  # e.g., "ค่าบริการ 3% (ภงด.53)"
        "Data",
    )
    frappe.db.commit()
```

**One-time rename (26 TWCs):**

⚠️ **Pre-step**: Delete orphan `Services 3%` TWC (NULL `category_name`, no Thai WHT Income Type link, no production references):

```python
def delete_orphan_twc():
    """Delete orphan 'Services 3%' TWC (legacy record, not linked to any Thai WHT Income Type)."""
    if frappe.db.exists("Tax Withholding Category", "Services 3%"):
        frappe.delete_doc("Tax Withholding Category", "Services 3%")
        print("Deleted orphan TWC 'Services 3%'")
```

```python
def migrate_twc_doc_names():
    """
    Rename TWCs from English doc name → category_name (Thai).
    category_name is already unique across all TWCs (rate + PND form differentiates).
    No suffix needed.

    Frappe rename_doc() auto-updates:
    - Thai WHT Income Type.tax_withholding_category (reverse link)
    - All Link field values on Item, Customer, Supplier, Payment Entry, etc.
    """
    twcs = frappe.get_all(
        "Tax Withholding Category",
        fields=["name", "category_name"]
    )
    renamed = 0
    for twc in twcs:
        if twc.name == twc.category_name:
            continue  # already correct
        try:
            frappe.rename_doc("Tax Withholding Category", twc.name, twc.category_name, force=True)
            renamed += 1
        except Exception as e:
            print(f"  Failed: {twc.name} → {twc.category_name}: {e}")
    frappe.db.commit()
    print(f"Renamed {renamed} TWCs")
```

**Update seed script** (`install_tax_withholding_category_data.py`):

```python
# No change needed — seed script already sets doc.name via:
twc.name = twc_name           # English (autoname will override this for NEW records)
twc.category_name = f"{category_name_th} {rate:g}% ({thai_form})"  # Thai

# For NEW records (after autoname change), Frappe auto-sets doc.name = category_name
# So we can stop explicitly setting twc.name during seeding:
# twc.name = twc_name  ← REMOVE this, let autoname handle it
# Keep: twc.category_name = ...
```

---

## Task 3 — CSV: Keep As-Is ✅

No change needed to `print_designer/data/withholding_tax_PND3_PND53.csv`.

- All English — ✅ good for data integrity
- Thai translation via `THAI_TRANSLATIONS` dict in `install_thai_wht_income_type.py` — single source of truth, no duplication
- Translators don't need Python access — dict edits are rare and deliberate

---

## Summary

|                   | Thai WHT Income Type                           | Tax Withholding Category                 |
| ----------------- | ---------------------------------------------- | ---------------------------------------- |
| Thai field        | `income_category_th`                           | `category_name`                          |
| Current doc name  | English                                        | English                                  |
| New doc name      | `PND3-ค่าโฆษณา`                                | `ค่าบริการ 3% (ภงด.53)`                  |
| Autoname change   | `field:income_category_th`                     | `field:category_name`                    |
| Records to rename | 26                                             | 26 (after deleting orphan `Services 3%`) |
| Impact on Item    | `Item.pd_custom_wht_income_type` shows Thai ✅ | Same ✅                                  |

## Files to Create/Modify

| File                                                                 | Action                                                              |
| -------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `print_designer/commands/install_tax_withholding_category_fields.py` | User already drafted — add description, read_only, fix insert_after |
| `print_designer/commands/migrate_twc_thai_wht_links.py`              | Create — one-time: populate pd_custom_thai_wht_income_type          |
| `print_designer/commands/migrate_thai_wht_doc_names.py`              | Create — one-time: rename Thai WHT Income Type to Thai              |
| `print_designer/commands/delete_orphan_twc.py`                       | Create — one-time: delete orphan `Services 3%` TWC                  |
| `print_designer/commands/migrate_twc_doc_names.py`                   | Create — one-time: rename TWC to Thai                               |
| `print_designer/commands/set_autoname_twc.py`                        | Create — set TWC autoname to category_name                          |
| `print_designer/commands/set_autoname_thai_wht.py`                   | Create — set Thai WHT Income Type autoname to income_category_th    |
| `print_designer/commands/install_thai_wht_income_type.py`            | Modify — update doc_name to Thai                                    |
| `print_designer/commands/install_tax_withholding_category_data.py`   | Modify — remove explicit twc.name assignment                        |
| `print_designer/hooks.py`                                            | Modify — add set*autoname*\* hooks                                  |
| `print_designer/uninstall.py`                                        | Modify — remove custom field on uninstall                           |

## Rollback Plan

```bash
# Restore both autonames to Prompt
bench execute "print_designer.commands.revert_autoname.revert_all_autoname"

# Rename back to English (reverse migration)
bench execute "print_designer.commands.revert_doc_names.revert_thai_wht_doc_names"
bench execute "print_designer.commands.revert_doc_names.revert_twc_doc_names"
```
