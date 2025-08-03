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
    
    // Check for service items and auto-enable WHT
    check_and_enable_wht_for_services(frm);
    
    // Add custom buttons for WHT-related actions
    if (frm.doc.docstatus === 1 && frm.doc.subject_to_wht) {
      add_wht_action_buttons(frm);
    }
  },
  
  company: function(frm) {
    toggle_wht_fields_visibility(frm);
    check_and_enable_wht_for_services(frm);
  },
  
  validate: function(frm) {
    // Auto-check WHT if any service items are present
    check_and_enable_wht_for_services(frm);
  }
});

// Handle changes in items table
frappe.ui.form.on('Sales Invoice Item', {
  items_add: function(frm, cdt, cdn) {
    check_and_enable_wht_for_services(frm);
  },
  
  items_remove: function(frm) {
    check_and_enable_wht_for_services(frm);
  },
  
  item_code: function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (row.item_code) {
      // Check if the added item is a service
      frappe.db.get_value('Item', row.item_code, 'is_service_item')
        .then(function(r) {
          if (r.message && r.message.is_service_item) {
            // Refresh WHT calculation
            setTimeout(() => {
              check_and_enable_wht_for_services(frm);
            }, 500);
          }
        });
    }
  }
});

function check_and_enable_wht_for_services(frm) {
  if (!frm.doc.company || !frm.doc.items || frm.doc.items.length === 0) {
    return;
  }
  
  // Check if company has Thailand service business enabled
  frappe.db.get_value('Company', frm.doc.company, 'thailand_service_business')
    .then(function(r) {
      const thailand_enabled = r.message && r.message.thailand_service_business;
      
      if (!thailand_enabled) {
        return; // Exit if Thailand WHT not enabled for company
      }
      
      // Check if any items are services
      let has_service_items = false;
      let service_items = [];
      let checked_items = 0;
      
      frm.doc.items.forEach(function(item) {
        if (item.item_code) {
          frappe.db.get_value('Item', item.item_code, ['is_service_item', 'item_name'])
            .then(function(item_r) {
              checked_items++;
              
              if (item_r.message && item_r.message.is_service_item) {
                has_service_items = true;
                service_items.push(item_r.message.item_name || item.item_code);
              }
              
              // When all items are checked
              if (checked_items === frm.doc.items.length) {
                if (has_service_items && !frm.doc.subject_to_wht) {
                  // Auto-enable WHT if not already enabled
                  frm.set_value('subject_to_wht', 1);
                  
                  // Show info message
                  frm.dashboard.add_comment(
                    __('WHT automatically enabled for service items: {0}', [service_items.join(', ')]), 
                    'blue', 
                    true
                  );
                  
                  // Calculate WHT amount
                  calculate_estimated_wht_amount(frm);
                  
                } else if (!has_service_items && frm.doc.subject_to_wht) {
                  // Ask user if they want to disable WHT
                  frappe.confirm(
                    __('No service items found. Do you want to disable withholding tax?'),
                    function() {
                      frm.set_value('subject_to_wht', 0);
                      frm.set_value('estimated_wht_amount', 0);
                    }
                  );
                }
              }
            });
        } else {
          checked_items++;
        }
      });
    });
}

function calculate_estimated_wht_amount(frm) {
  if (!frm.doc.subject_to_wht) {
    frm.set_value('estimated_wht_amount', 0);
    return;
  }
  
  // Calculate WHT amount based on service items only
  calculate_wht_for_service_items_only(frm);
}

function calculate_wht_for_service_items_only(frm) {
  if (!frm.doc.items || frm.doc.items.length === 0) {
    frm.set_value('estimated_wht_amount', 0);
    return;
  }
  
  let service_amount = 0;
  let checked_items = 0;
  
  frm.doc.items.forEach(function(item) {
    if (item.item_code && item.amount) {
      frappe.db.get_value('Item', item.item_code, 'is_service_item')
        .then(function(r) {
          checked_items++;
          
          if (r.message && r.message.is_service_item) {
            service_amount += flt(item.amount);
          }
          
          // When all items are checked
          if (checked_items === frm.doc.items.length) {
            if (service_amount > 0) {
              // Calculate 3% WHT on service items only
              const wht_amount = flt((service_amount * 3.0) / 100, 2);
              frm.set_value('estimated_wht_amount', wht_amount);
              
              // Update description to show service amount
              const field = frm.get_field('estimated_wht_amount');
              if (field) {
                field.set_description(`3% WHT on service items (${format_currency(service_amount, frm.doc.currency)})`);
              }
            } else {
              frm.set_value('estimated_wht_amount', 0);
            }
          }
        });
    } else {
      checked_items++;
    }
  });
}

function toggle_wht_fields_visibility(frm) {
  if (!frm.doc.company) return;
  
  // Check if company has Thailand service business enabled
  frappe.db.get_value('Company', frm.doc.company, 'thailand_service_business')
    .then(function(r) {
      const is_enabled = r.message && r.message.thailand_service_business;
      
      if (is_enabled) {
        // Show all WHT fields normally
        frm.toggle_display(['wht_section'], true);
        frm.get_field('subject_to_wht').$wrapper.find('.help-box').hide();
      } else {
        // Show fields but with warning message
        frm.toggle_display(['wht_section'], true);
        
        // Add warning message to the section
        if (!frm.get_field('subject_to_wht').$wrapper.find('.wht-warning').length) {
          frm.get_field('subject_to_wht').$wrapper.append(`
            <div class="wht-warning alert alert-warning" style="margin-top: 10px;">
              <strong>Note:</strong> Thailand Withholding Tax is not enabled for this company. 
              <a href="/app/company/${frm.doc.company}" target="_blank">Enable it in Company settings</a> to use this feature.
              <button class="btn btn-sm btn-primary" style="margin-left: 10px;" onclick="enable_thailand_wht_for_company('${frm.doc.company}', this)">
                Enable Now
              </button>
            </div>
          `);
        }
        
        // Clear WHT values if not enabled
        if (frm.doc.subject_to_wht) {
          frm.set_value('subject_to_wht', 0);
          frm.set_value('estimated_wht_amount', 0);
          frm.set_value('wht_certificate_required', 0);
        }
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

// Global function to enable Thailand WHT for a company
window.enable_thailand_wht_for_company = function(company_name, button_element) {
  // Disable button to prevent double-click
  button_element.disabled = true;
  button_element.innerHTML = 'Enabling...';
  
  frappe.call({
    method: 'frappe.client.set_value',
    args: {
      doctype: 'Company',
      name: company_name,
      fieldname: 'thailand_service_business',
      value: 1
    },
    callback: function(r) {
      if (r.message) {
        frappe.msgprint(__('Thailand Withholding Tax has been enabled for this company.'));
        
        // Remove the warning message
        $('.wht-warning').fadeOut(function() {
          $(this).remove();
        });
        
        // Refresh the form to update field visibility
        setTimeout(() => {
          cur_frm.refresh();
        }, 1000);
        
      } else {
        frappe.msgprint(__('Failed to enable Thailand Withholding Tax. Please try manually.'));
        button_element.disabled = false;
        button_element.innerHTML = 'Enable Now';
      }
    },
    error: function() {
      frappe.msgprint(__('Error enabling Thailand Withholding Tax. Please check permissions.'));
      button_element.disabled = false;
      button_element.innerHTML = 'Enable Now';
    }
  });
};