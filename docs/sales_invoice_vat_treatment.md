# Sales Invoice VAT Treatment Implementation

## Overview
This document explains the Sales Invoice regional GL entries implementation for Thai VAT compliance, which overrides the Sales Taxes and Charges Template's VAT account based on the VAT Treatment field.

## Problem Statement

### Background
- **Sales Taxes and Charges Template** always requires a VAT account (mandatory field)
- The template's default VAT account = Company's `default_output_vat_account`
- For services where VAT occurs later (upon payment receipt), we need to use VAT Undue account instead
- User intent is expressed via the **VAT Treatment** field on Sales Invoice

### The Bug
Previously, Sales Invoice would always use the template's VAT account, even when the user selected "VAT Undue (7%)" treatment, causing incorrect VAT ledger entries.

## Solution

### Implementation Files

#### 1. `/apps/print_designer/print_designer/regional/sales_invoice.py`
New regional GL entries handler that:
- Checks `vat_treatment` field on Sales Invoice
- Fetches Company's default VAT accounts
- Replaces VAT GL entries with correct account based on VAT Treatment

#### 2. `/apps/print_designer/print_designer/hooks.py`
Registered the regional override:
```python
regional_overrides = {
    "Thailand": {
        "erpnext.accounts.doctype.payment_entry.payment_entry.add_regional_gl_entries": "print_designer.regional.payment_entry.add_regional_gl_entries",
        "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_regional_gl_entries": "print_designer.regional.sales_invoice.make_regional_gl_entries"
    }
}
```

### Logic Flow

```
Sales Invoice Submission
    ↓
Check vat_treatment field
    ↓
    ├─ "VAT Undue (7%)" → Use Company's default_output_vat_undue_account
    ├─ "Standard VAT (7%)" → Use Company's default_output_vat_account
    └─ No value → Use template's default (no override)
    ↓
Override VAT GL entries with correct account
    ↓
Save GL entries to ledger
```

### VAT Account Selection Priority

| VAT Treatment Field | VAT Account Used | When to Use |
|---------------------|------------------|-------------|
| VAT Undue (7%) | Company's `default_output_vat_undue_account` | Services, VAT point not yet occurred (upon payment receipt) |
| Standard VAT (7%) | Company's `default_output_vat_account` | Goods, VAT point occurred immediately |
| Not set | Template's VAT account (default behavior) | No override needed |

## Testing Procedure

### Prerequisites
1. Ensure Company has configured:
   - `default_output_vat_account` (e.g., "Output VAT - MC")
   - `default_output_vat_undue_account` (e.g., "Output VAT Undue - MC")

2. Create a Sales Taxes and Charges Template with 7% VAT (will default to `default_output_vat_account`)

### Test Case 1: VAT Undue (Services)
**Scenario**: Selling services where VAT occurs upon payment receipt

1. Create new Sales Invoice
2. Select customer and add service items
3. Select Sales Taxes and Charges Template (7% VAT)
4. Set **VAT Treatment** to "VAT Undue (7%)"
5. Save and Submit the Sales Invoice
6. Click **Preview** → **Accounting Ledger**

**Expected Result**:
```
Dr. Customer (Accounts Receivable)     ฿107.00
    Cr. Service Income                      ฿100.00
    Cr. Output VAT Undue - MC               ฿7.00    ← Should use VAT Undue account
```

**How to Verify**:
- VAT GL entry should show **Output VAT Undue** account
- NOT the template's default Output VAT account

### Test Case 2: Standard VAT (Goods)
**Scenario**: Selling goods where VAT occurs immediately

1. Create new Sales Invoice
2. Select customer and add product items
3. Select Sales Taxes and Charges Template (7% VAT)
4. Set **VAT Treatment** to "Standard VAT (7%)"
5. Save and Submit the Sales Invoice
6. Click **Preview** → **Accounting Ledger**

**Expected Result**:
```
Dr. Customer (Accounts Receivable)     ฿107.00
    Cr. Sales Income                        ฿100.00
    Cr. Output VAT - MC                     ฿7.00    ← Should use standard VAT account
```

**How to Verify**:
- VAT GL entry should show **Output VAT** account (template default)
- This matches the template's configuration

### Test Case 3: No VAT Treatment (Default Behavior)
**Scenario**: User doesn't set VAT Treatment field

1. Create new Sales Invoice
2. Select customer and add items
3. Select Sales Taxes and Charges Template (7% VAT)
4. Leave **VAT Treatment** blank
5. Save and Submit the Sales Invoice
6. Click **Preview** → **Accounting Ledger**

