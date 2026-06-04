// Copyright (c) 2024, Digisoft ERP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry', {
    refresh: function(frm) {
        // Only show Create WHT Register button for Receive payments
        if (frm.doc.payment_type === 'Receive') {
            // Show button to create WHT Register if certificate number is entered but register not linked
            if (frm.doc.pd_custom_wht_certificate_no && !frm.doc.pd_custom_receive_wht_register) {
                frm.add_custom_button(
                    __('Create WHT Register'),
                    function() {
                        create_wht_register_from_pe(frm);
                    },
                    __('WHT')
                );
            }

            // Show button to view/edit WHT Register if linked
            if (frm.doc.pd_custom_receive_wht_register) {
                frm.add_custom_button(
                    __('View WHT Register'),
                    function() {
                        frappe.set_route('Form', 'Receive WHT Register', frm.doc.pd_custom_receive_wht_register);
                    },
                    __('WHT')
                );
            }
        }
    },

    pd_custom_wht_certificate_no: function(frm) {
        // Auto-create WHT Register when certificate number is entered
        if (frm.doc.payment_type === 'Receive' && frm.doc.pd_custom_wht_certificate_no && !frm.doc.pd_custom_receive_wht_register) {
            // Delay to allow user to enter multiple fields
            frappe.call({
                method: 'print_designer.doctype.receive_wht_register.receive_wht_register.create_from_payment_entry',
                args: {
                    payment_entry: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.name) {
                        frappe.msgprint(r.message.message);
                        frm.refresh_field('pd_custom_receive_wht_register');
                        frm.reload_doc();
                    }
                },
                error: function(r) {
                    // Silent fail - user might not have permission
                    console.log('WHT Register creation failed:', r);
                }
            });
        }
    }
});

function create_wht_register_from_pe(frm) {
    frappe.call({
        method: 'print_designer.doctype.receive_wht_register.receive_wht_register.create_from_payment_entry',
        args: {
            payment_entry: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.name) {
                frappe.msgprint(r.message.message);
                frm.refresh_field('pd_custom_receive_wht_register');
                frm.reload_doc();
            } else if (r.exc) {
                frappe.msgprint({
                    message: __('Error creating WHT Register: {0}', [r.exc]),
                    title: __('Error'),
                    indicator: 'red'
                });
            }
        }
    });
}