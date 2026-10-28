// Thailand Withholding Tax Client Script for Sales Order
// Populates server-side fields needed for depends_on conditions

frappe.ui.form.on('Sales Order', {
    // Populate Company fields when company is selected
    company: function(frm) {
        if (frm.doc.company) {
            // Get Company configuration and populate fields for depends_on visibility
            frappe.db.get_value('Company', frm.doc.company, [
                'thailand_service_business', 
                'construction_service'
            ]).then(r => {
                if (r.message) {
                    // Populate fields silently for depends_on conditions
                    frm.doc.thailand_service_business = r.message.thailand_service_business || 0;
                    frm.doc.construction_service = r.message.construction_service || 0;
                    
                    // Refresh the form to trigger depends_on evaluation
                    frm.refresh();
                    
                    console.log('Thailand WHT: Company fields populated', {
                        thailand_service_business: frm.doc.thailand_service_business,
                        construction_service: frm.doc.construction_service
                    });
                }
            });
        } else {
            // Clear fields when company is cleared
            frm.doc.thailand_service_business = 0;
            frm.doc.construction_service = 0;
            frm.refresh();
        }
    },
    
    // Also populate on form load if company is already set
    refresh: function(frm) {
        // Only populate if fields haven't been fetched yet (undefined)
        // Check for undefined specifically, not falsy values (0 is valid)
        if (frm.doc.company && 
            frm.doc.thailand_service_business === undefined && 
            frm.doc.construction_service === undefined) {
            // Trigger company event to populate fields
            frm.events.company(frm);
        }

        // Keep "Subject to Withholding Tax" in sync with the item groups
        pd_apply_subject_to_wht_from_items(frm);
    },
    
    // Keep the WHT preview section in sync when the flag is toggled manually
    pd_custom_subject_to_wht: function(frm) {
        pd_sync_wht_preview_section(frm);
    },

    // Handle WHT income type changes for description updates (language-aware)
    pd_custom_wht_income_type: function(frm) {
        if (frm.doc.pd_custom_wht_income_type && frm.doc.pd_custom_subject_to_wht) {
            // The field links to "Tax Withholding Category" - fetch the
            // description from the category (Thai / English label)
            pd_set_wht_description(frm);
        } else if (!frm.doc.pd_custom_wht_income_type) {
            frm.set_value('pd_custom_wht_description', '');
        }
    }
});

// Auto-set VAT Treatment from item service flag
frappe.ui.form.on('Sales Order Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.item_code) {
            pd_check_single_item_vat(frm, row.item_code);
            pd_apply_subject_to_wht_from_items(frm);
            // Fill the WHT income type / rate from the item master
            pd_apply_item_wht_config(frm);
        }
    },
    items_remove: function(frm) {
        setTimeout(() => pd_check_vat_treatment_from_items(frm), 100);
        // Re-sync the WHT flag and the WHT preview section with the remaining items
        pd_apply_subject_to_wht_from_items(frm);
        // Re-sync the WHT income type / rate with the remaining items
        pd_apply_item_wht_config(frm);
    }
});