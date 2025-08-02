# Thai Form 50ทวิ - Complete User Workflow Guide

## 🎯 **Two Ways to Access Thai Form 50ทวิ**

### **Method 1: Payment Entry Extension (Recommended)**
*Generate WHT certificate directly from payment process*

### **Method 2: Dedicated DocType**
*Separate form specifically for WHT certificates*

---

## 📋 **Method 1: Payment Entry Extension Workflow**

### **Step 1: Navigate to Payment Entry**
```
Main Menu → Accounts → Payment Entry → New
```
**OR**
```
Global Search (Ctrl+K) → Type "Payment Entry" → New
```

### **Step 2: Fill Basic Payment Details**
1. **Payment Type:** Pay
2. **Party Type:** Supplier
3. **Party:** Select supplier
4. **Paid Amount:** Enter amount
5. **Paid From/To:** Select bank accounts

### **Step 3: Enable Thai WHT**
1. Scroll down to **"Thai Withholding Tax (ภาษีหัก ณ ที่จ่าย)"** section
2. ☑ Check **"Apply Thai Withholding Tax"**
3. Form expands to show WHT fields

### **Step 4: Configure WHT Details**
1. **Income Type:** Select from dropdown (1-6)
   - 1 - เงินเดือน ค่าจ้าง
   - 2 - ค่าธรรมเนียม ค่านายหน้า
   - 3 - ค่าลิขสิทธิ์ ค่าบริการทางเทคนิค
   - 4.1 - ดอกเบี้ย
   - 4.2 - เงินปันผล กำไรสุทธิ
   - 5 - ค่าเช่าทรัพย์สิน
   - 6 - อื่น ๆ (Others)

2. **Tax Rate:** Auto-populated, can modify
3. **Tax IDs:** Auto-filled from master data
4. **Addresses:** Verify company and party addresses

### **Step 5: Save and Generate Certificate**
1. **Save** the Payment Entry
2. **Submit** the document
3. Click **Print** button
4. Select **"Thai Form 50ทวิ - Official Certificate"**
5. **Download PDF** - Official certificate ready!

---

## 🏛️ **Method 2: Dedicated DocType Workflow**

### **Step 1: Add Menu Item (One-time Setup)**

**Option A: Add to Workspace**
```
Settings → Workspace → Accounting
→ Add Custom Link
→ Link Type: DocType
→ Link Name: Thai WHT Certificate
→ Save
```

**Option B: Add to Menu**
```python
# Add to hooks.py
standard_portal_menu_items = [
    {
        "title": "Thai WHT Certificate", 
        "route": "/app/thai-wht-certificate",
        "reference_doctype": "Thai WHT Certificate",
        "role": "Accounts User"
    }
]
```

### **Step 2: Navigate to WHT Certificate**
```
Main Menu → Accounting → Thai WHT Certificate → New
```
**OR**
```
Global Search (Ctrl+K) → Type "Thai WHT" → New
```

### **Step 3: Fill Certificate Details**
1. **Certificate Date:** Auto-filled (today)
2. **Tax Year:** Enter tax year
3. **Company:** Select your company
4. **Payment Entry:** Link to existing payment (optional)

### **Step 4: Fill Payer Information**
1. **Payer Name:** Auto-filled from company
2. **Payer Tax ID:** Auto-filled
3. **Payer Address:** Verify/edit

### **Step 5: Fill Payee Information**
1. **Party Type:** Supplier
2. **Party:** Select supplier
3. **Party Name:** Auto-filled
4. **Party Tax ID:** Enter 13-digit ID
5. **Party Address:** Enter address

### **Step 6: Configure Income Details**
1. **Income Type:** Select category (1-6)
2. **Other Description:** If type 6 selected
3. **Tax Rate:** Enter percentage

### **Step 7: Add Tax Details**
1. In **"Withholding Tax Details"** table, click **Add Row**
2. Fill each row:
   - **Income Type Code:** Auto-filled
   - **Description:** Auto-filled
   - **Payment Date:** Enter date
   - **Amount Paid:** Enter amount
   - **Tax Rate:** Auto-filled
   - **Tax Withheld:** Auto-calculated

