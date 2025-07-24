"""
API endpoints for Thai Withholding Tax operations
Provides REST API access to WHT functionality
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def calculate_wht_amount(base_amount, tax_rate):
    """
    Simple API endpoint to calculate WHT amount
    """
    try:
        base = flt(base_amount)
        rate = flt(tax_rate)
        
        if base <= 0 or rate <= 0:
            return {"error": "Base amount and tax rate must be greater than 0"}
        
        if rate > 30:
            return {"error": "Tax rate cannot exceed 30%"}
        
        wht_amount = (base * rate) / 100
        net_amount = base - wht_amount
        
        return {
            "success": True,
            "base_amount": base,
            "tax_rate": rate,
            "wht_amount": flt(wht_amount, 2),
            "net_amount": flt(net_amount, 2),
            "calculation": f"{base} × {rate}% = {flt(wht_amount, 2)}"
        }
        
    except Exception as e:
        frappe.log_error(f"WHT calculation error: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_wht_rates_guide():
    """
    Get comprehensive WHT rates guide
    """
    try:
        from print_designer.custom.withholding_tax import get_wht_rate_guide
        return get_wht_rate_guide()
        
    except Exception as e:
        frappe.log_error(f"Error getting WHT rates guide: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def suggest_wht_rate(item_group=None, supplier_type=None, service_description=None):
    """
    API endpoint for WHT rate suggestion
    """
    try:
        from print_designer.custom.withholding_tax import get_suggested_wht_rate
        
        suggestion = get_suggested_wht_rate(
            item_group=item_group,
            supplier_type=supplier_type, 
            service_description=service_description
        )
        
        return {
            "success": True,
            "suggestion": suggestion
        }
        
    except Exception as e:
        frappe.log_error(f"Error suggesting WHT rate: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def generate_wht_certificate(document_name, doctype="Payment Entry"):
    """
    API endpoint to generate WHT certificate
    """
    try:
        if not frappe.has_permission(doctype, "read", document_name):
            frappe.throw(_("Insufficient permissions"))
        
        from print_designer.custom.withholding_tax import get_wht_certificate_data, generate_wht_certificate_pdf
        
        # Get certificate data
        cert_data = get_wht_certificate_data(document_name, doctype)
        
        # Generate PDF if requested
        pdf_result = generate_wht_certificate_pdf(document_name, doctype)
        
        return {
            "success": True,
            "certificate_data": cert_data,
            "pdf_generated": pdf_result["success"],
            "message": "WHT certificate generated successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating WHT certificate: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def create_wht_journal_entry(document_name, doctype="Payment Entry"):
    """
    API endpoint to create WHT journal entry
    """
    try:
        if not frappe.has_permission("Journal Entry", "create"):
            frappe.throw(_("Insufficient permissions to create Journal Entry"))
        
        from print_designer.custom.withholding_tax import create_wht_journal_entry
        
        je_name = create_wht_journal_entry(document_name, doctype)
        
        return {
            "success": True,
            "journal_entry": je_name,
            "message": f"Journal Entry {je_name} created successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating WHT journal entry: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_wht_summary_report(from_date, to_date, company=None, supplier=None):
    """
    API endpoint for WHT summary report
    """
    try:
        if not from_date or not to_date:
            return {"error": "From date and to date are required"}
        
        from print_designer.custom.withholding_tax import get_wht_summary_report
        
        report_data = get_wht_summary_report(
            from_date=from_date,
            to_date=to_date,
            company=company,
            supplier=supplier
        )
        
        return {
            "success": True,
            "report": report_data
        }
        
    except Exception as e:
        frappe.log_error(f"Error generating WHT report: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_supplier_wht_history(supplier, from_date=None, to_date=None):
    """
    Get WHT history for a specific supplier
    """
    try:
        if not supplier:
            return {"error": "Supplier is required"}
        
        # Set default date range (current year)
        if not from_date:
            from_date = f"{getdate().year}-01-01"
        if not to_date:
            to_date = f"{getdate().year}-12-31"
        
        # Get Payment Entries
        payment_entries = frappe.get_all("Payment Entry",
            filters={
                "party_type": "Supplier",
                "party": supplier,
                "custom_is_withholding_tax": 1,
                "docstatus": 1,
                "reference_date": ["between", [from_date, to_date]]
            },
            fields=[
                "name", "reference_date", "paid_amount", "custom_withholding_tax_rate",
                "custom_withholding_tax_amount", "custom_wht_certificate_number",
                "custom_wht_certificate_generated"
            ]
        )
        
        # Get Purchase Invoices
        purchase_invoices = frappe.get_all("Purchase Invoice",
            filters={
                "supplier": supplier,
                "custom_is_withholding_tax": 1,
                "docstatus": 1,
                "posting_date": ["between", [from_date, to_date]]
            },
            fields=[
                "name", "posting_date", "grand_total", "custom_withholding_tax_rate",
                "custom_withholding_tax_amount", "custom_supplier_tax_id"
            ]
        )
        
        # Calculate totals
        total_payments = sum(flt(pe.paid_amount) for pe in payment_entries)
        total_invoices = sum(flt(pi.grand_total) for pi in purchase_invoices)
        total_wht = sum(flt(pe.custom_withholding_tax_amount) for pe in payment_entries) + \
                   sum(flt(pi.custom_withholding_tax_amount) for pi in purchase_invoices)
        
        # Get supplier details
        supplier_doc = frappe.get_doc("Supplier", supplier)
        
        return {
            "success": True,
            "supplier": {
                "name": supplier,
                "supplier_name": supplier_doc.supplier_name,
                "tax_id": supplier_doc.tax_id,
                "supplier_group": supplier_doc.supplier_group
            },
            "period": {"from_date": from_date, "to_date": to_date},
            "summary": {
                "total_payment_entries": len(payment_entries),
                "total_purchase_invoices": len(purchase_invoices),
                "total_payments": total_payments,
                "total_invoices": total_invoices,
                "total_wht_amount": total_wht,
                "total_base_amount": total_payments + total_invoices
            },
            "payment_entries": payment_entries,
            "purchase_invoices": purchase_invoices
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting supplier WHT history: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def validate_supplier_tax_id(tax_id):
    """
    Validate Thai supplier tax ID format
    """
    try:
        if not tax_id:
            return {"valid": False, "error": "Tax ID is required"}
        
        # Remove any spaces or dashes
        clean_id = tax_id.replace(" ", "").replace("-", "")
        
        # Check length (should be 13 digits)
        if len(clean_id) != 13:
            return {"valid": False, "error": "Tax ID must be 13 digits"}
        
        # Check if all characters are digits
        if not clean_id.isdigit():
            return {"valid": False, "error": "Tax ID must contain only numbers"}
        
        # Basic checksum validation for Thai Tax ID
        if not validate_thai_tax_id_checksum(clean_id):
            return {"valid": False, "error": "Invalid Tax ID checksum"}
        
        return {
            "valid": True,
            "formatted_id": f"{clean_id[:1]}-{clean_id[1:5]}-{clean_id[5:10]}-{clean_id[10:12]}-{clean_id[12]}",
            "clean_id": clean_id
        }
        
    except Exception as e:
        frappe.log_error(f"Error validating tax ID: {str(e)}")
        return {"valid": False, "error": str(e)}


def validate_thai_tax_id_checksum(tax_id):
    """
    Validate Thai tax ID using checksum algorithm
    """
    try:
        if len(tax_id) != 13:
            return False
        
        # Calculate checksum
        multipliers = [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
        total = sum(int(tax_id[i]) * multipliers[i] for i in range(12))
        
        checksum = 11 - (total % 11)
        if checksum >= 10:
            checksum = checksum % 10
        
        return int(tax_id[12]) == checksum
        
    except:
        return False


@frappe.whitelist()
def get_wht_dashboard_data(company=None):
    """
    Get dashboard data for WHT overview
    """
    try:
        from datetime import datetime, timedelta
        
        # Current year data
        current_year = datetime.now().year
        year_start = f"{current_year}-01-01"
        year_end = f"{current_year}-12-31"
        
        # Current month data
        current_month_start = f"{current_year}-{datetime.now().month:02d}-01"
        
        filters = {"custom_is_withholding_tax": 1, "docstatus": 1}
        if company:
            filters["company"] = company
        
        # Year-to-date data
        ytd_payments = frappe.get_all("Payment Entry",
            filters=dict(filters, **{
                "party_type": "Supplier",
                "reference_date": ["between", [year_start, year_end]]
            }),
            fields=["paid_amount", "custom_withholding_tax_amount"]
        )
        
        ytd_invoices = frappe.get_all("Purchase Invoice",
            filters=dict(filters, **{
                "posting_date": ["between", [year_start, year_end]]
            }),
            fields=["grand_total", "custom_withholding_tax_amount"]
        )
        
        # Calculate totals
        ytd_total_base = sum(flt(p.paid_amount) for p in ytd_payments) + \
                        sum(flt(i.grand_total) for i in ytd_invoices)
        
        ytd_total_wht = sum(flt(p.custom_withholding_tax_amount) for p in ytd_payments) + \
                       sum(flt(i.custom_withholding_tax_amount) for i in ytd_invoices)
        
        # Month-to-date data
        mtd_payments = frappe.get_all("Payment Entry",
            filters=dict(filters, **{
                "party_type": "Supplier", 
                "reference_date": [">=", current_month_start]
            }),
            fields=["custom_withholding_tax_amount"]
        )
        
        mtd_invoices = frappe.get_all("Purchase Invoice",
            filters=dict(filters, **{
                "posting_date": [">=", current_month_start]
            }),
            fields=["custom_withholding_tax_amount"]
        )
        
        mtd_total_wht = sum(flt(p.custom_withholding_tax_amount) for p in mtd_payments) + \
                       sum(flt(i.custom_withholding_tax_amount) for i in mtd_invoices)
        
        # Top suppliers by WHT amount
        top_suppliers = get_top_suppliers_by_wht(year_start, year_end, company)
        
        return {
            "success": True,
            "dashboard": {
                "year_to_date": {
                    "total_documents": len(ytd_payments) + len(ytd_invoices),
                    "total_base_amount": ytd_total_base,
                    "total_wht_amount": ytd_total_wht,
                    "average_rate": (ytd_total_wht / ytd_total_base * 100) if ytd_total_base else 0
                },
                "month_to_date": {
                    "total_documents": len(mtd_payments) + len(mtd_invoices),
                    "total_wht_amount": mtd_total_wht
                },
                "top_suppliers": top_suppliers,
                "period": {"year": current_year, "month": datetime.now().month}
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting WHT dashboard data: {str(e)}")
        return {"error": str(e)}


def get_top_suppliers_by_wht(from_date, to_date, company=None):
    """
    Get top 5 suppliers by WHT amount
    """
    try:
        filters = {
            "custom_is_withholding_tax": 1,
            "docstatus": 1,
            "reference_date": ["between", [from_date, to_date]]
        }
        
        if company:
            filters["company"] = company
        
        # Get payment entries grouped by supplier
        suppliers_data = frappe.db.sql("""
            SELECT 
                party as supplier,
                party_name as supplier_name,
                SUM(custom_withholding_tax_amount) as total_wht,
                COUNT(*) as transaction_count,
                SUM(paid_amount) as total_payments
            FROM `tabPayment Entry`
            WHERE custom_is_withholding_tax = 1 
            AND docstatus = 1
            AND party_type = 'Supplier'
            AND reference_date BETWEEN %s AND %s
            {}
            GROUP BY party, party_name
            ORDER BY total_wht DESC
            LIMIT 5
        """.format("AND company = %(company)s" if company else ""), 
        {"from_date": from_date, "to_date": to_date, "company": company} if company 
        else {"from_date": from_date, "to_date": to_date}, as_dict=True)
        
        return suppliers_data
        
    except Exception as e:
        frappe.log_error(f"Error getting top suppliers: {str(e)}")
        return []