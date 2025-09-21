# Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today
from datetime import datetime


class EmployeeTaxLedger(Document):
    def validate(self):
        """Validate the Employee Tax Ledger"""
        self.validate_tax_year()
        self.calculate_totals()

    def validate_tax_year(self):
        """Ensure tax year is in Buddhist Era format"""
        if self.tax_year:
            # If entered as Christian year, convert to Buddhist
            if len(str(self.tax_year)) == 4 and int(self.tax_year) < 2500:
                self.tax_year = str(int(self.tax_year) + 543)

    def calculate_totals(self):
        """Calculate summary totals from monthly entries"""
        self.total_gross_salary = 0
        self.total_income_tax_deducted = 0
        self.total_social_security = 0
        self.total_provident_fund = 0

        for entry in self.monthly_entries:
            self.total_gross_salary += flt(entry.gross_salary)
            self.total_income_tax_deducted += flt(entry.income_tax_amount)
            self.total_social_security += flt(entry.social_security)
            self.total_provident_fund += flt(entry.provident_fund)

    def add_salary_slip_entry(self, salary_slip_doc):
        """Add or update entry from Salary Slip"""
        # Check if entry already exists for this salary slip
        existing_entry = None
        for entry in self.monthly_entries:
            if entry.salary_slip == salary_slip_doc.name:
                existing_entry = entry
                break

        # Get Income Tax amount from deductions
        income_tax = self.get_income_tax_from_salary_slip(salary_slip_doc)
        social_security = self.get_deduction_amount(salary_slip_doc, "Social Security")
        provident_fund = self.get_deduction_amount(salary_slip_doc, "Provident Fund")

        # Get month name
        posting_date = getdate(salary_slip_doc.posting_date)
        month_num = posting_date.month
        month_names = {
            1: "01 - January", 2: "02 - February", 3: "03 - March",
            4: "04 - April", 5: "05 - May", 6: "06 - June",
            7: "07 - July", 8: "08 - August", 9: "09 - September",
            10: "10 - October", 11: "11 - November", 12: "12 - December"
        }

        if existing_entry:
            # Update existing entry
            existing_entry.posting_date = salary_slip_doc.posting_date
            existing_entry.month = month_names.get(month_num)
            existing_entry.year = str(posting_date.year)
            existing_entry.gross_salary = salary_slip_doc.gross_pay
            existing_entry.income_tax_amount = income_tax
            existing_entry.social_security = social_security
            existing_entry.provident_fund = provident_fund
            existing_entry.net_pay = salary_slip_doc.net_pay
        else:
            # Add new entry
            self.append("monthly_entries", {
                "salary_slip": salary_slip_doc.name,
                "posting_date": salary_slip_doc.posting_date,
                "month": month_names.get(month_num),
                "year": str(posting_date.year),
                "gross_salary": salary_slip_doc.gross_pay,
                "income_tax_amount": income_tax,
                "social_security": social_security,
                "provident_fund": provident_fund,
                "net_pay": salary_slip_doc.net_pay
            })

        # Recalculate totals
        self.calculate_totals()

    def get_income_tax_from_salary_slip(self, salary_slip_doc):
        """Extract Income Tax amount from Salary Slip deductions"""
        tax_components = ["Income Tax", "TDS", "Withholding Tax", "Tax Deducted at Source"]

        for deduction in salary_slip_doc.deductions:
            if deduction.salary_component in tax_components:
                return flt(deduction.amount)

        # Also check for current_month_income_tax field
        if hasattr(salary_slip_doc, 'current_month_income_tax'):
            return flt(salary_slip_doc.current_month_income_tax)

        return 0

    def get_deduction_amount(self, salary_slip_doc, component_name):
        """Get specific deduction amount from Salary Slip"""
        for deduction in salary_slip_doc.deductions:
            if component_name.lower() in deduction.salary_component.lower():
                return flt(deduction.amount)
        return 0

    @frappe.whitelist()
    def generate_wht_certificate(self, reason="annual"):
        """Generate WHT Certificate from this ledger"""
        if self.wht_certificate:
            frappe.throw(f"WHT Certificate already exists: {self.wht_certificate}")

        if self.total_income_tax_deducted <= 0:
            frappe.throw("No income tax to generate certificate for")

        # Create WHT Certificate
        wht_cert = frappe.new_doc("Withholding Tax Certificate")

        # Certificate numbering
        buddhist_year = self.tax_year
        buddhist_year_short = str(buddhist_year)[-2:]

        if reason == "annual":
            month = "12"  # December for annual
            tax_month = "12 - ธันวาคม (December)"
            income_desc = f"เงินเดือนประจำปี {self.tax_year}"
        else:
            # For resignation, use the resignation month
            if self.resignation_date:
                resignation_date = getdate(self.resignation_date)
                month = str(resignation_date.month).zfill(2)
                tax_month = self.get_thai_month(month)
                income_desc = f"เงินเดือนและค่าตอบแทน (ลาออก {resignation_date.strftime('%d/%m/%Y')})"
            else:
                month = datetime.now().strftime("%m")
                tax_month = self.get_thai_month(month)
                income_desc = f"เงินเดือนและค่าตอบแทน"

        from frappe.model.naming import make_autoname
        cert_number = make_autoname(f"WHTC-{buddhist_year_short}{month}-.#####.")

        # Get employee details
        employee_doc = frappe.get_doc("Employee", self.employee)

        # Set certificate fields
        wht_cert.certificate_number = cert_number
        wht_cert.certificate_date = today()
        wht_cert.tax_year = self.tax_year
        wht_cert.tax_month = tax_month

        # Employee information (need to adapt since WHT cert expects supplier)
        # We'll use employee name as supplier name and tax ID
        wht_cert.supplier = None  # No supplier link for employee
        wht_cert.employee = self.employee
        wht_cert.supplier_name = self.employee_name
        wht_cert.supplier_tax_id = self.employee_tax_id or ""

        # Income details - use 40(1) for salary or 40(2) for fees
        if hasattr(employee_doc, 'employment_type') and employee_doc.employment_type == "Contract":
            wht_cert.income_type = "2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2) - Fee/Commission"
        else:
            wht_cert.income_type = "1. เงินเดือน ค่าจ้าง ฯลฯ 40(1) - Salary"

        wht_cert.income_description = income_desc

        # Amounts
        wht_cert.tax_base_amount = self.total_gross_salary
        wht_cert.wht_amount = self.total_income_tax_deducted

        # Calculate WHT rate
        if self.total_gross_salary > 0:
            wht_cert.wht_rate = (self.total_income_tax_deducted / self.total_gross_salary) * 100
        else:
            wht_cert.wht_rate = 0

        # Other fields
        wht_cert.wht_condition = "1. หัก ณ ที่จ่าย (Withhold at Source)"
        wht_cert.certificate_period = "Annual" if reason == "annual" else "Resignation"
        wht_cert.pnd_form_type = "PND1 Form"
        wht_cert.supplier_type_classification = "Individual - Staff (PND.1)"
        wht_cert.employee_tax_ledger = self.name

        # Company information
        wht_cert.company = frappe.defaults.get_user_default("company")
        wht_cert.company_branch = "00000"  # Head office

        # Status
        wht_cert.status = "Issued"

        # Insert and submit
        wht_cert.insert()
        wht_cert.submit()

        # Update this ledger
        self.wht_certificate = wht_cert.name
        self.certificate_issue_date = today()
        self.certificate_reason = "Annual" if reason == "annual" else "Resignation"
        self.status = "Certificate Issued"
        self.save()

        frappe.msgprint(f"WHT Certificate {wht_cert.name} created successfully", indicator="green")

        return wht_cert.name

    def get_thai_month(self, month_num):
        """Get Thai month string"""
        thai_months = {
            "01": "01 - มกราคม (January)",
            "02": "02 - กุมภาพันธ์ (February)",
            "03": "03 - มีนาคม (March)",
            "04": "04 - เมษายน (April)",
            "05": "05 - พฤษภาคม (May)",
            "06": "06 - มิถุนายน (June)",
            "07": "07 - กรกฎาคม (July)",
            "08": "08 - สิงหาคม (August)",
            "09": "09 - กันยายน (September)",
            "10": "10 - ตุลาคม (October)",
            "11": "11 - พฤศจิกายน (November)",
            "12": "12 - ธันวาคม (December)"
        }
        return thai_months.get(month_num, month_num)


