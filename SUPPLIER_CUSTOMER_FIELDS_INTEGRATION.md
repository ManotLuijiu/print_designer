# Customer and Supplier Branch Code Fields - Complete Integration Documentation

## Overview
This document details the complete integration of `pd_custom_branch_code` fields for both Customer and Supplier DocTypes across all Print Designer lifecycle hooks, commands, and patches.

## Files Modified/Created

### 1. Created Files
- `print_designer/commands/install_customer_fields.py` - Customer field installer
- `print_designer/commands/install_supplier_fields.py` - Supplier field installer (NEW)

### 2. Modified Files
- `print_designer/hooks.py` - Added supplier commands and lifecycle hooks
- `print_designer/custom_fields.py` - Commented out Supplier section (lines 343-356)

## Integration Points

### 1. Commands Registration (`hooks.py` lines 18-25)

```python
# Customer field management (Branch Code for Thai tax invoices)
"print_designer.commands.install_customer_fields.install_customer_fields_cmd",
"print_designer.commands.install_customer_fields.check_customer_fields_cmd",
"print_designer.commands.install_customer_fields.uninstall_customer_fields_cmd",

# Supplier field management (Branch Code for Thai tax invoices)
"print_designer.commands.install_supplier_fields.install_supplier_fields_cmd",
"print_designer.commands.install_supplier_fields.check_supplier_fields_cmd",
"print_designer.commands.install_supplier_fields.uninstall_supplier_fields_cmd",
```

**Available Bench Commands:**
```bash
# Customer
bench install-pd-customer-fields
bench check-pd-customer-fields
bench uninstall-pd-customer-fields

# Supplier
bench install-pd-supplier-fields
bench check-pd-supplier-fields
bench uninstall-pd-supplier-fields
```

---

### 2. After Install Hook (`hooks.py` lines 517-518)

```python
"print_designer.commands.install_customer_fields.create_customer_fields",  # Install Customer branch_code field
"print_designer.commands.install_supplier_fields.create_supplier_fields",  # Install Supplier branch_code field
```

**What Happens:**
- Fresh installation of Print Designer
- Both Customer and Supplier `pd_custom_branch_code` fields are created automatically
- Default value: `"00000"` (head office branch code)

---

### 3. After Migrate Hook (`hooks.py` lines 559-560)

```python
"print_designer.commands.install_customer_fields.create_customer_fields",  # Ensure Customer branch_code field is installed during migration
"print_designer.commands.install_supplier_fields.create_supplier_fields",  # Ensure Supplier branch_code field is installed during migration
```

