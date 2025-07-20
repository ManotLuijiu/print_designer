# Signature Enhancement Setup Guide

This guide helps ensure the signature enhancements work properly for existing Print Designer customers during migrations.

## Migration-Safe Installation

The signature enhancement system is designed to be **migration-safe** and can be run multiple times without issues.

### Automatic Installation

The system automatically installs during:

1. **New installations** - via `after_install` hook
2. **Migrations** - via `after_migrate` hook  
3. **Patches** - via patches.txt entry

### Manual Installation Commands

For existing customers or troubleshooting:

```bash
# Check current status
bench --site your-site.com execute print_designer.api.safe_install.check_installation_status

# Safe installation (can run multiple times)
bench --site your-site.com execute print_designer.api.safe_install.safe_install_signature_enhancements

# Development only: Force reinstall
bench --site your-site.com execute print_designer.api.safe_install.force_reinstall
```

### What Gets Installed

#### 1. Core Signature Fields
Adds custom fields to core DocTypes:
- **Company**: `ceo_signature`, `authorized_signature_1`, `authorized_signature_2`
- **User**: `signature_image`
- **Employee**: `signature_image` (if Employee DocType exists)

#### 2. Enhanced Signature Basic Information
Adds new fields to Signature Basic Information DocType:
- **Target DocType** - Select which DocType contains the signature field
- **Target Signature Field** - Select specific field to populate
- **Auto-populate Target Field** - Checkbox to enable automatic sync

#### 3. Migration of Existing Data
- Automatically maps existing signature records to new target field system
- Preserves all existing signature data
- No data loss during upgrade

## Verification Steps

After installation, verify the setup:

### 1. Check Custom Fields
```bash
# Verify Company signature fields exist
bench --site your-site.com execute frappe.db.get_all --kwargs '{"doctype": "Custom Field", "filters": {"dt": "Company", "fieldname": ["like", "%signature%"]}, "fields": ["fieldname", "label"]}'

# Verify Signature Basic Information enhancement fields
bench --site your-site.com execute frappe.db.get_all --kwargs '{"doctype": "Custom Field", "filters": {"dt": "Signature Basic Information"}, "fields": ["fieldname", "label"]}'
```

### 2. Test Signature Creation
1. Go to **Signature Basic Information > New**
2. Verify you see:
   - **Target DocType** dropdown
   - **Target Signature Field** dropdown (after selecting DocType)
   - **Auto-populate Target Field** checkbox

### 3. Test API Endpoints
```bash
# Test Company CEO signature (should now return data)
curl "http://your-site.com/api/method/frappe.client.get_value?doctype=Company&fieldname=ceo_signature&filters=Your Company Name"

# Test enhanced signature API
bench --site your-site.com execute print_designer.api.company_api.get_company_assets --kwargs '{"company_name": "Your Company Name"}'
```

## Troubleshooting

### Fields Not Visible in Form
1. **Clear cache**: `bench --site your-site.com clear-cache`
2. **Hard refresh browser** (Ctrl+F5)
3. **Check browser console** for JavaScript errors
4. **Verify fields exist** using commands above

### Migration Fails
The system is designed to be fault-tolerant:
- Individual step failures don't break the entire migration
- All operations are idempotent (safe to run multiple times)
- Errors are logged but don't stop the migration process

### Force Reinstall (Development Only)
If you need to completely reinstall (development mode only):
```bash
bench --site your-site.com execute print_designer.api.safe_install.force_reinstall
```

## Customer Impact

### For Existing Customers
- **Zero downtime** - all changes are additive
- **No data loss** - existing signatures are preserved and enhanced
- **Backward compatible** - old signature functionality continues to work
- **Automatic migration** - existing signature records get new field mappings

### For New Customers
- **Enhanced functionality** out of the box
- **Better user experience** with dropdown selections
- **Automatic field population** 

## Implementation Details

### Patches Applied
- `print_designer.patches.v1_0.enhance_signature_basic_information` - Main enhancement patch

### Hooks Modified
- `after_migrate` - Ensures installation runs after migrations
- `doc_events` - Auto-sync signatures when saved

### Safe Installation Features
- **Idempotent operations** - can run multiple times safely
- **Existence checks** - only creates what doesn't exist
- **Error isolation** - individual failures don't break entire process
- **Rollback capability** - for development environments

## Support

If customers experience issues:

1. **Check installation status** using verification commands
2. **Review error logs** in Error Log DocType
3. **Run safe installation** manually if needed
4. **Contact support** with specific error messages

The system is designed to be robust and self-healing, with comprehensive logging for troubleshooting.