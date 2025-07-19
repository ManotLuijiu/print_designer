#!/usr/bin/env python3

"""
Enable Print Designer Copy Feature
This script enables the copy functionality in Print Settings for all sites.
"""

import frappe
import frappe.defaults

def enable_copy_feature():
    """Enable copy functionality in Print Settings"""
    
    print("Enabling Print Designer Copy Feature...")
    
    # Get Print Settings
    print_settings = frappe.get_single("Print Settings")
    
    # Enable copy functionality
    if not print_settings.get("enable_multiple_copies"):
        print("- Enabling multiple copies...")
        print_settings.enable_multiple_copies = 1
        print_settings.flags.ignore_permissions = True
        print_settings.save()
        print("✓ Multiple copies enabled")
    else:
        print("✓ Multiple copies already enabled")
    
    # Set default copy count if not set
    if not print_settings.get("default_copy_count"):
        print("- Setting default copy count to 2...")
        print_settings.default_copy_count = 2
        print_settings.flags.ignore_permissions = True
        print_settings.save()
        print("✓ Default copy count set")
    else:
        print(f"✓ Default copy count already set: {print_settings.default_copy_count}")
    
    # Set default labels if not set
    if not print_settings.get("default_original_label"):
        print("- Setting default original label...")
        print_settings.default_original_label = frappe._("Original")
        print_settings.flags.ignore_permissions = True
        print_settings.save()
        print("✓ Default original label set")
    else:
        print(f"✓ Default original label already set: {print_settings.default_original_label}")
    
    if not print_settings.get("default_copy_label"):
        print("- Setting default copy label...")
        print_settings.default_copy_label = frappe._("Copy")
        print_settings.flags.ignore_permissions = True
        print_settings.save()
        print("✓ Default copy label set")
    else:
        print(f"✓ Default copy label already set: {print_settings.default_copy_label}")
    
    # Enable toolbar controls
    if not print_settings.get("show_copy_controls_in_toolbar"):
        print("- Enabling toolbar copy controls...")
        print_settings.show_copy_controls_in_toolbar = 1
        print_settings.flags.ignore_permissions = True
        print_settings.save()
        print("✓ Toolbar copy controls enabled")
    else:
        print("✓ Toolbar copy controls already enabled")
    
    print("\n🎉 Print Designer Copy Feature is now fully enabled!")
    print("\nHow to use:")
    print("1. Go to any document's print preview")
    print("2. Look for copy controls in the top-right toolbar")
    print("3. Adjust copy count using +/- buttons or by typing")
    print("4. Customize labels for 'Original' and 'Copy'")
    print("5. Click 'PDF' to generate multiple copies")
    print("\nNote: Copy functionality works best with wkhtmltopdf generator.")

if __name__ == "__main__":
    enable_copy_feature()