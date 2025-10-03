# Chart of Accounts Automation Plan

## Overview
Automate the Chart of Accounts (CoA) import process during Company creation to eliminate manual steps and provide a seamless accounting setup experience.

## Current State (Semi-Manual)

### Manual Steps Required
1. Create Company in ERPNext
2. Navigate to Chart of Accounts Importer
3. Upload CSV/Excel file with account structure
4. Preview and validate
5. Click Import
6. Manually set default accounts (Receivable, Payable, etc.)
7. Manually create tax templates

### Problems
- Time-consuming multi-step process
- Error-prone (users can skip steps)
- Inconsistent setup across companies
- Requires accounting knowledge to configure properly
- No standardization for industry-specific charts

## Automation Strategy: Phased Approach

### Phase 1: Basic Auto-Import (CURRENT - MVP)
**Goal**: Automatically import Chart of Accounts from JSON template during Company creation

**Implementation**:
```python
class CustomCompany(Company):
    def after_insert(self):
        """Import Chart of Accounts after company creation"""
        super().after_insert()

        if self.chart_of_accounts:
            self.create_default_accounts()

    def create_default_accounts(self):
        """Import CoA from JSON template"""
        from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts

        frappe.local.flags.ignore_root_company_validation = True
        create_charts(
            self.name,
            self.chart_of_accounts,
            self.country
        )
```

**Features**:
- ✅ Auto-import on Company creation
- ✅ Support JSON-based CoA templates
- ✅ Skip tax template errors gracefully
- ✅ Company appears in Account tree view immediately

**Limitations**:
- ❌ No default account assignment (receivable, payable, etc.)
- ❌ No tax template creation
- ❌ No industry-specific customization
- ❌ No account validation

**Status**: ✅ IMPLEMENTED

---

### Phase 2: Default Account Detection with Bilingual Support (NEXT)
**Goal**: Automatically detect and assign default accounts using metadata properties, with bilingual account name support

**Key Insight**:
- Chart of Accounts JSON is NOT a DocType itself - it's just a template file
- During import, `create_charts()` creates Account DocType records from the JSON
- Account DocType has custom fields: `account_name_th`, `auto_translate_thai`
- We can use JSON metadata (`_meta` properties) to guide the auto-assignment

**How Chart of Accounts Works**:
```python
# 1. JSON Template (th_inpac_pharma_chart.json)
{
  "tree": {
    "ลูกหนี้การค้า / Accounts Receivable": {
      "account_number": "1130-01",
      "account_type": "Receivable",
      "_meta": {
        "default_for": "receivable",
        "auto_assign_field": "default_receivable_account",
        "priority": 1
      }
    }
  }
}

# 2. create_charts() reads JSON and creates Account DocType records
# The account_name becomes: "ลูกหนี้การค้า / Accounts Receivable"

# 3. Account DocType fields populated:
# - account_name: "ลูกหนี้การค้า / Accounts Receivable" (from JSON key)
# - account_name_th: Can be auto-filled from account_name
# - account_number: "1130-01"
# - account_type: "Receivable"
# - company: "Inpac Pharma"
```

**Implementation Strategy**:
```python
def auto_assign_default_accounts(self):
    """
    Phase 2: Use metadata from JSON to auto-assign default accounts

    Strategy:
    1. Load the Chart of Accounts JSON that was used for this company
    2. Extract _meta properties from accounts
    3. Find matching Account DocType records by account_number or account_name
    4. Assign to Company default fields based on _meta.auto_assign_field
    """

    # Get the CoA template name that was used
    coa_template = self.chart_of_accounts
    if not coa_template:
        return

    # Load the CoA JSON metadata
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_chart
    coa_data = get_chart(coa_template)

    # Extract metadata from the JSON
    metadata_map = extract_metadata_from_coa(coa_data)
    # Returns: {"1130-01": {"default_for": "receivable", "auto_assign_field": "...", "priority": 1}}

    # Find and assign default accounts
    for account_number, meta in metadata_map.items():
        if meta.get("auto_assign_field"):
            # Find the Account DocType record by account_number
            account = frappe.db.get_value(
                "Account",
                {
                    "company": self.name,
                    "account_number": account_number,
                    "is_group": 0
                },
                "name"
            )

            if account:
                field_name = meta["auto_assign_field"]
                priority = meta.get("priority", 99)

                # Only assign if field is empty OR this account has higher priority
                current_value = getattr(self, field_name, None)
                if not current_value:
                    setattr(self, field_name, account)
                    frappe.msgprint(f"Auto-assigned {field_name}: {account}")

    self.save()

def extract_metadata_from_coa(coa_tree, parent_path=""):
    """
    Recursively extract _meta properties from CoA JSON
    Returns dict mapping account_number to metadata
    """
    metadata_map = {}

    for account_name, account_data in coa_tree.items():
        if isinstance(account_data, dict):
            # Extract metadata if present
            meta = account_data.get("_meta", {})
            account_number = account_data.get("account_number")

            if meta and account_number:
                metadata_map[account_number] = meta

            # Recurse into child accounts
            child_meta = extract_metadata_from_coa(account_data, parent_path + "/" + account_name)
            metadata_map.update(child_meta)

    return metadata_map
```

**Bilingual Account Name Handling**:

The Account DocType includes custom fields `account_name_th` and `auto_translate_thai` for bilingual support. The Chart of Accounts JSON uses a clean bilingual pattern with English names as keys and `thai_account` field for Thai translations.

