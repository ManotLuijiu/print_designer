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

        // Make WHT Certificate No clickable
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

    pd_custom_has_thai_taxes: function(frm) {
        // Show/hide WHT certificate section based on Thai taxes flag
        toggle_wht_certificate_section(frm);
    }
});

function add_wht_certificate_buttons(frm) {
    // Remove existing buttons to prevent duplicates
    frm.remove_custom_button(__("Preview WHT Certificate"));
    frm.remove_custom_button(__("Create WHT Certificate"));
    frm.remove_custom_button(__("View WHT Certificate"));

    // Check if this Payment Entry has Thai taxes
    const has_thai_taxes = frm.doc.pd_custom_has_thai_taxes;
    const wht_amount = flt(frm.doc.pd_custom_withholding_tax_amount || 0);

    if (!has_thai_taxes || wht_amount <= 0) {
        return;
    }

    // Add buttons based on certificate status
    if (frm.doc.pd_custom_wht_certificate) {
        // Certificate exists - Add view button
        frm.add_custom_button(__("View WHT Certificate"), function() {
            view_wht_certificate(frm);
        }, __("Thai Compliance"));

    } else if (!frm.doc.__islocal) {
        // No certificate exists but Payment Entry is saved - Add creation buttons
        frm.add_custom_button(__("Preview WHT Certificate"), function() {
            preview_wht_certificate(frm);
        }, __("Thai Compliance"));

        frm.add_custom_button(__("Create WHT Certificate"), function() {
            create_wht_certificate(frm);
        }, __("Thai Compliance"));
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
    // Confirm before creating
    frappe.confirm(
        __("Create Withholding Tax Certificate for this Payment Entry?<br><br>This will generate an official WHT certificate for Thai Revenue Department compliance."),
        function() {
            frappe.call({
                method: "print_designer.custom.payment_entry_server_events.create_wht_certificate_from_payment_entry",
                args: {
                    payment_entry_name: frm.doc.name
                },
                callback: function(response) {
                    if (response.message && response.message.status === "success") {
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
                        frappe.msgprint({
                            title: __("Creation Failed"),
                            message: response.message.message || __("Failed to create WHT Certificate"),
                            indicator: "red"
                        });
                    }
                },
                error: function(error) {
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
        frappe.set_route("Form", "Withholding Tax Certificate", frm.doc.pd_custom_wht_certificate);
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
        primary_action_label: __("Create Certificate"),
        primary_action: function() {
            dialog.hide();
            // Trigger certificate creation
            create_wht_certificate(cur_frm);
        }
    });

    dialog.show();
}

function get_wht_certificate_preview_html(data) {
    return `
        <div class="wht-certificate-preview" style="border: 1px solid #d1d8dd; border-radius: 6px; padding: 20px; background-color: #f8f9fa;">
            <h4 style="color: #495057; margin-bottom: 20px; text-align: center;">
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
                    <h5 style="color: #495057;">Amount Details (รายละเอียดจำนวนเงิน)</h5>
                    <table class="table table-bordered">
                        <tr>
                            <td><strong>Tax Base Amount (ยอดเงินก่อน VAT):</strong></td>
                            <td class="text-right">${format_currency(data.tax_base_amount)}</td>
                        </tr>
                        <tr>
                            <td><strong>WHT Rate (อัตราภาษี):</strong></td>
                            <td class="text-right">${flt(data.wht_rate, 2)}%</td>
                        </tr>
                        <tr style="background-color: #e9ecef;">
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

    if (frm.fields_dict.pd_custom_has_thai_taxes && frm.fields_dict.pd_custom_has_thai_taxes.$input) {
        frm.fields_dict.pd_custom_has_thai_taxes.$input.on('change', function() {
            setTimeout(() => {
                add_wht_certificate_buttons(frm);
                toggle_wht_certificate_section(frm);
            }, 500);
        });
    }
}

function toggle_wht_certificate_section(frm) {
    const has_thai_taxes = frm.doc.pd_custom_has_thai_taxes;

    // Show/hide WHT certificate fields based on Thai taxes flag
    frm.toggle_display("pd_custom_wht_certificate", has_thai_taxes);
    frm.toggle_display("pd_custom_needs_wht_certificate", has_thai_taxes);
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
     * Link field automatically provides:
     * - Draft status: Shows "x" and "→" icons
     * - Submitted status: Shows as clickable hyperlink
     */

    // For Payment Entry (Pay) - Link field for our issued certificates
    if (frm.doc.payment_type === "Pay") {
        const linkField = frm.fields_dict.pd_custom_wht_certificate;
        if (linkField && frm.doc.pd_custom_wht_certificate) {
            // Link field already has proper behavior built-in
            // Just refresh to ensure it's displayed correctly
            linkField.refresh();
        }
    }

    // For Payment Entry (Receive) - Data field for customer issued certificates
    // No special link behavior needed - it's a plain text field for manual input
}