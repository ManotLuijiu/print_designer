 The error revealed:
  ✅ Print Format watermark fields installed
  ❌ Error installing watermark fields: Fieldtype cannot be changed from Data to Int

  This indicates:
  1. Print Format watermark fields installed successfully
  2. Print Settings watermark fields failed due to field type conflict

  The Missing Link

  The watermark_settings field in Print Settings is what the JavaScript client script expects to exist. Without this field:

  1. Print Settings lacks the watermark configuration
  2. Client script may fail to initialize watermark controls
  3. Sidebar watermark selector doesn't appear

  Field Dependencies Chain

  Print Settings.watermark_settings (missing) 
      ↓
  JavaScript watermark selector initialization 
      ↓  
  Sidebar "Watermark per Page" display (not showing)
      ↓
  Watermark functionality in print preview

  Solution Steps

  To fix the "Watermark per Page" not showing issue:

  1. Fix Field Type Conflict

  The installation failed due to an existing field with wrong type. You need to:
  - Identify the conflicting field (likely watermark_font_size changed from Data to Int)
  - Delete the existing custom field with wrong type
  - Reinstall with correct field definitions

  2. Manual Field Installation

  # Check existing custom fields that might conflict
  bench --site erpnext-dev-server.bunchee.online execute "
  import frappe
  existing = frappe.db.get_list('Custom Field', 
      filters={'dt': 'Print Settings', 'fieldname': ['like', '%watermark%']}, 
      fields=['fieldname', 'fieldtype'])
  print(existing)
  "

  3. Force Reinstall Custom Fields

  # Delete conflicting custom fields first, then reinstall
  from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
  from print_designer.custom_fields import get_custom_fields

  # Force update existing fields
  custom_fields = get_custom_fields()
  create_custom_fields(custom_fields['Print Settings'], update=True)

  Commit 7b7d750 Analysis

  The commit you referenced (7b7d750) primarily focused on setting Chrome as the default PDF generator. It didn't introduce
  any changes that would directly cause the watermark per page to disappear. The issue is most likely related to:

  1. Incomplete installation of Print Designer app
  2. Custom field installation failure (as evidenced by the type conflict error)
  3. Missing database migrations

  Expected Behavior After Fix

  Once the watermark_settings field is properly installed in Print Settings, you should see:

  1. "Watermark per Page" section in print preview sidebar
  2. Dropdown with options: None, Original on First Page, Copy on All Pages, Original,Copy on Sequence
  3. Detailed description explaining each watermark mode
  4. Working watermark functionality in both preview and generated PDFs

  The watermark selector depends entirely on the proper installation of the Print Settings custom field - without it, the
  JavaScript code cannot initialize the sidebar control.
