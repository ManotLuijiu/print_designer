/**
 * Client-side functionality for Print Designer QR Delivery Approval and Thai WHT systems
 * Provides form customizations for Delivery Note and Payment Entry DocTypes
 */

// ==================================================
// CONFIGURATION
// ==================================================

const CONFIG = {
	DEBUG_MODE: frappe.boot.developer_mode || false,
	QR_GENERATION: {
		AUTO_SHOW_DELAY: 500,
		PROGRESS_DELAY: 30,
		MAX_RETRIES: 3,
		RETRY_BASE_DELAY: 1000 // Exponential backoff base
	},
	WHT: {
		DEFAULT_RATES: {
			SERVICE: 3,
			RENTAL: 1,
			ROYALTY: 5
		},
		DEBOUNCE_DELAY: 300
	},
	PRINT_FORMATS: {
		DELIVERY_WITH_QR: "Delivery Note with QR Approval",
		WHT_CERTIFICATE: "Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate"
	},
	POPUP_BLOCKED_CHECK_DELAY: 1000
};

// ==================================================
// UTILITY FUNCTIONS
// ==================================================

function debugLog(...args) {
	if (CONFIG.DEBUG_MODE) {
		console.log(...args);
	}
}

function debugError(...args) {
	if (CONFIG.DEBUG_MODE) {
		console.error(...args);
	}
}

const debounce = (func, delay) => {
	let timeoutId;
	return function (...args) {
		clearTimeout(timeoutId);
		timeoutId = setTimeout(() => func.apply(this, args), delay);
	};
};

function isValidApprovalURL(url) {
	try {
		const urlObj = new URL(url);

		// Check protocol
		if (!['http:', 'https:'].includes(urlObj.protocol)) {
			return { valid: false, error: "Invalid protocol" };
		}

		// Check host (should not be localhost in production)
		if (!frappe.boot.developer_mode && urlObj.hostname === 'localhost') {
			return { valid: false, error: "Localhost URL not allowed in production" };
		}

		// Check required parameters
		const hasDN = urlObj.searchParams.has('dn');
		const hasToken = urlObj.searchParams.has('token');

		if (!hasDN || !hasToken) {
			return { valid: false, error: "Missing required URL parameters (dn and token)" };
		}

		return { valid: true };
	} catch (e) {
		return { valid: false, error: e.message };
	}
}

function format_currency(amount) {
	return frappe.format(amount, { fieldtype: "Currency" });
}

function get_status_color(status) {
	switch (status) {
		case "Approved":
			return "success";
		case "Rejected":
			return "danger";
		default:
			return "warning";
	}
}

// ==================================================
// DELIVERY NOTE QR APPROVAL SYSTEM
// ==================================================

frappe.ui.form.on("Delivery Note", {
	refresh: function (frm) {
		add_delivery_note_buttons(frm);
		// ❌ REMOVED: show_qr_code_if_available(frm) - No auto-popup
		update_approval_status_indicator(frm);
		add_custom_css_for_qr_fields(frm);
		show_qr_available_notification(frm);
	},

	custom_goods_received_status: function (frm) {
		update_approval_status_indicator(frm);
	},

	on_submit: function (frm) {
		// QR code is now generated server-side automatically on submit
		// Just reload to refresh the UI and show the QR notification banner
		setTimeout(() => {
			frm.reload_doc();
		}, 500); // Small delay to ensure server-side generation completes
	},
});

