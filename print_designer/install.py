import os
import platform
import shutil
import zipfile
from pathlib import Path
from typing import Literal

import click
import frappe
from frappe import _
import requests
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from print_designer.custom_fields import CUSTOM_FIELDS
from print_designer.default_formats import (
    install_default_formats,
    on_print_designer_install,
)
from print_designer.pdf_generator.generator import FrappePDFGenerator


def check_frappe_version():
    def major_version(v: str) -> str:
        return v.split(".")[0]

    frappe_version = major_version(frappe.__version__)
    if int(frappe_version) >= 15:
        return

    click.secho(
        f"You're attempting to install Print Designer with Frappe version {frappe_version}. "
        "This is not supported and will result in broken install. Please install it using Version 15 or Develop branch.",
        fg="red",
    )
    raise SystemExit(1)


def before_install():
    check_frappe_version()


def after_install():
    # Install all custom fields in unified way
    install_all_custom_fields()

    # Print designer specific setup
    on_print_designer_install()
    remove_chrome_pdf_generator_option()
    add_weasyprint_pdf_generator_option()
    set_wkhtmltopdf_as_default_for_print_designer()
    setup_print_designer_settings()

    # TODO: move to get-app command ( not that much harmful as it will check if it is already installed )
    setup_chromium()


def install_all_custom_fields():
    """
    Unified custom field installation for fresh installations
    Handles both basic custom fields and Print Settings enhancements
    """
    try:
        frappe.logger().info("Installing all print_designer custom fields...")

        # 1. Install basic print_designer custom fields first
        create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
        frappe.logger().info("✅ Basic custom fields installed")

        # 2. Install signature and watermark fields
        _ensure_signature_fields()
        _ensure_watermark_fields()
        _ensure_watermark_defaults()
        frappe.logger().info("✅ Signature and watermark fields installed")

        # 3. Install enhanced Print Settings (includes watermark configuration)
        setup_enhanced_print_settings()
        frappe.logger().info("✅ Enhanced Print Settings installed")

        frappe.logger().info("🎉 All custom fields installation completed successfully")

    except Exception as e:
        frappe.logger().error(f"❌ Error during custom fields installation: {str(e)}")
        # Don't fail the entire installation
        pass


def after_migrate():
    """
    Hook that runs after each migration/update
    This is CRUCIAL for maintaining customizations after ERPNext updates
    """
    frappe.logger().info("Running post-migration setup for print_designer")

    # Ensure all custom fields exist (unified approach)
    ensure_all_fields_after_migration()

    # Fix any field ordering issues
    fix_print_settings_field_ordering()

    frappe.logger().info("Post-migration setup completed")


def ensure_all_fields_after_migration():
    """
    Unified function to ensure all print_designer fields exist after migration
    Consolidates all field creation to avoid duplication
    """
    try:
        frappe.logger().info("Ensuring all print_designer fields after migration...")
        
        # 1. Basic print_designer custom fields
        create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
        frappe.logger().info("✅ Basic custom fields ensured")
        
        # 2. Signature and watermark fields  
        _ensure_signature_fields()
        _ensure_watermark_fields()
        _ensure_watermark_defaults()
        frappe.logger().info("✅ Signature and watermark fields ensured")
        
        # 3. Enhanced Print Settings fields (includes all watermark configuration)
        setup_enhanced_print_settings()
        frappe.logger().info("✅ Enhanced Print Settings ensured")
        
        frappe.logger().info("🎉 All fields ensured after migration")
        
    except Exception as e:
        frappe.logger().error(f"❌ Error ensuring fields after migration: {str(e)}")
        pass


