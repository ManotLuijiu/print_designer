function calculate_retention(frm) {
  if (frm.doc.custom_retention && frm.doc.base_net_total) {
    const retention = (frm.doc.base_net_total * frm.doc.custom_retention) / 100;
    frm.set_value('custom_retention_amount', retention);
  } else {
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
    calculate_retention(frm);
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
