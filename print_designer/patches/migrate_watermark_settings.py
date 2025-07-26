# File: print_designer/patches/migrate_watermark_settings.py

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Migration script to move from custom fields to DocType-based watermark system
    """
    frappe.reload_doctype("Watermark Settings")
    frappe.reload_doctype("Watermark Template")
    frappe.reload_doctype("Print Format Watermark Config")

    # Create default Watermark Settings if it doesn't exist
    if not frappe.db.exists("Watermark Settings", "Watermark Settings"):
        create_default_watermark_settings()

    # Migrate legacy custom field data
    migrate_legacy_settings()

    # Create some default templates
    create_default_templates()

    print("Watermark settings migration completed successfully")


def create_default_watermark_settings():
    """Create default Watermark Settings document"""
    try:
        settings = frappe.new_doc("Watermark Settings")
        settings.enabled = 1
        settings.default_mode = "None"
        settings.default_font_size = 24
        settings.default_position = "Top Right"
        settings.default_font_family = "Sarabun"
        settings.default_color = "#999999"
        settings.default_opacity = 0.6
        settings.insert()
        frappe.db.commit()
        print(f"Created default Watermark Settings")
    except Exception as e:
        print(f"Error creating default settings: {str(e)}")


def migrate_legacy_settings():
    """Migrate data from custom fields to DocType"""
    try:
        # Check if Print Settings has legacy custom fields
        print_settings_meta = frappe.get_meta("Print Settings")
        legacy_fields = {}

        # Map of legacy custom field names to new field names
        field_mapping = {
            "watermark_enabled": "enabled",
            "watermark_default_mode": "default_mode",
            "watermark_font_size": "default_font_size",
            "watermark_position": "default_position",
            "watermark_font_family": "default_font_family",
            "watermark_color": "default_color",
            "watermark_opacity": "default_opacity",
        }

        # Check if any legacy fields exist
        for field in print_settings_meta.fields:
            if field.fieldname in field_mapping:
                legacy_fields[field.fieldname] = field_mapping[field.fieldname]

        if legacy_fields:
            print_settings = frappe.get_single("Print Settings")
            watermark_settings = frappe.get_single("Watermark Settings")

            migrated_count = 0
            for legacy_field, new_field in legacy_fields.items():
                legacy_value = print_settings.get(legacy_field)
                if legacy_value is not None:
                    setattr(watermark_settings, new_field, legacy_value)
                    migrated_count += 1

            if migrated_count > 0:
                watermark_settings.save()
                frappe.db.commit()
                print(
                    f"Migrated {migrated_count} legacy settings to Watermark Settings"
                )

    except Exception as e:
        print(f"Error migrating legacy settings: {str(e)}")


def create_default_templates():
    """Create some useful default watermark templates"""
    templates = [
        {
            "template_name": "Original Document",
            "watermark_mode": "Original on First Page",
            "font_size": 28,
            "position": "Top Right",
            "font_family": "Sarabun",
            "color": "#1976d2",
            "opacity": 0.7,
            "description": "Shows 'ORIGINAL' on first page only",
        },
        {
            "template_name": "Copy Document",
            "watermark_mode": "Copy on All Pages",
            "font_size": 24,
            "position": "Top Right",
            "font_family": "Sarabun",
            "color": "#d32f2f",
            "opacity": 0.6,
            "description": "Shows 'COPY' on all pages",
        },
        {
            "template_name": "Draft Watermark",
            "watermark_mode": "Copy on All Pages",
            "font_size": 32,
            "position": "Middle Center",
            "font_family": "Arial",
            "color": "#ff9800",
            "opacity": 0.3,
            "custom_text": "DRAFT",
            "description": "Large 'DRAFT' watermark in center",
        },
        {
            "template_name": "Confidential",
            "watermark_mode": "Copy on All Pages",
            "font_size": 20,
            "position": "Bottom Center",
            "font_family": "Tahoma",
            "color": "#9c27b0",
            "opacity": 0.8,
            "custom_text": "CONFIDENTIAL",
            "description": "Bottom centered confidential marking",
        },
    ]

    try:
        watermark_settings = frappe.get_single("Watermark Settings")

        for template_data in templates:
            # Check if template already exists
            existing = any(
                t.template_name == template_data["template_name"]
                for t in watermark_settings.watermark_templates
            )

            if not existing:
                watermark_settings.append("watermark_templates", template_data)

        watermark_settings.save()
        frappe.db.commit()
        print(f"Created {len(templates)} default watermark templates")

    except Exception as e:
        print(f"Error creating default templates: {str(e)}")


def cleanup_legacy_fields():
    """
    Optional cleanup function to remove legacy custom fields
    Run this only after confirming migration was successful
    """
    legacy_field_names = [
        "watermark_enabled",
        "watermark_default_mode",
        "watermark_font_size",
        "watermark_position",
        "watermark_font_family",
        "watermark_color",
        "watermark_opacity",
    ]

    try:
        for field_name in legacy_field_names:
            if frappe.db.exists(
                "Custom Field", {"dt": "Print Settings", "fieldname": field_name}
            ):
                frappe.delete_doc(
                    "Custom Field", {"dt": "Print Settings", "fieldname": field_name}
                )

        frappe.db.commit()
        print("Cleaned up legacy custom fields")

    except Exception as e:
        print(f"Error cleaning up legacy fields: {str(e)}")


if __name__ == "__main__":
    execute()
