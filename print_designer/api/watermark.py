import frappe
from frappe import _
from typing import Dict, Optional


@frappe.whitelist()
def validate_watermark_settings(doc, method=None):
    """
    Validation hook for Watermark Settings DocType
    Called automatically when Watermark Settings is saved
    """
    try:
        # Validate font size range
        if doc.default_font_size and (
            doc.default_font_size < 8 or doc.default_font_size > 72
        ):
            frappe.throw(_("Default font size must be between 8 and 72 pixels"))

        # Validate opacity range
        if doc.default_opacity and (doc.default_opacity < 0 or doc.default_opacity > 1):
            frappe.throw(_("Default opacity must be between 0 and 1"))

        # Validate template names are unique
        template_names = []
        for template in doc.watermark_templates:
            if template.template_name in template_names:
                frappe.throw(
                    _("Template name '{0}' is duplicated").format(
                        template.template_name
                    )
                )
            template_names.append(template.template_name)

            # Validate template settings
            if template.font_size and (
                template.font_size < 8 or template.font_size > 72
            ):
                frappe.throw(
                    _(
                        "Font size in template '{0}' must be between 8 and 72 pixels"
                    ).format(template.template_name)
                )

            if template.opacity and (template.opacity < 0 or template.opacity > 1):
                frappe.throw(
                    _("Opacity in template '{0}' must be between 0 and 1").format(
                        template.template_name
                    )
                )

        # Validate print format configs
        format_names = []
        for config in doc.print_format_configs:
            if config.print_format in format_names:
                frappe.throw(
                    _("Print Format '{0}' is configured multiple times").format(
                        config.print_format
                    )
                )
            format_names.append(config.print_format)

            # Validate override settings
            if config.override_settings:
                if config.font_size and (config.font_size < 8 or config.font_size > 72):
                    frappe.throw(
                        _(
                            "Override font size for '{0}' must be between 8 and 72 pixels"
                        ).format(config.print_format)
                    )

                if config.opacity and (config.opacity < 0 or config.opacity > 1):
                    frappe.throw(
                        _("Override opacity for '{0}' must be between 0 and 1").format(
                            config.print_format
                        )
                    )

    except Exception as e:
        frappe.log_error(f"Watermark validation error: {str(e)}")
        frappe.throw(_("Validation error: {0}").format(str(e)))


def clear_watermark_cache(doc=None, method=None):
    """
    Clear watermark cache when settings are updated
    Called automatically when Watermark Settings is saved
    """
    try:
        # Clear general watermark cache
        frappe.cache().delete_key("watermark_settings")
        frappe.cache().delete_key("watermark_templates")

        # Clear print format specific caches
        if doc and doc.print_format_configs:
            for config in doc.print_format_configs:
                cache_key = f"watermark_config_{config.print_format}"
                frappe.cache().delete_key(cache_key)

        frappe.publish_realtime(
            "watermark_settings_updated",
            {"message": "Watermark settings have been updated"},
        )

    except Exception as e:
        frappe.log_error(f"Error clearing watermark cache: {str(e)}")


def clear_format_watermark_cache(doc, method=None):
    """
    Clear cache for specific print format when it's updated
    Optional hook for Print Format updates
    """
    try:
        if doc.name:
            cache_key = f"watermark_config_{doc.name}"
            frappe.cache().delete_key(cache_key)
    except Exception as e:
        frappe.log_error(f"Error clearing format cache: {str(e)}")


# Optional: Add caching to improve performance
def get_cached_watermark_config(print_format):
    """
    Get watermark config with caching for better performance
    """
    cache_key = f"watermark_config_{print_format}"
    config = frappe.cache().get_value(cache_key)

    if config is None:
        config = get_watermark_config_for_print_format(print_format)
        # Cache for 1 hour
        frappe.cache().set_value(cache_key, config, expires_in_sec=3600)

    return config


@frappe.whitelist()
def get_watermark_config_for_print_format(print_format: str) -> Dict:
    """
    Get watermark configuration for specific print format

    Args:
        print_format: Name of the print format

    Returns:
        Dict containing watermark configuration
    """
    try:
        # Get global watermark settings
        settings = frappe.get_single("Watermark Settings")

        if not settings.enabled:
            return {"enabled": False}

        # Check for print format specific configuration
        format_config = None
        for config in settings.print_format_configs:
            if config.print_format == print_format:
                format_config = config
                break

        if format_config:
            # Use template configuration or overrides
            if format_config.watermark_template and not format_config.override_settings:
                template_config = get_watermark_template_config(
                    format_config.watermark_template
                )
                return {
                    "enabled": True,
                    "source": "template",
                    "template_name": format_config.watermark_template,
                    **template_config,
                }
            elif format_config.override_settings:
                # Use override settings
                return {
                    "enabled": True,
                    "source": "override",
                    "watermark_mode": format_config.watermark_mode
                    or settings.default_mode,
                    "font_size": format_config.font_size or settings.default_font_size,
                    "position": format_config.position or settings.default_position,
                    "font_family": format_config.font_family
                    or settings.default_font_family,
                    "color": format_config.color or settings.default_color,
                    "opacity": format_config.opacity or settings.default_opacity,
                    "custom_text": format_config.custom_text,
                }

        # Return default settings
        return {
            "enabled": True,
            "source": "default",
            "watermark_mode": settings.default_mode,
            "font_size": settings.default_font_size,
            "position": settings.default_position,
            "font_family": settings.default_font_family,
            "color": settings.default_color,
            "opacity": settings.default_opacity,
            "custom_text": None,
        }

    except Exception as e:
        frappe.log_error(f"Error getting watermark config: {str(e)}")
        return {"enabled": False, "error": str(e)}