**What Happens:**
- Run after every `bench migrate`
- Ensures fields exist even if they were accidentally deleted
- Idempotent - safe to run multiple times (won't create duplicates)
- Runs on user machines during app updates

---

### 4. Before Uninstall Hook (`hooks.py` lines 585-586)

```python
"print_designer.commands.install_customer_fields.uninstall_customer_fields",  # Remove Customer branch_code field
"print_designer.commands.install_supplier_fields.uninstall_supplier_fields",  # Remove Supplier branch_code field
```

**What Happens:**
- Run before app uninstallation
- Removes all Print Designer custom fields from Customer and Supplier
- Cleans up Custom Field DocTypes
- Ensures clean uninstall (Frappe compliance requirement)

---

## Field Specifications

### Customer Field
```python
{
    "fieldname": "pd_custom_branch_code",
    "label": "Branch Code",
    "fieldtype": "Data",
    "insert_after": "tax_id",
    "default": "00000",
    "module": "Print Designer",
    "description": "Branch code for Thai tax invoice compliance (00000 = head office)"
}
```

### Supplier Field
```python
{
    "fieldname": "pd_custom_branch_code",
    "label": "Branch Code",
    "fieldtype": "Data",
    "insert_after": "tax_id",
    "default": "00000",
    "module": "Print Designer",
    "description": "Branch code for Thai tax invoice compliance (00000 = head office)"
}
```

**Design Decision:** Identical field definition for consistency across both DocTypes

---

## Testing & Verification

### 1. Fresh Installation Test
```bash
# On a test site
cd /Users/manotlj/frappe-bench
bench new-site test-supplier-fields.local
bench --site test-supplier-fields.local install-app erpnext
bench --site test-supplier-fields.local install-app print_designer

# Verify fields were created
bench --site test-supplier-fields.local execute "print_designer.commands.install_customer_fields.check_customer_fields()"
bench --site test-supplier-fields.local execute "print_designer.commands.install_supplier_fields.check_supplier_fields()"
```

**Expected Output:**
```
🔍 Checking Customer custom fields...
✅ All 1 Customer custom fields are installed!

🔍 Checking Supplier custom fields...
✅ All 1 Supplier custom fields are installed!
```

---

### 2. Migration Test
```bash
# Simulate migration scenario
bench --site test-supplier-fields.local migrate

# Verify fields still exist after migration
bench --site test-supplier-fields.local check-pd-customer-fields
bench --site test-supplier-fields.local check-pd-supplier-fields
```

---

### 3. Uninstall Test
```bash
# Test uninstall cleanup
bench --site test-supplier-fields.local uninstall-app print_designer

# Verify fields were removed
bench --site test-supplier-fields.local execute """
import frappe
customer_field = frappe.db.exists('Custom Field', {'dt': 'Customer', 'fieldname': 'pd_custom_branch_code'})
supplier_field = frappe.db.exists('Custom Field', {'dt': 'Supplier', 'fieldname': 'pd_custom_branch_code'})
print(f'Customer field exists: {bool(customer_field)}')
print(f'Supplier field exists: {bool(supplier_field)}')
"""
```

**Expected Output:**
```
Customer field exists: False
Supplier field exists: False
```

---

### 4. Production Verification Script

```bash
# On production server
bench --site your-production-site.local execute """
import frappe

def verify_branch_code_fields():
    '''Comprehensive verification of branch code field installation'''
    results = {}

    # Check Customer field
    customer_field = frappe.db.exists('Custom Field', {
        'dt': 'Customer',
        'fieldname': 'pd_custom_branch_code'
    })
    results['customer_field_exists'] = bool(customer_field)

    # Check Supplier field
    supplier_field = frappe.db.exists('Custom Field', {
        'dt': 'Supplier',
        'fieldname': 'pd_custom_branch_code'
    })
    results['supplier_field_exists'] = bool(supplier_field)

    # Check for legacy/duplicate fields
    legacy_customer_fields = frappe.db.sql('''
        SELECT fieldname FROM \`tabCustom Field\`
        WHERE dt = 'Customer' AND fieldname LIKE '%branch%'
    ''', as_dict=True)

    legacy_supplier_fields = frappe.db.sql('''
        SELECT fieldname FROM \`tabCustom Field\`
        WHERE dt = 'Supplier' AND fieldname LIKE '%branch%'
    ''', as_dict=True)

    results['customer_branch_fields'] = [f['fieldname'] for f in legacy_customer_fields]
    results['supplier_branch_fields'] = [f['fieldname'] for f in legacy_supplier_fields]

    # Check for proper default values
    if customer_field:
        customer_default = frappe.db.get_value('Custom Field', customer_field, 'default')
        results['customer_default'] = customer_default

    if supplier_field:
        supplier_default = frappe.db.get_value('Custom Field', supplier_field, 'default')
        results['supplier_default'] = supplier_default

    return results

print(frappe.as_json(verify_branch_code_fields(), indent=2))
"""
```

**Expected Output (Production):**
```json
{
  "customer_field_exists": true,
  "supplier_field_exists": true,
  "customer_branch_fields": ["pd_custom_branch_code"],
  "supplier_branch_fields": ["pd_custom_branch_code"],
  "customer_default": "00000",
  "supplier_default": "00000"
}
```

---

## Troubleshooting

### Issue: Fields not appearing after installation

**Solution:**
```bash
# Clear cache
bench --site your-site.local clear-cache

# Reload DocType
bench --site your-site.local execute """
import frappe
frappe.reload_doctype('Customer')
frappe.reload_doctype('Supplier')
"""

# Re-run field installation
bench --site your-site.local execute "print_designer.commands.install_customer_fields.create_customer_fields()"
bench --site your-site.local execute "print_designer.commands.install_supplier_fields.create_supplier_fields()"
```

---

### Issue: Duplicate branch code fields on production

**Diagnostic:**
```bash
bench --site your-site.local execute """
import frappe
print('=== Customer Branch Fields ===')
customer_fields = frappe.db.sql('''
    SELECT name, fieldname, label, \`default\`, module
    FROM \`tabCustom Field\`
    WHERE dt = 'Customer' AND fieldname LIKE '%branch%'
''', as_dict=True)
for f in customer_fields:
    print(frappe.as_json(f, indent=2))

print('\\n=== Supplier Branch Fields ===')
supplier_fields = frappe.db.sql('''
    SELECT name, fieldname, label, \`default\`, module
    FROM \`tabCustom Field\`
    WHERE dt = 'Supplier' AND fieldname LIKE '%branch%'
''', as_dict=True)
for f in supplier_fields:
    print(frappe.as_json(f, indent=2))
"""
```

**Cleanup Script:**
```bash
# Remove legacy fields (BACKUP DATABASE FIRST!)
bench --site your-site.local execute """
import frappe

# Define the correct field
correct_field = 'pd_custom_branch_code'

# Remove legacy Customer branch fields
customer_fields = frappe.db.sql('''
    SELECT name, fieldname FROM \`tabCustom Field\`
    WHERE dt = 'Customer' AND fieldname LIKE '%branch%' AND fieldname != %s
''', (correct_field,), as_dict=True)

for field in customer_fields:
    print(f'Removing legacy Customer field: {field.fieldname}')
    frappe.delete_doc('Custom Field', field.name, force=1)

# Remove legacy Supplier branch fields
supplier_fields = frappe.db.sql('''
    SELECT name, fieldname FROM \`tabCustom Field\`
    WHERE dt = 'Supplier' AND fieldname LIKE '%branch%' AND fieldname != %s
''', (correct_field,), as_dict=True)

for field in supplier_fields:
    print(f'Removing legacy Supplier field: {field.fieldname}')
    frappe.delete_doc('Custom Field', field.name, force=1)

frappe.db.commit()
print('✅ Cleanup completed')
"""
```

---

## Integration Verification Checklist

- [x] **commands** registered in `hooks.py` lines 18-25
- [x] **after_install** hook calls both `create_customer_fields()` and `create_supplier_fields()` (lines 517-518)
- [x] **after_migrate** hook calls both `create_customer_fields()` and `create_supplier_fields()` (lines 559-560)
- [x] **before_uninstall** hook calls both `uninstall_customer_fields()` and `uninstall_supplier_fields()` (lines 585-586)
- [x] **Supplier section commented out** in `custom_fields.py` (lines 343-356)
- [x] **No patches needed** - fields are managed via after_install and after_migrate hooks
- [x] **Field definitions identical** for consistency
- [x] **Idempotent functions** - safe to run multiple times

---

## Notes

### Why No Patches?
Patches are typically used for one-time schema changes or data migrations. Since these fields are:
1. Managed by `after_install` and `after_migrate` hooks
2. Idempotent by design (safe to run multiple times)
3. Simple field additions (not complex migrations)

**We don't need patches.** The hooks handle all scenarios:
- Fresh installations → `after_install`
- Updates/migrations → `after_migrate`
- Cleanup → `before_uninstall`

### Why Comment Out custom_fields.py?
The Supplier field was previously in `custom_fields.py` under `GLOBAL_DEFAULTS_CUSTOM_FIELDS` (wrong section). By commenting it out and using a dedicated installer:
1. **Consistency**: Both Customer and Supplier use identical patterns
2. **Maintainability**: Easier to manage field lifecycle
3. **Clarity**: Clear separation of concerns
4. **Testing**: Individual test commands for each DocType

---

## Production Deployment Steps

1. **Pull latest code:**
   ```bash
   cd /Users/manotlj/frappe-bench/apps/print_designer
   git pull origin develop
   ```

2. **Run migration:**
   ```bash
   bench --site your-production-site.local migrate
   ```

3. **Verify installation:**
   ```bash
   bench --site your-production-site.local check-pd-customer-fields
   bench --site your-production-site.local check-pd-supplier-fields
   ```

4. **Clear cache:**
   ```bash
   bench --site your-production-site.local clear-cache
   ```

5. **Restart services:**
   ```bash
   bench restart
   ```

6. **Test in UI:**
   - Open Customer form → Check "Branch Code" field appears after "Tax ID"
   - Open Supplier form → Check "Branch Code" field appears after "Tax ID"
   - Verify default value is "00000"

---

## Success Criteria

✅ **Installation Success:**
- Both Customer and Supplier have `pd_custom_branch_code` field
- Default value is "00000"
- Field appears after "Tax ID" in form
- No duplicate/legacy branch fields exist

✅ **Migration Success:**
- Fields persist after `bench migrate`
- No errors in console or logs
- Fields remain functional in UI

✅ **Uninstall Success:**
- Both fields are completely removed
- No orphaned Custom Field records
- Clean uninstall without errors

---

*Document Version: 1.0*
*Last Updated: 2025-01-10*
*Author: Claude Code - Print Designer Team*
