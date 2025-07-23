# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Print Designer Overview

Print Designer is a Frappe application for creating professional print formats using an interactive visual designer. It provides a drag-and-drop interface for designing complex layouts without coding, with particular strength in Thai language support, digital signatures, and advanced PDF generation.

## Development Setup

### Prerequisites
- Frappe Framework V15 or develop branch
- Node.js for frontend build
- Python 3.10+ with required dependencies
- Chrome/Chromium browser for PDF generation
- Required system packages for Chrome CDP functionality

### Local Development Commands
```bash
# Initial setup in frappe-bench
bench get-app print_designer
bench new-site print-designer.localhost --install-app print_designer
bench browse print-designer.localhost --user Administrator

# Development workflow
bench start                    # Start development server
bench watch                    # Watch and build frontend assets
bench build                    # Build all assets
bench migrate                  # Run database migrations

# Testing and debugging
bench execute print_designer.commands.test_pdf_generators.test_all_generators
bench execute print_designer.utils.test_pdf_generation.test_pdf_generation
bench --site [site-name] console  # Interactive Python console for debugging

# Signature and stamp setup
bench execute print_designer.commands.signature_setup.setup_signatures
bench execute print_designer.commands.signature_setup.check_signature_status
bench execute print_designer.commands.install_watermark_fields.install_watermark_fields
```

### Docker Development
```bash
# Quick Docker setup
mkdir frappe-pd && cd frappe-pd
wget -O docker-compose.yml https://raw.githubusercontent.com/frappe/print_designer/develop/docker/docker-compose.yml
docker compose up
```

## Architecture

### Frontend Architecture
- **Vue 3 Composition API**: Main frontend framework
- **Pinia Store**: State management via MainStore and ElementStore
- **Interactive Elements**: Drag-and-drop canvas with resizable components
- **Component Types**: StaticText, DynamicText, Image, Table, Rectangle, Barcode

### Backend Architecture
- **Frappe Framework**: Standard app structure with hooks.py integration
- **PDF Generation**: Custom CDP-based Chrome automation for complex layouts
- **Template System**: Jinja2 templates for dynamic content rendering
- **Print Format Override**: Extends Frappe's Print Format DocType

### PDF Generation System
The app uses a sophisticated Chrome DevTools Protocol (CDP) system bypassing standard wkhtmltopdf:

1. **FrappePDFGenerator** (`pdf_generator/generator.py`): Manages Chrome browser instances and coordinates PDF creation workflow
2. **Browser** (`pdf_generator/browser.py`): Handles browser lifecycle, page creation, and CDP communication setup
3. **CDPSocketClient** (`pdf_generator/cdp_connection.py`): WebSocket communication with Chrome DevTools Protocol
4. **Page** (`pdf_generator/page.py`): Individual page management for header, footer, and body with separate rendering contexts
5. **PDFTransformer** (`pdf_generator/pdf_merge.py`): Merges header, footer, and body PDFs using PyPDF operations

Critical workflow stages:
- Initialize Chrome browser process with CDP enabled
- Create separate pages for header, footer, and body content with isolated contexts
- Generate PDFs asynchronously for static elements to optimize performance
- Handle dynamic content (page numbers, signatures) with separate rendering passes
- Merge all PDFs into final output with proper page ordering and metadata

## Key Files and Directories

### Frontend Structure
- `print_designer/public/js/print_designer/App.vue`: Main Vue 3 application with Composition API
- `print_designer/public/js/print_designer/store/MainStore.js`: Global state management (Pinia)
- `print_designer/public/js/print_designer/store/ElementStore.js`: Element-specific state and operations
- `print_designer/public/js/print_designer/components/base/`: Core element components (Text, Image, Table, Barcode, Rectangle)
- `print_designer/public/js/print_designer/components/layout/`: UI layout components (Toolbar, Properties, Canvas, Modals)
- `print_designer/public/js/print_designer/composables/`: Reusable Vue logic (Draggable, Resizable, Element management)
- `print_designer/public/js/print_designer/defaultObjects.js`: Element creation functions and toolbar definitions

### Backend Structure
- `print_designer/hooks.py`: Frappe app integration, Jinja methods, doc events, and custom overrides
- `print_designer/pdf_generator/`: Chrome CDP PDF generation system (core PDF engine)
- `print_designer/print_designer/page/print_designer/`: Main page controller and Jinja templates
- `print_designer/print_designer/overrides/`: DocType overrides (Print Format extensions)
- `print_designer/utils/`: Utility modules (signature integration, Thai language support, PDF logging)
- `print_designer/api/`: API endpoints for signature management and safe installation

### Critical Templates and Macros
- `print_designer/print_designer/page/print_designer/jinja/macros/`: Jinja2 rendering macros for each element type
- `print_designer/print_designer/page/print_designer/jinja/print_format.html`: Main template for PDF rendering
- `print_designer/overrides/printview_watermark.py`: Watermark integration for print preview

### Configuration and Dependencies
- `package.json`: Frontend dependencies (interactjs for drag/drop, html2canvas, qrcode.vue)
- `pyproject.toml`: Python project configuration with PDF generation dependencies and code formatting rules
- `print_designer/custom_fields.py`: Custom field definitions for enhanced DocType functionality

## Development Workflow

### Frontend Development Patterns
- **Vue 3 Composition API**: All components use `<script setup>` syntax with reactive state management
- **Pinia State Management**: MainStore for global state, ElementStore for canvas element operations
- **InteractJS Integration**: Drag, drop, resize functionality with snap-to-grid and visual feedback
- **Canvas-based Design**: Absolute positioning system with precise pixel control and visual handles
- **Event-driven Architecture**: Element selection, property updates, and canvas interactions use reactive patterns

