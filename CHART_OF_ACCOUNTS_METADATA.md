# Chart of Accounts Metadata System

## Concept: Account Properties (Like React Props)

### Problem
ERPNext's standard CoA JSON doesn't tell us which account should be used for what purpose:
- Which is the default Receivable account?
- Which is Input VAT vs Output VAT?
- Which account for Withholding Tax receivable vs payable?

### Solution: Add Metadata Properties
Add special properties to accounts in JSON, similar to React component props:

```json
{
  "Input VAT": {
    "account_type": "Tax",
    "_meta": {
      "is_input_vat": true,
      "default_for": "purchase_tax",
      "auto_assign": "company.default_input_vat_account"
    }
  }
}
```

---

## Metadata Property System

### Standard Properties (ERPNext Native)
These already exist in ERPNext:
```json
{
  "account_name": "Cash",
  "account_number": "1111-00",
  "account_type": "Cash",      // ERPNext account type
  "root_type": "Asset",        // ERPNext root type
  "is_group": 1,              // Group vs Leaf account
  "account_currency": "THB"    // Account currency
}
```

### Custom Metadata Properties (Our Extension)
Add `_meta` object for automation hints:

#### 1. Default Account Assignment
```json
{
  "ลูกหนี้การค้า": {
    "account_type": "Receivable",
    "_meta": {
      "default_for": "receivable",           // Mark as default receivable
      "auto_assign_field": "default_receivable_account"  // Company field to update
    }
  },
  "เจ้าหนี้การค้า": {
    "account_type": "Payable",
    "_meta": {
      "default_for": "payable",
      "auto_assign_field": "default_payable_account"
    }
  }
}
```

#### 2. Tax Account Classification
```json
{
  "ภาษีซื้อ": {
    "account_type": "Tax",
    "_meta": {
      "tax_type": "input_vat",               // Input VAT (purchase)
      "tax_rate": 7.0,                       // Thailand standard rate
      "tax_template": "purchase",            // Use in purchase tax template
      "auto_assign_field": "default_input_vat_account"
    }
  },
  "ภาษีขาย": {
    "account_type": "Tax",
    "_meta": {
      "tax_type": "output_vat",              // Output VAT (sales)
      "tax_rate": 7.0,
      "tax_template": "sales",
      "auto_assign_field": "default_output_vat_account"
    }
  }
}
```

#### 3. Withholding Tax Accounts
```json
{
  "ภาษีหัก ณ ที่จ่ายค้างจ่าย ภงด.1": {
    "account_type": "Tax",
    "_meta": {
      "tax_type": "wht_payable",             // WHT we owe
      "wht_category": "pnd1",                // Form type
      "tax_rates": [1, 2, 3, 5, 10],        // Supported rates
      "is_liability": true
    }
  },
  "ภาษีเงินได้ถูกหักณ.ที่จ่าย": {
    "account_type": "Tax",
    "_meta": {
      "tax_type": "wht_receivable",          // WHT we can claim
      "wht_category": "general",
      "is_asset": true
    }
  }
}
```

#### 4. Special Purpose Accounts
```json
{
  "เงินสด": {
    "account_type": "Cash",
    "_meta": {
      "default_for": "cash",
      "auto_assign_field": "default_cash_account",
      "is_default_mode_of_payment": true
    }
  },
  "เงินฝากธนาคาร": {
    "account_type": "Bank",
    "_meta": {
      "default_for": "bank",
      "auto_assign_field": "default_bank_account",
      "create_mode_of_payment": "Bank Transfer"
    }
  }
}
```

#### 5. Industry-Specific Metadata
```json
{
  "ค่าวิจัยและพัฒนา": {
    "account_type": "Expense",
    "_meta": {
      "industry": "pharmaceutical",
      "cost_center_template": "R&D",
      "requires_approval": true,
      "budget_control": "strict"
    }
  }
}
```

---

## Complete Example: Enhanced Inpac Pharma CoA

### Before (Standard ERPNext Format)
```json
{
  "country_code": "th",
  "name": "Inpac Pharma - Thai Pharmaceutical Chart of Accounts",
  "tree": {
    "สินทรัพย์": {
      "root_type": "Asset",
      "ภาษีซื้อ": {
        "account_number": "1154-00"
      }
    }
  }
}
```

