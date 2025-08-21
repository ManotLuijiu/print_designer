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

# Complete system setup and checks
bench execute print_designer.commands.install_complete_system.install_complete_system
bench execute print_designer.commands.install_complete_system.check_system_status

# Signature and stamp setup
bench execute print_designer.commands.signature_setup.setup_signatures
bench execute print_designer.commands.signature_setup.check_signature_status

# Watermark system setup
bench execute print_designer.commands.install_watermark_fields.install_watermark_fields

# Thai-specific features
bench execute print_designer.commands.install_thai_form_50_twi.install_thai_form_50_twi
bench execute print_designer.commands.install_delivery_qr.install_delivery_qr
bench execute print_designer.commands.install_delivery_fields.install_delivery_note_fields

# Typography system setup
bench execute print_designer.commands.install_typography_system.install_typography_system

# Asset building and dependencies
yarn install                   # Install frontend dependencies
bench build --app print_designer  # Build only print_designer assets
```

(Rest of the existing content remains the same)

## Memories
- The test needs to be run within the Frappe context for checking field installations
- Specific bash commands for checking Thailand Withholding Tax Fields and Item Service Fields:
  ● `bench --site erpnext-dev-server.bunchee.online execute print_designer.commands.install_thailand_wht_fields.check_thailand_wht_fields`
    - Checks Company.thailand_service_business field
    - Checks Company.default_wht_account field
  ● `bench --site erpnext-dev-server.bunchee.online execute print_designer.commands.install_item_service_field.check_item_service_field`
- Add the memory to provide guidance for executing tests within the Frappe context and checking specific field installations

- No need TH Sarabun New usinng Kanit and Noto Sans Thai instead.