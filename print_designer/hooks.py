from . import __version__ as app_version

app_name = "print_designer"
app_title = "Print Designer"
app_publisher = "Frappe Technologies Pvt Ltd."
app_description = "Frappe App to Design Print Formats using interactive UI."
app_email = "hello@frappe.io"
app_license = "AGPLv3"

required_apps = ["erpnext"]

# Custom bench commands
commands = [
    # Signature field management (clean installation system)
    "print_designer.commands.install_signature_fields.install_signature_fields_cmd",
    "print_designer.commands.install_signature_fields.check_signature_fields_cmd",
    "print_designer.commands.install_signature_fields.uninstall_signature_fields_cmd",
    # Customer field management (Branch Code for Thai tax invoices)
    "print_designer.commands.install_customer_fields.install_customer_fields_cmd",
    "print_designer.commands.install_customer_fields.check_customer_fields_cmd",
    "print_designer.commands.install_customer_fields.uninstall_customer_fields_cmd",
    "print_designer.commands.install_watermark_fields.install_watermark_fields",
    "print_designer.commands.install_thai_form_50_twi.install_thai_form_50_twi",
    "print_designer.commands.install_delivery_qr.install_delivery_qr",
    "print_designer.commands.install_complete_system.install_complete_system",
    "print_designer.commands.install_complete_system.check_system_status",
    "print_designer.commands.install_delivery_fields.install_delivery_note_fields",
    "print_designer.commands.install_typography_system.install_typography_system",
    # DISABLED: Old retention installer - replaced by enhanced retention installer (file renamed to .backup)
    # "print_designer.commands.install_retention_fields.install_retention_fields",
    # "print_designer.commands.install_retention_fields.check_retention_fields",
    "print_designer.commands.install_enhanced_retention_fields.install_enhanced_retention_fields",
    "print_designer.commands.install_enhanced_retention_fields.check_enhanced_retention_fields",
    # REMOVED: install_thailand_wht_fields commands - Now handled by separate quotation module
    "print_designer.commands.install_item_service_field.install_item_service_field",
    "print_designer.commands.install_item_service_field.check_item_service_field",
    "print_designer.commands.install_wht_rate_field.install_wht_rate_field",
    "print_designer.commands.install_wht_rate_field.check_wht_rate_field",
    "print_designer.commands.install_company_tab.install_company_tab",
    "print_designer.commands.install_company_tab.remove_company_tab",
    "print_designer.commands.fix_target_signature_field.fix_target_signature_field",
    "print_designer.commands.emergency_fix_watermark.emergency_fix_watermark",
    "print_designer.commands.install_retention_client_script.install_retention_client_script",
    "print_designer.commands.install_retention_client_script.check_retention_client_script",
    # Field validation commands
    "print_designer.commands.validate_construction_service_field.validate_construction_service_field",
    "print_designer.commands.validate_construction_service_field.check_construction_service_dependencies",
    "print_designer.commands.validate_construction_service_field.test_construction_service_functionality",
    "print_designer.commands.test_print_designer_installation.test_complete_print_designer_installation",
    # Production fix commands
    "print_designer.commands.force_install_construction_service.force_install_construction_service",
    # Company Thai Tax Fields (check function only - installation handled in after_install)
    "print_designer.commands.install_company_thai_tax_fields.check_company_thai_tax_fields",
    # Thai Account Translation Fields
    "print_designer.commands.install_account_thai_fields.install_account_thai_fields",
    "print_designer.commands.install_account_thai_fields.check_account_thai_fields_status",
    "print_designer.commands.install_account_thai_fields.remove_account_thai_translation_fields",
    # Account translation system commands (simple direct approach)
    "print_designer.commands.apply_account_thai_translations.execute",
    "print_designer.commands.apply_account_thai_translations.apply_account_thai_translations",
    "print_designer.commands.apply_account_thai_translations.get_translation_stats",
    "print_designer.commands.apply_account_thai_translations.check_glossary_coverage",
    # Account file generation for external server access
    "print_designer.utils.account_file_api.generate_files",
    "print_designer.utils.account_file_api.check_files",
    # Thai Language Setup Commands (check functions only - installation handled in after_install)
    "print_designer.install.thai_defaults.check_thai_language_setup",
    # Thai WHT System Commands (DocType-specific check functions)
    # Note: install_thai_wht_preview.py deleted - functionality moved to DocType-specific field installers
    # Payment Entry check functions (installation handled in after_install/before_uninstall)
    "print_designer.commands.install_payment_entry_fields.check_payment_entry_fields_status",
    "print_designer.commands.install_payment_entry_thai_fields.check_fields_exist",
    # Console Utilities for Development and Debugging
    "print_designer.commands.console_utils.execute_sql_query",
    "print_designer.commands.console_utils.check_custom_field",
    "print_designer.commands.console_utils.fix_fetch_from_field",
    "print_designer.commands.console_utils.check_thai_tax_fields_status",
    # Purchase Invoice and Purchase Order check functions (installation/removal handled in after_install/before_uninstall)
    "print_designer.commands.install_purchase_invoice_fields.check_purchase_invoice_fields",
    "print_designer.commands.install_purchase_order_fields.check_purchase_order_fields",
    # Item WHT Income Type field (check function only - installation handled in after_install)
    "print_designer.commands.install_item_wht_fields.check_item_wht_fields",
    # Thai WHT Override Testing
    "print_designer.commands.test_thai_wht_override.execute",
    "print_designer.commands.test_thai_wht_override.test_purchase_order_wht_override",
    # Thai WHT Calculation Precision Testing
    "print_designer.regional.purchase_order_wht_override.test_thai_wht_calculation_precision",
    "print_designer.regional.purchase_order_wht_override.test_thai_wht_automation",
    # Purchase Invoice Thai WHT Testing
    "print_designer.regional.purchase_invoice_wht_override.test_thai_wht_automation",
    # WHT Certificate Link Field Management - REDUNDANT: Fields now handled by install_payment_entry_thai_fields.py
    # "print_designer.commands.install_wht_certificate_link_field.install_wht_certificate_link_field",
    # "print_designer.commands.install_wht_certificate_link_field.check_wht_certificate_link_field",
    # Field cleanup commands
    "print_designer.commands.cleanup_has_thai_taxes_field.cleanup_has_thai_taxes_field",
    "print_designer.commands.cleanup_has_thai_taxes_field.check_has_thai_taxes_field_status",
    # PND Form testing utilities
    "print_designer.commands.test_pnd_population.test_pnd_population",
    # Employee Thai Tax ID field
    "print_designer.commands.install_employee_thai_tax_fields.install_employee_thai_tax_fields",
    "print_designer.commands.install_employee_thai_tax_fields.remove_employee_thai_tax_fields",
    "print_designer.commands.install_employee_thai_tax_fields.check_employee_thai_tax_fields",
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_js = [
    "print_watermark.bundle.js",
    # Other JS files are loaded via doctype_js for specific DocTypes
]

app_include_css = [
    "thai_fonts.bundle.css",
    # Additional CSS files are included via doctype_js or conditionally loaded
]


# include js, css files in header of web template
# web_include_css = "/assets/print_designer/css/print_designer.css"
# web_include_js = "/assets/print_designer/js/print_designer.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "print_designer/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
page_js = {
    "print": [
        "print_designer/client_scripts/safe_pdf_client.js",
        "print_designer/client_scripts/print.js",
    ],
    "point-of-sale": "print_designer/client_scripts/point_of_sale.js",
}

# include js in doctype views
doctype_js = {
    "Print Format": [
        "public/js/print_format/print_format.js",
        "public/js/print_format/print_format_conversion_dialog.js",
    ],
    # "Print Settings": "print_designer/client_scripts/print_settings.js",
    "Client Script": "print_designer/client_scripts/client_script.js",
    # "Global Defaults": "print_designer/client_scripts/global_defaults.js",
    # Corrected path for doctype_js
    "Quotation": "public/js/thailand_wht/thailand_wht_quotation.js",
    "Item": "public/js/thailand_wht/thailand_wht_item.js",
    "Payment Entry": [
        "public/js/delivery_approval.js",
        "public/js/thailand_wht/thailand_wht_payment_entry.js",
        "public/js/payment_entry_thai_tax.js",
        "public/js/payment_entry_wht_certificate.js",
    ],
    "Sales Invoice": [
        "public/js/thailand_wht/thailand_wht_sales_invoice.js",
    ],
    "Sales Order": "public/js/thailand_wht/thailand_wht_sales_order.js",
    "Purchase Order": "public/js/thailand_wht/thailand_wht_purchase_order.js",
    "Purchase Invoice": "public/js/thailand_wht/thailand_wht_purchase_invoice.js",
    "Print Settings": "public/js/print_format/print_settings.js",
    "Signature Basic Information": "public/js/stamps_signatures/signature_basic_information.js",
    "Delivery Note": "public/js/delivery_note/delivery_approval.js",
    "Company": ["public/js/print_format/company.js", "public/js/company/company_thai_accounts.js"],
    "Designation": "public/js/stamps_signatures/designation_signature.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Fixtures for deployment
# Note: Custom fields are installed programmatically via install.py to handle existing fields gracefully
# Fixtures are used for Client Scripts and Property Setters only
fixtures = [
    {"doctype": "Print Format", "filters": [["module", "=", "Print Designer"]]},
    {"doctype": "Report", "filters": [["module", "=", "Print Designer"]]},
    # {
    #     "doctype": "Custom Field",
    #     "filters": [
    #         [
    #             "name",
    #             "in",
    #             [
    #                 # Company DocType - All Custom Fields for Print Designer
    #                 # Company - Stamps & Signatures Fields (relocated to proper sections)
    #                 "Company-company_signatures_section",
    #                 "Company-authorized_signature_1",
    #                 "Company-authorized_signature_2",
    #                 "Company-ceo_signature",
    #                 "Company-company_stamps_section",
    #                 "Company-company_stamp_1",
    #                 "Company-company_stamp_2",
    #                 "Company-official_seal",
    #                 # Company - Thai Business Configuration
    #                 "Company-thailand_service_business",
    #                 "Company-default_wht_account",
    #                 "Company-default_wht_rate",
    #                 "Company-default_output_vat_undue_account",
    #                 "Company-default_output_vat_account",
    #                 "Company-default_input_vat_undue_account",
    #                 "Company-default_input_vat_account",
    #                 "Company-construction_service",
    #                 "Company-default_retention_rate",
    #                 "Company-default_retention_account",
    #                 # Company - Retention Settings
    #                 "Company-retention_section",
    #                 "Company-retention_enabled",
    #                 "Company-retention_percentage",
    #                 "Company-retention_account",
    #                 "Company-retention_description",
    #                 "Company-retention_notes",
    #                 # Company - Thai WHT Settings
    #                 "Company-thai_wht_section",
    #                 "Company-wht_enabled",
    #                 "Company-default_wht_rate",
    #                 "Company-wht_liability_account",
    #                 "Company-wht_description",
    #                 "Company-wht_certificate_required",
    #                 # Company - Typography Settings
    #                 "Company-typography_section",
    #                 "Company-default_print_font",
    #                 "Company-enable_thai_fonts",
    #                 "Company-custom_css_styles",
    #                 # Company - Watermark Settings
    #                 "Company-watermark_section",
    #                 "Company-default_watermark_text",
    #                 "Company-watermark_enabled",
    #                 "Company-watermark_position",
    #                 "Company-watermark_opacity",
    #                 # Company - Print Format Settings
    #                 "Company-print_format_section",
    #                 "Company-default_print_format",
    #                 "Company-enable_company_signature",
    #                 "Company-auto_apply_watermark",
    #                 # Company - Document Numbering
    #                 "Company-document_numbering_section",
    #                 "Company-custom_invoice_prefix",
    #                 "Company-enable_thai_numbering",
    #                 "Company-thai_business_registration",
    #                 "Company-vat_registration_number",
    #                 # Employee - Thai Tax ID
    #                 "Employee-pd_custom_thai_tax_id",
    #                 # Account - Thai Translation Fields
    #                 "Account-account_name_th",
    #                 "Account-auto_translate_thai",
    #                 "Account-thai_notes",
    #                 # Sales Invoice - Signature Fields
    #                 "Sales Invoice-prepared_by_signature",
    #                 "Sales Invoice-approved_by_signature",
    #                 # Sales Invoice - Watermark Field
    #                 "Sales Invoice-watermark_text",
    #                 # Sales Invoice - Digisoft ERP Tab
    #                 "Sales Invoice-digisoft_erp_tab",
    #                 # Removed redundant Thai Tax Information Fields - using thai_wht_preview_section instead
    #                 # Sales Invoice - Thai Compliance Fields
    #                 "Sales Invoice-thai_compliance_section",
    #                 "Sales Invoice-thai_vat_eligible",
    #                 "Sales Invoice-thai_export_eligible",
    #                 "Sales Invoice-thai_cash_receipt",
    #                 # Sales Invoice - VAT Treatment Field
    #                 "Sales Invoice-custom_vat_treatment",
    #                 # Sales Invoice - WHT (Withholding Tax) Fields
    #                 "Sales Invoice-subject_to_wht",
    #                 "Sales Invoice-wht_income_type",
    #                 "Sales Invoice-wht_description",
    #                 "Sales Invoice-wht_certificate_required",
    #                 "Sales Invoice-net_total_after_wht",
    #                 "Sales Invoice-net_total_after_wht_in_words",
    #                 "Sales Invoice-wht_note",
    #                 # Sales Invoice - Thai WHT Preview Fields
    #                 "Sales Invoice-thai_wht_preview_section",
    #                 "Sales Invoice-wht_amounts_column_break",
    #                 "Sales Invoice-wht_preview_column_break",
    #                 # Sales Invoice - Retention System Fields
    #                 "Sales Invoice-custom_subject_to_retention",
    #                 "Sales Invoice-custom_net_total_after_wht_retention",
    #                 "Sales Invoice-custom_net_total_after_wht_retention_in_words",
    #                 "Sales Invoice-custom_retention_note",
    #                 "Sales Invoice-custom_retention",
    #                 "Sales Invoice-custom_retention_amount",
    #                 "Sales Invoice-custom_withholding_tax",
    #                 "Sales Invoice-custom_withholding_tax_amount",
    #                 "Sales Invoice-custom_payment_amount",
    #                 # Quotation - Signature Fields
    #                 "Quotation-prepared_by_signature",
    #                 # Quotation - Watermark Field
    #                 "Quotation-watermark_text",
    #                 # Quotation - VAT Treatment Field
    #                 "Quotation-vat_treatment",
    #                 # Quotation - WHT (Withholding Tax) Fields
    #                 "Quotation-wht_note",
    #                 "Quotation-subject_to_wht",
    #                 "Quotation-wht_description",
    #                 "Quotation-wht_income_type",
    #                 "Quotation-net_total_after_wht_in_words",
    #                 "Quotation-net_total_after_wht",
    #                 # Quotation - Thai WHT Preview Fields
    #                 "Quotation-thai_wht_preview_section",
    #                 "Quotation-wht_amounts_column_break",
    #                 "Quotation-wht_preview_column_break",
    #                 # Quotation - Retention System Fields
    #                 "Quotation-custom_subject_to_retention",
    #                 "Quotation-custom_net_total_after_wht_retention",
    #                 "Quotation-custom_net_total_after_wht_retention_in_words",
    #                 "Quotation-custom_retention",
    #                 "Quotation-custom_retention_amount",
    #                 "Quotation-custom_retention_note",
    #                 "Quotation-custom_withholding_tax",
    #                 "Quotation-custom_withholding_tax_amount",
    #                 "Quotation-custom_payment_amount",
    #                 # Sales Order - Signature Fields
    #                 "Sales Order-prepared_by_signature",
    #                 "Sales Order-approved_by_signature",
    #                 # Sales Order - Watermark Field
    #                 "Sales Order-watermark_text",
    #                 # Sales Order - Deposit Fields
    #                 "Sales Order-has_deposit",
    #                 "Sales Order-deposit_invoice",
    #                 "Sales Order-percent_deposit",
    #                 "Sales Order-column_break_euapx",
    #                 "Sales Order-section_break_o8q38",
    #                 "Sales Order-deposit_deduction_method",
    #                 # Sales Order - VAT Treatment Field
    #                 "Sales Order-custom_vat_treatment",
    #                 # Sales Order - WHT (Withholding Tax) Fields
    #                 "Sales Order-subject_to_wht",
    #                 "Sales Order-wht_note",
    #                 "Sales Order-wht_description",
    #                 "Sales Order-wht_income_type",
    #                 "Sales Order-net_total_after_wht_in_words",
    #                 "Sales Order-net_total_after_wht",
    #                 # Sales Order - Thai WHT Preview Fields
    #                 "Sales Order-thai_wht_preview_section",
    #                 "Sales Order-wht_amounts_column_break",
    #                 "Sales Order-wht_preview_column_break",
    #                 # Sales Order - Retention System Fields
    #                 "Sales Order-custom_subject_to_retention",
    #                 "Sales Order-custom_net_total_after_wht_retention",
    #                 "Sales Order-custom_net_total_after_wht_retention_in_words",
    #                 "Sales Order-custom_retention_note",
    #                 "Sales Order-custom_retention",
    #                 "Sales Order-custom_retention_amount",
    #                 "Sales Order-custom_withholding_tax",
    #                 "Sales Order-custom_withholding_tax_amount",
    #                 "Sales Order-custom_payment_amount",
    #                 # Customer - Thai WHT Configuration Fields (Print Designer Section)
    #                 "Customer-print_designer_wht_section",
    #                 "Customer-print_designer_wht_column_1",
    #                 "Customer-subject_to_wht",
    #                 "Customer-wht_income_type",
    #                 "Customer-custom_wht_rate",
    #                 "Customer-print_designer_wht_column_2",
    #                 "Customer-is_juristic_person",
    #                 # Payment Entry - Thai Tax Compliance Fields
    #                 "Payment Entry-pd_custom_thai_compliance_tab",
    #                 "Payment Entry-pd_custom_thai_tax_column_1",
    #                 "Payment Entry-pd_custom_tax_base_amount",
    #                 "Payment Entry-pd_custom_tax_invoice_number",
    #                 "Payment Entry-pd_custom_tax_invoice_date",
    #                 "Payment Entry-pd_custom_income_type",
    #                 "Payment Entry-pd_custom_thai_tax_column_2",
    #                 "Payment Entry-pd_custom_wht_certificate_no",
    #                 "Payment Entry-pd_custom_wht_certificate_date",
    #                 "Payment Entry-pd_custom_withholding_tax_amount",
    #                 "Payment Entry-pd_custom_withholding_tax_rate",
    #                 "Payment Entry-pd_custom_net_payment_amount",
    #                 "Payment Entry-pd_custom_apply_withholding_tax",
    #             ],
    #         ]
    #     ],
    # },
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "doc_type",
                "in",
                [
                    "Company",
                    "Print Format",
                    "Print Settings",
                    "Global Defaults",
                    "Delivery Note",
                    "Digital Signature",
                    "Signature Basic Information",
                ],
            ]
        ],
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "Company-Form",
                    "Print Format-Form",
                    "Print Settings-Form",
                    "Delivery Note-Form",
                    "Digital Signature-Form",
                    "Signature Basic Information-Form",
                ],
            ]
        ],
    },
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
    "methods": [
        "print_designer.print_designer.page.print_designer.print_designer.render_user_text",
        "print_designer.print_designer.page.print_designer.print_designer.convert_css",
        "print_designer.print_designer.page.print_designer.print_designer.convert_uom",
        "print_designer.print_designer.page.print_designer.print_designer.get_barcode",
        "print_designer.utils.signature_integration.get_signature_data_for_print",
        "print_designer.utils.signature_integration.get_signature_for_document",
        "print_designer.utils.signature_integration.get_available_signatures",
        "print_designer.utils.signature_integration.log_signature_usage",
        # NEW: Signature and stamp methods
        "print_designer.utils.signature_stamp.get_signature_and_stamp_context",
        "print_designer.utils.signature_stamp.get_signature_image_url",
        "print_designer.utils.signature_stamp.get_company_stamp_url",
        "print_designer.utils.signature_stamp.get_signature_image",
        "print_designer.utils.signature_stamp.get_company_stamp_image",
        # Thai language methods
        "print_designer.utils.thai_amount_to_word.thai_money_in_words",
        "print_designer.utils.thai_amount_to_word.get_thai_in_words_for_print",
        "print_designer.utils.thai_amount_to_word.is_thai_format",
        "print_designer.utils.thai_amount_to_word.smart_money_in_words",
        "print_designer.utils.thai_amount_to_word.get_smart_in_words",
        # Delivery Note QR code methods
        "print_designer.custom.delivery_note_qr.generate_delivery_approval_qr",
        "print_designer.custom.delivery_note_qr.get_qr_code_image",
        "print_designer.custom.delivery_note_qr.get_delivery_status",
        # Delivery QR Jinja macros
        "print_designer.utils.delivery_qr_macros.render_delivery_approval_qr",
        # Typography CSS injection
        # "print_designer.api.global_typography.get_typography_css",
        "print_designer.utils.delivery_qr_macros.render_delivery_qr_compact",
        "print_designer.utils.delivery_qr_macros.render_delivery_status_badge",
        "print_designer.utils.delivery_qr_macros.render_delivery_approval_summary",
        "print_designer.utils.delivery_qr_macros.render_delivery_qr_with_instructions",
        "print_designer.utils.delivery_qr_macros.render_legacy_delivery_qr",
        # Thai Withholding Tax methods
        "print_designer.custom.withholding_tax.get_wht_certificate_data",
        "print_designer.custom.withholding_tax.determine_income_type",
        "print_designer.custom.withholding_tax.convert_to_thai_date",
        "print_designer.custom.withholding_tax.get_suggested_wht_rate",
        # Thai WHT Override and Debug methods
        "print_designer.regional.purchase_order_wht_override.get_thai_wht_calculation_debug_info",
        # Thai Billing amount conversion methods
        "print_designer.print_designer.doctype.thai_billing.thai_billing.get_thai_billing_amount_in_words",
    ]
}