**Expected Result**:
- Uses template's default VAT account (no override)
- Maintains backward compatibility

### Test Case 4: End-to-End VAT Undue Workflow
**Scenario**: Service sale with VAT Undue, then payment receipt with auto-conversion

**Part A: Sales Invoice with VAT Undue**
1. Create new Sales Invoice for services (e.g., consulting)
2. Add service items: ฿100
3. Select Sales Taxes and Charges Template (7% VAT)
4. Set **VAT Treatment** to "VAT Undue (7%)"
5. Submit the Sales Invoice
6. Preview Accounting Ledger

**Expected SI GL Entries**:
```
Dr. Customer (AR)              ฿107.00
    Cr. Service Income             ฿100.00
    Cr. Output VAT Undue - MC      ฿7.00  ← VAT Undue account used
```

**Part B: Payment Entry (Receive) with Auto-Conversion**
1. Create Payment Entry (Receive)
2. Select the customer
3. Link to the Sales Invoice created above
4. Allocate full amount: ฿107
5. Submit the Payment Entry
6. Preview Accounting Ledger

**Expected PE GL Entries**:
```
Dr. Cash/Bank                  ฿107.00
    Cr. Customer (AR)              ฿107.00

PLUS VAT Conversion (Auto-detected):
Dr. Output VAT Undue - MC      ฿7.00   ← Clear VAT Undue
    Cr. Output VAT - MC            ฿7.00   ← Realize VAT liability
```

**How to Verify**:
- Payment Entry automatically detected VAT Undue from linked SI
- Created VAT conversion GL entries without manual intervention
- Final VAT balance: VAT Undue = ฿0, VAT = ฿7 (liability to government)

### Test Case 5: Partial Payment with Proportional VAT Conversion
**Scenario**: Service sale with VAT Undue, paid in two installments

**Part A: Sales Invoice**
- Same as Test Case 4 Part A
- Grand Total: ฿107 (฿100 + ฿7 VAT Undue)

**Part B: First Payment (50%)**
1. Create Payment Entry (Receive)
2. Allocate ฿53.50 (50% of ฿107)
3. Submit

**Expected PE1 GL Entries**:
```
Dr. Cash/Bank                  ฿53.50
    Cr. Customer (AR)              ฿53.50

VAT Conversion (50% proportional):
Dr. Output VAT Undue - MC      ฿3.50   ← 50% of ฿7
    Cr. Output VAT - MC            ฿3.50
```

**Part C: Second Payment (50%)**
1. Create Payment Entry (Receive)
2. Allocate remaining ฿53.50
3. Submit

**Expected PE2 GL Entries**:
```
Dr. Cash/Bank                  ฿53.50
    Cr. Customer (AR)              ฿53.50

VAT Conversion (remaining 50%):
Dr. Output VAT Undue - MC      ฿3.50   ← Remaining 50% of ฿7
    Cr. Output VAT - MC            ฿3.50
```

**Final Verification**:
- Total VAT converted: ฿3.50 + ฿3.50 = ฿7.00 ✅
- VAT Undue balance: ฿0
- VAT balance: ฿7.00

### Test Case 6: Standard VAT (No Conversion Needed)
**Scenario**: Goods sale with Standard VAT, payment receipt without conversion

**Part A: Sales Invoice**
1. Create Sales Invoice for goods
2. Add product items: ฿100
3. Select Sales Taxes and Charges Template (7% VAT)
4. Set **VAT Treatment** to "Standard VAT (7%)"
5. Submit

**Expected SI GL Entries**:
```
Dr. Customer (AR)              ฿107.00
    Cr. Sales Income               ฿100.00
    Cr. Output VAT - MC            ฿7.00  ← Standard VAT (already realized)
```

**Part B: Payment Entry**
1. Create Payment Entry (Receive)
2. Link to Sales Invoice
3. Submit

**Expected PE GL Entries**:
```
Dr. Cash/Bank                  ฿107.00
    Cr. Customer (AR)              ฿107.00

NO VAT conversion needed (VAT already realized in SI)
```

## Debugging

### Enable Logging
Check Frappe logs for debug messages:
```bash
tail -f ~/frappe-bench/logs/frappe.log | grep "Sales Invoice.*VAT"
```

### Log Messages to Look For
- `[Sales Invoice {name}] VAT Treatment: {value} → Using VAT Undue account: {account}`
- `[Sales Invoice {name}] Replaced VAT account: {old} → {new} (Amount: {amount})`
- `[Sales Invoice {name}] Modified {count} VAT GL entries based on VAT Treatment: {value}`

