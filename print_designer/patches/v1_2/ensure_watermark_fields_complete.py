import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """
    Comprehensive watermark field installation patch.
    This ensures ALL watermark fields are properly installed including:
    1. Document-level watermark_text fields (Stock Entry, Sales Invoice, etc.)
    2. Print Format watermark settings
    3. Print Settings watermark configuration
    
    This patch is idempotent and safe to run multiple times.
    """
    try:
        frappe.logger().info("Running comprehensive watermark field installation...")
        
        # Step 1: Install document-level watermark fields
        install_document_watermark_fields()
        
        # Step 2: Install Print Format watermark settings
        install_print_format_watermark_fields()
        
        # Step 3: Install Print Settings watermark configuration
        install_print_settings_watermark_fields()
        
        # Step 4: Verify critical fields and fix any issues
        verify_and_fix_critical_fields()
        
        # Step 5: Set default values
        set_watermark_defaults()
        
        # Commit all changes
        frappe.db.commit()
        
        frappe.logger().info("✅ Comprehensive watermark field installation completed successfully")
        print("✅ Watermark fields installation completed. Stock Entry error should be resolved.")
        
    except Exception as e:
        frappe.log_error(f"Error in comprehensive watermark field installation: {str(e)}")
        print(f"❌ Error installing watermark fields: {str(e)}")
        # Don't raise exception - allow migration to continue


def install_document_watermark_fields():
    """Install watermark_text fields on all document types"""
    try:
        from print_designer.watermark_fields import get_watermark_custom_fields
        
        frappe.logger().info("Installing document-level watermark fields...")
        
        # Get all watermark field definitions
        custom_fields = get_watermark_custom_fields()
        
        # Log which DocTypes will get watermark fields
        doctypes = list(custom_fields.keys())
        frappe.logger().info(f"Installing watermark fields for {len(doctypes)} DocTypes: {doctypes}")
        
        # Create the custom fields (update=True ensures existing fields are updated)
        create_custom_fields(custom_fields, update=True)
        
        # Verify Stock Entry specifically since that's what had the error
        verify_stock_entry_watermark_field()
        
        frappe.logger().info("✅ Document watermark fields installed successfully")
        
    except Exception as e:
        frappe.log_error(f"Error installing document watermark fields: {str(e)}")
        raise


def verify_stock_entry_watermark_field():
    """Specifically verify Stock Entry has watermark_text field"""
    try:
        # Check if the field exists in Custom Field
        field_exists = frappe.db.exists("Custom Field", {
            "dt": "Stock Entry",
            "fieldname": "watermark_text"
        })
        
        if field_exists:
            frappe.logger().info("✅ Stock Entry watermark_text field exists in Custom Field")
        else:
            frappe.logger().warning("⚠️ Stock Entry watermark_text field NOT found in Custom Field - creating it")
            # Create it directly
            from print_designer.watermark_fields import WATERMARK_FIELDS
            
            if "Stock Entry" in WATERMARK_FIELDS:
                create_custom_fields({
                    "Stock Entry": WATERMARK_FIELDS["Stock Entry"]
                }, update=True)
                frappe.logger().info("✅ Created Stock Entry watermark_text field")
        
        # Verify the column exists in the database table
        columns = frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'")
        if columns:
            frappe.logger().info("✅ Stock Entry watermark_text column exists in database")
        else:
            frappe.logger().warning("⚠️ Stock Entry watermark_text column missing in database - running migrate")
            # Force column creation
            frappe.db.add_column("Stock Entry", "watermark_text", "varchar(140)")
            frappe.logger().info("✅ Added watermark_text column to Stock Entry table")
            
    except Exception as e:
        frappe.log_error(f"Error verifying Stock Entry watermark field: {str(e)}")


def install_print_format_watermark_fields():
    """Install watermark settings field for Print Format"""
    try:
        frappe.logger().info("Installing Print Format watermark fields...")
        
        custom_fields = {
            "Print Format": [
                {
                    "depends_on": "eval:doc.print_designer",
                    "fieldname": "watermark_settings",
                    "fieldtype": "Select",
                    "label": "Watermark per Page",
                    "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                    "default": "None",
                    "insert_after": "print_designer_template_app",
                    "description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'"
                }
            ]
        }
        
        create_custom_fields(custom_fields, update=True)
        frappe.logger().info("✅ Print Format watermark fields installed")
        
    except Exception as e:
        frappe.log_error(f"Error installing Print Format watermark fields: {str(e)}")


