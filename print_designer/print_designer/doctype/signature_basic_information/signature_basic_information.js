// Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Signature Basic Information", {
    refresh(frm) {
        // Auto-generate signature field name if empty
        if (!frm.doc.signature_field_name && frm.doc.signature_name) {
            frm.set_value('signature_field_name', frm.doc.signature_name.toLowerCase().replace(/[^a-z0-9]/g, '_'));
        }

        // Update field labels based on category
        if (frm.doc.signature_category === 'Company Stamp') {
            frm.set_df_property('signature_name', 'label', 'Stamp Name');
            frm.set_df_property('signature_title', 'label', 'Stamp Title');
            frm.set_df_property('signature_data_section', 'label', 'Stamp Image Data');
            frm.set_df_property('signature_type', 'label', 'Stamp Type');
            frm.set_df_property('signature_image', 'label', 'Stamp Image');
            frm.set_df_property('signature_data', 'label', 'Stamp Data');
        } else {
            frm.set_df_property('signature_name', 'label', 'Signature Name');
            frm.set_df_property('signature_title', 'label', 'Signature Title');
            frm.set_df_property('signature_data_section', 'label', 'Signature Data');
            frm.set_df_property('signature_type', 'label', 'Signature Type');
            frm.set_df_property('signature_image', 'label', 'Signature Image');
            frm.set_df_property('signature_data', 'label', 'Signature Data');
        }

        // Add signature drawing canvas for Digital Drawing type
        if (frm.doc.signature_type === 'Digital Drawing') {
            const button_label = frm.doc.signature_category === 'Company Stamp' ? __('Draw Stamp') : __('Draw Signature');
            frm.add_custom_button(button_label, function() {
                show_signature_dialog(frm);
            });
        }

        // Add signature preview if data exists
        if (frm.doc.signature_data || frm.doc.signature_image) {
			console.log('frm.doc from signature_basic_information',frm.doc)
            const button_label = frm.doc.signature_category === 'Company Stamp' ? __('Preview Stamp') : __('Preview Signature');
            frm.add_custom_button(button_label, function() {
                show_signature_preview(frm);
            });
        }
    },

    signature_name(frm) {
        // Auto-generate field name when signature name changes
        if (frm.doc.signature_name) {
            const field_name = frm.doc.signature_name.toLowerCase().replace(/[^a-z0-9]/g, '_');
            frm.set_value('signature_field_name', field_name);
        }
    },

    signature_category(frm) {
        // Update field labels and visibility based on category
        if (frm.doc.signature_category === 'Company Stamp') {
            frm.set_df_property('signature_name', 'label', 'Stamp Name');
            frm.set_df_property('signature_title', 'label', 'Stamp Title');
            frm.set_df_property('signature_data_section', 'label', 'Stamp Image Data');
            frm.set_df_property('signature_type', 'label', 'Stamp Type');
            frm.set_df_property('signature_image', 'label', 'Stamp Image');
            frm.set_df_property('signature_data', 'label', 'Stamp Data');
            frm.set_df_property('signature_type', 'options', 'Uploaded Image\nDigital Drawing');
        } else {
            frm.set_df_property('signature_name', 'label', 'Signature Name');
            frm.set_df_property('signature_title', 'label', 'Signature Title');
            frm.set_df_property('signature_data_section', 'label', 'Signature Data');
            frm.set_df_property('signature_type', 'label', 'Signature Type');
            frm.set_df_property('signature_image', 'label', 'Signature Image');
            frm.set_df_property('signature_data', 'label', 'Signature Data');
            frm.set_df_property('signature_type', 'options', 'Digital Drawing\nUploaded Image\nText Signature');
        }

        // Clear signature type when category changes
        frm.set_value('signature_type', '');

        // Refresh the form to apply changes
        frm.refresh();
    },

    signature_type(frm) {
        // Show/hide fields based on signature type
        if (frm.doc.signature_type === 'Digital Drawing') {
            frm.set_df_property('signature_image', 'hidden', 1);
            frm.set_df_property('signature_data', 'hidden', 0);
        } else if (frm.doc.signature_type === 'Uploaded Image') {
            frm.set_df_property('signature_image', 'hidden', 0);
            frm.set_df_property('signature_data', 'hidden', 1);
        } else if (frm.doc.signature_type === 'Text Signature') {
            frm.set_df_property('signature_image', 'hidden', 1);
            frm.set_df_property('signature_data', 'hidden', 0);
        }
    },

    is_default(frm) {
        // Ensure only one default signature per user
        if (frm.doc.is_default && frm.doc.user) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Signature Basic Information',
                    filters: {
                        user: frm.doc.user,
                        name: ['!=', frm.doc.name],
                        is_default: 1
                    },
                    fields: ['name']
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        // Update each found signature to remove default
                        r.message.forEach(function(signature) {
                            frappe.call({
                                method: 'frappe.client.set_value',
                                args: {
                                    doctype: 'Signature Basic Information',
                                    name: signature.name,
                                    fieldname: 'is_default',
                                    value: 0
                                }
                            });
                        });
                    }
                }
            });
        }
    }
});