### After (With Metadata Props and Bilingual Support)
```json
{
  "country_code": "th",
  "name": "Inpac Pharma - Thai Pharmaceutical Chart of Accounts",
  "disabled": "No",
  "_meta": {
    "version": "1.0",
    "industry": "pharmaceutical",
    "supports_auto_config": true,
    "created_by": "Inpac Pharma",
    "last_updated": "2025-10-03",
    "bilingual": true,
    "languages": ["th", "en"]
  },
  "tree": {
    "Assets": {
      "account_number": "1000-00",
      "is_group": 1,
      "root_type": "Asset",
      "thai_account": "สินทรัพย์",

      "Current Assets": {
        "account_number": "1100-00",
        "is_group": 1,
        "thai_account": "สินทรัพย์หมุนเวียน",

        "Accounts Receivable and Notes": {
          "account_number": "1130-00",
          "is_group": 1,
          "thai_account": "ลูกหนี้การค้าและตั๋วเงินรับ",

          "Accounts Receivable": {
            "account_number": "1130-01",
            "account_type": "Receivable",
            "thai_account": "ลูกหนี้การค้า",
            "_meta": {
              "default_for": "receivable",
              "auto_assign_field": "default_receivable_account",
              "priority": 1
            }
          }
        },

        "Input VAT": {
          "account_number": "1154-00",
          "account_type": "Tax",
          "thai_account": "ภาษีซื้อ",
          "_meta": {
            "tax_type": "input_vat",
            "tax_rate": 7.0,
            "tax_template": "purchase",
            "auto_assign_field": "default_input_vat_account",
            "thai_form": "pp30",
            "fifo_requirement": true,
            "claim_deadline_months": 6,
            "description": "Input VAT - Claimable within 6 months (FIFO)"
          }
        }
      }
    },

    "Liabilities": {
      "account_number": "2000-00",
      "is_group": 1,
      "root_type": "Liability",
      "thai_account": "หนี้สิน",

      "Current Liabilities": {
        "account_number": "2100-00",
        "is_group": 1,
        "thai_account": "หนี้สินหมุนเวียน",

        "Accounts Payable and Notes": {
          "account_number": "2120-00",
          "is_group": 1,
          "thai_account": "เจ้าหนี้การค้าและตั๋วเงินจ่าย",

          "Accounts Payable": {
            "account_number": "2120-01",
            "account_type": "Payable",
            "thai_account": "เจ้าหนี้การค้า",
            "_meta": {
              "default_for": "payable",
              "auto_assign_field": "default_payable_account",
              "priority": 1
            }
          }
        },

        "Output VAT": {
          "account_number": "2135-00",
          "account_type": "Tax",
          "thai_account": "ภาษีขาย",
          "_meta": {
            "tax_type": "output_vat",
            "tax_rate": 7.0,
            "tax_template": "sales",
            "auto_assign_field": "default_output_vat_account",
            "thai_form": "pp30",
            "vat_status": "due",
            "description": "Output VAT - Due (collected from customers)"
          }
        },

        "WHT Payable - PND.1": {
          "account_number": "2132-01",
          "account_type": "Tax",
          "thai_account": "ภาษีหัก ณ ที่จ่ายค้างจ่าย ภงด.1",
          "_meta": {
            "tax_type": "wht_payable",
            "wht_category": "pnd1",
            "tax_rates": [1, 2, 3, 5, 10],
            "thai_form": "pnd1",
            "description": "WHT Payable - Employee Tax (PND.1)",
            "is_liability": true
          }
        }
      }
    }
  }
}
```

---

## Metadata Property Reference

### Core Properties

#### `_meta.default_for`
Marks account as default for a specific purpose.

**Values**:
- `"receivable"` - Default AR account
- `"payable"` - Default AP account
- `"cash"` - Default cash account
- `"bank"` - Default bank account
- `"income"` - Default income account
- `"expense"` - Default expense account
- `"stock"` - Default inventory account
- `"cogs"` - Cost of goods sold

#### `_meta.auto_assign_field`
Company DocType field to auto-populate.

**Common Fields**:
```python
COMPANY_FIELDS = {
    "default_receivable_account": "Receivable account",
    "default_payable_account": "Payable account",
    "default_cash_account": "Cash account",
    "default_bank_account": "Bank account",
    "default_income_account": "Default income",
    "default_expense_account": "Default expense",
    "round_off_account": "Round off",
    "write_off_account": "Write off",
    "exchange_gain_loss_account": "Exchange gain/loss"
}
```

#### `_meta.tax_type`
Classification of tax account.

**Values**:
- `"input_vat"` - Input VAT (purchase)
- `"output_vat"` - Output VAT (sales)
- `"wht_payable"` - Withholding tax payable
- `"wht_receivable"` - Withholding tax receivable
- `"retention_payable"` - Retention payable
- `"retention_receivable"` - Retention receivable

#### `_meta.tax_template`
Which tax template to include this account in.

**Values**:
- `"sales"` - Sales Taxes and Charges Template
- `"purchase"` - Purchase Taxes and Charges Template
- `"both"` - Include in both templates

#### `_meta.priority`
When multiple accounts match, use priority (1 = highest).

**Example**:
```json
{
  "ลูกหนี้การค้า": {
    "_meta": {"priority": 1}  // This is THE default
  },
  "ลูกหนี้อื่น": {
    "_meta": {"priority": 2}  // Fallback option
  }
}
```

---

## Implementation Strategy

### Phase 2: Read Metadata and Auto-Assign

