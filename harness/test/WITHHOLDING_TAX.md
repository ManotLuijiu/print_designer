# Thai Withholding Tax System Documentation

This document describes the comprehensive Thai Withholding Tax (WHT) management system integrated into Print Designer.

## Overview

The Thai WHT system provides complete functionality for:
- **Automatic WHT calculation** on Payment Entry and Purchase Invoice
- **Government-compliant certificate generation** (Form 50 ทวิ)
- **Journal entry creation** for proper accounting
- **Comprehensive reporting** and analytics
- **Tax filing data preparation** for annual submissions

## Features

### 🧮 Automatic Calculations
- Real-time WHT amount calculation based on configurable rates
- Support for different income types with appropriate rates
- Validation of tax rates and minimum thresholds
- Smart rate suggestions based on service type

### 📄 Certificate Generation
- **Form 50 ทวิ** compliant certificates in Thai language
- Auto-generated certificate numbers (WHT-YYYY-MM-NNNN format)
- Professional print format with company and supplier details
- Thai Buddhist calendar date conversion

### 📊 Accounting Integration
- Automatic journal entry creation for WHT transactions
- Proper account mapping (WHT Payable vs Supplier accounts)
- Integration with ERPNext's accounting system
- Audit trail maintenance

### 📈 Reporting & Analytics
- Comprehensive WHT summary reports
- Supplier-wise WHT history tracking
- Tax filing data preparation (PND forms)
- Dashboard with key metrics

## System Architecture

### Backend Components

#### Core Module: `withholding_tax.py`
```python
# Main calculation function
calculate_withholding_tax(doc, method=None)

# Certificate data generation
get_wht_certificate_data(document_name, doctype)

# Journal entry creation
create_wht_journal_entry(document_name, doctype)

# Reporting functions
get_wht_summary_report(from_date, to_date, company, supplier)
```

#### API Layer: `withholding_tax_api.py`
```python
# REST API endpoints
/api/method/print_designer.api.withholding_tax_api.calculate_wht_amount
/api/method/print_designer.api.withholding_tax_api.generate_wht_certificate
/api/method/print_designer.api.withholding_tax_api.get_wht_summary_report
```

#### Client Scripts: `delivery_approval.js`
- Enhanced Payment Entry forms with WHT functionality
- Real-time calculation updates
- Certificate generation buttons
- Visual status indicators

### Document Events Integration

```python
# In hooks.py
doc_events = {
    "Payment Entry": {
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
    },
    "Purchase Invoice": {
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax", 
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
    }
}
```

## Usage Guide

### Payment Entry Workflow

1. **Create Payment Entry**
   - Select supplier and enter payment details
   - Choose "Pay" as payment type for supplier payments

2. **Enable WHT**
   - Check "Apply Thai Withholding Tax" checkbox
   - System automatically suggests appropriate rate based on service type
   - Manually adjust rate if needed (common rates: 3% services, 1% rental, 5% professional)

3. **Enter Supplier Details**
   - Add supplier's 13-digit Thai Tax ID
   - System validates Tax ID format and checksum

4. **Save and Calculate**
   - WHT amount automatically calculated: `Paid Amount × Rate ÷ 100`
   - Certificate number auto-generated
   - Document ready for submission

5. **Generate Certificate**
   - Click "Generate WHT Certificate" button
   - Certificate prints using Form 50 ทวิ format
   - Digital copy stored in system

6. **Create Accounting Entry**
   - Click to create Journal Entry for WHT
   - Debits Supplier Account (reduces liability)
   - Credits WHT Payable Account (government liability)

### Purchase Invoice Integration

The system also works with Purchase Invoice for scenarios where WHT is calculated during invoice processing:

1. **Invoice Processing**
   - Enable WHT during invoice entry
   - System calculates outstanding amount after WHT deduction
   - Links to subsequent Payment Entry

2. **Payment Processing**
   - Payment Entry automatically inherits WHT details
   - Net payment amount reflects WHT deduction
   - Proper accounting entries maintained

## Thai WHT Rate Configuration

### Standard Rates by Service Type

