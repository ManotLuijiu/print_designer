"""
Thai Withholding Tax Management System for Print Designer
Handles WHT calculations, certificate generation, and compliance reporting
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate, add_days, format_date
from frappe.model.document import Document
import json
from datetime import datetime


# ==================================================
# MAIN WHT CALCULATION FUNCTIONS
# ==================================================

@frappe.whitelist()
def calculate_withholding_tax(doc, method=None):
    """
    Calculate withholding tax for Payment Entry and Purchase Invoice
    Enhanced to work with both DocTypes
    """
    if hasattr(doc, 'custom_is_withholding_tax') and doc.custom_is_withholding_tax:
        if not doc.custom_withholding_tax_rate:
            return
            
        # Get base amount based on DocType
        base_amount = get_base_amount_for_wht(doc)
        
        if not base_amount:
            return
            
        # Calculate withholding tax amount
        wht_rate = flt(doc.custom_withholding_tax_rate)
        wht_amount = (base_amount * wht_rate) / 100
        
        # Update withholding tax amount
        doc.custom_withholding_tax_amount = flt(wht_amount, 2)
        
        # Handle DocType-specific updates
        if doc.doctype == "Purchase Invoice":
            # Adjust outstanding amount (net payable after WHT)
            doc.outstanding_amount = base_amount - wht_amount
            
            # Get supplier tax ID if not set
            if not doc.custom_supplier_tax_id and doc.supplier:
                supplier_tax_id = frappe.db.get_value("Supplier", doc.supplier, "tax_id")
                if supplier_tax_id:
                    doc.custom_supplier_tax_id = supplier_tax_id
                    
        elif doc.doctype == "Payment Entry":
            # Generate certificate number if not exists
            if not doc.custom_wht_certificate_number:
                doc.custom_wht_certificate_number = generate_certificate_number(doc)


def get_base_amount_for_wht(doc):
    """
    Get base amount for WHT calculation based on DocType
    """
    if doc.doctype == "Purchase Invoice":
        return flt(doc.grand_total)
    elif doc.doctype == "Payment Entry":
        if doc.payment_type == "Pay":
            return flt(doc.paid_amount)
        else:
            return flt(doc.received_amount)
    return 0


def generate_certificate_number(doc):
    """
    Generate Thai WHT certificate number in format: WHT-YYYY-MM-NNNN
    """
    now = datetime.now()
    prefix = f"WHT-{now.year}-{now.month:02d}-"
    
    # Get next sequence number for this month
    last_cert = frappe.db.sql("""
        SELECT custom_wht_certificate_number 
        FROM `tab{}` 
        WHERE custom_wht_certificate_number LIKE %s 
        ORDER BY custom_wht_certificate_number DESC 
        LIMIT 1
    """.format(doc.doctype), f"{prefix}%")
    
    if last_cert and last_cert[0][0]:
        try:
            last_number = int(last_cert[0][0].split('-')[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
        
    return f"{prefix}{next_number:04d}"


# ==================================================
# WHT CERTIFICATE DATA FUNCTIONS
# ==================================================

@frappe.whitelist()
def get_wht_certificate_data(document_name, doctype="Payment Entry"):
    """
    Get data for WHT certificate generation (supports both Payment Entry and Purchase Invoice)
    """
    try:
        doc = frappe.get_doc(doctype, document_name)
        
        # Get company details
        company = frappe.get_doc("Company", doc.company)
        
        # Get party details (supplier for both DocTypes)
        if doctype == "Purchase Invoice":
            party = frappe.get_doc("Supplier", doc.supplier)
            party_name = party.supplier_name
            party_address = party.supplier_address or ""
            party_tax_id = doc.custom_supplier_tax_id or party.tax_id or ""
        else:  # Payment Entry
            if doc.party_type == "Supplier":
                party = frappe.get_doc("Supplier", doc.party)
                party_name = party.supplier_name
                party_address = party.supplier_address or ""
                party_tax_id = doc.custom_supplier_tax_id or party.tax_id or ""
            else:
                frappe.throw(_("WHT certificates can only be generated for supplier payments"))
        
        # Prepare certificate data
        certificate_data = {
            "document": doc,
            "company": company,
            "party": party,
            "payer_name": company.company_name,
            "payer_address": get_company_address(company),
            "payer_tax_id": company.tax_id or "",
            "payee_name": party_name,
            "payee_address": party_address,
            "payee_tax_id": party_tax_id,
            "tax_details": get_tax_breakdown(doc),
            "certificate_date": getdate(doc.posting_date if hasattr(doc, 'posting_date') else doc.reference_date),
            "certificate_number": doc.custom_wht_certificate_number or generate_certificate_number(doc),
            "total_amount": get_base_amount_for_wht(doc),
            "wht_amount": doc.custom_withholding_tax_amount,
            "wht_rate": doc.custom_withholding_tax_rate,
            "income_type": determine_income_type(doc),
            "tax_year": getdate().year,
            "payment_method": get_payment_method(doc),
            "thai_date": convert_to_thai_date(getdate(doc.posting_date if hasattr(doc, 'posting_date') else doc.reference_date))
        }
        
        return certificate_data
        
    except Exception as e:
        frappe.log_error(f"Error getting WHT certificate data: {str(e)}")
        frappe.throw(_("Error retrieving certificate data: {}").format(str(e)))


def get_company_address(company):
    """
    Get formatted company address
    """
    address_fields = []
    
    if company.company_address:
        address_fields.append(company.company_address)
    
    # Try to get from Address doctype
    address_name = frappe.db.get_value("Dynamic Link", {
        "link_doctype": "Company",
        "link_name": company.name,
        "parenttype": "Address"
    }, "parent")
    
    if address_name:
        address = frappe.get_doc("Address", address_name)
        address_parts = [
            address.address_line1,
            address.address_line2,
            address.city,
            address.state,
            address.pincode,
            address.country
        ]
        address_str = ", ".join([part for part in address_parts if part])
        if address_str:
            return address_str
    
    return company.company_address or ""


def get_tax_breakdown(doc):
    """
    Get tax breakdown for WHT certificate
    """
    tax_details = []
    
    if doc.custom_is_withholding_tax:
        income_type = determine_income_type(doc)
        
        tax_detail = {
            "sequence": 1,
            "income_type": income_type,
            "income_type_code": get_income_type_code(income_type),
            "amount_paid": flt(get_base_amount_for_wht(doc)),
            "tax_rate": flt(doc.custom_withholding_tax_rate),
            "tax_withheld": flt(doc.custom_withholding_tax_amount),
            "tax_submitted": flt(doc.custom_withholding_tax_amount),  # Assume submitted same as withheld
            "period": get_tax_period(doc),
            "description": get_service_description(doc)
        }
        tax_details.append(tax_detail)
    
    return tax_details


def determine_income_type(doc):
    """
    Determine Thai income type for WHT certificate with enhanced logic
    """
    # Enhanced income types mapping with Thai descriptions
    income_types = {
        "professional": "ค่าธรรมเนียมวิชาชีพ ตามมาตรา 40(2)",
        "service": "ค่าธรรมเนียม ค่านายหน้า ฯลฯ ตามมาตรา 40(2)", 
        "consulting": "ค่าที่ปรึกษา ตามมาตรา 40(2)",
        "rental": "ค่าเช่าทรัพย์สิน ตามมาตรา 40(5)",
        "transportation": "ค่าขนส่ง ตามมาตรา 40(6)",
        "advertising": "ค่าโฆษณา ตามมาตรา 40(7)",
        "royalty": "ค่าลิขสิทธิ์ ตามมาตรา 40(3)",
        "construction": "ค่าก่อสร้าง ตามมาตรา 3 เตรส",
        "other": "การจ่ายเงินได้อื่นๆ ที่ต้องหักภาษี ณ ที่จ่าย"
    }
    
    # Try to determine from various sources
    if doc.doctype == "Purchase Invoice":
        # Check items for service type
        for item in doc.items:
            item_group = frappe.db.get_value("Item", item.item_code, "item_group")
            if item_group:
                detected_type = match_income_type(item_group.lower(), income_types)
                if detected_type:
                    return detected_type
            
            # Check item description
            if item.description:
                detected_type = match_income_type(item.description.lower(), income_types)
                if detected_type:
                    return detected_type
    
    elif doc.doctype == "Payment Entry":
        # Check payment references
        for ref in doc.references:
            if ref.reference_doctype == "Purchase Invoice":
                pi = frappe.get_doc("Purchase Invoice", ref.reference_name)
                if hasattr(pi, 'custom_is_withholding_tax') and pi.custom_is_withholding_tax:
                    return determine_income_type(pi)
    
    # Check supplier group or type
    if hasattr(doc, 'supplier') and doc.supplier:
        supplier_group = frappe.db.get_value("Supplier", doc.supplier, "supplier_group")
        if supplier_group:
            detected_type = match_income_type(supplier_group.lower(), income_types)
            if detected_type:
                return detected_type
    
    # Check custom field for income type if exists
    if hasattr(doc, 'custom_income_type') and doc.custom_income_type:
        return doc.custom_income_type
    
    # Default to service type
    return income_types["service"]


def match_income_type(text, income_types):
    """
    Match text against income type keywords
    """
    for key, thai_type in income_types.items():
        keywords = key.split('_')
        if any(keyword in text for keyword in keywords):
            return thai_type
    return None


def get_income_type_code(income_type):
    """
    Get numeric code for income type (for government reporting)
    """
    codes = {
        "ค่าธรรมเนียมวิชาชีพ": "01",
        "ค่าธรรมเนียม ค่านายหน้า": "02",
        "ค่าที่ปรึกษา": "02",
        "ค่าเช่าทรัพย์สิน": "05",
        "ค่าขนส่ง": "06", 
        "ค่าโฆษณา": "07",
        "ค่าลิขสิทธิ์": "03",
        "ค่าก่อสร้าง": "08",
    }
    
    for desc, code in codes.items():
        if desc in income_type:
            return code
    
    return "99"  # Other


def get_payment_method(doc):
    """
    Get payment method description
    """
    if doc.doctype == "Payment Entry":
        return doc.mode_of_payment or "เงินสด"
    return "เงินสด"  # Cash default


def get_service_description(doc):
    """
    Get service description for certificate
    """
    if doc.doctype == "Purchase Invoice":
        if doc.items:
            descriptions = [item.description or item.item_name for item in doc.items[:3]]  # First 3 items
            return ", ".join(descriptions)
    elif doc.doctype == "Payment Entry":
        return doc.remarks or "บริการต่างๆ"
    
    return "บริการต่างๆ"  # Various services


def get_tax_period(doc):
    """
    Get tax period for certificate
    """
    date = getdate(doc.posting_date if hasattr(doc, 'posting_date') else doc.reference_date)
    return f"{date.month:02d}/{date.year}"


def convert_to_thai_date(date):
    """
    Convert Gregorian date to Thai Buddhist calendar
    """
    if not date:
        return ""
    
    thai_months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    
    if isinstance(date, str):
        date = getdate(date)
    
    thai_year = date.year + 543
    thai_month = thai_months[date.month - 1]
    
    return f"{date.day} {thai_month} พ.ศ. {thai_year}"


# ==================================================
# JOURNAL ENTRY AND ACCOUNTING INTEGRATION
# ==================================================

@frappe.whitelist()
def create_wht_journal_entry(document_name, doctype="Payment Entry"):
    """
    Create journal entry for withholding tax (enhanced for both DocTypes)
    """
    try:
        doc = frappe.get_doc(doctype, document_name)
        
        if not doc.custom_is_withholding_tax or not doc.custom_withholding_tax_amount:
            frappe.throw(_("No withholding tax to process"))
        
        # Check if JE already exists
        existing_je = frappe.db.exists("Journal Entry", {
            "reference_type": doctype,
            "reference_name": document_name,
            "user_remark": ["like", "%WHT%"]
        })
        
        if existing_je:
            frappe.msgprint(_("Journal Entry already exists: {0}").format(existing_je))
            return existing_je
        
        # Create Journal Entry
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Journal Entry"
        je.posting_date = doc.posting_date if hasattr(doc, 'posting_date') else doc.reference_date
        je.company = doc.company
        je.remark = f"Withholding Tax for {doc.name}"
        je.user_remark = f"WHT {doc.custom_withholding_tax_rate}% - {doctype}"
        
        # Get accounts
        wht_payable_account = get_wht_payable_account(doc.company)
        
        if doctype == "Purchase Invoice":
            supplier_account = get_supplier_account(doc.supplier, doc.company)
            party_type = "Supplier"
            party = doc.supplier
        else:  # Payment Entry
            supplier_account = get_supplier_account(doc.party, doc.company)
            party_type = doc.party_type
            party = doc.party
        
        # Credit WHT Payable (Government Liability)
        je.append("accounts", {
            "account": wht_payable_account,
            "credit_in_account_currency": doc.custom_withholding_tax_amount,
            "party_type": "",
            "party": "",
            "reference_type": doctype,
            "reference_name": doc.name,
            "user_remark": "WHT Liability to Government"
        })
        
        # Debit Supplier Account (Reduce supplier liability)
        je.append("accounts", {
            "account": supplier_account,
            "debit_in_account_currency": doc.custom_withholding_tax_amount,
            "party_type": party_type,
            "party": party,
            "reference_type": doctype, 
            "reference_name": doc.name,
            "user_remark": "Supplier WHT Deduction"
        })
        
        je.save()
        je.submit()
        
        frappe.msgprint(_("Journal Entry {0} created and submitted for Withholding Tax").format(je.name))
        
        return je.name
        
    except Exception as e:
        frappe.log_error(f"Error creating WHT journal entry: {str(e)}")
        frappe.throw(_("Error creating journal entry: {}").format(str(e)))


def get_wht_payable_account(company):
    """
    Get or create WHT payable account for company
    """
    company_abbr = frappe.db.get_value('Company', company, 'abbr')
    account_name = f"Withholding Tax Payable - {company_abbr}"
    
    if frappe.db.exists("Account", account_name):
        return account_name
    
    # Create WHT payable account
    try:
        parent_account = get_parent_liability_account(company)
        
        account = frappe.new_doc("Account")
        account.account_name = "Withholding Tax Payable"
        account.parent_account = parent_account
        account.account_type = "Payable"
        account.company = company
        account.is_group = 0
        account.account_number = "2190"  # Standard WHT liability account number
        account.insert()
        
        frappe.msgprint(_("Created WHT Payable Account: {0}").format(account.name))
        return account.name
        
    except Exception as e:
        frappe.log_error(f"Error creating WHT account: {str(e)}")
        # Fallback to default payable account
        return frappe.db.get_value("Company", company, "default_payable_account")


def get_parent_liability_account(company):
    """
    Get appropriate parent liability account for company
    """
    # Look for "Current Liabilities" or similar
    liability_accounts = frappe.db.sql("""
        SELECT name FROM `tabAccount` 
        WHERE company = %s 
        AND is_group = 1 
        AND (root_type = 'Liability' OR account_type = 'Payable')
        AND (account_name LIKE '%Current%' OR account_name LIKE '%Liability%')
        ORDER BY lft
        LIMIT 1
    """, company)
    
    if liability_accounts:
        return liability_accounts[0][0]
    
    # Fallback to any liability group account
    return frappe.db.get_value("Account", {
        "company": company,
        "is_group": 1,
        "root_type": "Liability"
    }, "name")


def get_supplier_account(supplier, company):
    """
    Get supplier's creditors account
    """
    # First try supplier's default account
    supplier_account = frappe.db.get_value("Supplier", supplier, "default_account")
    
    if supplier_account:
        return supplier_account
    
    # Get default creditors account from company
    default_payable = frappe.db.get_value("Company", company, "default_payable_account")
    if default_payable:
        return default_payable
    
    # Last resort - find any creditors account
    creditors_account = frappe.db.get_value("Account", {
        "company": company,
        "account_type": "Payable",
        "is_group": 0
    }, "name")
    
    return creditors_account


# ==================================================
# REPORTING AND ANALYTICS FUNCTIONS
# ==================================================

@frappe.whitelist()
def get_wht_summary_report(from_date, to_date, company=None, supplier=None):
    """
    Get comprehensive WHT summary report for a period
    """
    try:
        # Base filters
        filters = {
            "custom_is_withholding_tax": 1,
            "docstatus": 1
        }
        
        # Date filter
        date_field = "posting_date"
        filters[date_field] = ["between", [from_date, to_date]]
        
        if company:
            filters["company"] = company
        
        if supplier:
            filters["supplier"] = supplier
        
        # Get data from both Payment Entry and Purchase Invoice
        payment_entries = frappe.get_all("Payment Entry", 
            filters=dict(filters, **{"party_type": "Supplier"}),
            fields=[
                "name", "reference_date as posting_date", "party as supplier", "party_name as supplier_name", 
                "paid_amount as grand_total", "custom_withholding_tax_rate", 
                "custom_withholding_tax_amount", "custom_supplier_tax_id", "custom_wht_certificate_number",
                "'Payment Entry' as doctype"
            ]
        )
        
        purchase_invoices = frappe.get_all("Purchase Invoice", 
            filters=filters,
            fields=[
                "name", "posting_date", "supplier", "supplier_name", 
                "grand_total", "custom_withholding_tax_rate", 
                "custom_withholding_tax_amount", "custom_supplier_tax_id", "custom_wht_certificate_number",
                "'Purchase Invoice' as doctype"
            ]
        )
        
        # Combine results
        all_documents = payment_entries + purchase_invoices
        
        # Calculate summaries
        total_base_amount = 0
        total_wht_amount = 0
        supplier_summary = {}
        rate_summary = {}
        
        for doc in all_documents:
            base_amount = flt(doc.grand_total)
            wht_amount = flt(doc.custom_withholding_tax_amount)
            rate = flt(doc.custom_withholding_tax_rate)
            supplier_name = doc.supplier_name or doc.supplier
            
            total_base_amount += base_amount
            total_wht_amount += wht_amount
            
            # Supplier summary
            if supplier_name not in supplier_summary:
                supplier_summary[supplier_name] = {"count": 0, "base_amount": 0, "wht_amount": 0}
            supplier_summary[supplier_name]["count"] += 1
            supplier_summary[supplier_name]["base_amount"] += base_amount
            supplier_summary[supplier_name]["wht_amount"] += wht_amount
            
            # Rate summary
            rate_key = f"{rate}%"
            if rate_key not in rate_summary:
                rate_summary[rate_key] = {"count": 0, "base_amount": 0, "wht_amount": 0}
            rate_summary[rate_key]["count"] += 1
            rate_summary[rate_key]["base_amount"] += base_amount
            rate_summary[rate_key]["wht_amount"] += wht_amount
        
        return {
            "documents": all_documents,
            "summary": {
                "total_documents": len(all_documents),
                "total_base_amount": total_base_amount,
                "total_wht_amount": total_wht_amount,
                "average_wht_rate": (total_wht_amount / total_base_amount * 100) if total_base_amount else 0,
                "period": f"{format_date(from_date)} to {format_date(to_date)}"
            },
            "supplier_summary": supplier_summary,
            "rate_summary": rate_summary
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating WHT report: {str(e)}")
        frappe.throw(_("Error generating report: {}").format(str(e)))


@frappe.whitelist()
def get_wht_tax_filing_data(tax_year, company):
    """
    Get data for annual WHT tax filing (PND forms)
    """
    try:
        year_start = f"{tax_year}-01-01"
        year_end = f"{tax_year}-12-31"
        
        # Get all WHT transactions for the year
        report_data = get_wht_summary_report(year_start, year_end, company)
        
        # Group by income type for PND filing
        income_type_summary = {}
        
        for doc in report_data["documents"]:
            doc_obj = frappe.get_doc(doc["doctype"], doc["name"])
            income_type = determine_income_type(doc_obj)
            
            if income_type not in income_type_summary:
                income_type_summary[income_type] = {
                    "count": 0,
                    "total_payments": 0,
                    "total_wht": 0,
                    "documents": []
                }
            
            income_type_summary[income_type]["count"] += 1
            income_type_summary[income_type]["total_payments"] += flt(doc["grand_total"])
            income_type_summary[income_type]["total_wht"] += flt(doc["custom_withholding_tax_amount"])
            income_type_summary[income_type]["documents"].append(doc)
        
        return {
            "tax_year": tax_year,
            "company": company,
            "summary": report_data["summary"],
            "income_type_breakdown": income_type_summary,
            "filing_requirements": get_filing_requirements(income_type_summary)
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating tax filing data: {str(e)}")
        frappe.throw(_("Error generating tax filing data: {}").format(str(e)))


def get_filing_requirements(income_type_summary):
    """
    Get filing requirements based on income types
    """
    requirements = []
    
    for income_type, data in income_type_summary.items():
        total_wht = data["total_wht"]
        
        # Different thresholds for different income types
        if total_wht > 0:
            if "40(2)" in income_type:  # Professional services
                requirements.append({
                    "form": "PND 54",
                    "income_type": income_type,
                    "total_wht": total_wht,
                    "due_date": "March 31st",
                    "required": total_wht >= 1000
                })
            elif "40(5)" in income_type:  # Rental
                requirements.append({
                    "form": "PND 55",
                    "income_type": income_type,
                    "total_wht": total_wht,
                    "due_date": "March 31st", 
                    "required": total_wht >= 500
                })
    
    return requirements


# ==================================================
# VALIDATION AND UTILITY FUNCTIONS
# ==================================================

def validate_wht_setup(doc, method=None):
    """
    Comprehensive validation for WHT setup
    """
    if not hasattr(doc, 'custom_is_withholding_tax') or not doc.custom_is_withholding_tax:
        return
    
    # Validate tax rate
    if not doc.custom_withholding_tax_rate or doc.custom_withholding_tax_rate <= 0:
        frappe.throw(_("Withholding Tax Rate must be greater than 0"))
    
    if doc.custom_withholding_tax_rate > 30:
        frappe.throw(_("Withholding Tax Rate cannot exceed 30%"))
    
    # Validate minimum amount threshold
    base_amount = get_base_amount_for_wht(doc)
    if base_amount < 1000:  # 1,000 THB minimum for WHT
        frappe.msgprint(_("Warning: Amount is below typical WHT threshold of 1,000 THB"), 
                      alert=True, indicator="orange")
    
    # Validate supplier tax ID for proper certificate generation
    if doc.doctype in ["Purchase Invoice", "Payment Entry"]:
        supplier = doc.supplier if hasattr(doc, 'supplier') else (doc.party if doc.party_type == "Supplier" else None)
        
        if not doc.custom_supplier_tax_id and supplier:
            # Try to get from supplier master
            supplier_tax_id = frappe.db.get_value("Supplier", supplier, "tax_id")
            if supplier_tax_id:
                doc.custom_supplier_tax_id = supplier_tax_id
            else:
                frappe.msgprint(_("Please add Supplier Tax ID for proper WHT certificate generation"), 
                              alert=True, indicator="orange")


# ==================================================
# SUGGESTED RATES AND AUTOMATION
# ==================================================

# Enhanced Thai WHT rates configuration
THAI_WHT_RATES = {
    "professional_service": {
        "rate": 5.0,
        "description": "ค่าธรรมเนียมวิชาชีพ",
        "keywords": ["professional", "legal", "accounting", "medical", "engineering"]
    },
    "consulting": {
        "rate": 3.0,
        "description": "ค่าที่ปรึกษา",
        "keywords": ["consulting", "advisory", "management"]
    },
    "general_service": {
        "rate": 3.0,
        "description": "ค่าบริการทั่วไป",
        "keywords": ["service", "maintenance", "repair"]
    },
    "advertising": {
        "rate": 2.0,
        "description": "ค่าโฆษณา",
        "keywords": ["advertising", "marketing", "promotion"]
    },
    "rental": {
        "rate": 5.0,  # Can be 1% or 5% depending on type
        "description": "ค่าเช่า",
        "keywords": ["rental", "lease", "rent"]
    },
    "transportation": {
        "rate": 1.0,
        "description": "ค่าขนส่ง",
        "keywords": ["transport", "delivery", "shipping", "freight"]
    },
    "construction": {
        "rate": 3.0,
        "description": "ค่าก่อสร้าง",
        "keywords": ["construction", "building", "renovation"]
    },
    "royalty": {
        "rate": 5.0,
        "description": "ค่าลิขสิทธิ์",
        "keywords": ["royalty", "license", "copyright", "patent"]
    }
}


@frappe.whitelist()
def get_suggested_wht_rate(item_group=None, supplier_type=None, service_description=None):
    """
    Get suggested WHT rate based on various inputs with enhanced logic
    """
    # Combine all text inputs for analysis
    search_text = " ".join(filter(None, [
        item_group or "",
        supplier_type or "",
        service_description or ""
    ])).lower()
    
    if search_text:
        # Score each rate category
        scores = {}
        for category, config in THAI_WHT_RATES.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in search_text:
                    score += 1
            
            if score > 0:
                scores[category] = score
        
        # Return highest scoring category
        if scores:
            best_match = max(scores.items(), key=lambda x: x[1])
            category = best_match[0]
            return {
                "rate": THAI_WHT_RATES[category]["rate"],
                "description": THAI_WHT_RATES[category]["description"],
                "category": category,
                "confidence": best_match[1]
            }
    
    # Default to general service rate
    return {
        "rate": 3.0,
        "description": "ค่าบริการทั่วไป",
        "category": "general_service",
        "confidence": 0
    }


@frappe.whitelist()
def get_wht_rate_guide():
    """
    Get complete WHT rate guide for reference
    """
    return {
        "rates": THAI_WHT_RATES,
        "general_info": {
            "minimum_threshold": 1000,
            "currency": "THB",
            "filing_deadline": "March 31st of following year",
            "forms_required": ["PND 54", "PND 55", "PND 56"]
        },
        "common_scenarios": [
            {"service": "IT Consulting", "rate": 3.0, "form": "PND 54"},
            {"service": "Legal Services", "rate": 5.0, "form": "PND 54"},
            {"service": "Office Rental", "rate": 5.0, "form": "PND 55"},
            {"service": "Equipment Rental", "rate": 1.0, "form": "PND 55"},
            {"service": "Advertising", "rate": 2.0, "form": "PND 54"},
            {"service": "Transportation", "rate": 1.0, "form": "PND 54"}
        ]
    }


# ==================================================
# INTEGRATION WITH PRINT DESIGNER
# ==================================================

def add_custom_fields():
    """
    Add custom fields for WHT functionality (called from installation)
    """
    # This function is called from the setup system
    # Fields are defined in setup/install.py
    pass


@frappe.whitelist()
def generate_wht_certificate_pdf(document_name, doctype="Payment Entry"):
    """
    Generate WHT certificate PDF using Print Designer format
    """
    try:
        # Get certificate data
        cert_data = get_wht_certificate_data(document_name, doctype)
        
        # Set print format
        print_format = "Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate"
        
        # Generate PDF
        pdf = frappe.get_print(doctype, document_name, print_format, as_pdf=True)
        
        # Mark certificate as generated
        doc = frappe.get_doc(doctype, document_name)
        doc.custom_wht_certificate_generated = 1
        doc.save()
        
        return {
            "success": True,
            "pdf": pdf,
            "certificate_data": cert_data
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating WHT certificate PDF: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }