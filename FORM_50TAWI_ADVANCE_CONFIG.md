# Thai Form 50ทวิ - Advanced Configuration Guide

## 🔧 **Post-Installation Configuration**

### 1. **Company Setup for Thai Operations**

**File Location: Setup → Company**

Add these fields to your Company master:

```python
# Custom fields for Company (add via Customize Form)
{
    "fieldname": "thai_company_settings_section",
    "label": "Thai Company Settings",
    "fieldtype": "Section Break",
    "insert_after": "tax_id"
},
{
    "fieldname": "thai_company_name", 
    "label": "Thai Company Name",
    "fieldtype": "Data",
    "insert_after": "thai_company_settings_section"
},
{
    "fieldname": "thai_address_line1",
    "label": "Thai Address Line 1", 
    "fieldtype": "Data",
    "insert_after": "thai_company_name"
},
{
    "fieldname": "thai_address_line2",
    "label": "Thai Address Line 2",
    "fieldtype": "Data", 
    "insert_after": "thai_address_line1"
},
{
    "fieldname": "revenue_office",
    "label": "Revenue Office",
    "fieldtype": "Data",
    "insert_after": "thai_address_line2"
}
```

### 2. **Supplier Setup for WHT**

**File Location: Buying → Supplier**

```python
# Custom fields for Supplier
{
    "fieldname": "thai_wht_section",
    "label": "Thai Withholding Tax Settings", 
    "fieldtype": "Section Break",
    "insert_after": "tax_id"
},
{
    "fieldname": "default_income_type",
    "label": "Default Income Type",
    "fieldtype": "Select",
    "options": "1\n2\n3\n4.1\n4.2\n5\n6",
    "insert_after": "thai_wht_section"
},
{
    "fieldname": "default_wht_rate",
    "label": "Default WHT Rate (%)",
    "fieldtype": "Percent",
    "insert_after": "default_income_type"
},
{
    "fieldname": "thai_supplier_name",
    "label": "Thai Supplier Name", 
    "fieldtype": "Data",
    "insert_after": "default_wht_rate"
},
{
    "fieldname": "is_non_resident",
    "label": "Non-Resident for Tax",
    "fieldtype": "Check",
    "insert_after": "thai_supplier_name"
}
```

### 3. **WHT Settings DocType**

Create a settings DocType for system-wide configuration:

**File Location: `print_designer/print_designer/doctype/thai_wht_settings/`**

```json
{
    "doctype": "DocType",
    "name": "Thai WHT Settings",
    "module": "Print Designer", 
    "is_single": 1,
    "fields": [
        {
            "fieldname": "general_section",
            "label": "General Settings",
            "fieldtype": "Section Break"
        },
        {
            "fieldname": "auto_calculate_wht",
            "label": "Auto Calculate WHT",
            "fieldtype": "Check",
            "default": 1
        },
        {
            "fieldname": "require_tax_id",
            "label": "Require Tax ID for WHT",
            "fieldtype": "Check", 
            "default": 1
        },
        {
            "fieldname": "validate_tax_id_checksum",
            "label": "Validate Tax ID Checksum",
            "fieldtype": "Check",
            "default": 1
        },
        {
            "fieldname": "rates_section", 
            "label": "Default Tax Rates",
            "fieldtype": "Section Break"
        },
        {
            "fieldname": "rate_section_40_1",
            "label": "Section 40(1) - Salary (%)",
            "fieldtype": "Percent",
            "default": 0
        },
        {
            "fieldname": "rate_section_40_2",
            "label": "Section 40(2) - Fees (%)", 
            "fieldtype": "Percent",
            "default": 3
        },
        {
            "fieldname": "rate_section_40_3",
            "label": "Section 40(3) - Royalties (%)",
            "fieldtype": "Percent", 
            "default": 3
        },
        {
            "fieldname": "rate_section_40_4a",
            "label": "Section 40(4a) - Interest (%)",
            "fieldtype": "Percent",
            "default": 1
        },
        {
            "fieldname": "rate_section_40_4bc",
            "label": "Section 40(4b,c) - Dividends (%)",
            "fieldtype": "Percent",
            "default": 5
        },
        {
            "fieldname": "rate_section_40_5",
            "label": "Section 40(5) - Rent (%)",
            "fieldtype": "Percent", 
            "default": 5
        },
        {
            "fieldname": "rate_others",
            "label": "Others - Default (%)",
            "fieldtype": "Percent",
            "default": 3
        }
    ]
}
```