# Boot session enhancements - consolidated
# (Moved to consolidated boot_session hook below)

# Override whitelisted methods to support signature and stamp in PDF generation and watermarks in print preview
override_whitelisted_methods = {
    "frappe.utils.print_format.download_pdf": "print_designer.utils.signature_stamp.download_pdf_with_signature_stamp",
    # Override print view to add watermark support from sidebar settings
    "frappe.www.printview.get_html_and_style": "print_designer.overrides.printview_watermark.get_html_and_style_with_watermark",
    "frappe.printing.get_print_format": "print_designer.api.print_format.get_print_format_with_watermark",
    # Override Print Settings API to include watermark fields in print sidebar
    "frappe.printing.page.print.print.get_print_settings_to_show": "print_designer.overrides.print_settings_api.get_print_settings_to_show",
    # Override Quotation make_sales_order to include WHT field mapping
    "erpnext.selling.doctype.quotation.quotation.make_sales_order": "print_designer.overrides.quotation_mapper.make_sales_order_with_wht",
    # Override Payment Entry creation to populate Thai tax fields from Sales Invoice
    "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry": "print_designer.custom.payment_entry_creation_hook.get_payment_entry_with_thai_tax",
}

# Installation
# ------------

before_install = "print_designer.install.before_install"
after_install = [
    "print_designer.install.after_install",
    # REMOVED: after_app_install is legacy and redundant
    "print_designer.utils.override_thailand.override_thailand_monkey_patch",
    "print_designer.install.handle_erpnext_override",
    "print_designer.api.enable_print_designer_ui.ensure_print_designer_ui_setup",  # Enable Print Designer UI visibility
    "print_designer.api.install_typography_ui.setup_typography_on_install",  # Install typography fields
    # REMOVED: thailand_wht_fields.py - Now handled by separate quotation module
    "print_designer.install.ensure_watermark_fields_installed",  # Ensure watermark fields are installed
    "print_designer.install.emergency_watermark_fix_fallback",  # Emergency fallback for critical watermark fields
    "print_designer.commands.install_quotation_fields.install_quotation_custom_fields",  # Install Quotation fields programmatically
    "print_designer.commands.install_company_thai_tax_fields.install_company_thai_tax_fields",  # Install Company Thai Tax fields
    "print_designer.commands.install_customer_fields.create_customer_fields",  # Install Customer branch_code field
    "print_designer.commands.install_employee_thai_tax_fields.install_employee_thai_tax_fields",  # Install Employee Thai Tax ID field
    "print_designer.commands.install_account_thai_fields.install_account_thai_fields",  # Install Account Thai translation fields
    "print_designer.commands.install_enhanced_retention_fields.install_enhanced_retention_fields",  # Install Company retention fields (construction_service, default_retention_rate, default_retention_account)
    "print_designer.commands.install_payment_entry_fields.install_payment_entry_custom_fields",  # Install Payment Entry Thai tax preview fields
    "print_designer.commands.install_payment_entry_thai_fields.execute",  # Install Payment Entry Thai compliance fields
    "print_designer.commands.install_purchase_invoice_fields.install_purchase_invoice_thai_tax_fields",  # Install Purchase Invoice Thai tax compliance fields
    "print_designer.commands.install_purchase_order_fields.execute",  # Install Purchase Order Thai tax compliance fields
    "print_designer.commands.install_item_service_field.install_item_service_field",  # Install Item Is Service field (required before WHT fields)
    "print_designer.commands.install_item_wht_fields.execute",  # Install Item WHT Income Type field for smart automation
    # DISABLED: old retention installer - using enhanced installer above
    # "print_designer.commands.restructure_retention_fields.restructure_retention_fields",  # Restructure retention fields to eliminate API loops
    # "print_designer.api.global_typography.after_install",
    # "print_designer.custom.company_tab.create_company_stamps_signatures_tab",
    "print_designer.install.thai_defaults.setup_thai_language_defaults",  # Setup Thai as default language for Thai users
    # Generate Account Thai translation files for external server access
    "print_designer.utils.account_file_api.generate_account_files_for_external_access",
]

