// Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("PND1 Form", {
	refresh(frm) {
		// Add refresh button for manual certificate update
		if (!frm.is_new()) {
			frm.add_custom_button(__("Refresh WHT Certificates"), function() {
				frappe.call({
					method: "refresh_certificates",
					doc: frm.doc,
					callback: function(r) {
						if (r.message) {
							frm.reload_doc();
							frappe.show_alert({
								message: `Updated with ${r.message.total_certificates} certificates`,
								indicator: 'green'
							});
						}
					}
				});
			}, __("Actions"));
		}

		// Ensure totals are current when form loads
		calculate_totals_client_side(frm);

		// Show summary information
		if (frm.doc.total_certificates) {
			frm.dashboard.add_comment(
				`<strong>Summary:</strong> ${frm.doc.total_certificates} certificates, Total Tax: ${format_currency(frm.doc.total_tax_amount)}`,
				'blue', true
			);
		}
	},

	tax_period_year(frm) {
		// Auto-refresh when period changes
		if (frm.doc.tax_period_year && frm.doc.tax_period_month) {
			frm.trigger('refresh_on_period_change');
		}
	},

	tax_period_month(frm) {
		// Auto-refresh when period changes
		if (frm.doc.tax_period_year && frm.doc.tax_period_month) {
			frm.trigger('refresh_on_period_change');
		}
	},

	refresh_on_period_change(frm) {
		// Auto-populate certificates when period is set
		if (!frm.is_new() && frm.doc.tax_period_year && frm.doc.tax_period_month) {
			frappe.call({
				method: "refresh_certificates",
				doc: frm.doc,
				callback: function(r) {
					if (r.message) {
						frm.reload_doc();
					}
				}
			});
		}
	}
});

// Recalculate totals when items are added/removed/modified
frappe.ui.form.on("PND1 Items", {
	items_add: function(frm) {
		calculate_totals_client_side(frm);
	},
	items_remove: function(frm) {
		calculate_totals_client_side(frm);
	},
	gross_amount: function(frm) {
		calculate_totals_client_side(frm);
	},
	tax_amount: function(frm) {
		calculate_totals_client_side(frm);
	}
});

function calculate_totals_client_side(frm) {
	// Calculate totals from items table
	let total_certificates = frm.doc.items ? frm.doc.items.length : 0;
	let total_gross_amount = 0;
	let total_tax_amount = 0;

	if (frm.doc.items) {
		frm.doc.items.forEach(function(item) {
			total_gross_amount += flt(item.gross_amount);
			total_tax_amount += flt(item.tax_amount);
		});
	}

	// Calculate average tax rate
	let average_tax_rate = 0;
	if (total_gross_amount > 0) {
		average_tax_rate = (total_tax_amount / total_gross_amount) * 100;
	}

	// Update form fields
	frm.set_value('total_certificates', total_certificates);
	frm.set_value('total_gross_amount', total_gross_amount);
	frm.set_value('total_tax_amount', total_tax_amount);
	frm.set_value('average_tax_rate', average_tax_rate);

	// Refresh the form to update the display
	frm.refresh_fields();
}
