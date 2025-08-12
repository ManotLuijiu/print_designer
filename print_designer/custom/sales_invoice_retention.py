"""
Sales Invoice Retention Calculation
Backend handler for retention field calculations
"""

import frappe


def install_retention_client_script():
    """Install client script for retention field visibility"""
    try:
        # Check if the client script already exists
        if frappe.db.exists('Client Script', {'name': 'Sales Invoice Retention Fields'}):
            print("✅ Retention client script already exists")
            return
        
        client_script = frappe.get_doc({
            'doctype': 'Client Script',
            'name': 'Sales Invoice Retention Fields',
            'dt': 'Sales Invoice',
            'view': 'Form',
            'module': 'Print Designer',
            'enabled': 1,
            'script': """
// Client script for retention fields - single API call with caching
frappe.ui.form.on('Sales Invoice', {
    setup: function(frm) {
        // Initialize cache
        frm.retention_company_cache = {};
    },
    
    refresh: function(frm) {
        console.log('🔄 Retention Client Script: refresh event');
        setup_retention_fields(frm);
    },
    
    company: function(frm) {
        console.log('🏢 Retention Client Script: company changed to', frm.doc.company);
        // Clear cache when company changes
        frm.retention_company_cache = {};
        setup_retention_fields(frm);
    }
});

function setup_retention_fields(frm) {
    if (!frm.doc.company) {
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], false);
        return;
    }
    
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
        frm.retention_company_cache[company_name] = is_enabled;
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], is_enabled);
        console.log('✅ Cached retention setting for', company_name, ':', is_enabled);
        
        if (!is_enabled) {
            frm.set_value('custom_retention', 0);
            frm.set_value('custom_retention_amount', 0);
        }
    });
}
"""
        })
        
        client_script.insert()
        frappe.db.commit()
        print("✅ Created Sales Invoice Retention Client Script")
        
    except Exception as e:
        print(f"❌ Error installing retention client script: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Retention Client Script Installation Error")


def calculate_retention_on_save(doc, method):
    """
    Calculate retention amount when Sales Invoice is saved.
    This replaces the frontend calculation to improve performance.
    """
    # Only process if company has construction service enabled
    if not doc.company:
        return
        
    # Check if construction service is enabled for this company
    company_doc = frappe.get_cached_doc('Company', doc.company)
    if not getattr(company_doc, 'construction_service', False):
        # Clear retention fields if construction service is disabled
        doc.custom_retention = 0
        doc.custom_retention_amount = 0
        return
        
    # Calculate retention amount if retention percentage is set
    if doc.custom_retention and doc.base_net_total:
        retention_amount = (doc.base_net_total * doc.custom_retention) / 100
        doc.custom_retention_amount = retention_amount
    else:
        doc.custom_retention_amount = 0


def validate_retention_fields(doc, method):
    """
    Validate retention fields during document validation.
    Ensures retention fields are properly calculated before saving.
    """
    calculate_retention_on_save(doc, method)