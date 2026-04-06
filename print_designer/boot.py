import json
import os
import frappe
from frappe import _


def boot_session(bootinfo):
    """Consolidated boot session with Print Designer"""

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
