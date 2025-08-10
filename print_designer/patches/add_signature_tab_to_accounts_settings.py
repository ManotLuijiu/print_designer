import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Add Signature tab to Print Settings (moved from Accounts Settings)"""

    # Define custom fields for Print Settings
    custom_fields = {
        "Print Settings": [
            {
                "fieldname": "signature_tab",
                "fieldtype": "Tab Break",
                "label": "Signature",
                "insert_after": "font_size",
            },
            {
                "fieldname": "signature_settings_section",
                "fieldtype": "Section Break",
                "label": "Signature Settings",
                "insert_after": "signature_tab",
            },
            {
                "fieldname": "enable_signature_in_print",
                "fieldtype": "Check",
                "label": "Enable Signature in Print Formats",
                "default": "0",
                "insert_after": "signature_settings_section",
                "description": "Enable signature functionality in print formats",
            },
            {
                "fieldname": "default_signature_user",
                "fieldtype": "Link",
                "label": "Default Signature User",
                "options": "User",
                "insert_after": "enable_signature_in_print",
                "depends_on": "enable_signature_in_print",
                "description": "Default user for signature selection",
            },
            {
                "fieldname": "signature_management_section",
                "fieldtype": "Section Break",
                "label": "Signature Management",
                "insert_after": "default_signature_user",
            },
            {
                "fieldname": "signature_management_html",
                "fieldtype": "HTML",
                "label": "Signature Management",
                "insert_after": "signature_management_section",
                "options": """
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
                """,
            },
        ]
    }

    # Create custom fields
    create_custom_fields(custom_fields, update=True)

    print("✅ Signature tab added to Print Settings")

    # Create client script to load signature statistics
    create_print_settings_signature_script()


def create_print_settings_signature_script():
    """Create client script for Print Settings signature functionality"""

    script_content = """
frappe.ui.form.on('Print Settings', {
    refresh: function(frm) {
        // Load signature statistics when signature tab is active
        if (frm.doc.enable_signature_in_print) {
            load_signature_stats();
        }
    },

    enable_signature_in_print: function(frm) {
        if (frm.doc.enable_signature_in_print) {
            load_signature_stats();
        }
    }
});

function load_signature_stats() {
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Signature Basic Information',
            filters: {}
        },
        callback: function(r) {
            if (r.message) {
                document.getElementById('total-signatures').textContent = r.message;
            }
        }
    });

    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Signature Basic Information',
            filters: {
                signature_category: 'Company Stamp'
            }
        },
        callback: function(r) {
            if (r.message) {
                document.getElementById('company-stamps').textContent = r.message;
            }
        }
    });

    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Signature Basic Information',
            filters: {
                is_active: 1
            }
        },
        callback: function(r) {
            if (r.message) {
                document.getElementById('active-signatures').textContent = r.message;
            }
        }
    });
}
"""

    # Check if client script already exists
    if frappe.db.exists("Client Script", {"dt": "Print Settings"}):
        # Update existing client script
        existing_scripts = frappe.get_all(
            "Client Script", {"dt": "Print Settings"}, ["name"]
        )
        if existing_scripts:
            frappe.db.set_value(
                "Client Script", existing_scripts[0].name, "script", script_content
            )
        else:
            create_new_client_script(script_content)
    else:
        create_new_client_script(script_content)


def create_new_client_script(script_content):
    """Create new client script with proper name"""
    try:
        # Create new client script
        client_script = frappe.new_doc("Client Script")
        client_script.doctype = "Print Settings"
        client_script.script = script_content
        client_script.insert()
        frappe.db.commit()
        print("✅ Client script created for Print Settings signature functionality")
    except Exception as e:
        print(f"Warning: Could not create client script: {e}")
        pass
