# Sales Invoice Field Order Fix - Production Deployment Guide

## Issue Summary

**Problem**: Sales Invoice `thai_wht_preview_section` only showing `wht_amounts_column_break` and `vat_treatment` fields instead of all 14 expected fields.

**Root Cause**: Circular dependency in `insert_after` field chain causing broken field ordering.

**Expected Fields**: 
- `wht_amounts_column_break`, `vat_treatment`, `subject_to_wht`, `wht_income_type`, `wht_description`
- `wht_certificate_required`, `net_total_after_wht`, `net_total_after_wht_in_words`, `wht_note`
- `wht_preview_column_break`, `custom_subject_to_retention`, `custom_net_total_after_wht_retention`
- `custom_net_total_after_wht_retention_in_words`, `custom_retention_note`

## Production-Safe Solution

### ✅ Implemented Solution: Frappe Patch System

**File**: `print_designer/patches/v1_0/fix_sales_invoice_field_order.py`  
**Patch Entry**: Added to `patches.txt` for automatic execution during migration

### 🛡️ Safety Features

1. **Pre-patch Validation**: Validates environment before applying changes
2. **Automatic Backup**: Creates rollback data before making changes  
3. **Post-patch Validation**: Confirms fix was applied correctly
4. **Automatic Rollback**: Reverts changes if validation fails
5. **Atomic Operations**: Uses database transactions for safety
6. **Production Logging**: Detailed logging for monitoring

## 🚀 Production Deployment Steps

### Step 1: Pre-Deployment Testing (MANDATORY)

```bash
# On staging/development environment first:
bench migrate --app print_designer

# Validate the fix worked:
bench execute print_designer.commands.install_sales_invoice_fields.validate_sales_invoice_fields_installation
```

### Step 2: Production Backup (CRITICAL)

```bash
# Database backup before deployment
bench --site production-site backup --with-files

# Verify backup was created
ls sites/production-site/private/backups/
```

### Step 3: Production Deployment

```bash
# Deploy code changes
git pull origin main  # or your deployment branch

# Run migration (this will automatically execute the patch)
bench migrate --site production-site

# Verify patch was applied
bench --site production-site console
>>> import frappe
>>> frappe.db.get_value("Patch Log", {"patch": "print_designer.patches.v1_0.fix_sales_invoice_field_order"})
```

### Step 4: Post-Deployment Validation

```bash
# Test Sales Invoice form rendering
# 1. Open Sales Invoice in browser
# 2. Check thai_wht_preview_section shows all 14 fields
# 3. Verify field order is correct
# 4. Test field dependencies work

# Optional: Run validation command
bench execute print_designer.commands.install_sales_invoice_fields.validate_sales_invoice_fields_installation
```

## 🚨 Emergency Rollback Plan

If the patch causes issues:

### Option 1: Automatic Patch Rollback (Built-in)
The patch includes automatic rollback if validation fails during execution.

### Option 2: Manual Database Restore
```bash
# Stop all services
bench --site production-site set-maintenance-mode on

# Restore from backup
bench --site production-site restore /path/to/backup/file.sql.gz

# Restart services  
bench --site production-site set-maintenance-mode off
```

### Option 3: Manual Field Revert (Last Resort)
```bash
# Revert specific fields manually
bench --site production-site console
>>> import frappe
>>> # Revert subject_to_wht back to old insert_after
>>> frappe.db.set_value("Custom Field", 
    {"dt": "Sales Invoice", "fieldname": "subject_to_wht"}, 
    "insert_after", "old_value")
>>> frappe.db.commit()
```

## 📋 Pre-Deployment Checklist

- [ ] ✅ **Staging tested**: Patch tested on staging environment
- [ ] ✅ **Database backup**: Full backup created and verified  
- [ ] ✅ **Maintenance window**: Scheduled during low-usage hours
- [ ] ✅ **Team notification**: Development team informed of deployment
- [ ] ✅ **Rollback plan**: Emergency procedures documented and tested
- [ ] ✅ **Monitoring ready**: Error monitoring and logging in place

## 📊 Expected Results

**Before Fix**:
```
Thai Ecosystem Preview Section:
├── wht_amounts_column_break    ✅ Visible
├── vat_treatment              ✅ Visible  
├── subject_to_wht             ❌ Hidden (circular dependency)
├── wht_income_type            ❌ Hidden
├── wht_description            ❌ Hidden
└── ... (10 more fields hidden)
```

**After Fix**:
```
Thai Ecosystem Preview Section:
├── Left Column (WHT Fields)
│   ├── wht_amounts_column_break     ✅ Visible
│   ├── vat_treatment                ✅ Visible
│   ├── subject_to_wht               ✅ Visible
│   ├── wht_income_type              ✅ Visible
│   ├── wht_description              ✅ Visible
│   ├── wht_certificate_required     ✅ Visible
│   ├── net_total_after_wht          ✅ Visible
│   ├── net_total_after_wht_in_words ✅ Visible
│   └── wht_note                     ✅ Visible
├── Right Column (Retention Fields)  
│   ├── wht_preview_column_break     ✅ Visible
│   ├── custom_subject_to_retention  ✅ Visible
│   ├── custom_net_total_after_wht_retention ✅ Visible
│   ├── custom_net_total_after_wht_retention_in_words ✅ Visible
│   └── custom_retention_note        ✅ Visible
```

## ⚠️ Important Notes for Production

1. **Zero Downtime**: This patch modifies metadata, not data - no user downtime required
2. **User Impact**: Users may need to refresh Sales Invoice forms to see changes
3. **Performance**: Patch runs in <30 seconds, minimal performance impact
4. **Compatibility**: Works with all existing Sales Invoice data
5. **Reversible**: Can be rolled back without data loss

## 🔍 Monitoring & Validation

### Post-Deployment Checks
1. **Error Logs**: Monitor for field-related errors in Sales Invoice
2. **User Feedback**: Check for reports of missing fields
3. **Form Rendering**: Verify all 14 fields display correctly
4. **Dependencies**: Test `depends_on` conditions work properly
5. **Performance**: Ensure no degradation in form load times

### Success Criteria
- ✅ All 14 thai_wht_preview_section fields visible
- ✅ Fields display in correct order
- ✅ Field dependencies work as expected  
- ✅ No errors in server logs
- ✅ User confirmation that fields are working

---

## 📞 Support Contacts

**Development Team**: Internal team  
**Database Admin**: Backup/restore specialist  
**System Administrator**: Production deployment lead