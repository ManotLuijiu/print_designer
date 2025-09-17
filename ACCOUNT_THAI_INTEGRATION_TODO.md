# Account Thai Integration - TODO List

## ✅ Completed Features (2025-01-17)

### 1. Database Integration
- Added `account_name_th` field to Account DocType
- Created translation glossaries (88 accounts translated)
- Implemented migration hook for automatic translation application
- Successfully translated all accounts including "Debtors" → "ลูกหนี้"

### 2. API Enhancement (Option 1 Implementation)
- Enhanced `account_api.py` with ERPNext-style methods
- Automatic Thai name inclusion in data fetching
- Bilingual display names (e.g., "Cash | เงินสด")
- Full backward compatibility maintained

### 3. External Data Sources
- Created HFO account glossary from Thai Ministry of Public Health
- Extracted Thai university accounts from Excel file
- Built comprehensive translation dictionaries

## 📝 TODO - User Language Preference Toggle

### Feature: Dynamic Language Display Based on User Preference
**Priority**: High
**Target**: Next development session

#### Requirements:
1. **User Preference Detection**
   - Read user's preferred language from `frappe.session.data.lang`
   - Support languages: `en` (English), `th` (Thai), `bilingual` (Both)

2. **Dynamic Field Selection**
   ```python
   def get_account_display_name(account, user_lang=None):
       """Return account name based on user language preference"""
       if not user_lang:
           user_lang = frappe.session.data.get('lang', 'en')

       if user_lang == 'th' and account.get('account_name_th'):
           return account.account_name_th
       elif user_lang == 'bilingual' and account.get('account_name_th'):
           return f"{account.account_name} | {account.account_name_th}"
       else:
           return account.account_name
   ```

3. **API Method Enhancement**
   - Add `lang` parameter to all API methods
   - Auto-detect from user session if not provided
   - Return appropriate display format based on preference

4. **Implementation Areas**
   - `get_accounts_enhanced()` - Add language toggle
   - `get_account_list_for_reports()` - Dynamic display name
   - `get_account_with_thai_for_erpnext()` - Language-aware response
   - New utility: `format_account_by_language()`

5. **UI Integration**
   - Link field display should respect language preference
   - Report columns should show appropriate language
   - Dropdown options should display based on user setting

#### Proposed API Changes:
```python
@frappe.whitelist()
def get_accounts_enhanced(company=None, lang=None, filters=None):
    """
    Enhanced account fetching with language preference support

    Args:
        lang (str): Language preference - 'en', 'th', 'bilingual', or None for auto-detect
    """
    if not lang:
        lang = frappe.session.data.get('lang', 'en')

    # ... existing logic ...

    # Format display based on language
    for account in accounts:
        account["display_name"] = get_account_display_name(account, lang)
```

#### Benefits:
- Users see account names in their preferred language
- No UI changes needed - automatic based on user settings
- Maintains all existing functionality
- Clean separation of display logic

## 🔮 Future Enhancements (Optional)

1. **Smart Language Detection**
   - Auto-detect based on browser language
   - Company-level default language settings
   - Role-based language preferences

2. **Extended Translation Support**
   - Account descriptions in Thai
   - Report headers and labels
   - Email templates with bilingual content

3. **Translation Management UI**
   - Web interface for managing translations
   - Bulk import/export functionality
   - Translation verification workflow

## 📚 Reference Files

- **Main API**: `/apps/print_designer/print_designer/api/account_api.py`
- **Glossary**: `/apps/print_designer/print_designer/utils/account_glossary.py`
- **HFO Glossary**: `/apps/print_designer/print_designer/utils/hfo_account_glossary.py`
- **Thai Glossary**: `/apps/print_designer/print_designer/utils/thai_account_glossary.py`
- **Apply Command**: `/apps/print_designer/print_designer/commands/apply_account_thai_translations.py`

## 📅 Session Summary

**Date**: 2025-01-17
**Completed**: Thai account name integration with ERPNext ecosystem
**Next Session**: Implement user language preference toggle system

---

*Note: The current implementation works perfectly with all 88 accounts having Thai translations. The language preference feature will make it even more user-friendly by automatically displaying the appropriate language based on user settings.*