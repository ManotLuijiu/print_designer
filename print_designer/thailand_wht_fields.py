# Thailand Withholding Tax Fields Configuration for Print Designer
# This file defines withholding tax fields for Thai service businesses
# Following the same pattern as retention_fields.py for consistency

THAILAND_WHT_FIELDS = {
    # Company Configuration
    "Company": [
        {
            "fieldname": "thailand_service_business",
            "fieldtype": "Check",
            "label": "Thailand Service Business",
            "insert_after": "country",
            "description": "Enable Thailand withholding tax features for service businesses",
            "default": 0,
        },
        {
            "fieldname": "default_wht_rate",
            "fieldtype": "Percent",
            "label": "Default WHT Rate (%)",
            "insert_after": "thailand_service_business",
            "depends_on": "eval:doc.thailand_service_business",
            "description": "Default withholding tax rate for services (e.g., 3% for most services)",
            "default": 3.0,
            "precision": 2,
        },
        {
            "fieldname": "default_wht_account",
            "fieldtype": "Link",
            "label": "Default Withholding Tax Account",
            "options": "Account",
            "insert_after": "default_wht_rate",
            "depends_on": "eval:doc.thailand_service_business",
            "description": "Default account for withholding tax asset (e.g., Withholding Tax Assets)",
        }
    ],
    
    # Sales Documents - Track WHT but don't calculate until payment
    "Quotation": [
        {
            "fieldname": "wht_section",
            "label": "Withholding Tax Details",
            "fieldtype": "Section Break",
            "insert_after": "taxes_and_charges",
            "depends_on": "eval:doc.company",
            "collapsible": 1,
        },
        {
            "fieldname": "subject_to_wht",
            "label": "Subject to Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "wht_section",
            "description": "This quotation is for services subject to withholding tax",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount",
            "fieldtype": "Currency",
            "insert_after": "subject_to_wht",
            "description": "Estimated withholding tax amount (for reference only)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht",
            "label": "Net Total (After WHT)",
            "fieldtype": "Currency",
            "insert_after": "estimated_wht_amount",
            "description": "Net total after adding VAT (7%) and deducting WHT",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht_in_words",
            "label": "Net Total (After WHT) in Words",
            "fieldtype": "Small Text",
            "insert_after": "net_total_after_wht",
            "description": "Net total amount in Thai words",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
        },
    ],
    
    "Item": [
        {
            "fieldname": "is_service_item",
            "label": "Is Service",
            "fieldtype": "Check",
            "insert_after": "is_fixed_asset",
            "description": "Check if this item represents a service (subject to WHT in Thailand)",
            "depends_on": "eval:1",
            "default": 0,
        },
    ],
    
    "Sales Order": [
        {
            "fieldname": "wht_section",
            "label": "Withholding Tax Details", 
            "fieldtype": "Section Break",
            "insert_after": "taxes_and_charges",
            "depends_on": "eval:doc.company",
            "collapsible": 1,
        },
        {
            "fieldname": "subject_to_wht",
            "label": "Subject to Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "wht_section",
            "description": "This sales order is for services subject to withholding tax",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount",
            "fieldtype": "Currency",
            "insert_after": "subject_to_wht",
            "description": "Estimated withholding tax amount (for reference only)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht",
            "label": "Net Total (After WHT)",
            "fieldtype": "Currency",
            "insert_after": "estimated_wht_amount",
            "description": "Net total after adding VAT (7%) and deducting WHT",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht_in_words",
            "label": "Net Total (After WHT) in Words",
            "fieldtype": "Small Text",
            "insert_after": "net_total_after_wht",
            "description": "Net total amount in Thai words",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
        },
    ],
    
    "Sales Invoice": [
        {
            "fieldname": "subject_to_wht",
            "label": "Subject to Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "taxes_and_charges",
            "description": "This invoice is for services subject to withholding tax",
            "depends_on": "eval:doc.company",
            "default": 0,
        },
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount",
            "fieldtype": "Currency",
            "insert_after": "subject_to_wht",
            "description": "Estimated withholding tax amount (will be deducted at payment)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "wht_certificate_required",
            "label": "WHT Certificate Required",
            "fieldtype": "Check",
            "insert_after": "estimated_wht_amount",
            "description": "Customer will provide withholding tax certificate",
            "depends_on": "eval:doc.subject_to_wht",
            "default": 1,
        },
        {
            "fieldname": "net_total_after_wht",
            "label": "Net Total (After WHT)",
            "fieldtype": "Currency",
            "insert_after": "wht_certificate_required",
            "description": "Net total after adding VAT (7%) and deducting WHT",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "net_total_after_wht_in_words",
            "label": "Net Total (After WHT) in Words",
            "fieldtype": "Small Text",
            "insert_after": "net_total_after_wht",
            "description": "Net total amount in Thai words",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.net_total_after_wht",
        },
    ],
    
    # Payment Entry - Where actual WHT is calculated and accounted
    "Payment Entry": [
        {
            "fieldname": "wht_section",
            "label": "Thailand Withholding Tax",
            "fieldtype": "Section Break",
            "insert_after": "references",
            "depends_on": "eval:doc.company && doc.payment_type == 'Receive'",
            "collapsible": 1,
        },
        {
            "fieldname": "apply_wht",
            "label": "Apply Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "wht_section",
            "description": "Apply withholding tax on this payment",
            "depends_on": "eval:doc.company && doc.payment_type == 'Receive'",
            "default": 0,
        },
        {
            "fieldname": "wht_rate",
            "label": "WHT Rate (%)",
            "fieldtype": "Percent",
            "insert_after": "apply_wht",
            "description": "Withholding tax rate (configurable per company)",
            "depends_on": "eval:doc.apply_wht",
            "default": 3.0,
            "precision": 2,
        },
        {
            "fieldname": "wht_amount",
            "label": "WHT Amount",
            "fieldtype": "Currency",
            "insert_after": "wht_rate",
            "description": "Calculated withholding tax amount",
            "read_only": 1,
            "depends_on": "eval:doc.apply_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "wht_account",
            "label": "Withholding Tax Account",
            "fieldtype": "Link",
            "options": "Account",
            "insert_after": "wht_amount",
            "description": "Account to record withholding tax asset",
            "depends_on": "eval:doc.apply_wht",
        },
        {
            "fieldname": "net_payment_amount",
            "label": "Net Payment Amount",
            "fieldtype": "Currency",
            "insert_after": "wht_account",
            "description": "Amount paid after withholding tax deduction",
            "read_only": 1,
            "depends_on": "eval:doc.apply_wht",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "wht_certificate_no",
            "label": "WHT Certificate No.",
            "fieldtype": "Data",
            "insert_after": "net_payment_amount",
            "description": "Withholding tax certificate number",
            "depends_on": "eval:doc.apply_wht",
        },
        {
            "fieldname": "wht_certificate_date",
            "label": "WHT Certificate Date",
            "fieldtype": "Date",
            "insert_after": "wht_certificate_no",
            "description": "Date of withholding tax certificate",
            "depends_on": "eval:doc.apply_wht",
        },
    ],
}