### Backend Development Patterns
- **Frappe Integration**: Custom Print Format override extends standard functionality while maintaining compatibility
- **Jinja2 Macro System**: Element rendering uses dedicated macros in `jinja/macros/` for consistent output
- **API Whitelisting**: All public endpoints use `@frappe.whitelist()` decorator for security
- **Hook-based Integration**: Uses Frappe hooks system for lifecycle events and custom overrides
- **PDF Generation Pipeline**: Custom CDP-based system replaces wkhtmltopdf for better control and output quality

### Code Quality Standards
- **Python Formatting**: Black with 99-character line length, isort for import organization
- **Type Hints**: Encouraged throughout Python codebase for better maintainability
- **Error Handling**: Comprehensive logging and error tracking for PDF generation and signature operations
- **Security**: Role-based permissions, input validation, and secure file handling for signatures/stamps

### Testing and Debugging
- **Manual Testing**: Primary testing through visual designer interface and PDF preview
- **PDF Generation Testing**: Requires Chrome/Chromium setup with proper CDP configuration
- **Debug Commands**: Use `bench --site [site-name] console` for interactive debugging
- **Logging**: Extensive logging in `utils/pdf_logging.py` for troubleshooting PDF generation issues

## Dependencies and Integrations

### Frontend Dependencies
- **InteractJS Suite**: `@interactjs/actions`, `@interactjs/modifiers`, `@interactjs/interact`, `@interactjs/auto-start` for comprehensive drag/drop/resize functionality
- **html2canvas**: Canvas-based screenshot generation for image capturing
- **qrcode.vue**: Vue 3 compatible QR code generation component
- **Vue 3 Ecosystem**: Composition API, Pinia stores (built into Frappe Framework)

### Backend Dependencies
- **PDF Generation**: `websockets` for CDP communication, `distro` for system detection
- **Barcode/QR Generation**: `PyQRCode`, `pypng`, `python-barcode` for various barcode formats
- **Alternative PDF**: `weasyprint` as fallback PDF generator
- **System Dependencies**: Extensive Chrome/Chromium packages listed in `pyproject.toml` for headless browser operation

### Thai Language Integration
- **Font Support**: Complete Thai font families (Kanit, Mitr, Sarabun, Prompt, etc.) in `public/fonts/thai/`
- **Text Processing**: `thai_amount_to_word.py` for Thai numerics and currency conversion
- **Cultural Formatting**: Thai-specific business document formats and templates

### Signature and Stamp System
- **Digital Signatures**: Custom DocTypes (`Digital Signature`, `Company Stamp`, `Signature Basic Information`)
- **Integration Points**: Hooks for signature embedding in PDF generation workflow
- **Security**: Role-based access and audit logging for signature usage

## Specialized Features and Capabilities

### Element Type System
- **StaticText**: Simple text with rich formatting options
- **DynamicText**: Jinja2-templated text with document field binding
- **Image**: Static images with positioning and scaling controls
- **Table**: Dynamic tables with document field mapping and styling
- **Rectangle**: Styled container elements with border and background options
- **Barcode**: QR codes and various barcode formats with data binding

### Advanced PDF Features
- **Multi-page Support**: Header, footer, and body sections with independent styling
- **Dynamic Content**: Page numbers, totals, and calculated fields
- **Watermark Integration**: Per-page watermark positioning and transparency
- **Font Management**: Google Fonts integration with Thai language support
- **Signature Embedding**: Digital signatures and company stamps with proper positioning

### Thai Language Specialization
- **Complete Font Coverage**: 8+ Thai font families with multiple weights and styles
- **Amount Conversion**: Thai currency and number-to-words conversion (`thai_money_in_words`)
- **Business Templates**: Pre-built Thai tax invoice and government form templates
- **Cultural Formatting**: Date formats, address layouts, and business conventions

### Integration Architecture
- **Frappe Hooks**: Deep integration with Frappe's event system and DocType lifecycle
- **Custom Fields**: Automated field installation for enhanced Print Format functionality
- **Override System**: Monkey-patching approach for extending core Frappe functionality without conflicts
- **API Endpoints**: RESTful APIs for signature management, template operations, and PDF generation

## Troubleshooting

### PDF Generation Issues
- **Chrome/Chromium Setup**: Ensure headless Chrome is properly installed with all required system packages from `pyproject.toml`
- **CDP Connection Issues**: Check WebSocket connections and port availability for Chrome DevTools Protocol
- **Font Rendering Problems**: Verify font availability and proper loading for complex layouts, especially Thai fonts
- **Memory Issues**: Monitor Chrome process memory usage during large document generation
- **Debug Commands**: Use `bench execute print_designer.utils.test_pdf_generation.test_pdf_generation` to isolate PDF issues

### Frontend Issues
- **Vue Reactivity**: Check browser console for Vue warnings about reactive data mutations
- **InteractJS Conflicts**: Verify drag/drop event handling doesn't conflict with canvas scrolling or zooming
- **Canvas Positioning**: Debug absolute positioning calculations and snap-to-grid functionality
- **State Management**: Check Pinia store updates and ensure proper element selection state

### Signature and Stamp Issues
- **Field Installation**: Run `bench execute print_designer.commands.signature_setup.check_signature_status` to verify setup
- **Permission Issues**: Ensure proper role-based access to signature management functions
- **Image Rendering**: Check signature image paths and file permissions for proper embedding

### Installation and Environment Problems
- **System Dependencies**: Install all packages listed in `pyproject.toml` apt section for Chrome functionality
- **Python Dependencies**: Verify all required packages are installed, especially `websockets` and `distro`
- **Node Dependencies**: Run `yarn install` in app directory to ensure frontend dependencies are current
- **Frappe Compatibility**: Ensure Frappe Framework V15+ for proper Vue 3 and modern JavaScript support
