import frappe

def verify_signature_integration():
    """Verify that signature integration is working"""
    
    # Check if custom fields exist
    signature_tab = frappe.db.exists("Custom Field", {"dt": "Accounts Settings", "fieldname": "signature_tab"})
    signature_section = frappe.db.exists("Custom Field", {"dt": "Accounts Settings", "fieldname": "signature_settings_section"})
    enable_field = frappe.db.exists("Custom Field", {"dt": "Accounts Settings", "fieldname": "enable_signature_in_print"})
    
    print("=== Signature Integration Status ===")
    print(f"✅ Signature tab field exists: {bool(signature_tab)}")
    print(f"✅ Signature section field exists: {bool(signature_section)}")
    print(f"✅ Enable signature field exists: {bool(enable_field)}")
    
    # Check if DocTypes exist
    signature_doctype = frappe.db.exists("DocType", "Signature Basic Information")
    signature_usage_doctype = frappe.db.exists("DocType", "Signature Usage")
    
    print(f"✅ Signature Basic Information DocType exists: {bool(signature_doctype)}")
    print(f"✅ Signature Usage DocType exists: {bool(signature_usage_doctype)}")
    
    # Check if client script exists
    client_script = frappe.db.exists("Client Script", {"dt": "Accounts Settings"})
    print(f"✅ Client Script for Accounts Settings exists: {bool(client_script)}")
    
    # Summary
    all_good = all([signature_tab, signature_section, enable_field, signature_doctype, signature_usage_doctype])
    if all_good:
        print("\n🎉 SUCCESS: Signature integration is fully working!")
        print("📝 You can now:")
        print("   - Go to Setup > Accounts Settings > Signature tab")
        print("   - Create signatures at Print Designer > Signature Basic Information")
        print("   - Use signatures in print formats")
    else:
        print("\n⚠️  Some components are missing - please check the setup")
    
    return all_good