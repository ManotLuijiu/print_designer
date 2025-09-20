/**
 * Payment Entry WHT Certificate Management
 *
 * Adds WHT Certificate creation and management functionality to Payment Entry forms.
 * Only applies to Payment Entry (Pay) transactions with Thai tax compliance.
 */

frappe.ui.form.on("Payment Entry", {
    refresh: function(frm) {
        // Only show WHT certificate features for Pay transactions
        if (frm.doc.payment_type !== "Pay") {
            return;
        }

        // Add WHT Certificate buttons to toolbar
        add_wht_certificate_buttons(frm);

        // Setup field watchers for real-time calculations
        setup_wht_certificate_watchers(frm);

        // Make WHT Certificate field clickable to redirect to PND form
        setup_wht_certificate_link(frm);
    },

    onload: function(frm) {
        // Load WHT certificate data if it exists
        if (frm.doc.pd_custom_wht_certificate) {
            load_wht_certificate_info(frm);
        }
    },

    pd_custom_withholding_tax_rate: function(frm) {
        // Recalculate WHT amount when rate changes
        calculate_wht_amount(frm);
    },

    pd_custom_tax_base_amount: function(frm) {
        // Recalculate WHT amount when tax base changes
        calculate_wht_amount(frm);
    },

});

function add_wht_certificate_buttons(frm) {
    // Remove existing buttons to prevent duplicates
    frm.remove_custom_button(__("Preview WHT Certificate"));
    frm.remove_custom_button(__("Create WHT Certificate"));
    frm.remove_custom_button(__("View WHT Certificate"));

    // Check if this Payment Entry has WHT amounts
    const wht_amount = flt(frm.doc.pd_custom_withholding_tax_amount || 0);

    // Check if document is saved (not new) - following ERPNext pattern
    const is_saved = !frm.doc.__islocal && !frm.is_new();

    // DEBUG: Log document state information
    console.log("DEBUG add_wht_certificate_buttons:", {
        name: frm.doc.name,
        payment_type: frm.doc.payment_type,
        wht_amount: wht_amount,
        is_new: frm.is_new(),
        __islocal: frm.doc.__islocal,
        docstatus: frm.doc.docstatus,
        is_saved: is_saved,
        has_certificate: !!frm.doc.pd_custom_wht_certificate
    });

    if (wht_amount <= 0) {
        console.log("DEBUG: Skipping - WHT amount is 0 or negative");
        return;
    }

    // Add buttons based on certificate status
    if (frm.doc.pd_custom_wht_certificate) {
        // Certificate exists - Add view button (will redirect to PND form if exists)
        console.log("DEBUG: Adding View button - certificate exists");
        frm.add_custom_button(__("View WHT Certificate"), function() {
            view_wht_certificate(frm);
        }, __("Thai Compliance"));

    } else if (is_saved) {
        // No certificate exists but Payment Entry is saved - Add preview button only
        console.log("DEBUG: Adding Preview button - document is saved and no certificate");
        frm.add_custom_button(__("Preview WHT Certificate"), function() {
            preview_wht_certificate(frm);
        }, __("Thai Compliance"));
    } else {
        console.log("DEBUG: No buttons added - document is new/unsaved");
    }
}

function preview_wht_certificate(frm) {
    frappe.call({
        method: "print_designer.custom.payment_entry_server_events.get_wht_certificate_preview",
        args: {
            payment_entry_name: frm.doc.name
        },
        callback: function(response) {
            if (response.message && response.message.eligible) {
                show_wht_certificate_preview_dialog(response.message);
            } else {
                frappe.msgprint({
                    title: __("Preview Not Available"),
                    message: response.message.message || __("This Payment Entry is not eligible for WHT Certificate"),
                    indicator: "orange"
                });
            }
        },
        error: function(error) {
            frappe.msgprint({
                title: __("Preview Error"),
                message: __("Failed to generate WHT Certificate preview"),
                indicator: "red"
            });
        }
    });
}

function create_wht_certificate(frm) {
    // DEBUG: Log attempt to create certificate
    console.log("DEBUG create_wht_certificate: Starting creation for", {
        payment_entry_name: frm.doc.name,
        payment_type: frm.doc.payment_type,
        is_new: frm.is_new(),
        docstatus: frm.doc.docstatus,
        wht_amount: frm.doc.pd_custom_withholding_tax_amount
    });

    // Confirm before creating
    frappe.confirm(
        __("Create Withholding Tax Certificate for this Payment Entry?<br><br>This will generate an official WHT certificate for Thai Revenue Department compliance."),
        function() {
            console.log("DEBUG: User confirmed certificate creation");
            frappe.call({
                method: "print_designer.custom.payment_entry_server_events.create_wht_certificate_from_payment_entry",
                args: {
                    payment_entry_name: frm.doc.name
                },
                callback: function(response) {
                    console.log("DEBUG: Certificate creation response:", response);
                    if (response.message && response.message.status === "success") {
                        console.log("DEBUG: Certificate creation successful");
                        frappe.msgprint({
                            title: __("Success"),
                            message: response.message.message,
                            indicator: "green"
                        });

                        // Refresh the form to show the new certificate link
                        frm.reload_doc().then(() => {
                            // Setup the clickable link after reload
                            setup_wht_certificate_link(frm);
                        });
                    } else {
                        console.log("DEBUG: Certificate creation failed:", response.message);
                        frappe.msgprint({
                            title: __("Creation Failed"),
                            message: response.message.message || __("Failed to create WHT Certificate"),
                            indicator: "red"
                        });
                    }
                },
                error: function(error) {
                    console.log("DEBUG: Certificate creation error:", error);
                    frappe.msgprint({
                        title: __("Creation Error"),
                        message: __("An error occurred while creating the WHT Certificate"),
                        indicator: "red"
                    });
                }
            });
        }
    );
}

