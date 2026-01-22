"""
Thai Language Defaults Setup for Print Designer

This module ensures that the system defaults to Thai language for
Thai users, setting appropriate system-wide defaults.
"""

import frappe
from frappe import _


def setup_thai_language_defaults():
    """
    Setup Thai as the default language for Thai users.
    This function sets system-wide defaults to Thai language.
    """
    try:
        # Set System Settings default language to Thai
        system_settings = frappe.get_single("System Settings")
        if system_settings.language != "th":
            frappe.db.set_value("System Settings", None, "language", "th")
            frappe.log_error("System language set to Thai (th)", "Thai Language Setup")

        # Set Print Settings default language to Thai if not already set
        print_settings = frappe.get_single("Print Settings")
        if not hasattr(print_settings, 'language') or print_settings.language != "th":
            frappe.db.set_value("Print Settings", None, "language", "th")

        # Set Customer.language default to Thai via Property Setter
        # This ensures new Customers (and their linked documents like Sales Invoice)
        # will default to Thai print language
        setup_customer_language_default()

        # Commit the changes
        frappe.db.commit()

        print("✅ Thai language defaults setup completed")

    except Exception as e:
        frappe.log_error(f"Error setting up Thai language defaults: {str(e)}", "Thai Language Setup Error")
        print(f"❌ Error setting up Thai language defaults: {str(e)}")


def check_thai_language_setup():
    """
    Check if Thai language defaults are properly configured.
    """
    try:
        # Check System Settings
        system_settings = frappe.get_single("System Settings")
        system_lang = system_settings.language
        
        # Check Print Settings
        print_settings = frappe.get_single("Print Settings")
        print_lang = getattr(print_settings, 'language', None)
        
        print(f"System Settings language: {system_lang}")
        print(f"Print Settings language: {print_lang}")
        
        if system_lang == "th":
            print("✅ System language is correctly set to Thai")
        else:
            print("⚠️  System language is not set to Thai")
            
        if print_lang == "th":
            print("✅ Print Settings language is correctly set to Thai")
        else:
            print("⚠️  Print Settings language is not set to Thai")
            
        return system_lang == "th" and print_lang == "th"
        
    except Exception as e:
        frappe.log_error(f"Error checking Thai language setup: {str(e)}", "Thai Language Check Error")
        print(f"❌ Error checking Thai language setup: {str(e)}")
        return False


def reset_user_language_preferences():
    """
    Reset all user language preferences to Thai (optional utility function).
    Use with caution as this affects all users.
    """
    try:
        # Update all users to have Thai as their language preference
        users = frappe.get_all("User", fields=["name"], filters={"enabled": 1})
        
        for user in users:
            frappe.db.set_value("User", user.name, "language", "th")
            
        frappe.db.commit()
        print(f"✅ Updated {len(users)} users to Thai language preference")
        
    except Exception as e:
        frappe.log_error(f"Error resetting user language preferences: {str(e)}", "User Language Reset Error")
        print(f"❌ Error resetting user language preferences: {str(e)}")


def setup_customer_language_default():
    """
    Set Customer.language field default to Thai via Property Setter.
    This ensures new customers will have Thai as their default print language,
    which flows to Sales Invoice and other documents.

    Root cause analysis:
    - Customer.language has no default in ERPNext
    - Sales Invoice.language inherits from Customer via party.py
    - Print sidebar uses doc.language first, bypassing Print Format's default_print_language
    - This causes print language to show "en" even when system is configured for Thai
    """
    try:
        property_setter_name = "Customer-language-default"

        # Check if Property Setter already exists
        if frappe.db.exists("Property Setter", property_setter_name):
            # Update existing
            frappe.db.set_value("Property Setter", property_setter_name, "value", "th")
            print(f"✅ Updated Property Setter: {property_setter_name}")
        else:
            # Create new Property Setter
            ps = frappe.get_doc({
                "doctype": "Property Setter",
                "name": property_setter_name,
                "doc_type": "Customer",
                "doctype_or_field": "DocField",
                "field_name": "language",
                "property": "default",
                "property_type": "Text",
                "value": "th",
                "is_system_generated": 0
            })
            ps.insert(ignore_permissions=True)
            print(f"✅ Created Property Setter: {property_setter_name}")

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error setting up Customer language default: {str(e)}", "Thai Language Setup Error")
        print(f"❌ Error setting up Customer language default: {str(e)}")


def setup_thai_print_format_defaults():
    """
    Set all existing Print Formats without default_print_language to Thai.
    """
    try:
        # Find Print Formats without default_print_language set
        print_formats = frappe.get_all(
            "Print Format", 
            filters=[
                ["default_print_language", "is", "not set"]
            ],
            fields=["name"]
        )
        
        # Also include those with empty or None values
        all_formats = frappe.get_all("Print Format", fields=["name", "default_print_language"])
        formats_to_update = []
        
        for pf in all_formats:
            if not pf.get("default_print_language") or pf.get("default_print_language") in ["", None]:
                formats_to_update.append(pf.name)
        
        # Update them to Thai
        for format_name in formats_to_update:
            frappe.db.set_value("Print Format", format_name, "default_print_language", "th")
        
        frappe.db.commit()
        
        if formats_to_update:
            print(f"✅ Updated {len(formats_to_update)} Print Formats to default to Thai language")
            print(f"Updated formats: {', '.join(formats_to_update)}")
        else:
            print("✅ All Print Formats already have language defaults set")
        
    except Exception as e:
        frappe.log_error(f"Error setting Print Format Thai defaults: {str(e)}", "Print Format Thai Setup Error")
        print(f"❌ Error setting Print Format Thai defaults: {str(e)}")