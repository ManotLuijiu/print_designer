/** biome-ignore-all lint/complexity/useArrowFunction: <explanation> */
console.log("[SIGNATURE DEBUG] signature_basic_information.js script loaded");

frappe.ui.form.on("Signature Basic Information", {
	onload: function (frm) {
		console.log(
			"[SIGNATURE DEBUG] Signature Basic Information form onload triggered",
		);
		// Load signature field options
		_load_signature_field_options(frm);
	},

	refresh: function (frm) {
		// Restore signature_target_field options on refresh if target_doctype is set
		if (frm.doc.target_doctype) {
			_update_signature_field_options(frm, frm.doc.target_doctype);
		}

		// Add custom buttons
		if (!frm.is_new()) {
			_add_custom_buttons(frm);
		}

		// Show helpful information
		_show_helpful_info(frm);
	},

	target_doctype: function (frm) {
		// When target DocType changes, update available fields
		if (frm.doc.target_doctype) {
			_update_signature_field_options(frm, frm.doc.target_doctype);
		} else {
			frm.set_df_property("signature_target_field", "options", "");
		}
	},

	signature_target_field: function (frm) {
		// When signature target field is selected, show field info
		if (frm.doc.signature_target_field) {
			_show_field_mapping_info(frm, frm.doc.signature_target_field);
		}
	},

	before_save: function (frm) {
		// Validate target field mapping
		if (frm.doc.signature_target_field && frm.doc.target_doctype) {
			return _validate_field_mapping(frm);
		}
	},
});

function _load_signature_field_options(frm) {
	console.log("[SIGNATURE DEBUG] Loading signature field options...");
	// Load target DocType options
	frappe.call({
		method:
			"print_designer.api.enhance_signature_doctype.get_target_doctype_options",
		callback: function (r) {
			console.log("[SIGNATURE DEBUG] API response:", r);
			if (r.message && r.message.success) {
				console.log(
					"[SIGNATURE DEBUG] Setting options:",
					r.message.options_string,
				);
				frm.set_df_property(
					"target_doctype",
					"options",
					r.message.options_string,
				);
			} else {
				console.log(
					"[SIGNATURE DEBUG] API call failed or returned no success flag",
				);
			}
		},
		error: function (err) {
			console.log("[SIGNATURE DEBUG] API call error:", err);
		},
	});
}

function _update_signature_field_options(frm, target_doctype) {
	console.log(
		"[SIGNATURE DEBUG] Updating signature field options for doctype:",
		target_doctype,
	);

	// Store current value to restore it after updating options
	let current_value = frm.doc.signature_target_field;

	frappe.call({
		method:
			"print_designer.api.enhance_signature_doctype.get_fields_for_target_doctype",
		args: {
			target_doctype: target_doctype,
		},
		callback: function (r) {
			console.log("[SIGNATURE DEBUG] Get fields API response:", r);
			if (r.message && r.message.success) {
				// Create options in format "DocType::fieldname"
				let options = [""];
				r.message.fields.forEach(function (field) {
					options.push(`${target_doctype}::${field.fieldname}`);
				});

				console.log("[SIGNATURE DEBUG] Created options array:", options);
				frm.set_df_property(
					"signature_target_field",
					"options",
					options.join("\n"),
				);
				console.log(
					"[SIGNATURE DEBUG] Set signature_target_field options successfully",
				);

				// Restore the previous value if it's still valid
				if (current_value && options.includes(current_value)) {
					frm.set_value("signature_target_field", current_value);
					console.log("[SIGNATURE DEBUG] Restored field value:", current_value);
				}

				// Show field information
				if (r.message.fields.length > 0) {
					let field_info = r.message.fields
						.map(
							(f) =>
								`• ${f.label} (${f.fieldname}): ${f.description || "No description"}`,
						)
						.join("<br>");

					frm.dashboard.add_comment(
						`Available signature fields for ${target_doctype}:<br>${field_info}`,
						"blue",
					);
				} else {
					frm.dashboard.add_comment(
						`No signature fields defined for ${target_doctype}. You may need to install signature fields first.`,
						"orange",
					);
				}
			} else {
				console.log(
					"[SIGNATURE DEBUG] Get fields API failed or no success flag",
				);
			}
		},
		error: function (err) {
			console.log("[SIGNATURE DEBUG] Get fields API error:", err);
		},
	});
}

function _show_field_mapping_info(frm, field_mapping) {
	frappe.call({
		method:
			"print_designer.api.signature_field_options.get_signature_field_info",
		args: {
			field_mapping: field_mapping,
		},
		callback: function (r) {
			if (r.message && r.message.success) {
				let info = r.message;
				let status = info.field_installed
					? '<span style="color: green;">✓ Installed</span>'
					: '<span style="color: red;">✗ Not Installed</span>';

				frm.dashboard.add_comment(
					`<strong>Target Field Info:</strong><br>
					DocType: ${info.doctype}<br>
					Field: ${info.fieldname} (${info.usage_info.label})<br>
					Status: ${status}<br>
					Description: ${info.usage_info.description || "No description"}`,
					info.field_installed ? "green" : "orange",
				);
			} else if (r.message && r.message.error) {
				frm.dashboard.add_comment(
					`<strong>Field Mapping Error:</strong> ${r.message.error}`,
					"red",
				);
			}
		},
	});
}

function _add_custom_buttons(frm) {
	// Sync to target field button
	if (frm.doc.signature_target_field && frm.doc.signature_image) {
		frm.add_custom_button(
			__("Sync to Target Field"),
			function () {
				frappe.call({
					method:
						"print_designer.api.signature_sync.sync_signature_to_target_field",
					args: {
						signature_record_name: frm.doc.name,
					},
					callback: function (r) {
						if (r.message && r.message.success) {
							frappe.msgprint({
								title: __("Sync Successful"),
								message: `Signature synced to ${r.message.target_doctype}.${r.message.target_field}`,
								indicator: "green",
							});
						} else {
							frappe.msgprint({
								title: __("Sync Failed"),
								message: r.message.error || "Unknown error occurred",
								indicator: "red",
							});
						}
					},
				});
			},
			__("Actions"),
		);
	}

	// Install signature fields button
	frm.add_custom_button(
		__("Install Signature Fields"),
		function () {
			frappe.call({
				method:
					"print_designer.api.signature_field_installer.install_signature_fields",
				callback: function (r) {
					if (r.message && r.message.success) {
						frappe.msgprint({
							title: __("Installation Successful"),
							message: `Installed signature fields for ${r.message.doctypes.length} DocTypes`,
							indicator: "green",
						});
						frm.reload_doc();
					} else {
						frappe.msgprint({
							title: __("Installation Failed"),
							message: r.message.error || "Unknown error occurred",
							indicator: "red",
						});
					}
				},
			});
		},
		__("Setup"),
	);
}

function _show_helpful_info(frm) {
	if (frm.is_new()) {
		frm.dashboard.add_comment(
			`<strong>Quick Setup Guide:</strong><br>
			1. Select the target DocType (e.g., Company, User, Employee)<br>
			2. Choose the signature field you want to populate<br>
			3. Upload your signature image<br>
			4. Save - the signature will auto-populate the target field`,
			"blue",
		);
	}
}

function _validate_field_mapping(frm) {
	return new Promise((resolve) => {
		frappe.call({
			method:
				"print_designer.api.signature_field_options.parse_signature_field_mapping",
			args: {
				field_mapping: frm.doc.signature_target_field,
			},
			callback: function (r) {
				if (r.message && r.message.error) {
					frappe.msgprint({
						title: __("Invalid Field Mapping"),
						message: r.message.error,
						indicator: "red",
					});
					resolve(false);
				} else {
					resolve(true);
				}
			},
		});
	});
}
