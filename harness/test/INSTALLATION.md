# Print Designer Complete System Installation

This document explains how to install and use the complete Print Designer system with Thai Withholding Tax Certificate and QR Delivery Approval features.

## Quick Installation

### Method 1: Bench Command (Recommended)
```bash
# Install complete system
bench --site your-site.com install-complete-system

# Check installation status
bench --site your-site.com check-system-status
```

### Method 2: Python API
```python
# In Frappe console
from print_designer.setup.install import setup_thai_withholding_tax_and_qr_delivery
result = setup_thai_withholding_tax_and_qr_delivery()
print(result)
```

### Method 3: REST API
```bash
# Install via API
curl -X POST "https://your-site.com/api/method/print_designer.api.system_setup.install_complete_system" \
  -H "Authorization: token api_key:api_secret"

# Check status via API  
curl "https://your-site.com/api/method/print_designer.api.system_setup.get_system_status" \
  -H "Authorization: token api_key:api_secret"
```

## Features Installed

### 🏛️ Thai Form 50 ทวิ (Withholding Tax Certificate)
- **Purpose**: Generate government-compliant withholding tax certificates
- **DocType**: Payment Entry
- **Print Format**: "Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate"
- **Custom Fields**: 7 fields for tax calculation and compliance

### 📱 QR Code Delivery Approval System  
- **Purpose**: Customer delivery confirmation via QR code scanning
- **DocType**: Delivery Note
- **Print Format**: "Delivery Note with QR Approval" 
- **Custom Fields**: 8 fields for approval workflow
- **Web Interface**: Bootstrap 5 responsive design at `/delivery-approval/{id}`

## Usage Instructions

### Thai Withholding Tax Certificate

1. **Create Payment Entry**
   - Go to Accounting > Payment Entry
   - Select supplier and payment details

2. **Enable Withholding Tax**
   - Check "Apply Thai Withholding Tax" 
   - Set tax rate (3% for services, 1% for rental, 5% for royalty)
   - Enter supplier's 13-digit Tax ID

3. **Generate Certificate**
   - Save and submit Payment Entry
   - Tax amount calculated automatically
   - Certificate number auto-generated

4. **Print Certificate**
   - Use "Payment Entry Form 50 ทวิ" print format
   - Thai language support included
   - Government-compliant layout

### QR Delivery Approval System

1. **Create Delivery Note**
   - Go to Stock > Delivery Note
   - Add customer and items

2. **Submit for QR Generation**
   - Submit Delivery Note
   - QR code automatically generated
   - Approval URL created

3. **Print with QR Code**
   - Use "Delivery Note with QR Approval" format
   - QR code appears in approval section
   - Professional layout with instructions

4. **Customer Approval Process**
   - Customer scans QR code
   - Opens mobile-friendly web interface
   - Reviews delivery details
   - Approves with optional digital signature
   - Or rejects with reason

5. **Status Tracking**
   - Real-time status updates
   - Approval timestamps recorded
   - Digital signatures stored
   - Audit trail maintained

## System Components

### Custom Fields Added

**Delivery Note:**
- `custom_delivery_approval_section` - Section break
- `custom_goods_received_status` - Select (Pending/Approved/Rejected) 
- `custom_approval_qr_code` - QR code data (Base64)
- `custom_approval_url` - Web approval URL
- `custom_customer_approval_date` - Approval timestamp
- `custom_approved_by` - User who approved
- `custom_customer_signature` - Digital signature image
- `custom_rejection_reason` - Rejection details

**Payment Entry:**
- `custom_thai_withholding_tax_section` - Section break
- `custom_is_withholding_tax` - Enable tax calculation
- `custom_withholding_tax_rate` - Tax percentage
- `custom_withholding_tax_amount` - Calculated amount
- `custom_supplier_tax_id` - Supplier Tax ID
- `custom_wht_certificate_number` - Certificate number
- `custom_wht_certificate_generated` - Generation status

### API Endpoints

**QR Delivery System:**
- `generate_delivery_approval_qr(delivery_note_name)` - Generate QR code
- `approve_delivery_goods(delivery_note_name, signature)` - Approve delivery
- `reject_delivery_goods(delivery_note_name, reason)` - Reject delivery  
- `get_delivery_status(delivery_note_name)` - Get approval status
- `get_qr_code_image(delivery_note_name)` - Get QR image

**System Management:**
- `install_complete_system()` - Install all components
- `get_system_status()` - Check installation status
- `get_usage_instructions()` - Get detailed usage guide
- `repair_installation()` - Fix installation issues

### Print Formats

**Thai WHT Certificate:**
- Professional Thai government form layout
- Auto-populated tax calculations
- Certificate numbering system
- Thai language support

**QR Delivery Note:**
- Modern delivery note design
- Integrated QR code section
- Customer approval instructions
- Status tracking display

### Web Interface Features

**Delivery Approval Page:**
- URL Pattern: `/delivery-approval/{delivery_note_id}`
- Bootstrap 5 responsive design
- FontAwesome 6.0 icons
- Professional card-based layout
- SignaturePad.js integration
- Real-time status updates
- Error handling and feedback
- Mobile-optimized interface

## Troubleshooting

### Check Installation Status
```bash
bench --site your-site.com check-system-status
```

### Repair Installation
```bash
# Via API
curl -X POST "https://your-site.com/api/method/print_designer.api.system_setup.repair_installation"
```

### Common Issues

**Missing Custom Fields:**
- Run repair installation
- Check field permissions
- Verify DocType exists

**Print Format Not Available:**
- Ensure JSON templates exist in `default_templates/erpnext/`
- Check Print Format permissions
- Re-run installation

**QR Code Not Generated:**
- Verify Delivery Note is submitted
- Check QR code dependencies in `pyproject.toml`
- Review error logs

**Web Interface Not Loading:**
- Verify `delivery-approval.html` exists in `www/`
- Check web permissions
- Review network connectivity

### Dependencies

**Python Packages:**
- `qrcode[pil]` - QR code generation
- `frappe` - Framework integration

**Frontend Libraries:**
- Bootstrap 5.1.3
- FontAwesome 6.0.0
- SignaturePad.js 4.0.0

## Support

For technical support:
1. Check system status first
2. Review error logs in Frappe
3. Run repair installation if needed
4. Verify all dependencies are installed

## License

This installation system is part of Print Designer app and follows the same AGPLv3 license.