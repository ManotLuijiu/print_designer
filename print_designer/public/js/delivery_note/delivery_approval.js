/**
 * Client-side functionality for Print Designer QR Delivery Approval and Thai WHT systems
 * Provides form customizations for Delivery Note and Payment Entry DocTypes
 */
/** biome-ignore-all lint/complexity/useArrowFunction: <explanation> */

// ==================================================
// DELIVERY NOTE QR APPROVAL SYSTEM
// ==================================================

frappe.ui.form.on("Delivery Note", {
	refresh: function (frm) {
		add_delivery_note_buttons(frm);
		show_qr_code_if_available(frm);
		update_approval_status_indicator(frm);
		add_custom_css_for_qr_fields(frm);
	},

	custom_goods_received_status: function (frm) {
		update_approval_status_indicator(frm);
	},

	on_submit: function (frm) {
		// Auto-generate QR code after successful submission
		setTimeout(function () {
			if (!frm.doc.custom_approval_qr_code) {
				generate_qr_code(frm);
			}
		}, 1500);
	},
});

function add_delivery_note_buttons(frm) {
	// Add QR generation button for submitted delivery notes without QR
	if (frm.doc.docstatus === 1 && !frm.doc.custom_approval_qr_code) {
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
		frm.add_custom_button(
			__("View Approval Page"),
			function () {
				window.open(frm.doc.custom_approval_url, "_blank");
			},
			__("Actions"),
		);
	}

	// Add QR code display button
	if (frm.doc.custom_approval_qr_code) {
		frm.add_custom_button(
			__("Show QR Code"),
			function () {
				show_qr_code_dialog(frm);
			},
			__("Actions"),
		);
	}

	// Add print with QR button
	if (frm.doc.custom_approval_qr_code) {
		frm.add_custom_button(
			__("Print with QR"),
			function () {
				print_delivery_note_with_qr(frm);
			},
			__("Print"),
		);
	}
}

function generate_qr_code(frm) {
	frappe.show_progress(__("Generating QR Code"), 30, 100, __("Please wait..."));

	frappe.call({
		method:
			"print_designer.custom.delivery_note_qr.generate_delivery_approval_qr",
		args: {
			delivery_note_name: frm.doc.name,
		},
		callback: function (r) {
			frappe.hide_progress();

			if (r.message?.qr_code) {
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

				frm.save().then(() => {
					frappe.msgprint({
						title: __("QR Code Generated Successfully"),
						message: __(
							"QR Code has been generated. Customer can scan this code to approve delivery receipt.",
						),
						indicator: "green",
					});

					// Show QR code dialog immediately
					setTimeout(() => show_qr_code_dialog(frm), 500);
				});
			} else {
				frappe.msgprint({
					title: __("Error"),
					message: __("Failed to generate QR code. Please try again."),
					indicator: "red",
				});
			}
		},
		error: function (r) {
			frappe.hide_progress();
			frappe.msgprint({
				title: __("QR Generation Error"),
				message:
					__("An error occurred while generating the QR code: ") +
					(r.message || "Unknown error"),
				indicator: "red",
			});
		},
	});
}

function show_qr_code_dialog(frm) {
	if (!frm.doc.custom_approval_qr_code) {
		frappe.msgprint(__("No QR code available. Please generate one first."));
		return;
	}

	const qr_dialog = new frappe.ui.Dialog({
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
                        
                        <div class="qr-instructions" style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 15px 0;">
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
			qr_dialog.hide();
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
	});

	qr_dialog.show();
}

function print_delivery_note_with_qr(frm) {
	frappe.route_options = {
		format: "Delivery Note with QR Approval",
	};
	frappe.set_route("print", frm.doctype, frm.docname);
}

function show_qr_code_if_available(frm) {
	// Auto-show QR dialog if QR was just generated
	if (frm.doc.custom_approval_qr_code && !frm._qr_shown && frm.is_new()) {
		frm._qr_shown = true;
		setTimeout(() => show_qr_code_dialog(frm), 1000);
	}
}

function update_approval_status_indicator(frm) {
	// Clear existing indicators
	frm.dashboard.clear_indicator();

	const status = frm.doc.custom_goods_received_status;

	if (status === "Approved") {
		frm.dashboard.add_indicator(__("Goods Received: Approved"), "green");
		if (frm.doc.custom_customer_approval_date) {
			frm.dashboard.add_comment(
				__("Approved on: ") +
					frappe.datetime.str_to_user(frm.doc.custom_customer_approval_date),
				"green",
			);
		}
	} else if (status === "Rejected") {
		frm.dashboard.add_indicator(__("Goods Received: Rejected"), "red");
		if (frm.doc.custom_rejection_reason) {
			frm.dashboard.add_comment(
				__("Reason: ") + frm.doc.custom_rejection_reason,
				"red",
			);
		}
	} else {
		frm.dashboard.add_indicator(__("Goods Received: Pending"), "orange");
		if (frm.doc.custom_approval_url) {
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
		calculate_withholding_tax_amount(frm);
	},

	paid_amount: function (frm) {
		calculate_withholding_tax_amount(frm);
	},

	received_amount: function (frm) {
		calculate_withholding_tax_amount(frm);
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
			frm.set_value("custom_withholding_tax_rate", 3); // Default 3% for services
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
		format: "Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate",
	};
	frappe.set_route("print", frm.doctype, frm.docname);
}

function generate_certificate_number(frm) {
	// Generate certificate number in format: WHT-YYYY-MM-NNNN
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, "0");
	const random = String(Math.floor(Math.random() * 9999) + 1).padStart(4, "0");

	const cert_number = `WHT-${year}-${month}-${random}`;
	frm.set_value("custom_wht_certificate_number", cert_number);
}

function update_wht_status_indicator(frm) {
	if (frm.doc.custom_is_withholding_tax) {
		if (frm.doc.custom_wht_certificate_generated) {
			frm.dashboard.add_indicator(__("WHT Certificate: Generated"), "green");
		} else {
			frm.dashboard.add_indicator(__("WHT Certificate: Pending"), "orange");
		}

		if (frm.doc.custom_withholding_tax_amount) {
			frm.dashboard.add_comment(
				__("WHT Amount: ") +
					format_currency(frm.doc.custom_withholding_tax_amount),
				"blue",
			);
		}
	}
}

// ==================================================
// UTILITY FUNCTIONS
// ==================================================

function format_currency(amount) {
	return frappe.format(amount, { fieldtype: "Currency" });
}

// Global utility object for external access
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
};

// Initialize on page load
$(document).ready(function () {
	// Add custom CSS for better styling
	$("<style>")
		.prop("type", "text/css")
		.html(`
            .qr-dialog-content .badge {
                font-size: 12px;
                padding: 6px 12px;
            }
            .delivery-approval-section {
                border-left: 4px solid #007bff;
                background: #f8f9ff;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }
            .wht-section {
                border-left: 4px solid #28a745;
                background: #f8fff9;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
            }
        `)
		.appendTo("head");
});

// ==================================================
// ERROR HANDLING AND LOGGING
// ==================================================

// Global error handler for delivery approval operations
window.addEventListener("error", function (e) {
	if (e.message && e.message.includes("delivery_approval")) {
		console.error("Delivery Approval Error:", e);
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
console.log(
	"Print Designer Delivery Approval & WHT System initialized successfully",
);