function view_wht_certificate(frm) {
    if (frm.doc.pd_custom_wht_certificate) {
        // First get the WHT Certificate to find its linked PND form
        frappe.db.get_doc("Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate)
            .then(doc => {
                if (doc.custom_pnd_form && doc.pnd_form_type) {
                    // Redirect to the actual PND form
                    frappe.set_route("Form", doc.pnd_form_type, doc.custom_pnd_form);
                } else {
                    // Fallback to WHT Certificate if no PND form linked
                    frappe.set_route("Form", "Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate);
                }
            })
            .catch(err => {
                // On error, fallback to WHT Certificate
                frappe.set_route("Form", "Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate);
            });
    }
}

function show_wht_certificate_preview_dialog(preview_data) {
    let dialog = new frappe.ui.Dialog({
        title: __("WHT Certificate Preview"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "preview_html",
                options: get_wht_certificate_preview_html(preview_data)
            }
        ],
        primary_action_label: __("Create Certificate (Disabled)"),
        primary_action: function() {
            // Disabled for automation - no manual certificate creation
            frappe.msgprint({
                title: __("Feature Disabled"),
                message: __("Manual certificate creation is disabled in automation mode"),
                indicator: "orange"
            });
        }
    });

    dialog.show();

    // Manually disable the primary button after dialog is shown
    setTimeout(() => {
        const $primaryBtn = dialog.$wrapper.find('.btn-modal-primary');
        if ($primaryBtn.length) {
            $primaryBtn
                .removeClass('btn-primary')
                .addClass('btn-secondary disabled')
                .attr('disabled', true)
                .attr('title', __('Auto Create after Submit'))
                .css({
                    'opacity': '0.6',
                    'cursor': 'not-allowed',
                    'pointer-events': 'auto'  // Allow hover for tooltip
                });
        }
    }, 100);
}

function get_wht_certificate_preview_html(data) {
    return `
        <div class="wht-certificate-preview" style="border: 1px solid var(--border-color); border-radius: 6px; padding: 20px; background-color: var(--bg-color);">
            <h4 style="color: var(--text-color); margin-bottom: 20px; text-align: center;">
                <i class="fa fa-file-text-o"></i> หนังสือรับรองการหักภาษีณ ที่จ่าย
            </h4>

            <div class="row">
                <div class="col-md-6">
                    <table class="table table-borderless">
                        <tr>
                            <td><strong>Certificate Number:</strong></td>
                            <td>${data.certificate_number}</td>
                        </tr>
                        <tr>
                            <td><strong>Certificate Date:</strong></td>
                            <td>${frappe.format(data.certificate_date, {fieldtype: "Date"})}</td>
                        </tr>
                        <tr>
                            <td><strong>Tax Year (พ.ศ.):</strong></td>
                            <td>${data.tax_year}</td>
                        </tr>
                        <tr>
                            <td><strong>Tax Month:</strong></td>
                            <td>${data.tax_month}</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <table class="table table-borderless">
                        <tr>
                            <td><strong>Supplier:</strong></td>
                            <td>${data.supplier}</td>
                        </tr>
                        <tr>
                            <td><strong>Income Type:</strong></td>
                            <td>${data.income_type}</td>
                        </tr>
                        <tr>
                            <td><strong>PND Form:</strong></td>
                            <td>${data.pnd_form_type}</td>
                        </tr>
                    </table>
                </div>
            </div>

            <div class="row mt-3">
                <div class="col-md-12">
                    <h5 style="color: var(--text-color);">Amount Details (รายละเอียดจำนวนเงิน)</h5>
                    <table class="table table-bordered">
                        <tr>
                            <td><strong>Tax Base Amount (ยอดเงินก่อน VAT):</strong></td>
                            <td class="text-right">${format_currency(data.tax_base_amount)}</td>
                        </tr>
                        <tr>
                            <td><strong>WHT Rate (อัตราภาษี):</strong></td>
                            <td class="text-right">${flt(data.wht_rate, 2)}%</td>
                        </tr>
                        <tr style="background-color: var(--table-bg);">
                            <td><strong>WHT Amount (ภาษีหัก ณ ที่จ่าย):</strong></td>
                            <td class="text-right"><strong>${format_currency(data.wht_amount)}</strong></td>
                        </tr>
                    </table>
                </div>
            </div>

            <div class="alert alert-info mt-3">
                <i class="fa fa-info-circle"></i>
                <strong>หมายเหตุ:</strong> หนังสือรับรองฉบับนี้จะถูกสร้างขึ้นตามมาตรา 50 ทวิ แห่งประมวลรัษฎากร
                สำหรับใช้แนบพร้อมกับแบบแสดงรายการภาษีเงินได้หัก ณ ที่จ่าย
            </div>
        </div>
    `;
}

function calculate_wht_amount(frm) {
    const tax_base = flt(frm.doc.pd_custom_tax_base_amount || 0);
    const wht_rate = flt(frm.doc.pd_custom_withholding_tax_rate || 0);

    if (tax_base > 0 && wht_rate > 0) {
        const calculated_wht = tax_base * (wht_rate / 100);
        frm.set_value("pd_custom_withholding_tax_amount", calculated_wht);
    }
}

function setup_wht_certificate_watchers(frm) {
    // Watch for changes that might affect WHT certificate eligibility
    if (frm.fields_dict.pd_custom_withholding_tax_amount && frm.fields_dict.pd_custom_withholding_tax_amount.$input) {
        frm.fields_dict.pd_custom_withholding_tax_amount.$input.on('change', function() {
            setTimeout(() => {
                add_wht_certificate_buttons(frm);
            }, 500);
        });
    }

}

function toggle_wht_certificate_section(frm) {
    // WHT certificate fields are now always visible for Payment Entry (Pay)
    // Visibility is controlled by depends_on conditions in field definitions
    const is_pay_type = frm.doc.payment_type === "Pay";

    frm.toggle_display("pd_custom_wht_certificate", is_pay_type);
    frm.toggle_display("pd_custom_needs_wht_certificate", is_pay_type);
}

function load_wht_certificate_info(frm) {
    if (!frm.doc.pd_custom_wht_certificate) {
        return;
    }

    // Load certificate status for display
    frappe.db.get_value("Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate, "status")
        .then(result => {
            if (result.message && result.message.status) {
                const status = result.message.status;
                const status_colors = {
                    "Draft": "orange",
                    "Issued": "green",
                    "Submitted to Revenue Dept": "blue",
                    "Cancelled": "red"
                };

                // Show status indicator
                frm.dashboard.add_indicator(__("WHT Certificate: {0}", [status]), status_colors[status] || "gray");
            }
        });
}

function format_currency(amount) {
    return frappe.format(amount, {fieldtype: "Currency"});
}

function setup_wht_certificate_link(frm) {
    /**
     * Setup WHT Certificate field behaviors based on payment type:
     * - Payment Entry (Pay): pd_custom_wht_certificate (Link field) - auto-generated certificates
     * - Payment Entry (Receive): pd_custom_wht_certificate_no (Data field) - manual input
     *
     * When clicked, redirects to the actual PND form instead of WHT Certificate
     */

    // For Payment Entry (Pay) - Link field for our issued certificates
    if (frm.doc.payment_type === "Pay") {
        const linkField = frm.fields_dict.pd_custom_wht_certificate;
        if (linkField && frm.doc.pd_custom_wht_certificate) {
            // Override the link click behavior
            setTimeout(() => {
                // Find the link element and override its click behavior
                const $link = frm.fields_dict.pd_custom_wht_certificate.$wrapper.find('.control-value a');
                if ($link.length) {
                    $link.off('click').on('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();

                        // Get the WHT Certificate to find its linked PND form
                        frappe.db.get_doc("Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate)
                            .then(doc => {
                                if (doc.custom_pnd_form && doc.pnd_form_type) {
                                    // Redirect to the actual PND form
                                    frappe.set_route("Form", doc.pnd_form_type, doc.custom_pnd_form);
                                } else {
                                    // Fallback to WHT Certificate if no PND form linked
                                    frappe.msgprint({
                                        title: __("PND Form Not Found"),
                                        message: __("The PND form for this WHT Certificate has not been created yet. Redirecting to WHT Certificate instead."),
                                        indicator: "orange"
                                    });
                                    frappe.set_route("Form", "Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate);
                                }
                            })
                            .catch(err => {
                                console.error("Error fetching WHT Certificate:", err);
                                // On error, fallback to WHT Certificate
                                frappe.set_route("Form", "Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate);
                            });
                    });

                    // Change the tooltip to indicate PND form redirect
                    $link.attr('title', __('Click to view PND Form'));
                }
            }, 100);

            // Refresh the field
            linkField.refresh();
        }
    }

    // For Payment Entry (Receive) - Data field for customer issued certificates
    // No special link behavior needed - it's a plain text field for manual input
}