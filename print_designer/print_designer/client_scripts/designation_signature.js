// Client Script for Designation DocType
// Enhances signature management and shows sync status

frappe.ui.form.on('Designation', {
    refresh: function(frm) {
        if (frm.doc.name) {
            // Add custom buttons for signature management
            add_signature_management_buttons(frm);
            
            // Show signature sync status
            show_signature_sync_status(frm);
        }
    },
    
    designation_signature: function(frm) {
        if (frm.doc.designation_signature) {
            // When signature is uploaded, offer to sync to employees
            frappe.msgprint({
                title: __('Signature Uploaded'),
                message: __('Would you like to sync this signature to employees with this designation?'),
                primary_action: {
                    label: __('Sync Now'),
                    action: function() {
                        sync_designation_signatures(frm);
                    }
                }
            });
        }
    },
    
    signature_authority_level: function(frm) {
        // Update approval limits based on authority level
        set_default_approval_limits(frm);
    }
});

function add_signature_management_buttons(frm) {
    // Sync Signatures button
    frm.add_custom_button(__('Sync Signatures'), function() {
        sync_designation_signatures(frm);
    }, __('Signature Management'));
    
    // Show Signature Report button
    frm.add_custom_button(__('Signature Report'), function() {
        show_signature_report(frm);
    }, __('Signature Management'));
    
    // View Employee Signatures button
    frm.add_custom_button(__('View Employee Signatures'), function() {
        view_employee_signatures(frm);
    }, __('Signature Management'));
    
    // Bulk Upload Signatures button
    frm.add_custom_button(__('Bulk Upload'), function() {
        show_bulk_upload_dialog(frm);
    }, __('Signature Management'));
}

function show_signature_sync_status(frm) {
    if (!frm.doc.name) return;
    
    // Get signature hierarchy for this designation
    frappe.call({
        method: 'print_designer.api.designation_signature_sync.get_signature_hierarchy',
        args: {
            designation: frm.doc.name
        },
        callback: function(r) {
            if (r.message && !r.message.error) {
                display_signature_status(frm, r.message);
            }
        }
    });
}

function display_signature_status(frm, hierarchy) {
    let status_html = '<div class="signature-status-container">';
    
    // Show current signature status
    if (frm.doc.designation_signature) {
        status_html += `
            <div class="alert alert-success">
                <strong>✅ Designation Signature: </strong>Uploaded
                <br><small>Authority Level: ${frm.doc.signature_authority_level || 'Not Set'}</small>
                <br><small>Max Approval: ${format_currency(frm.doc.max_approval_amount || 0)}</small>
            </div>
        `;
    } else {
        status_html += `
            <div class="alert alert-warning">
                <strong>⚠️ Designation Signature: </strong>Not uploaded
            </div>
        `;
    }
    
    // Show employee count with signatures
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Employee',
            filters: {
                designation: frm.doc.name
            }
        },
        callback: function(r) {
            let total_employees = r.message || 0;
            
            frappe.call({
                method: 'frappe.client.get_count', 
                args: {
                    doctype: 'Employee',
                    filters: {
                        designation: frm.doc.name,
                        signature_image: ['!=', '']
                    }
                },
                callback: function(r2) {
                    let employees_with_signatures = r2.message || 0;
                    let coverage_percent = total_employees > 0 ? Math.round((employees_with_signatures / total_employees) * 100) : 0;
                    
                    status_html += `
                        <div class="alert alert-info">
                            <strong>👥 Employee Coverage: </strong>${employees_with_signatures}/${total_employees} (${coverage_percent}%)
                        </div>
                    `;
                    
                    status_html += '</div>';
                    
                    // Add to form
                    if (!frm.fields_dict.signature_status_html) {
                        frm.add_custom_button(__('Refresh Status'), function() {
                            show_signature_sync_status(frm);
                        });
                    }
                    
                    // Insert status after designation_signature field
                    let field_wrapper = frm.fields_dict.designation_signature.wrapper;
                    let existing_status = field_wrapper.querySelector('.signature-status-container');
                    if (existing_status) {
                        existing_status.remove();
                    }
                    
                    let status_div = document.createElement('div');
                    status_div.innerHTML = status_html;
                    field_wrapper.appendChild(status_div);
                }
            });
        }
    });
}

function sync_designation_signatures(frm) {
    frappe.show_alert({
        message: __('Syncing signatures...'),
        indicator: 'blue'
    });
    
    frappe.call({
        method: 'print_designer.api.designation_signature_sync.sync_designation_signatures',
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __(`Sync completed! Updated ${r.message.designations_updated} designations, ${r.message.employees_synced} employees, ${r.message.users_synced} users`),
                    indicator: 'green'
                });
                
                // Refresh status display
                setTimeout(() => {
                    show_signature_sync_status(frm);
                }, 1000);
            } else {
                frappe.show_alert({
                    message: __('Sync failed: ' + (r.message?.error || 'Unknown error')),
                    indicator: 'red'
                });
            }
        }
    });
}

