from . import __version__ as app_version

app_name = "print_designer"
app_title = "Print Designer"
app_publisher = "Frappe Technologies Pvt Ltd."
app_description = "Frappe App to Design Print Formats using interactive UI."
app_email = "hello@frappe.io"
app_license = "AGPLv3"

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
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_js = ""

app_include_css = [
    "thai_fonts.bundle.css",
    "signature_stamp.bundle.css",
    "signature_preview.bundle.css",
    "delivery_approval.bundle.css",
]
# app_include_css = "thai_business_suite.app.bundle.css"


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
    "Print Format": "print_designer/client_scripts/print_format.js",
    "Signature Basic Information": "print_designer/client_scripts/signature_basic_information.js",
    "Delivery Note": "print_designer/public/js/delivery_approval.js",
    "Payment Entry": "print_designer/public/js/delivery_approval.js",
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

# Boot session enhancements
boot_session = "print_designer.utils.signature_stamp.boot_session"

# Override whitelisted methods to support signature and stamp in PDF generation and watermarks in print preview
override_whitelisted_methods = {
    "frappe.utils.print_format.download_pdf": "print_designer.utils.signature_stamp.download_pdf_with_signature_stamp",
    "frappe.www.printview.get_html_and_style": "print_designer.overrides.printview_watermark.get_html_and_style_with_watermark",
}

# Installation
# ------------

before_install = "print_designer.install.before_install"
after_install = "print_designer.install.after_install"
after_app_install = [
    "print_designer.install.after_app_install",
    "print_designer.utils.override_thailand.override_thailand_monkey_patch",
    "print_designer.install.handle_erpnext_override",  # Add this line
]

# Startup hooks
# -------------
on_startup = [
    "print_designer.startup.initialize_print_designer",
    "print_designer.hooks.override_erpnext_install",
    # NEW: Initialize signature and stamp patches
    "print_designer.utils.signature_stamp.startup_patches",
]

# Initialize protection against third-party app conflicts
after_migrate = [
    "print_designer.utils.print_protection.initialize_print_protection",
    "print_designer.utils.override_thailand.override_thailand_monkey_patch",
    "print_designer.api.safe_install.safe_install_signature_enhancements",
    "print_designer.install.ensure_custom_fields",
]

# Uninstallation
# ------------

before_uninstall = "print_designer.uninstall.before_uninstall"
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
    "Print Format": {
        "before_save": "print_designer.install.set_wkhtmltopdf_for_print_designer_format",
    },
    # Consolidated before_print hooks using the enhanced pdf.before_print function
    "Sales Invoice": {
        "before_print": "print_designer.pdf.before_print",
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
    # Thai Withholding Tax events
    "Payment Entry": {
        "validate": "print_designer.custom.withholding_tax.calculate_withholding_tax",
        "before_save": "print_designer.custom.withholding_tax.validate_wht_setup",
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
