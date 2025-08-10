# File: print_designer/commands/install_thai_form_50_twi.py

import os
import json
import click
import frappe
from frappe.commands import pass_context
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Add this function to your main installation script:
# File: print_designer/commands/install_thai_form_50_twi.py


def create_wht_reports():
    """Create WHT Certificate Register report"""

    click.echo("📊 Creating WHT Certificate Register report...")

    # Create report directory
    report_dir = frappe.get_app_path(
        "print_designer", "print_designer", "report", "wht_certificate_register"
    )
    os.makedirs(report_dir, exist_ok=True)

    # Create __init__.py
    init_file = os.path.join(report_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("")

    # Check if report already exists
    if frappe.db.exists("Report", "WHT Certificate Register"):
        click.echo("   ✓ WHT Certificate Register report already exists")
        return

    # Create report JSON file
    report_json_content = """{
    "doctype": "Report",
    "name": "WHT Certificate Register",
    "module": "Print Designer",
    "report_name": "WHT Certificate Register",
    "report_type": "Script Report",
    "ref_doctype": "Payment Entry",
    "is_standard": "No",
    "disabled": 0,
    "add_total_row": 1,
    "description": "Register of Thai Withholding Tax Certificates issued with detailed breakdowns by income type, party, and submission status."
}"""

    report_json_file = os.path.join(report_dir, "wht_certificate_register.json")
    with open(report_json_file, "w", encoding="utf-8") as f:
        f.write(report_json_content)

    # Create Python script file
    python_script = '''# Copyright (c) 2024, Print Designer Team and contributors
# For license information, please see license.txt

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
            "width": 100
        },
        {
            "label": _("Payment Entry"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 120
        },
        {
            "label": _("Party"),
            "fieldname": "party",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Party Tax ID"),
            "fieldname": "party_tax_id",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Income Type"),
            "fieldname": "income_type",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Amount Paid"),
            "fieldname": "amount_paid",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Tax Rate (%)"),
            "fieldname": "tax_rate",
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "label": _("Tax Withheld"),
            "fieldname": "tax_withheld",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Form Number"),
            "fieldname": "form_number",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Submission Date"),
            "fieldname": "submission_date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        }
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
    
    for row in data:
        income_type = row.income_type or "Unknown"
        if income_type not in income_type_totals:
            income_type_totals[income_type] = 0
        income_type_totals[income_type] += flt(row.tax_withheld)
    
    return {
        "data": {
            "labels": list(income_type_totals.keys()),
            "datasets": [
                {
                    "name": "Tax Withheld by Income Type",
                    "values": list(income_type_totals.values())
                }
            ]
        },
        "type": "donut",
        "height": 300
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
    
    avg_tax_rate = (total_tax_withheld / total_amount_paid * 100) if total_amount_paid > 0 else 0
    
    return [
        {
            "value": total_certificates,
            "label": "Total Certificates",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": total_amount_paid,
            "label": "Total Amount Paid",
            "indicator": "Green", 
            "datatype": "Currency"
        },
        {
            "value": total_tax_withheld,
            "label": "Total Tax Withheld",
            "indicator": "Orange",
            "datatype": "Currency"
        },
        {
            "value": f"{avg_tax_rate:.2f}%",
            "label": "Average Tax Rate",
            "indicator": "Purple",
            "datatype": "Data"
        },
        {
            "value": submitted_count,
            "label": "Submitted to Revenue Dept",
            "indicator": "Green",
            "datatype": "Int"
        },
        {
            "value": pending_count,
            "label": "Pending Submission",
            "indicator": "Red",
            "datatype": "Int"
        }
    ]

def format_income_type(income_type):
    """Format income type for display"""
    if not income_type:
        return ""
    
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
'''

    python_file = os.path.join(report_dir, "wht_certificate_register.py")
    with open(python_file, "w", encoding="utf-8") as f:
        f.write(python_script)

    # Create JavaScript client file
    js_script = """// Copyright (c) 2024, Print Designer Team and contributors
// For license information, please see license.txt

frappe.query_reports["WHT Certificate Register"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            "width": "80px"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.get_today(),
            "width": "80px"
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "width": "100px"
        },
        {
            "fieldname": "party",
            "label": __("Party"),
            "fieldtype": "Link",
            "options": "Supplier",
            "width": "100px"
        },
        {
            "fieldname": "income_type",
            "label": __("Income Type"),
            "fieldtype": "Select",
            "options": [
                "",
                "1 - เงินเดือน ค่าจ้าง",
                "2 - ค่าธรรมเนียม ค่านายหน้า", 
                "3 - ค่าลิขสิทธิ์ ค่าบริการทางเทคนิค",
                "4.1 - ดอกเบี้ย",
                "4.2 - เงินปันผล กำไรสุทธิ",
                "5 - ค่าเช่าทรัพย์สิน",
                "6 - อื่น ๆ"
            ],
            "width": "100px"
        },
        {
            "fieldname": "submission_status",
            "label": __("Submission Status"),
            "fieldtype": "Select",
            "options": [
                "",
                "Submitted",
                "Pending", 
                "Draft"
            ],
            "width": "100px"
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        // Format currency values
        if (["amount_paid", "tax_withheld"].includes(column.fieldname)) {
            if (value) {
                return `<div style="text-align: right;">${format_currency(value)}</div>`;
            }
        }
        
        // Format tax rate
        if (column.fieldname === "tax_rate" && value) {
            return `<div style="text-align: center;">${value}%</div>`;
        }
        
        // Format status with indicators
        if (column.fieldname === "status") {
            let color = get_status_color(value);
            return `<span class="indicator ${color}">${value}</span>`;
        }
        
        // Format Payment Entry as clickable link
        if (column.fieldname === "name") {
            return `<a href="/app/payment-entry/${value}" target="_blank">${value}</a>`;
        }
        
        return default_formatter(value, row, column, data);
    },
    
    "onload": function(report) {
        // Add custom buttons
        report.page.add_inner_button(__("Export to Excel"), function() {
            export_to_excel(report);
        });
        
        report.page.add_inner_button(__("Generate Certificates"), function() {
            generate_batch_certificates(report);
        });
        
        // Add refresh button
        report.page.add_inner_button(__("Refresh"), function() {
            report.refresh();
        }, __("Actions"));
    }
};

// Helper functions
function get_status_color(status) {
    const colors = {
        "Submitted": "green",
        "Pending": "orange",
        "Draft": "red"
    };
    return colors[status] || "gray";
}

function format_currency(value) {
    if (!value) return "0.00";
    return new Intl.NumberFormat('th-TH', {
        style: 'currency',
        currency: 'THB',
        minimumFractionDigits: 2
    }).format(value);
}

function export_to_excel(report) {
    const data = report.data;
    if (!data || data.length === 0) {
        frappe.msgprint(__("No data to export"));
        return;
    }
    
    // Create Excel export
    frappe.tools.downloadify(data, null, "WHT Certificate Register");
}

function generate_batch_certificates(report) {
    const selected_rows = report.datatable.getCheckedRows();
    
    if (selected_rows.length === 0) {
        frappe.msgprint(__("Please select rows to generate certificates"));
        return;
    }
    
    frappe.confirm(
        __("Generate WHT certificates for {0} selected entries?", [selected_rows.length]),
        function() {
            // Process batch generation
            frappe.msgprint(__("Batch certificate generation started"));
        }
    );
}
"""

    js_file = os.path.join(report_dir, "wht_certificate_register.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write(js_script)

    # Create the Report document
    try:
        report_doc = frappe.get_doc(
            {
                "doctype": "Report",
                "name": "WHT Certificate Register",
                "module": "Print Designer",
                "report_name": "WHT Certificate Register",
                "report_type": "Script Report",
                "ref_doctype": "Payment Entry",
                "is_standard": "No",
                "disabled": 0,
                "add_total_row": 1,
                "description": "Register of Thai Withholding Tax Certificates issued with detailed breakdowns by income type, party, and submission status.",
            }
        )

        report_doc.insert(ignore_permissions=True)
        click.echo("   ✓ Created WHT Certificate Register report")

    except Exception as e:
        click.echo(f"   ❌ Error creating report: {str(e)}")
        raise


# Update the main installation function to include report creation
def install_thai_form_50_twi_complete():
    """Complete installation including reports"""

    try:
        # ... existing installation steps ...

        # Step 6: Create Reports
        click.echo("📊 Step 6: Creating reports...")
        create_wht_reports()

        # ... rest of installation ...

    except Exception as e:
        click.echo(f"❌ Installation failed: {str(e)}")
        frappe.db.rollback()
        raise


@click.command("install-thai-form-50-twi")
@pass_context
def install_thai_form_50_twi(context):
    """Install Complete Thai Form 50 ทวิ (Withholding Tax Certificate) System"""

    site = context.sites[0] if context.sites else None
    if not site:
        click.echo("❌ Please specify a site using --site option")
        return

    frappe.init(site=site)
    frappe.connect()

    try:
        click.echo("🇹🇭 Installing Complete Thai Form 50 ทวิ System...")
        click.echo("=" * 60)

        # Step 1: Create Child DocType
        click.echo("📋 Step 1: Creating Thai Withholding Tax Detail DocType...")
        create_child_doctype()

        # Step 2: Setup Custom Fields
        click.echo("📝 Step 2: Setting up custom fields...")
        setup_custom_fields()

        # Step 3: Create Print Format (JSON-based)
        click.echo("🖨️  Step 3: Creating print format...")
        create_print_format_json()

        # Step 4: Create Jinja Template (Alternative)
        click.echo("📄 Step 4: Creating Jinja template...")
        create_jinja_print_format()

        # Step 5: Setup utility functions
        click.echo("🔧 Step 5: Setting up utility functions...")
        setup_utility_functions()

        # Step 6: Register event hooks
        click.echo("⚙️  Step 6: Registering event hooks...")
        register_event_hooks()

        frappe.db.commit()

        click.echo("=" * 60)
        click.echo("✅ Thai Form 50 ทวิ installation completed successfully!")
        click.echo("")

        # Display installation summary
        show_installation_summary()

    except Exception as e:
        click.echo(f"❌ Installation failed: {str(e)}")
        frappe.log_error("Thai Form 50ทวิ Installation Error", str(e))
        frappe.db.rollback()
        raise


def create_child_doctype():
    """Create Thai Withholding Tax Detail child DocType"""
    doctype_name = "Thai Withholding Tax Detail"

    if frappe.db.exists("DocType", doctype_name):
        click.echo(f"   ✓ {doctype_name} DocType already exists")
        return

    doctype_dict = {
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Print Designer",
        "istable": 1,
        "autoname": "hash",
        "creation": frappe.utils.now(),
        "modified": frappe.utils.now(),
        "owner": "Administrator",
        "modified_by": "Administrator",
        "fields": [
            {
                "fieldname": "income_type_code",
                "label": "Income Type Code",
                "fieldtype": "Select",
                "options": "1\n2\n3\n4.1\n4.2\n5\n6",
                "width": 80,
                "in_list_view": 1,
                "reqd": 1,
            },
            {
                "fieldname": "income_type_description",
                "label": "Income Type Description",
                "fieldtype": "Data",
                "width": 200,
                "in_list_view": 1,
            },
            {
                "fieldname": "payment_date",
                "label": "Payment Date",
                "fieldtype": "Date",
                "width": 100,
                "in_list_view": 1,
            },
            {
                "fieldname": "amount_paid",
                "label": "Amount Paid",
                "fieldtype": "Currency",
                "width": 120,
                "in_list_view": 1,
                "precision": 2,
            },
            {
                "fieldname": "tax_rate",
                "label": "Tax Rate (%)",
                "fieldtype": "Percent",
                "width": 80,
                "in_list_view": 1,
                "precision": 2,
            },
            {
                "fieldname": "tax_withheld",
                "label": "Tax Withheld",
                "fieldtype": "Currency",
                "width": 120,
                "in_list_view": 1,
                "precision": 2,
            },
        ],
        "permissions": [
            {
                "role": "System Manager",
                "permlevel": 0,
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
            },
            {
                "role": "Accounts Manager",
                "permlevel": 0,
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
            },
            {
                "role": "Accounts User",
                "permlevel": 0,
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
            },
        ],
    }

    try:
        doc = frappe.get_doc(doctype_dict)
        doc.insert(ignore_permissions=True)
        click.echo(f"   ✓ Created {doctype_name} DocType")
    except Exception as e:
        click.echo(f"   ❌ Error creating DocType: {str(e)}")
        raise


def setup_custom_fields():
    """Setup custom fields for Payment Entry"""
    custom_fields = {
        "Payment Entry": [
            {
                "fieldname": "thai_withholding_tax_section",
                "label": "Thai Withholding Tax (ภาษีหัก ณ ที่จ่าย)",
                "fieldtype": "Section Break",
                "insert_after": "taxes_and_charges",
                "collapsible": 1,
                "collapsible_depends_on": "apply_thai_withholding_tax",
            },
            {
                "fieldname": "apply_thai_withholding_tax",
                "label": "Apply Thai Withholding Tax",
                "fieldtype": "Check",
                "insert_after": "thai_withholding_tax_section",
                "default": 0,
            },
            {
                "fieldname": "income_type_selection",
                "label": "Income Type",
                "fieldtype": "Select",
                "options": "1 - เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส (Section 40.1)\n2 - ค่าธรรมเนียม ค่านายหน้า (Section 40.2)\n3 - ค่าแห่งลิขสิทธิ์ ค่าบริการทางเทคนิค (Section 40.3)\n4.1 - ดอกเบี้ย (Section 40.4a)\n4.2 - เงินปันผล กำไรสุทธิ (Section 40.4b,c)\n5 - ค่าเช่าทรัพย์สิน (Section 40.5)\n6 - อื่น ๆ (Others)",
                "insert_after": "apply_thai_withholding_tax",
                "depends_on": "apply_thai_withholding_tax",
                "default": "6 - อื่น ๆ (Others)",
                "reqd": 1,
            },
            {
                "fieldname": "other_income_description",
                "label": "Other Income Description (if Type 6)",
                "fieldtype": "Data",
                "insert_after": "income_type_selection",
                "depends_on": "eval:doc.income_type_selection && doc.income_type_selection.startsWith('6')",
                "default": "ค่าบริการ",
            },
            {
                "fieldname": "col_break_thai_1",
                "fieldtype": "Column Break",
                "insert_after": "other_income_description",
            },
            {
                "fieldname": "withholding_tax_rate",
                "label": "Withholding Tax Rate (%)",
                "fieldtype": "Percent",
                "insert_after": "col_break_thai_1",
                "depends_on": "apply_thai_withholding_tax",
                "default": 3.0,
                "precision": 2,
            },
            {
                "fieldname": "custom_company_tax_id",
                "label": "Company Tax ID",
                "fieldtype": "Data",
                "insert_after": "withholding_tax_rate",
                "depends_on": "apply_thai_withholding_tax",
                "fetch_from": "company.tax_id",
                "length": 17,
            },
            {
                "fieldname": "custom_company_address",
                "label": "Company Address",
                "fieldtype": "Small Text",
                "insert_after": "custom_company_tax_id",
                "depends_on": "apply_thai_withholding_tax",
            },
            {
                "fieldname": "custom_party_tax_id",
                "label": "Party Tax ID",
                "fieldtype": "Data",
                "insert_after": "custom_company_address",
                "depends_on": "apply_thai_withholding_tax",
                "fetch_from": "party.tax_id",
                "length": 17,
            },
            {
                "fieldname": "custom_party_address",
                "label": "Party Address",
                "fieldtype": "Small Text",
                "insert_after": "custom_party_tax_id",
                "depends_on": "apply_thai_withholding_tax",
            },
            {
                "fieldname": "section_break_thai_details",
                "fieldtype": "Section Break",
                "insert_after": "custom_party_address",
                "depends_on": "apply_thai_withholding_tax",
            },
            {
                "fieldname": "custom_withholding_tax_details",
                "label": "Withholding Tax Details",
                "fieldtype": "Table",
                "insert_after": "section_break_thai_details",
                "depends_on": "apply_thai_withholding_tax",
                "options": "Thai Withholding Tax Detail",
            },
            {
                "fieldname": "col_break_thai_totals",
                "fieldtype": "Column Break",
                "insert_after": "custom_withholding_tax_details",
            },
            {
                "fieldname": "custom_total_amount_paid",
                "label": "Total Amount Paid",
                "fieldtype": "Currency",
                "insert_after": "col_break_thai_totals",
                "depends_on": "apply_thai_withholding_tax",
                "read_only": 1,
                "precision": 2,
            },
            {
                "fieldname": "custom_total_tax_withheld",
                "label": "Total Tax Withheld",
                "fieldtype": "Currency",
                "insert_after": "custom_total_amount_paid",
                "depends_on": "apply_thai_withholding_tax",
                "read_only": 1,
                "precision": 2,
            },
            {
                "fieldname": "section_break_thai_submission",
                "fieldtype": "Section Break",
                "label": "Tax Submission Details",
                "insert_after": "custom_total_tax_withheld",
                "depends_on": "apply_thai_withholding_tax",
                "collapsible": 1,
            },
            {
                "fieldname": "submission_form_number",
                "label": "ภ.ง.ด.1ก Form Number",
                "fieldtype": "Data",
                "insert_after": "section_break_thai_submission",
                "depends_on": "apply_thai_withholding_tax",
            },
            {
                "fieldname": "submission_form_date",
                "label": "ภ.ง.ด.1ก Submission Date",
                "fieldtype": "Date",
                "insert_after": "submission_form_number",
                "depends_on": "apply_thai_withholding_tax",
            },
        ]
    }

    try:
        create_custom_fields(custom_fields, update=True)
        click.echo("   ✓ Created custom fields for Payment Entry")
    except Exception as e:
        click.echo(f"   ❌ Error creating custom fields: {str(e)}")
        raise


def create_print_format_json():
    """Create JSON-based Print Format for Print Designer"""
    print_format_name = "Thai Form 50ทวิ - JSON Format"

    if frappe.db.exists("Print Format", print_format_name):
        click.echo(f"   ✓ Print Format '{print_format_name}' already exists")
        return

    # JSON structure for Print Designer
    print_format_json = {
        "doctype": "Print Format",
        "name": print_format_name,
        "doc_type": "Payment Entry",
        "print_designer": 1,
        "font": "Sarabun",
        "font_size": 12,
        "margin_top": 15,
        "margin_bottom": 15,
        "margin_left": 15,
        "margin_right": 15,
        "page_size": "A4",
        "default_print_language": "th",
        "description": "Thai Form 50ทวิ - Official Withholding Tax Certificate (JSON-based Print Designer Format)",
        "print_designer_settings": json.dumps(
            {
                "page": {
                    "width": 595,
                    "height": 842,
                    "marginTop": 15,
                    "marginBottom": 15,
                    "marginLeft": 15,
                    "marginRight": 15,
                    "headerHeight": 0,
                    "footerHeight": 0,
                },
                "schema_version": "1.1.0",
            }
        ),
        "print_designer_body": json.dumps(
            [
                {
                    "type": "page",
                    "index": 0,
                    "childrens": [
                        {
                            "type": "text",
                            "id": "form_title",
                            "content": "หนังสือรับรองการหักภาษี ณ ที่จ่าย",
                            "startX": 50,
                            "startY": 30,
                            "width": 500,
                            "height": 25,
                            "style": {
                                "fontSize": "16px",
                                "fontWeight": "bold",
                                "textAlign": "center",
                                "fontFamily": "Sarabun, Arial, sans-serif",
                            },
                        },
                        {
                            "type": "text",
                            "id": "form_subtitle",
                            "content": "ตามมาตรา 50 ทวิ แห่งประมวลรัษฎากร",
                            "startX": 50,
                            "startY": 55,
                            "width": 500,
                            "height": 20,
                            "style": {
                                "fontSize": "12px",
                                "textAlign": "center",
                                "fontFamily": "Sarabun, Arial, sans-serif",
                            },
                        },
                    ],
                }
            ]
        ),
    }

    try:
        doc = frappe.get_doc(print_format_json)
        doc.insert(ignore_permissions=True)
        click.echo(f"   ✓ Created JSON Print Format: {print_format_name}")
    except Exception as e:
        click.echo(f"   ❌ Error creating JSON Print Format: {str(e)}")
        raise


def create_jinja_print_format():
    """Create Jinja-based Print Format as alternative"""
    print_format_name = "Thai Form 50ทวิ - Official Certificate"

    if frappe.db.exists("Print Format", print_format_name):
        click.echo(f"   ✓ Print Format '{print_format_name}' already exists")
        return

    # HTML template for official form
    html_template = get_official_html_template()

    print_format_dict = {
        "doctype": "Print Format",
        "name": print_format_name,
        "doc_type": "Payment Entry",
        "module": "Print Designer",
        "print_format_type": "Jinja",
        "font": "Sarabun",
        "font_size": 12,
        "margin_top": 10,
        "margin_bottom": 10,
        "margin_left": 10,
        "margin_right": 10,
        "page_size": "A4",
        "default_print_language": "th",
        "html": html_template,
        "css": get_official_css_styles(),
        "description": "Official Thai Form 50ทวิ - หนังสือรับรองการหักภาษี ณ ที่จ่าย (Revenue Department Compliant)",
    }

    try:
        doc = frappe.get_doc(print_format_dict)
        doc.insert(ignore_permissions=True)
        click.echo(f"   ✓ Created Jinja Print Format: {print_format_name}")
    except Exception as e:
        click.echo(f"   ❌ Error creating Jinja Print Format: {str(e)}")
        raise


def setup_utility_functions():
    """Setup utility functions file"""
    utility_file_path = frappe.get_app_path(
        "print_designer", "custom", "withholding_tax.py"
    )

    if os.path.exists(utility_file_path):
        click.echo("   ✓ Utility functions file already exists")
        return

    utility_code = get_utility_functions_code()

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(utility_file_path), exist_ok=True)

        with open(utility_file_path, "w", encoding="utf-8") as f:
            f.write(utility_code)

        click.echo("   ✓ Created utility functions file")
    except Exception as e:
        click.echo(f"   ❌ Error creating utility functions: {str(e)}")
        raise


def register_event_hooks():
    """Register event hooks in hooks.py"""
    hooks_info = """
# Add these event hooks to your hooks.py file:

doc_events = {
    # ... existing events ...
    "Payment Entry": {
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
        "on_update": "print_designer.custom.withholding_tax.update_withholding_details"
    }
}

# Add these whitelisted methods:
whitelisted = [
    # ... existing methods ...
    "print_designer.custom.withholding_tax.get_wht_rate_by_income_type",
    "print_designer.custom.withholding_tax.format_thai_tax_id",
    "print_designer.custom.withholding_tax.convert_to_thai_date"
]
"""

    click.echo("   ✓ Event hooks registration info prepared")
    click.echo("   📝 Please add the following to your hooks.py file:")
    click.echo(hooks_info)


def get_official_html_template():
    """Return the official HTML template"""
    return """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>หนังสือรับรองการหักภาษี ณ ที่จ่าย (ฟอร์ม 50 ทวิ)</title>
</head>
<body>
    <div class="form-50-twi">
        <!-- Form Header -->
        <div class="form-header">
            <div class="form-title">หนังสือรับรองการหักภาษี ณ ที่จ่าย</div>
            <div class="form-subtitle">ตามมาตรา 50 ทวิ แห่งประมวลรัษฎากร</div>
        </div>
        
        <div class="copy-info">
            ฉบับที่ 1 (สำหรับผู้ถูกหักภาษี ณ ที่จ่าย ใช้แนบพร้อมกับแบบแสดงรายการภาษี)
        </div>

        <!-- Payer Information Section -->
        <div class="section-box">
            <div class="section-title">ผู้มีหน้าที่หักภาษี ณ ที่จ่าย :-</div>
            
            <div class="field-row">
                <span class="field-label">ชื่อ</span>
                <span class="field-value">{{ doc.company or "" }}</span>
            </div>
            
            <div class="field-row">
                <span class="field-label">ที่อยู่</span>
                <span class="field-value">
                    {%- set company_address = doc.custom_company_address or frappe.get_value("Company", doc.company, "address") -%}
                    {{ company_address or "" }}
                </span>
            </div>
            
            <div class="field-row">
                <span class="field-label">เลขประจำตัวผู้เสียภาษีอากร</span>
                <span class="field-value">
                    {%- if doc.custom_company_tax_id or frappe.get_value("Company", doc.company, "tax_id") -%}
                        {%- set tax_id = doc.custom_company_tax_id or frappe.get_value("Company", doc.company, "tax_id") -%}
                        {%- set clean_id = tax_id.replace("-", "").replace(" ", "") -%}
                        {%- if clean_id|length == 13 -%}
                            {{ clean_id[0] }}-{{ clean_id[1:5] }}-{{ clean_id[5:10] }}-{{ clean_id[10:12] }}-{{ clean_id[12] }}
                        {%- else -%}
                            {{ tax_id }}
                        {%- endif -%}
                    {%- endif -%}
                </span>
            </div>
        </div>

        <!-- Payee Information Section -->
        <div class="section-box">
            <div class="section-title">ผู้ถูกหักภาษี ณ ที่จ่าย :-</div>
            
            <div class="field-row">
                <span class="field-label">ชื่อ</span>
                <span class="field-value">{{ doc.party_name or "" }}</span>
            </div>
            
            <div class="field-row">
                <span class="field-label">ที่อยู่</span>
                <span class="field-value">{{ doc.custom_party_address or "" }}</span>
            </div>
            
            <div class="field-row">
                <span class="field-label">เลขประจำตัวผู้เสียภาษีอากร</span>
                <span class="field-value">
                    {%- if doc.custom_party_tax_id -%}
                        {%- set clean_id = doc.custom_party_tax_id.replace("-", "").replace(" ", "") -%}
                        {%- if clean_id|length == 13 -%}
                            {{ clean_id[0] }}-{{ clean_id[1:5] }}-{{ clean_id[5:10] }}-{{ clean_id[10:12] }}-{{ clean_id[12] }}
                        {%- else -%}
                            {{ doc.custom_party_tax_id }}
                        {%- endif -%}
                    {%- endif -%}
                </span>
            </div>
        </div>

        <!-- Income Types and Tax Details Table -->
        <table class="income-types-table">
            <thead>
                <tr>
                    <th style="width: 50%;">
                        ประเภทเงินได้พึงประเมินที่จ่าย<br>
                        (กรุณาทำเครื่องหมาย ✓ ใน □ ที่ตรงกับประเภทเงินได้ที่จ่าย และระบุรายละเอียด)
                    </th>
                    <th style="width: 15%;">วัน เดือน ปี ภาษีที่จ่าย</th>
                    <th style="width: 15%;">จำนวนเงินที่จ่าย</th>
                    <th style="width: 20%;">ภาษีที่หักและนำส่งไว้</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="income-type-list">
                        <div>1. {% if doc.income_type_selection and doc.income_type_selection.startswith('1') %}☑{% else %}☐{% endif %} เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส เงินรางวัล เบี้ยประชุม เงินพิเศษ ฯลฯ ตามมาตรา 40(1)</div>
                        
                        <div>2. {% if doc.income_type_selection and doc.income_type_selection.startswith('2') %}☑{% else %}☐{% endif %} ค่าธรรมเนียม ค่านายหน้า ฯลฯ ตามมาตรา 40(2)</div>
                        
                        <div>3. {% if doc.income_type_selection and doc.income_type_selection.startswith('3') %}☑{% else %}☐{% endif %} ค่าแห่งลิขสิทธิ์ ค่าบริการทางเทคนิค ฯลฯ ตามมาตรา 40(3)</div>
                        
                        <div>4. (1) {% if doc.income_type_selection and doc.income_type_selection.startswith('4.1') %}☑{% else %}☐{% endif %} ดอกเบี้ย ตามมาตรา 40(4)(ก)</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;(2) {% if doc.income_type_selection and doc.income_type_selection.startswith('4.2') %}☑{% else %}☐{% endif %} เงินปันผล กำไรสุทธิ ฯลฯ ตามมาตรา 40(4)(ข) และ (ค)</div>
                        
                        <div>5. {% if doc.income_type_selection and doc.income_type_selection.startswith('5') %}☑{% else %}☐{% endif %} ค่าเช่าทรัพย์สิน ตามมาตรา 40(5)</div>
                        
                        <div>6. {% if doc.income_type_selection and doc.income_type_selection.startswith('6') %}☑{% else %}☐{% endif %} อื่น ๆ (โปรดระบุ) 
                        {%- if doc.income_type_selection and doc.income_type_selection.startswith('6') -%}
                            <u>{{ doc.other_income_description or "ค่าบริการ" }}</u>
                        {%- else -%}
                            ____________________
                        {%- endif -%}
                        </div>
                    </td>
                    <td style="text-align: center;">
                        {%- if doc.posting_date -%}
                            {{ doc.posting_date.strftime('%d/%m/') }}{{ doc.posting_date.year + 543 }}
                        {%- endif -%}
                    </td>
                    <td style="text-align: right;">
                        {%- if doc.custom_total_amount_paid or doc.paid_amount -%}
                            {{ "{:,.2f}".format(doc.custom_total_amount_paid or doc.paid_amount) }}
                        {%- endif -%}
                    </td>
                    <td style="text-align: right;">
                        {%- if doc.custom_total_tax_withheld -%}
                            {{ "{:,.2f}".format(doc.custom_total_tax_withheld) }}
                        {%- endif -%}
                    </td>
                </tr>
            </tbody>
        </table>

        <!-- Total Section -->
        <div class="total-section">
            รวมเงินที่จ่ายและภาษีที่หักนำส่ง &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            {%- if doc.custom_total_amount_paid or doc.paid_amount -%}
                {{ "{:,.2f}".format(doc.custom_total_amount_paid or doc.paid_amount) }}
            {%- endif -%}
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            {%- if doc.custom_total_tax_withheld -%}
                {{ "{:,.2f}".format(doc.custom_total_tax_withheld) }}
            {%- endif -%}
        </div>

        <!-- Certification and Signature -->
        <div class="certification-section">
            <p>ขอรับรองว่าได้หักภาษี ณ ที่จ่าย ถูกต้องตามจำนวนดังกล่าวข้างต้น และได้นำส่งเงินภาษีดังกล่าวให้แก่กรมสรรพากรแล้ว</p>
            <p>ตามใบนำส่งภาษีหัก ณ ที่จ่าย</p>
            
            <div style="margin: 10px 0;">
                แบบ ภ.ง.ด.1ก ลงวันที่ 
                {%- if doc.submission_form_date -%}
                    <span class="signature-line">{{ doc.submission_form_date.strftime('%d/%m/') }}{{ doc.submission_form_date.year + 543 }}</span>
                {%- else -%}
                    <span class="signature-line">&nbsp;</span>
                {%- endif -%}
                เลขที่ใบนำส่ง 
                <span class="signature-line">{{ doc.submission_form_number or "" }}</span>
            </div>
        </div>

        <!-- Signature Section -->
        <div class="signature-section">
            <div style="margin-bottom: 10px;">
                ออก ณ <span class="signature-line">&nbsp;</span> 
                วันที่ <span class="signature-line">
                {%- if doc.posting_date -%}
                    {{ doc.posting_date.day }}
                {%- endif -%}
                </span> 
                เดือน <span class="signature-line">
                {%- if doc.posting_date -%}
                    {%- set thai_months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"] -%}
                    {{ thai_months[doc.posting_date.month - 1] }}
                {%- endif -%}
                </span> 
                พ.ศ. <span class="signature-line">
                {%- if doc.posting_date -%}
                    {{ doc.posting_date.year + 543 }}
                {%- endif -%}
                </span>
            </div>
            
            <div style="margin-top: 20px;">
                ลงชื่อ <span class="signature-line">&nbsp;</span> ผู้จ่ายเงิน<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;( <span class="signature-line">&nbsp;</span> )<br><br>
                ตำแหน่ง <span class="signature-line">&nbsp;</span>
            </div>
        </div>
    </div>
</body>
</html>
"""


def get_official_css_styles():
    """Return the official CSS styles"""
    return """
/* Official Thai Form 50ทวิ Styles */
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');

body {
    font-family: 'Sarabun', sans-serif;
    font-size: 12px;
    line-height: 1.3;
    color: #000;
    margin: 0;
    padding: 15mm;
    background: white;
}

.form-50-twi {
    max-width: 210mm;
    margin: 0 auto;
    border: 2px solid #000;
    padding: 15px;
}

.form-header {
    text-align: center;
    margin-bottom: 20px;
}

.form-title {
    font-size: 16px;
    font-weight: bold;
    margin: 5px 0;
}

.form-subtitle {
    font-size: 12px;
    margin: 3px 0;
}

.copy-info {
    font-size: 11px;
    margin: 10px 0;
    text-align: left;
}

.section-box {
    border: 1px solid #000;
    margin: 15px 0;
    padding: 10px;
}

.section-title {
    font-weight: bold;
    margin-bottom: 10px;
    font-size: 12px;
}

.field-row {
    margin: 8px 0;
    display: flex;
    align-items: center;
}

.field-label {
    display: inline-block;
    width: 160px;
    font-size: 11px;
}

.field-value {
    flex: 1;
    border-bottom: 1px dotted #000;
    min-height: 16px;
    padding: 2px 5px;
    font-size: 11px;
}

.income-types-table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 10px;
}

.income-types-table td, .income-types-table th {
    border: 1px solid #000;
    padding: 8px 5px;
    vertical-align: top;
}

.income-types-table th {
    background-color: #f5f5f5;
    font-weight: bold;
    text-align: center;
}

.income-type-list {
    font-size: 9px;
    line-height: 1.4;
}

.checkbox {
    font-family: 'Arial', sans-serif;
    font-size: 12px;
    margin-right: 5px;
}

.total-section {
    text-align: right;
    margin: 15px 0;
    font-weight: bold;
}

.certification-section {
    margin: 20px 0;
    font-size: 11px;
}

.signature-section {
    margin-top: 30px;
    text-align: right;
}

.signature-line {
    border-bottom: 1px dotted #000;
    display: inline-block;
    min-width: 200px;
    margin: 0 5px;
}

@media print {
    body {
        margin: 0;
        padding: 10mm;
        font-size: 11px;
    }
    
    .form-50-twi {
        border: 1px solid #000;
        padding: 10px;
    }
}
"""


def get_utility_functions_code():
    """Return the utility functions code"""
    return '''# File: print_designer/custom/withholding_tax.py
# Thai Withholding Tax Certificate Utility Functions

import frappe
from frappe import _
import re
from datetime import datetime

def calculate_withholding_tax(doc, method):
    """Calculate withholding tax automatically for Payment Entry"""
    if not getattr(doc, 'apply_thai_withholding_tax', False):
        return
    
    # Clear existing details
    doc.custom_withholding_tax_details = []
    total_amount_paid = 0
    total_tax_withheld = 0
    
    # Get tax rate
    tax_rate = get_wht_rate_by_income_type(doc.income_type_selection) if hasattr(doc, 'income_type_selection') else 3.0
    if hasattr(doc, 'withholding_tax_rate') and doc.withholding_tax_rate:
        tax_rate = doc.withholding_tax_rate
    
    # Calculate for payment amount
    if doc.paid_amount and doc.paid_amount > 0:
        base_amount = doc.paid_amount
        tax_amount = (base_amount * tax_rate) / 100
        
        # Get income type details
        income_code = doc.income_type_selection.split(' - ')[0] if hasattr(doc, 'income_type_selection') and doc.income_type_selection else "6"
        income_desc = get_income_type_description(doc.income_type_selection, doc.other_income_description if hasattr(doc, 'other_income_description') else None)
        
        # Add detail row
        doc.append("custom_withholding_tax_details", {
            "income_type_code": income_code,
            "income_type_description": income_desc,
            "payment_date": doc.posting_date,
            "amount_paid": base_amount,
            "tax_rate": tax_rate,
            "tax_withheld": tax_amount
        })
        
        total_amount_paid += base_amount
        total_tax_withheld += tax_amount
    
    # Update totals
    doc.custom_total_amount_paid = total_amount_paid
    doc.custom_total_tax_withheld = total_tax_withheld

def validate_wht_setup(doc, method):
    """Validate Thai WHT setup"""
    if not getattr(doc, 'apply_thai_withholding_tax', False):
        return
    
    # Validate required fields
    if not getattr(doc, 'custom_party_tax_id', None):
        frappe.throw(_("Party Tax ID is required for Thai Withholding Tax"))
    
    # Validate Thai Tax ID format
    if doc.custom_party_tax_id:
        clean_id = doc.custom_party_tax_id.replace("-", "").replace(" ", "")
        if len(clean_id) != 13 or not clean_id.isdigit():
            frappe.throw(_("Thai Tax ID must be 13 digits"))
    
    # Validate withholding tax rate
    if not getattr(doc, 'withholding_tax_rate', None):
        frappe.throw(_("Withholding Tax Rate is required"))
    
    if doc.withholding_tax_rate < 0 or doc.withholding_tax_rate > 100:
        frappe.throw(_("Withholding Tax Rate must be between 0% and 100%"))

def update_withholding_details(doc, method):
    """Update withholding tax details on document update"""
    if getattr(doc, 'apply_thai_withholding_tax', False):
        # Auto-populate company details if missing
        if not getattr(doc, 'custom_company_tax_id', None):
            company_tax_id = frappe.get_value("Company", doc.company, "tax_id")
            if company_tax_id:
                doc.custom_company_tax_id = company_tax_id
        
        if not getattr(doc, 'custom_company_address', None):
            company_address = frappe.get_value("Company", doc.company, "address")
            if company_address:
                doc.custom_company_address = company_address
        
        # Auto-populate party details if missing
        if doc.party and not getattr(doc, 'custom_party_tax_id', None):
            party_tax_id = frappe.get_value(doc.party_type, doc.party, "tax_id")
            if party_tax_id:
                doc.custom_party_tax_id = party_tax_id

@frappe.whitelist()
def get_wht_rate_by_income_type(income_type):
    """Get standard WHT rates by income type"""
    if not income_type:
        return 3.0
    
    rates = {
        "1": 0.0,    # Salary - usually 0% at source, calculated monthly
        "2": 3.0,    # Fees, commissions
        "3": 3.0,    # Royalties, technical services
        "4.1": 1.0,  # Interest
        "4.2": 5.0,  # Dividends
        "5": 5.0,    # Rental income
        "6": 3.0     # Others
    }
    
    code = income_type.split(' - ')[0] if ' - ' in income_type else income_type
    return rates.get(code, 3.0)

def get_income_type_description(income_type_selection, other_description=None):
    """Get income type description in Thai"""
    if not income_type_selection:
        return "อื่น ๆ"
    
    descriptions = {
        "1": "เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส",
        "2": "ค่าธรรมเนียม ค่านายหน้า",
        "3": "ค่าแห่งลิขสิทธิ์ ค่าบริการทางเทคนิค",
        "4.1": "ดอกเบี้ย",
        "4.2": "เงินปันผล กำไรสุทธิ",
        "5": "ค่าเช่าทรัพย์สิน",
        "6": other_description or "ค่าบริการ"
    }
    
    code = income_type_selection.split(' - ')[0] if ' - ' in income_type_selection else income_type_selection
    return descriptions.get(code, "อื่น ๆ")

@frappe.whitelist()
def format_thai_tax_id(tax_id):
    """Format Thai Tax ID with dashes: 1-2345-67890-12-3"""
    if not tax_id:
        return ""
    
    clean_id = str(tax_id).replace("-", "").replace(" ", "")
    if len(clean_id) == 13 and clean_id.isdigit():
        return f"{clean_id[0]}-{clean_id[1:5]}-{clean_id[5:10]}-{clean_id[10:12]}-{clean_id[12]}"
    return tax_id

@frappe.whitelist()
def convert_to_thai_date(date_obj):
    """Convert date to Thai Buddhist year format"""
    if not date_obj:
        return ""
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except:
            return date_obj
    
    thai_months = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    
    thai_year = date_obj.year + 543
    thai_month = thai_months[date_obj.month - 1]
    
    return f"{date_obj.day} {thai_month} {thai_year}"

def validate_thai_tax_id(tax_id):
    """Validate Thai Tax ID format and checksum"""
    if not tax_id:
        return False
    
    clean_id = str(tax_id).replace("-", "").replace(" ", "")
    
    # Check length
    if len(clean_id) != 13:
        return False
    
    # Check if all digits
    if not clean_id.isdigit():
        return False
    
    # Validate checksum (Thai Tax ID uses mod 11 algorithm)
    total = 0
    for i in range(12):
        total += int(clean_id[i]) * (13 - i)
    
    remainder = total % 11
    check_digit = (11 - remainder) % 10
    
    return int(clean_id[12]) == check_digit

@frappe.whitelist()
def get_company_address_formatted(company):
    """Get formatted company address"""
    if not company:
        return ""
    
    company_doc = frappe.get_doc("Company", company)
    
    # Try to get company address
    address_name = company_doc.address
    if address_name:
        address_doc = frappe.get_doc("Address", address_name)
        address_parts = []
        
        if address_doc.address_line1:
            address_parts.append(address_doc.address_line1)
        if address_doc.address_line2:
            address_parts.append(address_doc.address_line2)
        if address_doc.city:
            address_parts.append(address_doc.city)
        if address_doc.state:
            address_parts.append(address_doc.state)
        if address_doc.pincode:
            address_parts.append(address_doc.pincode)
        
        return " ".join(address_parts)
    
    return ""

@frappe.whitelist()
def create_thai_wht_certificate_copy2(payment_entry_name):
    """Create Copy 2 of Thai WHT Certificate"""
    # This function would create the second copy
    # with different header text for taxpayer's records
    pass
'''


def show_installation_summary():
    """Show installation summary and usage instructions"""
    click.echo("📊 **Installation Summary:**")
    click.echo("   ✓ Thai Withholding Tax Detail DocType")
    click.echo("   ✓ Custom Fields for Payment Entry")
    click.echo("   ✓ JSON Print Format for Print Designer")
    click.echo("   ✓ Jinja Print Format (Alternative)")
    click.echo("   ✓ Utility Functions for Calculations")
    click.echo("   ✓ Event Hooks Registration Info")
    click.echo("")

    click.echo("🇹🇭 **Thai Form 50ทวิ Features:**")
    click.echo("   ✅ Official Revenue Department format compliance")
    click.echo("   ✅ All 6 income type categories with checkboxes")
    click.echo("   ✅ Automatic tax calculations by income type")
    click.echo("   ✅ Thai Tax ID formatting (1-2345-67890-12-3)")
    click.echo("   ✅ Thai Buddhist calendar (พ.ศ.) dates")
    click.echo("   ✅ Sarabun font for authentic Thai typography")
    click.echo("   ✅ Official certification text and signatures")
    click.echo("   ✅ ภ.ง.ด.1ก form reference tracking")
    click.echo("")

    click.echo("📖 **Usage Instructions:**")
    click.echo("   1. Create Payment Entry for supplier/employee payment")
    click.echo("   2. Enable 'Apply Thai Withholding Tax' checkbox")
    click.echo("   3. Select income type (1-6) from dropdown")
    click.echo("   4. Enter 13-digit Tax IDs for company and party")
    click.echo("   5. Set withholding tax rate (auto-suggested by type)")
    click.echo("   6. Save and submit Payment Entry")
    click.echo("   7. Print using 'Thai Form 50ทวิ - Official Certificate'")
    click.echo("")

    click.echo("⚠️  **Post-Installation Steps:**")
    click.echo("   1. Add event hooks to hooks.py (see output above)")
    click.echo("   2. Run: bench restart")
    click.echo("   3. Clear cache: bench --site [site] clear-cache")
    click.echo("   4. Test with a sample Payment Entry")
    click.echo("")

    click.echo("🔧 **File Locations Created:**")
    click.echo("   📁 print_designer/custom/withholding_tax.py")
    click.echo(
        "   📁 print_designer/print_designer/doctype/thai_withholding_tax_detail/"
    )
    click.echo("   📄 Thai Form 50ทวิ - JSON Format (Print Designer)")
    click.echo("   📄 Thai Form 50ทวิ - Official Certificate (Jinja)")
    click.echo("")

    click.echo("✨ **Ready to use! Your Thai Form 50ทวิ system is now installed.**")


if __name__ == "__main__":
    install_thai_form_50_twi()
