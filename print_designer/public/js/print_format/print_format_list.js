/**
 * Print Format List View Customization
 * Adds "Add New PTG" button to the Print Format list view
 */

// Wait for frappe.listview to be ready
frappe.provide("frappe.listview.on");

if (frappe.listview && frappe.listview.on) {
	frappe.listview.on["Print Format"] = {
		refresh: function (listview) {
			// Add "Add New PTG" button next to the standard "+ Add" button
			if (!listview.page.btn_ptg_added) {
				listview.page.add_menu_item(__("Add New PTG"), function () {
					// Open dialog to create a new PTG Template
					const dialog = new frappe.ui.Dialog({
						title: __("Create New PTG Template"),
						fields: [
							{
								label: __("Template Name"),
								fieldname: "template_name",
								fieldtype: "Data",
								reqd: 1,
								description: __("Unique name for this template"),
							},
							{
								label: __("Target DocType"),
								fieldname: "target_doctype",
								fieldtype: "Link",
								options: "DocType",
								reqd: 1,
								description: __("The document type this template is for"),
							},
						],
						primary_action: function () {
							const values = dialog.get_values();
							if (!values) return;

							frappe.call({
								method: "print_template_generator.print_template_generator.api.ptg_template.create_ptg_template",
								args: {
									template_name: values.template_name,
									target_doctype: values.target_doctype,
								},
								callback: function (r) {
									if (r.message) {
										dialog.hide();
										frappe.set_route("ptg-editor", values.template_name);
									}
								},
							});
						},
						primary_action_label: __("Create & Open Editor"),
					});
					dialog.show();
				});
				listview.page.btn_ptg_added = true;
			}
		},
	};
}
