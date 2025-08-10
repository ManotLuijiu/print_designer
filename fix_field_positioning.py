#!/usr/bin/env python3
"""
Fix Company Signature Fields Positioning
This script ensures signature fields are properly positioned in the Stamps & Signatures tab
"""

import frappe

def fix_signature_field_positioning():
    """Fix the positioning of signature fields to appear in the Stamps & Signatures tab"""
    
    print("🔧 Fixing Company Signature Fields Positioning")
    print("=" * 60)
    
    # Expected field sequence and positioning
    field_sequence = [
        {
            "fieldname": "stamps_signatures_tab",
            "fieldtype": "Tab Break",
            "label": "Stamps & Signatures", 
            "insert_after": "default_in_transit_warehouse"
        },
        {
            "fieldname": "company_signatures_section",
            "fieldtype": "Section Break",
            "label": "Company Signatures",
            "insert_after": "stamps_signatures_tab"
        },
        {
            "fieldname": "authorized_signature_1",
            "fieldtype": "Attach Image",
            "label": "Authorized Signature 1",
            "insert_after": "company_signatures_section",
            "description": "Primary authorized signatory for company documents"
        },
        {
            "fieldname": "authorized_signature_2", 
            "fieldtype": "Attach Image",
            "label": "Authorized Signature 2",
            "insert_after": "authorized_signature_1",
            "description": "Secondary authorized signatory for company documents"
        },
        {
            "fieldname": "ceo_signature",
            "fieldtype": "Attach Image", 
            "label": "CEO Signature",
            "insert_after": "authorized_signature_2",
            "description": "CEO signature for executive documents"
        },
        {
            "fieldname": "company_stamps_section",
            "fieldtype": "Section Break",
            "label": "Company Stamps", 
            "insert_after": "ceo_signature"
        },
        {
            "fieldname": "company_stamp_1",
            "fieldtype": "Attach Image",
            "label": "Company Stamp 1",
            "insert_after": "company_stamps_section",
            "description": "Primary company stamp for official documents"
        },
        {
            "fieldname": "company_stamp_2",
            "fieldtype": "Attach Image", 
            "label": "Company Stamp 2",
            "insert_after": "company_stamp_1",
            "description": "Secondary company stamp for official documents"
        },
        {
            "fieldname": "official_seal",
            "fieldtype": "Attach Image",
            "label": "Official Seal", 
            "insert_after": "company_stamp_2",
            "description": "Official company seal for legal documents"
        }
    ]
    
    results = []
    
    for field_config in field_sequence:
        fieldname = field_config["fieldname"]
        
        print(f"\n🔄 Processing {fieldname}...")
        
        try:
            # Check if field exists
            existing_field = frappe.db.get_value(
                "Custom Field",
                {"dt": "Company", "fieldname": fieldname},
                ["name", "insert_after"],
                as_dict=True
            )
            
            if existing_field:
                # Update positioning if wrong
                if existing_field.insert_after != field_config["insert_after"]:
                    print(f"   📝 Updating insert_after: {existing_field.insert_after} → {field_config['insert_after']}")
                    
                    frappe.db.set_value(
                        "Custom Field",
                        existing_field.name,
                        "insert_after",
                        field_config["insert_after"]
                    )
                    
                    # Also update other properties if needed
                    update_values = {}
                    if "description" in field_config:
                        update_values["description"] = field_config["description"]
                    
                    if update_values:
                        for key, value in update_values.items():
                            frappe.db.set_value("Custom Field", existing_field.name, key, value)
                    
                    print(f"   ✅ Updated positioning for {fieldname}")
                    results.append((fieldname, "updated"))
                else:
                    print(f"   ✅ {fieldname} already correctly positioned")
                    results.append((fieldname, "correct"))
            else:
                # Create the field if it doesn't exist
                print(f"   ➕ Creating missing field {fieldname}")
                
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = "Company"
                custom_field.fieldname = fieldname
                custom_field.fieldtype = field_config["fieldtype"]
                custom_field.label = field_config["label"]
                custom_field.insert_after = field_config["insert_after"]
                
                if "description" in field_config:
                    custom_field.description = field_config["description"]
                
                custom_field.insert()
                print(f"   ✅ Created {fieldname}")
                results.append((fieldname, "created"))
                
        except Exception as e:
            print(f"   ❌ Error processing {fieldname}: {str(e)}")
            results.append((fieldname, f"error: {str(e)}"))
    
    # Commit all changes
    frappe.db.commit()
    
    # Clear cache to refresh DocType
    frappe.clear_cache(doctype="Company")
    
    print("\n📊 Results Summary:")
    print("-" * 40)
    
    for fieldname, status in results:
        status_icon = {
            "updated": "🔄",
            "correct": "✅", 
            "created": "➕"
        }
        
        if status.startswith("error"):
            print(f"❌ {fieldname}: {status}")
        else:
            icon = status_icon.get(status, "❓")
            print(f"{icon} {fieldname}: {status}")
    
    success_count = len([r for r in results if not r[1].startswith("error")])
    print(f"\n📈 Successfully processed {success_count}/{len(results)} fields")
    
    return results

def verify_field_positioning():
    """Verify that fields are correctly positioned"""
    
    print("\n🔍 Verifying Field Positioning")
    print("=" * 40)
    
    # Get all Company custom fields ordered by idx
    fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Company"},
        fields=["fieldname", "label", "fieldtype", "insert_after", "idx"],
        order_by="idx asc"
    )
    
    # Find the stamps tab and related fields
    stamps_tab_idx = None
    signature_fields = []
    
    for field in fields:
        if field.fieldname == "stamps_signatures_tab":
            stamps_tab_idx = field.idx
            print(f"📑 Found Stamps & Signatures tab at index {stamps_tab_idx}")
        elif any(keyword in field.fieldname for keyword in ["signature", "stamp", "seal"]):
            signature_fields.append(field)
    
    if stamps_tab_idx is None:
        print("❌ Stamps & Signatures tab not found!")
        return False
    
    # Check if signature fields come after the tab
    fields_in_tab = [f for f in signature_fields if f.idx > stamps_tab_idx]
    
    print(f"🖼️  Found {len(fields_in_tab)} signature fields positioned after the tab:")
    for field in sorted(fields_in_tab, key=lambda x: x.idx):
        print(f"   {field.idx}: {field.fieldname} ({field.label})")
    
    expected_fields = [
        "company_signatures_section", "authorized_signature_1", "authorized_signature_2", 
        "ceo_signature", "company_stamps_section", "company_stamp_1", 
        "company_stamp_2", "official_seal"
    ]
    
    missing_fields = [f for f in expected_fields if f not in [field.fieldname for field in fields_in_tab]]
    
    if missing_fields:
        print(f"\n⚠️  Missing fields in tab: {missing_fields}")
        return False
    else:
        print(f"\n✅ All expected fields are positioned in the Stamps & Signatures tab!")
        return True

def run_fix():
    """Run the complete fix process"""
    try:
        results = fix_signature_field_positioning()
        success = verify_field_positioning()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 Company signature fields positioning fixed successfully!")
            print("   - All signature and stamp fields are now in the Stamps & Signatures tab")
            print("   - Fields are properly ordered and positioned")
            print("   - You can now attach images to these fields")
            print("\n📝 To attach images:")
            print("   1. Go to Company DocType")
            print("   2. Click on the 'Stamps & Signatures' tab")
            print("   3. Click 'Attach' button for each signature/stamp field")
            print("   4. Upload your signature/stamp image files")
        else:
            print("⚠️  Fix completed but some issues remain. Check the output above.")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_fix()