"""
Install Retention Fields for Construction Services - Restructured for Zero API Loops

Implements the NEW retention system that eliminates infinite API loops by:
1. Removing problematic section-based custom fields with frappe.db.get_value() dependencies
2. Creating 5 new fields directly in the Totals section with simple eval: dependencies  
3. Installing zero-API-call client script for calculations
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def delete_specific_custom_field(doctype, fieldname):
    """Delete a specific custom field from a DocType"""
    try:
        # Find the Custom Field record
        custom_field = frappe.db.get_value(
            "Custom Field", 
            {"dt": doctype, "fieldname": fieldname}, 
            "name"
        )
        
        if custom_field:
            # Delete the Custom Field record
            frappe.delete_doc("Custom Field", custom_field)
            print(f"✅ Deleted Custom Field: {doctype}.{fieldname}")
            frappe.db.commit()
            print("✅ Database committed - field removed")
            return True
        else:
            print(f"❌ Custom Field '{fieldname}' not found in {doctype}")
            return False

    except Exception as e:
        print(f"❌ Error deleting {doctype}.{fieldname}: {str(e)}")
        frappe.db.rollback()
        return False


def install_retention_fields():
    """Install restructured retention fields system to eliminate infinite API loops."""
    
    print("🔄 Installing Restructured Retention Fields (Zero API Loop Architecture)...")
    
    # STEP 1: Remove old problematic fields that cause infinite API loops
    print("\n🗑️ Removing old problematic fields...")
    old_problematic_fields = [
        'retention_section',  # Section with frappe.db.get_value() dependency
        'custom_retention',   # Field with frappe.db.get_value() dependency  
        'withholding_tax_details_section',  # If exists
    ]
    
    for field_name in old_problematic_fields:
        if frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field_name}):
            try:
                frappe.delete_doc("Custom Field", {"dt": "Sales Invoice", "fieldname": field_name})
                print(f"  ✅ Deleted old field: {field_name}")
            except Exception as e:
                # Use direct SQL if normal delete fails
                frappe.db.sql("DELETE FROM `tabCustom Field` WHERE dt='Sales Invoice' AND fieldname=%s", field_name)
                print(f"  ✅ Force deleted: {field_name}")
    
    # STEP 2: Create new restructured fields in Totals section
    print("\n➕ Creating new Totals section fields...")
    
    # Define custom fields - RESTRUCTURED ARCHITECTURE
    custom_fields = {
        "Company": [
            {
                "fieldname": "construction_service",
                "label": "Enable Construction Service", 
                "fieldtype": "Check",
                "insert_after": "country",
                "description": "Enable construction service features including retention calculations",
                "default": 0,
            }
        ],
        "Sales Invoice": [
            # NEW ARCHITECTURE: All 5 fields in Totals section with simple eval: dependencies
            {
                "fieldname": "custom_retention_percent",
                "label": "Retention %",
                "fieldtype": "Percent", 
                "insert_after": "total_taxes_and_charges",
                "depends_on": "eval:doc.company",  # Simple dependency - no API calls
                "description": "Retention percentage to be withheld from payment"
            },
            {
                "fieldname": "custom_retention_amount", 
                "label": "Retention Amount",
                "fieldtype": "Currency",
                "insert_after": "custom_retention_percent", 
                "depends_on": "eval:doc.company && doc.custom_retention_percent",  # Simple eval dependency
                "read_only": 1,
                "description": "Calculated retention amount"
            },
            {
                "fieldname": "custom_withholding_tax_percent",
                "label": "Withholding Tax (%)",
                "fieldtype": "Percent",
                "insert_after": "custom_retention_amount",
                "depends_on": "eval:doc.company",  # Simple dependency - no API calls
                "description": "Withholding tax percentage"
            },
            {
                "fieldname": "custom_withholding_tax_amount",
                "label": "Withholding Tax Amount", 
                "fieldtype": "Currency",
                "insert_after": "custom_withholding_tax_percent",
                "depends_on": "eval:doc.company && doc.custom_withholding_tax_percent",  # Simple eval dependency
                "read_only": 1,
                "description": "Calculated withholding tax amount"
            },
            {
                "fieldname": "custom_payment_amount",
                "label": "Payment Amount",
                "fieldtype": "Currency", 
                "insert_after": "custom_withholding_tax_amount",
                "depends_on": "eval:doc.company",  # Simple dependency - no API calls
                "read_only": 1,
                "description": "Final payment amount after deductions"
            }
        ],
    }
    
    try:
        # Create custom fields
        create_custom_fields(custom_fields, update=True)
        
        print("✅ Restructured custom fields created successfully!")
        print("   - Company: construction_service (checkbox)")
        print("   - Sales Invoice: 5 fields in Totals section:")
        print("     • custom_retention_percent")
        print("     • custom_retention_amount") 
        print("     • custom_withholding_tax_percent")
        print("     • custom_withholding_tax_amount")
        print("     • custom_payment_amount")
        
        # STEP 3: Install zero-API-call client script
        print("\n📜 Installing zero-API-call client script...")
        install_zero_api_client_script()
        
        frappe.db.commit()
        print("✅ Restructured retention fields installation completed!")
        print("\n🎉 Architecture Summary:")
        print("✅ No more separate collapsible sections")  
        print("✅ All fields integrated into native Totals section")
        print("✅ Simple eval: expressions instead of frappe.db.get_value() calls")
        print("✅ Client-side calculations with no server round trips")
        print("✅ Should eliminate infinite API loop completely")
        
    except Exception as e:
        print(f"❌ Error installing restructured retention fields: {str(e)}")
        frappe.db.rollback()
        raise


def install_zero_api_client_script():
    """Install the zero-API-call client script for retention calculations."""
    
    # Remove any existing problematic client scripts first
    old_scripts = [
        "Sales Invoice Retention with Default Rate",
        "Sales Invoice Enhanced Retention", 
        "Sales Invoice Retention System",
        "Sales Invoice Retention - DocType Based"
    ]
    
    for script_name in old_scripts:
        if frappe.db.exists("Client Script", script_name):
            frappe.delete_doc("Client Script", script_name)
            print(f"  🗑️ Removed old script: {script_name}")
    
    # Create or update zero-API-call client script
    script_name = "Sales Invoice Totals Calculations"
    
    if frappe.db.exists("Client Script", script_name):
        client_script = frappe.get_doc("Client Script", script_name)
        print(f"  🔄 Updating existing client script: {script_name}")
    else:
        client_script = frappe.get_doc({
            "doctype": "Client Script",
            "name": script_name,
            "dt": "Sales Invoice",
            "view": "Form", 
            "enabled": 1,
        })
        print(f"  ➕ Creating new client script: {script_name}")
    
    # Set/update the script content
    client_script.script = """
