import json
import os
import frappe
from frappe import _


def boot_session(bootinfo):
    """Consolidated boot session with Print Designer + Thai Billing workspace"""

    # === IMPORTED FROM signature_stamp.py ===
    # Add print designer settings to boot info (copied from signature_stamp.py boot_session)

    # Get Print Settings to include watermark configuration
    try:
        print_settings = frappe.get_single("Print Settings")

        # Extract watermark settings
        watermark_config = {
            "watermark_settings": print_settings.get("watermark_settings", "None"),
            "watermark_font_size": print_settings.get("watermark_font_size", 12),
            "watermark_position": print_settings.get("watermark_position", "Top Right"),
            "watermark_font_family": print_settings.get("watermark_font_family", "Arial"),
            "enable_multiple_copies": print_settings.get("enable_multiple_copies", 0),
            "default_copy_count": print_settings.get("default_copy_count", 2),
            "default_original_label": print_settings.get("default_original_label", "Original"),
            "default_copy_label": print_settings.get("default_copy_label", "Copy"),
            "show_copy_controls_in_toolbar": print_settings.get("show_copy_controls_in_toolbar", 1),
        }

        log_to_print_designer(f"Boot session watermark config: {watermark_config}")

    except Exception as e:
        # Fallback to default values if Print Settings cannot be accessed
        watermark_config = {
            "watermark_settings": "None",
            "watermark_font_size": 12,
            "watermark_position": "Top Right",
            "watermark_font_family": "Arial",
            "enable_multiple_copies": 0,
            "default_copy_count": 2,
            "default_original_label": "Original",
            "default_copy_label": "Copy",
            "show_copy_controls_in_toolbar": 1,
        }
        log_to_print_designer(f"Boot session watermark fallback due to error: {e}")

    bootinfo.print_designer_settings = {
        "enable_digital_signatures": True,
        "enable_company_stamps": True,
        "default_signature_company_filter": True,
        # Add watermark settings for frontend availability
        **watermark_config
    }

    # === ORIGINAL boot.py FUNCTIONALITY ===
    # Thai tax compliance settings (enabled)
    bootinfo.thai_compliance = {
        "enabled": frappe.get_system_settings("enable_thai_tax_compliance") or 0,
        "vat_rate": 7.0,
        "wht_rates": get_wht_rates(),
        "required_fields": ["subject_to_wht", "is_paid"],
    }

    # Purchase Invoice business rules (enabled)
    bootinfo.purchase_rules = {
        "credit_services_disable_vat_report": True,
        "fifo_vat_validation": True,
    }

    # Custom modules availability (enabled)
    bootinfo.digisoft_features = {
        "input_vat_report": frappe.db.exists("Report", "Thai Input VAT Report"),
        "wht_certificates": True,
        "retention_management": True,
    }

    # User-specific company settings
    if frappe.session.user != "Guest":
        bootinfo.user_defaults = {
            "company": frappe.defaults.get_user_default("company"),
            "currency": frappe.defaults.get_user_default("currency"),
            "fiscal_year": frappe.defaults.get_user_default("fiscal_year"),
        }

    # Extend Selling workspace with Thai Billing
    # NOTE: Commented out for Frappe v16 compatibility - bootinfo.workspaces structure changed
    # This is not a core function, workspace extension can be handled via workspace JSON instead
    # extend_selling_workspace(bootinfo)


def log_to_print_designer(message, level="INFO"):
    """Log messages to Print Designer specific log file (copied from signature_stamp.py)"""
    try:
        log_dir = os.path.join(frappe.get_site_path(), "logs", "print_designer")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "print_designer.log")

        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception as e:
        # Fallback to frappe logger if file logging fails
        frappe.logger("print_designer").info(f"Log write failed: {e}, Original message: {message}")


def extend_selling_workspace(bootinfo):
    """Extend the Selling workspace to include Thai Billing after Sales Invoice"""

    # Get the current workspaces from bootinfo
    if not hasattr(bootinfo, 'workspaces') or not bootinfo.workspaces:
        return

    # Frappe v16 changed bootinfo.workspaces structure - it's now a list of strings
    # Skip this function in v16+ as workspace extension is handled differently
    if bootinfo.workspaces and isinstance(bootinfo.workspaces[0], str):
        # v16 format: list of workspace names (strings)
        return

    # v15 format: list of workspace dictionaries
    # Find the Selling workspace
    selling_workspace = None
    for workspace in bootinfo.workspaces:
        if isinstance(workspace, dict) and workspace.get('name') == 'Selling':
            selling_workspace = workspace
            break

    if not selling_workspace or not selling_workspace.get('links'):
        return

    # Find the Sales Invoice link and insert Thai Billing after it
    links = selling_workspace['links']
    sales_invoice_index = -1

    # Find the index of Sales Invoice
    for i, link in enumerate(links):
        if link.get('link_to') == 'Sales Invoice' and link.get('type') == 'Link':
            sales_invoice_index = i
            break

    # If Sales Invoice found, insert Thai Billing after it
    if sales_invoice_index >= 0:
        billing_link = {
            "dependencies": "Customer, Sales Invoice",
            "hidden": 0,
            "is_query_report": 0,
            "label": "Billing",
            "link_count": 0,
            "link_to": "Thai Billing",
            "link_type": "DocType",
            "onboard": 0,
            "type": "Link"
        }

        # Insert after Sales Invoice (index + 1)
        links.insert(sales_invoice_index + 1, billing_link)


def get_wht_rates():
    """Get standard Thai WHT rates"""
    return {
        "professional_services": 3.0,
        "construction": 3.0,
        "rental": 5.0,
        "advertising": 2.0,
        "service_fees": 3.0,
        "transportation": 1.0,
    }
