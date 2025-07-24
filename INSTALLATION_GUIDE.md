# Thai Withholding Tax Certificate & QR Delivery Approval - Complete Installation Guide

This comprehensive guide will help you implement the Thai Withholding Tax Certificate (ฟอร์ม 50 ทวิ) and QR Code delivery approval system in ERPNext's Print Designer app.

## Overview

The system provides:
- **Thai Withholding Tax Certificates**: Government-compliant Form 50 ทวิ generation
- **QR Delivery Approval**: Mobile-friendly delivery confirmation system  
- **Automated Calculations**: Real-time WHT calculations with rate suggestions
- **Professional Print Formats**: Thai language support with proper formatting
- **Complete API Integration**: REST endpoints for external system integration

> **📋 Note**: This guide covers the **enhanced QR delivery system** (`custom/delivery_note_qr.py`) which provides comprehensive functionality including security tokens, digital signatures, and mobile optimization. The app also contains a simpler legacy QR system (`delivery_note/delivery_note.py`) for backwards compatibility. For new installations, use the enhanced system documented here.

## Prerequisites

### System Requirements
1. **ERPNext V15+** with Print Designer app installed
2. **Python 3.10+** with required packages
3. **Admin access** to ERPNext instance
4. **Chrome/Chromium** browser for PDF generation

### Required Python Packages
```bash
# Install required packages
pip install qrcode[pil] pypng python-barcode
```

### File Structure Overview
```
print_designer/
├── print_designer/
│   ├── custom/
│   │   ├── __init__.py
│   │   ├── delivery_note_qr.py
│   │   └── withholding_tax.py
│   ├── api/  
│   │   ├── __init__.py
│   │   ├── system_setup.py
│   │   └── withholding_tax_api.py
│   ├── setup/
│   │   ├── __init__.py
│   │   └── install.py
│   ├── commands/
│   │   └── install_complete_system.py
│   └── public/
│       ├── js/
│       │   └── delivery_approval.js
│       └── css/
│           └── delivery_approval.bundle.scss
```

## Installation Methods

### Method 1: Automated Installation (Recommended)

The system includes automated installation commands for easy setup.

#### Step 1: Install Complete System
```bash
# Install all components (WHT + QR + Custom Fields + Print Formats)
bench --site your-site.com install-complete-system

# Check installation status
bench --site your-site.com check-system-status
```

#### Step 2: Verify Installation
The installation process will:
- ✅ Create all custom fields for Payment Entry and Purchase Invoice
- ✅ Install Thai WHT print formats with proper formatting
- ✅ Set up QR delivery approval system
- ✅ Configure API endpoints and hooks
- ✅ Enable client-side enhancements

### Method 2: Manual Installation

If you prefer manual control or need to troubleshoot specific components.

#### Step 1: Create Core Modules

All core modules are already created in the system:

**Backend Modules:**
- `custom/withholding_tax.py` - Complete WHT calculation and certificate system
- `custom/delivery_note_qr.py` - QR code generation and approval tracking
- `api/withholding_tax_api.py` - REST API endpoints for WHT operations
- `setup/install.py` - Installation orchestration system

**Frontend Components:**
- `public/js/delivery_approval.js` - Enhanced UI for both QR and WHT features
- `public/css/delivery_approval.bundle.scss` - Professional styling

#### Step 2: Manual Field Installation
```python
# Via ERPNext console
from print_designer.setup.install import setup_thai_withholding_tax_and_qr_delivery
result = setup_thai_withholding_tax_and_qr_delivery()
print(result)
```

#### Step 3: Verify Hooks Configuration

The `hooks.py` file should include (already configured):

```python
# Custom bench commands
commands = [
    "print_designer.commands.install_complete_system.install_complete_system",
    "print_designer.commands.install_complete_system.check_system_status",
]

# Client scripts for enhanced UI
doctype_js = {
    "Delivery Note": "print_designer/public/js/delivery_approval.js",
    "Payment Entry": "print_designer/public/js/delivery_approval.js",
}

# CSS bundles for professional styling
app_include_css = [
    "delivery_approval.bundle.css",
]

# Document events for automatic processing
doc_events = {
    "Payment Entry": {
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
    },
    "Purchase Invoice": {
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
    },
    "Delivery Note": {
        "on_submit": "print_designer.custom.delivery_note_qr.add_qr_to_delivery_note",
    },
}

# Jinja methods for template integration
jinja = {
    "methods": [
        # Thai Withholding Tax methods
        "print_designer.custom.withholding_tax.get_wht_certificate_data",
        "print_designer.custom.withholding_tax.determine_income_type",
        "print_designer.custom.withholding_tax.convert_to_thai_date",
        "print_designer.custom.withholding_tax.get_suggested_wht_rate",
        # Delivery Note QR code methods
        "print_designer.custom.delivery_note_qr.generate_delivery_approval_qr",
        "print_designer.custom.delivery_note_qr.get_qr_code_image",
        "print_designer.custom.delivery_note_qr.get_delivery_status",
    ]
}
```

