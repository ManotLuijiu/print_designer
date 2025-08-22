// Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company Retention Settings", {
    refresh(frm) {
        if (frm.doc.company) {
            frm.add_custom_button(__('Setup for All Companies'), function() {
                frappe.call({
                    method: "print_designer.print_designer.doctype.company_retention_settings.company_retention_settings.setup_retention_for_all_companies",
                    callback: function(r) {
                        frm.refresh();
                    }
                });
            });
        }
        
        // Show retention account filter
        if (frm.doc.company) {
            frm.set_query("retention_account", function() {
                return {
                    "filters": {
                        "company": frm.doc.company,
                        "account_type": ["in", ["Payable", "Current Liability"]]
                    }
                };
            });
        }
    },
    
    company(frm) {
        if (frm.doc.company) {
            // Update retention account filter when company changes
            frm.set_query("retention_account", function() {
                return {
                    "filters": {
                        "company": frm.doc.company,
                        "account_type": ["in", ["Payable", "Current Liability"]]
                    }
                };
            });
            
            // Clear retention account if it doesn't belong to new company
            if (frm.doc.retention_account) {
                frappe.db.get_value('Account', frm.doc.retention_account, 'company')
                    .then(r => {
                        if (r.message.company !== frm.doc.company) {
                            frm.set_value('retention_account', '');
                        }
                    });
            }
        }
    },
    
    construction_service_enabled(frm) {
        if (frm.doc.construction_service_enabled && !frm.doc.default_retention_rate) {
            frm.set_value('default_retention_rate', 5.0);
        }
        
        if (frm.doc.construction_service_enabled && !frm.doc.maximum_retention_rate) {
            frm.set_value('maximum_retention_rate', 10.0);
        }
    },
    
    default_retention_rate(frm) {
        if (frm.doc.default_retention_rate && frm.doc.maximum_retention_rate) {
            if (frm.doc.default_retention_rate > frm.doc.maximum_retention_rate) {
                frappe.msgprint(__("Default Retention Rate should not exceed Maximum Retention Rate"));
            }
        }
    },
    
    maximum_retention_rate(frm) {
        if (frm.doc.default_retention_rate && frm.doc.maximum_retention_rate) {
            if (frm.doc.default_retention_rate > frm.doc.maximum_retention_rate) {
                frappe.msgprint(__("Maximum Retention Rate should not be less than Default Retention Rate"));
            }
        }
    }
});
