/** biome-ignore-all lint/complexity/useArrowFunction: <explanation> */
const set_template_app_options = (frm) => {
	frappe
		.xcall("frappe.core.doctype.module_def.module_def.get_installed_apps")
		.then((r) => {
			frm.set_df_property(
				"print_designer_template_app",
				"options",
				JSON.parse(r),
			);
			if (!frm.doc.print_designer_template_app) {
				frm.set_value("print_designer_template_app", "print_designer");
			}
		});
};

const setup_print_designer_ui = (frm) => {
	// Add helpful information about Print Designer functionality
	if (frm.doc.print_designer) {
		frm.dashboard.add_comment(
			__(
				"This format uses Print Designer. Click 'Edit Format' to open the visual designer.",
			),
			"blue",
			true,
		);
	}

	// Add quick toggle button for Print Designer
	if (
		!frm.is_new() &&
		frappe.user.has_role(["System Manager", "Print Manager"])
	) {
		const current_status = frm.doc.print_designer ? "enabled" : "disabled";
		const toggle_text = frm.doc.print_designer
			? "Disable Print Designer"
			: "Enable Print Designer";
		const button_class = frm.doc.print_designer ? "btn-warning" : "btn-primary";

		frm
			.add_custom_button(
				__(toggle_text),
				function () {
					const new_value = frm.doc.print_designer ? 0 : 1;
					const action = new_value ? "enable" : "disable";

					frappe.confirm(
						__(
							`Are you sure you want to ${action} Print Designer for this format?`,
						),
						function () {
							frm.set_value("print_designer", new_value);
							frm.save().then(() => {
								const message = new_value
									? "Print Designer enabled. The 'Edit Format' button will now open Print Designer."
									: "Print Designer disabled. The 'Edit Format' button will now open Print Format Builder.";
								frappe.show_alert({
									message: __(message),
									indicator: new_value ? "green" : "orange",
								});
								// Refresh to update UI
								frm.refresh();
							});
						},
					);
				},
				__("Actions"),
			)
			.addClass(button_class);
	}
};

/**
 * Dialog of the "Export as Default Template" action.
 *
 * The dialog asks for the public format name, the filename and the
 * destination category of the template.  The public name determines the
 * installation collisions, the filename organizes the repository and the
 * category is the folder of the template inside the app.
 *
 * The transaction profile of the format is part of the export, so it is
 * shown and can be corrected here.
 */
const show_export_as_default_template_dialog = (frm) => {
	const doc_type = frm.doc.doc_type;
	const supports_direction = doc_type === "Payment Entry";
	const supports_type =
		doc_type === "Payment Entry" || doc_type === "Sales Invoice";
	const default_filename = `${slugify_filename(frm.doc.name)}.json`;

	frappe.call({
		method: "print_designer.api.default_template_export.get_categories",
		callback: (r) => {
			const categories = (r && r.message) || [];

			const dialog = new frappe.ui.Dialog({
				title: __("Export as Default Template"),
				fields: [
					{
						fieldname: "template_name",
						fieldtype: "Data",
						label: __("Public Format Name"),
						reqd: 1,
						default: frm.doc.name,
						description: __(
							"The name of the template. It determines the installation collisions.",
						),
					},
					{
						fieldname: "filename",
						fieldtype: "Data",
						label: __("Filename"),
						reqd: 1,
						default: default_filename,
						description: __("The filename of the exported file."),
					},
					{
						fieldname: "category",
						fieldtype: "Select",
						label: __("Destination Category"),
						options: categories.map((item) => item.value),
					},
					{
						fieldname: "profile_section",
						fieldtype: "Section Break",
						label: __("Transaction Profile"),
					},
					{
						fieldname: "transaction_direction",
						fieldtype: "Select",
						label: __("Transaction Direction"),
						options: ["", "Pay", "Receive"],
						default: frm.doc.pd_custom_transaction_direction || "",
						depends_on: "eval:doc.transaction_direction_shown",
						hidden: !supports_direction,
					},
					{
						fieldname: "transaction_direction_shown",
						fieldtype: "Check",
						label: __("Show Direction"),
						hidden: 1,
						default: supports_direction ? 1 : 0,
					},
					{
						fieldname: "transaction_type",
						fieldtype: "Select",
						label: __("Transaction Type"),
						options: ["", "Services", "Goods"],
						default: frm.doc.pd_custom_transaction_type || "",
						hidden: !supports_type,
					},
				],
				primary_action_label: __("Export"),
				primary_action: (values) => {
					dialog.disable_primary_action();
					export_as_default_template(frm, values, dialog);
				},
			});

			dialog.show();
		},
	});
};

