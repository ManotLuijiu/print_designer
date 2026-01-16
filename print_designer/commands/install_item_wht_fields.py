"""Install WHT Income Type custom field for Item DocType."""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def migrate_wht_income_type_field(doctype):
    """
    Migrate wht_income_type field from Select to Link type.
    Frappe doesn't allow changing fieldtype directly, so we need to delete and recreate.
    """
    field_name = f"{doctype}-wht_income_type"
    if frappe.db.exists("Custom Field", field_name):
        existing_field = frappe.db.get_value("Custom Field", field_name, "fieldtype")
        if existing_field == "Select":
            # Delete old Select field to allow creating new Link field
            frappe.delete_doc("Custom Field", field_name, force=True)
            frappe.db.commit()
            print(f"  Migrated {doctype}.wht_income_type: Select → Link")


def execute():
    """Install WHT Income Type custom field for Item."""

    custom_fields = {
        "Item": [
            # WHT Income Type for Purchase Transactions
            {
                "fieldname": "wht_income_type",
                "label": _("WHT Income Type"),
                "fieldtype": "Link",
                "insert_after": "stock_uom",
                "depends_on": "eval:doc.pd_custom_is_service_item",
                "options": "Thai WHT Income Type",
                "description": _("Default WHT income type for this item when used in purchase transactions"),
                "read_only": 0,
                "hidden": 0,
                "collapsible": 0,
                "length": 0,
                "bold": 0,
            }
        ]
    }

    print("Installing Item WHT Income Type field...")
    # Migrate wht_income_type from Select to Link (if exists as Select)
    migrate_wht_income_type_field("Item")
    create_custom_fields(custom_fields, update=True)

    # Clear cache
    frappe.clear_cache(doctype="Item")

    print("✅ Successfully installed WHT Income Type field for Item")
    print("✅ Field configuration:")
    print("   - Fieldname: wht_income_type")
    print("   - Depends on: pd_custom_is_service_item (Service Item checkbox)")
    print("   - Location: After stock_uom field")
    print("   - Options: professional_services, rental, service_fees, construction, advertising, other_services")

    return True


@frappe.whitelist()
def check_item_wht_fields():
    """Check if Item WHT Income Type field is installed."""

    required_field = "wht_income_type"

    existing_field = frappe.db.sql("""
        SELECT fieldname, label, depends_on
        FROM `tabCustom Field`
        WHERE dt = 'Item'
        AND fieldname = %s
    """, required_field, as_dict=True)

    if existing_field:
        field = existing_field[0]
        print("✅ Item WHT Income Type field is installed")
        print(f"   - Field: {field.fieldname}")
        print(f"   - Label: {field.label}")
        print(f"   - Depends on: {field.depends_on}")
        return True
    else:
        print("❌ Item WHT Income Type field is missing")
        print("   Run: bench install-item-wht-fields")
        return False


def uninstall_item_wht_fields():
    """Remove Item WHT Income Type field during app uninstall."""

    try:
        # Delete custom field
        frappe.db.delete("Custom Field", {
            "dt": "Item",
            "fieldname": "wht_income_type"
        })

        # Clear cache
        frappe.clear_cache(doctype="Item")
        frappe.db.commit()

        print("✅ Successfully removed Item WHT Income Type field")
        return True

    except Exception as e:
        frappe.db.rollback()
        print(f"❌ Error removing Item WHT field: {str(e)}")
        return False