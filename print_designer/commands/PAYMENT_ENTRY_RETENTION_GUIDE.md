# Payment Entry Retention System Guide

## Overview

The Payment Entry Retention System automatically handles retention amounts when processing payments for Sales Invoices that have retention requirements. This is particularly useful for construction services where a percentage of payment is typically held as retention until project completion.

## Key Features

### 🏗️ **Automatic Retention Detection**
- Automatically detects when Payment Entry references include Sales Invoices with retention
- Calculates retention amounts based on allocated amounts
- Shows retention summary at payment level

### 💰 **Smart Amount Calculations**
- **Per-Invoice Tracking**: Each invoice reference shows its retention amount and net payable
- **Payment Level Summary**: Total retention across all invoices in the payment
- **Net Payment Calculation**: Actual amount to be paid after retention deduction

### 📊 **Retention Liability Management**
- Creates retention asset GL entries on payment submission
- Uses company-specific retention asset accounts
- Tracks retention for future release

## Installation

```bash
# Install Payment Entry retention fields (includes legacy cleanup)
bench execute print_designer.commands.install_payment_entry_retention_fields.install_payment_entry_retention_fields

# Verify installation
bench execute print_designer.commands.install_payment_entry_retention_fields.check_payment_entry_retention_fields
```

## Field Naming Convention & Migration

All new custom fields use the `pd_custom_` prefix for namespace isolation:

### Current Fields (with pd_custom_ prefix)
- `pd_custom_retention_summary_section` - Section break for retention display
- `pd_custom_has_retention` - Flag indicating retention presence
- `pd_custom_retention_column_break` - Column break for layout
- `pd_custom_total_retention_amount` - Sum of retention across invoices

### Legacy Fields (automatically cleaned up)
- `retention_summary_section` → `pd_custom_retention_summary_section`
- `has_retention` → `pd_custom_has_retention` 
- `retention_column_break` → `pd_custom_retention_column_break`
- `total_retention_amount` → `pd_custom_total_retention_amount`

### Migration Commands

```bash
# Clean up legacy fields without pd_custom_ prefix
bench execute print_designer.commands.install_payment_entry_retention_fields.cleanup_legacy_retention_fields

# Uninstall all retention fields (both new and legacy)
bench execute print_designer.commands.install_payment_entry_retention_fields.uninstall_payment_entry_thai_tax_fields
```

### Automatic Migration
- Legacy field cleanup occurs automatically during `bench migrate` via `after_migrate` hook
- All fields are automatically removed during app uninstallation via `before_uninstall` hook

## How It Works

### 1. **Sales Invoice Setup**
First, ensure your Sales Invoices are configured with retention:
- Enable **Construction Service** in Company settings
- Set **default_retention_rate** (e.g., 5%)
- Configure **default_retention_account** for retention asset booking

### 2. **Payment Entry Workflow**

When creating a Payment Entry for invoices with retention:

1. **Invoice Selection**: Select Sales Invoices normally via "Get Outstanding Invoices"
2. **Automatic Detection**: System automatically detects retention amounts
3. **Retention Summary**: Shows retention details in dedicated section
4. **Amount Calculation**: Calculates net payment after retention deduction

### 3. **Payment Entry Display**

**Header Level**:
- `has_retention`: Checkbox indicating payment has retention
- `total_retention_amount`: Sum of retention across all invoices
- `net_payment_after_retention`: Actual amount to be paid
- `retention_account`: Account for booking retention asset
- `retention_note`: Detailed retention breakdown

**Reference Level** (Per Invoice):
- `has_retention`: Flag for this specific invoice
- `retention_amount`: Retention amount for this invoice
- `retention_percentage`: Retention rate from original invoice
- `net_payable_amount`: Amount payable after retention (Outstanding - Retention)

## Example Scenario

### Sales Invoice with Retention
```
Invoice Total: ฿100,000
Retention Rate: 5%
Retention Amount: ฿5,000
Net Payable: ฿95,000
```

### Payment Entry Processing
```
Payment References:
- Invoice ABC-001: Outstanding ฿100,000, Allocated ฿100,000
  - Retention: ฿5,000 (5%)
  - Net Payable: ฿95,000

Payment Summary:
- Total Allocated: ฿100,000
- Total Retention: ฿5,000
- Net Payment After Retention: ฿95,000
```

