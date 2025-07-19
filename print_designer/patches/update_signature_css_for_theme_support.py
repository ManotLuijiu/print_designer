import frappe


def execute():
    """Update signature management CSS to support theme switching"""
    
    # Updated CSS with theme support
    updated_css = """
                <div class="signature-management-panel">
                    <h5>Manage Signatures & Company Stamps</h5>
                    <p>Configure and manage digital signatures and company stamps for your documents.</p>
                    <div class="row">
                        <div class="col-md-6">
                            <a href="/app/signature-basic-information" class="btn btn-primary btn-sm">
                                <i class="fa fa-edit"></i> Manage Signatures
                            </a>
                        </div>
                        <div class="col-md-6">
                            <a href="/app/signature-basic-information/new-signature-basic-information-1" class="btn btn-success btn-sm">
                                <i class="fa fa-plus"></i> Create New Signature
                            </a>
                        </div>
                    </div>
                    <hr>
                    <div class="signature-quick-stats" id="signature-stats">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-body text-center">
                                        <h6>Total Signatures</h6>
                                        <span class="badge badge-info" id="total-signatures">-</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-body text-center">
                                        <h6>Company Stamps</h6>
                                        <span class="badge badge-warning" id="company-stamps">-</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-body text-center">
                                        <h6>Active</h6>
                                        <span class="badge badge-success" id="active-signatures">-</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <style>
                .signature-management-panel {
                    padding: var(--padding-md);
                    background: var(--subtle-fg);
                    border: 1px solid var(--border-color);
                    border-radius: var(--border-radius);
                    margin: var(--margin-md) 0;
                }
                .signature-management-panel .card {
                    border: 1px solid var(--border-color);
                    border-radius: var(--border-radius-sm);
                    margin-bottom: var(--margin-sm);
                    background: var(--card-bg);
                }
                .signature-management-panel .card-body {
                    padding: var(--padding-md);
                    color: var(--text-color);
                }
                .signature-management-panel .btn {
                    margin-right: var(--margin-sm);
                    margin-bottom: var(--margin-sm);
                }
                .signature-management-panel h5 {
                    color: var(--heading-color);
                    margin-bottom: var(--margin-sm);
                }
                .signature-management-panel p {
                    color: var(--text-muted);
                }
                .signature-management-panel h6 {
                    color: var(--text-color);
                    font-weight: var(--weight-medium);
                }
                .signature-management-panel hr {
                    border-color: var(--border-color);
                    background-color: var(--border-color);
                }
                .signature-management-panel .badge {
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    border: 1px solid var(--border-color);
                }
                .signature-management-panel .badge-info {
                    background-color: var(--bg-blue);
                    color: var(--text-on-blue);
                    border-color: var(--blue-500);
                }
                .signature-management-panel .badge-warning {
                    background-color: var(--bg-yellow);
                    color: var(--text-on-yellow);
                    border-color: var(--yellow-500);
                }
                .signature-management-panel .badge-success {
                    background-color: var(--bg-green);
                    color: var(--text-on-green);
                    border-color: var(--green-500);
                }
                </style>
                """
    
    # Update Custom Field for Print Settings
    try:
        custom_field_name = frappe.db.get_value("Custom Field", 
            {"dt": "Print Settings", "fieldname": "signature_management_html"}, "name")
        
        if custom_field_name:
            cf = frappe.get_doc("Custom Field", custom_field_name)
            cf.options = updated_css
            cf.save()
            print(f"✅ Updated Custom Field: {custom_field_name}")
        else:
            print("❌ Custom Field not found for Print Settings")
    except Exception as e:
        print(f"Warning: Could not update Print Settings Custom Field: {e}")
    
    # Also update Custom Field for Accounts Settings (if it still exists)
    try:
        custom_field_name = frappe.db.get_value("Custom Field", 
            {"dt": "Accounts Settings", "fieldname": "signature_management_html"}, "name")
        
        if custom_field_name:
            cf = frappe.get_doc("Custom Field", custom_field_name)
            cf.options = updated_css
            cf.save()
            print(f"✅ Updated Custom Field: {custom_field_name}")
        else:
            print("ℹ️  Custom Field not found for Accounts Settings (expected)")
    except Exception as e:
        print(f"Info: Accounts Settings Custom Field not found or already removed: {e}")
    
    frappe.db.commit()
    print("✅ Signature management CSS updated with theme support")