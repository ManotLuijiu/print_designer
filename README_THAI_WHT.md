# Thai Withholding Tax & QR Delivery System - Documentation Index

This comprehensive system provides Thai government-compliant withholding tax certificate generation and QR-based delivery approval functionality for ERPNext's Print Designer app.

## 📚 Documentation Overview

### 🚀 Quick Start
- **[INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)** - Complete installation instructions with step-by-step setup
- **Installation Command**: `bench --site your-site.com install-complete-system`

### 📖 System Documentation

#### Core System Reference
- **[WITHHOLDING_TAX.md](./WITHHOLDING_TAX.md)** - Complete system documentation
  - Usage workflows and features
  - API documentation with examples
  - Thai tax compliance details
  - Configuration and customization
  - Troubleshooting guide

#### Frontend Documentation  
- **[CLIENT_SCRIPTS.md](./CLIENT_SCRIPTS.md)** - Client-side functionality
  - Interactive UI components
  - QR code dialog system
  - Real-time WHT calculations
  - Mobile-responsive features
  - JavaScript API reference

## 🔧 System Components

### Backend Modules
- `custom/withholding_tax.py` - Core WHT calculation and certificate system
- `custom/delivery_note_qr.py` - QR code generation and approval tracking
- `api/withholding_tax_api.py` - REST API endpoints
- `setup/install.py` - Automated installation system

### Frontend Components
- `public/js/delivery_approval.js` - Enhanced UI for both systems
- `public/css/delivery_approval.bundle.scss` - Professional styling

### Integration Points
- `hooks.py` - Document events and Jinja methods
- Custom fields for Payment Entry, Purchase Invoice, and Delivery Note
- Print formats with Thai language support

## ✨ Key Features

### Thai Withholding Tax System
- ✅ **Government Compliant**: Form 50 ทวิ exact replica
- ✅ **Automatic Calculations**: Real-time WHT with rate suggestions
- ✅ **Thai Language Support**: Buddhist calendar and proper formatting
- ✅ **Multiple DocTypes**: Payment Entry and Purchase Invoice support
- ✅ **Journal Entry Integration**: Automatic accounting entries
- ✅ **Comprehensive API**: REST endpoints for external integration
- ✅ **Reporting & Analytics**: Summary reports and tax filing data

### QR Delivery Approval System
- ✅ **Mobile-Friendly**: Responsive QR approval interface
- ✅ **Digital Signatures**: Customer signature collection
- ✅ **Real-time Updates**: Automatic status synchronization
- ✅ **Professional Print**: QR-embedded delivery notes
- ✅ **Audit Trail**: Complete approval history tracking

## 🎯 Quick Usage

### Thai Withholding Tax
1. **Enable WHT** on Payment Entry or Purchase Invoice
2. **Set Rate** (3% services, 5% professional, 1% transport, etc.)
3. **Enter Tax ID** (13-digit Thai format with validation)
4. **Generate Certificate** with Form 50 ทวิ compliance
5. **Create Journal Entry** for accounting integration

### QR Delivery Approval
1. **Submit Delivery Note** (QR generates automatically)
2. **Print with QR** using enhanced print format
3. **Customer Scans QR** on mobile device
4. **Approve/Reject** with digital signature
5. **Status Updates** automatically in ERPNext

## 🔗 API Quick Reference

### Calculate WHT
```bash
POST /api/method/print_designer.api.withholding_tax_api.calculate_wht_amount
```

### Generate Certificate
```bash
POST /api/method/print_designer.api.withholding_tax_api.generate_wht_certificate
```

### WHT Summary Report
```bash
GET /api/method/print_designer.api.withholding_tax_api.get_wht_summary_report
```

### Validate Tax ID
```bash
POST /api/method/print_designer.api.withholding_tax_api.validate_supplier_tax_id
```

## 🛠️ Installation Status Check

```bash
# Check complete system status
bench --site your-site.com check-system-status

# Manual health check
bench --site your-site.com execute "
from print_designer.api.system_setup import check_system_health
print(check_system_health())
"
```

## 📋 System Requirements

- **ERPNext V15+** with Print Designer app
- **Python 3.10+** with `qrcode[pil]`, `pypng`, `python-barcode`
- **Chrome/Chromium** for PDF generation
- **Admin access** to ERPNext instance

## 🔍 Troubleshooting Quick Reference

### WHT Issues
- **Not Calculating**: Check checkbox enabled, rate > 0, amount > 0
- **Certificate Errors**: Verify print format exists, Tax ID present
- **Permission Issues**: Check role permissions for custom fields

### QR Issues  
- **Not Generating**: Install `qrcode` package, verify custom fields
- **Display Problems**: Check PIL installation, image processing
- **Mobile Issues**: Test responsive design, approval page access

### General Issues
- **Thai Fonts**: Verify font installation and UTF-8 encoding
- **API Errors**: Check authentication, parameter validation
- **Performance**: Monitor Chrome processes, optimize queries

## 🎉 Ready to Use!

The Thai Withholding Tax and QR Delivery Approval system is production-ready with:

- **Complete Government Compliance** 🇹🇭
- **Professional User Interface** ✨  
- **Comprehensive API Integration** 🔗
- **Robust Error Handling** 🛡️
- **Mobile-Responsive Design** 📱
- **Complete Documentation** 📚

---

**Need Help?** Check the detailed documentation files above or run the system status check to identify any configuration issues.