```python
THAI_WHT_RATES = {
    "professional_service": {
        "rate": 5.0,
        "description": "ค่าธรรมเนียมวิชาชีพ",
        "keywords": ["professional", "legal", "accounting", "medical", "engineering"]
    },
    "consulting": {
        "rate": 3.0,
        "description": "ค่าที่ปรึกษา", 
        "keywords": ["consulting", "advisory", "management"]
    },
    "general_service": {
        "rate": 3.0,
        "description": "ค่าบริการทั่วไป",
        "keywords": ["service", "maintenance", "repair"]
    },
    "advertising": {
        "rate": 2.0,
        "description": "ค่าโฆษณา",
        "keywords": ["advertising", "marketing", "promotion"]
    },
    "rental": {
        "rate": 5.0,  # Can be 1% or 5% depending on type
        "description": "ค่าเช่า",
        "keywords": ["rental", "lease", "rent"]
    },
    "transportation": {
        "rate": 1.0,
        "description": "ค่าขนส่ง",
        "keywords": ["transport", "delivery", "shipping"]
    }
}
```

### Income Type Mapping

The system automatically determines Thai income types for certificates:

- **Section 40(2)**: Professional fees, consulting, general services
- **Section 40(3)**: Royalties and intellectual property
- **Section 40(5)**: Rental income
- **Section 40(6)**: Transportation services
- **Section 40(7)**: Advertising and marketing

## API Documentation

### Calculate WHT Amount
```bash
POST /api/method/print_designer.api.withholding_tax_api.calculate_wht_amount
{
    "base_amount": 10000,
    "tax_rate": 3.0
}

Response:
{
    "success": true,
    "base_amount": 10000,
    "tax_rate": 3.0,
    "wht_amount": 300.00,
    "net_amount": 9700.00,
    "calculation": "10000 × 3.0% = 300.00"
}
```

### Get Rate Suggestion
```bash
GET /api/method/print_designer.api.withholding_tax_api.suggest_wht_rate
?item_group=Consulting Services
?supplier_type=Professional
?service_description=IT consulting services

Response:
{
    "success": true,
    "suggestion": {
        "rate": 3.0,
        "description": "ค่าที่ปรึกษา",
        "category": "consulting",
        "confidence": 2
    }
}
```

### Generate Certificate
```bash
POST /api/method/print_designer.api.withholding_tax_api.generate_wht_certificate
{
    "document_name": "PAY-2024-001",
    "doctype": "Payment Entry"
}

Response:
{
    "success": true,
    "certificate_data": { /* Certificate details */ },
    "pdf_generated": true,
    "message": "WHT certificate generated successfully"
}
```

### Summary Report
```bash
GET /api/method/print_designer.api.withholding_tax_api.get_wht_summary_report
?from_date=2024-01-01
?to_date=2024-12-31
?company=My Company Ltd
?supplier=ABC Supplier

Response:
{
    "success": true,
    "report": {
        "documents": [ /* List of WHT documents */ ],
        "summary": {
            "total_documents": 25,
            "total_base_amount": 500000,
            "total_wht_amount": 15000,
            "average_wht_rate": 3.0
        },
        "supplier_summary": { /* By supplier breakdown */ },
        "rate_summary": { /* By rate breakdown */ }
    }
}
```

## Custom Fields Reference

### Payment Entry Fields

| Field Name | Type | Description |
|------------|------|-------------|
| `custom_thai_withholding_tax_section` | Section Break | WHT section header |
| `custom_is_withholding_tax` | Check | Enable WHT calculation |
| `custom_withholding_tax_rate` | Float | Tax rate percentage |
| `custom_withholding_tax_amount` | Currency | Calculated WHT amount |
| `custom_supplier_tax_id` | Data | Supplier's Thai Tax ID |
| `custom_wht_certificate_number` | Data | Auto-generated cert number |
| `custom_wht_certificate_generated` | Check | Certificate status |

### Purchase Invoice Fields

Similar fields are added to Purchase Invoice with the same naming convention and functionality.

## Print Format Integration

### Thai Form 50 ทวิ Template

The system includes a government-compliant Form 50 ทวิ template:

- **Template Name**: "Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate"
- **Language**: Thai with proper formatting
- **Layout**: Official government form structure
- **Data Binding**: Automatic field population
- **Date Format**: Thai Buddhist calendar

### Template Usage in Jinja

```html
<!-- Access WHT certificate data in templates -->
{{ get_wht_certificate_data(doc.name, "Payment Entry") }}

<!-- Get Thai formatted date -->
{{ convert_to_thai_date(doc.reference_date) }}

<!-- Determine income type -->
{{ determine_income_type(doc) }}
```