def install_print_settings_watermark_fields():
    """Install watermark configuration fields for Print Settings"""
    try:
        frappe.logger().info("Installing Print Settings watermark fields...")
        
        custom_fields = {
            "Print Settings": [
                {
                    "label": "Copy Settings",
                    "fieldname": "copy_settings_section",
                    "fieldtype": "Section Break",
                    "insert_after": "print_taxes_with_zero_amount",
                    "collapsible": 1,
                },
                {
                    "label": "Enable Multiple Copies",
                    "fieldname": "enable_multiple_copies",
                    "fieldtype": "Check",
                    "default": "0",
                    "insert_after": "copy_settings_section",
                    "description": "Enable multiple copy generation for print formats",
                },
                {
                    "label": "Show Copy Controls in Toolbar",
                    "fieldname": "show_copy_controls_in_toolbar",
                    "fieldtype": "Check",
                    "default": "1",
                    "insert_after": "enable_multiple_copies",
                    "depends_on": "enable_multiple_copies",
                    "description": "Show copy controls in print preview toolbar",
                },
                {
                    "label": "Watermark Settings",
                    "fieldname": "watermark_settings_section",
                    "fieldtype": "Section Break",
                    "insert_after": "show_copy_controls_in_toolbar",
                    "collapsible": 1,
                },
                {
                    "label": "Watermark per Page",
                    "fieldname": "watermark_settings",
                    "fieldtype": "Select",
                    "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
                    "default": "None",
                    "insert_after": "watermark_settings_section",
                    "description": "Control watermark display",
                },
                {
                    "label": "Watermark Font Size (px)",
                    "fieldname": "watermark_font_size",
                    "fieldtype": "Int",
                    "default": "24",
                    "insert_after": "watermark_settings",
                    "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                    "description": "Font size for watermark text in pixels",
                },
                {
                    "label": "Watermark Position",
                    "fieldname": "watermark_position",
                    "fieldtype": "Select",
                    "options": "Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right",
                    "default": "Top Right",
                    "insert_after": "watermark_font_size",
                    "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                    "description": "Position of watermark text on the page",
                },
                {
                    "label": "Watermark Font Family",
                    "fieldname": "watermark_font_family",
                    "fieldtype": "Select",
                    "options": "Arial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri\nSarabun\nKanit\nNoto Sans Thai",
                    "default": "Arial",
                    "insert_after": "watermark_position",
                    "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
                    "description": "Font family for watermark text",
                },
            ]
        }
        
        create_custom_fields(custom_fields, update=True)
        frappe.logger().info("✅ Print Settings watermark fields installed")
        
    except Exception as e:
        frappe.log_error(f"Error installing Print Settings watermark fields: {str(e)}")


def verify_and_fix_critical_fields():
    """Verify critical watermark fields exist and fix any issues"""
    try:
        frappe.logger().info("Verifying critical watermark fields...")
        
        # List of critical DocTypes that commonly have watermark issues
        critical_doctypes = [
            "Stock Entry",
            "Sales Invoice", 
            "Purchase Invoice",
            "Delivery Note",
            "Sales Order",
            "Purchase Order",
            "Payment Entry",
            "Journal Entry",
            "Quotation"
        ]
        
        for doctype in critical_doctypes:
            # Check if Custom Field exists
            field_exists = frappe.db.exists("Custom Field", {
                "dt": doctype,
                "fieldname": "watermark_text"
            })
            
            if not field_exists:
                frappe.logger().warning(f"⚠️ {doctype} missing watermark_text field - fixing...")
                # Create the field
                from print_designer.watermark_fields import WATERMARK_FIELDS
                
                if doctype in WATERMARK_FIELDS:
                    create_custom_fields({
                        doctype: WATERMARK_FIELDS[doctype]
                    }, update=True)
                    frappe.logger().info(f"✅ Created watermark_text field for {doctype}")
            
            # Verify column exists in database
            try:
                columns = frappe.db.sql(f"SHOW COLUMNS FROM `tab{doctype}` LIKE 'watermark_text'")
                if not columns:
                    frappe.logger().warning(f"⚠️ {doctype} missing watermark_text column - adding...")
                    frappe.db.add_column(doctype, "watermark_text", "varchar(140)")
                    frappe.logger().info(f"✅ Added watermark_text column to {doctype}")
            except Exception as e:
                frappe.logger().error(f"Could not verify/add column for {doctype}: {str(e)}")
        
        frappe.logger().info("✅ Critical field verification completed")
        
    except Exception as e:
        frappe.log_error(f"Error verifying critical fields: {str(e)}")


def set_watermark_defaults():
    """Set default values for watermark fields"""
    try:
        frappe.logger().info("Setting watermark default values...")
        
        print_settings = frappe.get_single("Print Settings")
        
        defaults = {
            'watermark_font_size': 24,
            'watermark_position': 'Top Right',
            'watermark_font_family': 'Arial',
            'watermark_settings': 'None',
            'enable_multiple_copies': 0,
            'show_copy_controls_in_toolbar': 1
        }
        
        updated = False
        for field, default_value in defaults.items():
            if not print_settings.get(field):
                print_settings.set(field, default_value)
                updated = True
        
        if updated:
            print_settings.flags.ignore_permissions = True
            print_settings.flags.ignore_mandatory = True
            print_settings.save()
            frappe.logger().info("✅ Watermark default values set")
        
    except Exception as e:
        frappe.log_error(f"Error setting watermark defaults: {str(e)}")