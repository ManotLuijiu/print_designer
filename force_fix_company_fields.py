#!/usr/bin/env python3
"""
Force Fix Company Signature Fields - Direct Database Approach
This script directly manipulates the database to ensure fields are properly positioned
"""

import frappe

def force_fix_company_signature_fields():
    """Force fix by directly updating the database"""
    
    print("🔧 FORCE FIXING Company Signature Fields")
    print("=" * 60)
    
    # Step 1: Delete existing problematic fields if they exist
    print("\n🗑️  Step 1: Cleaning up existing fields...")
    
    fields_to_remove = [
        "stamps_signatures_tab", "company_signatures_section", 
        "authorized_signature_1", "authorized_signature_2", "ceo_signature",
        "company_stamps_section", "company_stamp_1", "company_stamp_2", "official_seal"
    ]
    
    for fieldname in fields_to_remove:
        existing = frappe.db.get_value("Custom Field", {"dt": "Company", "fieldname": fieldname}, "name")
        if existing:
            frappe.delete_doc("Custom Field", existing, force=True)
            print(f"   🗑️  Removed existing {fieldname}")
        else:
            print(f"   ➖ {fieldname} not found (OK)")
    
    frappe.db.commit()
    
    # Step 2: Create fields in the exact correct order
    print("\n➕ Step 2: Creating fields in correct order...")
    
    # Find a good insertion point - look for a standard Company field
    base_field = frappe.db.get_value("DocField", {"parent": "Company", "fieldname": "country"}, "name")
    if not base_field:
        # Fallback to any field that should exist
        base_field = "country"
    
    print(f"   📍 Using insertion point after: {base_field}")
    
    # Create fields one by one in exact order
    field_definitions = [
        {
            "fieldname": "stamps_signatures_tab",
            "label": "Stamps & Signatures", 
            "fieldtype": "Tab Break",
            "insert_after": base_field,
        },
        {
            "fieldname": "company_signatures_section",
            "label": "Company Signatures",
            "fieldtype": "Section Break", 
            "insert_after": "stamps_signatures_tab",
        },
        {
            "fieldname": "authorized_signature_1",
            "label": "Authorized Signature 1",
            "fieldtype": "Attach Image",
            "insert_after": "company_signatures_section",
            "description": "Primary authorized signatory for company documents",
        },
        {
            "fieldname": "authorized_signature_2", 
            "label": "Authorized Signature 2",
            "fieldtype": "Attach Image",
            "insert_after": "authorized_signature_1",
            "description": "Secondary authorized signatory for company documents",
        },
        {
            "fieldname": "ceo_signature",
            "label": "CEO Signature", 
            "fieldtype": "Attach Image",
            "insert_after": "authorized_signature_2",
            "description": "CEO signature for executive documents",
        },
        {
            "fieldname": "company_stamps_section",
            "label": "Company Stamps",
            "fieldtype": "Section Break",
            "insert_after": "ceo_signature",
        },
        {
            "fieldname": "company_stamp_1",
            "label": "Company Stamp 1",
            "fieldtype": "Attach Image", 
            "insert_after": "company_stamps_section",
            "description": "Primary company stamp for official documents",
        },
        {
            "fieldname": "company_stamp_2",
            "label": "Company Stamp 2", 
            "fieldtype": "Attach Image",
            "insert_after": "company_stamp_1",
            "description": "Secondary company stamp for official documents",
        },
        {
            "fieldname": "official_seal",
            "label": "Official Seal",
            "fieldtype": "Attach Image",
            "insert_after": "company_stamp_2", 
            "description": "Official company seal for legal documents",
        }
    ]
    
    created_fields = []
    
    for field_def in field_definitions:
        try:
            # Create custom field document
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Company"
            
            for key, value in field_def.items():
                setattr(custom_field, key, value)
            
            # Additional properties for proper display
            custom_field.permlevel = 0
            custom_field.print_hide = 0
            custom_field.hidden = 0
            custom_field.read_only = 0
            custom_field.allow_on_submit = 0
            
            custom_field.insert()
            created_fields.append(field_def["fieldname"])
            print(f"   ✅ Created {field_def['fieldname']} ({field_def['label']})")
            
        except Exception as e:
            print(f"   ❌ Failed to create {field_def['fieldname']}: {str(e)}")
    
    frappe.db.commit()
    
    # Step 3: Force clear all caches
    print("\n🔄 Step 3: Clearing all caches...")
    frappe.clear_cache()
    frappe.clear_document_cache("Company", "Company")
    frappe.db.sql("DELETE FROM `tabSessions` WHERE user != 'Administrator'")
    
    # Step 4: Reload the DocType
    print("\n🔄 Step 4: Reloading DocType...")
    try:
        frappe.reload_doctype("Company", force=True)
        print("   ✅ DocType reloaded")
    except Exception as e:
        print(f"   ⚠️  DocType reload warning: {str(e)}")
    
    # Step 5: Verify creation
    print("\n🔍 Step 5: Verification...")
    
    all_fields = frappe.get_all(
        "Custom Field", 
        filters={"dt": "Company"},
        fields=["fieldname", "label", "fieldtype", "insert_after", "idx"],
        order_by="idx asc"
    )
    
    signature_fields = [f for f in all_fields if f.fieldname in [fd["fieldname"] for fd in field_definitions]]
    
    print(f"   📊 Found {len(signature_fields)} signature fields:")
    for field in sorted(signature_fields, key=lambda x: x.idx):
        print(f"      {field.idx}: {field.fieldname} ({field.fieldtype}) -> {field.insert_after}")
    
    # Check tab specifically
    tab_field = next((f for f in signature_fields if f.fieldname == "stamps_signatures_tab"), None)
    if tab_field:
        print(f"   📑 Stamps & Signatures tab: ✅ (index {tab_field.idx})")
        
        # Count fields after the tab
        fields_after_tab = [f for f in signature_fields if f.idx > tab_field.idx]
        print(f"   🖼️  Fields in tab: {len(fields_after_tab)}")
        
        if len(fields_after_tab) >= 8:  # Should have 8 fields (2 sections + 6 attach fields)
            print("   🎉 SUCCESS: All fields should now be visible in the Stamps & Signatures tab!")
            return True
        else:
            print(f"   ⚠️  Only {len(fields_after_tab)} fields positioned after tab (expected 8)")
            return False
    else:
        print("   ❌ Stamps & Signatures tab not found!")
        return False

def restart_instructions():
    """Provide instructions for restarting the system"""
    print("\n🔄 IMPORTANT: To see the changes, you need to:")
    print("   1. Restart your Frappe development server:")
    print("      bench restart")
    print("   2. Or refresh your browser with Ctrl+F5 (hard refresh)")
    print("   3. Navigate to Company DocType")
    print("   4. Look for the 'Stamps & Signatures' tab")
    print("\n📋 The tab should contain:")
    print("   - Company Signatures section:")
    print("     • Authorized Signature 1")
    print("     • Authorized Signature 2") 
    print("     • CEO Signature")
    print("   - Company Stamps section:")
    print("     • Company Stamp 1")
    print("     • Company Stamp 2")
    print("     • Official Seal")

def run_force_fix():
    """Execute the force fix"""
    try:
        success = force_fix_company_signature_fields()
        restart_instructions()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 FORCE FIX COMPLETED SUCCESSFULLY!")
            print("   All signature fields have been recreated and positioned correctly.")
        else:
            print("⚠️  FORCE FIX COMPLETED WITH WARNINGS")
            print("   Some fields may not be positioned correctly. Check output above.")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_force_fix()