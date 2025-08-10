# Print Designer Signature Fields Implementation Guide

## Overview

This implementation adds signature image fields to various DocTypes across all Frappe modules, making them available for use in print formats through the Print Designer interface.

## What's Included

### 1. **Signature Fields Configuration** (`signature_fields.py`)
- Comprehensive signature field definitions for 22+ DocTypes
- Covers all major modules: HR, CRM, Accounting, Sales, Purchase, Stock, etc.
- Fields include: `signature_image`, `authorized_signature_1`, `ceo_signature`, `prepared_by_signature`, etc.

### 2. **Automatic Integration** (`custom_fields.py`)
- Seamlessly integrates with existing Print Designer custom fields
- Automatically includes signature fields in the custom fields system
- No conflicts with existing Print Designer functionality

### 3. **Installation Scripts** (`install_signature_fields.py`)
- Complete installation/uninstallation system
- Verification tools to ensure proper installation
- Status checking and error handling

### 4. **Command Line Interface** (`commands/signature_fields.py`)
- Easy-to-use CLI commands for managing signature fields
- Support for install, verify, uninstall, and status operations

## DocTypes with Signature Fields

### Core Master Data
- **User**: `signature_image`
- **Employee**: `signature_image`
- **Customer**: `signature_image`
- **Supplier**: `signature_image`
- **Company**: `authorized_signature_1`, `authorized_signature_2`, `ceo_signature`

### Transaction Documents
- **Sales Invoice**: `prepared_by_signature`, `approved_by_signature`
- **Purchase Invoice**: `prepared_by_signature`, `approved_by_signature`
- **Sales Order**: `prepared_by_signature`, `approved_by_signature`
- **Purchase Order**: `prepared_by_signature`, `approved_by_signature`
- **Delivery Note**: `prepared_by_signature`, `delivered_by_signature`, `received_by_signature`
- **Purchase Receipt**: `prepared_by_signature`, `received_by_signature`

### HR Documents
- **Offer Letter**: `hr_signature`, `candidate_signature`
- **Appraisal**: `appraiser_signature`, `employee_signature`

### Quality & Maintenance
- **Quality Inspection**: `inspector_signature`, `supervisor_signature`
- **Maintenance Schedule**: `technician_signature`

### And many more...

## Installation

### Method 1: Using Frappe Console (Recommended)
```bash
# Start Frappe console
bench --site [your-site] console

# In the console, run:
from apps.print_designer.print_designer.install_signature_fields import install_signature_fields
install_signature_fields()
```

### Method 2: Using Python Script
```bash
# Create and run installation script
python3 -c "
import frappe
from apps.print_designer.print_designer.install_signature_fields import install_signature_fields

frappe.init('.')
frappe.connect()
install_signature_fields()
"
```

### Method 3: Manual Installation
1. Navigate to your bench directory
2. Copy the signature fields files to the print_designer app
3. Run: `bench migrate`
4. Install custom fields using Frappe's standard process

## Verification

### Check Installation Status
```bash
# Using Frappe console
bench --site [your-site] console

# Run status check
from apps.print_designer.print_designer.install_signature_fields import status
status()
```

### Verify Field Discovery
```bash
# Check that signature fields are discovered by Print Designer
from apps.print_designer.print_designer.install_signature_fields import verify_signature_fields
verify_signature_fields()
```

## Usage in Print Designer

### 1. **Access Print Designer**
- Go to Print Settings → Print Format
- Create new or edit existing print format
- Enable "Print Designer" checkbox

### 2. **Add Signature Images**
- In Print Designer interface, click "Add Image"
- Select "Dynamic Image" option
- Choose your desired signature field from the dropdown
- Position and resize as needed

### 3. **Available Signature Fields**
All signature fields will automatically appear in the image field dropdown, organized by DocType:
- User.signature_image
- Employee.signature_image
- Company.authorized_signature_1
- Sales Invoice.prepared_by_signature
- etc.

## Field Configuration Details

### Field Properties
- **Field Type**: "Attach Image" (supports jpg, png, gif, svg)
- **Field Label**: Descriptive labels like "Signature", "Authorized Signature", etc.
- **Insert Position**: Strategically placed after relevant fields
- **Description**: Helpful descriptions for each field's purpose

### Security & Permissions
- Signature fields inherit DocType permissions
- File attachments follow Frappe's standard security model
- Only users with appropriate permissions can upload/view signatures

## Maintenance

### Update Signature Fields
To add new signature fields or modify existing ones:
1. Edit `signature_fields.py`
2. Run the installation script again
3. New fields will be added automatically

### Remove Signature Fields
```bash
# Using Frappe console
from apps.print_designer.print_designer.install_signature_fields import uninstall_signature_fields
uninstall_signature_fields()
```

## Troubleshooting

### Common Issues

1. **Fields Not Appearing in Print Designer**
   - Ensure signature fields are properly installed
   - Check that the DocType exists in your system
   - Verify permissions on the DocType

2. **Installation Errors**
   - Some DocTypes may not exist in all Frappe installations
   - The script will skip missing DocTypes automatically
   - Check the installation summary for details

3. **Image Not Displaying in PDF**
   - Ensure the signature image file exists
   - Check file permissions
   - Verify the image format is supported

### Debug Commands
```bash
# Check what DocTypes have signature fields
from apps.print_designer.print_designer.signature_fields import get_doctypes_with_signatures
print(get_doctypes_with_signatures())

# Check specific DocType fields
from apps.print_designer.print_designer.signature_fields import get_signature_fields_for_doctype
print(get_signature_fields_for_doctype('User'))

# Verify image field discovery
from apps.print_designer.print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
image_fields = get_image_docfields()
signature_fields = [f for f in image_fields if 'signature' in f.get('fieldname', '')]
print(f"Found {len(signature_fields)} signature fields in discovery")
```

## Architecture Benefits

### 1. **Automatic Discovery**
- Uses Print Designer's existing `get_image_docfields()` function
- No UI modifications needed
- Seamless integration

### 2. **Modular Design**
- Separate configuration file for easy maintenance
- Clean separation of concerns
- Easy to extend or modify

### 3. **Robust Installation**
- Error handling for missing DocTypes
- Detailed logging and feedback
- Rollback capability

### 4. **Standards Compliance**
- Follows Frappe's custom field conventions
- Uses standard attachment handling
- Maintains security model

## Future Enhancements

### Possible Improvements
1. **Digital Signature Integration**: Add support for digital signatures
2. **Signature Templates**: Pre-defined signature templates
3. **Multi-language Support**: Localized field labels
4. **Approval Workflows**: Integration with approval processes
5. **Batch Operations**: Bulk signature upload/management

### Customization Options
- Add signature fields to custom DocTypes
- Create signature-specific print format templates
- Implement signature validation rules
- Add signature history tracking

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Frappe documentation on custom fields
3. Examine the Print Designer documentation
4. Test with a minimal print format first

This implementation provides a solid foundation for signature management in Print Designer while maintaining compatibility with existing functionality and following Frappe best practices.