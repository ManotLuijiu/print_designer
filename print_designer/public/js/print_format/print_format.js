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

frappe.ui.form.on("Print Format", {
	refresh: function (frm) {
		frm.trigger("render_buttons");
		set_template_app_options(frm);
		setup_print_designer_ui(frm);
		// Add Export/Import buttons for Print Designer formats
		frm.trigger("add_export_import_buttons");
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
	},
	add_export_import_buttons: function (frm) {
		// Only add these buttons for Print Designer formats
		if (!frm.is_new() && frm.doc.print_designer) {
			// Add Duplicate button first (in Actions group)
			frm.add_custom_button(__("Duplicate"), function () {
				frappe.prompt({
					label: __("New Format Name"),
					fieldname: "new_name",
					fieldtype: "Data",
					reqd: 1,
					default: frm.doc.name + " Copy"
				}, function (values) {
					frappe.call({
						method: "print_designer.api.print_format_export_import.duplicate_print_format",
						args: {
							source_name: frm.doc.name,
							new_name: values.new_name
						},
						callback: function (r) {
							if (r.message) {
								frappe.show_alert({
									message: __("Print Format duplicated as {0}", [r.message]),
									indicator: "green"
								});
								// Open the duplicated format
								frappe.set_route("Form", "Print Format", r.message);
							}
						}
					});
				}, __("Duplicate Print Format"), __("Duplicate"));
			}, __("Actions"));

			// Add Export button (in Actions group, after Duplicate)
			frm.add_custom_button(__("Export Format"), function () {
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
			}, __("Actions"));

			// Add Import button (in Actions group, after Export)
			frm.add_custom_button(__("Import Format"), function () {
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
			}, __("Actions"));
		}
	}
});
