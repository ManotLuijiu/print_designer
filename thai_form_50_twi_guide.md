# Thai Form 50 ทวิ (Withholding Tax Certificate) - Complete Guide

This guide covers the Thai Form 50 ทวิ (หนังสือรับรองการหักภาษี ณ ที่จ่าย) implementation in Print Designer for ERPNext.

## ✅ Installation Complete

The Thai Form 50 ทวิ formats have been successfully installed for:
- **Payment Entry**
- **Purchase Invoice** 
- **Journal Entry**

## 🎯 What is Form 50 ทวิ?

Form 50 ทวิ is the official Thai withholding tax certificate required by Thai Revenue Department for:
- **Recording tax withheld** from payments to suppliers/employees
- **Tax compliance** documentation
- **Evidence of tax collection** for both payer and payee
- **Supporting documents** for tax returns

## 📋 Form Structure

### Section 1: Payer Information (ผู้จ่ายเงิน)
- Company name and tax ID
- Company address
- Automatically populated from ERPNext Company master

### Section 2: Payee Information (ผู้รับเงิน)
- Supplier/Employee name and tax ID
- Address information
- Automatically populated from Party master

### Section 3: Payment Period (ระยะเวลาการจ่าย)
- Month and year of payment
- Uses document posting date

### Section 4: Income Type (ประเภทเงินได้)
Checkboxes for:
- ✅ **เงินเดือน ค่าจ้าง** (Salary, wages, allowances, bonus)
- ✅ **ค่าจ้างทำของ** (Service fees, rent, transportation)
- ✅ **ค่านายหน้า** (Brokerage and referral fees)
- ✅ **ค่าเช่าทรัพย์สิน** (Property rental)
- ✅ **ค่าขายทรัพย์สิน** (Asset sales)
- ✅ **อื่นๆ** (Others - with description field)

### Section 5: Tax Calculation Table
- Payment date
- Income description
- Amount paid
- Taxable amount
- Tax rate (%)
- Tax withheld amount

### Section 6: Signatures
- Tax withholding agent signature
- Tax recipient signature
- Date fields

## 🛠️ Usage Instructions

### For Payment Entry
```
1. Create Payment Entry with supplier/employee payment
2. Go to Print → Select "Payment Entry Form 50 ทวิ"
3. Form auto-fills with:
   - Company and party information
   - Payment amounts and dates
   - Calculated withholding tax (default 3%)
   - Reference documents
```

### For Purchase Invoice
```
1. Create Purchase Invoice with withholding tax
2. Go to Print → Select "Purchase Invoice Form 50 ทวิ"
3. Form shows:
   - Invoice details and amounts
   - Supplier information
   - Tax calculations
   - Proper Thai format
```

### For Journal Entry
```
1. Create Journal Entry for tax transactions
2. Go to Print → Select "Journal Entry Form 50 ทวิ"
3. Certificate includes:
   - Account-based calculations
   - Party information from journal
   - Tax withholding details
```

## 💡 Key Features

### ✅ **Automatic Data Population**
- Company info from Company master
- Party details from Supplier/Employee
- Tax ID formatting (13-digit Thai format)
- Address information

### ✅ **Smart Tax Calculations**
- Default 3% withholding rate
- Automatic taxable amount calculation
- Total calculations
- Multiple payment handling

### ✅ **Thai Compliance**
- Official Form 50 ทวิ layout
- Thai and English labels
- Buddhist calendar year (พ.ศ.)
- Proper signature areas
- Revenue Department approved format

### ✅ **Multi-Document Support**
- Works with Payment Entry references
- Handles multiple invoices
- Aggregates tax calculations
- Shows individual payment lines

## 🔧 Customization Options

### Tax Rates
The default withholding rate is 3%, but you can modify for different income types:

```python
# In the template, modify:
{%- set withholding_rate = 3.0 -%}  # Change this value

# For different income types:
{%- if doc.party_type == "Employee" -%}
    {%- set withholding_rate = 5.0 -%}  # Employee tax rate
{%- elif doc.party_type == "Supplier" -%}
    {%- set withholding_rate = 3.0 -%}  # Supplier tax rate
{%- endif -%}
```

