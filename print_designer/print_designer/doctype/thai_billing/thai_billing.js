// Copyright (c) 2025, Print Designer and contributors
// For license information, please see license.txt

frappe.ui.form.on('Thai Billing', {
	onload: function(frm) {
		// Set filters for customer address and contact
		frm.set_query("customer_address", function() {
			return {
				filters: {
					"link_doctype": "Customer",
					"link_name": frm.doc.customer
				}
			};
		});

		frm.set_query("contact_person", function() {
			return {
				filters: {
					"link_doctype": "Customer",
					"link_name": frm.doc.customer
				}
			};
		});
	},

	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 0) {
			// Add button to fetch pending invoices
			frm.add_custom_button(__('Get Pending Invoices'), function() {
				frm.call('add_pending_invoices').then(() => {
					frm.refresh_field('invoice_items');
					frm.refresh_field('total_invoices');
					frm.refresh_field('total_amount');
					frm.refresh_field('grand_total');
				});
			});

			// Add button to clear all items
			frm.add_custom_button(__('Clear All Items'), function() {
				frappe.confirm(__('Are you sure you want to clear all invoice items?'), function() {
					frm.doc.invoice_items = [];
					frm.refresh_field('invoice_items');
					frm.trigger('calculate_totals');
				});
			});
		}

		// Show billing summary button
		if (frm.doc.customer) {
			frm.add_custom_button(__('View Customer Billing Summary'), function() {
				frappe.route_options = {
					"customer": frm.doc.customer
				};
				frappe.set_route("query-report", "Customer Billing Summary");
			});
		}

		// Set indicator based on status
		if (frm.doc.status) {
			let indicator_color = {
				"Draft": "red",
				"Submitted": "blue",
				"Paid": "green",
				"Overdue": "orange",
				"Cancelled": "gray"
			};
			frm.dashboard.set_headline_alert(
				`<div class="indicator ${indicator_color[frm.doc.status]}">
					${__("Status")}: ${__(frm.doc.status)}
				</div>`
			);
		}
	},

	customer: function(frm) {
		if (frm.doc.customer) {
			// Clear address and contact when customer changes
			frm.set_value('customer_address', '');
			frm.set_value('contact_person', '');
			frm.set_value('billing_address_display', '');

			// Clear existing invoice items
			frm.doc.invoice_items = [];
			frm.refresh_field('invoice_items');
			frm.trigger('calculate_totals');
		}
	},

	customer_address: function(frm) {
		if (frm.doc.customer_address) {
			frappe.call({
				method: 'frappe.contacts.doctype.address.address.get_address_display',
				args: {
					"address_dict": frm.doc.customer_address
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('billing_address_display', r.message);
					}
				}
			});
		}
	},

	due_date: function(frm) {
		// Validate due date
		if (frm.doc.posting_date && frm.doc.due_date) {
			if (frappe.datetime.get_diff(frm.doc.due_date, frm.doc.posting_date) < 0) {
				frappe.msgprint(__('Due Date cannot be before Posting Date'));
				frm.set_value('due_date', '');
			}
		}
	},

	billing_period_from: function(frm) {
		validate_billing_period(frm);
	},

	billing_period_to: function(frm) {
		validate_billing_period(frm);
	},

	calculate_totals: function(frm) {
		let total_invoices = 0;
		let total_amount = 0.0;

		frm.doc.invoice_items.forEach(function(item) {
			if (item.invoice_amount) {
				total_invoices += 1;
				total_amount += flt(item.invoice_amount);
			}
		});

		frm.set_value('total_invoices', total_invoices);
		frm.set_value('total_amount', total_amount);
		frm.set_value('grand_total', total_amount);
	}
});

// Child table events
frappe.ui.form.on('Thai Billing Item', {
	sales_invoice: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.sales_invoice) {
			// Validate that invoice belongs to the same customer
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Sales Invoice',
					'name': row.sales_invoice,
					'fieldname': ['customer', 'posting_date', 'due_date', 'grand_total', 'outstanding_amount', 'remarks']
				},
				callback: function(r) {
					if (r.message) {
						if (r.message.customer !== frm.doc.customer) {
							frappe.msgprint(__('Sales Invoice {0} does not belong to customer {1}',
								[row.sales_invoice, frm.doc.customer_name]));
							frappe.model.set_value(cdt, cdn, 'sales_invoice', '');
							return;
						}

						// Auto-populate fields
						frappe.model.set_value(cdt, cdn, 'invoice_date', r.message.posting_date);
						frappe.model.set_value(cdt, cdn, 'due_date', r.message.due_date);
						frappe.model.set_value(cdt, cdn, 'invoice_amount', r.message.grand_total);
						frappe.model.set_value(cdt, cdn, 'outstanding_amount', r.message.outstanding_amount);
						frappe.model.set_value(cdt, cdn, 'invoice_description', r.message.project || 'Credit Sales');
					}
				}
			});
		}
	},

	invoice_amount: function(frm) {
		frm.trigger('calculate_totals');
	},

	invoice_items_remove: function(frm) {
		frm.trigger('calculate_totals');
	}
});

// Helper functions
function validate_billing_period(frm) {
	if (frm.doc.billing_period_from && frm.doc.billing_period_to) {
		if (frappe.datetime.get_diff(frm.doc.billing_period_to, frm.doc.billing_period_from) < 0) {
			frappe.msgprint(__('Billing Period To Date cannot be before From Date'));
			frm.set_value('billing_period_to', '');
		}
	}
}