## Custom Fields Reference

### Payment Entry Fields
The system automatically creates these custom fields:

| Field Name | Type | Description |
|------------|------|-------------|
| `custom_thai_withholding_tax_section` | Section Break | WHT section header |
| `custom_is_withholding_tax` | Check | Enable WHT calculation |
| `custom_withholding_tax_rate` | Float | Tax rate percentage (0-30%) |
| `custom_withholding_tax_amount` | Currency | Calculated WHT amount |
| `custom_supplier_tax_id` | Data | Supplier's 13-digit Thai Tax ID |
| `custom_wht_certificate_number` | Data | Auto-generated certificate number |
| `custom_wht_certificate_generated` | Check | Certificate generation status |

### Purchase Invoice Fields
Similar fields are added to Purchase Invoice for complete integration:

| Field Name | Type | Description |
|------------|------|-------------|
| `custom_thai_withholding_tax_section` | Section Break | WHT section header |
| `custom_is_withholding_tax` | Check | Enable WHT calculation |
| `custom_withholding_tax_rate` | Float | Tax rate percentage |
| `custom_withholding_tax_amount` | Currency | Calculated WHT amount |
| `custom_supplier_tax_id` | Data | Supplier's Tax ID |

### Delivery Note Fields
For QR delivery approval functionality:

| Field Name | Type | Description |
|------------|------|-------------|
| `custom_delivery_approval_section` | Section Break | QR approval section |
| `custom_goods_received_status` | Select | Delivery status (Pending/Approved/Rejected) |
| `custom_approval_qr_code` | Long Text | Base64 QR code image |
| `custom_approval_url` | Data | Approval page URL |
| `custom_customer_approval_date` | Datetime | Approval timestamp |
| `custom_approved_by` | Data | Customer name/signature |
| `custom_customer_signature` | Long Text | Digital signature data |
| `custom_rejection_reason` | Small Text | Rejection reason |

## DocType Reference

### Delivery Note Approval DocType
The system includes a comprehensive DocType for managing secure token-based delivery approvals:

**DocType Name**: `Delivery Note Approval`  
**Module**: Print Designer  
**Naming Series**: `DNA-.YYYY.-.#####`

#### Fields Structure:

| Field Name | Type | Options | Description |
|------------|------|---------|-------------|
| `naming_series` | Select | DNA-.YYYY.-.##### | Document naming pattern |
| `delivery_note` | Link | Delivery Note | Reference to delivery note |
| `approval_token` | Data | unique | Secure approval token |
| `customer_mobile` | Data | - | Customer mobile number |
| `status` | Select | Pending/Approved/Rejected/Expired | Current approval status |
| `generated_on` | Datetime | read_only | Token generation timestamp |
| `approved_on` | Datetime | read_only | Approval completion timestamp |
| `customer_name` | Data | - | Name of approving customer |
| `digital_signature` | Long Text | read_only | Base64 digital signature data |
| `remarks` | Text | - | Customer comments/feedback |

#### Key Features:
- **Secure Token System**: Each approval has a unique token for secure guest access
- **Expiry Management**: Configurable expiry (7 days default) with automatic status updates  
- **Email Notifications**: Automatic notifications to sales team on approval/rejection
- **Audit Trail**: Complete tracking of approval workflow with timestamps
- **Mobile Optimization**: Guest-accessible approval pages optimized for mobile use

#### API Methods:
```python
# DocType Methods
approval.get_approval_url()          # Get mobile-friendly approval URL
approval.is_expired()                # Check if approval has expired
approval.approve_delivery()          # Process customer approval
approval.reject_delivery()           # Process customer rejection
approval.send_approval_notification() # Send email notifications

# Guest API Functions (allow_guest=True)
get_approval_details(token)          # Get approval info by token
submit_approval_decision(token, decision, customer_name, signature, remarks)
```

#### Integration Points:
- **Delivery Note Hooks**: Automatically creates approval record on delivery note submission
- **QR Generation**: Integrates with `delivery_note_qr.py` for QR code generation
- **Status Sync**: Updates delivery note status fields when approval changes
- **Permission System**: Role-based access for Sales Manager, Sales User, System Manager

## Print Formats

### Thai Withholding Tax Certificate
**Print Format Name**: "Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate"

**Features:**
- Government-compliant Form 50 ทวิ layout
- Thai language with proper formatting
- Buddhist calendar date conversion
- Automatic field population from document data
- Professional styling with company branding

