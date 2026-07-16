"""
Thai WHT Helper Utilities

Provides functions to get Thai-specific WHT details from Tax Withholding Category.
Used by Payment Entry, Purchase Invoice, Sales Invoice, etc. for PND form generation.

Architecture:
- Transaction fields use: Tax Withholding Category (bilingual, for GL)
- Reports/PND forms use: Thai WHT Income Type (Thai-specific fields)
- This module bridges the two by looking up Thai WHT Income Type via TWC link
"""

import frappe
from frappe.utils import cstr, flt


def get_thai_wht_details_from_twc(twc_name):
    """
    Get Thai WHT Income Type details from Tax Withholding Category name.
    
    Args:
        twc_name: Tax Withholding Category name (e.g., "WHT 3% Services - Individual (PND3)")
    
    Returns:
        dict with Thai-specific fields:
        {
            'form_type': 'PND3',
            'form_type_th': 'ภงด.3',
            'income_category': 'Advertising Income',
            'income_category_th': 'ค่าโฆษณา',
            'conditions': '...',
            'conditions_th': '...',
            'tax_rate': 2.0,
            'recipient_type': 'Individual',
        }
        Returns None if no linked Thai WHT Income Type found.
    """
    if not twc_name:
        return None
    
    # Method 1: Look up via tax_withholding_category field in Thai WHT Income Type
    thai_wht_name = frappe.db.get_value(
        "Thai WHT Income Type",
        {"tax_withholding_category": twc_name},
        "name"
    )
    
    if thai_wht_name:
        return _get_thai_wht_details(thai_wht_name)
    
    # Method 2: Try matching by similar name (TWC name format: "WHT X% Name - Type (Form)")
    # e.g., "WHT 2% Advertising - Individual (PND3)" → "PND3-Advertising Income"
    return _get_thai_wht_from_twc_name(twc_name)


def _get_thai_wht_details(thai_wht_name):
    """Get Thai WHT details from Thai WHT Income Type document."""
    if not thai_wht_name:
        return None
    
    try:
        doc = frappe.get_cached_doc("Thai WHT Income Type", thai_wht_name)
        return {
            'name': doc.name,
            'form_type': doc.form_type,
            'form_type_th': doc.form_type_th,
            'income_category': doc.income_category,
            'income_category_th': doc.income_category_th,
            'conditions': doc.conditions,
            'conditions_th': doc.conditions_th,
            'income_description': doc.income_description,
            'income_description_th': doc.income_description_th,
            'tax_rate': flt(doc.tax_rate),
            'recipient_type': doc.recipient_type,
            'is_active': doc.is_active,
        }
    except Exception:
        return None


def _get_thai_wht_from_twc_name(twc_name):
    """
    Try to match TWC name to Thai WHT Income Type by parsing name pattern.
    
    TWC name format: "WHT X% Name - Type (Form)"
    Thai WHT Income Type name format: "{form_type}-{income_category}"
    """
    if not twc_name:
        return None
    
    # Parse TWC name
    # Example: "WHT 2% Advertising - Individual (PND3)" → form_type="PND3", income_category="Advertising"
    parts = twc_name.split(" - ")
    if len(parts) >= 2:
        # Last part is the form type in parentheses
        form_part = parts[-1].strip("() ")
        
        # First part contains rate and income category
        # "WHT 2% Advertising Income" → "Advertising Income"
        first_part = parts[0]
        # Remove "WHT X% " prefix
        if first_part.startswith("WHT"):
            income_category = first_part.replace("WHT", "").strip()
            # Remove rate pattern like "2%" or "3%"
            income_category = income_category.lstrip("0123456789.% ").strip()
        
        # Try to find matching Thai WHT Income Type
        # Try different form types and income categories
        form_types = ["PND3", "PND53"]
        for form_type in form_types:
            thai_wht_name = f"{form_type}-{income_category}"
            if frappe.db.exists("Thai WHT Income Type", thai_wht_name):
                return _get_thai_wht_details(thai_wht_name)
    
    return None


def get_wht_rate_from_twc(twc_name, posting_date=None):
    """
    Get WHT rate from Tax Withholding Category.
    
    Args:
        twc_name: Tax Withholding Category name
        posting_date: Optional posting date to get rate for specific fiscal year
    
    Returns:
        float: WHT rate percentage (e.g., 3.0 for 3%)
    """
    if not twc_name:
        return 0.0
    
    try:
        twc = frappe.get_cached_doc("Tax Withholding Category", twc_name)
        
        # Get rate from rates child table
        if hasattr(twc, 'rates') and twc.rates:
            if posting_date:
                # Find rate for specific fiscal year
                for rate_row in twc.rates:
                    if rate_row.from_date and rate_row.to_date:
                        if rate_row.from_date <= posting_date <= rate_row.to_date:
                            return flt(rate_row.rate)
            
            # Default to first rate row
            return flt(twc.rates[0].rate)
        
        # Fallback to tax_rate field if no rates child table
        return flt(getattr(twc, 'tax_rate', 0))
    except Exception:
        return 0.0


def get_twc_from_item(item_code, transaction_type="selling"):
    """
    Get default Tax Withholding Category from Item's standard ERPNext field.
    
    NOTE: ERPNext already handles this automatically via get_item_details() in:
    - erpnext/stock/get_item_details.py -> get_tax_withholding_category()
    This function is kept for backward compatibility.
    
    Args:
        item_code: Item code
        transaction_type: "selling" for sales_tax_withholding_category, "buying" for purchase_tax_withholding_category
    
    Returns:
        str: Tax Withholding Category name or None
    """
    if not item_code:
        return None
    
    field = "sales_tax_withholding_category" if transaction_type == "selling" else "purchase_tax_withholding_category"
    return frappe.get_value("Item", item_code, field)


def format_wht_description(twc_name, lang='th'):
    """
    Format WHT description from TWC name with Thai details.
    
    Args:
        twc_name: Tax Withholding Category name
        lang: 'th' for Thai, 'en' for English
    
    Returns:
        str: Formatted description (e.g., "ค่าโฆษณา (Advertising Income)")
    """
    if not twc_name:
        return ""
    
    thai_details = get_thai_wht_details_from_twc(twc_name)
    if thai_details:
        if lang == 'th':
            return thai_details.get('income_category_th', '') or thai_details.get('income_category', '')
        else:
            return thai_details.get('income_category', '')
    
    # Fallback: parse from TWC name
    parts = twc_name.split(" - ")
    if len(parts) >= 2:
        return parts[0].replace("WHT", "").strip()
    
    return twc_name


@frappe.whitelist()
def get_thai_wht_options(doctype=None):
    """
    Get all Tax Withholding Categories with Thai WHT details.
    Used for dropdown population in client scripts.
    
    Args:
        doctype: Optional doctype filter
    
    Returns:
        list of dict with TWC name and Thai details
    """
    twc_list = frappe.get_all(
        "Tax Withholding Category",
        filters={"disabled": 0},
        fields=["name", "category_name", "tax_rate"],
        order_by="category_name"
    )
    
    result = []
    for twc in twc_list:
        thai_details = get_thai_wht_details_from_twc(twc.name)
        result.append({
            'name': twc.name,
            'category_name': twc.category_name,
            'tax_rate': twc.tax_rate,
            'form_type': thai_details.get('form_type') if thai_details else None,
            'form_type_th': thai_details.get('form_type_th') if thai_details else None,
            'income_category_th': thai_details.get('income_category_th') if thai_details else None,
        })
    
    return result