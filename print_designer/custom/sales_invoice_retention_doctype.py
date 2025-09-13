"""
Sales Invoice Retention with DocType Integration

This replaces the problematic client script that was causing infinite API loops.
Uses the new Company Retention Settings DocType for stable, cached data access.
"""

import frappe
from frappe import _


def install_sales_invoice_retention_client_script():
    """Install stable Sales Invoice client script using DocType"""
    
    try:
        # Remove old problematic client scripts first
        old_scripts = [
            "Sales Invoice Retention with Default Rate",
            "Sales Invoice Enhanced Retention",
            "Sales Invoice Retention System"
        ]
        
        for script_name in old_scripts:
            if frappe.db.exists("Client Script", script_name):
                frappe.delete_doc("Client Script", script_name)
                print(f"Removed old script: {script_name}")
        
        # Create new stable client script
        client_script = frappe.get_doc({
            "doctype": "Client Script",
            "name": "Sales Invoice Retention - DocType Based",
            "dt": "Sales Invoice", 
            "view": "Form",
            "enabled": 1,
            "script": """
// Sales Invoice Retention - DocType Based (No API loops)
frappe.ui.form.on('Sales Invoice', {
    setup: function(frm) {
        // Initialize retention settings cache
        if (!window.retention_settings_cache) {
            window.retention_settings_cache = {};
        }
    },
    
    refresh: function(frm) {
        setup_retention_fields_stable(frm);
    },
    
    company: function(frm) {
        // Clear company-specific cache and setup
        if (frm.doc.company && window.retention_settings_cache[frm.doc.company]) {
            delete window.retention_settings_cache[frm.doc.company];
        }
        setup_retention_fields_stable(frm);
    },
    
    custom_retention: function(frm) {
        calculate_retention_amount_stable(frm);
    },
    
    base_net_total: function(frm) {
        calculate_retention_amount_stable(frm);
    }
});

function setup_retention_fields_stable(frm) {
    if (!frm.doc.company) {
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], false);
        return;
    }
    
    const company = frm.doc.company;
    
    // Check global cache first
    if (window.retention_settings_cache[company]) {
        const settings = window.retention_settings_cache[company];
        apply_retention_settings(frm, settings);
        return;
    }
    
    // Single API call using DocType method
    frappe.call({
        method: 'print_designer.print_designer.doctype.company_retention_settings.company_retention_settings.get_company_retention_info',
        args: {
            company: company
        },
        callback: function(r) {
            if (r.message) {
                // Cache the settings globally
                window.retention_settings_cache[company] = r.message;
                apply_retention_settings(frm, r.message);
                console.log('✅ Cached retention settings for', company, ':', r.message);
            } else {
                // Hide fields if no settings found
                frm.toggle_display(['custom_retention', 'custom_retention_amount'], false);
            }
        },
        error: function(err) {
            console.error('Error fetching retention settings:', err);
            frm.toggle_display(['custom_retention', 'custom_retention_amount'], false);
        }
    });
}

function apply_retention_settings(frm, settings) {
    const is_enabled = settings.construction_service_enabled;
    
    // Toggle field visibility
    frm.toggle_display(['custom_retention', 'custom_retention_amount'], is_enabled);
    
    if (is_enabled) {
        // Set default retention rate if field is empty
        if (!frm.doc.custom_retention && settings.default_retention_rate) {
            frm.set_value('custom_retention', settings.default_retention_rate);
        }
        
        // Calculate retention amount if needed
        calculate_retention_amount_stable(frm);
        
        // Show retention information in dashboard
        if (settings.default_retention_rate) {
            frm.dashboard.add_comment(__('Default Retention Rate: {0}%', [settings.default_retention_rate]), 'blue', true);
        }
    } else {
        // Clear retention values if not enabled
        if (frm.doc.custom_retention) {
            frm.set_value('custom_retention', 0);
        }
        if (frm.doc.custom_retention_amount) {
            frm.set_value('custom_retention_amount', 0);
        }
    }
}

function calculate_retention_amount_stable(frm) {
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
        frappe.db.commit()
        
        print(f"✅ Created stable client script: {client_script.name}")
        return client_script
        
    except Exception as e:
        frappe.log_error(f"Error installing retention client script: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise


def remove_problematic_client_scripts():
    """Remove all problematic client scripts that cause API loops"""
    
    problematic_scripts = [
        "Sales Invoice Retention with Default Rate",
        "Sales Invoice Enhanced Retention", 
        "Sales Invoice Retention System",
        "Signature Statistics Simple"
    ]
    
    removed_count = 0
    for script_name in problematic_scripts:
        if frappe.db.exists("Client Script", script_name):
            frappe.delete_doc("Client Script", script_name)
            print(f"✅ Removed problematic script: {script_name}")
            removed_count += 1
        else:
            print(f"   Script not found: {script_name}")
    
    frappe.db.commit()
    print(f"🗑️  Removed {removed_count} problematic client scripts")
    return removed_count


def setup_retention_system():
    """Complete setup of the retention system"""
    
    print("🚀 Setting up stable retention system...")
    
    # Step 1: Remove problematic scripts
    remove_problematic_client_scripts()
    
    # Step 2: Install stable script
    install_sales_invoice_retention_client_script()
    
    # Step 3: Create retention settings for all companies
    companies = frappe.get_all("Company", fields=["name"])
    created_count = 0
    
    for company in companies:
        if not frappe.db.exists("Company Retention Settings", company.name):
            try:
                # Check if company has construction_service enabled
                company_doc = frappe.get_doc("Company", company.name)
                construction_enabled = getattr(company_doc, 'construction_service', False)
                
                settings = frappe.get_doc({
                    "doctype": "Company Retention Settings",
                    "company": company.name,
                    "construction_service_enabled": construction_enabled,
                    "default_retention_rate": 5.0,
                    "auto_calculate_retention": 1,
                    "maximum_retention_rate": 10.0
                })
                settings.insert()
                created_count += 1
                print(f"✅ Created retention settings for {company.name}")
                
            except Exception as e:
                print(f"❌ Failed to create settings for {company.name}: {str(e)}")
    
    frappe.db.commit()
    
    print(f"""
🎉 Retention system setup complete!
   - Removed problematic client scripts
   - Installed stable DocType-based client script  
   - Created retention settings for {created_count} companies
   
✅ The infinite API loop should now be resolved!
🔄 Clear browser cache and reload Sales Invoice forms to test.
""")
    
    return True


if __name__ == "__main__":
    setup_retention_system()