# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [](https://github.com/ManotLuijiu/print_designer/compare/v1.24.2...v) (2026-07-24)


### 🔧 Maintenance

* add graphify-out/ and wiki/ to .gitignore ([9f12721](https://github.com/ManotLuijiu/print_designer/commit/9f12721f437f345e7ae5949f5f7385d1c5b47523))
* remove graphify-out and wiki from git tracking (already in .gitignore) ([dd6098c](https://github.com/ManotLuijiu/print_designer/commit/dd6098c994e93d6449d937e2fedd184038d246dd))


### ✨ Features

* **printview:** implement position-aware page number injection ([78f54f4](https://github.com/ManotLuijiu/print_designer/commit/78f54f4219c659939caa72daf166bd9fea3b3083))
* Watermark tool in Design View - show watermark in main view header zone ([44248f6](https://github.com/ManotLuijiu/print_designer/commit/44248f645388df8590d92a361d45ad236a0f7a8a))

### [1.24.2](https://github.com/ManotLuijiu/print_designer/compare/v1.28.0...v1.24.2) (2026-07-21)


### ✨ Features

* **print-sidebar:** Add Copy, Watermark, and Page Number settings with 2-column grid layout ([f7529f8](https://github.com/ManotLuijiu/print_designer/commit/f7529f8ac1ad1bdeae6ad22b147237cc8124b774))

### [1.24.1](https://github.com/ManotLuijiu/print_designer/compare/v1.27.0...v1.24.1) (2026-07-19)


### 🐛 Bug Fixes

* **print:** prototype override to preserve Print Format language on Refresh ([7e19cc6](https://github.com/ManotLuijiu/print_designer/commit/7e19cc6a325ea838b39ff75d64ad158c1f215897))

### [1.24.0](https://github.com/ManotLuijiu/print_designer/compare/v1.23.0...v1.24.0) (2026-07-17)

### ✨ Features

* Add Layer panel toggle for managing element visibility and layering
* Add Grid toggle for 10mm/50mm grid overlay display
* Add Help toggle with border toggle explanation popover
* Redesign border toggle icons from SVG to informative rectangles (All, L, R, T, B)
* Add border style options: Solid, Dotted, and Dashed styles

### 🔧 Maintenance

* add empty app.js stubs ([9d2b2c0](https://github.com/ManotLuijiu/print_designer/commit/9d2b2c0bbc9c26a7d56471b0d510fbcb994239ad))

### ♻️ Refactoring

* **thailand_wht:** Remove redundant pd_custom_wht_income_type field ([88b752c](https://github.com/ManotLuijiu/print_designer/commit/88b752c73c161b0700d764f29da44623493f3231))

### ✨ Features

* Add 'Thai Tax Compliance' charge_type option ([322d1b9](https://github.com/ManotLuijiu/print_designer/commit/322d1b9720c7127303033d25c959c803282e1ed7))
* Fixed WHT ([9512ba4](https://github.com/ManotLuijiu/print_designer/commit/9512ba4acae7dc8c7448327935044a53de3a74df))
* **Sales Invoice:** Thai Tax Compliance charge_type override ([2499c25](https://github.com/ManotLuijiu/print_designer/commit/2499c25d12c52543ab6164577da913f0f014741e))
* **thailand_wht:** Auto-fill tax_withholding_category from Item ([ad780d9](https://github.com/ManotLuijiu/print_designer/commit/ad780d92dd521d951822e21344a82bdbcd42073c))
* Add Layer panel toggle for managing element visibility and layering
* Add Grid toggle for 10mm/50mm grid overlay display
* Add Help toggle with border toggle explanation popover
* Redesign border toggle icons from SVG to informative rectangles (All, L, R, T, B)
* Add border style options: Solid, Dotted, and Dashed styles

### 🐛 Bug Fixes

* bidirectional minRows sync for table drag-resize and manual input ([fe6301f](https://github.com/ManotLuijiu/print_designer/commit/fe6301fccb1b9033d2c77ea19190838137ea291f))
* Extend erpnext_tds_disabler to Sales Invoice ([611f05b](https://github.com/ManotLuijiu/print_designer/commit/611f05b56e80e4479c6aaccd93228dff838cde56))
* Remove install_item_wht_fields references from hooks.py ([ee67adf](https://github.com/ManotLuijiu/print_designer/commit/ee67adf5b677bca77c5d57bc6f2a043f1967829e))
* Thai WHT calculation using total instead of grand_total ([0a78b08](https://github.com/ManotLuijiu/print_designer/commit/0a78b08ec933b7f593c781a93fa7f229b71e89cc))

## [1.23.0](https://github.com/ManotLuijiu/print_designer/compare/v1.22.0...v1.23.0) (2026-07-15)

### 📚 Documentation

* plan language-aware words field pairs ([f471b52](https://github.com/ManotLuijiu/print_designer/commit/f471b528d4e9fb1a0a0e6a836b3672e69930d323))
* specify language-aware words field pairs ([e50f11d](https://github.com/ManotLuijiu/print_designer/commit/e50f11da12cef71decfe4306d47512722cda88c3))

### 🐛 Bug Fixes

* configure Receipt amount words rendering ([04b78f0](https://github.com/ManotLuijiu/print_designer/commit/04b78f089ea26d59f0920e351871f545f6f2315f))
* distinguish automatic print language ([92a989d](https://github.com/ManotLuijiu/print_designer/commit/92a989d51561f7f47343cc709f0b7679fc08f87a))
* render configured words fields in print language ([60faae8](https://github.com/ManotLuijiu/print_designer/commit/60faae886ab59673df3f72c3db9c54a288a7eeaf))

### 🔧 Maintenance

* close number-to-words field pair issue ([4204e4f](https://github.com/ManotLuijiu/print_designer/commit/4204e4f69aa5886943cf28b668ac0d86ed141bd6))
* close print language precedence bug ([402f487](https://github.com/ManotLuijiu/print_designer/commit/402f487378e5bf519774c651bd9ea2d808af5696))

### ✨ Features

* 020626_adding_address_utils ([3fd3096](https://github.com/ManotLuijiu/print_designer/commit/3fd309653f6acf7e3cf0cd420f0a4bc55e5d8a09))
* 050626 ([9de3d32](https://github.com/ManotLuijiu/print_designer/commit/9de3d321cfda2d1c720096b82b418212f04daea8))
* 060626 add whitelist to thai_amount_to_word ([b9f7903](https://github.com/ManotLuijiu/print_designer/commit/b9f7903169e1404616a47b5904b560f1baba8c4c))
* add number-to-words field pair resolver ([2ee3d32](https://github.com/ManotLuijiu/print_designer/commit/2ee3d32f70bb77661f4e0035866d357d02ebd4b2))
* add thai_billing, thai_billing_item ([6e6d46d](https://github.com/ManotLuijiu/print_designer/commit/6e6d46d6228a532243477fd54c6246c8d6ad3769))
* add thai_billing, thai_billing_item ([c282a19](https://github.com/ManotLuijiu/print_designer/commit/c282a19a78bbff3aac7fcb3cecefd36fc9c7a63c))
* add thai_billing, thai_billing_item ([226d7b3](https://github.com/ManotLuijiu/print_designer/commit/226d7b3804e25a5e3115bbd66b4f60e24a38217a))
* added dockerfile ([0a7bbfa](https://github.com/ManotLuijiu/print_designer/commit/0a7bbfafe1723bd96f3b1235874af5ae541324f1))
* Added Import/Export ([4760b36](https://github.com/ManotLuijiu/print_designer/commit/4760b36d47d64b514831cec0dafd0395f6fb8cec))
* backup print_designer ([46ea285](https://github.com/ManotLuijiu/print_designer/commit/46ea28515e3a8b19ae6a2dfd069f6956ca6c7d20))
* backup print_designer2 ([e179b79](https://github.com/ManotLuijiu/print_designer/commit/e179b794a4d3c1720b3efd2ff58a86c383413b38))
* backup TBS ([f0379e3](https://github.com/ManotLuijiu/print_designer/commit/f0379e3c00a2df7fc2f6b4e89b71d88dcc9b0d54))
* configure words fields in print designer ([1b57267](https://github.com/ManotLuijiu/print_designer/commit/1b572678939daa20f760b11f2871473bb087622b))
* disable Apply Thai Withholding Tax Compliance in PI ([9845bd5](https://github.com/ManotLuijiu/print_designer/commit/9845bd51149a66a0c660225de0b14a63bfe0bb9e))
* expose words fields to design preview ([14e3037](https://github.com/ManotLuijiu/print_designer/commit/14e30376d91121b6743b7007e3a7bad106976d6e))
* Fixed Format ([a66747c](https://github.com/ManotLuijiu/print_designer/commit/a66747c49e6a26f040f6fb98c10c4d7dca189477))
* inpac_selling/custom/customer.json ([4fab26d](https://github.com/ManotLuijiu/print_designer/commit/4fab26db351379f5b46759ce7fce4230deb9755b))
* mariadb-optimization ([31618a7](https://github.com/ManotLuijiu/print_designer/commit/31618a700145c3b6ddf82d44ffb68d4d71963b30))
* modified:   print_designer/commands/install_company_thai_tax_fields.py ([1eca262](https://github.com/ManotLuijiu/print_designer/commit/1eca262aec276797c835a112161dd11bcb5efa81))
* modified:   print_designer/commands/install_company_thai_tax_fields.py ([865e5e4](https://github.com/ManotLuijiu/print_designer/commit/865e5e4fdecb82a4cf8b16eb740dd0f6a0463daa))
* PND Reports ([9dbcf2f](https://github.com/ManotLuijiu/print_designer/commit/9dbcf2f445fd91f81ed90044389b8d03d163ff1e))
* **thai_wht:** bilingual naming for WHT Income Type + list view column customization ([3419961](https://github.com/ManotLuijiu/print_designer/commit/3419961569e276fd7513f3c3e563cf16a89c278c))
* translation_tools/hooks.py ([4f62536](https://github.com/ManotLuijiu/print_designer/commit/4f6253602fc93d54cf8c5d7a2df8d3a379e6796d))

## [1.22.0](https://github.com/ManotLuijiu/print_designer/compare/v1.21.0...v1.22.0) (2026-04-01)

### ✨ Features

* add Print WHT Cert button and auto-create WHT Certificate on PI submit ([f001677](https://github.com/ManotLuijiu/print_designer/commit/f001677eb755fe94fc14b6c9584d6ac069e4aa00))

### 🔧 Maintenance

* **release:** 1.21.0 ([876fbd7](https://github.com/ManotLuijiu/print_designer/commit/876fbd70b2bf80f076fb8338e2c71ddb25c6c8b9))

## [1.20.0](https://github.com/ManotLuijiu/print_designer/compare/v1.19.2...v1.20.0) (2026-03-25)

### ✨ Features

* install_watermark_fields fixed ([2ab19ca](https://github.com/ManotLuijiu/print_designer/commit/2ab19ca918eba0901230284eebcdb77c817255b1))
* watermark sidebar margin 4-directional fields, position tooltips, sidebar injection ([65f24b7](https://github.com/ManotLuijiu/print_designer/commit/65f24b729a50d7630a8c65d46eb4947f21abf25d))

### [1.19.2](https://github.com/ManotLuijiu/print_designer/compare/v1.19.1...v1.19.2) (2026-03-20)

### 🔧 Maintenance

* move Thai Billing hooks to thai_business_suite ([5df4586](https://github.com/ManotLuijiu/print_designer/commit/5df458643b548efa9c4588810d51d593ad5ca254))

### [1.19.1](https://github.com/ManotLuijiu/print_designer/compare/v1.19.0...v1.19.1) (2026-03-11)

### 🐛 Bug Fixes

* remove mixed Thai from WHT Note default value ([b7ce489](https://github.com/ManotLuijiu/print_designer/commit/b7ce489273d4a394831d586c179c45abd6604450))

## [1.19.0](https://github.com/ManotLuijiu/print_designer/compare/v1.18.0...v1.19.0) (2026-03-08)

### ✨ Features

* extract VAT treatment helper, auto-set VAT from item service flag ([27f4bf1](https://github.com/ManotLuijiu/print_designer/commit/27f4bf181f2ccff3c16f3f7a6c37f02123edc222))

## [1.18.0](https://github.com/ManotLuijiu/print_designer/compare/v1.17.6...v1.18.0) (2026-03-08)

### ✨ Features

* rename all custom fields to pd_custom_* prefix convention ([cd779ad](https://github.com/ManotLuijiu/print_designer/commit/cd779ad288fe49f7b7d8dafea37a107dc3e634b6))

### [1.17.6](https://github.com/ManotLuijiu/print_designer/compare/v1.17.5...v1.17.6) (2026-02-27)

### 🐛 Bug Fixes

* make wht_income_type editable on direct Sales Invoice ([4853cce](https://github.com/ManotLuijiu/print_designer/commit/4853cceb6570e7e58bb5007882643e724a7eb68d))

### [1.17.5](https://github.com/ManotLuijiu/print_designer/compare/v1.17.4...v1.17.5) (2026-02-26)

### ✨ Features

* Thai WHT Income Type dropdown with all-Thai description row ([937af3b](https://github.com/ManotLuijiu/print_designer/commit/937af3b8deb2a43d36bc9509a61177b14a8ece03))

### [1.17.4](https://github.com/ManotLuijiu/print_designer/compare/v1.17.3...v1.17.4) (2026-02-25)

### ✨ Features

* show Thai income category in WHT Income Type link fields ([babc61f](https://github.com/ManotLuijiu/print_designer/commit/babc61f5f3c3f73f57956dfed019532322824649))

### [1.17.3](https://github.com/ManotLuijiu/print_designer/compare/v1.17.2...v1.17.3) (2026-02-14)

### ✨ Features

* route raw printing through TBS Print Agent instead of QZ Tray ([5faed08](https://github.com/ManotLuijiu/print_designer/commit/5faed08e383a6825707bcb0dbff8a9775e10076a))

### 1.17.2 (2026-02-14)

### 🐛 Bug Fixes

* handle missing custom fields in field index ordering patch ([bb0af69](https://github.com/ManotLuijiu/print_designer/commit/bb0af690b4995f9041c5e8f0dcb5f7f71df6dc19))

### ✨ Features

* fix customer doctype ([151d71b](https://github.com/ManotLuijiu/print_designer/commit/151d71b6fb9e28b2c46d75a23d51b179e5f7de8e))
* set Chrome CDP as default PDF generator and remove implicit margins ([1fafed3](https://github.com/ManotLuijiu/print_designer/commit/1fafed31b60eb633f5e7314c8d957e314c1cc387))

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
* **Thailand WHT System Unification**: Complete consolidation of Thailand Withholding Tax preview and field systems into unified management interface
  * New comprehensive `thailand_wht_fields.py` system (1,110 lines) providing unified field definitions for all WHT-enabled DocTypes
  * Added `print_designer.custom.thai_wht_custom_fields` module with complete field definition system (448 lines)
  * Added `print_designer.custom.thai_wht_events` module for centralized WHT event handling
  * Added `print_designer.custom.thai_wht_preview` module for real-time WHT calculation and preview
  * New `print_designer.commands.install_thai_wht_preview` installation command system
  * Added `print_designer.overrides.company` for Thailand-specific company integration

### Enhanced
* **Sales Document Integration**: WHT fields now properly integrated into existing taxes sections across Quotation, Sales Order, and Sales Invoice
  * WHT preview fields positioned logically following ERPNext UI patterns
  * Real-time WHT amount calculations and preview functionality in all sales documents
  * Comprehensive field coverage: Company configuration, Customer setup, and Sales document preview
  * Multi-DocType support with consistent field structure and behavior

### Changed
* **Consolidated Installation Commands**: Merged separate WHT installation systems into unified command structure in hooks.py
* **Improved Field Organization**: WHT fields repositioned from separate sections into logical tax-related sections
* **Enhanced System Architecture**: Moved from multiple scattered files to centralized system management
* **Better Integration**: Updated hooks.py with streamlined Thai WHT event system and comprehensive command registration

### Technical
* **Field Definition Consolidation**: Merged multiple WHT field definition files into comprehensive unified system
* **Enhanced Error Handling**: Improved installation and validation processes for WHT field management
* **Migration Support**: Automatic migration of existing WHT field installations with `migrate_sales_invoice_wht_fields()`
* **Thai Language Support**: Proper Thai descriptions and formatting for WHT income types and compliance requirements
* **Standard Rate Integration**: Built-in support for Thai standard WHT rates (3% services, 5% professional services, etc.)

## [1.7.2] - 2025-08-22

### Fixed
* Fixed Sales Invoice form state management issue where Submit button reverted to Save after saving document
* Eliminated problematic client scripts that caused form dirty state during refresh
* Implemented proper ERPNext-pattern server-side calculations for Thailand WHT and retention amounts

### Added  
* Added comprehensive server-side calculation system in `print_designer.custom.sales_invoice_calculations`
* Added proper validation-time calculations for retention amounts, withholding tax, and final payment amounts
* Added graceful error handling and defensive programming for missing company settings

### Changed
* Moved Thailand WHT and retention calculations from client scripts to validate() method following ERPNext grand_total pattern
* Updated Sales Invoice hooks to use proper server-side validation instead of client-side interference
* Commented out unused modules in thailand_wht_fields.py to reflect active Sales Invoice-only scope

## [1.7.1] - 2025-08-22

### Fixed
* Fixed retention system field conflicts between programmatic installation and fixtures
* Cleaned up duplicate field installation mechanisms to prevent API loops
* Disabled conflicting programmatic retention field installation in hooks.py and install.py

### Changed
* Consolidated retention system to use fixtures-only approach for better reliability
* Updated custom field fixtures with proper conditional visibility (depends_on expressions)
* Improved retention field UX with proper validation feedback and automatic calculations

## [1.7.0] - 2025-08-22

### Added
* **Retention System Fixtures Export**: Complete retention fields system exported to fixtures for deployment
  * Added 6 custom fields for Sales Invoice retention calculations:
    * `custom_retention` - Retention (%)
    * `custom_retention_amount` - Retention Amount (Currency)
    * `custom_withholding_tax` - Withholding Tax (%)
    * `custom_withholding_tax_amount` - Withholding Tax Amount (Currency)
    * `custom_payment_amount` - Payment Amount (Currency)
    * `custom_retention_percent` - Retention % (alternate field)
* **Retention System Commands**: New management commands for retention field installation
  * Added `restructure_retention_fields.py` command for field restructuring
  * Enhanced retention field installation with fixture support
* **Custom Retention Backend**: Sales Invoice retention calculation backend integration
* **Company Retention Settings**: New DocType for company-level retention configuration

### Changed
* **Hooks Configuration**: Updated fixtures configuration to include retention system fields
* **Installation Commands**: Enhanced retention field installation with better error handling
* **Frontend Styling**: Updated company preview CSS for better retention display

### Technical Notes
* Retention fields are now exportable as fixtures enabling cross-installation deployment
* Fields can be converted from fixtures to programmatic installation for better maintainability
* Supports Thai business retention requirements with proper currency handling

## [1.6.1] - 2025-01-21

### Fixed
* **CRITICAL API Flooding Issue**: Resolved infinite loop causing hundreds of duplicate API calls
  * Disabled recursive `validate` hook in hooks.py that was causing server flooding
  * Optimized retention calculation from multiple API calls to single call
  * Fixed custom field `depends_on` expressions removing eval API calls
  * Reduced form loading from hundreds of API calls to single call (99% performance improvement)
* **Retention System Performance**: Dramatically improved response time and stability
  * Enhanced error handling and logging in retention calculations  
  * Added proper caching mechanism to prevent API call recursion
  * Fixed browser freezing and server overload issues

### Added
* **Emergency Fix Tools**: Complete monitoring and prevention system
  * Added `fix_retention_api_flooding.py` script for emergency resolution
  * Added `monitor_retention_performance.py` for health monitoring and prevention
  * Implemented performance validation and health check functions
  * Created prevention measures for future API flooding incidents

### Technical
* Emergency response reduced API calls by ~99% (from hundreds to 1 per form load)
* Form loading time improved from timeout/freeze to 0.012 seconds
* Server stability restored with proper recursive loop prevention
* Health monitoring system added to prevent future performance issues

## [1.6.0] - 2025-01-21

### Added
* **Enhanced Retention System**: Complete retention management system for construction services
  * Added `construction_service` field to Company doctype for enabling construction features
  * Added `default_retention_rate` field with 5% default for construction projects
  * Added `default_retention_account` field for retention liability management
  * Added `custom_retention` and `custom_retention_amount` fields to Sales Invoice
  * Implemented automated account discovery and setup functions
  * Created comprehensive validation and checking system
* **Thai Business Integration**: Following Thailand Service Business pattern for consistency
  * Mirrored Default Withholding Tax Account pattern for retention accounts
  * Integrated with existing WHT calculation system
  * Enhanced client-side caching for performance optimization

### Enhanced
* Improved installation command system with `install_enhanced_retention_fields.py`
* Added intelligent account search functionality for retention accounts
* Enhanced field dependency management with proper `depends_on` evaluation
* Comprehensive error handling and rollback mechanisms for field installation

### Technical
* Added automated retention account setup with fallback to suitable payable accounts
* Implemented field validation system to prevent installation conflicts
* Enhanced retention calculation integration with existing tax systems
* Improved user experience for starter users with pre-configured defaults

## [1.5.6] - 2024-08-21

### Fixed
* Fixed font validation error in production environments for watermark_font_family field
* Fixed error logging message length issues by implementing proper truncation for Error Log title field (130 character limit)
* Enhanced migration logic to handle existing installations safely during font option updates
* Resolved validation failures when existing font values are not in updated options list

### Changed
* Updated Thai font options: removed "TH Sarabun New", added "Kanit" and "Noto Sans Thai" for better compatibility
* Improved error handling in Print Settings setup with proper message formatting
* Enhanced watermark font field migration to automatically update invalid font selections

### Technical
* Added intelligent font value migration that maps old font names to compatible alternatives
* Implemented proper error message truncation to prevent Error Log creation failures
* Enhanced install.py, overrides/erpnext_install.py, and patches for consistent font options across all installation paths

## [1.5.5] - 2024-08-21

### Fixed
* Fixed Thailand WHT JavaScript performance issues
* Improved performance for withholding tax calculations
