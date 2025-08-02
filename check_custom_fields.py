#!/usr/bin/env python3

import frappe

def check_custom_fields():
    """Check for existing custom fields that might conflict"""
    frappe.init(site='erpnext-dev-server.bunchee.online')
    frappe.connect()
    
    # Check for authorized_signature_1 field
    existing_fields = frappe.get_all('Custom Field', 
                                   filters={'dt': 'Company', 'fieldname': 'authorized_signature_1'}, 
                                   fields=['name', 'fieldname', 'label', 'creation'])
    
    print("Existing authorized_signature_1 fields:")
    for field in existing_fields:
        print(f"  - {field}")
    
    # Check all Company signature fields
    signature_fields = frappe.get_all('Custom Field', 
                                    filters={'dt': 'Company', 'fieldname': ['like', '%signature%']}, 
                                    fields=['name', 'fieldname', 'label'])
    
    print("\nAll signature-related Company fields:")
    for field in signature_fields:
        print(f"  - {field['fieldname']}: {field['label']}")

if __name__ == '__main__':
    check_custom_fields()