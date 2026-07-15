"""
Configure list view columns for Thai WHT Income Type.

Usage:
    bench --site <site> execute configure_twi_list_view
"""
import frappe


def configure_twi_list_view():
    doctype = "Thai WHT Income Type"

    # Hide unwanted columns from list view
    hide_cols = ["form_type", "income_category", "recipient_type"]
    for fieldname in hide_cols:
        frappe.db.sql(
            """
            UPDATE `tabDocField`
            SET in_list_view = 0
            WHERE parent = %s AND fieldname = %s
            """,
            (doctype, fieldname),
        )

    # Show desired columns in list view
    show_cols = [
        ("doc_title_th", 2),
        ("income_category_th", 3),
        ("form_type_th", 4),
        ("tax_rate", 5),
        ("income_description_th", 6),
    ]
    for fieldname, idx in show_cols:
        frappe.db.sql(
            """
            UPDATE `tabDocField`
            SET in_list_view = 1, idx = %s
            WHERE parent = %s AND fieldname = %s
            """,
            (idx, doctype, fieldname),
        )

    frappe.db.commit()
    print("✅ Thai WHT Income Type list view configured: ID, Doc Title (TH), Income Category (TH), Form Type (TH), Tax Rate (%), Income Description (TH)")
