# Console Utilities for Print Designer Development

This document describes the reliable console access method and utilities for debugging and development.

## 🎯 The Working Method

The most reliable way to access the Frappe console for database operations:

```bash
echo 'PYTHON_CODE_HERE' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console
```

## 🔧 Available Console Utilities

### Import Path
```python
from print_designer.commands.console_utils import (
    check_custom_field,
    fix_fetch_from_field,
    check_thai_tax_fields_status,
    execute_sql_query
)
```

### Functions

1. **`check_custom_field(doctype, fieldname)`** - Check field existence and properties
2. **`fix_fetch_from_field(doctype, fieldname, new_fetch_from=None)`** - Fix fetch_from references
3. **`check_thai_tax_fields_status()`** - Check all Thai tax fields across doctypes
4. **`execute_sql_query(query, values=None)`** - Execute SQL with proper formatting

## 📋 Ready-to-Use Templates

### Check Field Status
```bash
echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

from print_designer.commands.console_utils import check_custom_field
result = check_custom_field("Payment Entry", "pd_custom_company_tax_address")
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console
```

### Fix Field Issues
```bash
echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

from print_designer.commands.console_utils import fix_fetch_from_field
success = fix_fetch_from_field("Payment Entry", "pd_custom_company_tax_address", None)
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console
```

### Full Status Check
```bash
echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

from print_designer.commands.console_utils import check_thai_tax_fields_status
status = check_thai_tax_fields_status()
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console
```

### Execute SQL Query
```bash
echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

from print_designer.commands.console_utils import execute_sql_query
result = execute_sql_query("SELECT dt, fieldname FROM `tabCustom Field` WHERE fetch_from IS NOT NULL")
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console
```

## 🚀 Common Operations

### Check If Fields Exist
```python
# Method 1: Direct check
exists = frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "vat_treatment"})

# Method 2: Using utility (with detailed info)
result = check_custom_field("Payment Entry", "vat_treatment")
```

### Fix Fetch From Issues
```python
# Remove fetch_from reference
success = fix_fetch_from_field("Payment Entry", "pd_custom_company_tax_address")

# Set new fetch_from
success = fix_fetch_from_field("Payment Entry", "field_name", "company.valid_field")
```

### Database Queries
```python
# Get all fields with fetch_from issues
fields = execute_sql_query("""
    SELECT dt, fieldname, fetch_from
    FROM `tabCustom Field`
    WHERE fetch_from LIKE '%pd_custom_thai_tax_address%'
""")

# Check Payment Entry field count
count = execute_sql_query("""
    SELECT COUNT(*) as count
    FROM `tabCustom Field`
    WHERE dt = %s
""", ["Payment Entry"])
```

## 🛠️ Development Tips

### 1. Always Include Frappe Init
```python
import frappe
frappe.init("moo.localhost")
frappe.connect()
```

### 2. Use Transactions for Risky Operations
```python
try:
    frappe.db.begin()
    # Your operations here
    frappe.db.commit()
except Exception as e:
    frappe.db.rollback()
    print(f"Error: {e}")
```

### 3. Clear Cache After Changes
```python
frappe.clear_cache()
frappe.db.commit()  # Ensure changes are saved
```

### 4. Error Handling
```python
try:
    result = check_custom_field("DocType", "field_name")
    if result:
        print("Field exists and is working")
    else:
        print("Field not found")
except Exception as e:
    print(f"Error: {e}")
```

## 📊 Status Verification

After making changes, always verify:

```bash
echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

# Check specific field
exists = frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "vat_treatment"})
print(f"vat_treatment exists: {exists}")

# Check fetch_from issues
issues = frappe.db.sql("""
    SELECT fieldname, fetch_from
    FROM `tabCustom Field`
    WHERE dt = %s AND fetch_from LIKE %s
""", ("Payment Entry", "%pd_custom_thai_tax_address%"))
print(f"Fetch_from issues: {len(issues)}")

# Clear cache
frappe.clear_cache()
print("Cache cleared")
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console
```

## 🎯 Best Practices

1. **Test on development site first** (`moo.localhost`)
2. **Use utility functions for common operations** (they include error handling)
3. **Always clear cache after field changes**
4. **Verify changes with status checks**
5. **Use print statements for debugging output**
6. **Handle exceptions gracefully**

## 📁 File Locations

- **Console Utilities**: `/apps/print_designer/print_designer/commands/console_utils.py`
- **Easy Console Templates**: `/apps/print_designer/print_designer/commands/easy_console.py`
- **Hooks Registration**: `/apps/print_designer/print_designer/hooks.py` (lines 61-64)

This console method is now battle-tested and works reliably for all database operations!