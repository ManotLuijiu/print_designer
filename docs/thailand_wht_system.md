# Thailand WHT System - Complete Integration Guide

## Overview

This document describes the comprehensive Thailand Withholding Tax (WHT) system that has been merged and unified into a single implementation in `print_designer/thailand_wht_fields.py`. The system provides complete WHT functionality across Company configuration, Customer setup, and all sales documents.

## Architecture

### Unified System Structure

The Thailand WHT system has been consolidated from two separate implementations:
1. **Main WHT System** (`thailand_wht_fields.py`) - Core functionality 
2. **WHT Preview System** (`thai_wht_custom_fields.py`) - Preview and Customer fields

**Result**: Single comprehensive system with all functionality merged into `thailand_wht_fields.py`

### Field Configuration

The system follows the **no section break** pattern established in the main system, using Column Break fields instead for clean layout without collapsible sections.

## DocType Coverage

### 1. Company Configuration
**Purpose**: Enable and configure WHT functionality at company level

**Fields**:
- `thailand_service_business` (Check) - Enable WHT features
- `default_wht_rate` (Percent) - Default WHT rate (3%)
- `default_wht_account` (Link:Account) - Default WHT asset account

### 2. Customer Configuration  
**Purpose**: Configure per-customer WHT settings

**Fields**:
- `subject_to_wht` (Check) - Customer subject to WHT
- `wht_config_column_break` (Column Break) - Layout
- `is_juristic_person` (Check) - Juristic person status
- `wht_income_type` (Select) - Default income type
- `custom_wht_rate` (Percent) - Custom WHT rate override

### 3. Item Configuration
**Purpose**: Mark service items for WHT calculation

**Fields**:
- `is_service_item` (Check) - Item represents a service

### 4. Sales Documents (Quotation, Sales Order, Sales Invoice)
**Purpose**: WHT preview calculations and information

**Common Fields**:
- `subject_to_wht` (Check) - Document subject to WHT
- `wht_preview_column_break` (Column Break) - Layout
- `wht_income_type` (Select) - Income type for calculation
- `wht_description` (Data) - Thai income type description
- `wht_base_amount` (Currency) - Base amount for calculation
- `estimated_wht_rate` (Percent) - Calculated WHT rate
- `estimated_wht_amount` (Currency) - Calculated WHT amount
- `net_payment_amount` (Currency) - Expected payment after WHT
- `net_total_after_wht` (Currency) - Legacy field for compatibility
- `net_total_after_wht_in_words` (Small Text) - Amount in Thai words
- `wht_note` (Small Text) - Important notice about WHT timing

**Sales Invoice Additional Fields**:
- `wht_certificate_required` (Check) - Certificate requirement
- `custom_retention` (Check) - Apply retention
- `custom_retention_amount` (Currency) - Retention amount
- `custom_withholding_tax` (Check) - Apply WHT
- `custom_withholding_tax_amount` (Currency) - WHT amount
- `custom_payment_amount` (Currency) - Final payment amount

## Installation Commands

### Primary Installation
```bash
# Complete system installation
bench execute print_designer.commands.thailand_wht_system.install_complete_system

# Quick installation alias
bench execute print_designer.commands.thailand_wht_system.install
```

### Verification Commands
```bash
# Check complete system
bench execute print_designer.commands.thailand_wht_system.check_complete_system

# Check specific components
bench execute print_designer.commands.thailand_wht_system.check_company_fields
bench execute print_designer.commands.thailand_wht_system.check_customer_fields
bench execute print_designer.commands.thailand_wht_system.check_sales_documents
```

### System Management
```bash
# Validate configuration
bench execute print_designer.commands.thailand_wht_system.validate_system

# Reinstall/update system
bench execute print_designer.commands.thailand_wht_system.reinstall_system

# System information
bench execute print_designer.commands.thailand_wht_system.show_system_info
```

### Development & Testing
```bash
# Create test data
bench execute print_designer.commands.thailand_wht_system.create_test_data

# Migration for existing installations
bench execute print_designer.commands.thailand_wht_system.migrate_existing_installations
```

## WHT Income Types & Rates

### Standard Income Types
| Income Type | Thai Description | Standard Rate |
|-------------|------------------|---------------|
| `professional_services` | ค่าบริการทางวิชาชีพ | 5% |
| `rental` | ค่าเช่า | 5% |
| `service_fees` | ค่าบริการ | 3% |
| `construction` | ค่าก่อสร้าง | 3% |
| `advertising` | ค่าโฆษณา | 2% |
| `other_services` | ค่าบริการอื่นๆ | 3% |