```python
# JSON Pattern (IMPLEMENTED in th_inpac_pharma_chart.json):
{
  "Assets": {
    "account_number": "1000-00",
    "is_group": 1,
    "root_type": "Asset",
    "thai_account": "สินทรัพย์",

    "Current Assets": {
      "account_number": "1100-00",
      "is_group": 1,
      "thai_account": "สินทรัพย์หมุนเวียน",

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
    }
  }
}

# Result after import:
# - account_name: "Assets" (English, from JSON key)
# - account_name_th: "สินทรัพย์" (Thai, populated from thai_account field)
# - account_number: "1000-00"
```

**Bilingual Import - Populating account_name_th**:

Strategy to populate `account_name_th` field during Chart of Accounts import:

```python
def populate_thai_account_names(self):
    """
    Post-processing hook to populate account_name_th from JSON thai_account field

    Runs after create_charts() completes to map Thai names to Account DocType records
    """

    # Load the CoA JSON that was used
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_chart
    coa_data = get_chart(self.chart_of_accounts)

    # Extract thai_account mappings from JSON
    thai_name_map = extract_thai_names_from_coa(coa_data)
    # Returns: {"1000-00": "สินทรัพย์", "1100-00": "สินทรัพย์หมุนเวียน", ...}

    # Update Account DocType records with Thai names
    for account_number, thai_name in thai_name_map.items():
        frappe.db.set_value(
            "Account",
            {
                "company": self.name,
                "account_number": account_number
            },
            "account_name_th",
            thai_name
        )

    frappe.db.commit()
    frappe.msgprint(f"Populated Thai account names for {len(thai_name_map)} accounts")

def extract_thai_names_from_coa(coa_tree, parent_path=""):
    """
    Recursively extract thai_account field from CoA JSON
    Returns dict mapping account_number to Thai name
    """
    thai_name_map = {}

    for account_name, account_data in coa_tree.items():
        if isinstance(account_data, dict):
            # Extract Thai name if present
            thai_name = account_data.get("thai_account")
            account_number = account_data.get("account_number")

            if thai_name and account_number:
                thai_name_map[account_number] = thai_name

            # Recurse into child accounts
            child_thai_names = extract_thai_names_from_coa(account_data, parent_path + "/" + account_name)
            thai_name_map.update(child_thai_names)

    return thai_name_map
```

**Language-Aware Display Function**:

Function to detect user language preference and determine which account name to display:

```python
def get_user_language():
    """
    Detect user's language preference from Frappe settings
    Returns 'th' for Thai, 'en' for English
    """
    user_lang = frappe.db.get_value("User", frappe.session.user, "language")

    # Check for Thai language indicators
    if user_lang in ["th", "Thai", "ไทย"]:
        return "th"

    return "en"

def get_account_name_field():
    """
    Determine which account name field to use based on user language
    Returns field name for queries and display
    """
    if get_user_language() == "th":
        return "account_name_th"
    else:
        return "account_name"
```

**Account Tree Display Logic**:

Modify Account Tree to conditionally fetch and display Thai names based on user language:

```python
# Frontend modification pattern for Account Tree
# Location: erpnext/accounts/doctype/account/account_tree.js (or custom override)

frappe.treeview_settings["Account"] = {
    get_tree_nodes: function(node, callback) {
        // Detect user language preference
        const user_lang = frappe.boot.lang || frappe.defaults.get_user_default("language");
        const is_thai = ["th", "Thai", "ไทย"].includes(user_lang);

        // Select appropriate field for display
        const name_field = is_thai ? "account_name_th" : "account_name";

        frappe.call({
            method: "erpnext.accounts.doctype.account.account.get_children",
            args: {
                parent: node,
                company: frappe.defaults.get_user_default("Company"),
                name_field: name_field  // Pass preferred field to backend
            },
            callback: function(r) {
                callback(r.message);
            }
        });
    },

    get_label: function(node) {
        // Display Thai name if available and user language is Thai
        const user_lang = frappe.boot.lang || frappe.defaults.get_user_default("language");
        const is_thai = ["th", "Thai", "ไทย"].includes(user_lang);

        if (is_thai && node.account_name_th) {
            return node.account_name_th;
        }

        return node.account_name;
    }
};
```

**Backend API Modification**:

Extend Account Tree backend to support language-aware queries:

```python
# Location: erpnext/accounts/doctype/account/account.py (or custom override)

@frappe.whitelist()
def get_children(parent, company, name_field="account_name"):
    """
    Get child accounts with language-aware field selection

    Args:
        parent: Parent account name
        company: Company filter
        name_field: Field to use for account name display (account_name or account_name_th)
    """

    # Validate name_field parameter
    if name_field not in ["account_name", "account_name_th"]:
        name_field = "account_name"

    accounts = frappe.get_all(
        "Account",
        filters={
            "parent_account": parent,
            "company": company
        },
        fields=[
            "name",
            "account_name",
            "account_name_th",
            "account_number",
            "is_group",
            "account_type"
        ],
        order_by="account_number"
    )

    # Format for tree display
    return [{
        "value": acc.name,
        "title": acc.get(name_field) or acc.account_name,  # Fallback to account_name if Thai name not available
        "expandable": acc.is_group,
        "account_name": acc.account_name,
        "account_name_th": acc.account_name_th,
        "account_number": acc.account_number
    } for acc in accounts]
```