### Income Type Detection
Modify the checkbox logic to auto-detect income types:

```python
# Auto-select based on party type
{{ checkbox(doc.party_type == "Employee") }}  # Salary checkbox
{{ checkbox(doc.party_type == "Supplier") }}  # Service checkbox
```

### Company Information
Ensure your Company master has:
- **Tax ID** (13-digit Thai format)
- **Complete address**
- **Company name in Thai**

## 📊 Real-World Examples

### Example 1: Consultant Payment
```
Company: ABC Corp Ltd.
Consultant: John Doe (Freelancer)
Service Fee: 10,000 THB
Withholding Tax (3%): 300 THB
Net Payment: 9,700 THB

Form 50 ทวิ shows:
- Payer: ABC Corp Ltd.
- Payee: John Doe
- Income Type: ค่าจ้างทำของ (Service fees)
- Taxable Amount: 10,000 THB
- Tax Withheld: 300 THB
```

### Example 2: Employee Bonus
```
Company: XYZ Co., Ltd.
Employee: สมใจ รักการทำงาน
Bonus: 50,000 THB
Withholding Tax (5%): 2,500 THB
Net Payment: 47,500 THB

Form 50 ทวิ shows:
- Payer: XYZ Co., Ltd.
- Payee: สมใจ รักการทำงาน
- Income Type: เงินเดือน ค่าจ้าง (Salary/wages)
- Taxable Amount: 50,000 THB
- Tax Withheld: 2,500 THB
```

### Example 3: Rental Payment
```
Company: DEF Corp
Landlord: Property Owner Ltd.
Monthly Rent: 30,000 THB
Withholding Tax (5%): 1,500 THB
Net Payment: 28,500 THB

Form 50 ทวิ shows:
- Payer: DEF Corp
- Payee: Property Owner Ltd.
- Income Type: ค่าเช่าทรัพย์สิน (Property rental)
- Taxable Amount: 30,000 THB
- Tax Withheld: 1,500 THB
```

## ⚠️ Important Compliance Notes

### Legal Requirements
- **Must be issued** for all withholding tax transactions
- **Original to payee**, copy for payer records
- **Submit to Revenue Department** with monthly tax returns
- **Keep for 5 years** as per Thai law

### Tax ID Requirements
- **Company Tax ID**: 13-digit format (0-0000-00000-00-0)
- **Individual Tax ID**: 13-digit citizen ID or 10-digit tax ID
- **Foreign entities**: Special tax ID format

### Common Tax Rates
- **Employees**: 0-35% (progressive)
- **Service providers**: 3%
- **Professional services**: 5%
- **Rent (companies)**: 5%
- **Rent (individuals)**: 5%
- **Interest**: 15%
- **Royalties**: 5%

## 🔄 Updates and Maintenance

### Reinstall/Update Forms
```bash
bench --site [site-name] install-thai-form-50-twi
```

### Check Installed Formats
Go to: **Settings → Print Format** and search for "Form 50 ทวิ"

### Backup Forms
Export your customized formats before updates:
1. Go to Print Format
2. Export the format
3. Re-import after updates if needed

## 🆘 Troubleshooting

### Form Not Showing Data?
- ✅ Check party has tax ID configured
- ✅ Verify company tax ID is set
- ✅ Ensure posting date is available
- ✅ Check document is saved/submitted

### Wrong Tax Calculations?
- ✅ Verify tax rates in template
- ✅ Check document amounts
- ✅ Review withholding tax setup
- ✅ Confirm income type classification

### Missing Thai Fonts?
- ✅ Install Sarabun font system-wide
- ✅ Use Print Designer font settings
- ✅ Check browser font support

### Layout Issues?
- ✅ Use Print Designer to adjust
- ✅ Modify CSS for spacing
- ✅ Test print preview
- ✅ Check page margins

## 📞 Support

This Form 50 ทวิ implementation provides:
- ✅ **Official compliance** with Thai Revenue Department
- ✅ **Automatic calculations** and data population
- ✅ **Professional formatting** for business use
- ✅ **Multi-document support** for complex scenarios
- ✅ **Customizable layout** via Print Designer

The forms are designed to meet Thai tax law requirements while integrating seamlessly with ERPNext workflows.