"""
Sales Invoice Retention with Company Integration

UPDATED: Now reads directly from Company fields instead of Company Retention Settings.
Company Retention Settings DocType is deprecated/redundant as SO/SI calculations
already use Company fields (construction_service, default_retention_rate, default_retention_account).

See: sales_order_calculations.py:64-82, sales_invoice_calculations.py:58-83
"""

import frappe
from frappe import _


def install_sales_invoice_retention_client_script():
    """Install stable Sales Invoice client script using Company fields directly"""

    try:
        # Remove old problematic client scripts first
        old_scripts = [
            "Sales Invoice Retention with Default Rate",
            "Sales Invoice Enhanced Retention",
            "Sales Invoice Retention System",
            "Sales Invoice Retention - DocType Based"  # Remove old DocType-based script
        ]

        for script_name in old_scripts:
            if frappe.db.exists("Client Script", script_name):
                frappe.delete_doc("Client Script", script_name)
                print(f"Removed old script: {script_name}")

        # Create new stable client script reading from Company directly
        client_script = frappe.get_doc({
            "doctype": "Client Script",
            "name": "Sales Invoice Retention - Company Based",
            "dt": "Sales Invoice",
            "view": "Form",
            "enabled": 1,
            "script": """
// Sales Invoice Retention - Company Based (No Company Retention Settings dependency)
// Reads directly from Company fields: construction_service, default_retention_rate
frappe.ui.form.on('Sales Invoice', {
    setup: function(frm) {
        // Initialize company settings cache
        if (!window.company_retention_cache) {
            window.company_retention_cache = {};
        }
    },

    refresh: function(frm) {
        setup_retention_fields_from_company(frm);
    },

    company: function(frm) {
        // Clear company-specific cache and setup
        if (frm.doc.company && window.company_retention_cache[frm.doc.company]) {
            delete window.company_retention_cache[frm.doc.company];
        }
        setup_retention_fields_from_company(frm);
    },

    pd_custom_retention_pct: function(frm) {
        calculate_retention_amount_simple(frm);
    },

    base_net_total: function(frm) {
        calculate_retention_amount_simple(frm);
    }
});

function setup_retention_fields_from_company(frm) {
    if (!frm.doc.company) {
        frm.toggle_display(['pd_custom_retention_pct', 'pd_custom_retention_amount'], false);
        return;
    }

    const company = frm.doc.company;

    // Check global cache first
    if (window.company_retention_cache[company]) {
        const settings = window.company_retention_cache[company];
        apply_retention_settings_from_company(frm, settings);
        return;
    }

    // Fetch directly from Company DocType (no Company Retention Settings dependency)
    frappe.db.get_doc('Company', company).then(company_doc => {
        const settings = {
            construction_service_enabled: company_doc.construction_service || false,
            default_retention_rate: company_doc.default_retention_rate || 5.0,
            retention_account: company_doc.default_retention_account || null
        };

        // Cache the settings globally
        window.company_retention_cache[company] = settings;
        apply_retention_settings_from_company(frm, settings);
        console.log('✅ Cached company retention settings for', company, ':', settings);
    }).catch(err => {
        console.error('Error fetching company:', err);
        frm.toggle_display(['pd_custom_retention_pct', 'pd_custom_retention_amount'], false);
    });
}

function apply_retention_settings_from_company(frm, settings) {
    const is_enabled = settings.construction_service_enabled;

    // Toggle field visibility
    frm.toggle_display(['pd_custom_retention_pct', 'pd_custom_retention_amount'], is_enabled);

    if (is_enabled) {
        // Set default retention rate if field is empty
        if (!frm.doc.pd_custom_retention_pct && settings.default_retention_rate) {
            frm.set_value('pd_custom_retention_pct', settings.default_retention_rate);
        }

        // Calculate retention amount if needed
        calculate_retention_amount_simple(frm);

        // Show retention information in dashboard
        if (settings.default_retention_rate) {
            frm.dashboard.add_comment(__('Default Retention Rate: {0}%', [settings.default_retention_rate]), 'blue', true);
        }
    } else {
        // Clear retention values if not enabled
        if (frm.doc.pd_custom_retention_pct) {
            frm.set_value('pd_custom_retention_pct', 0);
        }
        if (frm.doc.pd_custom_retention_amount) {
            frm.set_value('pd_custom_retention_amount', 0);
        }
    }
}

function calculate_retention_amount_simple(frm) {
    if (frm.doc.pd_custom_retention_pct && frm.doc.base_net_total) {
        const retention_amount = (frm.doc.base_net_total * frm.doc.pd_custom_retention_pct) / 100;
        frm.set_value('pd_custom_retention_amount', retention_amount);
    } else {
        frm.set_value('pd_custom_retention_amount', 0);
    }
}
"""
        })

        client_script.insert()
        frappe.db.commit()

        print(f"✅ Created Company-based client script: {client_script.name}")
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
    """Complete setup of the retention system (Company-based, no Company Retention Settings)"""

    print("🚀 Setting up Company-based retention system...")

    # Step 1: Remove problematic scripts
    remove_problematic_client_scripts()

    # Step 2: Install Company-based script (reads from Company fields directly)
    install_sales_invoice_retention_client_script()

    # NOTE: Company Retention Settings creation REMOVED
    # The retention system now reads directly from Company fields:
    # - construction_service
    # - default_retention_rate
    # - default_retention_account
    # See: sales_order_calculations.py:64-82, sales_invoice_calculations.py:58-83

    frappe.db.commit()

    print("""
🎉 Retention system setup complete!
   - Removed problematic client scripts
   - Installed Company-based client script (reads from Company fields)

✅ Key Changes:
   - NO Company Retention Settings created (redundant DocType)
   - Retention reads directly from Company.construction_service
   - Retention reads directly from Company.default_retention_rate
   - Retention reads directly from Company.default_retention_account

🔄 Clear browser cache and reload Sales Invoice forms to test.
""")

    return True


if __name__ == "__main__":
    setup_retention_system()