// Thailand Withholding Tax Client Script for Quotation
// Calculates estimated WHT amount for quotations

frappe.ui.form.on('Quotation', {
  subject_to_wht: function(frm) {
    calculate_estimated_wht_amount(frm);
  },
  
  grand_total: function(frm) {
    if (frm.doc.subject_to_wht) {
      calculate_estimated_wht_amount(frm);
    }
  },
  
  refresh: function(frm) {
    // Show/hide WHT fields based on company setting
    toggle_wht_fields_visibility(frm);
  },
  
  company: function(frm) {
    toggle_wht_fields_visibility(frm);
  }
});

function calculate_estimated_wht_amount(frm) {
  if (!frm.doc.subject_to_wht || !frm.doc.grand_total) {
    frm.set_value('estimated_wht_amount', 0);
    return;
  }
  
  // Call server method to calculate WHT amount
  frappe.call({
    method: 'print_designer.accounting.thailand_wht_integration.calculate_estimated_wht',
    args: {
      base_amount: frm.doc.grand_total,
      wht_rate: 3.0
    },
    callback: function(r) {
      if (r.message) {
        frm.set_value('estimated_wht_amount', r.message);
      }
    }
  });
}

function toggle_wht_fields_visibility(frm) {
  if (!frm.doc.company) return;
  
  // Check if company has Thailand service business enabled
  frappe.db.get_value('Company', frm.doc.company, 'thailand_service_business')
    .then(function(r) {
      const is_enabled = r.message && r.message.thailand_service_business;
      
      // Show/hide WHT fields
      frm.toggle_display(['wht_section', 'subject_to_wht', 'estimated_wht_amount'], is_enabled);
      
      if (!is_enabled) {
        // Clear WHT values if not enabled
        frm.set_value('subject_to_wht', 0);
        frm.set_value('estimated_wht_amount', 0);
      }
    });
}