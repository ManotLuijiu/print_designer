import frappe

def execute():
    """Fix PND3 Form tax_period_month field type from Select to Int"""

    # First update the database column type
    frappe.db.sql("""
        ALTER TABLE `tabPND3 Form`
        MODIFY COLUMN tax_period_month INT(11)
    """)

    # Update existing records to convert string values to integers
    frappe.db.sql("""
        UPDATE `tabPND3 Form`
        SET tax_period_month = CAST(tax_period_month AS UNSIGNED)
        WHERE tax_period_month IS NOT NULL
    """)

    # Reload the DocType to apply JSON changes
    frappe.reload_doc("print_designer", "doctype", "PND3 Form")

    frappe.db.commit()
    print("✅ PND3 Form field type migration completed")