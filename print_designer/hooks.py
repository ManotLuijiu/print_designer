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
    "print_designer.commands.signature_setup.setup_signatures",
    "print_designer.commands.signature_setup.check_signature_status",
    "print_designer.commands.install_watermark_fields.install_watermark_fields",
    "print_designer.commands.install_thai_form_50_twi.install_thai_form_50_twi",
    "print_designer.commands.install_delivery_qr.install_delivery_qr",
    "print_designer.commands.install_complete_system.install_complete_system",
    "print_designer.commands.install_complete_system.check_system_status",
    "print_designer.commands.install_delivery_fields.install_delivery_note_fields",
    "print_designer.commands.install_typography_system.install_typography_system",
    "print_designer.commands.install_retention_fields.install_retention_fields",
    "print_designer.commands.install_retention_fields.check_retention_fields",
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
    # Thai WHT Preview System Commands
    "print_designer.commands.install_thai_wht_preview.install_thai_wht_preview",
    "print_designer.commands.install_thai_wht_preview.check_thai_wht_preview",
    "print_designer.commands.install_thai_wht_preview.remove_thai_wht_preview",
    "print_designer.commands.install_thai_wht_preview.test_thai_wht_preview",
    "print_designer.commands.install_thai_wht_preview.refresh_wht_preview",
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_js = [
    "print_watermark.bundle.js",
    # It is not bundled it is doctype_js
    # "delivery_approval.bundle.js",
    # "typography_injection.bundle.js",
]

