"""
Server-side client script for Sales Invoice retention fields
Handles field visibility without API calls
"""

import frappe

def create_sales_invoice_retention_client_script():
    """Create client script for Sales Invoice retention field visibility"""
    
    # Check if the client script already exists
    if frappe.db.exists('Client Script', {'name': 'Sales Invoice Retention Fields'}):
        return
    
    client_script = frappe.get_doc({
        'doctype': 'Client Script',
        'name': 'Sales Invoice Retention Fields',
        'dt': 'Sales Invoice',
        'view': 'Form',
        'module': 'Print Designer',
        'enabled': 1,
        'script': """
// Server-side client script for retention fields - no API calls
frappe.ui.form.on('Sales Invoice', {
    setup: function(frm) {
        // Cache company settings in form to avoid API calls
        frm.retention_company_cache = {};
    },
    
    onload: function(frm) {
        console.log('🔄 Client Script: Sales Invoice loaded');
        setup_retention_fields(frm);
    },
    
    refresh: function(frm) {
        console.log('🔄 Client Script: refresh event');
        setup_retention_fields(frm);
    },
    
    company: function(frm) {
        console.log('🏢 Client Script: company changed to', frm.doc.company);
        // Clear cache when company changes
        frm.retention_company_cache = {};
        setup_retention_fields(frm);
    }
});

function setup_retention_fields(frm) {
    if (!frm.doc.company) {
        // Hide retention fields if no company
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], false);
        return;
    }
    
    // Get company settings from bootinfo or make single call
    const company_name = frm.doc.company;
    
    // Use cached value if available
    if (frm.retention_company_cache[company_name] !== undefined) {
        const is_enabled = frm.retention_company_cache[company_name];
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], is_enabled);
        console.log('✅ Using cached retention setting:', is_enabled);
        return;
    }
    
    // Make single API call and cache result
    frappe.db.get_value('Company', company_name, 'construction_service', function(r) {
        const is_enabled = r && r.construction_service;
        
        // Cache the result
        frm.retention_company_cache[company_name] = is_enabled;
        
        // Show/hide fields
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], is_enabled);
        
        console.log('✅ Cached retention setting for', company_name, ':', is_enabled);
        
        // Clear retention values if not enabled
        if (!is_enabled) {
            frm.set_value('custom_retention', 0);
            frm.set_value('custom_retention_amount', 0);
        }
    });
}
"""
    })
    
    client_script.insert()
    print("✅ Created Sales Invoice Retention Client Script")

def install_retention_client_script():
    """Install the retention client script"""
    try:
        create_sales_invoice_retention_client_script()
        print("✅ Retention client script installation completed")
    except Exception as e:
        print(f"❌ Error installing retention client script: {str(e)}")
        raise