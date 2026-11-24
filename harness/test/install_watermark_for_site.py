#!/usr/bin/env python3
"""Install the watermark fields of the print designer on a site.

The script writes to the site, so it needs the name of the site.

    python harness/test/install_watermark_for_site.py your_site
"""

import sys
from pathlib import Path

# The root of the app, so that the package of the app can be imported.
THE_APP_ROOT = Path(__file__).resolve().parents[2]


def check_site_has_print_designer() -> bool:
    """Whether the site of the current connection has the app of the print designer."""
    import frappe

    return "print_designer" in frappe.get_installed_apps()


def install_watermark_fields(site_name: str) -> bool:
    """Install the watermark fields for the specified site"""
    sys.path.insert(0, str(THE_APP_ROOT))

    import frappe

    try:
        # Initialize the site
        frappe.init(site_name)
        frappe.connect()
    except frappe.exceptions.IncorrectSitePath:
        print(f"❌ Error: Site '{site_name}' does not exist")
        return False

    try:
        # Check if print_designer is installed
        if not check_site_has_print_designer():
            print(f"❌ Error: print_designer app is not installed on site '{site_name}'")
            print(
                f"Install print_designer first with: bench --site {site_name} install-app print_designer"
            )
            return False

        # Import the installation function of the app.
        from print_designer.install import ensure_all_fields_after_migration

        print(f"Installing watermark fields for site: {site_name}")

        # The custom fields and the enhanced Print Settings, which carry the
        # watermark fields, are installed by this function.
        if not ensure_all_fields_after_migration():
            print("❌ Error: the fields of the print designer were not installed")
            frappe.db.rollback()
            return False

        # Commit the changes
        frappe.db.commit()

        print("✅ Watermark fields installed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error installing watermark fields: {str(e)}")
        try:
            frappe.db.rollback()
        except Exception:
            pass
        return False


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python harness/test/install_watermark_for_site.py <site_name>")
        print("Example: python harness/test/install_watermark_for_site.py your_site")
        return 1

    site_name = sys.argv[1]
    success = install_watermark_fields(site_name)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