# Boot session enhancements (Frappe v15+ uses extend_bootinfo, older versions use boot_session)
# OLD: boot_session = "print_designer.utils.signature_stamp.boot_session"
# OLD: extend_bootinfo = "print_designer.utils.signature_stamp.boot_session"
# NEW: Consolidated boot session with Print Designer + Thai Billing workspace
boot_session = "print_designer.boot.boot_session"
extend_bootinfo = "print_designer.boot.boot_session"

# Initialize protection against third-party app conflicts
after_migrate = [
    # CRITICAL: Install core Print Designer custom fields first (fixes print_designer_template_app missing error)
    "print_designer.install.ensure_custom_fields",
    "print_designer.utils.print_protection.initialize_print_protection",
    "print_designer.utils.override_thailand.override_thailand_monkey_patch",
    "print_designer.startup.initialize_print_designer",  # Initialize Print Designer components
    "print_designer.hooks.override_erpnext_install",  # Apply ERPNext overrides
    "print_designer.commands.install_signature_fields.create_signature_fields",  # Install signature fields using clean system
    "print_designer.api.enable_print_designer_ui.ensure_print_designer_ui_setup",  # Ensure Print Designer UI visibility after migration
    # REMOVED DUPLICATE: "print_designer.api.install_typography_ui.setup_typography_on_install" - already in after_install
    # REMOVED DUPLICATE: "print_designer.install.ensure_watermark_fields_installed" - already in after_install
    # REMOVED DUPLICATE: "print_designer.install.emergency_watermark_fix_fallback" - already in after_install
    "print_designer.commands.install_quotation_fields.install_quotation_custom_fields",  # Install Quotation fields programmatically
    "print_designer.commands.install_company_thai_tax_fields.install_company_thai_tax_fields",  # Install Company Thai Tax fields during migration
    "print_designer.commands.install_customer_fields.create_customer_fields",  # Ensure Customer branch_code field is installed during migration
    "print_designer.commands.install_employee_thai_tax_fields.install_employee_thai_tax_fields",  # Install Employee Thai Tax ID field during migration
    "print_designer.commands.install_account_thai_fields.install_account_thai_fields",  # Ensure Account Thai translation fields are installed during migration
    "print_designer.commands.install_enhanced_retention_fields.install_enhanced_retention_fields",  # Install Company retention fields (construction_service, default_retention_rate, default_retention_account)
    "print_designer.commands.install_sales_order_fields.reinstall_sales_order_custom_fields",  # Ensure Sales Order WHT fields have correct depends_on conditions
    "print_designer.commands.install_sales_invoice_fields.reinstall_sales_invoice_custom_fields",  # Ensure Sales Invoice WHT fields have correct depends_on conditions
    "print_designer.commands.install_payment_entry_fields.install_payment_entry_custom_fields",  # Ensure Payment Entry Thai tax preview fields are installed during migration
    "print_designer.commands.install_payment_entry_thai_fields.execute",  # Ensure Payment Entry Thai compliance fields are installed during migration
    "print_designer.commands.install_purchase_invoice_fields.install_purchase_invoice_thai_tax_fields",  # Ensure Purchase Invoice Thai tax compliance fields are installed during migration
    "print_designer.commands.install_purchase_order_fields.execute",  # Ensure Purchase Order Thai tax compliance fields are installed during migration
    "print_designer.commands.install_item_service_field.install_item_service_field",  # Ensure Item Is Service field is installed during migration (required before WHT fields)
    "print_designer.commands.install_item_wht_fields.execute",  # Ensure Item WHT Income Type field is installed during migration
    # Generate Account Thai translation files for external server access
    "print_designer.utils.account_file_api.generate_account_files_for_external_access",
    # Apply Account Thai translations after migration to ensure complete coverage
    "print_designer.commands.apply_account_thai_translations.apply_account_thai_translations",
]

