"""
Company Stamp API utilities
"""

import frappe


@frappe.whitelist()
def get_company_stamps(company=None, stamp_type=None, usage_purpose=None):
    """
    Get company stamps with optional filters.
    
    Args:
        company (str): Company name to filter by
        stamp_type (str): Stamp type to filter by  
        usage_purpose (str): Usage purpose to filter by
        
    Returns:
        list: List of company stamps
    """
    filters = {"is_active": 1}
    
    if company:
        filters["company"] = company
    
    if stamp_type:
        filters["stamp_type"] = stamp_type
        
    if usage_purpose:
        filters["usage_purpose"] = usage_purpose
    
    stamps = frappe.get_all("Company Stamp",
        filters=filters,
        fields=[
            "name", "title", "company", "stamp_type", 
            "stamp_image", "usage_purpose", "description"
        ],
        order_by="company, stamp_type"
    )
    
    return stamps


@frappe.whitelist()
def get_default_company_stamp(company, usage_purpose="General"):
    """
    Get the default stamp for a company and usage purpose.
    
    Args:
        company (str): Company name
        usage_purpose (str): Usage purpose (default: "General")
        
    Returns:
        dict: Default company stamp or None
    """
    # First try to find stamp for specific usage purpose
    stamp = frappe.db.get_value("Company Stamp", {
        "company": company,
        "usage_purpose": usage_purpose,
        "is_active": 1
    }, ["name", "stamp_image", "title"], as_dict=True)
    
    if stamp:
        return stamp
    
    # Fallback to "All Documents" usage purpose
    stamp = frappe.db.get_value("Company Stamp", {
        "company": company,
        "usage_purpose": "All Documents",
        "is_active": 1
    }, ["name", "stamp_image", "title"], as_dict=True)
    
    if stamp:
        return stamp
    
    # Final fallback to any active stamp for the company
    stamp = frappe.db.get_value("Company Stamp", {
        "company": company,
        "is_active": 1
    }, ["name", "stamp_image", "title"], as_dict=True, order_by="creation")
    
    return stamp


@frappe.whitelist()
def get_stamp_usage_stats(company=None):
    """
    Get stamp usage statistics.
    
    Args:
        company (str): Company name to filter by
        
    Returns:
        dict: Usage statistics
    """
    filters = {"is_active": 1}
    if company:
        filters["company"] = company
    
    # Get stamp counts by type
    stamp_types = frappe.db.sql("""
        SELECT stamp_type, COUNT(*) as count
        FROM `tabCompany Stamp`
        WHERE is_active = 1 {company_filter}
        GROUP BY stamp_type
        ORDER BY count DESC
    """.format(
        company_filter="AND company = %(company)s" if company else ""
    ), {"company": company}, as_dict=True)
    
    # Get total active stamps
    total_stamps = frappe.db.count("Company Stamp", filters)
    
    # Get companies with stamps
    companies = frappe.db.sql("""
        SELECT company, COUNT(*) as stamp_count
        FROM `tabCompany Stamp`
        WHERE is_active = 1 {company_filter}
        GROUP BY company
        ORDER BY stamp_count DESC
    """.format(
        company_filter="AND company = %(company)s" if company else ""
    ), {"company": company}, as_dict=True)
    
    return {
        "total_stamps": total_stamps,
        "stamp_types": stamp_types,
        "companies": companies
    }