// Copyright (c) 2026, MooCoding and contributors
// For license information, please see license.txt

// The client workflow of the settings of the Thai tax.
//
// The buttons of the form call the endpoints of the controller of Print
// Designer.  The account fields are only checked when the doctype really
// carries them: a site may install the settings without the accounts, and
// the form then says nothing about accounts that it does not show.

frappe.ui.form.on("Thai Tax Settings", {
	refresh(frm) {
		// Add custom buttons for account creation and validation
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Create Thai Tax Accounts"),
				function () {
					create_thai_tax_accounts(frm);
				},
				__("Actions"),
			);

			frm.add_custom_button(
				__("Validate Setup"),
				function () {
					validate_thai_tax_setup(frm);
				},
				__("Actions"),
			);

			frm.add_custom_button(
				__("Install Thai Tax Fields"),
				function () {
					install_thai_tax_fields(frm);
				},
				__("Setup"),
			);

			frm.add_custom_button(
				__("Check System Status"),
				function () {
					check_thai_tax_system(frm);
				},
				__("Setup"),
			);
		}

		// Show helpful information
		if (frm.doc.auto_create_accounts) {
			frm.dashboard.add_comment(
				__(
					"Auto-create accounts is enabled. Tax accounts will be created automatically when you save this document.",
				),
				"blue",
				true,
			);
		}

		// Add indicators for account status
		show_account_indicators(frm);
	},

	auto_create_accounts(frm) {
		if (frm.doc.auto_create_accounts) {
			frappe.msgprint({
				title: __("Auto-Create Accounts Enabled"),
				message: __(
					"When you save this document, the system will automatically create Thai tax accounts if they don't exist.",
				),
				indicator: "blue",
			});
		}
	},

	default_wht_payable_account(frm) {
		validate_account_type(frm, "default_wht_payable_account", [
			"Payable",
			"Tax",
		]);
	},

	default_wht_receivable_account(frm) {
		validate_account_type(frm, "default_wht_receivable_account", [
			"Receivable",
			"Tax",
		]);
	},

	default_vat_input_account(frm) {
		validate_account_type(frm, "default_vat_input_account", ["Tax"]);
	},

	default_vat_output_account(frm) {
		validate_account_type(frm, "default_vat_output_account", ["Tax"]);
	},

	vat_rate(frm) {
		if (frm.doc.vat_rate < 0 || frm.doc.vat_rate > 100) {
			frappe.msgprint(__("VAT rate should be between 0 and 100 percent"));
			frm.set_value("vat_rate", 7.0);
		}
	},
});

frappe.ui.form.on("Thai WHT Rate Setting", {
	tax_rate(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.tax_rate < 0 || row.tax_rate > 100) {
			frappe.msgprint(__("WHT rate should be between 0 and 100 percent"));
			frappe.model.set_value(cdt, cdn, "tax_rate", 3.0);
		}
	},
});

function create_thai_tax_accounts(frm) {
	frappe.call({
		method: "print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings.create_thai_tax_accounts",
		args: {
			company: frappe.defaults.get_user_default("Company"),
		},
		freeze: true,
		freeze_message: __("Creating Thai Tax Accounts..."),
		callback: function (r) {
			if (r.message) {
				frappe.msgprint({
					title: __("Success"),
					message: r.message,
					indicator: "green",
				});
				frm.reload_doc();
			}
		},
	});
}

function validate_thai_tax_setup(frm) {
	// Check required accounts
	const missing_accounts = account_fields_of_the_form(frm)
		.filter((field) => !frm.doc[field.fieldname])
		.map((field) => field.label);

	let validation_msg = "";

	if (missing_accounts.length > 0) {
		validation_msg += `<strong>${__("Missing Accounts:")}</strong><br>`;
		missing_accounts.forEach((account) => {
			validation_msg += `• ${account}<br>`;
		});
		validation_msg += "<br>";
	}

	// Check WHT rates
	if (!frm.doc.default_wht_rates || frm.doc.default_wht_rates.length === 0) {
		validation_msg += `<strong>${__("Warning:")}</strong> No default WHT rates configured.<br><br>`;
	}

	if (validation_msg) {
		validation_msg += `<div class="text-muted">${__("Use 'Create Thai Tax Accounts' to automatically create missing accounts.")}</div>`;

		frappe.msgprint({
			title: __("Thai Tax Setup Validation"),
			message: validation_msg,
			indicator: missing_accounts.length > 0 ? "red" : "yellow",
		});
	} else {
		frappe.msgprint({
			title: __("Thai Tax Setup Validation"),
			message: __("✅ Thai tax setup is complete and valid!"),
			indicator: "green",
		});
	}
}

function install_thai_tax_fields(frm) {
	frappe.call({
		method: "print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings.install_thai_tax_fields",
		freeze: true,
		freeze_message: __("Installing Thai Tax Fields..."),
		callback: function (r) {
			if (r.message) {
				frappe.msgprint({
					title: __("Thai Tax Fields"),
					message: r.message,
					indicator: "green",
				});
			}
		},
	});
}

