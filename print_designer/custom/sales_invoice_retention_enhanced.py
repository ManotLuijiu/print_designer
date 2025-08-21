"""
Enhanced Sales Invoice Retention with Default Rate

Backend handler for retention field calculations using company default rates.
"""

import frappe
from frappe import _


def install_enhanced_retention_client_script():
    """Install enhanced client script for retention field visibility and default rate."""
    
    try:
        # Check if client script already exists
        existing_script = frappe.db.exists("Client Script", {
            "dt": "Sales Invoice",
            "name": ["like", "%Retention%"]
        })
        
        if existing_script:
            frappe.delete_doc("Client Script", existing_script)
        
        # Create new client script for Sales Invoice
        client_script = frappe.get_doc({
            "doctype": "Client Script",
            "name": "Sales Invoice Retention with Default Rate",
            "dt": "Sales Invoice",
            "view": "Form",
            "enabled": 1,
            "script": """
// Enhanced client script for retention fields with default rate
frappe.ui.form.on('Sales Invoice', {
    setup: function(frm) {
        frm.retention_company_cache = {};
        frm.retention_rate_cache = {};
    },
    
    refresh: function(frm) {
        setup_retention_fields(frm);
    },
    
    company: function(frm) {
        // Clear cache when company changes
        frm.retention_company_cache = {};
        frm.retention_rate_cache = {};
        setup_retention_fields(frm);
    },
    
    custom_retention: function(frm) {
        calculate_retention_amount(frm);
    },
    
    base_net_total: function(frm) {
        calculate_retention_amount(frm);
    }
});

function setup_retention_fields(frm) {
    if (!frm.doc.company) {
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], false);
        return;
    }
    
    const company_name = frm.doc.company;
    
    // Check cache first
    if (frm.retention_company_cache[company_name] !== undefined) {
        const is_enabled = frm.retention_company_cache[company_name];
        const default_rate = frm.retention_rate_cache[company_name];
        
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], is_enabled);
        
        // Set default retention rate if field is empty and construction service is enabled
        if (is_enabled && !frm.doc.custom_retention && default_rate) {
            frm.set_value('custom_retention', default_rate);
        }
        
        console.log('✅ Using cached retention settings:', is_enabled, 'Default rate:', default_rate);
        return;
    }
    
    // Single API call to get both construction_service and default_retention_rate
    frappe.db.get_value('Company', company_name, ['construction_service', 'default_retention_rate'])
        .then(r => {
            const is_enabled = r.message.construction_service === 1;
            const default_rate = r.message.default_retention_rate || 5.0;
            
            // Cache the values
            frm.retention_company_cache[company_name] = is_enabled;
            frm.retention_rate_cache[company_name] = default_rate;
            
            // Toggle field visibility
            frm.toggle_display(['custom_retention', 'custom_retention_amount'], is_enabled);
            
            console.log('✅ Cached retention settings for', company_name, ':', is_enabled, 'Default rate:', default_rate);
            
            // Set default retention rate if field is empty and construction service is enabled
            if (is_enabled && !frm.doc.custom_retention) {
                frm.set_value('custom_retention', default_rate);
            }
            
            // Clear retention values if not enabled
            if (!is_enabled && frm.doc.custom_retention) {
                frm.set_value('custom_retention', 0);
                frm.set_value('custom_retention_amount', 0);
            }
        })
        .catch(err => {
            console.error('Error fetching company retention settings:', err);
        });
}

function calculate_retention_amount(frm) {
    if (frm.doc.custom_retention && frm.doc.base_net_total) {
        const retention_amount = (frm.doc.base_net_total * frm.doc.custom_retention) / 100;
        frm.set_value('custom_retention_amount', retention_amount);
    } else {
        frm.set_value('custom_retention_amount', 0);
    }
}
"""
        })
        
        client_script.insert()
        
        print(f"✅ Enhanced retention client script created: {client_script.name}")
        
    except Exception as e:
        print(f"❌ Error installing enhanced retention client script: {str(e)}")
        raise


def calculate_retention_on_save(doc, method):
    """
    Calculate retention amount when Sales Invoice is saved.
    This is a server-side validation to ensure consistency.
    """
    if not doc.company:
        return
    
    # Check if construction service is enabled for the company
    construction_service = frappe.db.get_value("Company", doc.company, "construction_service")
    
    if not construction_service:
        # Clear retention fields if construction service is disabled
        doc.custom_retention = 0
        doc.custom_retention_amount = 0
        return
    
    # If retention percentage is not set, use company default
    if not doc.custom_retention:
        default_rate = frappe.db.get_value("Company", doc.company, "default_retention_rate")
        if default_rate:
            doc.custom_retention = default_rate
    
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