app_include_css = [
    "thai_fonts.bundle.css",
    # "signature_stamp.bundle.css",
    # "signature_preview.bundle.css",
    # "delivery_approval.bundle.css",
    # "global_typography_override.bundle.css",
    # "company_preview.bundle.css",
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
    # "Print Format": "print_designer/client_scripts/print_format.js",
    # "Print Settings": "print_designer/client_scripts/print_settings.js",
    "Client Script": "print_designer/client_scripts/client_script.js",
    # "Global Defaults": "print_designer/client_scripts/global_defaults.js",
    # Corrected path for doctype_js
    "Quotation": "public/js/thailand_wht/thailand_wht_quotation.js",
    "Item": "public/js/thailand_wht/thailand_wht_item.js",
    "Payment Entry": [
        "public/js/delivery_approval.js",
        "public/js/thailand_wht/thailand_wht_payment_entry.js",
    ],
    "Sales Invoice": [
        "public/js/thailand_wht/thailand_wht_sales_invoice.js",
    ],
    "Sales Order": "public/js/thailand_wht/thailand_wht_sales_order.js",
    "Print Format": "public/js/print_format/print_format.js",
    "Print Settings": "public/js/print_format/print_settings.js",
    "Signature Basic Information": "public/js/stamps_signatures/signature_basic_information.js",
    "Delivery Note": "public/js/delivery_note/delivery_approval.js",
    "Company": "public/js/print_format/company.js",
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
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    # Company DocType - All Custom Fields for Print Designer
                    # Company - Stamps & Signatures Fields (relocated to proper sections)
                    "Company-company_signatures_section",
                    "Company-authorized_signature_1",
                    "Company-authorized_signature_2",
                    "Company-ceo_signature",
                    "Company-company_stamps_section",
                    "Company-company_stamp_1",
                    "Company-company_stamp_2",
                    "Company-official_seal",
                    # Company - Thai Business Configuration
                    "Company-thailand_service_business",
                    "Company-default_wht_account",
                    "Company-default_wht_rate",
                    "Company-construction_service",
                    "Company-default_retention_rate",
                    "Company-default_retention_account",
                    # Company - Retention Settings
                    "Company-retention_section",
                    "Company-retention_enabled",
                    "Company-retention_percentage",
                    "Company-retention_account",
                    "Company-retention_description",
                    "Company-retention_notes",
                    # Company - Thai WHT Settings
                    "Company-thai_wht_section",
                    "Company-wht_enabled",
                    "Company-default_wht_rate",
                    "Company-wht_liability_account",
                    "Company-wht_description",
                    "Company-wht_certificate_required",
                    # Company - Typography Settings
                    "Company-typography_section",
                    "Company-default_print_font",
                    "Company-enable_thai_fonts",
                    "Company-custom_css_styles",
                    # Company - Watermark Settings
                    "Company-watermark_section",
                    "Company-default_watermark_text",
                    "Company-watermark_enabled",
                    "Company-watermark_position",
                    "Company-watermark_opacity",
                    # Company - Print Format Settings
                    "Company-print_format_section",
                    "Company-default_print_format",
                    "Company-enable_company_signature",
                    "Company-auto_apply_watermark",
                    # Company - Document Numbering
                    "Company-document_numbering_section",
                    "Company-custom_invoice_prefix",
                    "Company-enable_thai_numbering",
                    "Company-thai_business_registration",
                    "Company-vat_registration_number",
                    # Sales Invoice - Signature Fields
                    "Sales Invoice-prepared_by_signature",
                    "Sales Invoice-approved_by_signature",
                    # Sales Invoice - Watermark Field
                    "Sales Invoice-watermark_text",
                    # Sales Invoice - Digisoft ERP Tab
                    "Sales Invoice-digisoft_erp_tab",
                    # Sales Invoice - Thai Tax Information Fields
                    "Sales Invoice-thai_tax_information_section",
                    "Sales Invoice-thai_invoice_type",
                    "Sales Invoice-thai_tax_invoice_number",
                    "Sales Invoice-thai_tax_invoice_date",
                    "Sales Invoice-thai_customer_tax_id",
                    "Sales Invoice-thai_customer_branch_code",
                    # Sales Invoice - Thai Compliance Fields
                    "Sales Invoice-thai_compliance_section",
                    "Sales Invoice-thai_vat_eligible",
                    "Sales Invoice-thai_export_eligible",
                    "Sales Invoice-thai_cash_receipt",
                    # Sales Invoice - VAT Treatment Field
                    "Sales Invoice-custom_vat_treatment",
                    # Sales Invoice - WHT (Withholding Tax) Fields
                    "Sales Invoice-subject_to_wht",
                    "Sales Invoice-wht_income_type",
                    "Sales Invoice-wht_description",
                    "Sales Invoice-wht_certificate_required",
                    "Sales Invoice-net_total_after_wht",
                    "Sales Invoice-net_total_after_wht_in_words",
                    "Sales Invoice-wht_note",
                    # Sales Invoice - Thai WHT Preview Fields
                    "Sales Invoice-thai_wht_preview_section",
                    "Sales Invoice-wht_amounts_column_break",
                    "Sales Invoice-wht_preview_column_break",
                    # Sales Invoice - Retention System Fields
                    "Sales Invoice-custom_subject_to_retention",
                    "Sales Invoice-custom_net_total_after_wht_retention",
                    "Sales Invoice-custom_net_total_after_wht_and_retention_in_words",
                    "Sales Invoice-custom_retention_note",
                    "Sales Invoice-custom_retention",
                    "Sales Invoice-custom_retention_amount",
                    "Sales Invoice-custom_withholding_tax",
                    "Sales Invoice-custom_withholding_tax_amount",
                    "Sales Invoice-custom_payment_amount",
                    # Quotation - Signature Fields
                    "Quotation-prepared_by_signature",
                    # Quotation - Watermark Field
                    "Quotation-watermark_text",
                    # Quotation - VAT Treatment Field
                    "Quotation-vat_treatment",
                    # Quotation - WHT (Withholding Tax) Fields
                    "Quotation-wht_note",
                    "Quotation-subject_to_wht",
                    "Quotation-wht_description",
                    "Quotation-wht_income_type",
                    "Quotation-net_total_after_wht_in_words",
                    "Quotation-estimated_wht_amount",
                    "Quotation-net_total_after_wht",
                    # Quotation - Thai WHT Preview Fields
                    "Quotation-thai_wht_preview_section",
                    "Quotation-wht_amounts_column_break",
                    "Quotation-wht_preview_column_break",
                    # Quotation - Retention System Fields
                    "Quotation-custom_subject_to_retention",
                    "Quotation-custom_net_total_after_wht_retention",
                    "Quotation-custom_net_total_after_wht_and_retention_in_words",
                    "Quotation-custom_retention",
                    "Quotation-custom_retention_amount",
                    "Quotation-custom_retention_note",
                    "Quotation-custom_withholding_tax",
                    "Quotation-custom_withholding_tax_amount",
                    "Quotation-custom_payment_amount",
                    # Sales Order - Signature Fields
                    "Sales Order-prepared_by_signature",
                    "Sales Order-approved_by_signature",
                    # Sales Order - Watermark Field
                    "Sales Order-watermark_text",
                    # Sales Order - Deposit Fields
                    "Sales Order-has_deposit",
                    "Sales Order-deposit_invoice",
                    "Sales Order-percent_deposit",
                    "Sales Order-column_break_euapx",
                    "Sales Order-section_break_o8q38",
                    "Sales Order-deposit_deduction_method",
                    # Sales Order - VAT Treatment Field
                    "Sales Order-custom_vat_treatment",
                    # Sales Order - WHT (Withholding Tax) Fields
                    "Sales Order-subject_to_wht",
                    "Sales Order-wht_note",
                    "Sales Order-wht_description",
                    "Sales Order-wht_income_type",
                    "Sales Order-net_total_after_wht_in_words",
                    "Sales Order-net_total_after_wht",
                    # Sales Order - Thai WHT Preview Fields
                    "Sales Order-thai_wht_preview_section",
                    "Sales Order-wht_amounts_column_break",
                    "Sales Order-wht_preview_column_break",
                    # Sales Order - Retention System Fields
                    "Sales Order-custom_subject_to_retention",
                    "Sales Order-custom_net_total_after_wht_retention",
                    "Sales Order-custom_net_total_after_wht_retention_in_words",
                    "Sales Order-custom_retention_note",
                    "Sales Order-custom_retention",
                    "Sales Order-custom_retention_amount",
                    "Sales Order-custom_withholding_tax",
                    "Sales Order-custom_withholding_tax_amount",
                    "Sales Order-custom_payment_amount",
                ],
            ]
        ],
    },
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
}

