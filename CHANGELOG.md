# Changelog

All notable changes to Print Designer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
