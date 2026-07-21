import os
import platform
import shutil
import zipfile
from pathlib import Path
from typing import Literal

import click
import frappe
import requests
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.utils import get_bench_path
from frappe.utils.synchronization import filelock

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
    add_chrome_pdf_generator_option()
    add_weasyprint_pdf_generator_option()
    set_wkhtmltopdf_as_default_for_print_designer()
    setup_enhanced_print_settings()  # Use commands/install_print_settings_fields.py

    # Watermark, signature, and other field installations are now handled by:
    # - commands/install_print_settings_fields.py (Print Settings fields)
    # - hooks.py after_migrate (runs install_print_settings_fields)
    # - commands/install_watermark_fields.py (document watermark fields)

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
        frappe.db.commit()  # Commit to ensure fields are available for subsequent setup steps
        frappe.logger().info("✅ Basic custom fields installed")

        # 2. Install Print Settings (includes watermark, copy, page number)
        setup_enhanced_print_settings()
        frappe.logger().info("✅ Print Settings installed")

        # Other fields handled by hooks.py after_migrate

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

    frappe.logger().info("Post-migration setup completed")


def ensure_all_fields_after_migration():
    """
    Ensure print_designer fields exist after migration.
    Print Settings fields handled by commands/install_print_settings_fields.py
    """
    try:
        frappe.logger().info("Ensuring print_designer fields after migration...")

        # 1. Basic print_designer custom fields
        create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
        frappe.logger().info("✅ Basic custom fields ensured")

        # 2. Enhanced Print Settings fields (includes watermark, copy, page number)
        setup_enhanced_print_settings()
        frappe.logger().info("✅ Enhanced Print Settings ensured")

        # Other field installations handled by hooks.py after_migrate

        frappe.logger().info("🎉 Fields ensured after migration")

    except Exception as e:
        frappe.logger().error(f"❌ Error ensuring fields after migration: {str(e)}")
        pass


def setup_enhanced_print_settings():
    """
    Print Settings setup - delegated to api/print_settings_api.py
    """
    from print_designer.api.print_settings_api import setup_enhanced_print_settings as _setup

    _setup()


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
        if not print_settings.get("watermark_margin_top"):
            print_settings.set("watermark_margin_top", "10mm")
        if not print_settings.get("watermark_margin_bottom"):
            print_settings.set("watermark_margin_bottom", "10mm")
        if not print_settings.get("watermark_margin_left"):
            print_settings.set("watermark_margin_left", "10mm")
        if not print_settings.get("watermark_margin_right"):
            print_settings.set("watermark_margin_right", "10mm")
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


# DEPRECATED - Field ordering handled by commands/install_print_settings_fields.py
# def fix_print_settings_field_ordering():
#     """
#     Fix field ordering issues that might occur after ERPNext migration
#     Ensures proper field sequence in Print Settings
#     """
#     ... moved to commands/install_print_settings_fields.py


def after_app_install():
    """Legacy function for compatibility with after_install hook"""
    # Since this is called during print_designer installation, we don't need app parameter
    # This function was originally meant for installing formats for other apps
    # But when called via after_install hook, we're already installing print_designer
    # So we install default formats for print_designer itself
    install_default_formats(app="print_designer")


@filelock("print_designer_chromium_setup", timeout=1, is_global=True)
def setup_chromium():
    """Setup Chromium at the bench level."""
    # Load Chromium version from common_site_config.json or use default

    try:
        executable = find_or_download_chromium_executable()
    except Exception as e:
        click.echo(f"Failed to setup Chromium: {e}")
        raise RuntimeError(f"Failed to setup Chromium: {e}")

    add_chrome_pdf_generator_option()

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
    bench_path = get_bench_path()
    print(f"bench_path: {bench_path}")
    """Determine the path to the Chromium executable."""
    chromium_dir = os.path.join(bench_path, "chromium")

    platform_name = platform.system().lower()

    if platform_name not in ["linux", "darwin", "windows"]:
        click.echo(f"Unsupported platform: {platform_name}")

    executable_name = FrappePDFGenerator.EXECUTABLE_PATHS.get(platform_name)

    if not executable_name:
        click.echo(f"Chromium executable path not found for platform: {platform_name}")
        raise RuntimeError(f"Unsupported platform for Chromium: {platform_name}")

    # Construct the full path to the executable
    exec_path = Path(chromium_dir).joinpath(*executable_name)
    if not exec_path.exists():
        click.echo("Chromium is not available. downloading...")
        download_chromium()

    if not exec_path.exists():
        click.echo("Error while downloading chrome")

    return str(exec_path)


def download_chromium():
    bench_path = get_bench_path()
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
        with requests.get(download_url, stream=True, timeout=(10, 60), headers=headers) as r:
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
                    os.rename(executable_shell, os.path.join(renamed_dir, "headless_shell"))
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
    playwright_base_url = "https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/"

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


# COMMENTED OUT: Keeping for reference/rollback if needed
# def remove_chrome_pdf_generator_option():
#     set_pdf_generator_option("remove")


def add_chrome_pdf_generator_option():
    """Add Chrome to PDF Generator options (restored from original Frappe)"""
    set_pdf_generator_option("add_chrome")


def add_weasyprint_pdf_generator_option():
    """Add WeasyPrint to PDF Generator options if available"""
    try:
        import weasyprint

        set_pdf_generator_option("add")
        click.echo("Added WeasyPrint to PDF Generator options")
    except ImportError:
        click.echo("WeasyPrint not available, skipping addition to PDF Generator options")


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
                frappe.db.set_value("Print Format", format_doc.name, "pdf_generator", "wkhtmltopdf")
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
        click.echo(f"Error setting wkhtmltopdf as default for Print Designer formats: {str(e)}")


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


def set_pdf_generator_option(action: Literal["add", "remove", "add_chrome"]):
    pdf_generator_field = frappe.get_meta("Print Format").get_field("pdf_generator")
    if not pdf_generator_field or not pdf_generator_field.options:
        click.echo("PDF generator field not found or has no options, skipping update.")
        return

    options = pdf_generator_field.options.split("\n")

    if action == "add":
        # Add WeasyPrint if not already present
        if "WeasyPrint" not in options:
            options.append("WeasyPrint")
    elif action == "add_chrome":
        # Add chrome if not already present (restored from original Frappe)
        if "chrome" not in options:
            options.append("chrome")
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


# DEPRECATED - Use print_designer.api.print_settings_api.setup_enhanced_print_settings
# def setup_enhanced_print_settings():
#     """
#     Consolidated Print Settings setup - delegated to api/print_settings_api.py
#     """
#     from print_designer.api.print_settings_api import setup_enhanced_print_settings as _setup
#     _setup()


def is_erpnext_installed():
    """Check if ERPNext is installed"""
    try:
        import erpnext

        return True
    except ImportError:
        return False


# DEPRECATED - moved to commands/install_print_settings_fields.py
# def monkey_patch_erpnext():
#     """Apply monkey patch to ERPNext if installed"""
#     ... removed

# DEPRECATED - moved to commands/install_print_settings_fields.py
# def setup_print_designer_settings():
#     """Legacy function - now redirects to consolidated function"""
#     ... removed


# DEPRECATED - moved to api/print_settings_api.py
# def ensure_custom_fields():
#     ... moved to commands/install_print_settings_fields.py
