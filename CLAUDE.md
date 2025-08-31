# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Print Designer Overview

Print Designer is a Frappe application for creating professional print formats using an interactive visual designer. It provides a drag-and-drop interface for designing complex layouts without coding, with particular strength in Thai language support, digital signatures, and advanced PDF generation.

## Core Architecture

### High-Level System Design
Print Designer operates as a comprehensive print format creation system with:

- **Visual Designer**: Vue.js-based drag-and-drop interface for creating print layouts
- **Template Engine**: JSON-based format definitions with Jinja2 rendering
- **Multi-PDF Generator Support**: wkhtmltopdf, WeasyPrint, and Chrome CDP generators
- **Thai Business Features**: Specialized support for Thai tax forms, signatures, and language
- **Extensible Hook System**: Template installation and custom field management

### Key Component Relationships

```
Frontend (Vue.js) → JSON Format Definition → Python Template Renderer → PDF Generator
     ↑                     ↓                          ↓                    ↓
Print Designer UI → print_designer_body → Jinja2 Templates → PDF Output
```

### Core File Structure
```
print_designer/
├── print_designer/
│   ├── page/print_designer/          # Vue.js frontend application
│   ├── doctype/                      # Custom DocTypes (signatures, stamps, etc.)
│   └── overrides/                    # DocType extensions
├── default_templates/                # Auto-installed print templates 
├── api/                             # REST API endpoints
├── commands/                        # Bench command implementations
├── custom/                          # Document event handlers
├── pdf_generator/                   # Multi-engine PDF generation
├── utils/                          # Utilities (Thai language, signatures)
└── public/                         # Frontend assets and fonts
```

## Development Commands

### Essential Development Workflow
```bash
# Start development environment
bench start

# Build frontend assets (Vue.js components)
bench build --app print_designer
bench watch  # Auto-rebuild on changes

# Development debugging
bench --site [site-name] console
bench execute print_designer.utils.test_pdf_generation.test_pdf_generation

# System installation and verification
bench execute print_designer.commands.install_complete_system.install_complete_system
bench execute print_designer.commands.install_complete_system.check_system_status
```

### Template and Field Management
```bash
# Print template management
bench execute print_designer.default_formats.install_default_formats
bench --site [site-name] export-fixtures --app print_designer

# Thai-specific installations
bench execute print_designer.commands.install_thai_form_50_twi.install_thai_form_50_twi
bench execute print_designer.commands.install_item_service_field.install_item_service_field

# Field validation and checks
bench execute print_designer.commands.install_thailand_wht_fields.check_thailand_wht_fields
bench execute print_designer.commands.install_item_service_field.check_item_service_field

# Signature and stamp system
bench execute print_designer.commands.signature_setup.setup_signatures
bench execute print_designer.commands.signature_setup.check_signature_status

# Watermark system
bench execute print_designer.commands.install_watermark_fields.install_watermark_fields
```

### PDF Generation Testing
```bash
# Test different PDF generators
bench execute print_designer.commands.test_pdf_generators.test_all_generators

# Chrome CDP setup (required for advanced PDF features)
bench execute print_designer.install.setup_chromium
```

## Architecture Patterns

### Print Template Installation System
Print Designer uses a sophisticated template installation system:

1. **Template Discovery**: `default_formats.py` scans all installed apps for templates
2. **Hook-Based Loading**: Apps declare templates via `pd_standard_format_folder` hook
3. **Automatic Installation**: Templates auto-install during app installation/migration
4. **JSON Format**: Templates stored as JSON files in `default_templates/[app_name]/`

**Key Functions:**
- `on_print_designer_install()`: Installs templates for all apps during Print Designer setup
- `install_default_formats()`: Core template installation logic
- `get_filtered_formats_by_app()`: Template discovery and filtering

### Custom Field Management
Print Designer extensively uses custom fields across DocTypes:

1. **Fixture-Based**: Core fields defined in `fixtures/custom_field.json`
2. **Programmatic**: Complex fields installed via command modules
3. **Safe Migration**: Fields installed safely during app updates
4. **Dependency Handling**: Fields with proper `depends_on` conditions

**Installation Hooks:**
- `after_install`: Fresh installations
- `after_migrate`: Updates and migrations
- Emergency fallback functions for critical fields

### PDF Generation Architecture
Multi-engine PDF generation system supporting:

1. **wkhtmltopdf**: Default, reliable for most use cases
2. **WeasyPrint**: Better CSS support, good for complex layouts  
3. **Chrome CDP**: Advanced features, headless Chrome via CDP protocol

**Key Components:**
- `pdf_generator/`: Engine abstraction layer
- `pdf.py`: Template rendering and language handling
- Chromium auto-download and management system

### Thai Language & Business Support
Specialized features for Thai business requirements:

1. **Font System**: Kanit, Noto Sans Thai, Sarabun fonts included
2. **Language Detection**: URL parameter → Print Format → Fallback priority
3. **Amount Conversion**: Thai money-to-words conversion
4. **Tax Forms**: Form 50TWI, WHT certificates, VAT compliance
5. **Signatures**: Digital signatures with company stamps

## Code Quality Standards

### Frontend Standards
- Vue.js 3 Composition API
- ESBuild for bundling
- Bundle suffix naming: `.bundle.css`, `.bundle.js` (mandatory)
- SCSS for styling

### Python Standards
- Type hints preferred
- Error logging via `frappe.log_error()`
- Defensive programming for missing fields/documents
- Import isolation (try/except for optional dependencies)

### Testing Approach
- Console-based testing via `bench execute` 
- PDF generation testing across all engines
- Field installation verification
- Template rendering validation

#### Test Structure Example
```python
# print_designer/print_designer/tests/test_pdf_generation.py
import frappe
import unittest
from frappe.tests.utils import FrappeTestCase

class TestPDFGeneration(unittest.TestCase):  # or FrappeTestCase
    def setUp(self):
        # Test setup for PDF generation
        self.test_invoice = frappe.get_doc("Sales Invoice", "TEST-SINV-001")
        pass
    
    def test_pdf_generation_all_engines(self):
        """Test PDF generation across all three engines"""
        engines = ["wkhtmltopdf", "weasyprint", "chrome_cdp"]
        
        for engine in engines:
            with self.subTest(engine=engine):
                pdf_data = self.generate_pdf_with_engine(engine)
                self.assertIsNotNone(pdf_data)
                self.assertTrue(len(pdf_data) > 1000)  # Valid PDF should be >1KB
    
    def test_thai_language_rendering(self):
        """Test Thai language font rendering in PDF"""
        thai_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": "ลูกค้าทดสอบ",
            "language": "th"
        })
        pdf_data = self.generate_pdf_with_thai_fonts(thai_invoice)
        self.assertIsNotNone(pdf_data)
    
    def test_digital_signature_integration(self):
        """Test digital signature embedding in PDF"""
        signature = frappe.get_doc("Digital Signature", "Company Seal")
        pdf_with_signature = self.generate_pdf_with_signature(signature)
        self.assertIsNotNone(pdf_with_signature)
    
    def tearDown(self):
        # Clean up test data
        pass
```

## Key Integration Points

### Hook System Integration
Print Designer integrates deeply with Frappe's hook system:

```python
# Document events for calculations
doc_events = {
    "Sales Invoice": {
        "validate": "print_designer.custom.sales_invoice_calculations.sales_invoice_calculate_thailand_amounts"
    }
}

# Override core Frappe methods  
override_whitelisted_methods = {
    "frappe.utils.print_format.download_pdf": "print_designer.utils.signature_stamp.download_pdf_with_signature_stamp"
}
```

### Template Discovery System
Apps can provide Print Designer templates:

```python
# In app's hooks.py
pd_standard_format_folder = "my_templates"  # Directory containing templates
```

### Custom Field Dependencies
Complex field relationships using `depends_on`:

```python
"depends_on": "eval:doc.subject_to_wht"  # Field visibility logic
"insert_after": "net_total"             # Field positioning
```

## Development Standards

### Custom Field Management (MANDATORY)

#### Naming Convention
All custom fields created by print_designer MUST follow this naming pattern:
- **App Name**: print_designer  
- **Prefix**: `pd_custom_`
- **Pattern**: `pd_custom_{descriptive_field_name}`
- **Label**: Can be human-readable without prefix

```python
# CORRECT - Following naming convention
"Sales Invoice": [
    {
        "fieldname": "pd_custom_watermark_per_page",
        "label": "Watermark per Page",
        "fieldtype": "Check",
        "default": 0,
        "insert_after": "print_language"
    }
]

# INCORRECT - Missing prefix (legacy fields, to be migrated)
"Sales Invoice": [
    {
        "fieldname": "watermark_per_page",  # Missing pd_custom_ prefix
        "label": "Watermark per Page",
        "fieldtype": "Check",
        "default": 0,
        "insert_after": "print_language"
    }
]
```

**Note**: Some legacy fields may not follow this convention yet. New fields MUST use the `pd_custom_` prefix, and existing fields should be migrated when modified.

### Test Folder Structure (MANDATORY)
All test files MUST be placed in the designated tests folder following ERPNext standards:

```
print_designer/
├── print_designer/
│   └── tests/                    # MANDATORY test folder location
│       ├── __init__.py          # Required for Python module
│       ├── test_print_format.py          # Print format creation tests
│       ├── test_pdf_generation.py        # PDF generation engine tests
│       ├── test_signature_stamp.py       # Digital signature tests
│       └── test_thai_language.py         # Thai language support tests
├── api/
│   └── tests/                    # API-specific tests (if needed)
│       ├── __init__.py
│       └── test_print_api.py     # Print API endpoint tests
├── commands/
│   └── tests/                    # Command installation tests (if needed)
│       ├── __init__.py
│       └── test_field_installation.py
└── utils/
    └── tests/                    # Utility function tests (if needed)
        ├── __init__.py
        └── test_pdf_utils.py
```

**Reference Standard**: Follow `apps/erpnext/erpnext/tests` structure as documented in Documentation/rules.md

**Rules**:
1. **All test files** MUST be in `app_name/app_name/tests/` folder
2. **Test files** MUST start with `test_` prefix
3. **Each module** can have its own tests subfolder if complex
4. **Import pattern**: `from print_designer.tests.test_module import TestClass`

## Development Best Practices

### Template Development
1. Create templates in `default_templates/[app_name]/`
2. Use descriptive naming: `doctype_purpose_version.json`
3. Test template installation via `install_default_formats()`
4. Include bilingual labels for Thai business

### Custom Field Development  
1. Define in fixtures for version control
2. Use programmatic installation for complex fields
3. Always provide fallback/migration functions
4. Test field installation across different ERPNext versions

### PDF Generation
1. Test across all three PDF generators
2. Handle Chrome CDP errors gracefully (pipe errors)
3. Use appropriate fonts for Thai text
4. Implement proper language detection

### Error Handling
1. Use `frappe.log_error()` for persistent logging
2. Graceful degradation when optional features fail
3. Defensive checks for missing custom fields
4. Clear error messages for users

## Thai Business Specializations

### Withholding Tax System
- Custom fields: `subject_to_wht`, `wht_income_type`, `net_total_after_wht`  
- Calculation hooks in document validation
- Thai revenue department form compliance
- Multi-document WHT calculation (Quotation → Sales Order → Sales Invoice)

### Signature & Stamp System  
- Company signatures and official seals
- Digital signature DocTypes
- Integration with print templates via Jinja methods
- Signature usage tracking and analytics

