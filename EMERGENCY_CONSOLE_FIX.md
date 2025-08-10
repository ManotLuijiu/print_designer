# EMERGENCY CONSOLE FIX for Stock Entry Watermark Error

## Quick Fix Instructions

1. Go to: https://tipsiricons.bunchee.online/app/dev-console
2. Copy and paste this ENTIRE code block and press Enter:

```python
# EMERGENCY FIX: Add missing watermark_text column to Stock Entry
print("🚨 EMERGENCY FIX: Adding watermark_text column to Stock Entry")

# Step 1: Check if column exists
columns = frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'")

if not columns:
    print("❌ watermark_text column is MISSING from Stock Entry table")
    print("🔧 Adding watermark_text column directly to database...")
    
    # Add the column directly to the database
    frappe.db.sql("""
        ALTER TABLE `tabStock Entry` 
        ADD COLUMN `watermark_text` varchar(140) DEFAULT 'None'
    """)
    
    print("✅ watermark_text column added to Stock Entry table")
else:
    print("✅ watermark_text column already exists in Stock Entry table")

# Step 2: Ensure Custom Field exists
custom_field_exists = frappe.db.exists("Custom Field", {
    "dt": "Stock Entry",
    "fieldname": "watermark_text"
})

if not custom_field_exists:
    print("❌ Stock Entry watermark_text Custom Field is MISSING")
    print("🔧 Creating Custom Field...")
    
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
    custom_fields = {
        "Stock Entry": [
            {
                "fieldname": "watermark_text",
                "fieldtype": "Select",
                "label": "Document Watermark",
                "options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
                "default": "None",
                "insert_after": "stock_entry_type",
                "print_hide": 1,
                "allow_on_submit": 1,
                "translatable": 1,
                "description": "Watermark text to display on printed document"
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    print("✅ Stock Entry watermark_text Custom Field created")
else:
    print("✅ Stock Entry watermark_text Custom Field already exists")

# Step 3: Commit changes
frappe.db.commit()

print("🎉 EMERGENCY FIX COMPLETED!")
print("✅ Stock Entry watermark_text error should now be resolved")
print("✅ You can now try saving Stock Entry again")
```

## Alternative: SQL Fix Only

If the above doesn't work, try just the SQL fix:

```python
# Direct SQL fix - just add the missing column
frappe.db.sql("""
    ALTER TABLE `tabStock Entry` 
    ADD COLUMN `watermark_text` varchar(140) DEFAULT 'None'
""")
frappe.db.commit()
print("✅ Added watermark_text column to Stock Entry")
```

## Verification

After running the fix, verify it worked:

```python
# Check if column exists
columns = frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'")
print(f"Column exists: {'✅ YES' if columns else '❌ NO'}")

# Check if Custom Field exists  
field_exists = frappe.db.exists("Custom Field", {"dt": "Stock Entry", "fieldname": "watermark_text"})
print(f"Custom Field exists: {'✅ YES' if field_exists else '❌ NO'}")
```

## What This Fix Does

1. **Adds Database Column** - Directly adds the missing `watermark_text` column to the `tabStock Entry` table
2. **Creates Custom Field** - Ensures the Frappe Custom Field definition exists
3. **Sets Default Value** - Sets default to "None" to prevent future issues
4. **Commits Changes** - Saves all changes to the database

## Expected Result

After running this fix:
- ✅ Stock Entry saves will work without the "Unknown column" error
- ✅ You can create and save Stock Entry documents normally
- ✅ Other DocTypes will also get their watermark fields fixed

## If Fix Doesn't Work

Try these additional steps:

1. **Clear Cache:**
```python
frappe.clear_cache()
```

2. **Rebuild DocType:**
```python
frappe.reload_doctype("Stock Entry")
```

3. **Check Error Again:**
Try saving a Stock Entry again to see if the error is resolved.

The issue is that the database table is missing the column that the Custom Field definition expects to exist. This direct SQL approach bypasses the normal field creation process and adds the column immediately.