function show_signature_report(frm) {
    frappe.call({
        method: 'print_designer.api.designation_signature_sync.get_designation_signature_report',
        callback: function(r) {
            if (r.message && !r.message.error) {
                let report = r.message;
                
                let dialog = new frappe.ui.Dialog({
                    title: 'Signature Coverage Report',
                    size: 'large',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'report_html'
                        }
                    ]
                });
                
                let report_html = `
                    <div class="signature-report">
                        <h4>📊 Summary</h4>
                        <div class="row">
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5>${report.summary.total_designations}</h5>
                                        <small>Total Designations</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5>${report.summary.designations_with_signatures}</h5>
                                        <small>With Signatures</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5>${report.summary.total_employees}</h5>
                                        <small>Total Employees</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card text-center">
                                    <div class="card-body">
                                        <h5>${report.summary.coverage_percentage}%</h5>
                                        <small>Coverage Rate</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <h4>🏢 Designation Details</h4>
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>Designation</th>
                                    <th>Signature</th>
                                    <th>Authority</th>
                                    <th>Employees</th>
                                    <th>Coverage</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                report.designations.forEach(des => {
                    let signature_status = des.has_signature ? '✅' : '❌';
                    let coverage_color = des.coverage_rate > 80 ? 'success' : des.coverage_rate > 50 ? 'warning' : 'danger';
                    
                    report_html += `
                        <tr>
                            <td><a href="/app/designation/${des.name}">${des.name}</a></td>
                            <td>${signature_status}</td>
                            <td><span class="badge badge-info">${des.authority_level}</span></td>
                            <td>${des.employees_with_signatures}/${des.employee_count}</td>
                            <td><span class="badge badge-${coverage_color}">${des.coverage_rate}%</span></td>
                        </tr>
                    `;
                });
                
                report_html += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                dialog.fields_dict.report_html.$wrapper.html(report_html);
                dialog.show();
            }
        }
    });
}

function view_employee_signatures(frm) {
    frappe.route_options = {
        'designation': frm.doc.name
    };
    frappe.set_route('List', 'Employee');
}

function show_bulk_upload_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: 'Bulk Upload Designation Signatures',
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'instructions',
                options: `
                    <div class="alert alert-info">
                        <h5>📋 Instructions:</h5>
                        <ol>
                            <li>Upload signature images to the File Manager first</li>
                            <li>Copy the file URLs from File Manager</li>
                            <li>Enter the mappings below</li>
                            <li>Click 'Bulk Update' to apply all signatures at once</li>
                        </ol>
                    </div>
                `
            },
            {
                fieldtype: 'Table',
                fieldname: 'signature_mappings',
                label: 'Signature Mappings',
                fields: [
                    {
                        fieldtype: 'Link',
                        fieldname: 'designation',
                        label: 'Designation',
                        options: 'Designation',
                        in_list_view: 1,
                        reqd: 1
                    },
                    {
                        fieldtype: 'Attach',
                        fieldname: 'signature_url',
                        label: 'Signature File',
                        in_list_view: 1,
                        reqd: 1
                    },
                    {
                        fieldtype: 'Select',
                        fieldname: 'authority_level',
                        label: 'Authority Level',
                        options: 'None\nLow\nMedium\nHigh\nExecutive',
                        default: 'Medium',
                        in_list_view: 1
                    },
                    {
                        fieldtype: 'Currency',
                        fieldname: 'max_approval_amount',
                        label: 'Max Approval Amount',
                        in_list_view: 1
                    }
                ]
            }
        ],
        primary_action_label: 'Bulk Update',
        primary_action: function() {
            let mappings = dialog.get_value('signature_mappings');
            
            if (mappings && mappings.length > 0) {
                frappe.call({
                    method: 'print_designer.api.designation_signature_sync.bulk_update_designation_signatures',
                    args: {
                        designation_mappings: JSON.stringify(mappings)
                    },
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __(`Bulk update completed! Updated ${r.message.updated_count} designations`),
                                indicator: 'green'
                            });
                            dialog.hide();
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title: 'Bulk Update Errors',
                                message: r.message?.errors?.join('<br>') || 'Unknown error occurred'
                            });
                        }
                    }
                });
            } else {
                frappe.msgprint('Please add at least one signature mapping');
            }
        }
    });
    
    dialog.show();
}

function set_default_approval_limits(frm) {
    if (!frm.doc.max_approval_amount && frm.doc.signature_authority_level) {
        let default_limits = {
            'Low': 10000,
            'Medium': 50000,
            'High': 200000,
            'Executive': 1000000
        };
        
        let default_amount = default_limits[frm.doc.signature_authority_level];
        if (default_amount) {
            frm.set_value('max_approval_amount', default_amount);
        }
    }
}

function format_currency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}