## 📊 **Advanced Features**

### 1. **Batch WHT Certificate Generation**

**File Location: `print_designer/custom/batch_wht_certificates.py`**

```python
import frappe
from frappe import _

@frappe.whitelist()
def generate_batch_wht_certificates(filters):
    """Generate WHT certificates for multiple payments"""
    
    # Get payment entries with WHT
    payments = frappe.get_list("Payment Entry", 
        filters={
            "apply_thai_withholding_tax": 1,
            "docstatus": 1,
            **filters
        },
        fields=["name", "party", "paid_amount", "posting_date"]
    )
    
    certificates = []
    for payment in payments:
        # Generate certificate for each payment
        doc = frappe.get_doc("Payment Entry", payment.name)
        pdf = frappe.get_print("Payment Entry", payment.name, 
                              "Thai Form 50ทวิ - Official Certificate", 
                              as_pdf=True)
        
        certificates.append({
            "payment": payment.name,
            "party": payment.party, 
            "amount": payment.paid_amount,
            "pdf": pdf
        })
    
    return certificates

@frappe.whitelist() 
def create_wht_summary_report(from_date, to_date):
    """Create summary report of all WHT for a period"""
    
    sql = """
        SELECT 
            pe.name,
            pe.party,
            pe.posting_date,
            pe.income_type_selection,
            pe.custom_total_amount_paid,
            pe.custom_total_tax_withheld,
            pe.custom_party_tax_id
        FROM `tabPayment Entry` pe
        WHERE pe.apply_thai_withholding_tax = 1
        AND pe.docstatus = 1  
        AND pe.posting_date BETWEEN %s AND %s
        ORDER BY pe.posting_date
    """
    
    data = frappe.db.sql(sql, (from_date, to_date), as_dict=1)
    
    # Calculate totals
    total_paid = sum(d.custom_total_amount_paid or 0 for d in data)
    total_tax = sum(d.custom_total_tax_withheld or 0 for d in data)
    
    return {
        "data": data,
        "total_paid": total_paid,
        "total_tax": total_tax,
        "count": len(data)
    }
```

### 2. **WHT Dashboard**

**File Location: `print_designer/print_designer/page/wht_dashboard/`**

Create a dashboard page for WHT overview:

```html
<!-- wht_dashboard.html -->
<div class="wht-dashboard">
    <div class="row">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body text-center">
                    <h5>This Month</h5>
                    <h3 class="text-primary" id="month-total">฿0</h3>
                    <small>Total WHT</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body text-center">
                    <h5>This Year</h5>
                    <h3 class="text-success" id="year-total">฿0</h3>
                    <small>Total WHT</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body text-center">
                    <h5>Certificates</h5>
                    <h3 class="text-info" id="cert-count">0</h3>
                    <small>Issued</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card">
                <div class="card-body text-center">
                    <h5>Pending</h5>
                    <h3 class="text-warning" id="pending-count">0</h3>
                    <small>To Submit</small>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h6>WHT by Income Type</h6>
                </div>
                <div class="card-body">
                    <canvas id="income-type-chart"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h6>Monthly Trend</h6>
                </div>
                <div class="card-body">
                    <canvas id="monthly-trend-chart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 3. **Custom Reports**

**File Location: `print_designer/print_designer/report/`**

#### A. **WHT Certificate Register**

```python
# wht_certificate_register.py
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
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
            "fieldname": "custom_party_tax_id",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Income Type"), 
            "fieldname": "income_type_selection",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Amount Paid"),
            "fieldname": "custom_total_amount_paid",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Tax Withheld"),
            "fieldname": "custom_total_tax_withheld", 
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Form Number"),
            "fieldname": "submission_form_number",
            "fieldtype": "Data",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = "WHERE pe.apply_thai_withholding_tax = 1 AND pe.docstatus = 1"
    
    if filters.get("from_date"):
        conditions += f" AND pe.posting_date >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        conditions += f" AND pe.posting_date <= '{filters.get('to_date')}'"
    if filters.get("party"):
        conditions += f" AND pe.party = '{filters.get('party')}'"
        
    sql = f"""
        SELECT 
            pe.posting_date,
            pe.name,
            pe.party,
            pe.custom_party_tax_id,
            pe.income_type_selection,
            pe.custom_total_amount_paid,
            pe.custom_total_tax_withheld,
            pe.submission_form_number
        FROM `tabPayment Entry` pe
        {conditions}
        ORDER BY pe.posting_date DESC
    """
    
    return frappe.db.sql(sql, as_dict=1)
