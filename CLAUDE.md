# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Print Designer Overview

Print Designer is a Frappe application for creating professional print formats using an interactive visual designer. It provides a drag-and-drop interface for designing complex layouts without coding, targeting invoices, reports, and other business documents.

## Development Setup

### Prerequisites
- Frappe Framework V15 or develop branch
- Node.js for frontend build
- Python 3.10+ with required dependencies
- Chrome/Chromium browser for PDF generation

### Local Development Commands
```bash
# Initial setup in frappe-bench
bench get-app print_designer
bench new-site print-designer.localhost --install-app print_designer
bench browse print-designer.localhost --user Administrator

# Development server
bench start                    # Start development server
bench watch                    # Watch and build frontend assets
bench build                    # Build all assets
bench migrate                  # Run database migrations
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
The app uses a sophisticated Chrome DevTools Protocol (CDP) system for PDF generation:

1. **FrappePDFGenerator**: Manages Chrome browser instances
2. **Browser**: Handles page creation and PDF generation workflow
3. **CDPSocketClient**: WebSocket communication with Chrome
4. **Page**: Individual page management (header, footer, body)
5. **PDFTransformer**: Merges header, footer, and body PDFs

Key workflow:
- Initialize Chrome browser process
- Create separate pages for header, footer, and body content
- Generate PDFs asynchronously for static elements
- Handle dynamic content (page numbers) with separate rendering
- Merge all PDFs into final output

## Key Files and Directories

### Frontend Structure
- `print_designer/public/js/print_designer/App.vue`: Main Vue application
- `print_designer/public/js/print_designer/store/`: Pinia stores for state management
- `print_designer/public/js/print_designer/components/`: Vue components
- `print_designer/public/js/print_designer/composables/`: Reusable Vue composables

### Backend Structure
- `print_designer/hooks.py`: Frappe app integration and hooks
- `print_designer/pdf_generator/`: Chrome CDP PDF generation system
- `print_designer/print_designer/page/print_designer/`: Main page controller
- `print_designer/print_designer/overrides/`: DocType overrides

### Configuration
- `package.json`: Frontend dependencies (interactjs, html2canvas)
- `build.json`: CSS build configuration
- `pyproject.toml`: Python project configuration with PDF generation dependencies

## Development Workflow

### Frontend Development
- Vue 3 components follow Composition API patterns
- Uses Pinia for reactive state management
- Interactive elements use interactjs for drag/drop/resize
- Canvas-based design with absolute positioning

### Backend Development
- Follows Frappe app conventions
- Custom PDF generation bypasses standard wkhtmltopdf
- Jinja template rendering for dynamic content
- WhiteList decorators for API endpoints

### Testing
- No dedicated test framework detected
- Manual testing through the visual designer interface
- PDF generation testing requires Chrome/Chromium setup

## Dependencies

### Frontend
- `@interactjs/actions`, `@interactjs/modifiers`: Drag and drop interactions
- `html2canvas`: Canvas-based screenshot generation
- Vue 3 ecosystem (built into Frappe)

### Backend
- `PyQRCode`, `python-barcode`: Barcode generation
- `websockets`: WebSocket communication for CDP
- `distro`: System information for Chrome setup

## Common Development Tasks

### Adding New Element Types
1. Create Vue component in `components/base/`
2. Add to `defaultObjects.js` for toolbar
3. Update store handlers in `ElementStore.js`
4. Add Jinja template in `jinja/macros/`

### Extending PDF Generation
- Modify `pdf_generator/` classes for new PDF features
- Update `browser.py` for new page types
- Extend `page.py` for new CDP commands

### Print Format Integration
- Override behavior in `print_designer/overrides/print_format.py`
- Add hooks in `hooks.py` for DocType events
- Update Jinja templates for new rendering logic

## Troubleshooting

### PDF Generation Issues
- Ensure Chrome/Chromium is properly installed
- Check CDP WebSocket connections
- Verify font availability for complex layouts

### Frontend Issues
- Check browser console for Vue errors
- Verify interactjs event handling
- Debug canvas positioning and sizing

### Installation Problems
- macOS: Install Xcode Command Line Tools and Homebrew dependencies
- Linux ARM: Install build-essential and Cairo dependencies
- Verify wkhtmltopdf version compatibility (0.12.5+ with patched qt)

## Issue

 The issue is in /home/frappe/frappe-bench/apps/print_designer/print_designer/public/js/print_designer/components/la
  yout/AppImageModal.vue around lines 201-227:
