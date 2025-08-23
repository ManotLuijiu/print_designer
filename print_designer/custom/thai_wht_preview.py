"""
Thai Withholding Tax Preview System for Sales Cycle
=================================================

This system provides WHT preview calculations for Quotation, Sales Order, and Sales Invoice
WITHOUT interfering with ERPNext's payment-time WHT system.

Key Features:
- Preview-only calculations (no GL entries)
- Thai-specific WHT rates and rules
- Customer notification of WHT deductions
- Integration with print formats for billing (วางบิล)
- Seamless handoff to ERPNext's payment WHT system

Design Principles:
1. PREVIEW ONLY - No accounting impact until payment
2. COMPLEMENTARY - Works alongside ERPNext's WHT system  
3. THAI-SPECIFIC - Focused on Thai tax regulations
4. CUSTOMER-FACING - Clear communication about WHT deductions
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate
import json
from datetime import datetime


# ==================================================
# THAI WHT RATE CONFIGURATION
# ==================================================

THAI_WHT_RATES = {
    # Income Type 1: Professional Services (บริการวิชาชีพ)
    'professional_services': {
        'rate': 3.0,
        'description': 'บริการวิชาชีพ (Professional Services)',
        'pnd_form': 'PND3',
        'income_type': 1
    },
    
    # Income Type 2: Rental/Lease (ค่าเช่า)
    'rental': {
        'rate': 5.0,
        'description': 'ค่าเช่าทรัพย์สิน (Property Rental)',
        'pnd_form': 'PND3',
        'income_type': 2
    },
    
    # Income Type 3: Service Fees (ค่าบริการ)
    'service_fees': {
        'rate': 3.0,
        'description': 'ค่าบริการ (Service Fees)',
        'pnd_form': 'PND3',
        'income_type': 3
    },
    
    # Income Type 4: Construction/Contracting (ค่าก่อสร้าง)
    'construction': {
        'rate': 2.0,
        'description': 'ค่าก่อสร้าง (Construction Services)',
        'pnd_form': 'PND3',
        'income_type': 4
    },
    
    # Income Type 5: Advertising (ค่าโฆษณา)
    'advertising': {
        'rate': 2.0,
        'description': 'ค่าโฆษณา (Advertising Services)',
        'pnd_form': 'PND3',
        'income_type': 5
    },
    
    # Default rate for unspecified services
    'other_services': {
        'rate': 1.0,
        'description': 'บริการอื่นๆ (Other Services)',
        'pnd_form': 'PND3',
        'income_type': 99
    }
}

# WHT Exemption threshold (minimum amount subject to WHT)
THAI_WHT_THRESHOLD = 1000.0  # 1,000 THB minimum per transaction


# ==================================================
# WHT PREVIEW CALCULATION FUNCTIONS
# ==================================================

def calculate_thai_wht_preview(doc):
    """
    Calculate Thai WHT preview for sales documents
    
    Args:
        doc: Quotation, Sales Order, or Sales Invoice document
        
    Returns:
        dict: WHT preview information
    """
    if not should_calculate_wht_preview(doc):
        return clear_wht_preview_fields(doc)
    
    # Get customer's WHT configuration
    customer_wht_config = get_customer_wht_config(doc.customer)
    
    if not customer_wht_config.get('subject_to_wht'):
        return clear_wht_preview_fields(doc)
    
    # Calculate base amount for WHT
    base_amount = get_wht_base_amount(doc)
    
    if base_amount < THAI_WHT_THRESHOLD:
        return clear_wht_preview_fields(doc)
    
    # Get applicable WHT rate
    wht_rate = get_applicable_wht_rate(doc, customer_wht_config)
    
    # Calculate WHT amount
    wht_amount = (base_amount * wht_rate) / 100
    
    # Calculate net payment amount (after WHT deduction)
    net_payment_amount = doc.grand_total - wht_amount
    
    # Update WHT preview fields
    wht_preview = {
        'subject_to_wht': 1,
        'estimated_wht_rate': wht_rate,
        'estimated_wht_amount': flt(wht_amount, 2),
        'wht_base_amount': flt(base_amount, 2),
        'net_payment_amount': flt(net_payment_amount, 2),
        'wht_income_type': customer_wht_config.get('income_type', 'service_fees'),
        'wht_description': get_wht_description(customer_wht_config.get('income_type', 'service_fees'))
    }
    
    return wht_preview


def should_calculate_wht_preview(doc):
    """Check if WHT preview should be calculated"""
    # Only for Thai companies
    if not is_thai_company(doc.company):
        return False
    
    # Only for customers with Thai tax setup
    if not doc.customer:
        return False
    
    # Skip if document is cancelled or draft with no amount
    if not doc.grand_total or doc.grand_total <= 0:
        return False
    
    return True


def get_customer_wht_config(customer):
    """Get customer's WHT configuration"""
    if not customer:
        return {}
    
    try:
        # Check if customer has WHT configuration
        customer_doc = frappe.get_cached_doc("Customer", customer)
        
        config = {
            'subject_to_wht': getattr(customer_doc, 'subject_to_wht', False),
            'wht_rate': getattr(customer_doc, 'wht_rate', 0),
            'income_type': getattr(customer_doc, 'income_type', 'service_fees'),
            'tax_id': getattr(customer_doc, 'tax_id', ''),
            'is_juristic_person': getattr(customer_doc, 'is_juristic_person', True)
        }
        
        return config
        
    except Exception as e:
        frappe.log_error(f"Error getting customer WHT config for {customer}: {str(e)}")
        return {}