```

### 4. **Integration with Accounting**

**File Location: `print_designer/custom/accounting_integration.py`**

```python
import frappe
from frappe import _

def create_wht_journal_entry(payment_entry):
    """Create automatic journal entry for WHT"""
    
    if not payment_entry.apply_thai_withholding_tax:
        return
        
    wht_account = frappe.get_single("Thai WHT Settings").wht_payable_account
    if not wht_account:
        frappe.throw(_("Please set WHT Payable Account in Thai WHT Settings"))
    
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.posting_date = payment_entry.posting_date
    je.company = payment_entry.company
    je.remark = f"WHT for Payment Entry {payment_entry.name}"
    
    # Credit WHT Payable
    je.append("accounts", {
        "account": wht_account,
        "credit_in_account_currency": payment_entry.custom_total_tax_withheld,
        "party_type": payment_entry.party_type,
        "party": payment_entry.party
    })
    
    # Debit Expense Account  
    expense_account = payment_entry.paid_to
    je.append("accounts", {
        "account": expense_account,
        "debit_in_account_currency": payment_entry.custom_total_tax_withheld
    })
    
    je.save()
    je.submit()
    
    return je.name

@frappe.whitelist()
def get_wht_balance_for_party(party, party_type):
    """Get outstanding WHT balance for a party"""
    
    sql = """
        SELECT SUM(custom_total_tax_withheld) as total_wht
        FROM `tabPayment Entry`
        WHERE apply_thai_withholding_tax = 1
        AND docstatus = 1
        AND party = %s
        AND party_type = %s
    """
    
    result = frappe.db.sql(sql, (party, party_type), as_dict=1)
    return result[0].total_wht if result else 0
```

## 🔍 **Testing & Validation**

### 1. **Test Cases**

Create comprehensive test cases:

**File Location: `print_designer/tests/test_thai_wht.py`**

```python
import frappe
import unittest
from print_designer.custom.withholding_tax import format_thai_tax_id, validate_thai_tax_id

class TestThaiWHT(unittest.TestCase):
    
    def test_tax_id_formatting(self):
        """Test Thai Tax ID formatting"""
        
        # Test valid 13-digit ID
        result = format_thai_tax_id("1234567890123")
        self.assertEqual(result, "1-2345-67890-12-3")
        
        # Test ID with existing dashes
        result = format_thai_tax_id("1-2345-67890-12-3")
        self.assertEqual(result, "1-2345-67890-12-3")
        
        # Test invalid length
        result = format_thai_tax_id("12345")
        self.assertEqual(result, "12345")  # Returns original
    
    def test_tax_id_validation(self):
        """Test Tax ID checksum validation"""
        
        # Test valid ID (example)
        valid = validate_thai_tax_id("1234567890129")
        self.assertTrue(valid)
        
        # Test invalid checksum
        invalid = validate_thai_tax_id("1234567890123")
        self.assertFalse(invalid)
    
    def test_wht_calculation(self):
        """Test WHT calculation logic"""
        
        # Create test payment entry
        payment = frappe.new_doc("Payment Entry")
        payment.payment_type = "Pay"
        payment.party_type = "Supplier"
        payment.party = "Test Supplier"
        payment.paid_amount = 10000
        payment.apply_thai_withholding_tax = 1
        payment.income_type_selection = "2 - ค่าธรรมเนียม ค่านายหน้า"
        payment.withholding_tax_rate = 3.0
        
        # Test calculation
        from print_designer.custom.withholding_tax import calculate_withholding_tax
        calculate_withholding_tax(payment, None)
        
        self.assertEqual(payment.custom_total_amount_paid, 10000)
        self.assertEqual(payment.custom_total_tax_withheld, 300)