function add_delivery_note_buttons(frm) {
	debugLog("🔍 Checking button availability for:", frm.doc.name);
	debugLog("Document Status:", frm.doc.docstatus, "(1=submitted)");
	debugLog("Has QR Code:", !!frm.doc.custom_approval_qr_code);
	debugLog("Has Approval URL:", !!frm.doc.custom_approval_url);
	debugLog("Goods Status:", frm.doc.custom_goods_received_status);

	// Add QR generation button for submitted delivery notes without QR
	if (frm.doc.docstatus === 1 && !frm.doc.custom_approval_qr_code) {
		debugLog("✅ Adding 'Generate QR Code' button");
		frm.add_custom_button(
			__("Generate QR Code"),
			function () {
				generate_qr_code(frm);
			},
			__("Actions"),
		);
	}

	// Add approval page viewing button
	if (frm.doc.custom_approval_url) {
		debugLog("✅ Adding 'View Approval Page' button");
		frm.add_custom_button(
			__("View Approval Page"),
			function () {
				view_approval_page(frm);
			},
			__("Actions"),
		);
	}

	// Add QR code display button
	if (frm.doc.custom_approval_qr_code) {
		debugLog("✅ Adding 'Show QR Code' button");
		frm.add_custom_button(
			__("Show QR Code"),
			function () {
				debugLog("📱 Showing QR Code dialog for:", frm.doc.name);
				show_qr_code_dialog(frm);
			},
			__("Actions"),
		);
	}

	// Add print with QR button
	if (frm.doc.custom_approval_qr_code) {
		debugLog("✅ Adding 'Print with QR' button");
		frm.add_custom_button(
			__("Print with QR"),
			function () {
				debugLog("🖨️ Printing delivery note with QR for:", frm.doc.name);
				print_delivery_note_with_qr(frm);
			},
			__("Print"),
		);
	}
}

function view_approval_page(frm) {
	debugLog("🔗 Opening Approval Page");
	debugLog("Delivery Note:", frm.doc.name);
	debugLog("Approval URL:", frm.doc.custom_approval_url);

	try {
		const url = frm.doc.custom_approval_url;

		// Validate URL
		if (!url || url.trim() === "") {
			frappe.msgprint({
				title: __("Error"),
				message: __("No approval URL found. Please generate a QR code first."),
				indicator: "red",
			});
			return;
		}

		// Validate URL format
		const validation = isValidApprovalURL(url);
		if (!validation.valid) {
			frappe.msgprint({
				title: __("Invalid URL"),
				message: __("Error: {0}", [validation.error]),
				indicator: "red",
			});
			return;
		}

		const urlObj = new URL(url);
		debugLog("URL Analysis:", {
			protocol: urlObj.protocol,
			host: urlObj.host,
			pathname: urlObj.pathname,
			searchParams: Object.fromEntries(urlObj.searchParams),
		});

		// Show confirmation dialog
		frappe.confirm(
			__("Open the delivery approval page in a new tab?") +
				"<br><br><strong>URL:</strong> " +
				url.substring(0, 80) +
				(url.length > 80 ? "..." : "") +
				"<br><strong>Delivery Note:</strong> " +
				frm.doc.name +
				"<br><strong>Status:</strong> " +
				(frm.doc.custom_goods_received_status || "Pending"),
			function () {
				debugLog("✅ User confirmed - opening approval page");
				const newWindow = window.open(url, "_blank");

				// Check if popup was blocked
				setTimeout(function () {
					if (!newWindow || newWindow.closed) {
						debugLog("❌ Popup blocked or failed to open");
						frappe.msgprint({
							title: __("Popup Blocked"),
							message:
								__(
									"Please allow popups for this site and try again. Alternatively, copy this URL: ",
								) +
								"<br><br><input type='text' class='form-control' value='" +
								url +
								"' readonly onclick='this.select()'>",
							indicator: "yellow",
						});
					} else {
						debugLog("✅ Approval page opened successfully");
						frappe.show_alert(
							{
								message: __("Approval page opened in new tab"),
								indicator: "green",
							},
							3,
						);
					}
				}, CONFIG.POPUP_BLOCKED_CHECK_DELAY);
			},
			function () {
				debugLog("❌ User cancelled approval page opening");
			},
		);
	} catch (error) {
		debugError("❌ Error opening approval page:", error);
		frappe.msgprint({
			title: __("Error"),
			message: __("Invalid approval URL format. Error: ") + error.message,
			indicator: "red",
		});
	}
}

