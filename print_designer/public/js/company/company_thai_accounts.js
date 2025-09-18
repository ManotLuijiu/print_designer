/**
 * Company Thai Account Translation System
 *
 * This file handles the Thai accounting translation features for Company DocType:
 * 1. enable_thai_accounting_translation - Checkbox to enable/disable Thai translation feature
 * 2. auto_populate_thai_accounts - Button to auto-translate account names to Thai
 * 3. thailand_service_business - Enable WHT features
 * 4. construction_service - Enable retention features
 * 5. default_retention_rate - Set default retention percentage
 */

frappe.ui.form.on("Company", {
	onload: function (frm) {
		console.log("🔍 DEBUG: Company form onload");
		console.log("📋 Company name:", frm.doc.name);

		// List all Thai-related fields for debugging
		const thaiFields = [
			"enable_thai_accounting_translation",
			"auto_populate_thai_accounts",
			"thailand_service_business",
			"default_wht_rate",
			"default_wht_account",
			"construction_service",
			"default_retention_rate",
			"default_retention_account",
		];

		console.log("🔍 DEBUG: Checking Thai-related fields:");
		thaiFields.forEach((field) => {
			if (frm.fields_dict[field]) {
				console.log(`  ✅ ${field}: Found`);
				if (frm.doc[field] !== undefined) {
					console.log(`     Value: ${frm.doc[field]}`);
				}
			} else {
				console.log(`  ❌ ${field}: Not found`);
			}
		});
	},

	refresh: function (frm) {
		console.log("🔍 DEBUG: Company form refresh");
		console.log(
			"🌍 Thai accounting enabled:",
			frm.doc.enable_thai_accounting_translation,
		);
		console.log("🏗️ Construction service:", frm.doc.construction_service);

		// Setup auto-populate Thai accounts button
		if (frm.fields_dict.auto_populate_thai_accounts) {
			console.log("🔘 DEBUG: Setting up auto_populate_thai_accounts button");

			// Find the button element and attach click handler
			frm.fields_dict.auto_populate_thai_accounts.$wrapper
				.find("button")
				.off("click") // Remove any existing handlers
				.on("click", function () {
					console.log("🚀 DEBUG: auto_populate_thai_accounts button clicked!");
					console.log("📊 Company:", frm.doc.name);

					// Show confirmation dialog
					frappe.confirm(
						"This will auto-populate Thai translations for all standard account names in this company. Continue?",
						function () {
							console.log("✅ DEBUG: User confirmed - calling server method");

							// Call the server-side method
							frappe.call({
								method:
									"print_designer.print_designer.commands.install_account_thai_fields.auto_populate_company_thai_accounts",
								args: {
									company: frm.doc.name,
								},
								freeze: true,
								freeze_message: "Auto-populating Thai account names...",
								callback: function (response) {
									console.log("📥 DEBUG: Server response:", response);

									if (response.message) {
										console.log("✅ DEBUG: Response details:", {
											status: response.message.status,
											accounts_updated: response.message.accounts_updated,
										});

										if (response.message.status === "success") {
											frappe.show_alert(
												{
													message: __(
														`Successfully updated Thai names for ${response.message.accounts_updated} accounts`,
													),
													indicator: "green",
												},
												5,
											);

											// Log each update for debugging
											console.log(
												`✅ DEBUG: ${response.message.accounts_updated} accounts updated with Thai translations`,
											);

											// Refresh Chart of Accounts if open
											if (frappe.pages && frappe.pages["Accounts Browser"]) {
												console.log("🔄 DEBUG: Refreshing Chart of Accounts");
												frappe.pages["Accounts Browser"].refresh();
											}
										}
									}
								},
								error: function (error) {
									console.error("❌ DEBUG: Server error:", error);
									frappe.show_alert(
										{
											message: __(
												"Error auto-populating Thai account names. Check console for details.",
											),
											indicator: "red",
										},
										10,
									);
								},
							});
						},
						function () {
							console.log("❌ DEBUG: User cancelled auto-population");
						},
					);
				});

			console.log("✅ DEBUG: Button handler attached");

			// Add visual indicator when Thai translation is enabled
			if (frm.doc.enable_thai_accounting_translation) {
				frm.fields_dict.auto_populate_thai_accounts.$wrapper
					.find("button")
					.addClass("btn-primary");
			}
		} else {
			console.warn(
				"⚠️ DEBUG: auto_populate_thai_accounts button field not found",
			);
		}
	},

	/**
	 * When enable_thai_accounting_translation checkbox is toggled
	 * This enables/disables the Thai translation feature for Chart of Accounts
	 */
	enable_thai_accounting_translation: function (frm) {
		console.log(
			"🔄 DEBUG: enable_thai_accounting_translation toggled:",
			frm.doc.enable_thai_accounting_translation,
		);

		if (frm.doc.enable_thai_accounting_translation) {
			console.log("✅ DEBUG: Thai translation ENABLED");

			// Show the auto-populate button more prominently
			if (frm.fields_dict.auto_populate_thai_accounts) {
				frm.fields_dict.auto_populate_thai_accounts.$wrapper.show();
				frm.fields_dict.auto_populate_thai_accounts.$wrapper
					.find("button")
					.addClass("btn-primary")
					.attr(
						"title",
						"Click to automatically translate common account names to Thai",
					);
			}

			frappe.show_alert(
				{
					message: __(
						'Thai accounting translation enabled. Click "Auto-populate Thai Account Names" to translate existing accounts.',
					),
					indicator: "blue",
				},
				7,
			);
		} else {
			console.log("❌ DEBUG: Thai translation DISABLED");

			// Make button less prominent when disabled
			if (frm.fields_dict.auto_populate_thai_accounts) {
				frm.fields_dict.auto_populate_thai_accounts.$wrapper
					.find("button")
					.removeClass("btn-primary");
			}
		}
	},

	/**
	 * When thailand_service_business checkbox is toggled
	 * This enables/disables WHT (Withholding Tax) features
	 */
	thailand_service_business: function (frm) {
		console.log(
			"🔄 DEBUG: thailand_service_business toggled:",
			frm.doc.thailand_service_business,
		);

		if (frm.doc.thailand_service_business) {
			console.log("✅ DEBUG: Thailand service business ENABLED");
			console.log("  - WHT Rate:", frm.doc.default_wht_rate || "Not set");
			console.log("  - WHT Account:", frm.doc.default_wht_account || "Not set");

			// Set default WHT rate if not set
			if (!frm.doc.default_wht_rate) {
				frm.set_value("default_wht_rate", 3.0);
				console.log("  📝 DEBUG: Set default WHT rate to 3%");
			}
		} else {
			console.log("❌ DEBUG: Thailand service business DISABLED");
		}
	},

	/**
	 * When construction_service checkbox is toggled
	 * This enables/disables retention features for construction industry
	 */
	construction_service: function (frm) {
		console.log(
			"🔄 DEBUG: construction_service toggled:",
			frm.doc.construction_service,
		);

		if (frm.doc.construction_service) {
			console.log("✅ DEBUG: Construction service ENABLED");
			console.log(
				"  - Retention Rate:",
				frm.doc.default_retention_rate || "Not set",
			);
			console.log(
				"  - Retention Account:",
				frm.doc.default_retention_account || "Not set",
			);

			// Set default retention rate if not set
			if (!frm.doc.default_retention_rate) {
				frm.set_value("default_retention_rate", 5.0);
				console.log("  📝 DEBUG: Set default retention rate to 5%");
			}

			frappe.show_alert(
				{
					message: __(
						"Construction service enabled. Configure retention settings for construction projects.",
					),
					indicator: "blue",
				},
				5,
			);
		} else {
			console.log("❌ DEBUG: Construction service DISABLED");
		}
	},

	/**
	 * When default_retention_rate is changed
	 */
	default_retention_rate: function (frm) {
		console.log(
			"📊 DEBUG: default_retention_rate changed to:",
			frm.doc.default_retention_rate,
		);

		if (frm.doc.default_retention_rate) {
			if (frm.doc.default_retention_rate > 10) {
				console.warn("⚠️ DEBUG: Retention rate is unusually high (> 10%)");
				frappe.show_alert(
					{
						message: __(
							"Note: Retention rate is typically 5-10% for construction projects",
						),
						indicator: "yellow",
					},
					5,
				);
			} else if (frm.doc.default_retention_rate < 3) {
				console.log("ℹ️ DEBUG: Low retention rate (< 3%)");
			}
		}
	},

	/**
	 * When default_wht_rate is changed
	 */
	default_wht_rate: function (frm) {
		console.log(
			"📊 DEBUG: default_wht_rate changed to:",
			frm.doc.default_wht_rate,
		);

		// Thai WHT rates are typically:
		// - 3% for services
		// - 1% for transportation
		// - 5% for rental
		if (
			frm.doc.default_wht_rate &&
			(frm.doc.default_wht_rate < 1 || frm.doc.default_wht_rate > 5)
		) {
			console.warn("⚠️ DEBUG: WHT rate outside typical range (1-5%)");
		}
	},
});

// Add document ready handler to check if fields are properly loaded
$(document).ready(function () {
	console.log("📄 DEBUG: company_thai_accounts.js loaded and ready");

	// Monitor for button element creation
	const observer = new MutationObserver(function (mutations) {
		mutations.forEach(function (mutation) {
			if (mutation.addedNodes.length) {
				mutation.addedNodes.forEach(function (node) {
					if (node.nodeType === 1) {
						// Element node
						// Check if it's our button
						const $button = $(node).find(
							'[data-fieldname="auto_populate_thai_accounts"] button',
						);
						if ($button.length > 0) {
							console.log(
								"🔘 DEBUG: auto_populate_thai_accounts button added to DOM",
							);
							$button.attr(
								"title",
								"Auto-translate standard account names to Thai",
							);
						}
					}
				});
			}
		});
	});

	// Start observing
	if (document.body) {
		observer.observe(document.body, {
			childList: true,
			subtree: true,
		});
	}
});

console.log("✅ DEBUG: Company Thai Accounts script loaded successfully");
