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
    "print_designer.commands.install_thailand_wht_fields.install_thailand_wht_fields",
    "print_designer.commands.install_thailand_wht_fields.check_thailand_wht_fields",
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
    # {
    #     "doctype": "DocType",
    #     "filters": [
    #         [
    #             "name",
    #             "in",
    #             [
    #                 "Watermark Settings",
    #                 "Watermark Template",
    #                 "Print Format Watermark Config",
    #                 "Digital Signature",
    #                 "Signature Basic Information",
    #                 "Signature Usage",
    #             ],
    #         ]
    #     ],
    # },
    # Custom Fields are installed programmatically via install.py to avoid conflicts with existing fields
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    # Sales Invoice - Retention System Fields (for learning/export)
                    "Sales Invoice-custom_retention",
                    "Sales Invoice-custom_retention_amount", 
                    "Sales Invoice-custom_withholding_tax",
                    "Sales Invoice-custom_withholding_tax_amount",
                    "Sales Invoice-custom_payment_amount",
                ],
            ]
        ],
    },
    # {
    #     "doctype": "Custom Field",
    #     "filters": [
    #         [
    #             "name", 
    #             "in",
    #             [
    #                 # Company DocType - Stamps & Signatures Tab and Fields
    #                 "Company-stamps_signatures_tab",
    #                 "Company-company_signatures_section",
    #                 "Company-authorized_signature_1",
    #                 "Company-authorized_signature_2",
    #                 "Company-ceo_signature",
    #                 "Company-company_stamps_section",
    #                 "Company-company_stamp_1",
    #                 "Company-company_stamp_2",
    #                 "Company-official_seal",
    # Print Format - Print Designer Fields (commented to prevent conflicts)
    # "Print Format-print_designer",
    # "Print Format-print_designer_print_format",
    # "Print Format-print_designer_header",
    # "Print Format-print_designer_body",
    # "Print Format-print_designer_after_table",
    # "Print Format-print_designer_footer",
    # "Print Format-print_designer_settings",
    # "Print Format-print_designer_preview_img",
    # "Print Format-print_designer_template_app",
    # "Print Format-watermark_settings",
    # Print Settings - Copy and Watermark Settings (commented to prevent conflicts)
    # "Print Settings-copy_settings_section",
    # "Print Settings-enable_multiple_copies",
    # "Print Settings-default_copy_count",
    # "Print Settings-copy_labels_column",
    # "Print Settings-default_original_label",
    # "Print Settings-default_copy_label",
    # "Print Settings-show_copy_controls_in_toolbar",
    # "Print Settings-watermark_settings_section",
    # "Print Settings-watermark_settings",
    # "Print Settings-watermark_font_size",
    # "Print Settings-watermark_position",
    # "Print Settings-watermark_font_family",
    # Global Defaults - Typography Settings (commented to prevent conflicts)
    # "Global Defaults-typography_section",
    # "Global Defaults-primary_font_family",
    # "Global Defaults-font_preferences_column",
    # "Global Defaults-enable_thai_font_support",
    # "Global Defaults-custom_font_stack",
    # "Global Defaults-custom_typography_css",
    # HR Module - Employee & User Signatures (commented to prevent conflicts)
    # "Employee-signature_image",
    # "User-signature_image",
    # "Designation-designation_signature",
    # "Designation-signature_authority_level",
    # "Designation-max_approval_amount",
    # CRM Module (commented to prevent conflicts)
    # "Customer-signature_image",
    # "Lead-signature_image",
    # "Supplier-signature_image",
    # Projects Module (commented to prevent conflicts)
    # "Project-project_manager_signature",
    # "Item-quality_inspector_signature",
    # Sales Module - Transaction Documents (commented to prevent conflicts)
    # "Sales Invoice-prepared_by_signature",
    # "Sales Invoice-approved_by_signature",
    # "Sales Order-prepared_by_signature",
    # "Sales Order-approved_by_signature",
    # "Quotation-prepared_by_signature",
    # Purchase Module - Transaction Documents (commented to prevent conflicts)
    # "Purchase Invoice-prepared_by_signature",
    # "Purchase Invoice-approved_by_signature",
    # "Purchase Order-prepared_by_signature",
    # "Purchase Order-approved_by_signature",
    # "Request for Quotation-prepared_by_signature",
    # Stock Module - Delivery & Receipt (commented to prevent conflicts)
    # "Delivery Note-prepared_by_signature",
    # "Delivery Note-delivered_by_signature",
    # "Delivery Note-received_by_signature",
    # "Delivery Note-custom_delivery_approval_section",
    # "Delivery Note-customer_approval_status",
    # "Delivery Note-customer_signature",
    # "Delivery Note-customer_approved_by",
    # "Delivery Note-customer_approved_on",
    # "Delivery Note-approval_qr_code",
    # "Delivery Note-custom_goods_received_status",
    # "Delivery Note-custom_approval_qr_code",
    # "Delivery Note-custom_approval_url",
    # "Delivery Note-custom_customer_approval_date",
    # "Delivery Note-custom_approved_by",
    # "Delivery Note-custom_customer_signature",
    # "Delivery Note-custom_rejection_reason",
    # "Purchase Receipt-prepared_by_signature",
    # "Purchase Receipt-received_by_signature",
    # Asset Module (commented to prevent conflicts)
    # "Asset-custodian_signature",
    # HR Module - Additional (commented to prevent conflicts)
    # "Job Offer-hr_signature",
    # "Job Offer-candidate_signature",
    # "Appraisal-appraiser_signature",
    # "Appraisal-employee_signature",
    # Quality Module (commented to prevent conflicts)
    # "Quality Inspection-inspector_signature",
    # "Quality Inspection-supervisor_signature",
    # Maintenance Module (commented to prevent conflicts)
    # "Maintenance Schedule-technician_signature",
    # Custom DocTypes (commented to prevent conflicts)
    # "Contract-party_signature",
    # "Contract-witness_signature",
    # ],
    # ]
    # ],
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
    "print_designer.thailand_wht_fields.install_thailand_wht_fields",  # Install Thailand WHT fields
    "print_designer.install.ensure_watermark_fields_installed",  # Ensure watermark fields are installed
    "print_designer.install.emergency_watermark_fix_fallback",  # Emergency fallback for critical watermark fields
    "print_designer.commands.restructure_retention_fields.restructure_retention_fields",  # Restructure retention fields to eliminate API loops
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
    "print_designer.thailand_wht_fields.install_thailand_wht_fields",  # Install Thailand WHT fields
    "print_designer.install.after_migrate",  # Ensure all fields including retention fields after migration
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
    # Consolidated before_print hooks using the enhanced pdf.before_print function
    # Temporarily disabled Sales Invoice before_print due to Chrome issues
    "Sales Invoice": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.print_designer.doctype.company_retention_settings.company_retention_settings.sales_invoice_validate",
        "before_save": "print_designer.print_designer.doctype.company_retention_settings.company_retention_settings.sales_invoice_before_save",
    },
    "Purchase Invoice": {
        "before_print": "print_designer.pdf.before_print",
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
    },
    "Sales Order": {
        "before_print": "print_designer.pdf.before_print",
    },
    "Purchase Order": {
        "before_print": "print_designer.pdf.before_print",
    },
    "Quotation": {
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