# Uninstallation
# ------------

before_uninstall = [
    "print_designer.uninstall.before_uninstall",
    "print_designer.commands.install_signature_fields.uninstall_signature_fields",  # Remove all signature fields using clean system
    "print_designer.custom.company_tab.remove_company_stamps_signatures_tab",  # Remove Company tab on uninstall
    "print_designer.commands.install_customer_fields.uninstall_customer_fields",  # Remove Customer branch_code field
    "print_designer.commands.install_employee_thai_tax_fields.remove_employee_thai_tax_fields",  # Remove Employee Thai Tax ID field
    "print_designer.commands.install_account_thai_fields.remove_account_thai_translation_fields",  # Remove Account Thai translation fields
    "print_designer.commands.install_payment_entry_fields.uninstall_payment_entry_custom_fields",  # Remove Payment Entry Thai tax preview fields
    "print_designer.commands.install_payment_entry_thai_fields.remove_thai_fields",  # Remove Payment Entry Thai compliance fields
    "print_designer.commands.install_purchase_invoice_fields.remove_purchase_invoice_thai_tax_fields",  # Remove Purchase Invoice Thai tax compliance fields
    "print_designer.commands.install_purchase_order_fields.uninstall_purchase_order_fields",  # Remove Purchase Order Thai tax compliance fields
    "print_designer.commands.install_item_wht_fields.uninstall_item_wht_fields",  # Remove Item WHT Income Type field (must be before service field)
    "print_designer.commands.install_item_service_field.uninstall_item_service_field",  # Remove Item Is Service field
]
# after_uninstall = "print_designer.uninstall.after_uninstall"