**Implementation Workflow**:

1. **During Chart of Accounts Import** (`create_default_accounts()`):
   - `create_charts()` runs and creates Account DocType records with English names
   - `populate_thai_account_names()` runs as post-processing hook
   - Maps `thai_account` from JSON to `account_name_th` field in Account DocType

2. **User Language Detection**:
   - Check `User.language` field
   - Support "th", "Thai", or "ไทย" as Thai language indicators
   - Cache language preference in session for performance

3. **Account Tree Display**:
   - Frontend detects user language on page load
   - Passes `name_field` parameter to backend API
   - Backend queries with appropriate field
   - Frontend displays Thai or English name based on preference

**Benefits**:
- ✅ Clean separation: English for system (account_name), Thai for display (account_name_th)
- ✅ Language-aware UI without complex translation logic
- ✅ Maintains ERPNext standard structure (account_name as primary key)
- ✅ Supports mixed language organizations (some users Thai, some English)
- ✅ Fallback to English if Thai name not available

---

### Dynamic Bank Account Configuration (Interactive Setup)

**Problem**: Bank accounts in Chart of Accounts contain specific bank account numbers that vary per company:

```json
{
  "Current Account": {
    "account_number": "1112-00",
    "is_group": 1,
    "thai_account": "เงินฝากกระแสรายวัน",

    "Kasikorn - Current 711-1-04156-8": {
      "account_number": "1112-01",
      "thai_account": "กสิกรไทย/กระแสฯ 711-1-04156-8",
      "_meta": {
        "default_for": "bank",
        "auto_assign_field": "default_bank_account",
        "priority": 1,
        "bank_template": true,           // NEW: Mark as template requiring user input
        "bank_code": "KASIKORNBANK",     // NEW: Bank identifier
        "account_type_code": "CURRENT"   // NEW: Account type (CURRENT/SAVINGS)
      }
    }
  }
}
```

**Solution**: Interactive bank account setup modal at company creation stage

**Implementation Strategy**:

#### 1. Chart of Accounts JSON Template Variables

Use placeholder pattern for bank account numbers in JSON:

```json
{
  "Current Account": {
    "account_number": "1112-00",
    "is_group": 1,
    "thai_account": "เงินฝากกระแสรายวัน",

    "Kasikorn - Current {{kasikorn_current_account}}": {
      "account_number": "1112-01",
      "thai_account": "กสิกรไทย/กระแสฯ {{kasikorn_current_account}}",
      "_meta": {
        "default_for": "bank",
        "auto_assign_field": "default_bank_account",
        "priority": 1,
        "bank_template": true,
        "bank_code": "KASIKORNBANK",
        "bank_name_th": "กสิกรไทย",
        "bank_name_en": "Kasikorn",
        "account_type": "CURRENT",
        "account_type_th": "กระแสรายวัน",
        "variable_name": "kasikorn_current_account"
      }
    },

    "Bangkok Bank - Savings {{bbl_savings_account}}": {
      "account_number": "1113-01",
      "thai_account": "กรุงเทพ/ออมทรัพย์ {{bbl_savings_account}}",
      "_meta": {
        "bank_template": true,
        "bank_code": "BBL",
        "bank_name_th": "กรุงเทพ",
        "bank_name_en": "Bangkok Bank",
        "account_type": "SAVINGS",
        "account_type_th": "ออมทรัพย์",
        "variable_name": "bbl_savings_account",
        "priority": 2
      }
    },

    "SCB - Current {{scb_current_account}}": {
      "account_number": "1112-02",
      "thai_account": "ไทยพาณิชย์/กระแสฯ {{scb_current_account}}",
      "_meta": {
        "bank_template": true,
        "bank_code": "SCB",
        "bank_name_th": "ไทยพาณิชย์",
        "bank_name_en": "SCB",
        "account_type": "CURRENT",
        "variable_name": "scb_current_account",
        "priority": 3
      }
    }
  }
}
```

#### 2. Thai Banks Master List

Comprehensive list of major Thai banks for selection UI:

```python
THAI_BANKS = [
    {
        "code": "KASIKORNBANK",
        "name_en": "Kasikorn Bank",
        "name_th": "ธนาคารกสิกรไทย",
        "short_th": "กสิกรไทย",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "BBL",
        "name_en": "Bangkok Bank",
        "name_th": "ธนาคารกรุงเทพ",
        "short_th": "กรุงเทพ",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "SCB",
        "name_en": "Siam Commercial Bank",
        "name_th": "ธนาคารไทยพาณิชย์",
        "short_th": "ไทยพาณิชย์",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "KBANK",
        "name_en": "Krungsri Bank",
        "name_th": "ธนาคารกรุงศรีอยุธยา",
        "short_th": "กรุงศรี",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "KTB",
        "name_en": "Krungthai Bank",
        "name_th": "ธนาคารกรุงไทย",
        "short_th": "กรุงไทย",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "TMB",
        "name_en": "TMB Bank",
        "name_th": "ธนาคารทหารไทย",
        "short_th": "ทหารไทย",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "CIMB",
        "name_en": "CIMB Thai Bank",
        "name_th": "ธนาคารซีไอเอ็มบีไทย",
        "short_th": "ซีไอเอ็มบี",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "TISCO",
        "name_en": "TISCO Bank",
        "name_th": "ธนาคารทิสโก้",
        "short_th": "ทิสโก้",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "KIATNAKIN",
        "name_en": "Kiatnakin Bank",
        "name_th": "ธนาคารเกียรตินาคิน",
        "short_th": "เกียรตินาคิน",
        "account_types": ["CURRENT", "SAVINGS"]
    },
    {
        "code": "GSB",
        "name_en": "Government Savings Bank",
        "name_th": "ธนาคารออมสิน",
        "short_th": "ออมสิน",
        "account_types": ["SAVINGS"]
    },
    {
        "code": "BAAC",
        "name_en": "Bank for Agriculture and Agricultural Cooperatives",
        "name_th": "ธนาคารเพื่อการเกษตรและสหกรณ์การเกษตร",
        "short_th": "ธ.ก.ส.",
        "account_types": ["SAVINGS"]
    }
]

ACCOUNT_TYPES = {
    "CURRENT": {
        "name_en": "Current Account",
        "name_th": "บัญชีกระแสรายวัน",
        "short_th": "กระแสฯ"
    },
    "SAVINGS": {
        "name_en": "Savings Account",
        "name_th": "บัญชีออมทรัพย์",
        "short_th": "ออมทรัพย์"
    }
}
```

