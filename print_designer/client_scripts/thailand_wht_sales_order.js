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
    
    // Check for service items and auto-enable WHT
    check_and_enable_wht_for_services(frm);
    
    // Copy WHT settings to Sales Invoice
    if (frm.doc.docstatus === 1 && frm.doc.subject_to_wht) {
      add_wht_action_buttons(frm);
    }
  },
  
  company: function(frm) {
    toggle_wht_fields_visibility(frm);
    check_and_enable_wht_for_services(frm);
  }
});

// Handle changes in items table
frappe.ui.form.on('Sales Order Item', {
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