/**
 * A file system friendly name for a template.
 *
 * The name of a saved format may carry spaces and slashes, so the default
 * file name of the export is a slug of it.
 */
const slugify_filename = (value) =>
	String(value || "")
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "_")
		.replace(/^_+|_+$/g, "") || "template";

const export_as_default_template = (frm, values, dialog) => {
	frappe.call({
		method: "print_designer.api.default_template_export.export_as_default_template",
		args: {
			print_format_name: frm.doc.name,
			template_name: values.template_name,
			category: values.category,
			transaction_direction: values.transaction_direction || "",
			transaction_type: values.transaction_type || "",
		},
		callback: (r) => {
			const message = r && r.message;
			if (!message) {
				// The export did not answer. The dialog stays open and the
				// button comes back, so the export can be tried again.
				if (dialog) {
					dialog.enable_primary_action();
				}
				return;
			}

			const dataStr = JSON.stringify(message.template, null, 2);
			const dataBlob = new Blob([dataStr], { type: "application/json" });
			const url = URL.createObjectURL(dataBlob);

			const downloadLink = document.createElement("a");
			downloadLink.href = url;
			downloadLink.download = values.filename || message.filename;
			document.body.appendChild(downloadLink);
			downloadLink.click();
			document.body.removeChild(downloadLink);
			URL.revokeObjectURL(url);

			if (dialog) {
				dialog.hide();
			}

			frappe.show_alert({
				message: __("Default template exported successfully"),
				indicator: "green",
			});
		},
		error: () => {
			// The export failed. The dialog stays open and the button comes
			// back, so the export can be tried again.
			if (dialog) {
				dialog.enable_primary_action();
			}
		},
	});
};