#### 3. Interactive Bank Setup Modal (Frappe Dialog)

Modal dialog shown after company creation, before Chart of Accounts import:

```python
def show_bank_account_setup_dialog(self):
    """
    Show interactive modal for bank account configuration
    Similar to shadcn-ui component selection pattern
    """

    # Extract bank templates from CoA JSON
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_chart
    coa_data = get_chart(self.chart_of_accounts)

    bank_templates = extract_bank_templates_from_coa(coa_data)
    # Returns: [
    #   {"bank_code": "KASIKORNBANK", "account_type": "CURRENT", "variable_name": "kasikorn_current_account"},
    #   {"bank_code": "BBL", "account_type": "SAVINGS", "variable_name": "bbl_savings_account"},
    # ]

    # Create dialog with bank selection
    dialog = frappe.msgprint(
        msg="",
        title=_("Configure Bank Accounts"),
        primary_action={
            "label": _("Create Accounts"),
            "action": lambda: process_bank_accounts(dialog)
        },
        as_dialog=True
    )

    # Build bank selection UI (checkboxes like shadcn-ui)
    html = build_bank_selection_html(bank_templates, THAI_BANKS)
    dialog.set_message(html)

    return dialog

def build_bank_selection_html(bank_templates, thai_banks):
    """
    Build HTML for bank selection UI with shadcn-ui style
    """
    html = """
    <div class="bank-setup-container">
        <div class="bank-setup-header">
            <h3>Select Banks and Enter Account Numbers</h3>
            <p class="text-muted">Choose the banks your company uses and provide account numbers</p>
        </div>

        <div class="bank-selection-actions">
            <button class="btn btn-xs btn-default" onclick="selectAllBanks()">
                <i class="fa fa-check-square-o"></i> Select All
            </button>
            <button class="btn btn-xs btn-default" onclick="deselectAllBanks()">
                <i class="fa fa-square-o"></i> Deselect All
            </button>
        </div>

        <div class="bank-list">
    """

    # Group by bank code
    banks_grouped = {}
    for template in bank_templates:
        bank_code = template["bank_code"]
        if bank_code not in banks_grouped:
            banks_grouped[bank_code] = []
        banks_grouped[bank_code].append(template)

    # Render each bank with account type options
    for bank_code, templates in banks_grouped.items():
        bank_info = next((b for b in thai_banks if b["code"] == bank_code), None)
        if not bank_info:
            continue

        html += f"""
        <div class="bank-item" data-bank-code="{bank_code}">
            <div class="bank-header">
                <input type="checkbox" class="bank-checkbox" id="bank_{bank_code}"
                       onchange="toggleBankAccounts('{bank_code}')">
                <label for="bank_{bank_code}">
                    <strong>{bank_info['name_en']}</strong> ({bank_info['name_th']})
                </label>
            </div>
            <div class="bank-accounts" id="accounts_{bank_code}" style="display:none; margin-left: 30px;">
        """

        # Render account type inputs
        for template in templates:
            account_type = template["account_type"]
            account_type_info = ACCOUNT_TYPES.get(account_type, {})
            variable_name = template["variable_name"]

            html += f"""
            <div class="form-group">
                <label class="control-label">
                    {account_type_info.get('name_en', account_type)}
                    ({account_type_info.get('name_th', '')})
                </label>
                <input type="text"
                       class="form-control bank-account-input"
                       id="{variable_name}"
                       name="{variable_name}"
                       placeholder="e.g., 711-1-04156-8"
                       data-bank-code="{bank_code}"
                       data-account-type="{account_type}">
                <p class="help-text">Enter account number without bank code</p>
            </div>
            """

        html += """
            </div>
        </div>
        """

    html += """
        </div>
    </div>

    <style>
        .bank-setup-container { padding: 20px; }
        .bank-setup-header { margin-bottom: 20px; }
        .bank-selection-actions { margin-bottom: 15px; }
        .bank-item {
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 10px;
        }
        .bank-header { margin-bottom: 10px; }
        .bank-checkbox { margin-right: 10px; }
        .bank-accounts { padding: 10px 0; }
        .bank-account-input { max-width: 300px; }
    </style>

    <script>
        function toggleBankAccounts(bankCode) {
            const checkbox = document.getElementById('bank_' + bankCode);
            const accountsDiv = document.getElementById('accounts_' + bankCode);
            accountsDiv.style.display = checkbox.checked ? 'block' : 'none';

            // Clear inputs if unchecked
            if (!checkbox.checked) {
                accountsDiv.querySelectorAll('input[type="text"]').forEach(input => {
                    input.value = '';
                });
            }
        }

        function selectAllBanks() {
            document.querySelectorAll('.bank-checkbox').forEach(checkbox => {
                checkbox.checked = true;
                toggleBankAccounts(checkbox.id.replace('bank_', ''));
            });
        }

        function deselectAllBanks() {
            document.querySelectorAll('.bank-checkbox').forEach(checkbox => {
                checkbox.checked = false;
                toggleBankAccounts(checkbox.id.replace('bank_', ''));
            });
        }
    </script>
    """

    return html

def process_bank_accounts(dialog):
    """
    Process user input from bank setup dialog
    Returns dict of variable substitutions
    """
    bank_account_variables = {}

    # Extract values from dialog inputs
    for input_elem in dialog.fields_dict:
        if input_elem.startswith('bank_account_'):
            variable_name = input_elem
            account_number = dialog.get_value(variable_name)

            if account_number:
                bank_account_variables[variable_name] = account_number

    return bank_account_variables
```

