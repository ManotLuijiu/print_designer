"""
Configure list view columns for Thai WHT DocTypes.

This runs after install/migrate to ensure:
- TWI: name(ID) + 5 columns, ID has flex: 2.5
- TWC: name(ID) + category_name, ID has flex: 2.5

Usage:
    bench --site <site> execute install_list_view_columns
"""
import frappe


def install_list_view_columns():
    _configure_twi_list_view()
    _configure_twc_list_view()
    frappe.db.commit()
    print("✅ List view columns configured")


def _configure_twi_list_view():
    """Thai WHT Income Type: name(ID) + 5 columns, ID has flex: 2.5"""
    doctype = "Thai WHT Income Type"

    # Remove any existing 'name' field in list view (might have been added before)
    frappe.db.sql(
        "DELETE FROM `tabDocField` WHERE parent=%s AND fieldname='name'",
        (doctype,),
    )

    # Add name as first list view column with flex: 2.5
    frappe.db.sql(
        """
        INSERT INTO `tabDocField`
        (name, parent, fieldname, label, fieldtype, in_list_view, idx, width)
        VALUES (%s, %s, 'name', 'ID', 'Data', 1, 1, 'flex: 2.5')
        """,
        (f"{doctype}-name-list", doctype),
    )

    # Ensure standard columns are in list view
    standard_cols = [
        ("form_type", "Form Type", 2),
        ("recipient_type", "Recipient Type", 3),
        ("form_type_th", "Form Type (TH)", 6),
        ("tax_rate", "Tax Rate (%)", 7),
        ("income_category", "Income Category", 12),
    ]
    for fieldname, label, idx in standard_cols:
        existing = frappe.db.get_value(
            "DocField",
            {"parent": doctype, "fieldname": fieldname},
            "name",
        )
        if existing:
            frappe.db.sql(
                "UPDATE `tabDocField` SET in_list_view=1, idx=%s WHERE name=%s",
                (idx, existing),
            )
        # If not in DocField, it's in DocType JSON — skip

    print(f"  ✓ {doctype}: ID flex: 2.5 + 5 columns")


def _configure_twc_list_view():
    """Tax Withholding Category: name(ID) + category_name, ID has flex: 2.5"""
    doctype = "Tax Withholding Category"

    # Remove any existing 'name' field in list view
    frappe.db.sql(
        "DELETE FROM `tabDocField` WHERE parent=%s AND fieldname='name'",
        (doctype,),
    )

    # Add name as first list view column with flex: 2.5
    frappe.db.sql(
        """
        INSERT INTO `tabDocField`
        (name, parent, fieldname, label, fieldtype, in_list_view, idx, width)
        VALUES (%s, %s, 'name', 'ID', 'Data', 1, 1, 'flex: 2.5')
        """,
        (f"{doctype}-name-list", doctype),
    )

    # Ensure category_name is in list view (idx=2)
    existing = frappe.db.get_value(
        "DocField",
        {"parent": doctype, "fieldname": "category_name"},
        "name",
    )
    if existing:
        frappe.db.sql(
            "UPDATE `tabDocField` SET in_list_view=1, idx=2 WHERE name=%s",
            (existing,),
        )

    print(f"  ✓ {doctype}: ID flex: 2.5 + Category Name")


if __name__ == "__main__":
    install_list_view_columns()
