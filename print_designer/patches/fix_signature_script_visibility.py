import frappe


def execute():
    """Fix signature script visibility by removing JavaScript from HTML field and creating proper Client Script"""
    
    # Updated HTML without JavaScript
    updated_html = """
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
                                        <span class="badge badge-info signature-count-badge" id="total-signatures">0</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-body text-center">
                                        <h6>Company Stamps</h6>
                                        <span class="badge badge-warning signature-count-badge" id="company-stamps">0</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card">
                                    <div class="card-body text-center">
                                        <h6>Active</h6>
                                        <span class="badge badge-success signature-count-badge" id="active-signatures">0</span>
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
                .signature-management-panel .signature-count-badge {
                    min-width: 40px;
                    padding: 6px 12px;
                    font-size: 14px;
                    font-weight: var(--weight-medium);
                    display: inline-block;
                    text-align: center;
                    border-radius: var(--border-radius-sm);
                }
                </style>
                """
    
    # JavaScript for Client Script
    client_script_content = """
frappe.ui.form.on('Print Settings', {
    refresh: function(frm) {
        // Load signature statistics when form loads
        setTimeout(function() {
            load_signature_statistics();
        }, 500);
    }
});

function load_signature_statistics() {
    // Get total signatures
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Signature Basic Information',
            filters: {}
        },
        callback: function(r) {
            if (r.message !== undefined) {
                const totalElement = document.getElementById('total-signatures');
                if (totalElement) {
                    totalElement.textContent = r.message;
                }
            }
        }
    });
    
    // Get company stamps
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Signature Basic Information',
            filters: {
                signature_category: 'Company Stamp'
            }
        },
        callback: function(r) {
            if (r.message !== undefined) {
                const stampsElement = document.getElementById('company-stamps');
                if (stampsElement) {
                    stampsElement.textContent = r.message;
                }
            }
        }
    });
    
    // Get active signatures
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Signature Basic Information',
            filters: {
                is_active: 1
            }
        },
        callback: function(r) {
            if (r.message !== undefined) {
                const activeElement = document.getElementById('active-signatures');
                if (activeElement) {
                    activeElement.textContent = r.message;
                }
            }
        }
    });
}
"""
    
    # Update Custom Field for Print Settings (remove JavaScript from HTML)
    try:
        custom_field_name = frappe.db.get_value("Custom Field", 
            {"dt": "Print Settings", "fieldname": "signature_management_html"}, "name")
        
        if custom_field_name:
            cf = frappe.get_doc("Custom Field", custom_field_name)
            cf.options = updated_html
            cf.save()
            print(f"✅ Updated Custom Field HTML (removed JavaScript): {custom_field_name}")
        else:
            print("❌ Custom Field not found for Print Settings")
    except Exception as e:
        print(f"Warning: Could not update Print Settings Custom Field: {e}")
    
    # Create or update Client Script for Print Settings signature functionality
    try:
        # Check if client script already exists
        existing_scripts = frappe.get_all("Client Script", 
            {"dt": "Print Settings", "script": ["like", "%signature%"]}, ["name"])
        
        if existing_scripts:
            # Update existing script
            for script in existing_scripts:
                cs = frappe.get_doc("Client Script", script.name)
                cs.script = client_script_content
                cs.save()
                print(f"✅ Updated existing Client Script: {script.name}")
        else:
            # Create new client script
            client_script = frappe.new_doc("Client Script")
            client_script.dt = "Print Settings"
            client_script.script = client_script_content
            client_script.enabled = 1
            client_script.insert()
            print(f"✅ Created new Client Script for Print Settings signature functionality")
    except Exception as e:
        print(f"Warning: Could not create/update Client Script: {e}")
    
    frappe.db.commit()
    print("✅ Fixed signature script visibility - moved JavaScript to Client Script")