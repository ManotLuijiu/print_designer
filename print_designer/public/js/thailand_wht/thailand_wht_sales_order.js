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
    },
    
    // Handle WHT income type changes for description updates (language-aware)
    wht_income_type: function(frm) {
        if (frm.doc.wht_income_type && frm.doc.subject_to_wht) {
            // Fetch description from Thai WHT Income Type DocType based on user language
            const lang = frappe.boot.lang || 'en';
            const desc_field = lang === 'th' ? 'income_description_th' : 'income_description';
            const category_field = lang === 'th' ? 'income_category_th' : 'income_category';

            frappe.db.get_value('Thai WHT Income Type', frm.doc.wht_income_type,
                [desc_field, category_field, 'tax_rate'], function(r) {
                    if (r) {
                        const category = r[category_field] || '';
                        const description = r[desc_field] || '';
                        const display_text = category ? `${category} - ${description}` : description;
                        frm.set_value('wht_description', display_text);
                    }
                });
        } else if (!frm.doc.wht_income_type) {
            frm.set_value('wht_description', '');
        }
    }
});