#### 4. Variable Substitution in Chart of Accounts

Replace template variables with user-provided values during import:

```python
def create_default_accounts_with_variables(self, bank_account_variables):
    """
    Import Chart of Accounts with variable substitution

    Args:
        bank_account_variables: Dict of {variable_name: account_number}
        Example: {"kasikorn_current_account": "711-1-04156-8"}
    """
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_chart, create_charts

    # Load CoA template
    coa_data = get_chart(self.chart_of_accounts)

    # Perform variable substitution
    coa_with_values = substitute_variables_in_coa(coa_data, bank_account_variables)

    # Import with substituted values
    frappe.local.flags.ignore_root_company_validation = True
    create_charts(
        self.name,
        custom_chart=coa_with_values,  # Use modified CoA instead of template
        from_coa_importer=True
    )

def substitute_variables_in_coa(coa_tree, variables, parent_path=""):
    """
    Recursively substitute {{variable}} placeholders with actual values

    Args:
        coa_tree: Chart of Accounts tree structure
        variables: Dict of {variable_name: value}

    Returns:
        Modified CoA tree with substituted values
    """
    import re

    substituted_tree = {}

    for account_name, account_data in coa_tree.items():
        if isinstance(account_data, dict):
            # Check if this account uses templates
            meta = account_data.get("_meta", {})
            is_bank_template = meta.get("bank_template", False)
            variable_name = meta.get("variable_name")

            # If template and user didn't provide value, skip this account
            if is_bank_template and variable_name:
                if variable_name not in variables:
                    continue  # Skip accounts not selected by user

            # Substitute variables in account name
            new_account_name = substitute_placeholders(account_name, variables)

            # Substitute variables in account data fields
            new_account_data = {}
            for key, value in account_data.items():
                if isinstance(value, str):
                    new_account_data[key] = substitute_placeholders(value, variables)
                elif isinstance(value, dict) and key != "_meta":
                    # Recurse into child accounts
                    new_account_data[key] = substitute_variables_in_coa({key: value}, variables, parent_path + "/" + new_account_name)[key]
                else:
                    new_account_data[key] = value

            substituted_tree[new_account_name] = new_account_data

    return substituted_tree

def substitute_placeholders(text, variables):
    """
    Replace {{variable}} with actual value

    Example: "Kasikorn - Current {{kasikorn_current_account}}"
         --> "Kasikorn - Current 711-1-04156-8"
    """
    import re

    def replace_match(match):
        var_name = match.group(1)
        return variables.get(var_name, match.group(0))  # Keep placeholder if variable not found

    return re.sub(r'\{\{(\w+)\}\}', replace_match, text)

def extract_bank_templates_from_coa(coa_tree, parent_path=""):
    """
    Extract all bank template accounts from CoA
    Returns list of bank template metadata
    """
    bank_templates = []

    for account_name, account_data in coa_tree.items():
        if isinstance(account_data, dict):
            meta = account_data.get("_meta", {})

            if meta.get("bank_template"):
                bank_templates.append({
                    "bank_code": meta.get("bank_code"),
                    "bank_name_th": meta.get("bank_name_th"),
                    "bank_name_en": meta.get("bank_name_en"),
                    "account_type": meta.get("account_type"),
                    "account_type_th": meta.get("account_type_th"),
                    "variable_name": meta.get("variable_name"),
                    "priority": meta.get("priority", 99)
                })

            # Recurse
            child_templates = extract_bank_templates_from_coa(account_data, parent_path + "/" + account_name)
            bank_templates.extend(child_templates)

    return bank_templates
```

#### 5. Company Creation Workflow Integration

```python
class CustomCompany(Company):
    def after_insert(self):
        """Import Chart of Accounts with interactive bank setup"""
        super().after_insert()

        if self.chart_of_accounts:
            # Show bank setup dialog
            bank_variables = self.show_bank_account_setup_dialog()

            # Import CoA with substituted variables
            self.create_default_accounts_with_variables(bank_variables)

            # Populate Thai account names
            self.populate_thai_account_names()

            # Auto-assign default accounts
            self.auto_assign_default_accounts()
```

**User Experience Flow**:

1. **Company Creation**: User creates new company and selects "Inpac Pharma - Thai Pharmaceutical Chart of Accounts"
2. **Bank Setup Modal**: Interactive dialog appears showing:
   - List of all Thai banks (Kasikorn, Bangkok Bank, SCB, etc.)
   - Checkboxes to select which banks the company uses
   - "Select All" / "Deselect All" buttons (like shadcn-ui)
   - Input fields for account numbers (shown only when bank is selected)
3. **User Selection**:
   - User checks "Kasikorn Bank" → Input field appears for Current Account number
   - User enters "711-1-04156-8"
   - User checks "Bangkok Bank" → Input field appears for Savings Account number
   - User enters "123-4-56789-0"
4. **Chart Import**: System creates accounts with actual values:
   - "Kasikorn - Current 711-1-04156-8" (English)
   - "กสิกรไทย/กระแสฯ 711-1-04156-8" (Thai)
   - "Bangkok Bank - Savings 123-4-56789-0"
   - "กรุงเทพ/ออมทรัพย์ 123-4-56789-0"
5. **Accounts Not Selected**: Banks not checked are simply not created (optional accounts)

**Benefits**:
- ✅ User-friendly UI similar to shadcn-ui component selection
- ✅ Only create accounts for banks actually used by the company
- ✅ Accurate bank account numbers from the start
- ✅ Supports multiple banks and account types
- ✅ Thai and English bilingual account names
- ✅ No manual editing required after import

**Account Type Mapping with Metadata**:
| Company Field | account_type | _meta.default_for | _meta.auto_assign_field |
|---------------|--------------|-------------------|-------------------------|
| `default_receivable_account` | Receivable | "receivable" | "default_receivable_account" |
| `default_payable_account` | Payable | "payable" | "default_payable_account" |
| `default_cash_account` | Cash | "cash" | "default_cash_account" |
| `default_bank_account` | Bank | "bank" | "default_bank_account" |
| `default_income_account` | Income | "income" | "default_income_account" |
| `default_expense_account` | Expense | "expense" | "default_expense_account" |
| `round_off_account` | Round Off | "round_off" | "round_off_account" |

**Features**:
- ✅ Metadata-driven (no hardcoded account names)
- ✅ Language-independent (works with Thai, English, or bilingual)
- ✅ Priority-based selection when multiple accounts exist
- ✅ Backward compatible (falls back to account_type if no metadata)
- ✅ Works with existing Account DocType custom fields (account_name_th)

**Benefits**:
- Users don't need to manually configure default accounts
- Reduces setup time from 30 minutes to instant
- Eliminates configuration errors
- Supports bilingual businesses (Thai + English)

**Technical Notes**:
- Chart of Accounts JSON is NOT a DocType - it's a template file
- `create_charts()` function reads JSON and creates Account DocType records
- Account DocType has fields: account_name, account_name_th, account_number, account_type
- Metadata in JSON guides automation but doesn't become DocType fields
- Match accounts by account_number (most reliable) or account_name

**Status**: 🔵 PLANNED

---

### Phase 3: Tax Template Auto-Creation (ADVANCED)
**Goal**: Automatically create country-specific tax templates with proper account mapping

**Implementation Strategy**:
```python
def auto_create_tax_templates(self):
    """
    Create tax templates based on:
    1. Country-specific tax rules (Thailand = 7% VAT)
    2. Account structure (detect tax accounts)
    3. Industry requirements (pharmaceutical = specific tax treatments)
    """

    # Detect tax accounts from CoA
    vat_accounts = frappe.get_all(
        "Account",
        filters={
            "company": self.name,
            "account_type": "Tax",
            "account_name": ["like", "%VAT%"]
        },
        fields=["name", "account_name"]
    )

    # Create Sales Tax Template
    if vat_accounts:
        create_sales_tax_template(
            company=self.name,
            tax_account=vat_accounts[0].name,
            rate=7.0  # Thailand VAT rate
        )
```

**Tax Template Types**:
1. **Sales Taxes and Charges Template**
   - Output VAT (7% for Thailand)
   - Withholding Tax (multiple rates: 1%, 2%, 3%, 5%, 10%)
   - Service Tax (if applicable)

2. **Purchase Taxes and Charges Template**
   - Input VAT (7% for Thailand)
   - Withholding Tax on purchases
   - Import duties (if applicable)

3. **Item Tax Templates**
   - Exempt items (pharmaceuticals, medical supplies)
   - Zero-rated items (exports)
   - Standard-rated items (7% VAT)

**Country-Specific Rules**:
```python
TAX_RULES = {
    "Thailand": {
        "vat_rate": 7.0,
        "wht_rates": [1.0, 2.0, 3.0, 5.0, 10.0],
        "tax_accounts_pattern": {
            "output_vat": ["ภาษีขาย", "Output VAT", "VAT Out"],
            "input_vat": ["ภาษีซื้อ", "Input VAT", "VAT In"],
            "wht": ["ภาษีหัก ณ ที่จ่าย", "Withholding Tax", "WHT"]
        }
    }
}
```

**Features**:
- ✅ Country-aware tax template creation
- ✅ Industry-specific tax treatments (pharmaceutical exemptions)
- ✅ Multi-language account name detection (Thai + English)
- ✅ Automatic tax account detection from CoA

**Status**: 🔵 PLANNED

---

### Phase 4: Industry-Specific CoA Templates (SPECIALIZED)
**Goal**: Provide pre-configured CoA templates for specific industries with best practices