frappe.ui.form.on("Print Format", {
	refresh: function (frm) {
		frm.trigger("render_buttons");
		set_template_app_options(frm);
		setup_print_designer_ui(frm);
		// Add Export/Import menu items for Print Designer formats (only once per refresh)
		if (!frm.is_new() && frm.doc.print_designer) {
			console.log("Adding Export/Import menu items for Print Designer format:", frm.doc.name);
			
			// Add menu items using the same pattern as Frappe's Print and Duplicate
			// Export Format menu item
			frm.page.add_menu_item(
				__("Export Format"),
				function () {
					frappe.call({
						method: "print_designer.api.print_format_export_import.export_print_format",
						args: {
							print_format_name: frm.doc.name
						},
						callback: function (r) {
							if (r.message) {
								// Create a downloadable JSON file
								const export_data = r.message;
								const dataStr = JSON.stringify(export_data, null, 2);
								const dataBlob = new Blob([dataStr], { type: 'application/json' });
								const url = URL.createObjectURL(dataBlob);
								
								// Create download link
								const downloadLink = document.createElement('a');
								downloadLink.href = url;
								const timestamp = new Date().toISOString().replace(/:/g, '-').substring(0, 19);
								downloadLink.download = `${frm.doc.name}_${timestamp}.json`;
								document.body.appendChild(downloadLink);
								downloadLink.click();
								document.body.removeChild(downloadLink);
								URL.revokeObjectURL(url);
								
								frappe.show_alert({
									message: __("Print Format exported successfully"),
									indicator: "green"
								});
							}
						}
					});
				},
				true
			);

			// Import Format menu item
			frm.page.add_menu_item(
				__("Import Format"),
				function () {
					// Create file input dialog
					const dialog = new frappe.ui.Dialog({
						title: __("Import Print Designer Format"),
						fields: [
							{
								fieldname: "import_file",
								fieldtype: "Attach",
								label: __("Select Export File (JSON)"),
								reqd: 1,
								description: __("Select a previously exported Print Designer format JSON file")
							},
							{
								fieldname: "column_break",
								fieldtype: "Column Break"
							},
							{
								fieldname: "new_name",
								fieldtype: "Data",
								label: __("New Format Name"),
								description: __("Leave empty to use the original name or auto-generate if exists")
							},
							{
								fieldname: "section_break",
								fieldtype: "Section Break"
							},
							{
								fieldname: "overwrite",
								fieldtype: "Check",
								label: __("Overwrite if exists"),
								description: __("Warning: This will replace existing format with same name"),
								default: 0
							}
						],
						primary_action_label: __("Import"),
						primary_action: function (values) {
							// Read the file content
							if (!values.import_file) {
								frappe.msgprint(__("Please select a file to import"));
								return;
							}

							// Fetch the file content
							$.ajax({
								url: values.import_file,
								type: 'GET',
								success: function (data) {
									// Import the format
									frappe.call({
										method: "print_designer.api.print_format_export_import.import_print_format",
										args: {
											export_data: typeof data === 'string' ? data : JSON.stringify(data),
											new_name: values.new_name,
											overwrite: values.overwrite
										},
										callback: function (r) {
											if (r.message) {
												dialog.hide();
												frappe.show_alert({
													message: __("Print Format imported successfully as {0}", [r.message]),
													indicator: "green"
												}, 5);

												// Ask if user wants to open the imported format
												frappe.confirm(
													__("Do you want to open the imported Print Format?"),
													function () {
														frappe.set_route("Form", "Print Format", r.message);
													}
												);
											}
										}
									});
								},
								error: function (xhr, status, error) {
									frappe.msgprint(__("Error reading file: {0}", [error]));
								}
							});
						}
					});
					dialog.show();
				},
				true
			);

			// Convert to Print Designer Export menu item - Opens dialog for file path conversion
			frm.page.add_menu_item(
				__("Convert to Print Designer Export"),
				function () {
					// Show conversion dialog (defined in print_format_conversion_dialog.js)
					if (window.show_print_format_conversion_dialog) {
						window.show_print_format_conversion_dialog();
					} else {
						frappe.msgprint({
							title: __('Dialog Not Available'),
							message: __('Conversion dialog script not loaded. Please refresh the page.'),
							indicator: 'red'
						});
					}
				},
				true
			);

			// Export as Default Template menu item - ships the format with the app
			frm.page.add_menu_item(
				__("Export as Default Template"),
				function () {
					show_export_as_default_template_dialog(frm);
				},
				true
			);
		}
	},
	render_buttons: function (frm) {
		console.log("render_buttons", frm.doc);
		frm.page.clear_inner_toolbar();
		if (!frm.is_new()) {
			if (!frm.doc.custom_format) {
				frm.add_custom_button(__("Edit Format"), function () {
					console.log("Edit Format clicked", frm.doc);
					if (!frm.doc.doc_type) {
						frappe.msgprint(__("Please select DocType first"));
						return;
					}
					if (frm.doc.print_format_builder_beta) {
						frappe.set_route("print-format-builder-beta", frm.doc.name);
					} else if (frm.doc.print_designer) {
						frappe.set_route("print-designer", frm.doc.name);
					} else {
						frappe.set_route("print-format-builder", frm.doc.name);
					}
				});
			} else if (frm.doc.custom_format && !frm.doc.raw_printing) {
				frm.set_df_property("html", "reqd", 1);
			}
			if (frappe.model.can_write("Customize Form")) {
				frappe.model.with_doctype(frm.doc.doc_type, function () {
					let current_format = frappe.get_meta(
						frm.doc.DocType,
					)?.default_print_format;
					if (current_format === frm.doc.name) {
						return;
					}

					frm.add_custom_button(__("Set as Default"), function () {
						frappe.call({
							method:
								"frappe.printing.doctype.print_format.print_format.make_default",
							args: {
								name: frm.doc.name,
							},
							callback: function () {
								frm.refresh();
							},
						});
					});
				});
			}
		}
	}
});