def setup_enhanced_print_settings():
    """
    Create enhanced Print Settings fields directly (merged approach)
    Since we install after ERPNext, we can create ALL fields in one place
    """
    try:
        frappe.logger().info("Creating enhanced Print Settings fields...")

        # Create all Print Settings custom fields in one go
        create_custom_fields(
            {
                "Print Settings": [
                    # Original ERPNext fields (ensure they exist)
                    {
                        "label": _("Compact Item Print"),
                        "fieldname": "compact_item_print",
                        "fieldtype": "Check",
                        "default": "1",
                        "insert_after": "with_letterhead",
                    },
                    {
                        "label": _("Print UOM after Quantity"),
                        "fieldname": "print_uom_after_quantity",
                        "fieldtype": "Check",
                        "default": "0",
                        "insert_after": "compact_item_print",
                    },
                    {
                        "label": _("Print taxes with zero amount"),
                        "fieldname": "print_taxes_with_zero_amount",
                        "fieldtype": "Check",
                        "default": "0",
                        "insert_after": "allow_print_for_cancelled",
                    },
                    # Print Designer copy-related fields
                    {
                        "label": _("Copy Settings"),
                        "fieldname": "copy_settings_section",
                        "fieldtype": "Section Break",
                        "insert_after": "print_taxes_with_zero_amount",
                        "collapsible": 1,
                    },
                    {
                        "label": _("Enable Multiple Copies"),
                        "fieldname": "enable_multiple_copies",
                        "fieldtype": "Check",
                        "default": "0",
                        "insert_after": "copy_settings_section",
                        "description": _(
                            "Enable multiple copy generation for print formats"
                        ),
                    },
                    {
                        "label": _("Default Copy Count"),
                        "fieldname": "default_copy_count",
                        "fieldtype": "Int",
                        "default": "2",
                        "insert_after": "enable_multiple_copies",
                        "depends_on": "enable_multiple_copies",
                        "description": _("Default number of copies to generate"),
                    },
                    {
                        "label": _("Copy Labels"),
                        "fieldname": "copy_labels_column",
                        "fieldtype": "Column Break",
                        "insert_after": "default_copy_count",
                    },
                    {
                        "label": _("Default Original Label"),
                        "fieldname": "default_original_label",
                        "fieldtype": "Data",
                        "default": _("Original"),
                        "insert_after": "copy_labels_column",
                        "depends_on": "enable_multiple_copies",
                        "description": _("Default label for original copy"),
                    },
                    {
                        "label": _("Default Copy Label"),
                        "fieldname": "default_copy_label",
                        "fieldtype": "Data",
                        "default": _("Copy"),
                        "insert_after": "default_original_label",
                        "depends_on": "enable_multiple_copies",
                        "description": _("Default label for additional copies"),
                    },
                    {
                        "label": _("Show Copy Controls in Toolbar"),
                        "fieldname": "show_copy_controls_in_toolbar",
                        "fieldtype": "Check",
                        "default": "1",
                        "insert_after": "default_copy_label",
                        "depends_on": "enable_multiple_copies",
                        "description": _("Show copy controls in print preview toolbar"),
                    },
                    # Watermark fields section
                    {
                        "label": _("Watermark Settings"),
                        "fieldname": "watermark_settings_section",
                        "fieldtype": "Section Break",
                        "insert_after": "show_copy_controls_in_toolbar",
                        "collapsible": 1,
                    },
                    {
                        "label": _("Watermark per Page"),
                        "fieldname": "watermark_settings",
                        "fieldtype": "Select",
                        "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                        "default": "None",
                        "insert_after": "watermark_settings_section",
                        "description": _(
                            "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=alternates between 'Original' and 'Copy'"
                        ),
                    },
                    {
                        "label": _("Watermark Font Size"),
                        "fieldname": "watermark_font_size",
                        "fieldtype": "Data",
                        "default": "24px",
                        "insert_after": "watermark_settings",
                        "depends_on": "eval:doc.watermark_settings != 'None'",
                        "description": _(
                            "Font size for watermark text (e.g., 24px, 2em)"
                        ),
                    },
                    {
                        "label": _("Watermark Position"),
                        "fieldname": "watermark_position",
                        "fieldtype": "Select",
                        "options": "Top Right\nTop Left\nTop Center\nMiddle Right\nMiddle Left\nMiddle Center\nBottom Right\nBottom Left\nBottom Center",
                        "default": "Top Right",
                        "insert_after": "watermark_font_size",
                        "depends_on": "eval:doc.watermark_settings != 'None'",
                        "description": _(
                            "Position where watermark appears on the page"
                        ),
                    },
                    {
                        "label": _("Watermark Font Family"),
                        "fieldname": "watermark_font_family",
                        "fieldtype": "Select",
                        "options": "Arial\nSarabun\nTH Sarabun New\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia",
                        "default": "Arial",
                        "insert_after": "watermark_position",
                        "depends_on": "eval:doc.watermark_settings != 'None'",
                        "description": _("Font family for watermark text"),
                    },
                ]
            },
            ignore_validate=True,
        )

        # Setup default values
        setup_print_settings_defaults()

        frappe.logger().info("✅ Enhanced Print Settings configured successfully")

    except Exception as e:
        frappe.logger().error(f"❌ Error setting up enhanced print settings: {str(e)}")


