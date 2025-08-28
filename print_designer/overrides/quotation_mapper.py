"""
Custom mapper override for Quotation to Sales Order
Handles WHT (Withholding Tax) field mapping that is not covered by ERPNext core
"""

import frappe
from frappe import _


def copy_wht_fields_to_sales_order(sales_order_doc, quotation_name):
    """
    Copy WHT fields from Quotation to Sales Order during make_sales_order operation
    
    Args:
        sales_order_doc: Sales Order document being created
        quotation_name: Name of the source Quotation
    """
    try:
        # Get the source quotation
        quotation = frappe.get_cached_doc("Quotation", quotation_name)
        
        # List of WHT fields to copy from Quotation to Sales Order
        wht_fields_to_copy = [
            'wht_income_type',
            'wht_description',
            'net_total_after_wht',
            'net_total_after_wht_in_words',
            'wht_note'
        ]
        
        # Copy each WHT field if it exists in both documents
        for field in wht_fields_to_copy:
            if hasattr(quotation, field) and hasattr(sales_order_doc, field):
                source_value = getattr(quotation, field, None)
                if source_value:  # Only copy non-empty values
                    setattr(sales_order_doc, field, source_value)
                    frappe.logger().info(f"Copied {field}: {source_value} from {quotation_name} to Sales Order")
        
        frappe.logger().info(f"Successfully copied WHT fields from Quotation {quotation_name} to Sales Order")
        
    except Exception as e:
        frappe.log_error(
            message=f"Error copying WHT fields from Quotation {quotation_name}: {str(e)}",
            title="WHT Field Mapping Error"
        )


@frappe.whitelist()
def make_sales_order_with_wht(source_name, target_doc=None):
    """
    Enhanced make_sales_order function that includes WHT field mapping
    This function wraps the ERPNext core make_sales_order and adds WHT field copying
    """
    # Import the original function
    from erpnext.selling.doctype.quotation.quotation import make_sales_order as original_make_sales_order
    
    # Call the original function
    sales_order_doc = original_make_sales_order(source_name, target_doc)
    
    # Copy WHT fields
    copy_wht_fields_to_sales_order(sales_order_doc, source_name)
    
    return sales_order_doc