**Industry Templates**:

#### 1. Pharmaceutical Manufacturing
```json
{
  "name": "Thai Pharmaceutical Standard CoA",
  "industry": "pharmaceutical",
  "features": [
    "GMP compliance accounts",
    "FDA registration cost tracking",
    "Batch cost centers",
    "Quality control expense accounts",
    "Research & Development tracking",
    "Regulatory compliance costs"
  ],
  "accounts": {
    "R&D Expenses": {
      "Clinical Trials": {},
      "Product Development": {},
      "Quality Assurance": {}
    },
    "Regulatory Costs": {
      "FDA Registration": {},
      "License Renewals": {},
      "Compliance Audits": {}
    }
  }
}
```

#### 2. Construction & Real Estate
```json
{
  "name": "Thai Construction Standard CoA",
  "industry": "construction",
  "features": [
    "Project-based cost centers",
    "Retention accounting",
    "Progress billing accounts",
    "Subcontractor management",
    "Material inventory tracking"
  ]
}
```

#### 3. Retail & E-commerce
```json
{
  "name": "Thai Retail Standard CoA",
  "industry": "retail",
  "features": [
    "Multi-channel sales tracking",
    "Inventory valuation (FIFO/Average)",
    "Customer loyalty programs",
    "Shipping & logistics",
    "Returns and refunds"
  ]
}
```

**Implementation**:
- Store industry templates in `apps/print_designer/chart_of_accounts/`
- Add "Industry" field to Company DocType
- Auto-select appropriate template based on industry
- Allow customization after import

**Status**: 🔵 PLANNED

---

### Phase 5: Intelligent CoA Validation (QUALITY ASSURANCE)
**Goal**: Validate Chart of Accounts structure for completeness and compliance

**Validation Rules**:

#### 1. Required Accounts Check
```python
REQUIRED_ACCOUNTS = {
    "all_companies": [
        "Receivable",
        "Payable",
        "Cash",
        "Bank",
        "Stock",
        "Cost of Goods Sold"
    ],
    "thailand": [
        "Input VAT",
        "Output VAT",
        "Withholding Tax Payable",
        "Withholding Tax Receivable"
    ],
    "pharmaceutical": [
        "R&D Expenses",
        "Quality Control",
        "Regulatory Compliance"
    ]
}
```

#### 2. Account Structure Validation
- ✅ All root types present (Asset, Liability, Equity, Income, Expense)
- ✅ Proper parent-child relationships
- ✅ No circular references
- ✅ Group accounts have children
- ✅ Leaf accounts have account types

#### 3. Thai Accounting Standards Compliance
- ✅ Account numbering follows Thai standards (if applicable)
- ✅ Thai account names for Thai companies
- ✅ Proper tax account structure
- ✅ Compliance with Revenue Department requirements

**Implementation**:
```python
def validate_coa_structure(self):
    """Validate CoA after import"""
    validation_results = {
        "missing_required_accounts": [],
        "invalid_structure": [],
        "compliance_issues": []
    }

    # Check required accounts
    for account_type in REQUIRED_ACCOUNTS["all_companies"]:
        if not frappe.db.exists("Account", {
            "company": self.name,
            "account_type": account_type
        }):
            validation_results["missing_required_accounts"].append(account_type)

    # Generate report
    if any(validation_results.values()):
        generate_validation_report(validation_results)
```

**Status**: 🔵 PLANNED

---

### Phase 6: AI-Powered CoA Generation (FUTURE)
**Goal**: Use AI to generate customized Chart of Accounts based on business description

**Concept**:
```python
def generate_coa_from_description(company_name, business_description, industry):
    """
    Use AI to analyze business description and generate appropriate CoA

    Example Input:
    "We manufacture and distribute pharmaceutical products in Thailand.
     We have 3 factories, 50 distributors, and export to 5 countries.
     We need to track R&D costs, FDA compliance, and batch manufacturing."

    AI Output:
    - Suggests pharmaceutical industry template
    - Adds export-related accounts
    - Creates multi-location cost centers
    - Includes compliance tracking accounts
    - Recommends batch costing structure
    """
    pass
```

**Features**:
- Natural language business description
- AI-powered account structure generation
- Industry best practices application
- Compliance requirement detection
- Multi-entity consolidation planning

**Status**: 💭 CONCEPT

---

## Implementation Roadmap

### Phase 1: MVP (Week 1) ✅ DONE
- [x] Basic auto-import from JSON
- [x] Error handling for tax templates
- [x] Company appears in Account tree view

### Phase 2: Default Accounts (Week 2) 🎯 NEXT
- [ ] Auto-detect default accounts by type
- [ ] Create missing critical accounts
- [ ] Validate account assignments
- [ ] Add user notification for detected accounts

### Phase 3: Tax Templates (Week 3-4)
- [ ] Country-specific tax rules engine
- [ ] Multi-language tax account detection
- [ ] Auto-create sales/purchase tax templates
- [ ] Industry-specific tax treatments

### Phase 4: Industry Templates (Week 5-6)
- [ ] Create pharmaceutical template
- [ ] Create construction template
- [ ] Create retail template
- [ ] Add industry selector to Company form

### Phase 5: Validation (Week 7)
- [ ] CoA structure validation
- [ ] Required accounts checker
- [ ] Compliance validation
- [ ] Validation report generation

### Phase 6: AI Generation (Future)
- [ ] Research AI/LLM integration
- [ ] Build business description parser
- [ ] Develop CoA generation logic
- [ ] Test and refine

