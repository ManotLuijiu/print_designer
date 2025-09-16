#!/usr/bin/env python3
"""
Console Utilities for Print Designer
Provides convenient database access and debugging functions for development
"""

import frappe
from frappe import _


def execute_sql_query(query, values=None):
    """
    Execute SQL query with proper error handling and output formatting

    Args:
        query (str): SQL query to execute
        values (list, optional): Parameters for the query

    Returns:
        list: Query results
    """
    try:
        if values:
            result = frappe.db.sql(query, values, as_dict=True)
        else:
            result = frappe.db.sql(query, as_dict=True)

        print(f"Query executed successfully. Found {len(result)} records.")

        if result:
            # Print first few records for preview
            for i, row in enumerate(result[:5]):
                print(f"Record {i+1}: {row}")

            if len(result) > 5:
                print(f"... and {len(result) - 5} more records")

        return result

    except Exception as e:
        print(f"SQL Error: {str(e)}")
        frappe.log_error(f"Console SQL Error: {str(e)}", "Console Utils")
        return []


def check_custom_field(doctype, fieldname):
    """
    Check if a custom field exists and its properties

    Args:
        doctype (str): DocType name
        fieldname (str): Field name to check

    Returns:
        dict: Field information or None
    """
    try:
        field = frappe.db.get_value(
            "Custom Field",
            {"dt": doctype, "fieldname": fieldname},
            ["name", "fieldtype", "label", "fetch_from", "hidden", "read_only"],
            as_dict=True
        )

        if field:
            print(f"✅ Custom field found: {doctype}.{fieldname}")
            print(f"   Name: {field.get('name')}")
            print(f"   Type: {field.get('fieldtype')}")
            print(f"   Label: {field.get('label')}")
            print(f"   Fetch From: {field.get('fetch_from') or 'None'}")
            print(f"   Hidden: {field.get('hidden')}")
            print(f"   Read Only: {field.get('read_only')}")
            return field
        else:
            print(f"❌ Custom field not found: {doctype}.{fieldname}")
            return None

    except Exception as e:
        print(f"Error checking field: {str(e)}")
        return None


def fix_fetch_from_field(doctype, fieldname, new_fetch_from=None):
    """
    Fix fetch_from reference in a custom field

    Args:
        doctype (str): DocType name
        fieldname (str): Field name to fix
        new_fetch_from (str, optional): New fetch_from value (None to remove)

    Returns:
        bool: Success status
    """
    try:
        field_name = frappe.db.get_value(
            "Custom Field",
            {"dt": doctype, "fieldname": fieldname},
            "name"
        )

        if not field_name:
            print(f"❌ Field not found: {doctype}.{fieldname}")
            return False

        field_doc = frappe.get_doc("Custom Field", field_name)
        old_fetch_from = field_doc.fetch_from
        field_doc.fetch_from = new_fetch_from
        field_doc.save()

        print(f"✅ Updated {doctype}.{fieldname}")
        print(f"   Changed fetch_from from: '{old_fetch_from}' to: '{new_fetch_from}'")

        return True

    except Exception as e:
        print(f"❌ Error fixing fetch_from: {str(e)}")
        frappe.log_error(f"Error fixing fetch_from for {doctype}.{fieldname}: {str(e)}", "Console Utils")
        return False


def check_thai_tax_fields_status():
    """
    Check the status of all Thai tax custom fields across doctypes

    Returns:
        dict: Status summary
    """
    try:
        print("🔍 Checking Thai Tax Custom Fields Status...")

        # Check Payment Entry fields
        pe_fields = [
            "pd_custom_tax_base_amount",
            "pd_custom_apply_withholding_tax",
            "vat_treatment",
            "subject_to_wht",
            "net_total_after_wht"
        ]

        print("\n📋 Payment Entry Fields:")
        pe_status = {}
        for field in pe_fields:
            result = check_custom_field("Payment Entry", field)
            pe_status[field] = bool(result)

        # Check Sales Invoice fields
        si_fields = [
            "subject_to_wht",
            "custom_withholding_tax_amount",
            "vat_treatment"
        ]

        print("\n📋 Sales Invoice Fields:")
        si_status = {}
        for field in si_fields:
            result = check_custom_field("Sales Invoice", field)
            si_status[field] = bool(result)

        # Summary
        total_fields = len(pe_fields) + len(si_fields)
        working_fields = sum(pe_status.values()) + sum(si_status.values())

        print(f"\n📊 Summary: {working_fields}/{total_fields} fields working")

        return {
            "payment_entry": pe_status,
            "sales_invoice": si_status,
            "total": total_fields,
            "working": working_fields
        }

    except Exception as e:
        print(f"❌ Error checking field status: {str(e)}")
        return {}


@frappe.whitelist()
def console_execute(code):
    """
    Execute Python code in console with proper frappe context
    Useful for remote debugging and testing

    Args:
        code (str): Python code to execute

    Returns:
        dict: Execution result
    """
    if not frappe.conf.get("developer_mode"):
        frappe.throw(_("Console execution only allowed in developer mode"))

    try:
        # Create a safe execution context
        context = {
            'frappe': frappe,
            'print': lambda *args: frappe.publish_realtime('console_output', {'output': ' '.join(map(str, args))}),
            'execute_sql_query': execute_sql_query,
            'check_custom_field': check_custom_field,
            'fix_fetch_from_field': fix_fetch_from_field,
            'check_thai_tax_fields_status': check_thai_tax_fields_status,
        }

        # Execute the code
        exec(code, context)

        return {"status": "success", "message": "Code executed successfully"}

    except Exception as e:
        error_msg = str(e)
        frappe.log_error(f"Console execution error: {error_msg}", "Console Utils")
        return {"status": "error", "message": error_msg}


# Convenient aliases for common operations
def quick_sql(query, values=None):
    """Quick SQL execution alias"""
    return execute_sql_query(query, values)


def check_field(doctype, fieldname):
    """Quick field check alias"""
    return check_custom_field(doctype, fieldname)


def fix_field(doctype, fieldname, fetch_from=None):
    """Quick field fix alias"""
    return fix_fetch_from_field(doctype, fieldname, fetch_from)


if __name__ == "__main__":
    # Example usage when run directly
    print("Print Designer Console Utils")
    print("Available functions:")
    print("- execute_sql_query(query, values=None)")
    print("- check_custom_field(doctype, fieldname)")
    print("- fix_fetch_from_field(doctype, fieldname, new_fetch_from=None)")
    print("- check_thai_tax_fields_status()")
    print("- quick_sql(query, values=None)")
    print("- check_field(doctype, fieldname)")
    print("- fix_field(doctype, fieldname, fetch_from=None)")