def setup_print_settings_defaults():
    """Setup default values for Print Settings after field creation"""
    try:
        print_settings = frappe.get_single("Print Settings")

        # Set default values for copy functionality
        if print_settings.get("enable_multiple_copies") is None:
            print_settings.set("enable_multiple_copies", 1)
        if not print_settings.get("default_copy_count"):
            print_settings.set("default_copy_count", 2)
        if not print_settings.get("default_original_label"):
            print_settings.set("default_original_label", _("Original"))
        if not print_settings.get("default_copy_label"):
            print_settings.set("default_copy_label", _("Copy"))
        if print_settings.get("show_copy_controls_in_toolbar") is None:
            print_settings.set("show_copy_controls_in_toolbar", 1)

        # Set default values for watermark functionality
        if not print_settings.get("watermark_settings"):
            print_settings.set("watermark_settings", "None")
        if not print_settings.get("watermark_font_size"):
            print_settings.set("watermark_font_size", "12px")
        if not print_settings.get("watermark_position"):
            print_settings.set("watermark_position", "Top Right")
        if not print_settings.get("watermark_font_family"):
            print_settings.set("watermark_font_family", "Sarabun")

        # Save settings
        print_settings.flags.ignore_permissions = True
        print_settings.flags.ignore_mandatory = True
        print_settings.save()

        frappe.logger().info("✅ Print Settings defaults configured")

    except Exception as e:
        frappe.logger().error(f"❌ Error setting Print Settings defaults: {str(e)}")
        pass


def fix_print_settings_field_ordering():
    """
    Fix field ordering issues that might occur after ERPNext migration
    Ensures proper field sequence in Print Settings
    """
    try:
        # Define the expected field order after print_taxes_with_zero_amount
        field_order = [
            # Copy settings section
            "copy_settings_section",
            "enable_multiple_copies",
            "default_copy_count",
            "copy_labels_column",
            "default_original_label",
            "default_copy_label",
            "show_copy_controls_in_toolbar",
            # Watermark settings section
            "watermark_settings_section",
            "watermark_settings",
            "watermark_font_size",
            "watermark_position",
            "watermark_font_family",
        ]

        # Update field positions to maintain correct order
        previous_field = "print_taxes_with_zero_amount"

        for fieldname in field_order:
            if frappe.db.exists(
                "Custom Field", {"dt": "Print Settings", "fieldname": fieldname}
            ):
                frappe.db.set_value(
                    "Custom Field",
                    {"dt": "Print Settings", "fieldname": fieldname},
                    "insert_after",
                    previous_field,
                )
                previous_field = fieldname

        frappe.logger().info("Print Settings field ordering fixed")

    except Exception as e:
        frappe.logger().error(f"Error fixing field ordering: {str(e)}")




def after_app_install(app):
    if app != "print_designer":
        install_default_formats(app)