@frappe.whitelist()
def update_from_salary_slip(salary_slip_name):
    """Update Employee Tax Ledger from Salary Slip submission"""
    salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)

    # Get tax year (Buddhist Era)
    posting_date = getdate(salary_slip.posting_date)
    tax_year = str(posting_date.year + 543)

    # Find or create ledger for employee and year
    ledger_name = frappe.db.get_value(
        "Employee Tax Ledger",
        {"employee": salary_slip.employee, "tax_year": tax_year},
        "name"
    )

    if not ledger_name:
        # Create new ledger
        ledger = frappe.new_doc("Employee Tax Ledger")
        ledger.employee = salary_slip.employee
        ledger.employee_name = salary_slip.employee_name
        ledger.tax_year = tax_year
        ledger.status = "Active"
    else:
        # Get existing ledger
        ledger = frappe.get_doc("Employee Tax Ledger", ledger_name)

    # Add salary slip entry
    ledger.add_salary_slip_entry(salary_slip)
    ledger.save()

    return ledger.name


@frappe.whitelist()
def generate_annual_wht_certificates(tax_year=None):
    """Generate WHT certificates for all employees for a tax year"""
    if not tax_year:
        # Default to previous year
        current_year = datetime.now().year
        tax_year = str(current_year + 543 - 1)  # Previous Buddhist year

    ledgers = frappe.get_all(
        "Employee Tax Ledger",
        filters={
            "tax_year": tax_year,
            "status": ["!=", "Certificate Issued"],
            "total_income_tax_deducted": [">", 0]
        },
        fields=["name", "employee", "employee_name", "total_income_tax_deducted"]
    )

    results = []
    for ledger_data in ledgers:
        try:
            ledger = frappe.get_doc("Employee Tax Ledger", ledger_data.name)
            cert_name = ledger.generate_wht_certificate("annual")
            results.append({
                "employee": ledger_data.employee_name,
                "certificate": cert_name,
                "status": "Success"
            })
        except Exception as e:
            results.append({
                "employee": ledger_data.employee_name,
                "certificate": None,
                "status": f"Error: {str(e)}"
            })

    return results