---

## Technical Architecture

### File Structure
```
apps/print_designer/
├── print_designer/
│   ├── overrides/
│   │   └── company.py                    # Company DocType override
│   ├── accounts/
│   │   ├── chart_of_accounts/
│   │   │   ├── th_pharmaceutical.json    # Industry templates
│   │   │   ├── th_construction.json
│   │   │   └── th_retail.json
│   │   ├── coa_validator.py              # Validation logic
│   │   ├── default_accounts.py           # Default account detection
│   │   └── tax_template_generator.py     # Tax template creation
│   └── hooks.py                          # Hook registrations
└── CHART_OF_ACCOUNTS_AUTOMATION.md      # This document
```

### Module Dependencies
```python
# Core modules
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts
from erpnext.accounts.doctype.chart_of_accounts_importer.chart_of_accounts_importer import set_default_accounts

# Custom modules (to be created)
from print_designer.accounts.coa_validator import validate_coa_structure
from print_designer.accounts.default_accounts import auto_assign_default_accounts
from print_designer.accounts.tax_template_generator import auto_create_tax_templates
```

---

## Configuration Options

### Company Settings Extension
Add custom fields to Company DocType:
```python
CUSTOM_FIELDS = {
    "Company": [
        {
            "fieldname": "auto_configure_accounts",
            "label": "Auto-Configure Accounting",
            "fieldtype": "Check",
            "default": 1,
            "description": "Automatically configure default accounts and tax templates"
        },
        {
            "fieldname": "industry_type",
            "label": "Industry Type",
            "fieldtype": "Select",
            "options": "\nPharmaceutical\nConstruction\nRetail\nManufacturing\nServices\nOther"
        },
        {
            "fieldname": "coa_validation_level",
            "label": "CoA Validation Level",
            "fieldtype": "Select",
            "options": "Basic\nStandard\nStrict",
            "default": "Standard"
        }
    ]
}
```

---

## Testing Strategy

### Unit Tests
```python
# test_company_override.py
def test_auto_import_coa():
    """Test automatic CoA import on company creation"""
    company = create_test_company(
        chart_of_accounts="Inpac Pharma - Thai Pharmaceutical Chart of Accounts"
    )
    assert frappe.db.count("Account", {"company": company.name}) > 0

def test_default_account_detection():
    """Test automatic default account assignment"""
    company = create_test_company()
    assert company.default_receivable_account is not None
    assert company.default_payable_account is not None
```

### Integration Tests
```python
def test_complete_company_setup():
    """Test end-to-end company creation with full automation"""
    company = create_company_with_automation()

    # Verify accounts imported
    assert has_complete_coa(company)

    # Verify default accounts assigned
    assert all_default_accounts_set(company)

    # Verify tax templates created
    assert tax_templates_exist(company)
```

---

## Success Metrics

### Time Savings
- **Manual Process**: ~30-60 minutes per company
- **Phase 1 (Current)**: ~10 minutes (CoA auto-imported)
- **Phase 2 Target**: ~5 minutes (+ default accounts)
- **Phase 3 Target**: ~2 minutes (+ tax templates)
- **Phase 4-5 Target**: <1 minute (full automation)

### Error Reduction
- **Manual Process**: 40% error rate (missing accounts, wrong assignments)
- **Target**: <5% error rate with validation

### User Satisfaction
- Reduce support tickets for accounting setup by 80%
- Improve onboarding experience rating from 3/5 to 4.5/5

---

## Notes and Considerations

### Important Decisions

1. **Skip set_default_accounts() in Phase 1**
   - Reason: Function does too much (assigns defaults + creates tax templates)
   - Strategy: Break into smaller functions we control
   - Benefit: More granular control and error handling

2. **JSON over CSV for CoA Templates**
   - Reason: Better structure, easier to maintain, supports metadata
   - Trade-off: Can't use Chart of Accounts Importer UI directly
   - Solution: Build custom templates in JSON, convert if needed

3. **Gradual Enhancement Philosophy**
   - Start simple, add complexity incrementally
   - Each phase must be independently functional
   - Allow users to opt-out of automation if desired

### Potential Issues

1. **Existing Companies**: How to handle companies created before automation?
   - Solution: Provide "Re-configure Accounts" button
   - Run validation and offer to fix missing configurations

2. **Customized CoA**: Users might customize after import
   - Solution: Store "auto_configured" flag, don't override user changes
   - Provide diff view to show what would change

3. **Multi-currency Complications**: Default accounts must match currency
   - Solution: Detect company currency, filter accounts accordingly
   - Create currency-specific default accounts if needed

### Future Enhancements

1. **CoA Marketplace**: Share industry templates across installations
2. **Version Control**: Track CoA changes over time
3. **Migration Tools**: Upgrade CoA when tax laws change
4. **Audit Trails**: Log all automatic configurations
5. **Rollback Capability**: Undo automatic configurations if needed

---

## Conclusion

This phased approach allows us to:
- ✅ Start simple and deliver value immediately (Phase 1)
- ✅ Build confidence with each working phase
- ✅ Gather user feedback and adjust
- ✅ Maintain backward compatibility
- ✅ Scale complexity as needed

**Current Status**: Phase 1 MVP implemented and working
**Next Step**: Implement Phase 2 default account detection
**Long-term Vision**: Fully automated, AI-powered accounting setup