### **Step 8: Save and Submit**
1. **Save** the certificate
2. **Submit** the document
3. Click **Print** button
4. **Download PDF** certificate

---

## ⚙️ **Setting Up Quick Access**

### **1. Add to Workspaces**

Create custom workspace for Thai tax operations:

```python
# File: print_designer/fixtures/workspace.json
{
    "name": "Thai Tax Operations",
    "module": "Print Designer", 
    "label": "Thai Tax",
    "icon": "tax",
    "color": "#ff6b6b",
    "shortcuts": [
        {
            "type": "DocType",
            "label": "Payment Entry",
            "doc_type": "Payment Entry"
        },
        {
            "type": "DocType", 
            "label": "Thai WHT Certificate",
            "doc_type": "Thai WHT Certificate"
        },
        {
            "type": "Report",
            "label": "WHT Certificate Register", 
            "report_name": "WHT Certificate Register"
        }
    ]
}
```

### **2. Add Dashboard Cards**

```python
# File: print_designer/custom/dashboard_cards.py

@frappe.whitelist()
def get_thai_wht_dashboard_data():
    """Get data for Thai WHT dashboard cards"""
    
    # This month's WHT
    this_month = frappe.db.sql("""
        SELECT COUNT(*) as count, SUM(custom_total_tax_withheld) as total
        FROM `tabPayment Entry`
        WHERE apply_thai_withholding_tax = 1
        AND MONTH(posting_date) = MONTH(CURDATE())
        AND YEAR(posting_date) = YEAR(CURDATE())
        AND docstatus = 1
    """, as_dict=1)[0]
    
    # Pending submissions
    pending = frappe.db.count("Payment Entry", {
        "apply_thai_withholding_tax": 1,
        "submission_form_date": ["is", "not set"],
        "docstatus": 1
    })
    
    return {
        "this_month_count": this_month.count or 0,
        "this_month_total": this_month.total or 0,
        "pending_submissions": pending
    }
```

### **3. Create Shortcuts**

**Desktop Icons:**
```
Settings → Desktop Settings
→ Add Module: Thai Tax Operations
→ Icon: Tax icon
→ Color: Orange
```

**Quick Links:**
```
Settings → Navbar Settings
→ Add Custom Link
→ Label: "ฟอร์ม 50ทวิ"
→ URL: /app/payment-entry/new
```

---

## 🎯 **User Experience Comparison**

| Aspect | Payment Entry Method | Dedicated DocType Method |
|--------|---------------------|--------------------------|
| **Navigation** | 1 click (existing menu) | 2-3 clicks (custom menu) |
| **Data Entry** | Integrated workflow | Separate form |
| **Learning Curve** | Minimal (familiar UI) | Moderate (new interface) |
| **Data Consistency** | ✅ Automatic sync | ⚠️ Manual entry |
| **User Workflow** | ✅ Single process | ⚠️ Two-step process |
| **Form Complexity** | ⚠️ Many fields | ✅ Focused interface |

---

## 📱 **Mobile Access**

For mobile users:

### **ERPNext Mobile App:**
1. Download ERPNext mobile app
2. Login to your instance
3. Navigate: **Accounts → Payment Entry**
4. Enable WHT section
5. Generate certificate

### **Mobile Browser:**
1. Open browser on mobile
2. Go to your ERPNext URL
3. Switch to **Desktop View** for full functionality
4. Follow same workflow as desktop

---

## 🎯 **Recommended User Training**

### **For Accounts Team:**
1. **Show Payment Entry workflow** (Method 1)
2. **Practice with test suppliers**
3. **Verify certificate output**
4. **Learn report access**

### **Training Checklist:**
- [ ] Navigate to Payment Entry
- [ ] Enable Thai WHT section
- [ ] Fill income type and tax rate
- [ ] Verify Tax ID formatting
- [ ] Generate and print certificate
- [ ] Access WHT Certificate Register report
- [ ] Export reports to Excel

---

## 🚀 **Quick Start Guide**

### **For New Users:**
1. **Create test supplier** with Thai Tax ID
2. **Make sample payment** with WHT enabled
3. **Generate certificate** and verify format
4. **Check report** shows the entry
5. **Export to Excel** for review