function generate_qr_code(frm, retryCount = 0, silent = false) {
	debugLog("🔄 Starting QR code generation for:", frm.doc.name, "Retry:", retryCount, "Silent:", silent);

	frappe.show_progress(
		__("Generating QR Code"),
		CONFIG.QR_GENERATION.PROGRESS_DELAY,
		100,
		__("Please wait..."),
	);

	frappe.call({
		method: "print_designer.custom.delivery_note_qr.generate_delivery_approval_qr",
		args: {
			delivery_note_name: frm.doc.name,
		},
		callback: function (r) {
			debugLog("📡 QR generation API response:", r);
			frappe.hide_progress();

			if (r.message?.qr_code) {
				debugLog("✅ QR code generated successfully");

				// Update the document with QR code data
				frappe.model.set_value(
					frm.doctype,
					frm.docname,
					"custom_approval_qr_code",
					r.message.qr_code,
				);
				frappe.model.set_value(
					frm.doctype,
					frm.docname,
					"custom_approval_url",
					r.message.approval_url,
				);

				debugLog("💾 Saving document with QR data");
				frm
					.save()
					.then(() => {
						debugLog("✅ Document saved successfully");
						// Ensure form is fully reloaded before showing dialogs or accessing grid
						debugLog("🔄 Reloading document to ensure all data is fresh");
						return frm.reload_doc();
					})
					.then(() => {
						debugLog("✅ Document reloaded successfully");

						if (!silent) {
							// Only show success message and dialog if not in silent mode
							frappe.msgprint({
								title: __("QR Code Generated Successfully"),
								message: __(
									"QR Code has been generated. Customer can scan this code to approve delivery receipt.",
								),
								indicator: "green",
							});

							// Show QR code dialog immediately
							debugLog("📱 Opening QR code dialog");
							setTimeout(() => show_qr_code_dialog(frm), CONFIG.QR_GENERATION.AUTO_SHOW_DELAY);
						} else {
							debugLog("✅ QR code generated silently (no dialog shown)");
							// Show subtle notification instead
							frappe.show_alert({
								message: __("QR Code generated successfully"),
								indicator: "green",
							}, 3);
						}
					})
					.catch((error) => {
						debugError("❌ Error saving/reloading document:", error);
						frappe.msgprint({
							title: __("Save Error"),
							message:
								__("QR code generated but failed to save. Error: ") +
								(error.message || error),
							indicator: "orange",
						});
					});
			} else {
				debugLog("❌ QR code generation failed - no QR code in response");
				frappe.msgprint({
					title: __("Error"),
					message:
						__("Failed to generate QR code. Please try again.") +
						(r.message ? " Response: " + JSON.stringify(r.message) : ""),
					indicator: "red",
				});
			}
		},
		error: function (r) {
			frappe.hide_progress();

			if (retryCount < CONFIG.QR_GENERATION.MAX_RETRIES) {
				// Retry with exponential backoff
				const delay = Math.pow(2, retryCount) * CONFIG.QR_GENERATION.RETRY_BASE_DELAY;
				frappe.show_alert({
					message: __("Retrying... (Attempt {0}/{1})", [
						retryCount + 1,
						CONFIG.QR_GENERATION.MAX_RETRIES,
					]),
					indicator: "orange",
				});

				setTimeout(() => generate_qr_code(frm, retryCount + 1, silent), delay);
			} else {
				// Final failure
				debugError("❌ QR generation API error after retries:", r);
				frappe.msgprint({
					title: __("QR Generation Failed"),
					message: __(
						"Failed after {0} attempts: {1}",
						[CONFIG.QR_GENERATION.MAX_RETRIES, r.message || "Unknown error"],
					),
					indicator: "red",
				});
			}
		},
	});
}

function show_qr_code_dialog(frm) {
	if (!frm.doc.custom_approval_qr_code) {
		frappe.msgprint(__("No QR code available. Please generate one first."));
		return;
	}

	// Clean up existing dialog if any
	if (frm._qr_dialog) {
		frm._qr_dialog.$wrapper.remove();
		frm._qr_dialog = null;
	}

	frm._qr_dialog = new frappe.ui.Dialog({
		title: __("Delivery Approval QR Code"),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "qr_code_html",
				options: `
					<div class="qr-dialog-content text-center">
						<div class="qr-header">
							<h4 style="color: #2c3e50; margin-bottom: 15px;">
								<i class="fa fa-qrcode" style="margin-right: 8px;"></i>
								Scan to Approve Delivery
							</h4>
						</div>

						<div class="qr-code-container" style="margin: 20px 0;">
							<img src="data:image/png;base64,${frm.doc.custom_approval_qr_code}"
								 style="max-width: 280px; max-height: 280px; border: 2px solid #e9ecef; border-radius: 8px; padding: 10px; background: #fff;"
								 alt="QR Code for Delivery Approval" />
						</div>

						<div class="qr-instructions" style="padding: 15px; border-radius: 6px; margin: 15px 0;">
							<p class="text-muted mb-2">
								<i class="fa fa-mobile" style="margin-right: 5px;"></i>
								Customer can scan this QR code with their mobile phone to:
							</p>
							<ul class="text-left" style="margin: 10px 0; padding-left: 20px;">
								<li>✅ Approve goods received</li>
								<li>❌ Report delivery issues</li>
								<li>🖊️ Add digital signature</li>
								<li>📝 View delivery details</li>
							</ul>
						</div>

						<div class="qr-url-section">
							<p><strong>Direct URL:</strong></p>
							<a href="${frm.doc.custom_approval_url}" target="_blank"
							   style="word-break: break-all; color: #007bff; text-decoration: none;">
							   ${frm.doc.custom_approval_url}
							</a>
						</div>

						<div class="qr-status mt-3">
							<span class="badge badge-${get_status_color(frm.doc.custom_goods_received_status)}">
								Status: ${frm.doc.custom_goods_received_status || "Pending"}
							</span>
						</div>
					</div>

					<style>
						.qr-dialog-content {
							padding: 10px;
						}
						.qr-code-container img:hover {
							transform: scale(1.05);
							transition: transform 0.2s ease;
						}
					</style>
				`,
			},
		],
		size: "large",
		primary_action_label: __("Print with QR Code"),
		primary_action: function () {
			print_delivery_note_with_qr(frm);
			frm._qr_dialog.hide();
		},
		secondary_action_label: __("Copy URL"),
		secondary_action: function () {
			navigator.clipboard.writeText(frm.doc.custom_approval_url).then(() => {
				frappe.show_alert({
					message: __("Approval URL copied to clipboard"),
					indicator: "green",
				});
			});
		},
		onhide: function () {
			// Clean up when dialog is hidden
			if (frm._qr_dialog) {
				frm._qr_dialog.$wrapper.remove();
				frm._qr_dialog = null;
			}
		},
	});

	frm._qr_dialog.show();
}

function print_delivery_note_with_qr(frm) {
	frappe.route_options = {
		format: CONFIG.PRINT_FORMATS.DELIVERY_WITH_QR,
	};
	frappe.set_route("print", frm.doctype, frm.docname);
}

function show_qr_available_notification(frm) {
	// Show a subtle indicator when QR code is available
	// User can click "Show QR Code" button to view it
	if (frm.doc.custom_approval_qr_code && frm.doc.docstatus === 1) {
		// Only show notification once per session
		if (!frm._qr_notification_shown) {
			frm._qr_notification_shown = true;

			debugLog("ℹ️ QR code available - showing notification indicator");

			// Add a subtle info indicator to the dashboard
			if (frm.dashboard && frm.dashboard.add_comment) {
				frm.dashboard.add_comment(
					__("📱 Customer QR approval code is ready. Click 'Show QR Code' button to view."),
					"blue",
					true // Clear existing comments
				);
			}
		}
	}
}