// Sales Invoice Totals Calculations - Zero API calls
frappe.ui.form.on('Sales Invoice', {
    custom_retention_percent: function(frm) {
        calculate_retention_amount(frm);
    },
    
    custom_withholding_tax_percent: function(frm) {
        calculate_withholding_tax_amount(frm);
    },
    
    base_net_total: function(frm) {
        calculate_retention_amount(frm);
        calculate_withholding_tax_amount(frm);
        calculate_payment_amount(frm);
    },
    
    net_total: function(frm) {
        calculate_retention_amount(frm);
        calculate_withholding_tax_amount(frm);
        calculate_payment_amount(frm);
    },
    
    refresh: function(frm) {
        // Recalculate all amounts on form load
        calculate_retention_amount(frm);
        calculate_withholding_tax_amount(frm);
        calculate_payment_amount(frm);
    }
});

function calculate_retention_amount(frm) {
    if (frm.doc.custom_retention_percent && frm.doc.base_net_total) {
        const retention_amount = (frm.doc.base_net_total * frm.doc.custom_retention_percent) / 100;
        frm.set_value('custom_retention_amount', retention_amount);
        calculate_payment_amount(frm);
    } else {
        frm.set_value('custom_retention_amount', 0);
        calculate_payment_amount(frm);
    }
}

function calculate_withholding_tax_amount(frm) {
    if (frm.doc.custom_withholding_tax_percent && frm.doc.base_net_total) {
        const wht_amount = (frm.doc.base_net_total * frm.doc.custom_withholding_tax_percent) / 100;
        frm.set_value('custom_withholding_tax_amount', wht_amount);
        calculate_payment_amount(frm);
    } else {
        frm.set_value('custom_withholding_tax_amount', 0);
        calculate_payment_amount(frm);
    }
}

function calculate_payment_amount(frm) {
    let payment_amount = frm.doc.base_net_total || 0;
    
    // Subtract retention amount
    if (frm.doc.custom_retention_amount) {
        payment_amount -= frm.doc.custom_retention_amount;
    }
    
    // Subtract withholding tax amount
    if (frm.doc.custom_withholding_tax_amount) {
        payment_amount -= frm.doc.custom_withholding_tax_amount;
    }
    
    frm.set_value('custom_payment_amount', payment_amount);
}
"""
    
    # Save the script (this handles both insert and update)
    client_script.save()
    print(f"  ✅ Client script saved successfully: {script_name}")


def check_retention_fields():
    """Check if retention fields are properly installed."""
    
    print("Checking Retention Fields Installation...")
    
    # Check Company field
    company_field = frappe.get_meta("Company").get_field("construction_service")
    if company_field:
        print("✅ Company.construction_service field found")
    else:
        print("❌ Company.construction_service field missing")
    
    # Check Sales Invoice fields
    si_meta = frappe.get_meta("Sales Invoice")
    
    retention_field = si_meta.get_field("custom_retention")
    if retention_field:
        print("✅ Sales Invoice.custom_retention field found")
    else:
        print("❌ Sales Invoice.custom_retention field missing")
    
    retention_amount_field = si_meta.get_field("custom_retention_amount")
    if retention_amount_field:
        print("✅ Sales Invoice.custom_retention_amount field found")
    else:
        print("❌ Sales Invoice.custom_retention_amount field missing")
    
    return bool(company_field and retention_field and retention_amount_field)


if __name__ == "__main__":
    install_retention_fields()