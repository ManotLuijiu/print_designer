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
		console.log("🔍 PND1 Form: tax_period_year changed to:", frm.doc.tax_period_year);
		// Auto-refresh when period changes
		if (frm.doc.tax_period_year && frm.doc.tax_period_month) {
			console.log("✅ Both year and month set, triggering refresh");
			frm.trigger('refresh_on_period_change');
		} else {
			console.log("⏳ Waiting for month to be set. Month:", frm.doc.tax_period_month);
		}
	},

	tax_period_month(frm) {
		console.log("🔍 PND1 Form: tax_period_month changed to:", frm.doc.tax_period_month);
		// Auto-refresh when period changes
		if (frm.doc.tax_period_year && frm.doc.tax_period_month) {
			console.log("✅ Both year and month set, triggering refresh");
			frm.trigger('refresh_on_period_change');
		} else {
			console.log("⏳ Waiting for year to be set. Year:", frm.doc.tax_period_year);
		}
	},

	refresh_on_period_change(frm) {
		console.log("🔄 PND1 Form: refresh_on_period_change called");
		console.log("Year:", frm.doc.tax_period_year, "Month:", frm.doc.tax_period_month);

		// Auto-populate Employee Tax Ledger entries when period is set
		// Works for both new and existing forms
		if (frm.doc.tax_period_year && frm.doc.tax_period_month) {
			console.log("📡 Calling server to get Employee Tax Ledger entries...");
			frappe.call({
				method: "print_designer.print_designer.doctype.pnd1_form.pnd1_form.get_employee_tax_ledger_entries",
				args: {
					tax_period_year: frm.doc.tax_period_year,
					tax_period_month: frm.doc.tax_period_month
				},
				callback: function(r) {
					console.log("📥 Server response received:", r);
					if (r.message && r.message.length > 0) {
						console.log("✅ Found", r.message.length, "entries");
						// Clear existing items
						frm.clear_table("items");

						// Add new items from Employee Tax Ledger
						r.message.forEach(function(item, idx) {
							console.log(`  Adding item ${idx + 1}:`, item.employee_name, item.tax_amount);
							let row = frm.add_child("items");
							Object.assign(row, item);
						});

						frm.refresh_field("items");
						calculate_totals_client_side(frm);

						frappe.show_alert({
							message: `Loaded ${r.message.length} employee(s) from Tax Ledger`,
							indicator: 'green'
						});
					} else {
						console.log("⚠️ No entries found for this period");
						frappe.show_alert({
							message: `No Employee Tax Ledger entries found for ${frm.doc.tax_period_month}/${frm.doc.tax_period_year}`,
							indicator: 'yellow'
						});
					}
				},
				error: function(r) {
					console.error("❌ Error calling server:", r);
					frappe.show_alert({
						message: "Error fetching Employee Tax Ledger entries",
						indicator: 'red'
					});
				}
			});
		} else {
			console.log("❌ Missing year or month, skipping refresh");
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
