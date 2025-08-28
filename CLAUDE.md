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
