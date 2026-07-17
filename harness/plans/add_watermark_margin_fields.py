#!/usr/bin/env python3
"""
Patch script to add watermark margin fields to Print Settings for aws-solution site.
Run with: bench --site aws-solution.bunchee.online execute add_watermark_margin_fields.py
"""

import frappe

def add_watermark_margin_fields():
    """Add watermark margin fields to Print Settings DocType"""
    
    # Check if fields already exist
    existing_fields = frappe.db.sql("""
        SELECT fieldname FROM `tabDocField` 
        WHERE parent = 'Print Settings' 
        AND fieldname LIKE 'watermark_margin_%'
    """, pluck='fieldname')
    
    print(f"Existing margin fields: {existing_fields}")
    
    margin_fields = [
        {
            "fieldname": "watermark_margin_top",
            "fieldtype": "Data",
            "label": "Watermark Margin Top",
            "default": "10mm",
            "insert_after": "watermark_margin_left",
        },
        {
            "fieldname": "watermark_margin_bottom",
            "fieldtype": "Data", 
            "label": "Watermark Margin Bottom",
            "default": "10mm",
            "insert_after": "watermark_margin_top",
        },
        {
            "fieldname": "watermark_margin_left",
            "fieldtype": "Data",
            "label": "Watermark Margin Left",
            "default": "10mm",
            "insert_after": "watermark_margin_right",
        },
        {
            "fieldname": "watermark_margin_right",
            "fieldtype": "Data",
            "label": "Watermark Margin Right",
            "default": "10mm",
            "insert_after": "watermark_position",
        },
    ]
    
    for field in margin_fields:
        if field["fieldname"] in existing_fields:
            print(f"Field {field['fieldname']} already exists, skipping")
            continue
            
        # Get max idx
        max_idx = frappe.db.sql("""
            SELECT MAX(idx) FROM `tabDocField` WHERE parent = 'Print Settings'
        """)[0][0] or 0
        
        # Create the field
        docfield = frappe.get_doc({
            "doctype": "DocField",
            "parent": "Print Settings",
            "parentfield": "fields",
            "parenttype": "DocType",
            "fieldname": field["fieldname"],
            "fieldtype": field["fieldtype"],
            "label": field["label"],
            "default": field["default"],
            "insert_after": field["insert_after"],
            "idx": max_idx + 1,
        })
        
        try:
            docfield.insert()
            print(f"Created field: {field['fieldname']}")
        except Exception as e:
            print(f"Error creating {field['fieldname']}: {e}")
    
    # Update Print Settings document with default values
    try:
        ps = frappe.get_single("Print Settings")
        for field in margin_fields:
            if not ps.get(field["fieldname"]):
                ps.set(field["fieldname"], field["default"])
        ps.save()
        print("Updated Print Settings with default margin values")
    except Exception as e:
        print(f"Error updating Print Settings: {e}")
    
    # Clear cache
    frappe.clear_cache()
    print("Cache cleared")

if __name__ == "__main__":
    add_watermark_margin_fields()