def setup_chromium():
    """Setup Chromium at the bench level."""
    # Load Chromium version from common_site_config.json or use default

    try:
        executable = find_or_download_chromium_executable()
        click.echo(f"Chromium is already set up at {executable}")
    except Exception as e:
        click.echo(f"Failed to setup Chromium: {e}")
        raise RuntimeError(f"Failed to setup Chromium: {e}")
    return executable


def make_chromium_executable(executable):
    """Make the Chromium executable."""
    if os.path.exists(executable):
        # check if the file is executable
        if os.access(executable, os.X_OK):
            click.echo(f"Chromium executable is already executable: {executable}")
            return
        click.echo(f"Making Chromium executable: {executable}")
        os.chmod(executable, 0o755)  # Set executable permissions
        click.echo(f"Chromium executable permissions set: {executable}")
    else:
        raise RuntimeError(f"Chromium executable not found: {executable}.")


def find_or_download_chromium_executable():
    """Finds the Chromium executable or downloads if not found."""
    bench_path = frappe.utils.get_bench_path()
    """Determine the path to the Chromium executable."""
    chromium_dir = os.path.join(bench_path, "chromium")

    platform_name = platform.system().lower()

    if platform_name not in ["linux", "darwin", "windows"]:
        click.echo(f"Unsupported platform: {platform_name}")

    executable_name = FrappePDFGenerator.EXECUTABLE_PATHS.get(platform_name)

    # Construct the full path to the executable
    exec_path = Path(chromium_dir).joinpath(*executable_name)
    if not exec_path.exists():
        click.echo("Chromium is not available. downloading...")
        download_chromium()

    if not exec_path.exists():
        click.echo("Error while downloading chrome")

    return str(exec_path)