```python
def auto_assign_default_accounts(self):
    """
    Phase 2: Use _meta properties to auto-assign default accounts
    """
    # Find all accounts with _meta.default_for property
    accounts = frappe.get_all(
        "Account",
        filters={"company": self.name},
        fields=["name", "account_name", "account_type"]
    )

    # Load CoA JSON to get metadata
    coa_data = load_coa_json(self.chart_of_accounts)
    metadata_map = extract_metadata_from_coa(coa_data)

    # Assign defaults based on metadata
    for account in accounts:
        meta = metadata_map.get(account.account_name)
        if meta and meta.get("auto_assign_field"):
            field_name = meta["auto_assign_field"]
            if hasattr(self, field_name):
                setattr(self, field_name, account.name)

    self.save()
```

### Phase 3: Tax Template Generation

```python
def auto_create_tax_templates(self):
    """
    Phase 3: Use _meta.tax_type and _meta.tax_template to create templates
    """
    coa_data = load_coa_json(self.chart_of_accounts)
    tax_accounts = extract_tax_accounts_from_metadata(coa_data)

    # Create Sales Tax Template
    sales_taxes = [acc for acc in tax_accounts if acc["tax_template"] in ["sales", "both"]]
    if sales_taxes:
        create_sales_tax_template(self.name, sales_taxes)

    # Create Purchase Tax Template
    purchase_taxes = [acc for acc in tax_accounts if acc["tax_template"] in ["purchase", "both"]]
    if purchase_taxes:
        create_purchase_tax_template(self.name, purchase_taxes)
```

---

## Backward Compatibility

### Handling CoA Without Metadata
If `_meta` properties are not present, fall back to ERPNext standard logic:

```python
def get_default_account(self, account_type):
    """Get default account with metadata or fallback to type-based search"""

    # Try metadata first
    account = find_account_by_metadata(
        company=self.name,
        default_for=account_type
    )

    if account:
        return account

    # Fallback: ERPNext standard - first non-group account of type
    return frappe.db.get_value(
        "Account",
        {
            "company": self.name,
            "account_type": account_type,
            "is_group": 0
        },
        "name"
    )
```

---

## Benefits of Metadata System

### 1. Self-Documenting
CoA file itself explains what each account is for:
```json
{
  "ภาษีซื้อ": {
    "_meta": {
      "description": "Input VAT - Claimable within 6 months (FIFO)",
      "tax_type": "input_vat"
    }
  }
}
```

### 2. Automation-Ready
Machine can read metadata and configure automatically:
- No hardcoded account names
- No language-dependent detection
- Works for any language (Thai, English, etc.)

### 3. Industry Templates
Easy to create specialized templates:
```json
{
  "_meta": {
    "industry": "pharmaceutical",
    "compliance": ["FDA", "GMP", "Thai_Revenue"]
  }
}
```

### 4. Versioning
Track changes to CoA structure:
```json
{
  "_meta": {
    "version": "2.0",
    "changelog": "Added retention accounts for construction industry"
  }
}
```

### 5. Validation
Metadata enables smart validation:
```python
if meta.get("tax_type") == "input_vat":
    assert meta.get("tax_rate") == 7.0, "Thailand VAT must be 7%"
```

---

## Standard Metadata Schema (Proposed)

```typescript
interface AccountMetadata {
  // Default assignment
  default_for?: "receivable" | "payable" | "cash" | "bank" | "income" | "expense" | "stock" | "cogs";
  auto_assign_field?: string;  // Company field name
  priority?: number;            // 1 = highest priority

  // Tax classification
  tax_type?: "input_vat" | "output_vat" | "wht_payable" | "wht_receivable" | "retention_payable" | "retention_receivable";
  tax_rate?: number;           // Default tax rate
  tax_rates?: number[];        // Supported rates (for WHT)
  tax_template?: "sales" | "purchase" | "both";

  // Thai-specific
  thai_form?: "pp30" | "pp36" | "pnd1" | "pnd3" | "pnd53";
  wht_category?: "pnd1" | "pnd3" | "pnd53" | "general";

  // Industry-specific
  industry?: string;           // "pharmaceutical", "construction", etc.
  cost_center_template?: string;
  requires_approval?: boolean;
  budget_control?: "none" | "advisory" | "strict";

  // Documentation
  description?: string;        // Human-readable description
  notes?: string;             // Additional notes

  // Automation hints
  create_mode_of_payment?: string;     // Auto-create payment mode
  is_default_mode_of_payment?: boolean;

  // Metadata about metadata
  version?: string;
  last_updated?: string;
  created_by?: string;
}
```

---

## Next Steps

1. **Update Inpac Pharma CoA** with `_meta` properties
2. **Create helper functions** to read metadata from JSON
3. **Implement Phase 2** using metadata for auto-assignment
4. **Test with multiple CoA templates** to validate approach
5. **Document metadata standard** for other developers

This metadata system makes the CoA truly "smart" and automation-ready! 🚀