### Rate Calculation Logic
1. **Customer Custom Rate**: If `customer.custom_wht_rate` is set, use it
2. **Income Type Rate**: Use standard rate for income type
3. **Entity Type Adjustment**: Higher rates for individuals vs. juristic persons
4. **Company Default**: Fall back to company default rate

## Field Dependencies & Logic

### Display Dependencies
- Company fields: `thailand_service_business` enables WHT features
- Customer fields: `subject_to_wht` shows WHT configuration  
- Sales document fields: `subject_to_wht` shows all WHT preview fields
- Amount fields: Show when `subject_to_wht` is checked

### Calculation Flow
1. **Check Customer**: `subject_to_wht` flag
2. **Determine Rate**: Custom rate → Income type rate → Company default
3. **Calculate Base**: Use document net total or specified amount
4. **Calculate WHT**: `base_amount × wht_rate / 100`
5. **Net Payment**: `total_amount - wht_amount`

## Integration Points

### Print Formats
WHT fields are available in print formats for:
- Quotations with WHT preview
- Sales Orders with WHT estimates  
- Sales Invoices with final WHT calculations
- Thai language labels and amounts in words

### Workflow Integration
- **Quote Stage**: Preview WHT impact on pricing
- **Order Stage**: Confirm WHT calculations  
- **Invoice Stage**: Final WHT amounts for payment
- **Payment Stage**: Actual WHT deduction and certificate

### API Integration
All WHT functions available via Python API:
```python
from print_designer.thailand_wht_fields import (
    calculate_wht_amount,
    get_wht_rate_for_income_type,
    get_wht_income_type_description
)
```

## System Validation

### Automatic Checks
The system includes comprehensive validation:
- Field installation verification
- Configuration completeness check
- Company setup validation  
- Customer configuration review

### Manual Validation
```bash
# Run complete system validation
bench execute print_designer.commands.thailand_wht_system.validate_system
```

## Migration from Previous Versions

### From Separate Systems
If upgrading from separate `thailand_wht_fields.py` and `thai_wht_custom_fields.py`:

1. **Backup Data**: Export existing custom field data
2. **Run Migration**: `migrate_existing_installations()`
3. **Install Complete System**: `install_complete_system()`
4. **Verify**: `check_complete_system()`

### Field Compatibility
- All existing Sales Invoice fields preserved
- New Customer configuration fields added
- Quotation and Sales Order fields activated
- No data loss during migration

## Troubleshooting

### Common Issues

**Fields Not Visible**:
```bash
# Clear cache and rebuild
bench clear-cache
bench migrate
```

**Installation Failures**:
```bash
# Reinstall system
bench execute print_designer.commands.thailand_wht_system.reinstall_system
```

**Configuration Issues**:
```bash
# Validate system setup
bench execute print_designer.commands.thailand_wht_system.validate_system
```

### Debug Commands
```bash
# Check specific DocType
bench --site [site] console
>>> from print_designer.thailand_wht_fields import check_specific_doctype_wht_fields
>>> check_specific_doctype_wht_fields("Customer")
```

## Best Practices

### Company Setup
1. Enable `thailand_service_business` checkbox
2. Set appropriate `default_wht_rate` (typically 3%)
3. Configure `default_wht_account` to existing asset account

### Customer Configuration  
1. Mark customers with `subject_to_wht` as needed
2. Set `is_juristic_person` correctly (affects rates)
3. Configure `wht_income_type` for customer's primary service
4. Use `custom_wht_rate` only for special arrangements

### Document Workflow
1. **Quotation**: Enable WHT preview for accurate pricing
2. **Sales Order**: Confirm WHT calculations with customer
3. **Sales Invoice**: Final WHT amounts for payment processing
4. **Print Formats**: Include WHT information in Thai language

### Testing
1. Create test customers with different WHT configurations
2. Test all income types and rate calculations
3. Verify print format display of WHT information
4. Test migration scenarios with existing data

## Support & Maintenance

### Regular Maintenance
- Run `validate_system()` periodically
- Update WHT rates when regulations change
- Test field visibility after Frappe updates
- Back up custom field configurations

### System Updates
The unified system supports:
- Hot fixes via `reinstall_system()`
- Field updates without data loss
- Migration scripts for structural changes
- Backward compatibility maintenance

For technical support, use the command-line tools to diagnose issues and generate detailed system reports.