## Compliance Features

### Government Requirements
- **Form 50 ทวิ**: Exact replica of official form
- **Tax ID Validation**: 13-digit format with checksum
- **Income Classification**: Proper section mapping per Thai tax law
- **Certificate Numbering**: Unique sequential numbering

### Audit Trail
- Complete transaction history
- Document references maintained
- User activity logging
- Change tracking for all WHT-related fields

### Reporting for Tax Authorities
- **PND 54**: For services under Section 40(2)
- **PND 55**: For rental income under Section 40(5)
- **Annual Summary**: By income type and supplier
- **Filing Data**: Structured for tax software import

## Installation

**📋 For complete installation instructions, see [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)**

### Quick Installation
```bash
# Install complete Print Designer system including WHT
bench --site your-site.com install-complete-system

# Check installation status
bench --site your-site.com check-system-status
```

### Manual Installation
```bash
# Install WHT system only
bench --site your-site.com execute "
from print_designer.setup.install import setup_thai_withholding_tax_and_qr_delivery
result = setup_thai_withholding_tax_and_qr_delivery()
print(result)
"
```

The installation guide covers:
- **System Requirements** and prerequisites
- **Automated vs Manual** installation methods
- **Custom Field Reference** with complete field documentation
- **Print Format Setup** with Thai language templates
- **API Configuration** and endpoint setup
- **Troubleshooting Guide** for common issues
- **Security Considerations** and best practices

## Configuration

### Company Setup
1. **Tax Settings**: Configure company Tax ID
2. **Account Mapping**: Set up WHT Payable account
3. **Print Settings**: Configure Form 50 ทวิ as default

### Supplier Setup
1. **Tax ID**: Enter 13-digit Thai Tax ID
2. **Supplier Group**: Set appropriate group for rate suggestions
3. **Default Accounts**: Configure payable accounts

## Troubleshooting

### Common Issues

**WHT Not Calculating**
- Verify `custom_is_withholding_tax` checkbox is enabled
- Check that tax rate > 0
- Ensure paid_amount/grand_total > 0

**Certificate Not Generating**
- Verify Print Format "Payment Entry Form 50 ทวิ" exists
- Check supplier Tax ID is present
- Ensure document is submitted (docstatus = 1)

**Journal Entry Errors**
- Verify WHT Payable account exists
- Check chart of accounts configuration
- Ensure Journal Entry permissions

**Tax ID Validation Failing**
- Use exactly 13 digits
- Remove spaces and dashes
- Verify checksum calculation

### Debug Mode
```python
# Enable debug logging
frappe.log_error("WHT Debug Info", "WHT System")

# Check field values
print(doc.custom_is_withholding_tax)
print(doc.custom_withholding_tax_rate)
print(doc.custom_withholding_tax_amount)
```

## Performance Considerations

### Database Optimization
- Indexes on WHT-related fields
- Efficient query patterns for reports
- Caching of frequently accessed data

### API Rate Limiting
- Implement rate limiting for calculation APIs
- Cache rate suggestions
- Optimize report generation queries

## Security

### Permission Framework
- Role-based access to WHT functions
- Document-level permissions maintained
- Audit logging for sensitive operations

### Data Privacy
- Supplier Tax ID encryption (recommended)
- Secure certificate storage
- Access logging for compliance

## Future Enhancements

### Planned Features
- **Multi-currency Support**: Foreign currency WHT calculations
- **Electronic Filing**: Direct integration with Thai tax authorities
- **Advanced Analytics**: Machine learning for rate predictions
- **Mobile App**: Mobile certificate verification

### Extension Points
- Custom rate calculation logic
- Additional certificate formats
- Third-party tax software integration
- Blockchain-based certificate verification

## Support

For technical support with the Thai WHT system:

1. **Check System Status**: Run installation status check
2. **Review Logs**: Check Frappe error logs for detailed information
3. **Validate Setup**: Verify all custom fields and accounts exist
4. **Test API**: Use API endpoints to isolate issues

## License and Compliance

This Thai WHT system is developed specifically for compliance with Thai Revenue Department requirements and follows all applicable tax regulations. The system is provided as part of the Print Designer app under AGPLv3 license.