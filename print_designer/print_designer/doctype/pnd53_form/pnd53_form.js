// Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("PND53 Form", {
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

		// Show summary information
		if (frm.doc.total_certificates) {
			frm.dashboard.add_comment(
				`<strong>Summary:</strong> ${frm.doc.total_certificates} certificates, Total Tax: ฿${format_currency(frm.doc.total_tax_amount)}`,
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