# Installation
# ------------

before_install = "print_designer.install.before_install"
after_install = [
    "print_designer.install.after_install",
    "print_designer.install.after_app_install",  # Legacy function - kept for compatibility
    "print_designer.utils.override_thailand.override_thailand_monkey_patch",
    "print_designer.install.handle_erpnext_override",
    "print_designer.api.enable_print_designer_ui.ensure_print_designer_ui_setup",  # Enable Print Designer UI visibility
    "print_designer.api.install_typography_ui.setup_typography_on_install",  # Install typography fields
    # REMOVED: thailand_wht_fields.py - Now handled by separate quotation module
    "print_designer.install.ensure_watermark_fields_installed",  # Ensure watermark fields are installed
    "print_designer.install.emergency_watermark_fix_fallback",  # Emergency fallback for critical watermark fields
    # DISABLED: Conflicts with fixture-based retention fields - using fixtures instead
    # The retention system (custom_retention, custom_retention_amount, etc.) is now managed
    # exclusively through fixtures in print_designer/fixtures/custom_field.json to prevent
    # conflicts and ensure consistent conditional visibility with depends_on expressions
    # "print_designer.commands.restructure_retention_fields.restructure_retention_fields",  # Restructure retention fields to eliminate API loops
    # "print_designer.api.global_typography.after_install",
    # "print_designer.custom.company_tab.create_company_stamps_signatures_tab",
]

# Boot session enhancements
boot_session = "print_designer.utils.signature_stamp.boot_session"
# Extend bootinfo hook (Frappe v15+ replacement for boot_session)
# --------------------------------------------------
extend_bootinfo = "print_designer.utils.signature_stamp.boot_session"

# Initialize protection against third-party app conflicts
after_migrate = [
    "print_designer.utils.print_protection.initialize_print_protection",
    "print_designer.utils.override_thailand.override_thailand_monkey_patch",
    "print_designer.startup.initialize_print_designer",  # Initialize Print Designer components
    "print_designer.hooks.override_erpnext_install",  # Apply ERPNext overrides
    "print_designer.api.safe_install.safe_install_signature_enhancements",
    # "print_designer.install.ensure_custom_fields",
    "print_designer.install.setup_enhanced_print_settings",  # Direct call for existing users
    # "print_designer.install.ensure_signature_fields",
    "print_designer.api.enable_print_designer_ui.ensure_print_designer_ui_setup",  # Ensure Print Designer UI visibility after migration
    "print_designer.api.install_typography_ui.setup_typography_on_install",  # Ensure typography fields installation
    # REMOVED: thailand_wht_fields.py - Now handled by separate quotation module
    # DISABLED: Using fixture-based retention fields instead of programmatic installation
    # Retention fields (custom_retention, custom_retention_amount, custom_withholding_tax,
    # custom_withholding_tax_amount, custom_payment_amount) are now managed exclusively
    # through fixtures to prevent conflicts and ensure proper conditional visibility
    # "print_designer.install.after_migrate",  # Ensure all fields including retention fields after migration
    "print_designer.install.ensure_watermark_fields_installed",  # Ensure watermark fields are installed after migration
    "print_designer.install.emergency_watermark_fix_fallback",  # Emergency fallback for critical watermark fields
    # "print_designer.api.global_typography.setup_default_typography",
    # "print_designer.custom.company_tab.create_company_stamps_signatures_tab",
]