def get_wht_base_amount(doc):
    """Calculate base amount for WHT calculation"""
    # For Thai WHT, typically calculated on net total (before VAT)
    # but depends on the type of service
    
    base_amount = flt(doc.net_total) or flt(doc.grand_total)
    
    # If VAT is included, use net total
    if hasattr(doc, 'total_taxes_and_charges') and doc.total_taxes_and_charges:
        base_amount = flt(doc.net_total)
    
    return base_amount


def get_applicable_wht_rate(doc, customer_config):
    """Get applicable WHT rate based on income type and customer setup"""
    
    # Use customer-specific rate if configured
    if customer_config.get('wht_rate'):
        return flt(customer_config.get('wht_rate'))
    
    # Use income type-based rate
    income_type = customer_config.get('income_type', 'service_fees')
    
    if income_type in THAI_WHT_RATES:
        return THAI_WHT_RATES[income_type]['rate']
    
    # Default to service fees rate
    return THAI_WHT_RATES['service_fees']['rate']


def get_wht_description(income_type):
    """Get WHT description for income type"""
    if income_type in THAI_WHT_RATES:
        return THAI_WHT_RATES[income_type]['description']
    
    return THAI_WHT_RATES['service_fees']['description']


def clear_wht_preview_fields(doc):
    """Clear WHT preview fields"""
    return {
        'subject_to_wht': 0,
        'estimated_wht_rate': 0,
        'estimated_wht_amount': 0,
        'wht_base_amount': 0,
        'net_payment_amount': flt(doc.grand_total, 2),
        'wht_income_type': '',
        'wht_description': ''
    }


def is_thai_company(company):
    """Check if company is Thai company"""
    try:
        company_doc = frappe.get_cached_doc("Company", company)
        country = getattr(company_doc, 'country', '')
        return country.lower() in ['thailand', 'ประเทศไทย', 'ไทย']
    except:
        return True  # Default to True for existing companies


# ==================================================
# DOCUMENT EVENT HANDLERS
# ==================================================

def sales_document_validate(doc, method=None):
    """
    Calculate WHT preview on sales document validation
    Called for Quotation, Sales Order, and Sales Invoice
    """
    try:
        wht_preview = calculate_thai_wht_preview(doc)
        
        # Update document fields
        for field, value in wht_preview.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
                
    except Exception as e:
        frappe.log_error(
            f"Error calculating WHT preview for {doc.doctype} {doc.name}: {str(e)}",
            "Thai WHT Preview Error"
        )
        # Don't fail validation if preview calculation fails


# ==================================================
# API ENDPOINTS
# ==================================================

@frappe.whitelist()
def get_wht_preview_info(doctype, docname):
    """API to get WHT preview information for a document"""
    try:
        doc = frappe.get_doc(doctype, docname)
        wht_preview = calculate_thai_wht_preview(doc)
        
        return {
            'success': True,
            'wht_preview': wht_preview,
            'available_income_types': THAI_WHT_RATES
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@frappe.whitelist()
def get_thai_wht_rates():
    """API to get available Thai WHT rates"""
    return THAI_WHT_RATES


@frappe.whitelist()
def preview_wht_calculation(customer, grand_total, income_type=None):
    """
    Preview WHT calculation for given parameters
    
    Args:
        customer: Customer name
        grand_total: Invoice grand total
        income_type: Optional income type override
    """
    try:
        # Create temporary doc-like object for calculation
        temp_doc = frappe._dict({
            'customer': customer,
            'grand_total': flt(grand_total),
            'net_total': flt(grand_total),  # Simplified for preview
            'company': frappe.defaults.get_user_default('Company')
        })
        
        # Override income type if provided
        customer_config = get_customer_wht_config(customer)
        if income_type:
            customer_config['income_type'] = income_type
        
        if not customer_config.get('subject_to_wht'):
            return {
                'subject_to_wht': False,
                'message': 'Customer is not subject to WHT'
            }
        
        wht_preview = calculate_thai_wht_preview(temp_doc)
        wht_preview['success'] = True
        
        return wht_preview
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ==================================================
# PRINT FORMAT HELPERS
# ==================================================

def get_wht_info_for_print(doc):
    """
    Get WHT information formatted for print templates
    Used in print formats to show WHT details to customers
    """
    try:
        if not hasattr(doc, 'subject_to_wht') or not doc.subject_to_wht:
            return None
        
        return {
            'show_wht': True,
            'wht_rate': flt(doc.estimated_wht_rate, 2),
            'wht_amount': flt(doc.estimated_wht_amount, 2),
            'wht_description': getattr(doc, 'wht_description', ''),
            'base_amount': flt(doc.wht_base_amount, 2),
            'net_payment': flt(doc.net_payment_amount, 2),
            'wht_note': _('หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน'),
            'wht_note_en': _('Note: Withholding tax amount will be deducted upon payment')
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting WHT info for print: {str(e)}")
        return None