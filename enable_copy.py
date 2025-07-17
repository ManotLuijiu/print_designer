import frappe

def enable_copy_functionality():
    print_settings = frappe.get_single("Print Settings")
    print_settings.enable_multiple_copies = 1
    print_settings.default_copy_count = 2
    print_settings.default_original_label = "Original"
    print_settings.default_copy_label = "Copy"
    print_settings.show_copy_controls_in_toolbar = 1
    print_settings.flags.ignore_permissions = True
    print_settings.save()
    print("Copy functionality enabled successfully")

enable_copy_functionality()