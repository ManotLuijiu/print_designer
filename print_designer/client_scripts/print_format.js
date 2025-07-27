const set_template_app_options = (frm) => {
	frappe.xcall("frappe.core.doctype.module_def.module_def.get_installed_apps").then((r) => {
		frm.set_df_property("print_designer_template_app", "options", JSON.parse(r));
		if (!frm.doc.print_designer_template_app) {
			frm.set_value("print_designer_template_app", "print_designer");
		}
	});
};

const setup_print_designer_ui = (frm) => {
	// Add helpful information about Print Designer functionality
	if (frm.doc.print_designer) {
		frm.dashboard.add_comment(
			__("This format uses Print Designer. Click 'Edit Format' to open the visual designer."),
			"blue",
			true
		);
	}
	
	// Add quick toggle button for Print Designer
	if (!frm.is_new() && frappe.user.has_role(["System Manager", "Print Manager"])) {
		const current_status = frm.doc.print_designer ? "enabled" : "disabled";
		const toggle_text = frm.doc.print_designer ? "Disable Print Designer" : "Enable Print Designer";
		const button_class = frm.doc.print_designer ? "btn-warning" : "btn-primary";
		
		frm.add_custom_button(__(toggle_text), function() {
			const new_value = frm.doc.print_designer ? 0 : 1;
			const action = new_value ? "enable" : "disable";
			
			frappe.confirm(
				__(`Are you sure you want to ${action} Print Designer for this format?`),
				function() {
					frm.set_value("print_designer", new_value);
					frm.save().then(() => {
						const message = new_value ? 
							"Print Designer enabled. The 'Edit Format' button will now open Print Designer." :
							"Print Designer disabled. The 'Edit Format' button will now open Print Format Builder.";
						frappe.show_alert({
							message: __(message),
							indicator: new_value ? "green" : "orange"
						});
						// Refresh to update UI
						frm.refresh();
					});
				}
			);
		}, __("Actions")).addClass(button_class);
	}
};

frappe.ui.form.on("Print Format", {
	refresh: function (frm) {
		frm.trigger("render_buttons");
		set_template_app_options(frm);
		setup_print_designer_ui(frm);
	},
	render_buttons: function (frm) {
		frm.page.clear_inner_toolbar();
		if (!frm.is_new()) {
			if (!frm.doc.custom_format) {
				frm.add_custom_button(__("Edit Format"), function () {
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
					let current_format = frappe.get_meta(frm.doc.DocType)?.default_print_format;
					if (current_format == frm.doc.name) {
						return;
					}

					frm.add_custom_button(__("Set as Default"), function () {
						frappe.call({
							method: "frappe.printing.doctype.print_format.print_format.make_default",
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
});
