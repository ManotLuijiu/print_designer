#!/usr/bin/env python3
"""
Fix Company Signatures Installation Script
This script ensures that both signature fields AND the Stamps & Signatures tab are properly installed.
"""

import frappe

def check_custom_fields():
    """Check if signature custom fields exist"""
    company_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Company"},
        fields=["fieldname", "label", "fieldtype", "insert_after"]
    )
    
    signature_fields = [f for f in company_fields if "signature" in f.fieldname or "stamp" in f.fieldname or "seal" in f.fieldname]
    
    print(f"Found {len(signature_fields)} signature-related fields:")
    for field in signature_fields:
        print(f"  - {field.fieldname} ({field.label}) - {field.fieldtype}")
    
    return signature_fields

def check_stamps_signatures_tab():
    """Check if the Stamps & Signatures tab exists"""
    tab_field = frappe.db.exists("Custom Field", {
        "dt": "Company",
        "fieldname": "stamps_signatures_tab",
        "fieldtype": "Tab Break"
    })
    
    if tab_field:
        print("✅ Stamps & Signatures tab exists")
        return True
    else:
        print("❌ Stamps & Signatures tab missing")
        return False

def install_signature_fields():
    """Install signature fields using the signature_fields.py configuration"""
    try:
        from print_designer.signature_fields import get_signature_fields
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        
        signature_fields = get_signature_fields()
        company_fields = signature_fields.get("Company", [])
        
        if company_fields:
            print(f"Installing {len(company_fields)} Company signature fields...")
            create_custom_fields({"Company": company_fields}, ignore_validate=True)
            frappe.db.commit()
            print("✅ Signature fields installed successfully")
            return True
        else:
            print("❌ No Company signature fields found in configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error installing signature fields: {str(e)}")
        return False

def create_stamps_signatures_tab():
    """Create the Stamps & Signatures tab"""
    try:
        from print_designer.custom.company_tab import create_company_stamps_signatures_tab
        
        result = create_company_stamps_signatures_tab()
        if result:
            print("✅ Stamps & Signatures tab created successfully")
            return True
        else:
            print("❌ Failed to create Stamps & Signatures tab")
            return False
            
    except Exception as e:
        print(f"❌ Error creating tab: {str(e)}")
        return False

def main():
    """Main installation process"""
    print("🔧 Fixing Company Signatures Installation")
    print("=" * 50)
    
    # Step 1: Check current status
    print("\n📋 Current Status:")
    existing_fields = check_custom_fields()
    tab_exists = check_stamps_signatures_tab()
    
    # Step 2: Install missing components
    print("\n🚀 Installing Missing Components:")
    
    # Install signature fields
    if len(existing_fields) < 6:  # Should have 6 signature/stamp fields
        print("\n📝 Installing signature fields...")
        install_signature_fields()
    else:
        print("\n✅ Signature fields already installed")
    
    # Create tab if missing
    if not tab_exists:
        print("\n📑 Creating Stamps & Signatures tab...")
        create_stamps_signatures_tab()
    else:
        print("\n✅ Stamps & Signatures tab already exists")
    
    # Step 3: Final verification
    print("\n🔍 Final Verification:")
    final_fields = check_custom_fields()
    final_tab_exists = check_stamps_signatures_tab()
    
    print(f"\n📊 Results:")
    print(f"  - Signature fields: {len(final_fields)}/6")
    print(f"  - Stamps & Signatures tab: {'✅' if final_tab_exists else '❌'}")
    
    if len(final_fields) >= 6 and final_tab_exists:
        print("\n🎉 Installation completed successfully!")
        print("   The Company DocType now has both signature fields and the Stamps & Signatures tab.")
    else:
        print("\n⚠️ Installation incomplete. Please check the errors above.")

def run_fix():
    """Function to be called by bench execute"""
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_fix()