@frappe.whitelist()
def get_watermark_template_config(template_name: str) -> Dict:
    """
    Get configuration for a specific watermark template

    Args:
        template_name: Name of the watermark template

    Returns:
        Dict containing template configuration
    """
    try:
        template = frappe.get_doc("Watermark Template", template_name)

        return {
            "watermark_mode": template.watermark_mode,
            "font_size": template.font_size,
            "position": template.position,
            "font_family": template.font_family,
            "color": template.color,
            "opacity": template.opacity,
            "custom_text": template.custom_text,
            "description": template.description,
        }

    except frappe.DoesNotExistError:
        frappe.throw(_("Watermark Template '{0}' not found").format(template_name))
    except Exception as e:
        frappe.log_error(f"Error getting template config: {str(e)}")
        frappe.throw(_("Error retrieving template configuration"))


@frappe.whitelist()
def get_available_watermark_templates() -> list:
    """
    Get list of available watermark templates

    Returns:
        List of template dictionaries with name and description
    """
    try:
        settings = frappe.get_single("Watermark Settings")
        templates = []

        for template in settings.watermark_templates:
            templates.append(
                {
                    "name": template.template_name,
                    "watermark_mode": template.watermark_mode,
                    "description": template.description
                    or f"Template: {template.template_name}",
                }
            )

        return templates

    except Exception as e:
        frappe.log_error(f"Error getting templates: {str(e)}")
        return []


@frappe.whitelist()
def save_print_format_watermark_config(print_format: str, config: Dict) -> Dict:
    """
    Save watermark configuration for a print format

    Args:
        print_format: Name of the print format
        config: Configuration dictionary

    Returns:
        Success/failure response
    """
    try:
        settings = frappe.get_single("Watermark Settings")

        # Find existing configuration
        existing_config = None
        for i, pf_config in enumerate(settings.print_format_configs):
            if pf_config.print_format == print_format:
                existing_config = i
                break

        # Prepare config data
        config_data = {
            "print_format": print_format,
            "watermark_template": config.get("watermark_template"),
            "override_settings": config.get("override_settings", 0),
        }

        if config.get("override_settings"):
            config_data.update(
                {
                    "watermark_mode": config.get("watermark_mode"),
                    "font_size": config.get("font_size"),
                    "position": config.get("position"),
                    "font_family": config.get("font_family"),
                    "color": config.get("color"),
                    "opacity": config.get("opacity"),
                    "custom_text": config.get("custom_text"),
                }
            )

        if existing_config is not None:
            # Update existing configuration
            settings.print_format_configs[existing_config].update(config_data)
        else:
            # Add new configuration
            settings.append("print_format_configs", config_data)

        settings.save()

        return {
            "success": True,
            "message": _("Watermark configuration saved successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error saving watermark config: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_watermark_template(template_data: Dict) -> Dict:
    """
    Create a new watermark template

    Args:
        template_data: Template configuration dictionary

    Returns:
        Success/failure response with template name
    """
    try:
        settings = frappe.get_single("Watermark Settings")

        # Validate template name uniqueness
        existing_names = [t.template_name for t in settings.watermark_templates]
        if template_data.get("template_name") in existing_names:
            return {"success": False, "error": _("Template name already exists")}

        # Add new template
        settings.append("watermark_templates", template_data)
        settings.save()

        return {
            "success": True,
            "message": _("Watermark template created successfully"),
            "template_name": template_data.get("template_name"),
        }

    except Exception as e:
        frappe.log_error(f"Error creating template: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def migrate_legacy_watermark_settings():
    """
    Migrate legacy custom field watermark settings to new DocType structure

    Returns:
        Migration status and report
    """
    try:
        # Check if Print Settings has legacy custom fields
        print_settings = frappe.get_single("Print Settings")

        migration_report = {"migrated_settings": 0, "migrated_formats": 0, "errors": []}

        # Create or update Watermark Settings
        if frappe.db.exists("Watermark Settings", "Watermark Settings"):
            watermark_settings = frappe.get_single("Watermark Settings")
        else:
            watermark_settings = frappe.new_doc("Watermark Settings")

        # Migrate global settings from custom fields if they exist
        legacy_fields = [
            "watermark_enabled",
            "watermark_default_mode",
            "watermark_font_size",
            "watermark_position",
            "watermark_font_family",
            "watermark_color",
            "watermark_opacity",
        ]

        migrated_any = False
        for field in legacy_fields:
            if hasattr(print_settings, field) and print_settings.get(field):
                migrated_any = True
                # Map legacy field to new field
                if field == "watermark_enabled":
                    watermark_settings.enabled = print_settings.get(field)
                elif field == "watermark_default_mode":
                    watermark_settings.default_mode = print_settings.get(field)
                elif field == "watermark_font_size":
                    watermark_settings.default_font_size = print_settings.get(field)
                elif field == "watermark_position":
                    watermark_settings.default_position = print_settings.get(field)
                elif field == "watermark_font_family":
                    watermark_settings.default_font_family = print_settings.get(field)
                elif field == "watermark_color":
                    watermark_settings.default_color = print_settings.get(field)
                elif field == "watermark_opacity":
                    watermark_settings.default_opacity = print_settings.get(field)

        if migrated_any:
            watermark_settings.save()
            migration_report["migrated_settings"] = 1

        return {
            "success": True,
            "message": _("Migration completed successfully"),
            "report": migration_report,
        }

    except Exception as e:
        frappe.log_error(f"Error during migration: {str(e)}")
        return {"success": False, "error": str(e)}
