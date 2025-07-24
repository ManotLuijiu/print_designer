#!/usr/bin/env python3
"""
Utility script to install watermark fields for Print Designer on any site.

Usage:
    python install_watermark_for_site.py <site_name>
    
Example:
    python install_watermark_for_site.py soeasy.bunchee.online
"""

import sys
import os

def check_site_has_print_designer(site_name):
    """Check if print_designer app is installed on the site"""
    bench_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, bench_path)
    
    try:
        import frappe
        frappe.init(site_name)
        frappe.connect()
        
        # Check if print_designer is in installed apps
        installed_apps = frappe.get_installed_apps()
        return 'print_designer' in installed_apps
        
    except frappe.exceptions.IncorrectSitePath:
        return False
    except Exception:
        return False

def install_watermark_fields(site_name):
    """Install watermark fields for the specified site"""
    
    # Add the frappe-bench path to sys.path so we can import frappe
    bench_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, bench_path)
    
    try:
        import frappe
        
        # Initialize the site
        frappe.init(site_name)
        frappe.connect()
        
        # Check if print_designer is installed
        if not check_site_has_print_designer(site_name):
            print(f"❌ Error: print_designer app is not installed on site '{site_name}'")
            print(f"Install print_designer first with: bench --site {site_name} install-app print_designer")
            return False
        
        # Import the installation functions
        from print_designer.commands.install_watermark_fields import (
            _install_print_format_watermark_fields,
            _install_print_settings_watermark_fields,
            _install_document_watermark_fields,
            _set_watermark_defaults
        )
        
        print(f"Installing watermark fields for site: {site_name}")
        
        # Run the installation functions
        _install_print_format_watermark_fields()
        _install_print_settings_watermark_fields()
        _install_document_watermark_fields()
        _set_watermark_defaults()
        
        # Commit the changes
        frappe.db.commit()
        
        print("✅ Watermark fields installed successfully!")
        return True
        
    except frappe.exceptions.IncorrectSitePath:
        print(f"❌ Error: Site '{site_name}' does not exist")
        return False
    except Exception as e:
        print(f"❌ Error installing watermark fields: {str(e)}")
        try:
            frappe.db.rollback()
        except:
            pass
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python install_watermark_for_site.py <site_name>")
        print("Example: python install_watermark_for_site.py soeasy.bunchee.online")
        sys.exit(1)
    
    site_name = sys.argv[1]
    success = install_watermark_fields(site_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()