**Template Usage:**
```html
<!-- Access WHT certificate data in templates -->
{{ get_wht_certificate_data(doc.name, "Payment Entry") }}

<!-- Get Thai formatted date -->
{{ convert_to_thai_date(doc.reference_date) }}

<!-- Determine income type -->
{{ determine_income_type(doc) }}
```

### QR Delivery Approval Format
**Print Format Name**: "Delivery Note with QR Approval"

**Features:**
- Embedded QR code for mobile scanning
- Professional layout with delivery instructions
- Status indicators and approval tracking
- Mobile-responsive design

## Usage Instructions

### Thai Withholding Tax Workflow

#### 1. Payment Entry Setup
1. Create or edit Payment Entry for supplier payment
2. Enable "Apply Thai Withholding Tax" checkbox
3. System automatically suggests rate based on service type:
   - **3%** for general services and consulting
   - **5%** for professional services and rental
   - **2%** for advertising
   - **1%** for transportation
4. Enter supplier's 13-digit Thai Tax ID
5. WHT amount calculates automatically: `Paid Amount × Rate ÷ 100`

#### 2. Certificate Generation
1. Save and submit Payment Entry
2. Click "Generate WHT Certificate" button
3. Certificate generates using Thai Form 50 ทวิ format
4. Print or save PDF for records
5. Optional: Create Journal Entry for accounting

#### 3. Purchase Invoice Integration
1. Enable WHT during invoice processing
2. System calculates outstanding amount after WHT deduction
3. Links automatically to subsequent Payment Entry

### QR Delivery Approval Workflow

#### 1. Delivery Note Processing
1. Create and submit Delivery Note
2. QR code generates automatically after submission
3. Print delivery note with embedded QR code

#### 2. Customer Approval Process
1. Customer scans QR code with mobile device
2. Mobile-friendly approval page opens
3. Customer can:
   - Approve delivery with digital signature
   - Reject delivery with reason
   - Add comments and feedback

#### 3. Status Tracking
1. Approval status updates automatically in ERPNext
2. Dashboard indicators show real-time status
3. Audit trail maintains complete history

## API Integration

### REST Endpoints

#### Calculate WHT Amount
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

#### Generate WHT Certificate
```bash
POST /api/method/print_designer.api.withholding_tax_api.generate_wht_certificate
{
    "document_name": "PAY-2024-001",
    "doctype": "Payment Entry"
}
```

#### Get WHT Summary Report
```bash
GET /api/method/print_designer.api.withholding_tax_api.get_wht_summary_report
?from_date=2024-01-01&to_date=2024-12-31&company=My Company Ltd
```

#### Validate Thai Tax ID
```bash
POST /api/method/print_designer.api.withholding_tax_api.validate_supplier_tax_id
{
    "tax_id": "1234567890123"
}
```

### QR Code Generation API
```bash
POST /api/method/print_designer.custom.delivery_note_qr.generate_delivery_approval_qr
{
    "delivery_note_name": "DN-2024-001"
}
```

## Configuration and Customization

### WHT Rate Configuration

Modify rates in `custom/withholding_tax.py`:

```python
THAI_WHT_RATES = {
    "professional_service": {
        "rate": 5.0,
        "description": "ค่าธรรมเนียมวิชาชีพ",
        "keywords": ["professional", "legal", "accounting", "medical"]
    },
    "consulting": {
        "rate": 3.0,
        "description": "ค่าที่ปรึกษา",
        "keywords": ["consulting", "advisory", "management"]
    },
    # Add more as needed
}
```

### Company Setup

#### 1. Configure Company Tax Settings
1. Go to **Company** master
2. Set **Tax ID** field with 13-digit company tax ID
3. Configure **Default WHT Payable Account**

#### 2. Chart of Accounts Setup
Create account: **"Withholding Tax Payable"**
- Account Type: **Payable**
- Account Number: **2190**
- Parent Account: **Current Liabilities**

#### 3. Supplier Setup
1. Add 13-digit **Tax ID** for suppliers
2. Set appropriate **Supplier Group** for rate suggestions
3. Configure **Default Payable Account**

### Print Format Customization

#### Add Company Logo
```json
{
    "type": "image",
    "image": {
        "fieldname": "company_logo"
    },
    "startX": 50,
    "startY": 20,
    "width": 100,
    "height": 50
}
```

#### Customize QR Code Size
```json
{
    "type": "barcode",
    "barcodeFormat": "qrcode",
    "width": 150,
    "height": 150,
    "barcodeColor": "#000000",
    "barcodeBackgroundColor": "#ffffff"
}
```

#### Thai Font Configuration
The system includes complete Thai font support:
- **Kanit** - Modern sans-serif
- **Mitr** - Rounded friendly
- **Sarabun** - Clean professional
- **Prompt** - Geometric modern

## Troubleshooting

