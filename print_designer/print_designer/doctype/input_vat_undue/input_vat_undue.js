// Copyright (c) 2026, AWS Solution Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Input VAT Undue", {
    refresh(frm) {
        // Show warning if already converted
        if (frm.doc.status === "Converted to Input VAT") {
            frm.set_intro(
                __("Original received — Thai Purchase VAT record created."),
                "green"
            );
            frm.set_df_property("has_original", "read_only", 1);
        }

        // Show warning if cancelled
        if (frm.doc.status === "Cancelled") {
            frm.set_intro(__("This record has been cancelled."), "red");
            frm.set_df_property("has_original", "read_only", 1);
        }
    },

    has_original(frm) {
        // Only trigger when being CHECKED (not unchecked)
        if (!frm.doc.has_original) return;

        // Prevent double-processing
        if (frm.doc.status === "Converted to Input VAT") {
            frappe.msgprint(
                __("Original already received."),
                __("Already Processed"),
                "orange"
            );
            return;
        }

        frappe.call({
            method:
                "print_designer.regional.thai_purchase_vat.mark_original_received",
            args: {
                input_vat_undue_name: frm.doc.name,
            },
            callback: function (response) {
                if (response.message) {
                    frappe.msgprint(
                        __("Thai Purchase VAT {0} created from Input VAT Undue {1}", [
                            response.message.thai_purchase_vat,
                            response.message.input_vat_undue,
                        ]),
                        __("Original Received"),
                        "green"
                    );
                    // Reload to show updated status
                    frm.reload_doc();
                }
            },
            error: function (response) {
                // Restore checkbox on error
                frm.set_value("has_original", 0);
                frappe.msgprint(
                    __(response.message || "Error creating record."),
                    __("Error"),
                    "red"
                );
            },
        });
    },
});
