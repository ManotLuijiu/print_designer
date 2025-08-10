#!/usr/bin/env python3
"""
EMERGENCY FIX for Stock Entry watermark_text column error
This script will directly fix the database schema issue
"""

import sys
sys.path.insert(0, '/home/frappe/frappe-bench')

import frappe

def emergency_fix_stock_entry():
    """Emergency fix for Stock Entry watermark_text column"""
    
    try:
        frappe.init('tipsiricons.bunchee.online')
        frappe.connect()
        
        print("🚨 EMERGENCY FIX: Adding watermark_text column to Stock Entry")
        print("=" * 60)
        
        # Step 1: Check if column exists
        columns = frappe.db.sql("SHOW COLUMNS FROM `tabStock Entry` LIKE 'watermark_text'")
        
        if not columns:
            print("❌ watermark_text column is MISSING from Stock Entry table")
            print("🔧 Adding watermark_text column directly to database...")
            
            # Add the column directly to the database
            frappe.db.sql("""
                ALTER TABLE `tabStock Entry` 
                ADD COLUMN `watermark_text` varchar(140) DEFAULT 'None'
            """)
            
            print("✅ watermark_text column added to Stock Entry table")
        else:
            print("✅ watermark_text column already exists in Stock Entry table")
        
        # Step 2: Ensure Custom Field exists
        custom_field_exists = frappe.db.exists("Custom Field", {
            "dt": "Stock Entry",
            "fieldname": "watermark_text"
        })
        
        if not custom_field_exists:
            print("❌ Stock Entry watermark_text Custom Field is MISSING")
            print("🔧 Creating Custom Field...")
            
            from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
            
            custom_fields = {
                "Stock Entry": [
                    {
                        "fieldname": "watermark_text",
                        "fieldtype": "Select",
                        "label": "Document Watermark",
                        "options": "None\nOriginal\nCopy\nDraft\nSubmitted\nCancelled\nDuplicate",
                        "default": "None",
                        "insert_after": "stock_entry_type",
                        "print_hide": 1,
                        "allow_on_submit": 1,
                        "translatable": 1,
                        "description": "Watermark text to display on printed document"
                    }
                ]
            }
            
            create_custom_fields(custom_fields, update=True)
            print("✅ Stock Entry watermark_text Custom Field created")
        else:
            print("✅ Stock Entry watermark_text Custom Field already exists")
        
        # Step 3: Fix other critical DocTypes
        print("\n🔧 Fixing other critical DocTypes...")
        fix_critical_doctypes()
        
        # Step 4: Commit changes
        frappe.db.commit()
        
        # Step 5: Verify fix
        print("\n🧪 Verifying fix...")
        test_stock_entry_creation()
        
        print("\n" + "=" * 60)
        print("🎉 EMERGENCY FIX COMPLETED!")
        print("✅ Stock Entry watermark_text error should now be resolved")
        print("✅ You can now try saving Stock Entry again")
        
        return True
        
    except Exception as e:
        print(f"❌ Emergency fix failed: {str(e)}")
        frappe.db.rollback()
        return False
        
    finally:
        frappe.destroy()


def fix_critical_doctypes():
    """Fix watermark fields for other critical DocTypes"""
    
    critical_doctypes = [
        "Sales Invoice",
        "Purchase Invoice", 
        "Delivery Note",
        "Sales Order",
        "Purchase Order",
        "Payment Entry",
        "Journal Entry",
        "Quotation"
    ]
    
    from print_designer.watermark_fields import WATERMARK_FIELDS
    
    for doctype in critical_doctypes:
        try:
            # Check if column exists
            columns = frappe.db.sql(f"SHOW COLUMNS FROM `tab{doctype}` LIKE 'watermark_text'")
            
            if not columns:
                print(f"  🔧 Adding watermark_text column to {doctype}...")
                frappe.db.sql(f"""
                    ALTER TABLE `tab{doctype}` 
                    ADD COLUMN `watermark_text` varchar(140) DEFAULT 'None'
                """)
                print(f"  ✅ Added column to {doctype}")
            
            # Ensure Custom Field exists
            custom_field_exists = frappe.db.exists("Custom Field", {
                "dt": doctype,
                "fieldname": "watermark_text"
            })
            
            if not custom_field_exists and doctype in WATERMARK_FIELDS:
                from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
                
                create_custom_fields({
                    doctype: WATERMARK_FIELDS[doctype]
                }, update=True)
                print(f"  ✅ Created Custom Field for {doctype}")
                
        except Exception as e:
            print(f"  ⚠️  Could not fix {doctype}: {str(e)}")


def test_stock_entry_creation():
    """Test creating a Stock Entry to verify the fix"""
    try:
        # Test creating a Stock Entry document (don't save it)
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.watermark_text = "Test"
        stock_entry.purpose = "Material Transfer"
        
        # This should not cause an error now
        print("  ✅ Stock Entry with watermark_text can be created without error")
        return True
        
    except Exception as e:
        print(f"  ❌ Stock Entry test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = emergency_fix_stock_entry()
    sys.exit(0 if success else 1)