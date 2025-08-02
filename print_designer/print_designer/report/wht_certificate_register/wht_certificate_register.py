# File: print_designer/print_designer/report/wht_certificate_register/wht_certificate_register.py

import frappe
from frappe import _
from frappe.utils import getdate, formatdate, flt


def execute(filters=None):
    """Main execution function for WHT Certificate Register report"""

    if not filters:
        filters = {}

    # Validate required filters
    validate_filters(filters)

    # Get columns and data
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary_data(data)

    return columns, data, None, chart, summary


def validate_filters(filters):
    """Validate required filters"""
    if not filters.get("from_date"):
        frappe.throw(_("From Date is required"))
    if not filters.get("to_date"):
        frappe.throw(_("To Date is required"))

    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be greater than To Date"))


def get_columns():
    """Define report columns"""
    return [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": _("Payment Entry"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 120,
        },
        {"label": _("Party"), "fieldname": "party", "fieldtype": "Data", "width": 150},
        {
            "label": _("Party Tax ID"),
            "fieldname": "party_tax_id",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Income Type"),
            "fieldname": "income_type",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Amount Paid"),
            "fieldname": "amount_paid",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Tax Rate (%)"),
            "fieldname": "tax_rate",
            "fieldtype": "Percent",
            "width": 100,
        },
        {
            "label": _("Tax Withheld"),
            "fieldname": "tax_withheld",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": _("Form Number"),
            "fieldname": "form_number",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Submission Date"),
            "fieldname": "submission_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100,
        },
    ]


def get_data(filters):
    """Get report data based on filters"""

    conditions = get_conditions(filters)

    sql = f"""
        SELECT 
            pe.posting_date,
            pe.name,
            pe.party,
            pe.custom_party_tax_id as party_tax_id,
            pe.income_type_selection as income_type,
            pe.custom_total_amount_paid as amount_paid,
            pe.withholding_tax_rate as tax_rate,
            pe.custom_total_tax_withheld as tax_withheld,
            pe.submission_form_number as form_number,
            pe.submission_form_date as submission_date,
            CASE 
                WHEN pe.submission_form_date IS NOT NULL THEN 'Submitted'
                WHEN pe.docstatus = 1 THEN 'Pending'
                ELSE 'Draft'
            END as status,
            pe.company
        FROM `tabPayment Entry` pe
        WHERE pe.apply_thai_withholding_tax = 1
        AND pe.docstatus = 1
        {conditions}
        ORDER BY pe.posting_date DESC, pe.name
    """

    data = frappe.db.sql(sql, filters, as_dict=1)

    # Format data
    for row in data:
        # Format income type for display
        if row.income_type:
            row.income_type = format_income_type(row.income_type)

        # Format tax ID
        if row.party_tax_id:
            row.party_tax_id = format_tax_id(row.party_tax_id)

        # Add row indicators
        row["status_indicator"] = get_status_indicator(row.status)

    return data


def get_conditions(filters):
    """Build SQL conditions based on filters"""
    conditions = []

    if filters.get("from_date"):
        conditions.append("pe.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("pe.posting_date <= %(to_date)s")

    if filters.get("party"):
        conditions.append("pe.party = %(party)s")

    if filters.get("company"):
        conditions.append("pe.company = %(company)s")

    if filters.get("income_type"):
        conditions.append("pe.income_type_selection LIKE %(income_type)s")
        filters["income_type"] = f"{filters['income_type']}%"

    if filters.get("submission_status"):
        if filters["submission_status"] == "Submitted":
            conditions.append("pe.submission_form_date IS NOT NULL")
        elif filters["submission_status"] == "Pending":
            conditions.append("pe.submission_form_date IS NULL AND pe.docstatus = 1")
        elif filters["submission_status"] == "Draft":
            conditions.append("pe.docstatus = 0")

    return " AND " + " AND ".join(conditions) if conditions else ""


def get_chart_data(data):
    """Generate chart data for the report"""

    # Group by income type
    income_type_totals = {}
    monthly_totals = {}

    for row in data:
        # Income type breakdown
        income_type = row.income_type or "Unknown"
        if income_type not in income_type_totals:
            income_type_totals[income_type] = 0
        income_type_totals[income_type] += flt(row.tax_withheld)

        # Monthly breakdown
        month_key = (
            row.posting_date.strftime("%Y-%m") if row.posting_date else "Unknown"
        )
        if month_key not in monthly_totals:
            monthly_totals[month_key] = 0
        monthly_totals[month_key] += flt(row.tax_withheld)

    return {
        "data": {
            "labels": list(income_type_totals.keys()),
            "datasets": [
                {
                    "name": "Tax Withheld by Income Type",
                    "values": list(income_type_totals.values()),
                }
            ],
        },
        "type": "donut",
        "height": 300,
    }


def get_summary_data(data):
    """Generate summary statistics"""

    if not data:
        return []

    total_amount_paid = sum(flt(row.amount_paid) for row in data)
    total_tax_withheld = sum(flt(row.tax_withheld) for row in data)
    total_certificates = len(data)

    submitted_count = len([row for row in data if row.status == "Submitted"])
    pending_count = len([row for row in data if row.status == "Pending"])

    avg_tax_rate = (
        (total_tax_withheld / total_amount_paid * 100) if total_amount_paid > 0 else 0
    )

    return [
        {
            "value": total_certificates,
            "label": "Total Certificates",
            "indicator": "Blue",
            "datatype": "Int",
        },
        {
            "value": total_amount_paid,
            "label": "Total Amount Paid",
            "indicator": "Green",
            "datatype": "Currency",
        },
        {
            "value": total_tax_withheld,
            "label": "Total Tax Withheld",
            "indicator": "Orange",
            "datatype": "Currency",
        },
        {
            "value": f"{avg_tax_rate:.2f}%",
            "label": "Average Tax Rate",
            "indicator": "Purple",
            "datatype": "Data",
        },
        {
            "value": submitted_count,
            "label": "Submitted to Revenue Dept",
            "indicator": "Green",
            "datatype": "Int",
        },
        {
            "value": pending_count,
            "label": "Pending Submission",
            "indicator": "Red",
            "datatype": "Int",
        },
    ]


def format_income_type(income_type):
    """Format income type for display"""
    if not income_type:
        return ""

    # Extract just the Thai description
    if " - " in income_type:
        parts = income_type.split(" - ")
        if len(parts) >= 2:
            return f"{parts[0]} - {parts[1].split('(')[0].strip()}"

    return income_type


def format_tax_id(tax_id):
    """Format Thai Tax ID with dashes"""
    if not tax_id:
        return ""

    clean_id = str(tax_id).replace("-", "").replace(" ", "")
    if len(clean_id) == 13 and clean_id.isdigit():
        return f"{clean_id[0]}-{clean_id[1:5]}-{clean_id[5:10]}-{clean_id[10:12]}-{clean_id[12]}"

    return tax_id


def get_status_indicator(status):
    """Get color indicator for status"""
    indicators = {"Submitted": "green", "Pending": "orange", "Draft": "red"}
    return indicators.get(status, "gray")
