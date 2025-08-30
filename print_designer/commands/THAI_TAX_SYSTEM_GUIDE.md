# Thai Tax System for Payment Entry - Complete Guide

## 🇹🇭 Overview

Complete Thai tax system for Payment Entry processing that handles VAT, WHT (Withholding Tax), and Construction Retention in a single unified workflow.

### Case Study: Project 100, VAT 7%, WHT 3%, Retention 5%

**Sales Invoice (Tax Invoice)**:
```
Dr. Accounts Receivable    107
    Cr. Income                 100
    Cr. Output VAT - Undue       7
```

**Payment Entry (Receipt)**:
```
Dr. Cash/Bank                 99  ← Net cash received
Dr. Construction Retention     5  ← Asset we hold
Dr. WHT - Assets               3  ← Tax credit asset  
Dr. Output VAT - Undue         7  ← Clear undue VAT
    Cr. Accounts Receivable        107  ← Clear receivable
    Cr. Output VAT                   7  ← Register due VAT
```

## 📋 Installation

### 1. Install Thai Tax Fields
```bash
# Install all Thai tax fields (VAT + WHT + Retention)
bench execute print_designer.commands.install_payment_entry_retention_fields.install_payment_entry_retention_fields_direct

# Verify installation
bench execute print_designer.commands.install_payment_entry_retention_fields.check_payment_entry_retention_fields_direct
```

### 2. Verify Field Installation
Expected fields in **Payment Entry**:
- `retention_summary_section`, `has_retention`, `total_retention_amount`
- `net_payment_after_retention`, `retention_account`  
- `has_thai_taxes`, `total_wht_amount`, `total_vat_undue_amount`
- `wht_account`, `output_vat_undue_account`, `output_vat_account`

Expected fields in **Payment Entry Reference**:
- `has_retention`, `retention_amount`, `retention_percentage`
- `wht_amount`, `wht_percentage`, `vat_undue_amount`
- `net_payable_amount`

## 🏗️ System Architecture

### Key Components

1. **Sales Invoice Integration**: 
   - Retention: `custom_subject_to_retention`, `custom_retention_amount`
   - WHT: `subject_to_wht`, `custom_withholding_tax_amount`
   - VAT: Sales Taxes and Charges with "Output VAT - Undue" account

2. **Payment Entry Processing**:
   - Automatic detection of Thai tax components
   - Proportional calculation for partial payments
   - Multi-account GL entry creation

3. **GL Entry Pattern**:
   - Retention → **Dr. Asset** (money we hold)
   - WHT → **Dr. Asset** (tax credit we claim)
   - VAT → **Dr. Undue Liability** + **Cr. Due Liability** (conversion)

## 🔧 Configuration Required

### Company Settings
Configure these accounts in Company master:
- `default_retention_account` → Asset account (e.g., "Construction Retention")
- `default_wht_account` → Asset account (e.g., "WHT - Assets")
- `default_output_vat_undue_account` → Liability account (e.g., "Output VAT - Undue")
- `default_output_vat_account` → Liability account (e.g., "Output VAT")

### Sales Invoice Setup
1. **VAT Setup**: Add to Sales Taxes and Charges
   - Account Head: "Output VAT - Undue" 
   - Rate: 7%

2. **WHT Setup**: Customer configuration
   - Enable `subject_to_wht`
   - Set `custom_wht_rate` (e.g., 3%)

3. **Retention Setup**: Invoice level
   - Enable `custom_subject_to_retention`
   - Set `custom_retention` percentage (e.g., 5%)

## 💼 Usage Workflow

### Step 1: Create Sales Invoice with Thai Taxes
```
Project Amount: ฿100.00
+ VAT 7%:       ฿7.00
= Grand Total:  ฿107.00

Thai Tax Details:
- Retention 5%: ฿5.00 (of net amount)
- WHT 3%:       ฿3.00 (of net amount)  
- VAT Undue:    ฿7.00 (from taxes table)
```

### Step 2: Create Payment Entry
1. Select "Payment Entry" → "Receive"
2. Choose Customer and add invoice reference
3. System automatically calculates:
   - Total amounts for each tax component
   - Net cash payment: ฿99.00 (107 - 5 - 3)
   - Accounts from Company configuration

### Step 3: Submit Payment Entry
System creates GL entries:
```
Dr. Cash/Bank                 99.00
Dr. Construction Retention     5.00
Dr. WHT - Assets               3.00  
Dr. Output VAT - Undue         7.00
    Cr. Accounts Receivable       107.00
    Cr. Output VAT                  7.00
```

