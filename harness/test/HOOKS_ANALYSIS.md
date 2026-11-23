# Print Designer hooks.py Analysis & Compliance Report

Based on `Documentation/rules.md` requirements, here are the issues found:

## 🚨 Critical Issues Found

### 1. Custom Field Naming Convention Violations
**Rule**: Print Designer should use `pd_custom_` prefix for all custom fields

**❌ Fields Missing pd_custom_ Prefix:**
```
Sales Invoice:
- subject_to_wht → pd_custom_subject_to_wht  
- wht_income_type → pd_custom_wht_income_type
- net_total_after_wht → pd_custom_net_total_after_wht
- watermark_text → pd_custom_watermark_text
- prepared_by_signature → pd_custom_prepared_by_signature
- approved_by_signature → pd_custom_approved_by_signature

Quotation:
- subject_to_wht → pd_custom_subject_to_wht
- wht_income_type → pd_custom_wht_income_type  
- net_total_after_wht → pd_custom_net_total_after_wht
- watermark_text → pd_custom_watermark_text
- prepared_by_signature → pd_custom_prepared_by_signature

Sales Order:
- subject_to_wht → pd_custom_subject_to_wht
- wht_income_type → pd_custom_wht_income_type
- net_total_after_wht → pd_custom_net_total_after_wht  
- watermark_text → pd_custom_watermark_text
- prepared_by_signature → pd_custom_prepared_by_signature
- approved_by_signature → pd_custom_approved_by_signature

Customer:
- subject_to_wht → pd_custom_subject_to_wht
- wht_income_type → pd_custom_wht_income_type
- custom_wht_rate → pd_custom_wht_rate (already has custom_ but wrong app prefix)
- is_juristic_person → pd_custom_is_juristic_person

Company: (Many fields missing pd_custom_ prefix)
- authorized_signature_1 → pd_custom_authorized_signature_1
- authorized_signature_2 → pd_custom_authorized_signature_2
- ceo_signature → pd_custom_ceo_signature
- company_stamp_1 → pd_custom_company_stamp_1
- company_stamp_2 → pd_custom_company_stamp_2
- official_seal → pd_custom_official_seal
- thailand_service_business → pd_custom_thailand_service_business
- default_wht_account → pd_custom_default_wht_account
- construction_service → pd_custom_construction_service
... (and many more Company fields)
```

**✅ Fields Already Compliant:**
- All `custom_*` retention fields (but should be `pd_custom_*` for proper app isolation)

### 2. Redundancy in hooks.py

**❌ Duplicate/Redundant Entries:**
```python
# Line 427: Legacy function (should be removed)
"print_designer.install.after_app_install",  # Legacy function - kept for compatibility

# Lines 447-450: Duplicate boot session hooks
boot_session = "print_designer.utils.signature_stamp.boot_session"
extend_bootinfo = "print_designer.utils.signature_stamp.boot_session"  # Same function!

# Lines 522-527: Dead code and active code mixed
# "Print Format": {  # Commented out - should be cleaned
# },
"Print Format": {  # Active version
    "before_save": "...",
    "on_update": "..."
},
```

**❌ Commented Dead Code:**
- Lines 514-516: Commented Global Defaults
- Lines 522-524: Commented Print Format event
- Multiple commented includes in app_include_css
- Multiple commented hooks throughout

### 3. Missing Uninstall Functionality

**❌ Issue**: Rule states "All custom fields that created by particular custom app need to uninstall once custom app be uninstalled"

**Current Status**: `before_uninstall` only removes company tab, doesn't clean up the 100+ custom fields defined in fixtures.

**Required**: Comprehensive uninstall function that removes all Print Designer custom fields.

### 4. Inconsistent Hook Organization

**❌ Issues:**
- Mixed installation hooks (some in after_install, some in after_migrate)
- Inconsistent commenting style  
- Some hooks disabled with reasons, others just commented out
- No clear separation between critical and optional hooks

## 🔧 Recommended Fixes

### 1. Custom Field Naming Migration
Create migration script to rename all custom fields to use `pd_custom_` prefix:

```python
# Example migration
old_fields = {
    "Sales Invoice": {
        "subject_to_wht": "pd_custom_subject_to_wht",
        "wht_income_type": "pd_custom_wht_income_type", 
        # ... etc
    }
}
```

### 2. hooks.py Cleanup
```python
# Remove redundant entries
# Remove: after_app_install (legacy)
# Fix: boot_session duplication  
# Clean: Remove all commented dead code
# Organize: Group similar hooks together
```

### 3. Add Comprehensive Uninstall
```python
before_uninstall = [
    "print_designer.uninstall.remove_all_custom_fields",  # NEW
    "print_designer.uninstall.before_uninstall",
    "print_designer.custom.company_tab.remove_company_stamps_signatures_tab",
]
```

## 📊 Impact Assessment

**Breaking Changes**: ❌ Yes - Field name changes will break existing templates
**Migration Required**: ✅ Yes - Need data migration for field renames  
**Testing Required**: ✅ Yes - All Print Designer formats need testing
**Documentation Update**: ✅ Yes - Update field references in docs

## 🚦 Priority Levels

1. **Critical**: Add uninstall functionality (prevents field orphaning)
2. **High**: Clean up hooks.py redundancy (improves maintainability) 
3. **Medium**: Custom field naming migration (improves namespace isolation)
4. **Low**: Code cleanup and documentation

## 📝 Compliance Status

- ❌ Custom field naming: **Non-compliant** (90%+ fields missing pd_custom_ prefix)
- ❌ hooks.py redundancy: **Issues found** (multiple redundant entries)
- ❌ Uninstall functionality: **Missing** (violates cleanup requirement)
- ✅ Test structure: **Compliant** (follows ERPNext pattern)

## 🎯 Next Steps

1. Create uninstall functionality immediately (prevents field orphaning)
2. Clean up hooks.py redundancy (improves performance) 
3. Plan custom field migration (breaking change - needs careful planning)
4. Update documentation to reflect proper field names