```

### 2. **Performance Optimization**

```python
# File: print_designer/custom/performance.py

@frappe.whitelist()
def optimize_wht_queries():
    """Add indexes for better performance"""
    
    indexes = [
        "ALTER TABLE `tabPayment Entry` ADD INDEX idx_thai_wht (apply_thai_withholding_tax, posting_date)",
        "ALTER TABLE `tabPayment Entry` ADD INDEX idx_party_tax_id (custom_party_tax_id)",
        "ALTER TABLE `tabPayment Entry` ADD INDEX idx_income_type (income_type_selection)"
    ]
    
    for index in indexes:
        try:
            frappe.db.sql(index)
        except Exception as e:
            if "Duplicate key name" not in str(e):
                frappe.log_error(f"Index creation failed: {str(e)}")

@frappe.whitelist() 
def cache_wht_settings():
    """Cache WHT settings for faster access"""
    
    settings = frappe.get_single("Thai WHT Settings")
    
    cache_data = {
        "rates": {
            "1": settings.rate_section_40_1,
            "2": settings.rate_section_40_2, 
            "3": settings.rate_section_40_3,
            "4.1": settings.rate_section_40_4a,
            "4.2": settings.rate_section_40_4bc,
            "5": settings.rate_section_40_5,
            "6": settings.rate_others
        },
        "auto_calculate": settings.auto_calculate_wht,
        "require_tax_id": settings.require_tax_id
    }
    
    frappe.cache().set_value("thai_wht_settings", cache_data)
    return cache_data
```

## 🚀 **Production Deployment**

### 1. **Pre-Production Checklist**

- [ ] ✅ All custom fields created
- [ ] ✅ Print formats tested with sample data
- [ ] ✅ Tax calculations verified
- [ ] ✅ Tax ID validation working
- [ ] ✅ PDF output matches official format
- [ ] ✅ Event hooks functioning
- [ ] ✅ Error handling tested
- [ ] ✅ Permissions configured
- [ ] ✅ User training completed

### 2. **Backup Strategy**

```bash
# Before deployment
bench --site [site] backup --with-files

# After deployment  
bench --site [site] backup --with-files
```

### 3. **Monitoring**

Set up monitoring for WHT operations:

```python
# File: print_designer/custom/monitoring.py

@frappe.whitelist()
def wht_health_check():
    """Monitor WHT system health"""
    
    checks = {
        "custom_fields_exist": check_custom_fields(),
        "print_formats_exist": check_print_formats(), 
        "doctypes_exist": check_doctypes(),
        "recent_certificates": count_recent_certificates(),
        "errors_today": count_today_errors()
    }
    
    return checks

def check_custom_fields():
    """Check if all custom fields exist"""
    required_fields = [
        "apply_thai_withholding_tax",
        "income_type_selection", 
        "custom_party_tax_id",
        "custom_total_tax_withheld"
    ]
    
    for field in required_fields:
        if not frappe.db.exists("Custom Field", {"fieldname": field, "dt": "Payment Entry"}):
            return False
    return True
```

This completes the comprehensive Thai Form 50ทวิ implementation with all advanced features, testing, and production considerations!