# Uninstallation
# ------------

before_uninstall = [
    "print_designer.uninstall.before_uninstall",
    "print_designer.custom.company_tab.remove_company_stamps_signatures_tab",  # Remove Company tab on uninstall
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
    # Global Defaults - Auto-apply typography changes
    # "Global Defaults": {
    #     "on_update": "print_designer.api.global_typography.on_global_defaults_update",
    # },
    # Watermark
    "Watermark Settings": {
        "validate": "print_designer.api.watermark.validate_watermark_settings",
        "on_update": "print_designer.api.watermark.clear_watermark_cache",
    },
    # "Print Format": {
    #     "on_update": "print_designer.api.watermark.clear_format_watermark_cache"
    # },
    "Print Format": {
        "before_save": "print_designer.install.set_wkhtmltopdf_for_print_designer_format",
        "on_update": "print_designer.api.watermark.clear_format_watermark_cache",
    },
    # Sales Invoice events - consolidated in doc_events section below
    "Purchase Invoice": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
    },
    # Sales Order and Quotation events - consolidated in doc_events section below
    "Purchase Order": {
        "before_print": "print_designer.pdf.before_print",
    },
    "Delivery Note": {
        "before_print": "print_designer.pdf.before_print",
        "on_submit": "print_designer.custom.delivery_note_qr.add_qr_to_delivery_note",
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
    # Thai Withholding Tax events - DISABLED: Missing custom fields cause save/submit issues
    # "Payment Entry": {
    #     "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
    #     "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
    #     "on_submit": "print_designer.accounting.thailand_wht_integration.process_payment_entry_wht",
    # },
    # Company DocType - Sync retention data to Company Retention Settings
    "Company": {
        "validate": "print_designer.overrides.company.sync_company_retention_settings",
        "on_update": "print_designer.overrides.company.sync_company_retention_settings",
    },
    # Thai WHT Preview System - Sales Documents
    "Quotation": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.custom.quotation_calculations.quotation_calculate_thailand_amounts",
    },
    "Sales Order": {
        "before_print": "print_designer.pdf.before_print",
        # "validate": "print_designer.custom.thai_wht_events.calculate_wht_preview_on_validate",  # Generic handler - commented out
        "validate": "print_designer.custom.sales_order_calculations.sales_order_calculate_thailand_amounts",  # Specific Sales Order handler like Quotation
    },
    # Sales Invoice - Updated to use specific calculation module like Quotation/Sales Order
    "Sales Invoice": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.custom.sales_invoice_calculations.sales_invoice_calculate_thailand_amounts",  # Specific Sales Invoice handler like Quotation
        # "validate": [  # Old configuration - commented out
        #     "print_designer.custom.sales_invoice_calculations.sales_invoice_calculate_thailand_amounts",
        #     "print_designer.custom.thai_wht_events.sales_invoice_wht_preview_handler",  # Generic handler - commented out
        # ],
        # "on_submit": "print_designer.custom.thai_wht_events.sales_invoice_wht_preview_handler",  # Generic handler - commented out
        # "on_cancel": "print_designer.custom.thai_wht_events.sales_invoice_wht_preview_handler",  # Generic handler - commented out
    },
    # Customer WHT Configuration Changes
    "Customer": {
        "validate": "print_designer.custom.thai_wht_events.customer_wht_config_changed",
        "on_update": "print_designer.custom.thai_wht_events.customer_wht_config_changed",
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
scheduler_events = {"daily": ["print_designer.api.watermark.cleanup_watermark_cache"]}


# Permission query conditions
permission_query_conditions = {
    "Watermark Template": "print_designer.api.watermark.get_permission_query_conditions"
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
