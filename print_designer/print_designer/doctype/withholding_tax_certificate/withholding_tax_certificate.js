// Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Withholding Tax Certificate", {
	setup: function(frm) {
		// Filter PND Form Type to only show valid PND DocTypes
		frm.set_query("pnd_form_type", function() {
			return {
				filters: {
					name: ["in", ["PND1 Form", "PND3 Form", "PND53 Form", "PND54 Form"]],
				},
			};
		});

		// Filter custom_pnd_form based on selected pnd_form_type
		frm.set_query("custom_pnd_form", function() {
			if (frm.doc.pnd_form_type) {
				return {
					filters: {
						docstatus: ["!=", 2], // Exclude cancelled documents
					},
				};
			}
		});
	},

	onload: function(frm) {
		// Override click behavior for pnd_form_type field to go to PND Form list
		setTimeout(function() {
			if (frm.fields_dict.pnd_form_type && frm.fields_dict.pnd_form_type.$wrapper) {
				frm.fields_dict.pnd_form_type.$wrapper.find('.link-field').off('click').on('click', function(e) {
					if (frm.doc.pnd_form_type) {
						e.preventDefault();
						e.stopPropagation();
						// Navigate to PND Form list view (since PND Items is a child table)
						frappe.set_route('List', frm.doc.pnd_form_type);
					}
				});
			}
		}, 1000);
	},

	refresh: function(frm) {
		// Add custom button to view PND form if linked
		if (frm.doc.custom_pnd_form && frm.doc.pnd_form_type) {
			frm.add_custom_button(__("View PND Form"), function() {
				frappe.set_route("Form", frm.doc.pnd_form_type, frm.doc.custom_pnd_form);
			}, __("Actions"));
		}

		// Re-apply click override after refresh
		frm.trigger('onload');
	},

	pnd_form_type: function(frm) {
		// Clear custom_pnd_form when pnd_form_type changes
		if (frm.doc.custom_pnd_form) {
			frm.set_value("custom_pnd_form", "");
		}
	}
});