### **Daily Workflow:**
1. **Morning:** Check pending certificates in report
2. **Process payments:** Enable WHT for applicable suppliers
3. **Generate certificates:** Print and file
4. **Monthly:** Export register for tax submission

The **Payment Entry extension method** is recommended for most users as it provides the smoothest, most integrated workflow!

Then tell me what this file does "print_designer/commands/install_thai_form_50_twi.py"

● Looking at the file
  /home/frappe/frappe-bench/apps/print_designer/print_designer/commands/install_thai_form_50_twi.py, this is
  a comprehensive installation command that sets up the complete Thai Form 50ทวิ (Withholding Tax Certificate)
   system. Here's what it does:

  🎯 Main Purpose:

  This file creates a complete Thai withholding tax certificate system that integrates with ERPNext's Payment
   Entry workflow.

  📋 What It Installs:

  1. Thai Withholding Tax Detail DocType

  - Creates a child table DocType for storing multiple withholding tax entries
  - Fields: income_type_code, income_type_description, payment_date, amount_paid, tax_rate, tax_withheld
  - Permissions for System Manager, Accounts Manager, Accounts User

  2. Payment Entry Custom Fields

  Creates the entire Thai WHT section mentioned in the workflow document:
  - apply_thai_withholding_tax - Checkbox to enable WHT
  - income_type_selection - Dropdown with 6 Thai income types
  - withholding_tax_rate - Tax rate percentage
  - custom_company_tax_id - Company's Thai tax ID
  - custom_party_tax_id - Supplier's Thai tax ID
  - custom_withholding_tax_details - Table linking to child DocType
  - custom_total_amount_paid - Calculated total
  - custom_total_tax_withheld - Calculated tax amount
  - submission_form_number - ภ.ง.ด.1ก form reference
  - submission_form_date - Tax submission date

  3. Two Print Formats

  - JSON Format - For Print Designer visual editor
  - Jinja Format - Traditional HTML template with complete Thai Form 50ทวิ layout

  4. WHT Certificate Register Report

  - Complete Script Report with filters (date range, party, income type, submission status)
  - Chart data showing tax withheld by income type
  - Summary statistics (total certificates, amounts, rates)
  - Export and batch generation capabilities

  5. Utility Functions

  Creates withholding_tax.py with helper functions:
  - Tax rate calculations by income type
  - Thai Tax ID formatting (1-2345-67890-12-3)
  - Thai Buddhist calendar date conversion
  - WHT certificate data processing

  ⚙️ How It Works:

  Installation Process:

  bench --site [site-name] execute print_designer.commands.install_thai_form_50_twi.install_thai_form_50_twi

  Step-by-Step Execution:

  1. Creates child DocType for withholding tax details
  2. Installs custom fields on Payment Entry (the missing piece!)
  3. Creates JSON print format for Print Designer
  4. Creates Jinja print format as alternative
  5. Sets up utility functions for calculations
  6. Creates WHT register report for tracking certificates

  🎯 What This Enables:

  After running this command, the exact workflow described in THAI_FORM_50TWI_COMPLETE_USER_WORKFLOW.md
  becomes functional:

  1. Payment Entry Extension Method ✅ - All custom fields will be available
  2. Thai WHT Section ✅ - Users can check "Apply Thai Withholding Tax"
  3. Income Type Dropdown ✅ - All 6 categories (1-6) with Thai descriptions
  4. Auto-calculations ✅ - Tax rates and amounts calculated automatically
  5. Print Certificates ✅ - Official Thai Form 50ทวิ format
  6. Report Generation ✅ - WHT Certificate Register for tracking

  🚀 Current Status:

  - File exists ✅ - Complete installation code ready
  - Not executed yet ❌ - Custom fields not installed on Payment Entry
  - Backend ready ✅ - All infrastructure code complete

  Bottom Line:

  This installation file is the missing link that transforms the codebase from having all the backend
  infrastructure to having a fully functional Thai withholding tax system that works exactly as described in
  the user workflow document. It creates all the Payment Entry custom fields that enable the Method 1
  workflow.