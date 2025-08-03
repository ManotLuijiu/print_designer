// Thailand Withholding Tax Client Script for Payment Entry
// Handles WHT calculations and validations

frappe.ui.form.on('Payment Entry', {
  apply_wht: function(frm) {
    if (frm.doc.apply_wht) {
      setup_wht_defaults(frm);
      calculate_wht_amounts(frm);
    } else {
      clear_wht_fields(frm);
    }
  },
  
  wht_rate: function(frm) {
    if (frm.doc.apply_wht) {
      calculate_wht_amounts(frm);
    }
  },
  
  paid_amount: function(frm) {
    if (frm.doc.apply_wht) {
      calculate_wht_amounts(frm);
    }
  },
  
  refresh: function(frm) {
    // Show/hide WHT fields based on company setting and payment type
    toggle_wht_fields_visibility(frm);
    
    // Set up WHT field dependencies
    setup_wht_field_dependencies(frm);
    
    // Add custom buttons for WHT actions
    if (frm.doc.docstatus === 1 && frm.doc.apply_wht) {
      add_wht_action_buttons(frm);
    }
  },
  
  company: function(frm) {
    toggle_wht_fields_visibility(frm);
    if (frm.doc.apply_wht) {
      setup_wht_defaults(frm);
    }
  },
  
  payment_type: function(frm) {
    toggle_wht_fields_visibility(frm);
  }
});

// Handle changes in payment references
frappe.ui.form.on('Payment Entry Reference', {
  allocated_amount: function(frm, cdt, cdn) {
    if (frm.doc.apply_wht) {
      calculate_wht_amounts(frm);
    }
  },
  
  references_remove: function(frm) {
    if (frm.doc.apply_wht) {
      calculate_wht_amounts(frm);
    }
  }
});

function setup_wht_defaults(frm) {
  // Set default WHT rate if not set
  if (!frm.doc.wht_rate) {
    frm.set_value('wht_rate', 3.0);
  }
  
  // Set default WHT account from company
  if (!frm.doc.wht_account && frm.doc.company) {
    frappe.call({
      method: 'print_designer.accounting.thailand_wht_integration.get_default_wht_account',
      args: { company: frm.doc.company },
      callback: function(r) {
        if (r.message) {
          frm.set_value('wht_account', r.message);
        }
      }
    });
  }
}

function calculate_wht_amounts(frm) {
  if (!frm.doc.apply_wht || !frm.doc.wht_rate) {
    return;
  }
  
  let total_wht_base = 0;
  
  // Calculate total amount subject to WHT from references
  if (frm.doc.references && frm.doc.references.length > 0) {
    frm.doc.references.forEach(function(ref) {
      if (ref.reference_doctype === 'Sales Invoice' && ref.allocated_amount) {
        // Check if invoice is subject to WHT
        frappe.call({
          method: 'print_designer.accounting.thailand_wht_integration.check_invoice_wht_status',
          args: {
            reference_type: ref.reference_doctype,
            reference_name: ref.reference_name
          },
          async: false,
          callback: function(r) {
            if (r.message) {
              total_wht_base += flt(ref.allocated_amount);
            }
          }
        });
      }
    });
  } else {
    // If no specific references, use paid amount
    total_wht_base = flt(frm.doc.paid_amount);
  }
  
  // Calculate WHT amount
  const wht_amount = flt((total_wht_base * flt(frm.doc.wht_rate)) / 100, 2);
  frm.set_value('wht_amount', wht_amount);
  
  // Calculate net payment amount
  const net_amount = flt(frm.doc.paid_amount) - wht_amount;
  frm.set_value('net_payment_amount', net_amount);
  
  // Show warning if WHT amount is significant
  if (wht_amount > 0) {
    frm.dashboard.add_comment(
      __('WHT will be deducted: {0}. Net payment: {1}', 
        [format_currency(wht_amount, frm.doc.currency), format_currency(net_amount, frm.doc.currency)]
      ), 
      'blue'
    );
  }
}

function clear_wht_fields(frm) {
  frm.set_value('wht_amount', 0);
  frm.set_value('net_payment_amount', frm.doc.paid_amount);
  frm.set_value('wht_certificate_no', '');
  frm.set_value('wht_certificate_date', '');
}

function toggle_wht_fields_visibility(frm) {
  if (!frm.doc.company) return;
  
  // Check conditions for showing WHT fields
  const should_show = frm.doc.payment_type === 'Receive';
  
  if (should_show) {
    // Check if company has Thailand service business enabled
    frappe.db.get_value('Company', frm.doc.company, 'thailand_service_business')
      .then(function(r) {
        const is_enabled = r.message && r.message.thailand_service_business;
        
        // Show/hide WHT section
        frm.toggle_display(['wht_section'], is_enabled);
        
        if (!is_enabled) {
          // Clear WHT values if not enabled
          frm.set_value('apply_wht', 0);
          clear_wht_fields(frm);
        }
      });
  } else {
    // Hide WHT fields for non-receive payments
    frm.toggle_display(['wht_section'], false);
    frm.set_value('apply_wht', 0);
    clear_wht_fields(frm);
  }
}

function setup_wht_field_dependencies(frm) {
  // Set up filters for WHT account
  frm.set_query('wht_account', function() {
    return {
      filters: {
        'company': frm.doc.company,
        'is_group': 0,
        'account_type': ['in', ['Tax', 'Current Asset']]
      }
    };
  });
}

function add_wht_action_buttons(frm) {
  // Add button to view WHT summary
  frm.add_custom_button(__('WHT Summary'), function() {
    show_wht_summary_dialog(frm);
  }, __('Thailand WHT'));
  
  // Add button to generate WHT certificate template
  frm.add_custom_button(__('WHT Certificate'), function() {
    generate_wht_certificate(frm);
  }, __('Thailand WHT'));
}

function show_wht_summary_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __('Thailand Withholding Tax Summary'),
    size: 'large',
    fields: [
      {
        fieldtype: 'HTML',
        fieldname: 'wht_summary',
        options: `
          <div class="alert alert-info">
            <h5>Withholding Tax Details</h5>
            <table class="table table-bordered">
              <tr><td><strong>Payment Amount:</strong></td><td>${format_currency(frm.doc.paid_amount, frm.doc.currency)}</td></tr>
              <tr><td><strong>WHT Rate:</strong></td><td>${frm.doc.wht_rate}%</td></tr>
              <tr><td><strong>WHT Amount:</strong></td><td>${format_currency(frm.doc.wht_amount, frm.doc.currency)}</td></tr>
              <tr><td><strong>Net Payment:</strong></td><td>${format_currency(frm.doc.net_payment_amount, frm.doc.currency)}</td></tr>
              <tr><td><strong>WHT Account:</strong></td><td>${frm.doc.wht_account || 'Not set'}</td></tr>
              <tr><td><strong>Certificate No:</strong></td><td>${frm.doc.wht_certificate_no || 'Not provided'}</td></tr>
              <tr><td><strong>Certificate Date:</strong></td><td>${frm.doc.wht_certificate_date || 'Not provided'}</td></tr>
            </table>
            <p><em>Note: This information will be used for accounting entries and tax reporting.</em></p>
          </div>
        `
      }
    ]
  });
  
  dialog.show();
}

function generate_wht_certificate(frm) {
  frappe.msgprint(__('WHT Certificate generation feature will be available in a future update.'));
}