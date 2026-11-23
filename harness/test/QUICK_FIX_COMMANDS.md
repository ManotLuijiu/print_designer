# Quick Fix Commands for Dynamic Images Issues

## Issue: "Image not Linked" in Dynamic Images

### Method 1: Python Script (Recommended)
```bash
cd /home/frappe/frappe-bench/apps/print_designer
python3 fix_dynamic_images.py
```

### Method 2: Frappe Console Commands
```bash
# 1. Install signature fields
bench --site [your-site] execute print_designer.api.signature_field_installer.install_signature_fields

# 2. Install signature enhancements (Target Signature Field)
bench --site [your-site] execute print_designer.api.safe_install.safe_install_signature_enhancements

# 3. Refresh dynamic images
bench --site [your-site] execute print_designer.api.refresh_dynamic_images.refresh_dynamic_images

# 4. Clear cache
bench --site [your-site] clear-cache
```

### Method 3: Browser Console (from Frappe interface)
```javascript
// Diagnose and fix automatically
frappe.call({
    method: 'print_designer.api.fix_dynamic_images_api.diagnose_and_fix_dynamic_images',
    callback: (r) => {
        console.log('Diagnosis:', r.message.diagnosis);
        console.log('Fixes Applied:', r.message.fixes_applied);
        console.log('Next Steps:', r.message.next_steps);
    }
});

// Get help finding Target Signature Field
frappe.call({
    method: 'print_designer.api.fix_dynamic_images_api.get_signature_field_locations',
    callback: (r) => console.log(r.message)
});
```

## Issue: "Target Signature Field" Not Visible

### ✅ Correct Location:
1. Go to: **Settings > Print Designer > Signature Basic Information**
2. Click: **New**
3. You'll see:
   - **Target DocType** dropdown
   - **Target Signature Field** dropdown  
   - **Auto-populate Target Field** checkbox

### ❌ Wrong Location:
- NOT in Print Designer > Dynamic Images dialog
- NOT in the main Print Designer canvas

## After Running Fixes:

### 1. Upload Sample Signatures
```bash
# Check company signature field status
bench --site [your-site] execute print_designer.api.fix_dynamic_images_api.create_sample_company_signatures
```

### 2. Verify Dynamic Images
1. Hard refresh browser (Ctrl+F5)
2. Go to Print Designer
3. Add Image Element > Dynamic Images
4. Look for Company signature fields (should show linked images)

### 3. Test Target Signature Field
1. Go to **Signature Basic Information > New**
2. Select **Target DocType**: Company
3. Select **Target Signature Field**: CEO Signature (or other)
4. Enable **Auto-populate Target Field**
5. Save

## Troubleshooting

### Still seeing "Image not Linked"?
1. **Check field installation**:
   ```bash
   bench --site [your-site] execute print_designer.api.signature_field_installer.check_signature_fields_status
   ```

2. **Upload actual images**:
   - Go to Company DocType
   - Open a company record  
   - Upload images to signature fields

3. **Clear browser cache**:
   - Hard refresh (Ctrl+F5)
   - Clear browser data if needed

### Target Signature Field still missing?
1. **Verify enhancement installation**:
   ```javascript
   frappe.db.get_list('Custom Field', {
       filters: {
           'dt': 'Signature Basic Information',
           'fieldname': ['in', ['target_doctype', 'target_signature_field']]
       }
   }).then(r => console.log('Enhanced fields:', r));
   ```

2. **Force reinstall**:
   ```bash
   bench --site [your-site] execute print_designer.api.safe_install.force_reinstall
   ```

## Expected Results

### ✅ After Successful Fix:
- **Dynamic Images**: Shows signature fields with actual images
- **Signature Basic Information**: Has Target DocType and Target Signature Field dropdowns
- **Company Records**: Have signature field uploads available
- **Print Formats**: Can use dynamic signature images

### 📊 Verification:
```javascript
// Check total signature fields available
frappe.call({
    method: 'print_designer.print_designer.page.print_designer.print_designer.get_image_docfields',
    callback: (r) => {
        const signatures = r.message.filter(f => f.fieldname.includes('signature'));
        console.log(`Found ${signatures.length} signature fields:`, signatures);
    }
});
```