# Function to get all withholding tax fields for installation
def get_thailand_wht_fields():
    """
    Returns all Thailand withholding tax fields in the format expected by Frappe's custom fields system
    """
    return THAILAND_WHT_FIELDS

# Function to get withholding tax fields for a specific DocType
def get_wht_fields_for_doctype(doctype):
    """
    Returns withholding tax fields for a specific DocType
    """
    return THAILAND_WHT_FIELDS.get(doctype, [])

# Function to check if a DocType has withholding tax fields
def has_wht_fields(doctype):
    """
    Check if a DocType has withholding tax fields configured
    """
    return doctype in THAILAND_WHT_FIELDS

# Function to get all DocTypes with withholding tax fields
def get_doctypes_with_wht():
    """
    Returns list of all DocTypes that have withholding tax fields
    """
    return list(THAILAND_WHT_FIELDS.keys())

# Function to install withholding tax fields
def install_thailand_wht_fields():
    """
    Install Thailand withholding tax custom fields for all configured DocTypes
    """
    import frappe
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
    try:
        custom_fields = get_thailand_wht_fields()
        
        # Try the standard bulk creation first
        try:
            # Validate all field values are strings to avoid formatting errors
            for doctype, fields in custom_fields.items():
                for field in fields:
                    for key, value in field.items():
                        if isinstance(value, (int, float)) and key not in ['default', 'precision', 'read_only', 'collapsible']:
                            field[key] = str(value)
            
            create_custom_fields(custom_fields, update=True)
            
        except Exception as bulk_error:
            print(f"⚠️  Bulk creation failed: {bulk_error}")
            print("🔄 Falling back to individual field creation...")
            
            # Fall back to individual field creation
            from frappe.custom.doctype.custom_field.custom_field import create_custom_field
            
            for doctype, fields in custom_fields.items():
                print(f"  📋 Creating {doctype} fields...")
                
                for field_config in fields:
                    fieldname = field_config.get("fieldname", "unknown")
                    
                    # Check if field already exists
                    if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
                        print(f"    ✅ {doctype}.{fieldname} already exists")
                        continue
                    
                    try:
                        field_config["dt"] = doctype
                        create_custom_field(doctype, field_config)
                        print(f"    ✅ Created {doctype}.{fieldname}")
                    except Exception as field_error:
                        print(f"    ❌ Error creating {doctype}.{fieldname}: {field_error}")
                        frappe.log_error(f"Failed to create {doctype}.{fieldname}: {str(field_error)}", "WHT Fields Individual Creation")
        
        print("✅ Custom fields created successfully!")
        print("   - Company: thailand_service_business (checkbox)")
        print("   - Company: default_wht_account (link to Account)")
        print("   - Quotation: subject_to_wht, estimated_wht_amount, net_total_after_wht")
        print("   - Sales Order: subject_to_wht, estimated_wht_amount, net_total_after_wht")
        print("   - Sales Invoice: subject_to_wht, estimated_wht_amount, wht_certificate_required, net_total_after_wht")
        print("   - Payment Entry: apply_wht, wht_rate, wht_amount, wht_account, net_payment_amount, wht_certificate_no, wht_certificate_date")
        
        # Run migration to fix existing installations
        print("\n🔄 Running migration for existing installations...")
        migrate_sales_invoice_wht_fields()
        
        frappe.db.commit()
        print("✅ Thailand withholding tax custom fields installed successfully")
        return True
    except Exception as e:
        print(f"❌ Error installing Thailand withholding tax fields: {str(e)}")
        frappe.log_error(f"Thailand WHT Fields Installation Error: {str(e)}")
        try:
            frappe.db.rollback()
        except:
            pass
        return False