### Thai Language Features
- Font loading: Kanit, Noto Sans Thai, Sarabun
- Amount to words conversion in Thai
- Language detection: URL params → format language → system default
- Proper RTL/LTR handling for mixed content

---

## Development Rules & Standards

### Custom Field Naming Convention (MANDATORY)
Following [Documentation/rules.md](/home/frappe/frappe-bench/Documentation/rules.md):

- **App Name**: print_designer
- **Prefix**: `pd_custom_` (suggested print-designer prefix)
- **Pattern**: `pd_custom_{descriptive_field_name}`

#### Examples
```python
# ✅ CORRECT - Following naming convention
custom_field = {
    "fieldname": "pd_custom_subject_to_wht",
    "fieldtype": "Check",
    "label": "Subject to WHT"
}

# ❌ INCORRECT - Missing app-specific prefix (current usage)
custom_field = {
    "fieldname": "subject_to_wht",  # Should be pd_custom_subject_to_wht
    "fieldtype": "Check",
    "label": "Subject to WHT"
}
```

### Current Custom Fields Requiring Updates
Based on the Thai business specializations mentioned:
- `subject_to_wht` → `pd_custom_subject_to_wht`
- `wht_income_type` → `pd_custom_wht_income_type`
- `net_total_after_wht` → `pd_custom_net_total_after_wht`

### Testing Standards
- **Test Location**: `print_designer/print_designer/tests/`
- **Reference**: Follow `apps/erpnext/erpnext/tests` structure
- **Docs**: https://docs.frappe.io/framework/user/en/testing

### Uninstall Compliance
- **Requirement**: All custom fields MUST be removed during app uninstallation
- **Implementation**: Add `before_uninstall` hook in `hooks.py`
- **Reference Issue**: https://github.com/frappe/frappe/issues/24108

#### Current Status
⚠️ **Action Required**: print_designer custom fields need to be updated with proper `pd_custom_` prefix for namespace isolation.

### File Creation Guidelines
- Scan relevant files before creating new ones to prevent redundancy
- Check hooks.py regularly for duplicated functions or redundancy
- Follow ERPNext Custom Field Guidelines consistently

### Priority Compliance Items
1. **Update custom field naming** to use `pd_custom_` prefix
2. **Add uninstall functionality** to clean up all custom fields
3. **Update test structure** to follow ERPNext standards
4. **Review hooks.py** for any redundancy

## Payment Entry References Architecture

### Overview
The Payment Entry `references` field is a sophisticated system for linking payments to outstanding invoices, providing real-time tracking of payment allocation across multiple invoices.

### Core Components

#### 1. Frontend Structure (`references` field)
- **Field Type**: Table field linking to `Payment Entry Reference` DocType
- **Purpose**: Track which invoices are being paid and allocation amounts
- **Location**: Payment Entry → References section

#### 2. Payment Entry Reference DocType Fields
```python
# Key fields in Payment Entry Reference
- reference_doctype     # Link to DocType (Sales Invoice, Purchase Invoice)  
- reference_name        # Dynamic Link to actual invoice
- total_amount         # Full invoice amount
- outstanding_amount   # Remaining unpaid amount  
- allocated_amount     # Amount being allocated in this payment
- due_date            # Invoice due date
- account             # Receivable/Payable account
- payment_term        # Payment terms if applicable
```

#### 3. Data Fetching Flow

**Frontend Trigger (JavaScript)**:
```javascript
// User clicks "Get Outstanding Invoices" button
get_outstanding_invoices: function (frm) {
    frm.events.get_outstanding_invoices_or_orders(frm, true, false);
}

// Makes server call to fetch outstanding invoices
frappe.call({
    method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents",
    args: { args: filters },
    callback: function (r, rt) {
        // Populates references table with returned data
    }
});
```

