// Thailand Withholding Tax Client Script for Sales Order
// Calculates estimated WHT amount for sales orders

frappe.ui.form.on('Sales Order', {
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
    
    // Copy WHT settings to Sales Invoice
    if (frm.doc.docstatus === 1 && frm.doc.subject_to_wht) {
      add_wht_action_buttons(frm);
    }
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

function add_wht_action_buttons(frm) {
  // Add button to create Sales Invoice with WHT settings
  frm.add_custom_button(__('Sales Invoice with WHT'), function() {
    create_sales_invoice_with_wht(frm);
  }, __('Create'));
}

function create_sales_invoice_with_wht(frm) {
  // Create sales invoice with WHT fields pre-populated
  frappe.model.open_mapped_doc({
    method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
    frm: frm,
    run_link_triggers: true,
    callback: function(si_doc) {
      // Copy WHT settings from Sales Order
      si_doc.subject_to_wht = frm.doc.subject_to_wht;
      si_doc.estimated_wht_amount = frm.doc.estimated_wht_amount;
      si_doc.wht_certificate_required = 1; // Default to requiring certificate
      
      frappe.msgprint(__('Sales Invoice created with WHT settings from Sales Order.'));
    }
  });
}