# ------------
# PDF
# ------------

pdf_header_html = "print_designer.pdf.pdf_header_footer_html"
pdf_body_html = "print_designer.pdf.pdf_body_html"
pdf_footer_html = "print_designer.pdf.pdf_header_footer_html"

get_print_format_template = "print_designer.pdf.get_print_format_template"
# before_print = "print_designer.pdf.before_print"  # Moved to doc_events for better control


pdf_generator = "print_designer.pdf_generator.pdf.get_pdf"

override_doctype_class = {
    "Print Format": "print_designer.print_designer.overrides.print_format.PDPrintFormat",
    "Company": "print_designer.overrides.company.CustomCompany",
}

# Path Relative to the app folder where default templates should be stored
pd_standard_format_folder = "default_templates"

doc_events = {
    # Watermark
    "Watermark Settings": {
        "validate": "print_designer.api.watermark.validate_watermark_settings",
        "on_update": "print_designer.api.watermark.clear_watermark_cache",
    },
    "Print Format": {
        "on_update": "print_designer.api.watermark.clear_format_watermark_cache",
    },
    # Sales Invoice events - consolidated in doc_events section below
    "Purchase Invoice": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.regional.purchase_invoice_wht_override.validate_thai_wht_configuration",
        "before_save": "print_designer.regional.purchase_invoice_wht_override.override_purchase_invoice_wht_calculation",
        "on_update": "print_designer.regional.purchase_invoice_wht_override.override_purchase_invoice_wht_calculation",
        "on_submit": "print_designer.custom.purchase_invoice_wht_generator.on_submit_purchase_invoice",
    },
    # Sales Order and Quotation events - consolidated in doc_events section below
    "Purchase Order": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.regional.purchase_order_wht_override.validate_thai_wht_configuration",
        "before_save": "print_designer.regional.purchase_order_wht_override.override_purchase_order_wht_calculation",
        "on_update": "print_designer.regional.purchase_order_wht_override.override_purchase_order_wht_calculation",
    },
    "Delivery Note": {
        "before_print": "print_designer.pdf.before_print",
        # "on_submit": "print_designer.custom.delivery_note_qr.add_qr_to_delivery_note",  # Disabled due to field length errors
        "before_save": "print_designer.utils.field_sync.sync_delivery_note_fields",
    },
    "Purchase Receipt": {
        "before_print": "print_designer.pdf.before_print",
    },
    "Signature Basic Information": {
        "after_insert": "print_designer.utils.signature_integration.handle_signature_save",
        "on_update": "print_designer.utils.signature_integration.handle_signature_save",
        "after_save": "print_designer.api.signature_sync.auto_sync_on_signature_save",
    },
    # NEW: Digital Signature and Company Stamp events
    "Digital Signature": {
        "after_insert": "print_designer.utils.signature_integration.handle_signature_save",
        "on_update": "print_designer.utils.signature_integration.handle_signature_save",
    },
    "Company Stamp": {
        "after_insert": "print_designer.utils.signature_integration.handle_signature_save",
        "on_update": "print_designer.utils.signature_integration.handle_signature_save",
    },
    # Thai Withholding Tax events - Updated for GL entry modification approach
    "Payment Entry": {
        "before_print": "print_designer.pdf.before_print",
        "validate": [
            "print_designer.custom.payment_entry_retention.payment_entry_validate_thai_compliance",
            "print_designer.custom.payment_entry_retention.payment_entry_calculate_retention_amounts",
            "print_designer.custom.payment_entry_retention.payment_entry_validate_retention",
            "print_designer.custom.payment_entry_server_events.validate",
        ],
        "after_insert": "print_designer.custom.payment_entry_server_events.after_insert",
        "on_submit": [
            "print_designer.custom.payment_entry_retention.payment_entry_on_submit_thai_compliance",
            "print_designer.custom.payment_entry_server_events.on_submit",
        ],
        "on_cancel": [
            "print_designer.custom.payment_entry_retention.payment_entry_on_cancel_reverse_retention_entries",
            "print_designer.custom.payment_entry_server_events.on_cancel",
        ],
    },
    # Company DocType - Sync retention data to Company Retention Settings
    "Company": {
        "on_update": "print_designer.overrides.company.sync_company_retention_settings",
    },
    # Thai WHT Preview System - Sales Documents (Consolidated Calculations)
    "Quotation": {
        "before_print": "print_designer.pdf.before_print",
        "validate": [
            "print_designer.custom.quotation_calculations.quotation_calculate_thailand_amounts",
            "print_designer.custom.quotation_calculations.calculate_wht_preview_for_quotation",
        ],
    },
    "Sales Order": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.custom.sales_order_calculations.sales_order_calculate_thailand_amounts",
    },
    # Sales Invoice - Using consolidated calculation functions
    "Sales Invoice": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.custom.sales_invoice_calculations.sales_invoice_calculate_thailand_amounts",
    },
    # Customer WHT Configuration Changes - Consolidated handlers
    "Customer": {
        "validate": "print_designer.custom.customer_wht_config_handler.handle_customer_wht_config_changes",
        "on_update": "print_designer.custom.customer_wht_config_handler.handle_customer_wht_config_changes",
    },
    # Salary Slip - Employee Tax Ledger Integration
    "Salary Slip": {
        "on_submit": "print_designer.print_designer.doctype.employee_tax_ledger.employee_tax_ledger.update_from_salary_slip",
    },
}


