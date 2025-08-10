Based on my analysis of the code, here's what I found regarding the Print Settings sidebar
  implementation:

  Frontend Files Responsible for Print Settings Sidebar

  1. JavaScript Files:

  Primary Implementation:
  - /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js - Main Print Page
    - Contains frappe.ui.form.PrintView class that creates the print page
    - setup_sidebar() method creates the print settings sidebar
    - setup_additional_settings() loads dynamic settings from backend
    - add_settings_to_sidebar() renders the custom fields in the sidebar

  Supporting Files:
  - /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/print_utils.js
    - Contains frappe.ui.get_print_settings() function for print dialog
    - Handles basic print settings like letterhead, orientation
  - /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/toolbar.js
    - Adds print menu item and print icon to form toolbar
    - Calls me.frm.print_doc() when print is clicked
  - /home/frappe/frappe-bench/apps/frappe/frappe/public/js/frappe/form/form.js
    - Contains print_doc() method that routes to print page

  2. Backend Integration:

  - /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.py
    - get_print_settings_to_show() function returns dynamic fields
    - Calls doc.get_print_settings() method if it exists on the document

  3. CSS Files:

  - /home/frappe/frappe-bench/apps/frappe/frappe/public/dist/css/print.bundle.*.css - Compiled CSS bundle
  - No direct CSS file found in source, likely uses framework styles

  4. Custom Fields from install.py:

  The create_print_setting_custom_fields() function in ERPNext's install.py creates these custom fields:
  - compact_item_print (Check field)
  - print_uom_after_quantity (Check field)
  - print_taxes_with_zero_amount (Check field - duplicated in the code)

  Key Implementation Details:

  1. Sidebar Creation Flow:
    - Print page loads → setup_sidebar() → setup_additional_settings()
    - Backend call to get_print_settings_to_show()
    - Returns fields from Print Settings DocType that the document wants to show
    - add_settings_to_sidebar() renders these fields dynamically
  2. Custom Field Integration:
    - Custom fields created by ERPNext install.py are automatically available
    - Documents can implement get_print_settings() method to specify which fields to show
    - Fields are rendered using the standard Frappe form field system

  The main responsibility for showing the Print Settings sidebar lies in
  /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js, specifically in the PrintView
  class methods for sidebar setup and dynamic field rendering.

  Please analyze this Request URL
  http://erpnext-dev-server.bunchee.online:8000/api/method/frappe.printing.page.print.print.get_print_setti
  ngs_to_show
  Request Method
  POST
  Status Code
  200 OK
  Remote Address
  5.223.62.137:8000
  Referrer Policy
  strict-origin-when-cross-origin this is response {
      "message": [
          {
              "name": "Print Settings-compact_item_print",
              "creation": "2025-07-10 16:33:52.346960",
              "modified": "2025-07-10 16:33:52.346960",
              "modified_by": "Administrator",
              "owner": "Administrator",
              "docstatus": 0,
              "parent": "Print Settings",
              "parentfield": "fields",
              "parenttype": "DocType",
              "idx": 10,
              "fieldname": "compact_item_print",
              "label": "Compact Item Print",
              "fieldtype": "Check",
              "search_index": 0,
              "show_dashboard": 0,
              "hidden": 0,
              "set_only_once": 0,
              "allow_in_quick_entry": 0,
              "print_hide": 0,
              "report_hide": 0,
              "reqd": 0,
              "bold": 0,
              "in_global_search": 0,
              "collapsible": 0,
              "unique": 0,
              "no_copy": 0,
              "allow_on_submit": 0,
              "permlevel": 0,
              "ignore_user_permissions": 0,
              "columns": 0,
              "default": 0,
              "in_list_view": 0,
              "fetch_if_empty": 0,
              "in_filter": 0,
              "remember_last_selected_value": 0,
              "ignore_xss_filter": 0,
              "print_hide_if_no_value": 0,
              "allow_bulk_edit": 0,
              "in_standard_filter": 0,
              "in_preview": 0,
              "read_only": 0,
              "precision": "",
              "length": 0,
              "translatable": 0,
              "hide_border": 0,
              "hide_days": 0,
              "hide_seconds": 0,
              "non_negative": 0,
              "is_virtual": 0,
              "sort_options": 0,
              "show_on_timeline": 0,
              "make_attachment_public": 0,
              "doctype": "DocField"
          },
          {
              "name": "Print Settings-print_uom_after_quantity",
              "creation": "2025-07-10 16:33:52.370618",
              "modified": "2025-07-10 16:33:52.370618",
              "modified_by": "Administrator",
              "owner": "Administrator",
              "docstatus": 0,
              "parent": "Print Settings",
              "parentfield": "fields",
              "parenttype": "DocType",
              "idx": 11,
              "fieldname": "print_uom_after_quantity",
              "label": "Print UOM after Quantity",
              "fieldtype": "Check",
              "search_index": 0,
              "show_dashboard": 0,
              "hidden": 0,
              "set_only_once": 0,
              "allow_in_quick_entry": 0,
              "print_hide": 0,
              "report_hide": 0,
              "reqd": 0,
              "bold": 0,
              "in_global_search": 0,
              "collapsible": 0,
              "unique": 0,
              "no_copy": 0,
              "allow_on_submit": 0,
              "permlevel": 0,
              "ignore_user_permissions": 0,
              "columns": 0,
              "default": 0,
              "in_list_view": 0,
              "fetch_if_empty": 0,
              "in_filter": 0,
              "remember_last_selected_value": 0,
              "ignore_xss_filter": 0,
              "print_hide_if_no_value": 0,
              "allow_bulk_edit": 0,
              "in_standard_filter": 0,
              "in_preview": 0,
              "read_only": 0,
              "precision": "",
              "length": 0,
              "translatable": 0,
              "hide_border": 0,
              "hide_days": 0,
              "hide_seconds": 0,
              "non_negative": 0,
              "is_virtual": 0,
              "sort_options": 0,
              "show_on_timeline": 0,
              "make_attachment_public": 0,
              "doctype": "DocField"
          },
          {
              "name": "Print Settings-print_taxes_with_zero_amount",
              "creation": "2025-07-10 16:33:52.393727",
              "modified": "2025-07-10 16:33:52.393727",
              "modified_by": "Administrator",
              "owner": "Administrator",
              "docstatus": 0,
              "parent": "Print Settings",
              "parentfield": "fields",
              "parenttype": "DocType",
              "idx": 17,
              "fieldname": "print_taxes_with_zero_amount",
              "label": "Print taxes with zero amount",
              "fieldtype": "Check",
              "search_index": 0,
              "show_dashboard": 0,
              "hidden": 0,
              "set_only_once": 0,
              "allow_in_quick_entry": 0,
              "print_hide": 0,
              "report_hide": 0,
              "reqd": 0,
              "bold": 0,
              "in_global_search": 0,
              "collapsible": 0,
              "unique": 0,
              "no_copy": 0,
              "allow_on_submit": 0,
              "permlevel": 0,
              "ignore_user_permissions": 0,
              "columns": 0,
              "default": 0,
              "in_list_view": 0,
              "fetch_if_empty": 0,
              "in_filter": 0,
              "remember_last_selected_value": 0,
              "ignore_xss_filter": 0,
              "print_hide_if_no_value": 0,
              "allow_bulk_edit": 0,
              "in_standard_filter": 0,
              "in_preview": 0,
              "read_only": 0,
              "precision": "",
              "length": 0,
              "translatable": 0,
              "hide_border": 0,
              "hide_days": 0,
              "hide_seconds": 0,
              "non_negative": 0,
              "is_virtual": 0,
              "sort_options": 0,
              "show_on_timeline": 0,
              "make_attachment_public": 0,
              "doctype": "DocField"
          }
      ]
  }