function show_signature_dialog(frm) {
    const is_stamp = frm.doc.signature_category === 'Company Stamp';
    const dialog_title = is_stamp ? __('Draw Your Stamp') : __('Draw Your Signature');
    const canvas_label = is_stamp ? __('Stamp Canvas') : __('Signature Canvas');
    const save_label = is_stamp ? __('Save Stamp') : __('Save Signature');

    const dialog = new frappe.ui.Dialog({
        title: dialog_title,
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'signature_canvas',
                label: canvas_label
            }
        ],
        primary_action_label: save_label,
        primary_action(values) {
            const canvas = dialog.fields_dict.signature_canvas.$wrapper.find('canvas')[0];
            const signature_data = canvas.toDataURL();
            frm.set_value('signature_data', signature_data);
            dialog.hide();
        }
    });

    dialog.show();

    // Create canvas for signature drawing
    const canvas_html = `
        <canvas id="signature-canvas" width="400" height="200"
                style="border: 2px solid #ddd; border-radius: 4px; background: white;">
        </canvas>
        <br><br>
        <button type="button" class="btn btn-secondary btn-sm" onclick="clearCanvas()">
            ${__('Clear')}
        </button>
    `;

    dialog.fields_dict.signature_canvas.$wrapper.html(canvas_html);

    // Initialize canvas drawing
    const canvas = dialog.fields_dict.signature_canvas.$wrapper.find('canvas')[0];
    const ctx = canvas.getContext('2d');
    let isDrawing = false;

    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);

    function startDrawing(e) {
        isDrawing = true;
        draw(e);
    }

    function draw(e) {
        if (!isDrawing) return;

        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#000';

        ctx.lineTo(x, y);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x, y);
    }

    function stopDrawing() {
        if (!isDrawing) return;
        isDrawing = false;
        ctx.beginPath();
    }

    // Global function for clear button
    window.clearCanvas = function() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
}

function create_detail_section(title, details) {
    let html = `<div class="signature-details-card">
                   <h5 class="signature-details-title">${__(title)}</h5>`;

    details.forEach(detail => {
        if (detail.value) {
            html += `<div class="signature-detail-item">
                        <strong>${__(detail.label)}:</strong> ${detail.value}
                     </div>`;
        }
    });

    html += '</div>';
    return html;
}