**Backend Processing**:
```python
# Server method calls get_outstanding_invoices()
outstanding_invoices = get_outstanding_invoices(
    party_type,              # Customer/Supplier
    party,                   # Specific party
    [party_account],         # Receivable/Payable account  
    common_filter=filters,   # Company, date filters
    vouchers=specific_vouchers  # Optional voucher filtering
)
```

#### 4. Payment Ledger Integration

**Core Data Source**: `Payment Ledger Entry` table tracks:
- **Invoice Creation**: Records full invoice amounts when invoices are submitted
- **Payment Processing**: Records payment amounts when payments are made
- **Outstanding Calculation**: Real-time calculation (invoice_amount - payments_made)
- **Multi-Currency Support**: Handles different currencies with exchange rates

**Query Architecture**:
```python
# Uses QueryPaymentLedger class for complex CTE queries
# Combines voucher amounts with outstanding calculations
query_voucher_amount = qb.from_(ple).select(
    ple.voucher_type, ple.voucher_no, ple.outstanding_amount,
    ple.invoice_amount, ple.due_date, ple.currency
).where(outstanding_conditions)
```

### 5. Thai Business Integration

**Custom Fields Added by Print Designer**:
```python
# Payment Entry Reference custom fields (pd_custom_ prefixed)
pd_custom_has_retention         # Thai retention flag
pd_custom_retention_amount      # Retention amount for construction
pd_custom_retention_percentage  # Retention rate
pd_custom_wht_amount           # Withholding tax amount
pd_custom_wht_percentage       # WHT rate
pd_custom_vat_undue_amount     # VAT undue conversion amount
pd_custom_net_payable_amount   # Final amount after deductions
```

**Business Logic Integration**:
- **Construction Retention**: Automatically calculated based on invoice service type
- **Thai WHT**: Withholding tax calculations per invoice reference
- **VAT Processing**: Handles Output VAT Undue to VAT Due conversion
- **Multi-Tax Summary**: Aggregates all tax components at Payment Entry level

### 6. Reference Population Process

1. **User Interaction**: User selects party and clicks "Get Outstanding Invoices"
2. **Server Query**: System queries Payment Ledger for unpaid invoices  
3. **Data Processing**: Filters, sorts, and calculates outstanding amounts
4. **Table Population**: JavaScript populates references table with:
   ```javascript
   c.reference_doctype = d.voucher_type;    // "Sales Invoice"
   c.reference_name = d.voucher_no;         // "SINV-001"
   c.outstanding_amount = d.outstanding_amount;  // Remaining unpaid
   c.total_amount = d.invoice_amount;       // Full invoice amount
   c.allocated_amount = d.allocated_amount; // Amount to allocate
   ```
5. **User Allocation**: User can modify allocated amounts per invoice
6. **Validation**: System ensures allocations don't exceed outstanding amounts

### 7. Real-Time Balance Tracking

**Payment Ledger Entry Workflow**:
- **Invoice Submission**: Creates positive PLE entries (amounts owed)
- **Payment Submission**: Creates negative PLE entries (amounts paid)  
- **Outstanding Calculation**: Sum of all PLE entries per invoice
- **Multi-Payment Support**: Single invoice can have multiple partial payments
- **Cancellation Handling**: Reverses PLE entries when documents are cancelled

### 8. Advanced Features

**Payment Terms Integration**:
- Splits invoices by payment terms when applicable
- Tracks outstanding per payment term
- Enables term-based payment allocation

**Multi-Currency Handling**:
- Exchange rate tracking per transaction date
- Currency conversion for outstanding calculations
- Party account currency vs company currency reconciliation

**Performance Optimizations**:
- Uses Common Table Expressions (CTE) for complex queries
- Indexes on Payment Ledger Entry for fast lookups
- Caching of frequently accessed data

This architecture provides a robust foundation for payment processing, ensuring accurate tracking of invoice payments while supporting complex business requirements like Thai tax compliance and construction retention handling.
