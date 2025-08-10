frappe.ui.form.on('Delivery Note', {
    refresh: function(frm) {
        if (!frm.doc.__islocal && frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Generate QR Code'), function() {
                generate_qr_code_preview(frm);
            }, __('Actions'));
        }
    }
});

function generate_qr_code_preview(frm) {
    frappe.call({
        method: 'custom_app.delivery_note.generate_approval_qr_code',
        args: {
            delivery_note_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const dialog = new frappe.ui.Dialog({
                    title: __('QR Code for Delivery Approval'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'qr_preview',
                            options: `
                                <div style="text-align: center; padding: 20px;">
                                    <img src="${r.message}" style="width: 200px; height: 200px; border: 1px solid #ddd;">
                                    <p style="margin-top: 15px; font-size: 14px;">
                                        <strong>Instructions:</strong><br>
                                        1. Customer scans QR code with mobile phone<br>
                                        2. Customer clicks the approval link<br>
                                        3. Digital signature is recorded automatically
                                    </p>
                                </div>
                            `
                        }
                    ]
                });
                dialog.show();
            }
        }
    });
}
