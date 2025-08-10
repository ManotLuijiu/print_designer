"""
Emergency Watermark Fix - Copy and paste this into Frappe Console

To run this fix:
1. Go to your site: https://tipsiricons.bunchee.online/app/dev-console
2. Paste this entire code block and press Enter

This will install the missing watermark_text field on Stock Entry and other DocTypes.
"""

# Install watermark fields directly through console
def fix_watermark_fields():
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        from print_designer.watermark_fields import get_watermark_custom_fields
        
        print("🔧 Installing watermark fields...")
        
        # Get all watermark field definitions
        custom_fields = get_watermark_custom_fields()
        
        print(f"📋 Found {len(custom_fields)} DocTypes with watermark fields")
        print(f"📍 Stock Entry included: {'Stock Entry' in custom_fields}")
        
        # Install the custom fields (this will create database columns)
        create_custom_fields(custom_fields, update=True)
        
        # Commit the database changes
        frappe.db.commit()
        
        print("✅ Watermark fields installed successfully!")
        
        # Verify Stock Entry field was created
        try:
            result = frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'")
            if result:
                print("✅ Confirmed: watermark_text column exists in Stock Entry table")
            else:
                print("❌ Warning: watermark_text column not found in Stock Entry table")
        except:
            print("ℹ️  Could not verify column creation")
            
        return True
        
    except Exception as e:
        print(f"❌ Error installing watermark fields: {str(e)}")
        frappe.db.rollback()
        return False

# Run the fix
fix_watermark_fields()

# Also install Print Settings watermark fields
def install_print_settings_watermark():
    try:
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        
        custom_fields = {
            "Print Settings": [
                {
                    "label": "Watermark Settings",
                    "fieldname": "watermark_settings_section",
                    "fieldtype": "Section Break",
                    "insert_after": "print_taxes_with_zero_amount",
                    "collapsible": 1,
                },
                {
                    "label": "Watermark per Page",
                    "fieldname": "watermark_settings",
                    "fieldtype": "Select",
                    "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                    "default": "None",
                    "insert_after": "watermark_settings_section",
                    "description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'",
                }
            ]
        }
        
        create_custom_fields(custom_fields, update=True)
        frappe.db.commit()
        print("✅ Print Settings watermark fields installed!")
        
    except Exception as e:
        print(f"❌ Error installing Print Settings watermark fields: {str(e)}")

install_print_settings_watermark()

print("\n🎉 Watermark system installation complete!")
print("🔄 Now try saving your Stock Entry again - the error should be resolved.")