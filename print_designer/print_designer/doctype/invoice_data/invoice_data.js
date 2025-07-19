// Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Data', {
    sales_invoice_id: function(frm) {
        if (frm.doc.sales_invoice_id) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: "Sales Invoice",
                    filters: {
                        name: frm.doc.sales_invoice_id
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        console.log("------------", r.message);
                        frm.set_value('customer', r.message.customer);
                        frm.set_value('date', frappe.datetime.get_today());
                        frm.set_value('invoice_date', r.message.posting_date);
                        frm.set_value('company', r.message.company);
                        
                        frm.clear_table('invoice_items');
                        
                        r.message.items.forEach(function(item) {
                            var child = frm.add_child('invoice_items');
                            child.item_code = item.item_code;
                            child.item_name = item.item_name;
                            child.qty = item.qty;
                            child.uom = item.uom;
                            child.rate = item.rate;
                            child.amount = item.amount;
                        });
                        frm.refresh_field('invoice_items');
                    }
                }
            });
        }
    }
});