function show_signature_preview(frm) {
    const is_stamp = frm.doc.signature_category === 'Company Stamp';
	console.log('is_stamp',is_stamp)
	console.log('signature_category:', frm.doc.signature_category);

    const preview_title = is_stamp ? __('Stamp Preview') : __('Signature Preview');

	console.log('preview_title',preview_title)

    let preview_html = '';
	let image_found = false;

    if (frm.doc.signature_data) {
        preview_html = `<div class="signature-preview-container">
                           <img src="${frm.doc.signature_image}"
                                class="signature-preview-image">
                       </div>`;
		image_found = true;
    } else if (frm.doc.signature_image) {
        preview_html = `<div class="signature-preview-container">
                           <img src="${frm.doc.signature_image}"
                                class="signature-preview-image">
                       </div>`;
		image_found = true;
    }

	// If no image found, show placeholder
    if (!image_found) {
        preview_html = `<div class="signature-preview-placeholder">
                           <i class="fa fa-image signature-preview-icon"></i><br>
                           No ${is_stamp ? 'stamp' : 'signature'} image available
                       </div>`;
    }

	// Add stamp details using helper function
    if (is_stamp) {
        const stamp_details = [
            { label: 'Type', value: frm.doc.stamp_type },
            { label: 'Number', value: frm.doc.stamp_number },
            { label: 'Authority', value: frm.doc.stamp_authority },
            { label: 'Expiry', value: frm.doc.stamp_expiry ? frappe.datetime.str_to_user(frm.doc.stamp_expiry) : null }
        ];

        if (stamp_details.some(detail => detail.value)) {
            preview_html += create_detail_section('Stamp Details', stamp_details);
        }
    } else {
        const signature_details = [
            { label: 'Signer', value: frm.doc.signature_name },
            { label: 'Date', value: frm.doc.signature_date ? frappe.datetime.str_to_user(frm.doc.signature_date) : null },
            { label: 'Purpose', value: frm.doc.signature_purpose }
        ];

        if (signature_details.some(detail => detail.value)) {
            preview_html += create_detail_section('Signature Details', signature_details);
        }
    }

    // Add stamp details if it's a company stamp
    // if (is_stamp && (frm.doc.stamp_type || frm.doc.stamp_number || frm.doc.stamp_authority)) {

	// 	preview_html += '<div class="signature-details-card">';
    //     preview_html += '<h5 class="signature-details-title">{__(Stamp Details)}</h5>';

    //     if (frm.doc.stamp_type) {
    //         preview_html += `<div class="signature-detail-item"><strong>Type:</strong> ${frm.doc.stamp_type}</div>`;
    //     }
    //     if (frm.doc.stamp_number) {
    //         preview_html += `<div class="signature-detail-item"><strong>Number:</strong> ${frm.doc.stamp_number}</div>`;
    //     }
    //     if (frm.doc.stamp_authority) {
    //         preview_html += `<div class="signature-detail-item"><strong>Authority:</strong> ${frm.doc.stamp_authority}</div>`;
    //     }
    //     if (frm.doc.stamp_expiry) {
    //         preview_html += `<div class="signature-detail-item"><strong>Expiry:</strong> ${frappe.datetime.str_to_user(frm.doc.stamp_expiry)}</div>`;
    //     }
    //     preview_html += '</div>';
    // }

	// Add signature details if it's a digital signature
	//  if (!is_stamp) {
    //     preview_html += '<div class="signature-details-card">';
    //     preview_html += '<h5 class="signature-details-title">{__(Signature Details)}</h5>';

    //     if (frm.doc.signature_name) {
    //         preview_html += `<div class="signature-detail-item"><strong>Signer:</strong> ${frm.doc.signature_name}</div>`;
    //     }
    //     if (frm.doc.signature_type) {
    //         preview_html += `<div class="signature-detail-item"><strong>Signer:</strong> ${frm.doc.signature_type}</div>`;
    //     }
    //     if (frm.doc.signature_date) {
    //         preview_html += `<div class="signature-detail-item"><strong>Date:</strong> ${frappe.datetime.str_to_user(frm.doc.signature_date)}</div>`;
    //     }
    //     if (frm.doc.signature_purpose) {
    //         preview_html += `<div class="signature-detail-item"><strong>Purpose:</strong> ${frm.doc.signature_purpose}</div>`;
    //     }
    //     preview_html += '</div>';
    // }

    const dialog = new frappe.ui.Dialog({
        title: preview_title,
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'preview',
                options: preview_html
            }
        ],
		 primary_action_label: __('Close'),
        primary_action: function() {
            dialog.hide();
        }
    });

    dialog.show();
}
