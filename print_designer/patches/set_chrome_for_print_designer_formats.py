import frappe


def execute():
    """Set PDF Generator to 'chrome' for all Print Designer formats"""
    
    # Update all existing Print Designer formats to use Chrome
    print_designer_formats = frappe.get_all(
        "Print Format",
        filters={"print_designer": 1},
        fields=["name", "pdf_generator"]
    )
    
    updated_count = 0
    for format_doc in print_designer_formats:
        try:
            # Update the format to use Chrome PDF generator
            frappe.db.set_value(
                "Print Format",
                format_doc.name,
                "pdf_generator",
                "chrome"
            )
            updated_count += 1
            print(f"Updated Print Designer format '{format_doc.name}' to use Chrome PDF generator")
        except Exception as e:
            print(f"Failed to update format '{format_doc.name}': {str(e)}")
    
    frappe.db.commit()
    print(f"Successfully updated {updated_count} Print Designer formats to use Chrome PDF generator")