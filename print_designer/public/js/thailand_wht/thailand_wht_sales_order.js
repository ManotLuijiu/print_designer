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
    
    // Handle WHT income type changes for description updates
    wht_income_type: function(frm) {
        if (frm.doc.wht_income_type && frm.doc.subject_to_wht) {
            const descriptions = {
                'professional_services': 'ค่าจ้างวิชาชีพ (Professional Services)',
                'rental': 'ค่าเช่า (Rental)',
                'service_fees': 'ค่าบริการ (Service Fees)',
                'construction': 'ค่าก่อสร้าง (Construction)',
                'advertising': 'ค่าโฆษณา (Advertising)',
                'other_services': 'ค่าบริการอื่น ๆ (Other Services)'
            };
            
            frm.set_value('wht_description', descriptions[frm.doc.wht_income_type] || '');
        }
    }
});