## 🧪 Test Scenarios

### Test Case 1: Full Thai Tax Invoice
```bash
# Create test Sales Invoice with all three tax components
# Expected: VAT ฿7, WHT ฿3, Retention ฿5, Net Payment ฿99
```

### Test Case 2: Partial Payment  
```bash
# Create Payment Entry for 50% of invoice
# Expected: Proportional calculation of all tax components
```

### Test Case 3: Multiple Invoices
```bash
# Payment Entry referencing multiple invoices with different tax combinations
# Expected: Aggregated totals with proper GL entries
```

### Test Case 4: Cancellation
```bash
# Cancel submitted Payment Entry
# Expected: All GL entries reversed properly
```

## 🔍 Validation Rules

### Automatic Validations
1. **Account Types**:
   - Retention Account: Asset/Receivable only
   - WHT Account: Asset only  
   - VAT Accounts: Liability only

2. **Amount Calculations**:
   - Total amounts match sum of references
   - No negative payment amounts
   - Proper proportional calculations

3. **Required Fields**:
   - Accounts required when respective amounts > 0
   - Company consistency across accounts

## 🚨 Troubleshooting

### Common Issues

1. **"Required Thai tax accounts missing"**
   - Solution: Configure Company default accounts
   - Command: Company Settings → Accounting → Default Accounts

2. **"Account type validation failed"**
   - Solution: Ensure correct account types:
     - Retention: Asset/Receivable
     - WHT: Asset
     - VAT: Liability

3. **"Output VAT - Undue not found"**
   - Solution: Use exact account name in Sales Taxes and Charges
   - System looks for "output vat" + "undue" in account name (case-insensitive)

4. **Amount calculation mismatches**
   - Solution: Check Sales Invoice calculations
   - Verify custom field values are populated correctly

## 🗑️ Uninstallation

### Remove Thai Tax System
```bash
# Remove all custom fields and clean up
bench execute print_designer.commands.install_payment_entry_retention_fields.uninstall_payment_entry_thai_tax_fields_direct

# Verify removal
bench execute print_designer.commands.install_payment_entry_retention_fields.check_payment_entry_retention_fields_direct
```

## 📊 GL Entry Reference

### Complete GL Pattern for Case Study
```
Sales Invoice (฿107 total):
Dr. Accounts Receivable        107.00
    Cr. Income                     100.00
    Cr. Output VAT - Undue           7.00

Payment Entry (฿99 cash):
Dr. Cash/Bank                   99.00  ← Actual cash received
Dr. Construction Retention       5.00  ← Asset we hold until completion
Dr. WHT - Assets                 3.00  ← Tax credit for revenue filing
Dr. Output VAT - Undue           7.00  ← Clear undue VAT balance
    Cr. Accounts Receivable         107.00  ← Clear customer balance
    Cr. Output VAT                    7.00  ← Register VAT due to govt
```

### Account Balance Impact
- **Cash/Bank**: +฿99 (net received)
- **Accounts Receivable**: -฿107 (cleared)
- **Construction Retention**: +฿5 (asset held)
- **WHT - Assets**: +฿3 (tax credit)  
- **Output VAT - Undue**: -฿7 (cleared)
- **Output VAT**: +฿7 (due to government)

## 🔗 Integration Points

### Existing Systems
- **Sales Invoice WHT**: Uses existing `custom_withholding_tax_amount` field
- **Sales Invoice Retention**: Uses existing `custom_retention_amount` field  
- **ERPNext VAT**: Integrates with standard Sales Taxes and Charges
- **Company Accounts**: Leverages existing default account configuration

### Future Enhancements
- Purchase Invoice integration for supplier payments
- VAT return report integration
- WHT certificate generation  
- Retention release workflow
- Multi-currency support

## 📈 Benefits

1. **Compliance**: Full Thai tax law compliance for construction/service businesses
2. **Automation**: Eliminates manual GL entry creation
3. **Accuracy**: Prevents calculation errors through validation
4. **Integration**: Works seamlessly with existing ERPNext features
5. **Flexibility**: Handles various combinations of tax components
6. **Traceability**: Complete audit trail of all tax transactions

---

## 📞 Support

For technical issues or questions about the Thai Tax System:
- Check existing ERPNext Payment Entry documentation
- Verify Company and Account configurations
- Test with simple scenarios before complex combinations
- Review GL Entry creation for accounting accuracy