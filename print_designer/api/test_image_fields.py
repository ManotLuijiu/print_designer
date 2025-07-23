import frappe


@frappe.whitelist()
def test_image_fields():
    """Test function to check if signature fields appear in Dynamic Images"""
    try:
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        
        # Get all image fields
        image_fields = get_image_docfields()
        
        # Filter signature fields
        signature_fields = [
            f for f in image_fields 
            if 'signature' in f.get('fieldname', '').lower()
        ]
        
        return {
            "success": True,
            "total_image_fields": len(image_fields),
            "signature_fields_count": len(signature_fields),
            "signature_fields": signature_fields[:10],  # First 10
            "sample_image_fields": image_fields[:5],  # First 5 for debugging
        }
        
    except Exception as e:
        frappe.log_error(f"Error testing image fields: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def test_custom_fields():
    """Test to check if signature custom fields are properly installed"""
    try:
        # Check Company signature fields
        company_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Company", "fieldtype": "Attach Image"},
            fields=["fieldname", "label", "fieldtype"]
        )
        
        # Check User signature fields
        user_fields = frappe.get_all(
            "Custom Field", 
            filters={"dt": "User", "fieldtype": "Attach Image"},
            fields=["fieldname", "label", "fieldtype"]
        )
        
        # Check Employee signature fields
        employee_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Employee", "fieldtype": "Attach Image"}, 
            fields=["fieldname", "label", "fieldtype"]
        )
        
        return {
            "success": True,
            "company_signature_fields": company_fields,
            "user_signature_fields": user_fields,
            "employee_signature_fields": employee_fields,
            "total_custom_signature_fields": len(company_fields) + len(user_fields) + len(employee_fields)
        }
        
    except Exception as e:
        frappe.log_error(f"Error testing custom fields: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def check_approved_by_signature():
    """Check if approved_by_signature fields are installed for transaction DocTypes"""
    try:
        # Check Sales Invoice approved_by_signature field
        sales_invoice_fields = frappe.get_all(
            'Custom Field',
            filters={'dt': 'Sales Invoice', 'fieldname': 'approved_by_signature'},
            fields=['fieldname', 'label', 'fieldtype', 'dt']
        )
        
        # Check Purchase Invoice approved_by_signature field  
        purchase_invoice_fields = frappe.get_all(
            'Custom Field',
            filters={'dt': 'Purchase Invoice', 'fieldname': 'approved_by_signature'},
            fields=['fieldname', 'label', 'fieldtype', 'dt']
        )
        
        # Check all signature fields in Sales Invoice
        all_sales_sigs = frappe.get_all(
            'Custom Field',
            filters={'dt': 'Sales Invoice', 'fieldtype': 'Attach Image'},
            fields=['fieldname', 'label', 'fieldtype']
        )
        
        # Check all signature fields in Purchase Invoice
        all_purchase_sigs = frappe.get_all(
            'Custom Field',
            filters={'dt': 'Purchase Invoice', 'fieldtype': 'Attach Image'},
            fields=['fieldname', 'label', 'fieldtype']
        )
        
        # Check Sales Order signature fields
        sales_order_sigs = frappe.get_all(
            'Custom Field',
            filters={'dt': 'Sales Order', 'fieldtype': 'Attach Image'},
            fields=['fieldname', 'label', 'fieldtype']
        )
        
        return {
            "success": True,
            "sales_invoice_approved_by": sales_invoice_fields,
            "purchase_invoice_approved_by": purchase_invoice_fields,
            "all_sales_invoice_signatures": all_sales_sigs,
            "all_purchase_invoice_signatures": all_purchase_sigs,
            "all_sales_order_signatures": sales_order_sigs,
            "summary": {
                "sales_invoice_total": len(all_sales_sigs),
                "purchase_invoice_total": len(all_purchase_sigs),
                "sales_order_total": len(sales_order_sigs)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error checking approved_by_signature: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def check_specific_signature_in_api():
    """Check if approved_by_signature fields appear in get_image_docfields API"""
    try:
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        
        # Get all image fields from API
        image_fields = get_image_docfields()
        
        # Filter for approved_by_signature specifically
        approved_by_fields = [
            f for f in image_fields 
            if f.get('fieldname') == 'approved_by_signature'
        ]
        
        # Filter for prepared_by_signature
        prepared_by_fields = [
            f for f in image_fields 
            if f.get('fieldname') == 'prepared_by_signature'
        ]
        
        # Check Sales Invoice and Purchase Invoice specifically
        sales_invoice_fields = [
            f for f in image_fields 
            if f.get('parent') == 'Sales Invoice'
        ]
        
        purchase_invoice_fields = [
            f for f in image_fields 
            if f.get('parent') == 'Purchase Invoice'
        ]
        
        return {
            "success": True,
            "total_image_fields": len(image_fields),
            "approved_by_signature_fields": approved_by_fields,
            "prepared_by_signature_fields": prepared_by_fields,
            "sales_invoice_image_fields": sales_invoice_fields,
            "purchase_invoice_image_fields": purchase_invoice_fields,
            "summary": {
                "approved_by_count": len(approved_by_fields),
                "prepared_by_count": len(prepared_by_fields),
                "sales_invoice_count": len(sales_invoice_fields),
                "purchase_invoice_count": len(purchase_invoice_fields)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error checking specific signature in API: {str(e)}")
        return {"error": str(e)}