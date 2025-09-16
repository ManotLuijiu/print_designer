#!/usr/bin/env python3
"""
Easy Console Access for Print Designer Development

This provides the exact console method that works reliably for database operations.
Usage examples and patterns for efficient debugging and development.
"""

def get_console_template(operation_type="basic"):
    """
    Get console command templates for different operations

    Args:
        operation_type (str): Type of operation (basic, field_check, field_fix, sql, status)

    Returns:
        str: Ready-to-use console command template
    """

    templates = {
        "basic": '''echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

# Your code here
print("Console ready!")
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console''',

        "field_check": '''echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

# Check Payment Entry field
fields = frappe.db.get_all("Custom Field",
    filters={"dt": "Payment Entry", "fieldname": "pd_custom_tax_base_amount"},
    fields=["name", "fetch_from", "fieldtype", "label"])
print("Field info:", fields)
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console''',

        "field_fix": '''echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

# Fix fetch_from field
field_name = frappe.db.get_value("Custom Field",
    {"dt": "Payment Entry", "fieldname": "pd_custom_tax_base_amount"}, "name")

if field_name:
    field_doc = frappe.get_doc("Custom Field", field_name)
    old_fetch = field_doc.fetch_from
    field_doc.fetch_from = None
    field_doc.save()
    print(f"Fixed: {old_fetch} → None")
else:
    print("Field not found")
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console''',

        "sql": '''echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

# Execute SQL query
result = frappe.db.sql("""
    SELECT dt, fieldname, fetch_from, fieldtype
    FROM `tabCustom Field`
    WHERE dt = %s AND fetch_from IS NOT NULL
""", ("Payment Entry",), as_dict=True)

print(f"Found {len(result)} fields with fetch_from:")
for r in result:
    print(f"  {r.fieldname}: {r.fetch_from}")
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console''',

        "status": '''echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

# Check Thai tax fields status
pe_fields = ["vat_treatment", "subject_to_wht", "net_total_after_wht"]

print("🔍 Payment Entry Thai Tax Fields Status:")
for field in pe_fields:
    exists = frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": field})
    status = "✅" if exists else "❌"
    print(f"  {status} {field}")

# Check for problematic fetch_from references
fetch_issues = frappe.db.sql("""
    SELECT fieldname, fetch_from
    FROM `tabCustom Field`
    WHERE dt = %s AND fetch_from LIKE %s
""", ("Payment Entry", "%pd_custom_thai_tax_address%"), as_dict=True)

if fetch_issues:
    print(f"\\n⚠️ Found {len(fetch_issues)} fetch_from issues:")
    for issue in fetch_issues:
        print(f"  {issue.fieldname} → {issue.fetch_from}")
else:
    print("\\n✅ No fetch_from issues found")
' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console'''
    }

    return templates.get(operation_type, templates["basic"])


def print_usage_guide():
    """Print comprehensive usage guide for console operations"""

    print("""
🔧 EASY CONSOLE ACCESS FOR PRINT DESIGNER DEVELOPMENT

==============================================================
METHOD THAT WORKS RELIABLY (as discovered):
==============================================================

echo 'PYTHON_CODE_HERE' | /Users/manotlj/miniconda3/bin/bench --site moo.localhost console

==============================================================
READY-TO-USE TEMPLATES:
==============================================================

1. 📋 CHECK FIELD STATUS:
""")
    print(get_console_template("field_check"))
    print("""

2. 🔧 FIX FETCH_FROM FIELD:
""")
    print(get_console_template("field_fix"))
    print("""

3. 📊 RUN SQL QUERY:
""")
    print(get_console_template("sql"))
    print("""

4. ✅ CHECK THAI TAX FIELDS STATUS:
""")
    print(get_console_template("status"))
    print("""

==============================================================
USAGE PATTERNS:
==============================================================

🟢 BASIC PATTERN:
1. Start with: echo 'PYTHON_CODE' | bench --site moo.localhost console
2. Always include:
   import frappe
   frappe.init("moo.localhost")
   frappe.connect()
3. Add your specific operations
4. Use print() for output

🟢 MULTI-LINE CODE:
For complex operations, use the echo approach with proper escaping:

echo 'import frappe
frappe.init("moo.localhost")
frappe.connect()

# Your multi-line code here
result = frappe.db.get_value("DocType", "DocType Name", "field")
print("Result:", result)
' | bench --site moo.localhost console

🟢 DEBUGGING THAI TAX ISSUES:
- Check field existence: frappe.db.exists("Custom Field", {...})
- Check fetch_from issues: SELECT * FROM `tabCustom Field` WHERE fetch_from LIKE '%non_existent%'
- Fix fields: field_doc.fetch_from = None; field_doc.save()
- Clear cache after changes: frappe.clear_cache()

==============================================================
COMMON OPERATIONS:
==============================================================

✅ Check if field exists:
frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": "field_name"})

✅ Get field info:
frappe.db.get_value("Custom Field", {"dt": "DocType", "fieldname": "field"}, ["name", "fetch_from"])

✅ Fix fetch_from:
field_doc = frappe.get_doc("Custom Field", field_name)
field_doc.fetch_from = None
field_doc.save()

✅ Run SQL:
frappe.db.sql("SELECT * FROM `tabCustom Field` WHERE conditions", as_dict=True)

✅ Clear cache:
frappe.clear_cache()

==============================================================
TIPS:
==============================================================

1. 🎯 Always test on moo.localhost first
2. 🔒 Use transactions for risky operations: frappe.db.begin(); frappe.db.commit()
3. 📝 Add print statements for debugging
4. 🧹 Clear cache after field changes
5. 🔍 Check both Custom Field and DocType for field definitions

==============================================================
""")


# Command-line interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        operation = sys.argv[1]
        if operation in ["field_check", "field_fix", "sql", "status", "basic"]:
            print(f"# {operation.upper()} CONSOLE COMMAND:")
            print(get_console_template(operation))
        else:
            print(f"Unknown operation: {operation}")
            print("Available operations: basic, field_check, field_fix, sql, status")
    else:
        print_usage_guide()