function update_approval_status_indicator(frm) {
	// Safety check for dashboard methods
	if (!frm.dashboard || !frm.dashboard.add_indicator) {
		debugLog("Dashboard methods not available");
		return;
	}

	// Clear existing indicators
	if (frm.dashboard.clear_indicator) {
		frm.dashboard.clear_indicator();
	} else if (frm.dashboard.indicators) {
		frm.dashboard.indicators = [];
		frm.dashboard.refresh();
	}

	const status = frm.doc.custom_goods_received_status;

	if (status === "Approved") {
		frm.dashboard.add_indicator(__("Goods Received: Approved"), "green");
		if (frm.doc.custom_customer_approval_date && frm.dashboard.add_comment) {
			frm.dashboard.add_comment(
				__("Approved on: ") +
					frappe.datetime.str_to_user(frm.doc.custom_customer_approval_date),
				"green",
			);
		}
	} else if (status === "Rejected") {
		frm.dashboard.add_indicator(__("Goods Received: Rejected"), "red");
		if (frm.doc.custom_rejection_reason && frm.dashboard.add_comment) {
			frm.dashboard.add_comment(
				__("Reason: ") + frm.doc.custom_rejection_reason,
				"red",
			);
		}
	} else {
		frm.dashboard.add_indicator(__("Goods Received: Pending"), "orange");
		if (frm.doc.custom_approval_url && frm.dashboard.add_comment) {
			frm.dashboard.add_comment(
				__("Waiting for customer approval via QR code"),
				"orange",
			);
		}
	}
}

function add_custom_css_for_qr_fields(frm) {
	// Add custom styling for QR-related fields
	if (frm.doc.custom_approval_qr_code) {
		frm
			.get_field("custom_approval_qr_code")
			.$wrapper.find(".control-input")
			.css({
				"max-height": "100px",
				overflow: "hidden",
			});
	}
}

// ==================================================
// PAYMENT ENTRY THAI WITHHOLDING TAX SYSTEM
// ==================================================

frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {
		add_payment_entry_buttons(frm);
		update_wht_status_indicator(frm);
	},

	custom_is_withholding_tax: function (frm) {
		handle_withholding_tax_toggle(frm);
	},

	custom_withholding_tax_rate: function (frm) {
		calculate_withholding_tax_amount_debounced(frm);
	},

	paid_amount: function (frm) {
		calculate_withholding_tax_amount_debounced(frm);
	},

	received_amount: function (frm) {
		calculate_withholding_tax_amount_debounced(frm);
	},
});

function add_payment_entry_buttons(frm) {
	// Add WHT Certificate generation button
	if (frm.doc.docstatus === 1 && frm.doc.custom_is_withholding_tax) {
		frm.add_custom_button(
			__("Generate WHT Certificate"),
			function () {
				generate_wht_certificate(frm);
			},
			__("Create"),
		);
	}

	// Add print WHT button if certificate exists
	if (frm.doc.custom_wht_certificate_generated) {
		frm.add_custom_button(
			__("Print WHT Certificate"),
			function () {
				print_wht_certificate(frm);
			},
			__("Print"),
		);
	}
}

function handle_withholding_tax_toggle(frm) {
	if (frm.doc.custom_is_withholding_tax) {
		// Set default rate if not set
		if (!frm.doc.custom_withholding_tax_rate) {
			frm.set_value("custom_withholding_tax_rate", CONFIG.WHT.DEFAULT_RATES.SERVICE);
		}

		// Show helpful message about tax rates
		frappe.show_alert({
			message: __("Common WHT rates: 3% (services), 1% (rental), 5% (royalty)"),
			indicator: "blue",
		});
	} else {
		// Clear tax amount when disabled
		frm.set_value("custom_withholding_tax_amount", 0);
	}
	calculate_withholding_tax_amount(frm);
}

function calculate_withholding_tax_amount(frm) {
	if (
		frm.doc.custom_is_withholding_tax &&
		frm.doc.custom_withholding_tax_rate
	) {
		let base_amount = 0;

		// Determine base amount based on payment type
		if (frm.doc.payment_type === "Pay") {
			base_amount = frm.doc.paid_amount || 0;
		} else {
			base_amount = frm.doc.received_amount || 0;
		}

		if (base_amount > 0) {
			const wht_amount =
				(base_amount * frm.doc.custom_withholding_tax_rate) / 100;
			frm.set_value("custom_withholding_tax_amount", wht_amount);

			// Show calculation preview
			frappe.show_alert({
				message: __("WHT Calculation: {0} × {1}% = {2}", [
					format_currency(base_amount),
					frm.doc.custom_withholding_tax_rate,
					format_currency(wht_amount),
				]),
				indicator: "green",
			});
		}
	}
}

