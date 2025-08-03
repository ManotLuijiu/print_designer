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
    
    // Check for service items and auto-enable WHT
    check_and_enable_wht_for_services(frm);
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
frappe.ui.form.on('Quotation Item', {
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

function check_and_enable_wht_for_services(frm) {
  // Skip if company doesn't have Thailand service business enabled
  if (!frm.doc.company) return;
  
  frappe.db.get_value('Company', frm.doc.company, 'thailand_service_business')
    .then(function(r) {
      if (!r.message || !r.message.thailand_service_business) {
        return;
      }
      
      // Check if any items are services
      if (!frm.doc.items || frm.doc.items.length === 0) {
        return;
      }
      
      let has_service_items = false;
      let checked_items = 0;
      const total_items = frm.doc.items.length;
      
      frm.doc.items.forEach(function(item) {
        if (item.item_code) {
          frappe.db.get_value('Item', item.item_code, 'is_service_item')
            .then(function(item_r) {
              checked_items++;
              
              if (item_r.message && item_r.message.is_service_item) {
                has_service_items = true;
              }
              
              // After checking all items, update WHT status
              if (checked_items === total_items) {
                if (has_service_items && !frm.doc.subject_to_wht) {
                  frm.set_value('subject_to_wht', 1);
                  calculate_estimated_wht_amount(frm);
                  frappe.show_alert({
                    message: '✅ WHT automatically enabled for service items',
                    indicator: 'green'
                  });
                } else if (!has_service_items && frm.doc.subject_to_wht) {
                  // Only auto-disable if no service items (user might have manually enabled)
                  frappe.show_alert({
                    message: 'ℹ️ No service items found. WHT remains as set.',
                    indicator: 'blue'
                  });
                }
              }
            });
        } else {
          checked_items++;
        }
      });
    });
}

function calculate_wht_for_service_items_only(frm) {
  if (!frm.doc.subject_to_wht || !frm.doc.items || frm.doc.items.length === 0) {
    frm.set_value('estimated_wht_amount', 0);
    return;
  }
  
  let service_total = 0;
  let checked_items = 0;
  const total_items = frm.doc.items.length;
  
  frm.doc.items.forEach(function(item) {
    if (item.item_code && item.amount) {
      frappe.db.get_value('Item', item.item_code, 'is_service_item')
        .then(function(r) {
          checked_items++;
          
          if (r.message && r.message.is_service_item) {
            service_total += item.amount;
          }
          
          // After checking all items, calculate WHT on service total
          if (checked_items === total_items) {
            const wht_amount = service_total * 0.03; // 3% WHT rate
            frm.set_value('estimated_wht_amount', wht_amount);
          }
        });
    } else {
      checked_items++;
      if (checked_items === total_items) {
        const wht_amount = service_total * 0.03;
        frm.set_value('estimated_wht_amount', wht_amount);
      }
    }
  });
}