def download_chromium():
    bench_path = frappe.utils.get_bench_path()
    """Download and extract Chromium for the specific version at the bench level."""
    chromium_dir = os.path.join(bench_path, "chromium")

    # Remove old Chromium directory if it exists
    if os.path.exists(chromium_dir):
        click.echo("Removing old Chromium directory...")
        shutil.rmtree(chromium_dir, ignore_errors=True)

    os.makedirs(chromium_dir, exist_ok=True)

    download_url = get_chromium_download_url()
    file_name = os.path.basename(download_url)
    zip_path = os.path.join(chromium_dir, file_name)

    try:
        click.echo(f"Downloading Chromium from {download_url}...")
        # playwright's requires a user agent
        headers = {"User-Agent": "Wget/1.21.1"}
        with requests.get(
            download_url, stream=True, timeout=(10, 60), headers=headers
        ) as r:
            r.raise_for_status()  # Raise an error for bad status codes
            total_size = int(r.headers.get("content-length", 0))  # Get total file size
            bar = click.progressbar(length=total_size, label="Downloading Chromium")
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    bar.update(len(chunk))

        click.echo("Extracting Chromium...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(chromium_dir)

        if os.path.exists(zip_path):
            os.remove(zip_path)

        # There should be only one directory
        # Ensure the correct directory is renamed
        extracted = os.listdir(chromium_dir)[0]
        executable_path = FrappePDFGenerator.EXECUTABLE_PATHS[platform.system().lower()]
        chrome_folder_name = executable_path[0]

        if extracted != chrome_folder_name:
            extracted_dir = os.path.join(chromium_dir, extracted)
            renamed_dir = os.path.join(chromium_dir, chrome_folder_name)
            if os.path.exists(extracted_dir):
                click.echo(f"Renaming {extracted_dir} to {renamed_dir}")
                os.rename(extracted_dir, renamed_dir)
            else:
                raise RuntimeError(
                    f"Failed to rename extracted directory. Expected {chrome_folder_name}."
                )
            if os.path.exists(renamed_dir):
                executable_shell = os.path.join(renamed_dir, "chrome-headless-shell")
                if os.path.exists(executable_shell):
                    os.rename(
                        executable_shell, os.path.join(renamed_dir, "headless_shell")
                    )
                else:
                    raise RuntimeError(
                        "Failed to rename executable. Expected chrome-headless-shell."
                    )
            # Make the `headless_shell` executable
            exec_path = os.path.join(renamed_dir, executable_path[1])
            make_chromium_executable(exec_path)

        click.echo(f"Chromium is ready to use at: {chromium_dir}")
    except requests.Timeout:
        click.echo("Download timed out. Check your internet connection.")
        raise RuntimeError("Download timed out.")
    except requests.ConnectionError:
        click.echo("Failed to connect to Chromium download server.")
        raise RuntimeError("Connection error.")
    except requests.RequestException as e:
        click.echo(f"Failed to download Chromium: {e}")
        raise RuntimeError(f"Failed to download Chromium: {e}")
    except zipfile.BadZipFile as e:
        click.echo(f"Failed to extract Chromium: {e}")
        raise RuntimeError(f"Failed to extract Chromium: {e}")


def get_chromium_download_url():
    # Avoid this unless it is going to run on a single type of platform and you have the correct binary hosted.
    common_config = frappe.get_common_site_config()

    chrome_download_url = common_config.get("chromium_download_url", None)

    if chrome_download_url:
        return chrome_download_url

    """
	We are going to use chrome-for-testing builds but unfortunately it doesn't have linux arm64 https://github.com/GoogleChromeLabs/chrome-for-testing/issues/1
	so we will use playwright's fallback builds for linux arm64
	TODO: we will also use the fallback builds for windows arm
	https://community.arm.com/arm-community-blogs/b/tools-software-ides-blog/posts/native-chromium-builds-windows-on-arm
	"""
    """
	To find the CHROME_VERSION AND CHROME_FALLBACK_VERSION, follow these steps:
	1. Visit the GitHub Actions page for Playwright: https://github.com/microsoft/playwright/actions/workflows/roll_browser_into_playwright.yml
	2. Open the latest job run.
	3. Navigate to the "Roll to New Browser Version" step.
	4. In the logs, look for a line similar to:
		Downloading Chromium 133.0.6943.16 (playwright build v1155)
		Here, the first number (e.g., 133.0.6943.16) is the CHROME_VERSION, and the second number (e.g., 1155) is the CHROME_FALLBACK_VERSION.
	"""
    # Using Google's chrome-for-testing-public builds for most platforms. (close to end user experience)
    # For Linux ARM64, we use Playwright's Chromium builds due to the lack of official support.

    download_path = {
        "linux64": "%s/linux64/chrome-headless-shell-linux64.zip",
        "mac-arm64": "%s/mac-arm64/chrome-headless-shell-mac-arm64.zip",
        "mac-x64": "%s/mac-x64/chrome-headless-shell-mac-x64.zip",
        "win32": "%s/win32/chrome-headless-shell-win32.zip",
        "win64": "%s/win64/chrome-headless-shell-win64.zip",
    }
    linux_arm_download_path = {
        "ubuntu20.04-arm64": "%s/chromium-headless-shell-linux-arm64.zip",
        "ubuntu22.04-arm64": "%s/chromium-headless-shell-linux-arm64.zip",
        "ubuntu24.04-arm64": "%s/chromium-headless-shell-linux-arm64.zip",
        "debian11-arm64": "%s/chromium-headless-shell-linux-arm64.zip",
        "debian12-arm64": "%s/chromium-headless-shell-linux-arm64.zip",
    }

    platform_key = calculate_platform()

    version = "133.0.6943.35"
    playwright_build_version = "1157"

    base_url = "https://storage.googleapis.com/chrome-for-testing-public/"
    playwright_base_url = (
        "https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/"
    )

    # Overwrite with values from common_site_config.json ( escape hatch )
    version = common_config.get("chromium_version", version)
    playwright_build_version = common_config.get(
        "playwright_chromium_version", playwright_build_version
    )
    # make sure that you have all required flavours at correct urls
    base_url = common_config.get("chromium_download_base_url", base_url)
    playwright_base_url = common_config.get(
        "playwright_chromium_download_base_url", playwright_base_url
    )

    if platform_key in download_path:
        relative_path = download_path[platform_key]
    elif platform_key in linux_arm_download_path:
        version = playwright_build_version
        base_url = playwright_base_url
        relative_path = linux_arm_download_path[platform_key]
    else:
        frappe.throw(
            f"No download path configured or Chromium download not available for platform: {platform_key}"
        )

    return f"{base_url}{relative_path % version}"


def get_linux_distribution_info():
    # not tested
    """Retrieve Linux distribution information using the `distro` library."""
    import distro

    if not distro:
        return {"id": "", "version": ""}

    return {"id": distro.id().lower(), "version": distro.version()}


def calculate_platform():
    """
    Determines the host platform and returns it as a string.
    Includes logic for Linux ARM, Linux x64, macOS (Intel and ARM), and Windows (32-bit and 64-bit).

    Returns:
            str: The detected platform string (e.g., 'linux64', 'mac-arm64', etc.).
    """
    system = platform.system().lower()
    arch = platform.machine().lower()

    # Handle Linux ARM-specific logic
    if system == "linux" and arch == "aarch64":
        distro_info = get_linux_distribution_info()
        distro_id = distro_info.get("id", "")
        version = distro_info.get("version", "")
        major_version = int(version.split(".")[0]) if version else 0

        if distro_id == "ubuntu":
            if major_version < 20:
                return "ubuntu18.04-arm64"
            if major_version < 22:
                return "ubuntu20.04-arm64"
            if major_version < 24:
                return "ubuntu22.04-arm64"
            if major_version < 26:
                return "ubuntu24.04-arm64"
            return "<unknown>"

        if distro_id in ["debian", "raspbian"]:
            if major_version < 11:
                return "debian10-arm64"
            if major_version < 12:
                return "debian11-arm64"
            return "debian12-arm64"
        return "<unknown>"

    # Handle other platforms
    elif system == "linux" and arch == "x86_64":
        return "linux64"
    elif system == "darwin" and arch == "arm64":
        return "mac-arm64"
    elif system == "darwin" and arch == "x86_64":
        return "mac-x64"
    elif system == "windows" and arch == "x86":
        return "win32"
    elif system == "windows" and arch == "x86_64":
        return "win64"

    return "<unknown>"


def remove_chrome_pdf_generator_option():
    set_pdf_generator_option("remove")


def add_weasyprint_pdf_generator_option():
    """Add WeasyPrint to PDF Generator options if available"""
    try:
        import weasyprint

        set_pdf_generator_option("add")
        click.echo("Added WeasyPrint to PDF Generator options")
    except ImportError:
        click.echo(
            "WeasyPrint not available, skipping addition to PDF Generator options"
        )


def set_wkhtmltopdf_as_default_for_print_designer():
    """Set wkhtmltopdf as default PDF generator for all Print Designer formats"""
    try:
        # Update all existing Print Designer formats to use wkhtmltopdf
        print_designer_formats = frappe.get_all(
            "Print Format",
            filters={"print_designer": 1},
            fields=["name", "pdf_generator"],
        )

        for format_doc in print_designer_formats:
            try:
                frappe.db.set_value(
                    "Print Format", format_doc.name, "pdf_generator", "wkhtmltopdf"
                )
                click.echo(
                    f"Set wkhtmltopdf PDF generator for Print Designer format: {format_doc.name}"
                )
            except Exception as e:
                click.echo(f"Failed to update format '{format_doc.name}': {str(e)}")

        frappe.db.commit()
        if print_designer_formats:
            click.echo(
                f"Updated {len(print_designer_formats)} Print Designer formats to use wkhtmltopdf PDF generator"
            )
    except Exception as e:
        click.echo(
            f"Error setting wkhtmltopdf as default for Print Designer formats: {str(e)}"
        )


def set_wkhtmltopdf_for_print_designer_format(doc, method):
    """Set appropriate PDF generator for Print Designer formats"""
    if doc.print_designer:
        # If no generator specified, set a default (prefer WeasyPrint if available)
        if not doc.pdf_generator:
            try:
                import weasyprint

                doc.pdf_generator = "WeasyPrint"
            except ImportError:
                doc.pdf_generator = "wkhtmltopdf"

        # Validate that the selected generator is supported
        supported_generators = ["wkhtmltopdf", "WeasyPrint", "chrome"]
        if doc.pdf_generator not in supported_generators:
            # Fallback to wkhtmltopdf for unsupported generators
            doc.pdf_generator = "wkhtmltopdf"


def set_pdf_generator_option(action: Literal["add", "remove"]):
    options = (
        frappe.get_meta("Print Format").get_field("pdf_generator").options
    ).split("\n")

    if action == "add":
        # Add WeasyPrint if not already present
        if "WeasyPrint" not in options:
            options.append("WeasyPrint")
    elif action == "remove":
        if "chrome" in options:
            options.remove("chrome")

    make_property_setter(
        "Print Format",
        "pdf_generator",
        "options",
        "\n".join(options),
        "Text",
        validate_fields_for_doctype=False,
    )


def setup_print_designer_settings():
    """Setup default print designer settings for copy functionality"""

    try:
        # Get or create Print Settings single
        print_settings = frappe.get_single("Print Settings")

        # Set default values if not already set
        if not print_settings.get("enable_multiple_copies"):
            print_settings.enable_multiple_copies = 1  # Enable by default

        if not print_settings.get("default_copy_count"):
            print_settings.default_copy_count = 2

        if not print_settings.get("default_original_label"):
            print_settings.default_original_label = frappe._("Original")

        if not print_settings.get("default_copy_label"):
            print_settings.default_copy_label = frappe._("Copy")

        if not print_settings.get("show_copy_controls_in_toolbar"):
            print_settings.show_copy_controls_in_toolbar = 1

        # Save the settings
        print_settings.flags.ignore_permissions = True
        print_settings.save()

        click.echo("Print Designer copy settings configured successfully")

    except Exception as e:
        click.echo(f"Error setting up Print Designer settings: {str(e)}")
        # Don't fail installation for this
        pass


def ensure_custom_fields():
    """Ensure print_designer custom fields are installed after migration.

    This function runs after every migration to make sure that custom fields
    like 'print_designer_template_app' are always present, even on fresh
    installations or user machines.
    """
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

        from print_designer.custom_fields import CUSTOM_FIELDS

        # Check if print_designer_template_app field exists
        existing_field = frappe.db.get_value(
            "Custom Field", {"fieldname": "print_designer_template_app"}, "name"
        )

        if not existing_field:
            click.echo("Installing missing print_designer custom fields...")
            create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
            frappe.db.commit()
            click.echo("✅ Print Designer custom fields installed successfully")

        # Also ensure signature enhancement fields are installed
        _ensure_signature_fields()

        # Ensure watermark fields are installed
        _ensure_watermark_fields()

        # Ensure watermark field defaults are set
        _ensure_watermark_defaults()

    except Exception as e:
        # Log error but don't fail migration
        frappe.log_error(f"Error ensuring print_designer custom fields: {str(e)}")
        click.echo(
            f"⚠️  Warning: Could not install print_designer custom fields: {str(e)}"
        )


def _ensure_signature_fields():
    """Ensure signature enhancement fields are installed for dropdown functionality."""
    try:
        # Check if signature_target_field exists
        existing_signature_field = frappe.db.get_value(
            "Custom Field",
            {
                "fieldname": "signature_target_field",
                "dt": "Signature Basic Information",
            },
            "name",
        )

        if not existing_signature_field:
            click.echo("Installing signature enhancement fields...")

            # Install the signature enhancement fields
            from print_designer.api.safe_install import (
                safe_install_signature_enhancements,
            )

            result = safe_install_signature_enhancements()

            if result.get("success"):
                click.echo("✅ Signature enhancement fields installed successfully")
            else:
                click.echo(
                    f"⚠️  Warning: {result.get('error', 'Unknown error installing signature fields')}"
                )

    except Exception as e:
        frappe.log_error(f"Error ensuring signature fields: {str(e)}")
        click.echo(f"⚠️  Warning: Could not install signature fields: {str(e)}")


def _ensure_watermark_fields():
    """Ensure watermark fields are installed across all DocTypes for dynamic watermark selection."""
    try:
        from print_designer.watermark_fields import install_watermark_fields

        # Check if any watermark fields exist
        existing_watermark_field = frappe.db.get_value(
            "Custom Field", {"fieldname": "watermark_text"}, "name"
        )

        if not existing_watermark_field:
            click.echo("Installing watermark fields across DocTypes...")
            success = install_watermark_fields()

            if success:
                frappe.db.commit()
                click.echo("✅ Watermark fields installed successfully")
            else:
                click.echo("⚠️  Warning: Could not install all watermark fields")
        else:
            click.echo("Watermark fields already exist, skipping installation")

    except Exception as e:
        frappe.log_error(f"Error ensuring watermark fields: {str(e)}")
        click.echo(f"⚠️  Warning: Could not install watermark fields: {str(e)}")


def _ensure_watermark_defaults():
    """Set defaults for watermark configuration fields"""
    try:
        print_settings = frappe.get_single("Print Settings")

        # Set defaults if fields are empty
        if not print_settings.get("watermark_font_size"):
            print_settings.watermark_font_size = 12

        if not print_settings.get("watermark_position"):
            print_settings.watermark_position = "Top Right"

        if not print_settings.get("watermark_font_family"):
            print_settings.watermark_font_family = "Sarabun"

        print_settings.save()
        click.echo("✅ Watermark field defaults set successfully")
    except Exception as e:
        frappe.log_error(f"Error setting watermark defaults: {str(e)}")
        click.echo(f"⚠️  Warning: Could not set watermark defaults: {str(e)}")


def install_watermark_field():
    """Install watermark_settings field in Print Settings for sidebar functionality."""
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

        from print_designer.custom_fields import CUSTOM_FIELDS

        click.echo("Installing watermark_settings field...")
        create_custom_fields(CUSTOM_FIELDS, update=True)
        frappe.db.commit()

        # Verify installation
        cf = frappe.db.get_value(
            "Custom Field",
            {"dt": "Print Settings", "fieldname": "watermark_settings"},
            "name",
        )
        if cf:
            click.echo("✅ Watermark field installed successfully in Print Settings")
        else:
            click.echo("⚠️  Warning: Watermark field not found after installation")

        # Clear cache to refresh meta
        frappe.clear_cache(doctype="Print Settings")

    except Exception as e:
        frappe.log_error(f"Error installing watermark field: {str(e)}")
        click.echo(f"⚠️  Error installing watermark field: {str(e)}")


def _install_watermark_fields_on_install():
    """Install watermark fields during fresh installation"""
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

        from print_designer.watermark_fields import get_watermark_custom_fields

        custom_fields = get_watermark_custom_fields()
        create_custom_fields(custom_fields, update=True)
        frappe.db.commit()
        click.echo("✅ Watermark fields installed during installation")

    except Exception as e:
        click.echo(
            f"⚠️  Warning: Could not install watermark fields during installation: {str(e)}"
        )
        frappe.log_error(f"Error installing watermark fields on install: {str(e)}")


def set_wkhtmltopdf_for_print_designer_format(doc, method):
    """Set pdf_generator to wkhtmltopdf for print_designer formats if not set."""
    if doc.print_designer and not doc.pdf_generator:
        doc.pdf_generator = "wkhtmltopdf"


def handle_erpnext_override(app_name):
    """Handle ERPNext integration after app installation"""
    if app_name == "erpnext":
        frappe.logger().info("ERPNext detected - ensuring Print Settings integration")
        # Since we install after ERPNext, just ensure our fields exist
        setup_enhanced_print_settings()
        frappe.logger().info("ERPNext integration completed successfully")
