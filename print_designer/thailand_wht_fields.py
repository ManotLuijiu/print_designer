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
            "fieldname": "default_wht_account",
            "fieldtype": "Link",
            "label": "Default Withholding Tax Account",
            "options": "Account",
            "insert_after": "thailand_service_business",
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
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "collapsible": 1,
        },
        {
            "fieldname": "subject_to_wht",
            "label": "Subject to Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "wht_section",
            "description": "This quotation is for services subject to 3% withholding tax",
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "default": 0,
        },
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount (3%)",
            "fieldtype": "Currency",
            "insert_after": "subject_to_wht",
            "description": "Estimated withholding tax amount (for reference only)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "options": "Company:company:default_currency",
        },
    ],
    
    "Sales Order": [
        {
            "fieldname": "wht_section",
            "label": "Withholding Tax Details", 
            "fieldtype": "Section Break",
            "insert_after": "taxes_and_charges",
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "collapsible": 1,
        },
        {
            "fieldname": "subject_to_wht",
            "label": "Subject to Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "wht_section",
            "description": "This sales order is for services subject to 3% withholding tax",
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "default": 0,
        },
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount (3%)",
            "fieldtype": "Currency",
            "insert_after": "subject_to_wht",
            "description": "Estimated withholding tax amount (for reference only)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "options": "Company:company:default_currency",
        },
    ],
    
    "Sales Invoice": [
        {
            "fieldname": "wht_section",
            "label": "Withholding Tax Details",
            "fieldtype": "Section Break", 
            "insert_after": "taxes_and_charges",
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "collapsible": 1,
        },
        {
            "fieldname": "subject_to_wht",
            "label": "Subject to Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "wht_section",
            "description": "This invoice is for services subject to 3% withholding tax",
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "default": 0,
        },
        {
            "fieldname": "estimated_wht_amount",
            "label": "Estimated WHT Amount (3%)",
            "fieldtype": "Currency",
            "insert_after": "subject_to_wht",
            "description": "Estimated withholding tax amount (will be deducted at payment)",
            "read_only": 1,
            "depends_on": "eval:doc.subject_to_wht && doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "options": "Company:company:default_currency",
        },
        {
            "fieldname": "wht_certificate_required",
            "label": "WHT Certificate Required",
            "fieldtype": "Check",
            "insert_after": "estimated_wht_amount",
            "description": "Customer will provide withholding tax certificate",
            "depends_on": "eval:doc.subject_to_wht && doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business')",
            "default": 1,
        },
    ],
    
    # Payment Entry - Where actual WHT is calculated and accounted
    "Payment Entry": [
        {
            "fieldname": "wht_section",
            "label": "Thailand Withholding Tax",
            "fieldtype": "Section Break",
            "insert_after": "references",
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business') && doc.payment_type == 'Receive'",
            "collapsible": 1,
        },
        {
            "fieldname": "apply_wht",
            "label": "Apply Withholding Tax",
            "fieldtype": "Check",
            "insert_after": "wht_section",
            "description": "Apply 3% withholding tax on this payment",
            "depends_on": "eval:doc.company && frappe.db.get_value('Company', doc.company, 'thailand_service_business') && doc.payment_type == 'Receive'",
            "default": 0,
        },
        {
            "fieldname": "wht_rate",
            "label": "WHT Rate (%)",
            "fieldtype": "Percent",
            "insert_after": "apply_wht",
            "description": "Withholding tax rate (default 3% for services)",
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
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
    try:
        custom_fields = get_thailand_wht_fields()
        create_custom_fields(custom_fields, update=True)
        print("✅ Thailand withholding tax custom fields installed successfully")
        return True
    except Exception as e:
        print(f"❌ Error installing Thailand withholding tax fields: {str(e)}")
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