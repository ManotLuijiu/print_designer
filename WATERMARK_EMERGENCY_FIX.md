# Emergency Fix for Watermark Field Error

## Problem
Stock Entry (and other DocTypes) showing error:
```
pymysql.err.OperationalError: (1054, "Unknown column 'watermark_text' in 'INSERT INTO'")
```

## Root Cause
Print Designer's watermark fields were not properly installed in the database, causing a schema mismatch.

## Quick Fix

### Option 1: Console Command (Fastest)

1. Go to: https://tipsiricons.bunchee.online/app/dev-console
2. Paste this code and press Enter:

```python
# Emergency watermark field installation
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from print_designer.watermark_fields import get_watermark_custom_fields

# Install all watermark fields
custom_fields = get_watermark_custom_fields()
create_custom_fields(custom_fields, update=True)
frappe.db.commit()

print("✅ Watermark fields installed! Stock Entry error should be fixed.")
```

### Option 2: Direct SQL Verification

After running the fix, verify the field was created:

```python
# Check if watermark_text column exists in Stock Entry table
result = frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'")
print(f"Stock Entry watermark_text column: {'✅ EXISTS' if result else '❌ MISSING'}")
```

### Option 3: Bench Command (if available)

If you have bench access to the server:

```bash
# Go to frappe-bench directory
cd /home/frappe/frappe-bench

# Install watermark fields
bench --site tipsiricons.bunchee.online execute print_designer.commands.install_watermark_fields.install_watermark_fields

# Migrate to ensure database schema is updated
bench --site tipsiricons.bunchee.online migrate
```

## Verification

After applying the fix:

1. **Test Stock Entry**: Try creating/saving a Stock Entry
2. **Check Column**: Run SQL check to confirm column exists
3. **Clear Cache**: Clear browser cache if needed

## Technical Details

The error occurs because:
1. Print Designer adds `watermark_text` field to Stock Entry DocType
2. Database table wasn't updated with the new column
3. Frappe tries to INSERT the field value but column doesn't exist

The fix creates the database column by installing custom fields properly.

## Expected Doctypes Fixed

This fix installs watermark_text fields on:
- Stock Entry ✅
- Sales Invoice
- Sales Order  
- Quotation
- Delivery Note
- Purchase Invoice
- Purchase Order
- Purchase Receipt
- Payment Entry
- Journal Entry
- And 15+ other DocTypes

## Success Indicators

✅ No more "Unknown column 'watermark_text'" errors  
✅ Stock Entry saves successfully  
✅ Other DocTypes can save with watermark fields  
✅ Print formats can use watermark functionality  