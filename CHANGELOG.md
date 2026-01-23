# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [1.17.1](https://github.com/ManotLuijiu/print_designer/compare/v1.17.0...v1.17.1) (2026-01-23)


### 🐛 Bug Fixes

* resolve 'creation' attribute error in watermark migration ([d4b2344](https://github.com/ManotLuijiu/print_designer/commit/d4b23448700cffa9e2f880c3b49e8176bc9179ef))

## [1.17.0](https://github.com/ManotLuijiu/print_designer/compare/v1.16.0...v1.17.0) (2026-01-22)


### ✨ Features

* **thai-billing:** Add Payment Entry integration and Thai Billing link field ([29414ae](https://github.com/ManotLuijiu/print_designer/commit/29414aebccdb865b8d2b199b33e3698bccd7e950))

## [1.16.0](https://github.com/ManotLuijiu/print_designer/compare/v1.14.0...v1.16.0) (2026-01-22)


### 👷 CI/CD

* add auto-merge workflow (develop → main) ([ce92fe0](https://github.com/ManotLuijiu/print_designer/commit/ce92fe03406fbe6111f97a43315e7ecb0ee5f07f))
* add CodeRabbit AI code review configuration ([855fcf3](https://github.com/ManotLuijiu/print_designer/commit/855fcf38ea25ac91c4502285725b379faade89e1))


### 🐛 Bug Fixes

* Restore Chromium PDF support, fix Watermark migration, add Thai defaults ([6234177](https://github.com/ManotLuijiu/print_designer/commit/62341770faeb7b0033ed58714166fb84a502f2af))


### ✨ Features

* Add Sales Invoice QR code support with Thai e-Tax format ([e579c9c](https://github.com/ManotLuijiu/print_designer/commit/e579c9c215d64106deaada743953c6369f5c2735))


### 🔧 Maintenance

* Add standard-version for automated releases ([3e401e2](https://github.com/ManotLuijiu/print_designer/commit/3e401e2d06b80db566330316cdcdde4bc6cd9485))

## [1.7.3] - 2025-08-23

### Added
- **Thailand WHT System Unification**: Complete consolidation of Thailand Withholding Tax preview and field systems into unified management interface
  - New comprehensive `thailand_wht_fields.py` system (1,110 lines) providing unified field definitions for all WHT-enabled DocTypes
  - Added `print_designer.custom.thai_wht_custom_fields` module with complete field definition system (448 lines)
  - Added `print_designer.custom.thai_wht_events` module for centralized WHT event handling
  - Added `print_designer.custom.thai_wht_preview` module for real-time WHT calculation and preview
  - New `print_designer.commands.install_thai_wht_preview` installation command system
  - Added `print_designer.overrides.company` for Thailand-specific company integration

### Enhanced
- **Sales Document Integration**: WHT fields now properly integrated into existing taxes sections across Quotation, Sales Order, and Sales Invoice
  - WHT preview fields positioned logically following ERPNext UI patterns
  - Real-time WHT amount calculations and preview functionality in all sales documents
  - Comprehensive field coverage: Company configuration, Customer setup, and Sales document preview
  - Multi-DocType support with consistent field structure and behavior

### Changed
- **Consolidated Installation Commands**: Merged separate WHT installation systems into unified command structure in hooks.py
- **Improved Field Organization**: WHT fields repositioned from separate sections into logical tax-related sections
- **Enhanced System Architecture**: Moved from multiple scattered files to centralized system management
- **Better Integration**: Updated hooks.py with streamlined Thai WHT event system and comprehensive command registration

### Technical
- **Field Definition Consolidation**: Merged multiple WHT field definition files into comprehensive unified system
- **Enhanced Error Handling**: Improved installation and validation processes for WHT field management
- **Migration Support**: Automatic migration of existing WHT field installations with `migrate_sales_invoice_wht_fields()`
- **Thai Language Support**: Proper Thai descriptions and formatting for WHT income types and compliance requirements
- **Standard Rate Integration**: Built-in support for Thai standard WHT rates (3% services, 5% professional services, etc.)

## [1.7.2] - 2025-08-22

### Fixed
- Fixed Sales Invoice form state management issue where Submit button reverted to Save after saving document
- Eliminated problematic client scripts that caused form dirty state during refresh
- Implemented proper ERPNext-pattern server-side calculations for Thailand WHT and retention amounts

### Added  
- Added comprehensive server-side calculation system in `print_designer.custom.sales_invoice_calculations`
- Added proper validation-time calculations for retention amounts, withholding tax, and final payment amounts
- Added graceful error handling and defensive programming for missing company settings

### Changed
- Moved Thailand WHT and retention calculations from client scripts to validate() method following ERPNext grand_total pattern
- Updated Sales Invoice hooks to use proper server-side validation instead of client-side interference
- Commented out unused modules in thailand_wht_fields.py to reflect active Sales Invoice-only scope

## [1.7.1] - 2025-08-22

### Fixed
- Fixed retention system field conflicts between programmatic installation and fixtures
- Cleaned up duplicate field installation mechanisms to prevent API loops
- Disabled conflicting programmatic retention field installation in hooks.py and install.py

### Changed
- Consolidated retention system to use fixtures-only approach for better reliability
- Updated custom field fixtures with proper conditional visibility (depends_on expressions)
- Improved retention field UX with proper validation feedback and automatic calculations

## [1.7.0] - 2025-08-22

### Added
- **Retention System Fixtures Export**: Complete retention fields system exported to fixtures for deployment
  - Added 6 custom fields for Sales Invoice retention calculations:
    - `custom_retention` - Retention (%) 
    - `custom_retention_amount` - Retention Amount (Currency)
    - `custom_withholding_tax` - Withholding Tax (%)
    - `custom_withholding_tax_amount` - Withholding Tax Amount (Currency)
    - `custom_payment_amount` - Payment Amount (Currency)
    - `custom_retention_percent` - Retention % (alternate field)
- **Retention System Commands**: New management commands for retention field installation
  - Added `restructure_retention_fields.py` command for field restructuring
  - Enhanced retention field installation with fixture support
- **Custom Retention Backend**: Sales Invoice retention calculation backend integration
- **Company Retention Settings**: New DocType for company-level retention configuration

### Changed
- **Hooks Configuration**: Updated fixtures configuration to include retention system fields
- **Installation Commands**: Enhanced retention field installation with better error handling
- **Frontend Styling**: Updated company preview CSS for better retention display

### Technical Notes
- Retention fields are now exportable as fixtures enabling cross-installation deployment
- Fields can be converted from fixtures to programmatic installation for better maintainability
- Supports Thai business retention requirements with proper currency handling

## [1.6.1] - 2025-01-21

### Fixed
- **CRITICAL API Flooding Issue**: Resolved infinite loop causing hundreds of duplicate API calls
  - Disabled recursive `validate` hook in hooks.py that was causing server flooding
  - Optimized retention calculation from multiple API calls to single call
  - Fixed custom field `depends_on` expressions removing eval API calls
  - Reduced form loading from hundreds of API calls to single call (99% performance improvement)
- **Retention System Performance**: Dramatically improved response time and stability
  - Enhanced error handling and logging in retention calculations  
  - Added proper caching mechanism to prevent API call recursion
  - Fixed browser freezing and server overload issues

### Added
- **Emergency Fix Tools**: Complete monitoring and prevention system
  - Added `fix_retention_api_flooding.py` script for emergency resolution
  - Added `monitor_retention_performance.py` for health monitoring and prevention
  - Implemented performance validation and health check functions
  - Created prevention measures for future API flooding incidents

### Technical
- Emergency response reduced API calls by ~99% (from hundreds to 1 per form load)
- Form loading time improved from timeout/freeze to 0.012 seconds
- Server stability restored with proper recursive loop prevention
- Health monitoring system added to prevent future performance issues

## [1.6.0] - 2025-01-21

### Added
- **Enhanced Retention System**: Complete retention management system for construction services
  - Added `construction_service` field to Company doctype for enabling construction features
  - Added `default_retention_rate` field with 5% default for construction projects
  - Added `default_retention_account` field for retention liability management
  - Added `custom_retention` and `custom_retention_amount` fields to Sales Invoice
  - Implemented automated account discovery and setup functions
  - Created comprehensive validation and checking system
- **Thai Business Integration**: Following Thailand Service Business pattern for consistency
  - Mirrored Default Withholding Tax Account pattern for retention accounts
  - Integrated with existing WHT calculation system
  - Enhanced client-side caching for performance optimization

### Enhanced
- Improved installation command system with `install_enhanced_retention_fields.py`
- Added intelligent account search functionality for retention accounts
- Enhanced field dependency management with proper `depends_on` evaluation
- Comprehensive error handling and rollback mechanisms for field installation

### Technical
- Added automated retention account setup with fallback to suitable payable accounts
- Implemented field validation system to prevent installation conflicts
- Enhanced retention calculation integration with existing tax systems
- Improved user experience for starter users with pre-configured defaults

## [1.5.6] - 2024-08-21

### Fixed
- Fixed font validation error in production environments for watermark_font_family field
- Fixed error logging message length issues by implementing proper truncation for Error Log title field (130 character limit)
- Enhanced migration logic to handle existing installations safely during font option updates
- Resolved validation failures when existing font values are not in updated options list

### Changed
- Updated Thai font options: removed "TH Sarabun New", added "Kanit" and "Noto Sans Thai" for better compatibility
- Improved error handling in Print Settings setup with proper message formatting
- Enhanced watermark font field migration to automatically update invalid font selections

### Technical
- Added intelligent font value migration that maps old font names to compatible alternatives
- Implemented proper error message truncation to prevent Error Log creation failures
- Enhanced install.py, overrides/erpnext_install.py, and patches for consistent font options across all installation paths

## [1.5.5] - 2024-08-21

### Fixed
- Fixed Thailand WHT JavaScript performance issues
- Improved performance for withholding tax calculations
