// Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company Stamp", {
	refresh: function(frm) {
		// Set default company if not set
		if (frm.is_new() && !frm.doc.company) {
			// Get user's default company
			const default_company = frappe.defaults.get_user_default("Company");
			if (default_company) {
				frm.set_value("company", default_company);
			}
		}
		
		// Add custom buttons for stamp management
		if (!frm.is_new() && frm.doc.is_active) {
			frm.add_custom_button(__("Preview Stamp"), function() {
				if (frm.doc.stamp_image) {
					frappe.show_preview(frm.doc.stamp_image);
				} else {
					frappe.msgprint(__("No stamp image available to preview"));
				}
			});
		}
	},
	
	company: function(frm) {
		// Update title when company changes (if title is not manually set)
		if (frm.doc.company && (!frm.doc.title || frm.doc.title === "New Company Stamp")) {
			frappe.db.get_value("Company", frm.doc.company, "company_name")
				.then(r => {
					if (r.message && r.message.company_name) {
						const stamp_type = frm.doc.stamp_type || "Official";
						frm.set_value("title", `${r.message.company_name} - ${stamp_type} Stamp`);
					}
				});
		}
	},
	
	stamp_type: function(frm) {
		// Update title when stamp type changes
		if (frm.doc.company && frm.doc.stamp_type) {
			frappe.db.get_value("Company", frm.doc.company, "company_name")
				.then(r => {
					if (r.message && r.message.company_name) {
						frm.set_value("title", `${r.message.company_name} - ${frm.doc.stamp_type} Stamp`);
					}
				});
		}
	}
});