● Looking at this API request and response, I can analyze the complete flow of how Print Settings sidebar
  fields are displayed:

  API Analysis

  Request URL: frappe.printing.page.print.print.get_print_settings_to_show

  This API call is triggered from the print page's setup_additional_settings() method in
  /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js.

  Response Analysis

  The response shows 3 DocField objects that represent the custom fields created by ERPNext's
  create_print_setting_custom_fields() function:

  1. compact_item_print (idx: 10)

  - Label: "Compact Item Print"
  - Type: Check field
  - Purpose: Controls compact display of items in print

  2. print_uom_after_quantity (idx: 11)

  - Label: "Print UOM after Quantity"
  - Type: Check field
  - Purpose: Controls whether UOM appears after quantity

  3. print_taxes_with_zero_amount (idx: 17)

  - Label: "Print taxes with zero amount"
  - Type: Check field
  - Purpose: Controls whether zero-amount taxes are shown

  Field Order and Positioning

  The idx values (10, 11, 17) indicate the display order in the Print Settings form. The gap between 11 and
   17 suggests there are other fields positioned between print_uom_after_quantity and
  print_taxes_with_zero_amount.

  Frontend Rendering Process

  1. API Call: Print page calls get_print_settings_to_show with doctype/docname
  2. Backend Processing: Returns relevant DocField definitions from Print Settings
  3. Sidebar Rendering: add_settings_to_sidebar() in print.js creates form fields from these DocField
  objects
  4. User Interaction: Changes to these fields affect print output dynamically

  Key Observations

  - All fields are Check type: Simple boolean toggles for print behavior
  - Default values: All set to 0 (unchecked by default)
  - Standard DocField structure: Full metadata available for proper rendering
  - Dynamic loading: Only fields relevant to the current document type are returned

  This confirms that the Print Settings sidebar is completely dynamic, loading only the fields that the
  current document type needs to display, and rendering them using the standard Frappe form field system
  based on the DocField metadata returned by this API.

  The frontend responsibility lies primarily in
  /home/frappe/frappe-bench/apps/frappe/frappe/printing/page/print/print.js which processes this response
  and creates the interactive sidebar controls.