// Debounced version for field triggers
const calculate_withholding_tax_amount_debounced = debounce(
	calculate_withholding_tax_amount,
	CONFIG.WHT.DEBOUNCE_DELAY,
);

function generate_wht_certificate(frm) {
	// Validate required fields
	if (!frm.doc.custom_supplier_tax_id) {
		frappe.msgprint({
			title: __("Missing Information"),
			message: __(
				"Please enter Supplier Tax ID before generating WHT certificate.",
			),
			indicator: "orange",
		});
		frm.scroll_to_field("custom_supplier_tax_id");
		return;
	}

	// Generate certificate number if not exists
	if (!frm.doc.custom_wht_certificate_number) {
		generate_certificate_number(frm);
	}

	// Print the certificate
	print_wht_certificate(frm);

	// Mark certificate as generated
	frappe.model.set_value(
		frm.doctype,
		frm.docname,
		"custom_wht_certificate_generated",
		1,
	);
	frm.save();

	frappe.msgprint({
		title: __("WHT Certificate Generated"),
		message: __(
			"Thai Withholding Tax Certificate (Form 50 ทวิ) has been generated successfully.",
		),
		indicator: "green",
	});
}

function print_wht_certificate(frm) {
	frappe.route_options = {
		format: CONFIG.PRINT_FORMATS.WHT_CERTIFICATE,
	};
	frappe.set_route("print", frm.doctype, frm.docname);
}

function generate_certificate_number(frm) {
	// Generate certificate number in format: WHT-YYYY-MM-NNNN
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, "0");

	// Use crypto.getRandomValues for secure random number
	const randomArray = new Uint32Array(1);
	crypto.getRandomValues(randomArray);
	const random = String(randomArray[0] % 9999 + 1).padStart(4, "0");

	const cert_number = `WHT-${year}-${month}-${random}`;
	frm.set_value("custom_wht_certificate_number", cert_number);
}

function update_wht_status_indicator(frm) {
	// Safety check for dashboard methods
	if (!frm.dashboard || !frm.dashboard.add_indicator) {
		debugLog("Dashboard methods not available");
		return;
	}

	if (frm.doc.custom_is_withholding_tax) {
		if (frm.doc.custom_wht_certificate_generated) {
			frm.dashboard.add_indicator(__("WHT Certificate: Generated"), "green");
		} else {
			frm.dashboard.add_indicator(__("WHT Certificate: Pending"), "orange");
		}

		if (frm.doc.custom_withholding_tax_amount && frm.dashboard.add_comment) {
			frm.dashboard.add_comment(
				__("WHT Amount: ") +
					format_currency(frm.doc.custom_withholding_tax_amount),
				"blue",
			);
		}
	}
}

// ==================================================
// GLOBAL UTILITY OBJECT
// ==================================================

window.print_designer_delivery_utils = {
	// QR Delivery functions
	generateQRForDelivery: generate_qr_code,
	showQRDialog: show_qr_code_dialog,
	printDeliveryWithQR: print_delivery_note_with_qr,

	// WHT functions
	generateWHTCertificate: generate_wht_certificate,
	printWHTCertificate: print_wht_certificate,
	calculateWHTAmount: calculate_withholding_tax_amount,

	// Utility functions
	getStatusColor: get_status_color,
	formatCurrency: format_currency,
	debugLog: debugLog,
};

// ==================================================
// ERROR HANDLING
// ==================================================

// Global error handler for delivery approval operations
window.addEventListener("error", function (e) {
	if (e.message && e.message.includes("delivery_approval")) {
		debugError("Delivery Approval Error:", e);
		frappe.msgprint({
			title: __("System Error"),
			message: __(
				"An error occurred in the delivery approval system. Please refresh the page and try again.",
			),
			indicator: "red",
		});
	}
});

// Log system initialization
debugLog("Print Designer Delivery Approval & WHT System initialized successfully");