function check_thai_tax_system(frm) {
	frappe.call({
		method: "print_designer.print_designer.doctype.thai_tax_settings.thai_tax_settings.check_thai_tax_system",
		freeze: true,
		freeze_message: __("Checking Thai Tax System..."),
		callback: function (r) {
			if (r.message) {
				frappe.msgprint({
					title: __("Thai Tax System Status"),
					message: the_message_of_the_status(r.message),
					indicator: the_indicator_of_the_status(r.message),
				});
			}
		},
		error: function (r) {
			frappe.msgprint({
				title: __("System Check Error"),
				message: __("Error checking Thai tax system: {0}", [
					r.message || "Unknown error",
				]),
				indicator: "red",
			});
		},
	});
}

// The message of the status of the system of the tax.
function the_message_of_the_status(result) {
	let message = "";

	// Build status message
	message += `<strong>${__("Thai Tax Settings:")}</strong> ${result.thai_tax_settings_exists ? "✅ Installed" : "❌ Not installed"}<br><br>`;

	message += `<strong>${__("Thai Tax Fields:")}</strong><br>`;
	message += `• Total fields: ${result.total_fields}<br>`;
	message += `• Installed: ${result.installed_fields}<br>`;
	message += `• Missing: ${result.total_fields - result.installed_fields}<br><br>`;

	if (result.missing_fields && result.missing_fields.length > 0) {
		message += `<strong>${__("Missing Fields:")}</strong><br>`;
		result.missing_fields.forEach((field) => {
			message += `• ${field}<br>`;
		});
		message += "<br>";
	}

	message += `<strong>${__("Thai Tax Accounts:")}</strong><br>`;
	message += `• WHT Payable: ${result.configured_accounts.wht_payable || "❌ Not configured"}<br>`;
	message += `• WHT Receivable: ${result.configured_accounts.wht_receivable || "❌ Not configured"}<br>`;
	message += `• VAT Input: ${result.configured_accounts.vat_input || "❌ Not configured"}<br>`;
	message += `• VAT Output: ${result.configured_accounts.vat_output || "❌ Not configured"}<br><br>`;

	if (result.all_fields_installed && result.accounts_configured) {
		message += `<div class="text-success">🎉 ${__("All Thai tax system components are properly installed!")}</div>`;
	} else {
		message += `<div class="text-warning">💡 ${__("Use the 'Install Thai Tax Fields' and 'Create Thai Tax Accounts' buttons to complete setup.")}</div>`;
	}

	return message;
}

// The colour of the message of the status of the system of the tax.
function the_indicator_of_the_status(result) {
	if (result.status === "error") {
		return "red";
	}

	if (result.all_fields_installed && result.accounts_configured) {
		return "green";
	}

	return "yellow";
}

function validate_account_type(frm, fieldname, allowed_types) {
	let account = frm.doc[fieldname];
	if (account) {
		frappe.db.get_value("Account", account, "account_type", function (r) {
			if (
				r &&
				r.account_type &&
				!allowed_types.includes(r.account_type)
			) {
				frappe.msgprint({
					title: __("Invalid Account Type"),
					message: __("Selected account must be of type: {0}", [
						allowed_types.join(", "),
					]),
					indicator: "red",
				});
				frm.set_value(fieldname, "");
			}
		});
	}
}

function show_account_indicators(frm) {
	// Add indicators next to account fields to show if accounts exist
	for (const field of account_fields_of_the_form(frm)) {
		let account = frm.doc[field.fieldname];
		if (account) {
			frappe.db.get_value("Account", account, "name", function (r) {
				if (r && r.name) {
					frm.fields_dict[field.fieldname].$wrapper
						.find(".control-input")
						.append(
							'<span class="indicator-pill green" title="Account exists">✓</span>',
						);
				} else {
					frm.fields_dict[field.fieldname].$wrapper
						.find(".control-input")
						.append(
							'<span class="indicator-pill red" title="Account not found">✗</span>',
						);
				}
			});
		}
	}
}

// The account fields of the form.
//
// The settings do not carry the accounts on every site, so only the fields
// that the doctype really has are looked at.
function account_fields_of_the_form(frm) {
	const candidates = [
		{
			fieldname: "default_wht_payable_account",
			label: __("Default WHT Payable Account"),
		},
		{
			fieldname: "default_wht_receivable_account",
			label: __("Default WHT Receivable Account"),
		},
		{
			fieldname: "default_vat_input_account",
			label: __("Default VAT Input Account"),
		},
		{
			fieldname: "default_vat_output_account",
			label: __("Default VAT Output Account"),
		},
	];

	if (!frm.meta || !frm.meta.has_field) {
		return candidates;
	}

	return candidates.filter((field) => frm.meta.has_field(field.fieldname));
}