### GL Entries Created
```
Dr. Accounts Receivable        ฿100,000
    Cr. Bank Account                      ฿95,000
    Cr. Construction Retention Payable    ฿5,000
```

## Configuration

### Company Settings
Navigate to **Company** → **Construction Service** section:
- ✅ Enable Construction Service
- Set **Default Retention Rate** (e.g., 5.0%)
- Configure **Default Retention Account** (asset account)

### Account Setup
Ensure retention asset account exists:
- Account Type: **Payable** or **Liability**
- Account Name: e.g., "Construction Retention Payable"
- Company: Must match payment company

## Validation Rules

### Payment Entry Validation
- Retention asset account is required when retention is present
- Retention account must belong to the same company
- Retention account must be of type 'Payable' or 'Liability'
- Total retention amount must match sum of reference retention amounts

### Error Messages
- "Retention Liability Account is required when processing payments with retention amounts"
- "Retention Liability Account must belong to the same company as the payment"
- "Total retention amount mismatch. Expected X, got Y"

## API Integration

### Document Events
The system hooks into Payment Entry document events:
- `validate`: Calculate and validate retention amounts
- `on_submit`: Create retention asset GL entries
- `on_cancel`: Reverse retention asset entries

### Custom Functions
```python
# Manual retention calculation
from print_designer.custom.payment_entry_retention import payment_entry_calculate_retention_amounts
payment_entry_calculate_retention_amounts(payment_entry_doc)
```

## Troubleshooting

### Common Issues

**1. Retention fields not showing**
```bash
# Check current installation status
bench execute print_designer.commands.install_payment_entry_retention_fields.check_payment_entry_retention_fields

# If legacy fields are interfering, clean them up first
bench execute print_designer.commands.install_payment_entry_retention_fields.cleanup_legacy_retention_fields

# Then reinstall with proper naming
bench execute print_designer.commands.install_payment_entry_retention_fields.install_payment_entry_retention_fields
```

**2. Retention amounts not calculating**
- Check if Sales Invoice has `custom_subject_to_retention = 1`
- Verify `custom_retention_amount > 0` on the invoice
- Ensure Payment Entry references are properly loaded

**3. GL entries not created**
- Check if retention asset account is configured
- Verify account permissions and company matching
- Review error logs for GL entry creation issues

### Debug Commands
```bash
# Check Payment Entry retention fields
bench execute print_designer.commands.install_payment_entry_retention_fields.check_payment_entry_retention_fields

# Verify company retention settings
bench --site [site-name] console
>>> frappe.get_doc("Company", "Your Company Name").as_dict()
```

## Advanced Features

### Multi-Invoice Payments
The system handles payments that include multiple invoices with different retention rates:
- Each invoice's retention is calculated separately
- Total retention is summed at payment level
- Net payment reflects total retention deduction

### Partial Payments
When making partial payments against invoices with retention:
- Retention is calculated proportionally based on allocated amount
- Example: 50% payment → 50% of retention amount

### Mixed Payments
Payments can include both retention and non-retention invoices:
- Only invoices with retention show retention fields
- Total payment amount includes full amounts for all invoices
- Net payment shows amount after retention deduction

## Integration with Existing Systems

### Thai Business Suite Integration
- Works with Thai WHT (Withholding Tax) calculations
- Retention and WHT are calculated separately and combined
- Supports Thai language display and formatting

### Print Designer Integration  
- Retention details appear in Payment Entry print formats
- Customizable retention notes and terms
- Professional invoice layouts with retention breakdown

## Future Enhancements

### Retention Release Management
A future enhancement could include:
- Retention Tracking DocType for release management
- Automated retention release upon project completion
- Retention aging reports and notifications

### Retention Reports
Planned reporting features:
- Retention Summary Report by Company/Project
- Retention Aging Report
- Retention Release Schedule Report

## Support

For technical support or customization requests:
- Check error logs: `bench logs`
- Review custom field installation: `bench execute print_designer.commands.install_payment_entry_retention_fields.check_payment_entry_retention_fields`
- Contact system administrator for advanced configuration needs