# Monkey patch ERPNext install function
def override_erpnext_install():
    """Override ERPNext's create_print_setting_custom_fields function"""
    try:
        import erpnext.setup.install

        from print_designer.overrides.erpnext_install import (
            create_print_setting_custom_fields,
        )

        # Replace the function
        erpnext.setup.install.create_print_setting_custom_fields = (
            create_print_setting_custom_fields
        )

    except ImportError:
        # ERPNext not installed, skip override
        pass
    except Exception as e:
        import frappe

        frappe.logger().error(f"Error overriding ERPNext install function: {str(e)}")


# scheduler_events = {
#     "hourly": [
#         # will run hourly
#         "app.scheduled_tasks.update_database_usage"
#     ],
# }

# Scheduled tasks for watermark cache management
scheduler_events = {
    "daily": [
        "print_designer.api.watermark.cleanup_watermark_cache",
    ]
}


# Permission query conditions
permission_query_conditions = {
    "Watermark Template": "print_designer.api.watermark.get_permission_query_conditions"
}

# Regional overrides for Thai compliance
regional_overrides = {
    "Thailand": {
        "erpnext.accounts.doctype.payment_entry.payment_entry.add_regional_gl_entries": "print_designer.regional.payment_entry.add_regional_gl_entries"
    }
}


# Standard portal menu items
standard_portal_menu_items = [
    {
        "title": "Print Formats",
        "route": "/print-formats",
        "reference_doctype": "Print Format",
        "role": "Print Manager",
    }
]

# Website route rules for custom URLs
website_route_rules = [{"from_route": "/app/billing", "to_route": "/app/thai-billing"}]

# Workspace extension is handled by the existing extend_bootinfo hook