### Common Issues and Solutions

#### WHT Not Calculating
**Problem**: WHT amount not updating automatically
**Solutions**:
1. Verify `custom_is_withholding_tax` checkbox is enabled
2. Check that tax rate > 0 and < 30
3. Ensure paid_amount/grand_total > 0
4. Clear cache and refresh form

#### Certificate Not Generating
**Problem**: WHT certificate button not working
**Solutions**:
1. Verify Print Format "Payment Entry Form 50 ทวิ" exists
2. Check supplier Tax ID is present and valid
3. Ensure document is submitted (docstatus = 1)
4. Check browser console for JavaScript errors

#### QR Code Not Showing
**Problem**: QR code not generating in delivery notes
**Solutions**:
1. Check if `qrcode` Python package is installed
2. Verify custom fields exist on Delivery Note
3. Ensure document is submitted
4. Check error logs for PIL/image processing issues

#### Thai Fonts Not Displaying
**Problem**: Thai text showing boxes or incorrect characters
**Solutions**:
1. Verify Thai fonts are installed on server
2. Check print format font family settings
3. Clear browser cache and reload
4. Ensure proper UTF-8 encoding

#### Permission Issues
**Problem**: Users cannot access WHT features
**Solutions**:
1. Add permissions for custom fields in **Role Permission Manager**
2. Check **Print Format** permissions for user roles
3. Verify **Website Settings** for approval page access
4. Grant **Journal Entry** create permissions for WHT journal entries

#### API Errors
**Problem**: API endpoints returning errors
**Solutions**:
1. Check if user has proper API access permissions
2. Verify all required parameters are provided
3. Check error logs for detailed error messages
4. Ensure proper authentication tokens

### Debug Mode

Enable debug logging:
```python
# In ERPNext console
frappe.log_error("WHT Debug Info", "WHT System")

# Check field values
print(doc.custom_is_withholding_tax)
print(doc.custom_withholding_tax_rate)
print(doc.custom_withholding_tax_amount)
```

### System Health Check

Run comprehensive system check:
```bash
# Check installation status
bench --site your-site.com check-system-status

# Verify custom fields
bench --site your-site.com execute "
from print_designer.api.system_setup import check_system_health
result = check_system_health()
print(result)
"
```

## Security Considerations

### Data Protection
1. **Tax ID Encryption**: Consider encrypting supplier tax IDs
2. **Certificate Storage**: Secure certificate file storage
3. **Access Logging**: Enable audit logging for sensitive operations
4. **Permission Framework**: Use role-based access control

### QR Code Security
1. **Authentication**: QR approval links should require authentication
2. **Expiration**: Consider adding expiration times to approval URLs
3. **Rate Limiting**: Implement rate limiting for approval endpoints
4. **Audit Trail**: Log all approval activities

### API Security
1. **Authentication**: All API endpoints require proper authentication
2. **Input Validation**: Comprehensive input validation and sanitization
3. **Rate Limiting**: Implement rate limiting for calculation APIs
4. **Error Handling**: Secure error messages without information disclosure

## Performance Optimization

### Database Optimization
- Indexes on WHT-related fields for faster queries
- Efficient query patterns for reports
- Caching of frequently accessed rate data

### PDF Generation
- Optimized Chrome CDP process management
- Efficient template rendering
- Proper resource cleanup

### Client-Side Performance
- Lazy loading of QR generation
- Debounced calculation functions
- Optimized CSS with minimal impact

## Support and Documentation

### Additional Resources
- **System Documentation**: See `WITHHOLDING_TAX.md` for detailed system reference
- **Client Scripts**: See `CLIENT_SCRIPTS.md` for frontend functionality
- **API Reference**: Complete API documentation in main documentation files

### Getting Help
1. **Check System Status**: Use built-in status checking commands
2. **Review Logs**: Check Frappe error logs for detailed information
3. **Validate Setup**: Verify all custom fields and accounts exist
4. **Test APIs**: Use API endpoints to isolate issues

### Version Compatibility
- **ERPNext**: V15+ required for proper Vue 3 support
- **Frappe Framework**: V15+ required
- **Python**: 3.10+ recommended
- **Node.js**: Latest LTS for frontend builds

## License and Compliance

This Thai WHT system is developed specifically for compliance with Thai Revenue Department requirements and follows all applicable tax regulations. The system is provided as part of the Print Designer app under AGPLv3 license.

**Government Compliance Features:**
- Form 50 ทวิ exact replica of official form
- Thai Tax ID validation with proper checksum
- Income classification per Thai tax law
- Certificate numbering standards
- Audit trail requirements

---

**Installation Complete!** 🎉

Your Thai Withholding Tax Certificate and QR Delivery Approval system is now ready for production use. The system provides complete government compliance while streamlining your business operations.