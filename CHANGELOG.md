# Changelog

All notable changes to Print Designer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
