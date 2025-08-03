// Thailand Withholding Tax Client Script for Sales Invoice
// Automatically calculates estimated WHT amount when subject_to_wht is checked

frappe.ui.form.on('Sales Invoice', {
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
    
    // Add custom buttons for WHT-related actions
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
      frm.toggle_display(['wht_section', 'subject_to_wht', 'estimated_wht_amount', 'wht_certificate_required'], is_enabled);
      
      if (!is_enabled) {
        // Clear WHT values if not enabled
        frm.set_value('subject_to_wht', 0);
        frm.set_value('estimated_wht_amount', 0);
        frm.set_value('wht_certificate_required', 0);
      }
    });
}

function add_wht_action_buttons(frm) {
  // Add button to create payment entry with WHT pre-filled
  frm.add_custom_button(__('Payment with WHT'), function() {
    create_payment_with_wht(frm);
  }, __('Create'));
  
  // Add button to view WHT certificate requirements
  frm.add_custom_button(__('WHT Requirements'), function() {
    show_wht_requirements_dialog(frm);
  }, __('Thailand WHT'));
}

function create_payment_with_wht(frm) {
  // Create payment entry with WHT fields pre-populated
  frappe.model.open_mapped_doc({
    method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
    frm: frm,
    run_link_triggers: true,
    callback: function(pe_doc) {
      // Pre-fill WHT fields
      pe_doc.apply_wht = 1;
      pe_doc.wht_rate = 3.0;
      
      // Set default WHT account
      frappe.call({
        method: 'print_designer.accounting.thailand_wht_integration.get_default_wht_account',
        args: { company: pe_doc.company },
        callback: function(r) {
          if (r.message) {
            pe_doc.wht_account = r.message;
          }
        }
      });
      
      frappe.msgprint(__('Payment Entry created with WHT settings. Please review and submit.'));
    }
  });
}

function show_wht_requirements_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __('Thailand Withholding Tax Requirements'),
    fields: [
      {
        fieldtype: 'HTML',
        fieldname: 'wht_info',
        options: `
          <div class="alert alert-info">
            <h5>Thailand Withholding Tax Information</h5>
            <ul>
              <li><strong>Rate:</strong> 3% on service income</li>
              <li><strong>Applied at:</strong> Payment stage (not invoice)</li>
              <li><strong>Certificate:</strong> ${frm.doc.wht_certificate_required ? 'Required' : 'Not required'}</li>
              <li><strong>Estimated WHT:</strong> ${format_currency(frm.doc.estimated_wht_amount, frm.doc.currency)}</li>
              <li><strong>Net Payment:</strong> ${format_currency(frm.doc.grand_total - frm.doc.estimated_wht_amount, frm.doc.currency)}</li>
            </ul>
            <p><em>Note: Actual WHT will be calculated and deducted during payment entry.</em></p>
          </div>
        `
      }
    ]
  });
  
  dialog.show();
}