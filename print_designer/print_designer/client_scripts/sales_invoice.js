function calculate_retention(frm) {
  if (frm.doc.custom_retention && frm.doc.base_net_total) {
    const retention = (frm.doc.base_net_total * frm.doc.custom_retention) / 100;
    frm.set_value('custom_retention_amount', retention);
  } else {
    frm.set_value('custom_retention_amount', 0);
  }
}

async function check_construction_service_enabled(frm) {
  if (!frm.doc.company) {
    return false;
  }
  
  try {
    const company_doc = await frappe.db.get_doc('Company', frm.doc.company);
    return company_doc && company_doc.construction_service;
  } catch (error) {
    console.warn('Error checking construction service setting:', error);
    return false;
  }
}

async function toggle_retention_fields(frm) {
  const is_enabled = await check_construction_service_enabled(frm);
  
  // Show/hide retention fields based on company setting
  frm.toggle_display(['custom_retention', 'custom_retention_amount'], is_enabled);
  
  // Clear retention values if construction service is disabled
  if (!is_enabled) {
    frm.set_value('custom_retention', 0);
    frm.set_value('custom_retention_amount', 0);
  }
}

const debounced_calculation = frappe.utils.debounce((frm) => {
  calculate_retention(frm);
}, 500);


frappe.ui.form.on('Sales Invoice', {
  custom_retention: function(frm) {
    calculate_retention(frm);
  },
  validate: function(frm) {
    calculate_retention(frm);
  },
  refresh: function(frm) {
    toggle_retention_fields(frm).then(() => {
      calculate_retention(frm);
    });
  },
  company: function(frm) {
    // Check retention field visibility when company changes
    toggle_retention_fields(frm);
  }
});

frappe.ui.form.on('Sales Invoice Item', {
  items_add: function(frm) {
    debounced_calculation(frm);
  },
  items_remove: function(frm) {
    debounced_calculation(frm);
  },
  qty: function(frm, cdt, cdn) {
    frappe.after_ajax(() => {
        calculate_retention(frm);
    });
  },
  rate: function(frm, cdt, cdn) {
    frappe.after_ajax(() => {
        calculate_retention(frm);
    });
  },
  item_code: function(frm, cdt, cdn) {
    frappe.after_ajax(() => {
        calculate_retention(frm);
    });
  },
  discount_percentage: function(frm, cdt, cdn) {
    frappe.after_ajax(() => {
        calculate_retention(frm);
    });
  },
  discount_amount: function(frm, cdt, cdn) {
    frappe.after_ajax(() => {
        calculate_retention(frm);
    });
  },
  amount: function(frm, cdt, cdn) {
    frappe.after_ajax(() => {
        calculate_retention(frm);
    });
  }
});
