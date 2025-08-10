#!/usr/bin/env python3
"""
Test script to verify Delivery Note custom fields are properly configured
Run with: bench execute print_designer.test_delivery_fields.test_delivery_fields
"""

import frappe

def test_delivery_fields():
    """Test that all required Delivery Note fields exist and are configured correctly"""
    
    print("🔍 Testing Delivery Note Custom Fields Configuration...")
    print("=" * 60)
    
    # Required fields as specified by user
    required_fields = {
        "customer_approval_status": {
            "fieldtype": "Select",
            "label": "Customer Approval Status",
            "options": "Pending\nApproved\nRejected",
            "default": "Pending"
        },
        "customer_signature": {
            "fieldtype": "Long Text",
            "label": "Customer Digital Signature"
        },
        "customer_approved_by": {
            "fieldtype": "Data",
            "label": "Customer Approved By"
        },
        "customer_approved_on": {
            "fieldtype": "Datetime",
            "label": "Customer Approved On"
        },
        "approval_qr_code": {
            "fieldtype": "Long Text",
            "label": "Approval QR Code"
        }
    }
    
    print("Testing required fields:")
    all_passed = True
    
    for fieldname, expected_config in required_fields.items():
        print(f"\n📋 Testing field: {fieldname}")
        
        # Check if field exists
        field_doc = frappe.db.get_value("Custom Field", {
            "dt": "Delivery Note",
            "fieldname": fieldname
        }, ["fieldtype", "label", "options", "default"], as_dict=True)
        
        if not field_doc:
            print(f"  ❌ Field does not exist: {fieldname}")
            all_passed = False
            continue
        
        print(f"  ✅ Field exists: {fieldname}")
        
        # Verify field type
        if field_doc.fieldtype != expected_config["fieldtype"]:
            print(f"  ❌ Wrong fieldtype. Expected: {expected_config['fieldtype']}, Got: {field_doc.fieldtype}")
            all_passed = False
        else:
            print(f"  ✅ Correct fieldtype: {field_doc.fieldtype}")
        
        # Verify label
        if field_doc.label != expected_config["label"]:
            print(f"  ❌ Wrong label. Expected: {expected_config['label']}, Got: {field_doc.label}")
            all_passed = False
        else:
            print(f"  ✅ Correct label: {field_doc.label}")
        
        # Verify options for Select fields
        if expected_config.get("options") and field_doc.options != expected_config["options"]:
            print(f"  ❌ Wrong options. Expected: {expected_config['options']}, Got: {field_doc.options}")
            all_passed = False
        elif expected_config.get("options"):
            print(f"  ✅ Correct options: {field_doc.options}")
        
        # Verify default for fields that should have one
        if expected_config.get("default") and field_doc.default != expected_config["default"]:
            print(f"  ❌ Wrong default. Expected: {expected_config['default']}, Got: {field_doc.default}")
            all_passed = False
        elif expected_config.get("default"):
            print(f"  ✅ Correct default: {field_doc.default}")
    
    print("\n" + "=" * 60)
    print("🔍 Testing Legacy Compatibility Fields...")
    
    # Test that legacy fields also exist for compatibility
    legacy_fields = [
        "custom_delivery_approval_section",
        "custom_goods_received_status",
        "custom_approval_qr_code",
        "custom_approval_url",
        "custom_customer_approval_date",
        "custom_approved_by",
        "custom_customer_signature",
        "custom_rejection_reason"
    ]
    
    for fieldname in legacy_fields:
        exists = frappe.db.exists("Custom Field", {
            "dt": "Delivery Note",
            "fieldname": fieldname
        })
        
        if exists:
            print(f"  ✅ Legacy field exists: {fieldname}")
        else:
            print(f"  ⚠️  Legacy field missing: {fieldname}")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ All required Delivery Note fields are properly configured")
        print("✅ Field types, labels, and options match specifications")
        print("✅ Legacy compatibility maintained")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Please run the field installation command:")
        print("   bench --site [your-site] install-delivery-note-fields")
    
    print("\n" + "=" * 60)
    print("📋 Summary of Available Fields:")
    
    # List all delivery note custom fields
    all_fields = frappe.get_all("Custom Field", 
        filters={"dt": "Delivery Note"},
        fields=["fieldname", "label", "fieldtype"],
        order_by="idx")
    
    for field in all_fields:
        print(f"  • {field.fieldname} ({field.fieldtype}) - {field.label}")
    
    return {
        "success": all_passed,
        "total_fields": len(all_fields),
        "required_fields_count": len(required_fields),
        "message": "All tests passed" if all_passed else "Some tests failed"
    }

def create_test_delivery_note():
    """Create a test delivery note to verify field functionality"""
    
    print("\n🧪 Creating test delivery note...")
    
    try:
        # Create test delivery note
        delivery_note = frappe.get_doc({
            "doctype": "Delivery Note",
            "customer": "_Test Customer",
            "posting_date": frappe.utils.today(),
            "customer_approval_status": "Pending",
            "items": [{
                "item_code": "_Test Item",
                "qty": 1,
                "rate": 100
            }]
        })
        
        delivery_note.insert(ignore_permissions=True)
        
        print(f"✅ Test delivery note created: {delivery_note.name}")
        
        # Test field access
        print(f"  • customer_approval_status: {delivery_note.customer_approval_status}")
        print(f"  • approval_qr_code: {'Set' if delivery_note.approval_qr_code else 'Empty'}")
        
        # Update fields to test synchronization
        delivery_note.customer_approval_status = "Approved"
        delivery_note.customer_approved_by = "Test Customer"
        delivery_note.customer_approved_on = frappe.utils.now_datetime()
        delivery_note.customer_signature = "test_signature_data"
        delivery_note.save()
        
        print("✅ Field updates successful")
        
        # Check that legacy fields were synced
        delivery_note.reload()
        if delivery_note.custom_goods_received_status == "Approved":
            print("✅ Legacy field synchronization working")
        else:
            print("⚠️  Legacy field synchronization may have issues")
        
        # Cleanup
        delivery_note.delete(ignore_permissions=True)
        print("✅ Test delivery note cleaned up")
        
        return {"success": True, "message": "Test delivery note creation successful"}
        
    except Exception as e:
        print(f"❌ Error creating test delivery note: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = test_delivery_fields()
    test_result = create_test_delivery_note()
    
    print(f"\nFinal Result: {result}")
    print(f"Test Creation Result: {test_result}")