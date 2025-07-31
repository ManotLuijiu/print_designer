#!/usr/bin/env python3
"""
Complete Company Signatures Installation
This script runs all necessary installation steps to set up Company signature fields and tab.
"""

import frappe

def install_all_signature_components():
    """Install all signature components for Company DocType"""
    
    print("🔧 Installing Complete Company Signature System")
    print("=" * 60)
    
    results = []
    
    # Step 1: Install signature fields using safe_install
    print("\n📝 Step 1: Installing signature fields...")
    try:
        from print_designer.api.safe_install import safe_install_signature_enhancements
        result1 = safe_install_signature_enhancements()
        
        if result1.get("success"):
            print("✅ Signature fields installed successfully")
            for step in result1.get("steps", []):
                status = "✅" if step["success"] else "❌"
                print(f"   {status} {step['title']}: {step['message']}")
        else:
            print(f"❌ Signature fields installation failed: {result1.get('error', 'Unknown error')}")
        
        results.append(("Signature Fields", result1.get("success", False)))
        
    except Exception as e:
        print(f"❌ Error installing signature fields: {str(e)}")
        results.append(("Signature Fields", False))
    
    # Step 2: Create Company Stamps & Signatures tab
    print("\n📑 Step 2: Creating Stamps & Signatures tab...")
    try:
        from print_designer.custom.company_tab import create_company_stamps_signatures_tab
        result2 = create_company_stamps_signatures_tab()
        
        if result2:
            print("✅ Stamps & Signatures tab created successfully")
        else:
            print("⚠️  Tab already exists or creation skipped")
        
        results.append(("Company Tab", result2 if result2 is not None else True))
        
    except Exception as e:
        print(f"❌ Error creating company tab: {str(e)}")
        results.append(("Company Tab", False))
    
    # Step 3: Install complete signature system
    print("\n🚀 Step 3: Running complete signature setup...")
    try:
        from print_designer.api.complete_setup import complete_signature_setup
        result3 = complete_signature_setup()
        
        if result3.get("success"):
            print("✅ Complete signature setup successful")
            for step in result3.get("steps", []):
                status = "✅" if step["success"] else "❌"
                print(f"   {status} {step['title']}: {step.get('message', '')}")
        else:
            print(f"❌ Complete setup failed: {result3.get('error', 'Unknown error')}")
        
        results.append(("Complete Setup", result3.get("success", False)))
        
    except Exception as e:
        print(f"❌ Error in complete setup: {str(e)}")
        results.append(("Complete Setup", False))
    
    # Step 4: Verify installation
    print("\n🔍 Step 4: Verifying installation...")
    try:
        # Check custom fields
        company_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Company"},
            fields=["fieldname", "label", "fieldtype"]
        )
        
        signature_fields = [f for f in company_fields if any(keyword in f.fieldname for keyword in ["signature", "stamp", "seal"])]
        tab_field = [f for f in company_fields if f.fieldname == "stamps_signatures_tab"]
        
        print(f"   📊 Found {len(signature_fields)} signature/stamp fields")
        print(f"   📑 Tab field exists: {'✅' if tab_field else '❌'}")
        
        for field in signature_fields:
            print(f"      - {field.fieldname} ({field.label}) - {field.fieldtype}")
        
        verification_success = len(signature_fields) >= 6 and len(tab_field) > 0
        results.append(("Verification", verification_success))
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        results.append(("Verification", False))
    
    # Final summary
    print("\n📊 Installation Summary:")
    print("-" * 40)
    
    all_success = True
    for component, success in results:
        status = "✅ Success" if success else "❌ Failed"
        print(f"   {component}: {status}")
        if not success:
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 Company signature system installation completed successfully!")
        print("   - All signature fields are installed")
        print("   - Stamps & Signatures tab is created")
        print("   - System is ready for use")
    else:
        print("⚠️  Installation completed with some issues.")
        print("   Please check the errors above and run again if needed.")
    print("=" * 60)

# Function for bench execute
def run_complete_install():
    install_all_signature_components()

if __name__ == "__main__":
    run_complete_install()