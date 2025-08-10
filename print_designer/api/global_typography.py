"""
Global Typography API for Print Designer

Handles system-wide font stack management through Global Defaults integration.
Provides dynamic CSS generation and application for typography settings.
"""

import os

import frappe
from frappe import _
from frappe.utils import get_site_path, now

# Font mappings for dynamic generation
FONT_MAPPINGS = {
    "Sarabun (Thai)": '"Sarabun", "Noto Sans Thai", "IBM Plex Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Noto Sans Thai": '"Noto Sans Thai", "Sarabun", "IBM Plex Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "IBM Plex Sans Thai": '"IBM Plex Sans Thai", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Kanit (Thai)": '"Kanit", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Prompt (Thai)": '"Prompt", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Mitr (Thai)": '"Mitr", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Pridi (Thai)": '"Pridi", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Inter": '"InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Roboto": '"Roboto", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", sans-serif',
    "Open Sans": '"Open Sans", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Lato": '"Lato", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    "Nunito Sans": '"Nunito Sans", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
}


@frappe.whitelist()
def apply_typography_settings(font_stack, enable_thai_support=True, css_content=None):
    """
    Apply typography settings system-wide by generating CSS overrides.

    Args:
            font_stack (str): Complete font stack to apply
            enable_thai_support (bool): Whether to enable Thai font optimizations
            css_content (str): Pre-generated CSS content

    Returns:
            dict: Success status and details
    """
    try:
        if not font_stack:
            return {"success": False, "error": "Font stack is required"}

        # Generate CSS content if not provided
        if not css_content:
            css_content = _generate_typography_css(font_stack, enable_thai_support)

        # Write CSS to the typography override file
        success = _write_typography_css(css_content)

        if success:
            # Update Global Defaults document to reflect changes
            _update_global_defaults_cache()

            return {
                "success": True,
                "message": "Typography settings applied successfully",
                "font_stack": font_stack,
                "thai_support": enable_thai_support,
            }
        else:
            return {"success": False, "error": "Failed to write typography CSS"}

    except Exception as e:
        frappe.log_error(f"Typography settings application error: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_typography_css():
    """
    Get the current typography CSS for Jinja injection.
    Generates CSS dynamically based on current Global Defaults settings.

    Returns:
            str: CSS content for typography override
    """
    try:
        global_defaults = frappe.get_single("Global Defaults")

        # Get current typography settings
        primary_font = global_defaults.get("primary_font_family", "Noto Sans Thai")
        print(f"primary_font: {primary_font}")
        enable_thai = bool(global_defaults.get("enable_thai_font_support", 1))
        print(f"enable_thai: {enable_thai}")
        custom_stack = global_defaults.get("custom_font_stack")
        print(f"custom_stack: {custom_stack}")
        if not isinstance(custom_stack, str):
            custom_stack = ""

        # Generate font stack dynamically based on current selection
        font_stack = _get_font_stack_for_selection(primary_font, custom_stack)
        print(f"font_stack: {font_stack}")
        # Generate fresh CSS with current settings
        if font_stack:
            css_content = _generate_typography_css(font_stack, enable_thai)
            print(f"css_content: {css_content}")
            # Update stored CSS for consistency (async)
            frappe.enqueue(
                "print_designer.api.global_typography._write_typography_css",
                css_content=css_content,
                queue="short",
            )

            return css_content
        else:
            # Fallback to stored CSS if no font stack generated
            return global_defaults.get("custom_typography_css", "")

    except Exception as e:
        frappe.log_error(f"Error generating dynamic typography CSS: {str(e)}")
        # Fallback to stored CSS
        try:
            global_defaults = frappe.get_single("Global Defaults")
            return global_defaults.get("custom_typography_css", "")
        except Exception:
            return ""


@frappe.whitelist()
def get_current_typography_settings():
    """
    Get current typography settings from Global Defaults.

    Returns:
            dict: Current typography configuration
    """
    try:
        global_defaults = frappe.get_single("Global Defaults")

        return {
            "primary_font_family": global_defaults.get(
                "primary_font_family", "Noto Sans Thai"
            ),
            "enable_thai_font_support": global_defaults.get(
                "enable_thai_font_support", 1
            ),
            "custom_font_stack": global_defaults.get("custom_font_stack", ""),
            "custom_typography_css": global_defaults.get("custom_typography_css", ""),
            "has_typography_override": bool(
                global_defaults.get("custom_typography_css")
            ),
        }

    except Exception as e:
        frappe.log_error(f"Error fetching typography settings: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def reset_typography_to_default():
    """
    Reset typography settings to Print Designer defaults.

    Returns:
            dict: Reset operation status
    """
    try:
        # Default Noto Sans Thai-based font stack
        default_font_stack = '"Noto Sans Thai", "Sarabun", "IBM Plex Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif'

        # Generate default CSS
        css_content = _generate_typography_css(default_font_stack, True)

        # Apply default settings
        success = _write_typography_css(css_content)

        if success:
            # Update Global Defaults
            global_defaults = frappe.get_single("Global Defaults")
            global_defaults.db_set(
                "primary_font_family", "Noto Sans Thai", update_modified=False
            )
            global_defaults.db_set("enable_thai_font_support", 1, update_modified=False)
            global_defaults.db_set("custom_font_stack", "", update_modified=False)

            return {
                "success": True,
                "message": "Typography reset to default Noto Sans Thai configuration",
            }
        else:
            return {"success": False, "error": "Failed to reset typography"}

    except Exception as e:
        frappe.log_error(f"Typography reset error: {str(e)}")
        return {"success": False, "error": str(e)}


def _generate_typography_css(font_stack, enable_thai_support=True):
    """
    Generate CSS content for typography override.

    Args:
            font_stack (str): Font stack to apply
            enable_thai_support (bool): Include Thai optimizations

    Returns:
            str: Generated CSS content
    """
    css_content = """/* Global Typography Override - Generated by Print Designer */
/* Applied: {timestamp} */

html:root, :root {{
    --font-stack: {font_stack} !important;
}}

/* Base font family application */
html, body {{
    font-family: var(--font-stack) !important;
}}

/* Form controls and UI elements */
.form-control, .form-select, .btn, .navbar, .sidebar, .page-container,
.page-content, .page-title, .navbar-brand, .menu-item, .list-item,
.doctype-list, .form-section, .section-head, .form-group, .field-label,
.form-message, .modal-header, .modal-body, .modal-footer,
.frappe-control, .control-input, .control-label, .like-disabled-input,
.comment-box, .timeline-item, .list-row, .list-row-col,
.desk-sidebar, .navbar-collapse, .dropdown-menu, .dropdown-item,
/* Text elements */
p, span, div, h1, h2, h3, h4, h5, h6, td, th, label,
/* Input elements */
input, button, select, optgroup, textarea {{
    font-family: var(--font-stack) !important;
}}

/* Print Designer specific elements */
.print-format-builder, .print-designer-canvas, .print-designer-toolbar,
.print-format-preview, .print-preview, .print-view {{
    font-family: var(--font-stack) !important;
}}
""".format(timestamp=now(), font_stack=font_stack)

    if enable_thai_support:
        css_content += """
/* Thai font optimizations */
.thai-font-optimized,
[lang="th"], .thai-text {{
    font-family: var(--font-stack) !important;
    font-feature-settings: "liga" 1, "kern" 1;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    word-break: break-word;
    overflow-wrap: break-word;
}}

/* Thai unicode support enhancements */
.thai-currency, .thai-amount,
.thai-date, .thai-address {{
    font-family: var(--font-stack) !important;
    font-weight: 400;
    letter-spacing: 0.025em;
}}
"""

    return css_content


def _write_typography_css(css_content):
    """
    Store CSS content in Global Defaults for dynamic injection.

    Args:
            css_content (str): CSS content to store

    Returns:
            bool: Success status
    """
    try:
        # Store the CSS content in Global Defaults for injection
        global_defaults = frappe.get_single("Global Defaults")
        global_defaults.db_set(
            "custom_typography_css", css_content, update_modified=False
        )

        return True

    except Exception as e:
        frappe.log_error(f"Failed to store typography CSS: {str(e)}")
        return False


def _ensure_css_in_bundle():
    """
    Ensure typography CSS is included in the Print Designer bundle.
    """
    try:
        bundle_file = os.path.join(
            frappe.get_app_path("print_designer"),
            "print_designer",
            "public",
            "css",
            "thai_fonts.bundle.scss",
        )

        # Import statement to add
        import_statement = "@import 'global_typography_override.css';"

        # Check if import already exists
        if os.path.exists(bundle_file):
            with open(bundle_file, "r", encoding="utf-8") as f:
                content = f.read()

            if import_statement not in content:
                # Add import at the beginning
                updated_content = import_statement + "\n\n" + content

                with open(bundle_file, "w", encoding="utf-8") as f:
                    f.write(updated_content)

    except Exception as e:
        frappe.log_error(f"Failed to update CSS bundle: {str(e)}")


def _check_typography_override_exists():
    """
    Check if typography override file exists.

    Returns:
            bool: Whether override file exists
    """
    css_file_path = os.path.join(
        frappe.get_app_path("print_designer"),
        "print_designer",
        "public",
        "css",
        "global_typography_override.css",
    )

    return os.path.exists(css_file_path)


def _update_global_defaults_cache():
    """
    Update Global Defaults cache to reflect typography changes.
    """
    try:
        # Clear cache for Global Defaults
        frappe.cache().delete_keys("global_defaults")

        # Rebuild sys_defaults
        from frappe.utils import get_defaults

        frappe.local.system_settings = None
        frappe.local.conf = None

    except Exception as e:
        frappe.log_error(f"Failed to update Global Defaults cache: {str(e)}")


# Initialization function called during app setup
def setup_default_typography():
    """
    Setup default typography settings during app installation.
    """
    try:
        # Check if Global Defaults exists and has typography fields
        if frappe.db.exists("Global Defaults", "Global Defaults"):
            global_defaults = frappe.get_single("Global Defaults")

            # Set default values if not already set
            if not global_defaults.get("primary_font_family"):
                global_defaults.db_set(
                    "primary_font_family", "Noto Sans Thai", update_modified=False
                )
                global_defaults.db_set(
                    "enable_thai_font_support", 1, update_modified=False
                )

        # Apply default typography
        reset_typography_to_default()

    except Exception as e:
        frappe.log_error(f"Failed to setup default typography: {str(e)}")


# Hook function for after_install
def after_install():
    """
    Setup typography after Print Designer installation.
    """
    setup_default_typography()


def on_global_defaults_update(doc, method):
    """
    Automatically apply typography settings when Global Defaults is updated.

    Args:
            doc: Global Defaults document
            method: The hook method (on_update)
    """
    try:
        # Check if typography fields have changed
        typography_fields = [
            "primary_font_family",
            "enable_thai_font_support",
            "custom_font_stack",
        ]

        # Only proceed if any typography field has changed
        has_typography_changes = False
        for field in typography_fields:
            if doc.has_value_changed(field):
                has_typography_changes = True
                break

        if not has_typography_changes:
            return

        # Get the selected font family
        primary_font = doc.get("primary_font_family", "Noto Sans Thai")
        enable_thai = bool(doc.get("enable_thai_font_support", 1))
        custom_stack = doc.get("custom_font_stack")
        if not isinstance(custom_stack, str):
            custom_stack = ""

        # Generate font stack based on selection
        font_stack = _get_font_stack_for_selection(primary_font, custom_stack)

        if font_stack:
            # Apply typography settings automatically
            apply_typography_settings(font_stack, enable_thai)
            frappe.logger().info(f"Typography automatically applied: {primary_font}")

    except Exception as e:
        frappe.log_error(f"Error in auto-applying typography: {str(e)}")


def _get_font_stack_for_selection(primary_font, custom_stack=""):
    """
    Generate font stack based on primary font selection.

    Args:
            primary_font (str): Selected primary font family
            custom_stack (str): Custom font stack if "System Default" is selected

    Returns:
            str: Generated font stack
    """
    # Font mappings from client script
    font_mappings = {
        "Sarabun (Thai)": '"Sarabun", "Noto Sans Thai", "IBM Plex Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Noto Sans Thai": '"Noto Sans Thai", "Sarabun", "IBM Plex Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "IBM Plex Sans Thai": '"IBM Plex Sans Thai", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Kanit (Thai)": '"Kanit", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Prompt (Thai)": '"Prompt", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Mitr (Thai)": '"Mitr", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Pridi (Thai)": '"Pridi", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Inter": '"InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Roboto": '"Roboto", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", sans-serif',
        "Open Sans": '"Open Sans", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Lato": '"Lato", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
        "Nunito Sans": '"Nunito Sans", "InterVariable", "Inter", "Noto Sans Thai", "Sarabun", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
    }

    # Handle System Default with custom font stack
    if primary_font == "System Default" and custom_stack:
        return custom_stack

    # Return mapped font stack or default to Noto Sans Thai
    return font_mappings.get(primary_font, font_mappings["Noto Sans Thai"])