# Function to uninstall withholding tax fields
def uninstall_thailand_wht_fields():
    """
    Remove Thailand withholding tax custom fields from all configured DocTypes
    """
    import frappe
    
    try:
        for doctype, fields in THAILAND_WHT_FIELDS.items():
            for field_config in fields:
                fieldname = field_config["fieldname"]
                
                # Delete custom field if it exists
                if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
                    frappe.delete_doc("Custom Field", frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname}, "name"))
        
        print("✅ Thailand withholding tax custom fields removed successfully")
        return True
    except Exception as e:
        print(f"❌ Error removing Thailand withholding tax fields: {str(e)}")
        return False

# Migration function to update existing installations
def migrate_sales_invoice_wht_fields():
    """
    Migrate Sales Invoice WHT fields to remove wht_section and consolidate into taxes section.
    This function ensures existing installations are updated to the new field structure.
    """
    import frappe
    
    try:
        print("🔄 Migrating Sales Invoice WHT fields...")
        
        # Step 1: Check if wht_section exists
        wht_section_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "wht_section"})
        
        if wht_section_exists:
            print("  📋 Found existing wht_section field - removing...")
            
            # Delete the wht_section field
            frappe.delete_doc("Custom Field", wht_section_exists, ignore_permissions=True)
            print("  ✅ Removed wht_section field")
        else:
            print("  ℹ️  wht_section field not found - already removed")
        
        # Step 2: Update subject_to_wht to insert after taxes_and_charges
        subject_to_wht_exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": "subject_to_wht"})
        
        if subject_to_wht_exists:
            subject_field = frappe.get_doc("Custom Field", subject_to_wht_exists)
            current_insert_after = subject_field.insert_after
            
            if current_insert_after != "taxes_and_charges":
                print(f"  📝 Updating subject_to_wht position: '{current_insert_after}' → 'taxes_and_charges'")
                subject_field.insert_after = "taxes_and_charges"
                subject_field.save(ignore_permissions=True)
                print("  ✅ Updated subject_to_wht field position")
            else:
                print("  ℹ️  subject_to_wht field already in correct position")
        else:
            print("  ⚠️  subject_to_wht field not found - may need full installation")
        
        # Step 3: Commit changes
        frappe.db.commit()
        print("✅ Sales Invoice WHT field migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error during Sales Invoice WHT field migration: {str(e)}")
        frappe.log_error(f"Sales Invoice WHT Migration Error: {str(e)}", "WHT Field Migration")
        try:
            frappe.db.rollback()
        except:
            pass
        return False

# Function to calculate withholding tax amount
def calculate_wht_amount(base_amount, wht_rate=3.0):
    """
    Calculate withholding tax amount based on base amount and rate
    """
    if not base_amount or not wht_rate:
        return 0
    return (base_amount * wht_rate) / 100

# Function to get net amount after WHT deduction
def get_net_amount_after_wht(gross_amount, wht_rate=3.0):
    """
    Calculate net amount after withholding tax deduction
    """
    if not gross_amount:
        return 0
    wht_amount = calculate_wht_amount(gross_amount, wht_rate)
    return gross_amount - wht_amount