### Common Issues

#### Issue: VAT account not being replaced
**Cause**: Company default VAT accounts not configured
**Solution**: Set up `default_output_vat_account` and `default_output_vat_undue_account` in Company DocType

#### Issue: Wrong VAT account used
**Cause**: VAT Treatment field contains unexpected value
**Solution**: Check VAT Treatment field value matches expected patterns ("VAT Undue", "Standard VAT")

#### Issue: No warning/error messages
**Cause**: Regional override not registered or bench needs restart
**Solution**:
```bash
cd ~/frappe-bench
bench restart
```

## Technical Details

### Hook Execution Flow
1. User submits Sales Invoice
2. ERPNext calls `sales_invoice.make_gl_entries()`
3. ERPNext generates GL entries including VAT from template
4. **Regional hook is triggered**: `make_regional_gl_entries(gl_entries, doc)`
5. Our code modifies VAT account in GL entries list
6. Modified GL entries are saved to General Ledger

### GL Entry Identification
VAT GL entries are identified by:
- Credit side (output VAT for sales)
- Account name contains: "VAT", "OUTPUT TAX", "ภาษีขาย", "OUTPUT VAT"

### Account Replacement Logic
```python
if "VAT Undue" in vat_treatment:
    target_vat_account = company_doc.default_output_vat_undue_account
elif "Standard VAT" in vat_treatment:
    target_vat_account = company_doc.default_output_vat_account

for gl_entry in gl_entries:
    if is_vat_entry(gl_entry):
        gl_entry['account'] = target_vat_account
```

## Integration with Payment Entry

### VAT Conversion on Payment Receipt (Automatic Detection)

The Payment Entry (Receive) automatically detects VAT Undue from linked Sales Invoices and creates conversion GL entries.

#### Detection Logic

**Step 1: Check Linked Sales Invoices**
```python
for each reference in Payment Entry.references:
    if reference.reference_doctype == "Sales Invoice":
        sales_invoice = get_doc("Sales Invoice", reference.reference_name)
        if "Undue" in sales_invoice.vat_treatment:
            # This Sales Invoice used VAT Undue
            # Need to convert VAT Undue → VAT Due
```

**Step 2: Calculate VAT Amount**
```python
# Query GL Entry table for VAT Undue account
vat_undue_gl_entries = get_gl_entries(
    voucher_type="Sales Invoice",
    voucher_no=sales_invoice.name,
    account=Company.default_output_vat_undue_account
)

# Calculate proportional VAT if partial payment
proportion = allocated_amount / sales_invoice.grand_total
proportional_vat = vat_undue_amount * proportion
```

**Step 3: Create VAT Conversion GL Entries**
```
Dr. Output VAT Undue - MC      ฿7.00
    Cr. Output VAT - MC            ฿7.00
```

#### Scenarios Handled

| Sales Invoice VAT Treatment | Payment Entry Action | GL Entries Created |
|----------------------------|---------------------|-------------------|
| VAT Undue (7%) | Auto-detect from SI GL entries | Dr. VAT Undue ฿7, Cr. VAT ฿7 |
| Standard VAT (7%) | No action needed | None (VAT already realized) |
| Not set | No action needed | None (uses template default) |

#### Partial Payment Support

When a Sales Invoice is paid in multiple installments:
```
Sales Invoice: ฿107 (฿100 + ฿7 VAT Undue)

Payment 1: ฿53.50 (50% payment)
→ Convert ฿3.50 VAT Undue → VAT Due (50% of ฿7)

Payment 2: ฿53.50 (remaining 50%)
→ Convert ฿3.50 VAT Undue → VAT Due (remaining 50%)
```

#### Implementation Files
- Detection: `print_designer/regional/payment_entry.py::_get_vat_undue_from_linked_sales_invoices()`
- Conversion: `print_designer/regional/payment_entry.py::_add_thai_receive_gl_entries()`

## Compliance

### Thai Tax Regulations
- **VAT Undue**: Used for services where VAT obligation occurs upon payment receipt
- **Standard VAT**: Used for goods where VAT obligation occurs upon delivery/invoice
- This implementation ensures correct VAT timing per Thai Revenue Department requirements

## References

- ERPNext Ledger System Documentation: `/Users/manotlj/frappe-bench/ERPNEXT_LEDGER_SYSTEM.md`
- Payment Entry Regional GL Entries: `print_designer/regional/payment_entry.py`
- Sales Invoice Calculations: `print_designer/custom/sales_invoice_calculations.py`
