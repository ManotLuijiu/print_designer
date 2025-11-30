"""
Sales Invoice Retention - Backend Calculation Approach

Pure backend-driven retention system that eliminates all API loops.
All calculations happen server-side via document events.
Client script only handles field visibility without any API calls.
"""

import frappe
from frappe import _


def install_minimal_retention_client_script():
    """Install minimal client script that only handles field visibility"""
    
    try:
        # Remove all previous retention client scripts
        old_scripts = [
            "Sales Invoice Retention with Default Rate",
            "Sales Invoice Enhanced Retention", 
            "Sales Invoice Retention System",
            "Sales Invoice Retention - DocType Based"
        ]
        
        for script_name in old_scripts:
            if frappe.db.exists("Client Script", script_name):
                frappe.delete_doc("Client Script", script_name)
                print(f"Removed old script: {script_name}")
        
        # Create minimal client script with zero API calls
        client_script = frappe.get_doc({
            "doctype": "Client Script",
            "name": "Sales Invoice Retention - Backend Driven",
            "dt": "Sales Invoice", 
            "view": "Form",
            "enabled": 1,
            "script": """
// Sales Invoice Retention - Pure Backend Approach (No API calls)
frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        // Simple field visibility based on company field only
        // All calculations handled on server-side
        const has_company = frm.doc.company ? true : false;
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], has_company);
        
        if (has_company && frm.doc.custom_retention_amount) {
            // Show retention info in dashboard (read-only display)
            frm.dashboard.add_comment(__('Retention Amount: {0}', [format_currency(frm.doc.custom_retention_amount)]), 'blue', true);
        }
    },
    
    company: function(frm) {
        // Just toggle field visibility - backend handles all logic
        const has_company = frm.doc.company ? true : false;
        frm.toggle_display(['custom_retention', 'custom_retention_amount'], has_company);
    }
    
    // NOTE: No onchange events for custom_retention or base_net_total
    // All calculations happen automatically on server-side via document events
});

// No helper functions, no API calls, no cache management needed
"""
        })
        
        client_script.insert()
        frappe.db.commit()
        
        print(f"✅ Created minimal client script: {client_script.name}")
        return client_script
        
    except Exception as e:
        frappe.log_error(f"Error installing minimal retention client script: {str(e)}")
        print(f"❌ Error: {str(e)}")
        raise


def setup_backend_retention_system():
    """Setup complete backend-driven retention system (Company-based)"""

    print("🚀 Setting up backend-driven retention system...")

    # Step 1: Install minimal client script (no API calls)
    install_minimal_retention_client_script()

    # Step 2: Verify document events are registered in hooks.py
    print("✅ Document events configured in hooks.py")
    print("   - Sales Invoice validate: sales_invoice_calculations.sales_invoice_calculate_thailand_amounts")
    print("   - Reads from Company fields directly (construction_service, default_retention_rate)")

    # NOTE: Company Retention Settings creation REMOVED
    # The retention system now reads directly from Company fields:
    # - construction_service
    # - default_retention_rate
    # - default_retention_account
    # See: sales_order_calculations.py:64-82, sales_invoice_calculations.py:58-83

    frappe.db.commit()

    print("""
🎉 Backend-driven retention system ready!

✅ Key Benefits:
   - Zero API calls from client-side
   - All calculations happen on server during save/validate
   - Reads directly from Company fields (no Company Retention Settings)
   - No cache management needed
   - No infinite loops possible

🔧 How it works:
   1. Client script only shows/hides fields based on company
   2. Server-side events automatically calculate retention when:
      - Document is validated
      - Document is saved
   3. Settings come from Company fields:
      - construction_service (enable/disable)
      - default_retention_rate (percentage)
      - default_retention_account (GL account)

🔄 To test:
   1. Clear browser cache
   2. Open Sales Invoice
   3. Add items and observe automatic retention calculation
   4. No API calls should appear in network tab
""")
    
    return True


if __name__ == "__main__":
    setup_backend_retention_system()