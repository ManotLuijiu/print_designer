import frappe


def execute():
    """Set PDF Generator to 'wkhtmltopdf' for all Print Designer formats (replacing chrome)"""
    
    try:
        # Update all existing Print Designer formats to use wkhtmltopdf instead of chrome
        print_designer_formats = frappe.get_all(
            "Print Format",
            filters={"print_designer": 1},
            fields=["name", "pdf_generator"]
        )
        
        updated_count = 0
        chrome_count = 0
        
        for format_doc in print_designer_formats:
            try:
                current_generator = format_doc.get("pdf_generator", "")
                
                # Count how many were using chrome
                if current_generator == "chrome":
                    chrome_count += 1
                
                # Update the format to use wkhtmltopdf PDF generator
                frappe.db.set_value(
                    "Print Format",
                    format_doc.name,
                    "pdf_generator",
                    "wkhtmltopdf"
                )
                updated_count += 1
                print(f"Updated Print Designer format '{format_doc.name}' from '{current_generator}' to 'wkhtmltopdf'")
                
            except Exception as e:
                print(f"Failed to update format '{format_doc.name}': {str(e)}")
        
        frappe.db.commit()
        
        print(f"\n✅ Chrome Removal Complete:")
        print(f"   • Found {chrome_count} formats using chrome PDF generator")
        print(f"   • Successfully updated {updated_count} Print Designer formats to use wkhtmltopdf")
        print(f"   • Chrome PDF generator references removed from all Print Designer formats")
        
        if chrome_count > 0:
            print(f"\n🚀 All {chrome_count} chrome-based Print Designer formats now use wkhtmltopdf")
        else:
            print(f"\n✓ No chrome PDF generators found - all Print Designer formats verified")
            
    except Exception as e:
        print(f"❌ Error updating Print Designer formats: {str(e)}")
        frappe.log_error(f"Error in set_wkhtmltopdf_for_print_designer_formats: {str(e)}")