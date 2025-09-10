from .signature_fields import get_signature_fields

# Print Designer specific custom fields
PRINT_DESIGNER_CUSTOM_FIELDS = {
    "Print Format": [
        {
            "default": "0",
            "fieldname": "print_designer",
            "fieldtype": "Check",
            "hidden": 1,
            "label": "Print Designer",
        },
        {
            "fieldname": "print_designer_print_format",
            "fieldtype": "JSON",
            "hidden": 1,
            "label": "Print Designer Print Format",
            "description": "This has json object that is used by main.html jinja template to render the print format.",
        },
        {
            "fieldname": "print_designer_header",
            "fieldtype": "JSON",
            "hidden": 1,
            "label": "Print Designer Header",
        },
        {
            "fieldname": "print_designer_body",
            "fieldtype": "JSON",
            "hidden": 1,
            "label": "Print Designer Body",
        },
        {
            "fieldname": "print_designer_after_table",
            "fieldtype": "JSON",
            "hidden": 1,
            "label": "Print Designer After Table",
        },
        {
            "fieldname": "print_designer_footer",
            "fieldtype": "JSON",
            "hidden": 1,
            "label": "Print Designer Footer",
        },
        {
            "fieldname": "print_designer_settings",
            "hidden": 1,
            "fieldtype": "JSON",
            "label": "Print Designer Settings",
        },
        {
            "fieldname": "print_designer_preview_img",
            "hidden": 1,
            "fieldtype": "Attach Image",
            "label": "Print Designer Preview Image",
        },
        {
            "depends_on": "eval:doc.print_designer && doc.standard == 'Yes'",
            "fieldname": "print_designer_template_app",
            "fieldtype": "Select",
            "label": "Print Designer Template Location",
            "default": "print_designer",
            "insert_after": "standard",
        },
        {
            "depends_on": "eval:doc.print_designer",
            "fieldname": "watermark_settings",
            "fieldtype": "Select",
            "label": "Watermark per Page",
            "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            "default": "None",
            "insert_after": "print_designer_template_app",
            "description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'",
        },
    ],
    "Print Settings": [
        {
            "label": "Copy Settings",
            "fieldname": "copy_settings_section",
            "fieldtype": "Section Break",
            "insert_after": "print_taxes_with_zero_amount",
            "collapsible": 1,
        },
        {
            "label": "Enable Multiple Copies",
            "fieldname": "enable_multiple_copies",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "copy_settings_section",
            "description": "Enable multiple copy generation for print formats",
        },
        {
            "label": "Default Copy Count",
            "fieldname": "default_copy_count",
            "fieldtype": "Int",
            "default": "2",
            "insert_after": "enable_multiple_copies",
            "depends_on": "enable_multiple_copies",
            "description": "Default number of copies to generate",
        },
        {
            "label": "Copy Labels",
            "fieldname": "copy_labels_column",
            "fieldtype": "Column Break",
            "insert_after": "default_copy_count",
        },
        {
            "label": "Default Original Label",
            "fieldname": "default_original_label",
            "fieldtype": "Data",
            "default": "Original",
            "insert_after": "copy_labels_column",
            "depends_on": "enable_multiple_copies",
            "description": "Default label for original copy",
        },
        {
            "label": "Default Copy Label",
            "fieldname": "default_copy_label",
            "fieldtype": "Data",
            "default": "Copy",
            "insert_after": "default_original_label",
            "depends_on": "enable_multiple_copies",
            "description": "Default label for additional copies",
        },
        {
            "label": "Show Copy Controls in Toolbar",
            "fieldname": "show_copy_controls_in_toolbar",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "default_copy_label",
            "depends_on": "enable_multiple_copies",
            "description": "Show copy controls in print preview toolbar",
        },
        {
            "label": "Watermark Settings",
            "fieldname": "watermark_settings_section",
            "fieldtype": "Section Break",
            "insert_after": "show_copy_controls_in_toolbar",
            "collapsible": 1,
        },
        {
            "label": "Watermark per Page",
            "fieldname": "watermark_settings",
            "fieldtype": "Select",
            "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            "default": "None",
            "insert_after": "watermark_settings_section",
            "description": "Control watermark display: None=no watermarks, Original on First Page=first page shows 'Original', Copy on All Pages=all pages show 'Copy', Original,Copy on Sequence=pages alternate between 'Original' and 'Copy'",
        },
        {
            "label": "Watermark Font Size (px)",
            "fieldname": "watermark_font_size",
            "fieldtype": "Int",
            "default": "12",
            "insert_after": "watermark_settings",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
            "description": "Font size for watermark text in pixels (default: 24px)",
        },
        {
            "label": "Watermark Position",
            "fieldname": "watermark_position",
            "fieldtype": "Select",
            "options": "Top Right\nTop Left\nBottom Right\nBottom Left\nCenter",
            "default": "Top Right",
            "insert_after": "watermark_font_size",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
            "description": "Position of watermark on the page",
        },
        {
            "label": "Watermark Font Family",
            "fieldname": "watermark_font_family",
            "fieldtype": "Select",
            "options": "Arial\nSarabun\nTimes New Roman\nCourier New\nHelvetica\nVerdana\nGeorgia\nTahoma",
            "default": "Sarabun",
            "insert_after": "watermark_position",
            "depends_on": "eval:doc.watermark_settings && doc.watermark_settings != 'None'",
            "description": "Font family for watermark text (Sarabun recommended for Thai unicode support)",
        },
    ],
}

# Delivery Note fields for QR approval system
DELIVERY_NOTE_CUSTOM_FIELDS = {
    "Delivery Note": [
        {
            "fieldname": "custom_delivery_approval_section",
            "fieldtype": "Section Break",
            "label": "Delivery Approval",
            "insert_after": "taxes_and_charges_added",
            "collapsible": 1
        },
        {
            "fieldname": "customer_approval_status",
            "fieldtype": "Select",
            "label": "Customer Approval Status",
            "options": "Pending\nApproved\nRejected",
            "default": "Pending",
            "insert_after": "custom_delivery_approval_section",
            "in_list_view": 1,
            "in_standard_filter": 1
        },
        {
            "fieldname": "customer_signature",
            "fieldtype": "Long Text",
            "label": "Customer Digital Signature",
            "insert_after": "customer_approval_status",
            "read_only": 1
        },
        {
            "fieldname": "customer_approved_by",
            "fieldtype": "Data",
            "label": "Customer Approved By",
            "insert_after": "customer_signature",
            "read_only": 1
        },
        {
            "fieldname": "customer_approved_on",
            "fieldtype": "Datetime",
            "label": "Customer Approved On",
            "insert_after": "customer_approved_by",
            "read_only": 1
        },
        {
            "fieldname": "approval_qr_code",
            "fieldtype": "Long Text",
            "label": "Approval QR Code",
            "insert_after": "customer_approved_on",
            "read_only": 1,
            "description": "Base64 encoded QR code for delivery approval"
        },
        # Legacy compatibility fields (maintaining existing system compatibility)
        {
            "fieldname": "custom_goods_received_status",
            "fieldtype": "Select",
            "label": "Goods Received Status (Legacy)",
            "options": "Pending\nApproved\nRejected",
            "default": "Pending",
            "insert_after": "approval_qr_code",
            "read_only": 1,
            "hidden": 1
        },
        {
            "fieldname": "custom_approval_qr_code",
            "fieldtype": "Long Text",
            "label": "Approval QR Code (Legacy)",
            "insert_after": "custom_goods_received_status",
            "read_only": 1,
            "hidden": 1
        },
        {
            "fieldname": "custom_approval_url",
            "fieldtype": "Data",
            "label": "Approval URL",
            "insert_after": "custom_approval_qr_code",
            "read_only": 1,
            "description": "URL for customer to approve delivery"
        },
        {
            "fieldname": "custom_customer_approval_date",
            "fieldtype": "Datetime",
            "label": "Customer Approval Date (Legacy)",
            "insert_after": "custom_approval_url",
            "read_only": 1,
            "hidden": 1
        },
        {
            "fieldname": "custom_approved_by",
            "fieldtype": "Data",
            "label": "Approved By (Legacy)",
            "insert_after": "custom_customer_approval_date",
            "read_only": 1,
            "hidden": 1
        },
        {
            "fieldname": "custom_customer_signature",
            "fieldtype": "Long Text",
            "label": "Customer Signature (Legacy)",
            "insert_after": "custom_approved_by",
            "read_only": 1,
            "hidden": 1
        },
        {
            "fieldname": "custom_rejection_reason",
            "fieldtype": "Small Text",
            "label": "Rejection Reason",
            "insert_after": "custom_customer_signature",
            "read_only": 1,
            "depends_on": "eval:doc.customer_approval_status == 'Rejected' || doc.custom_goods_received_status == 'Rejected'"
        }
    ]
}

# Global Defaults custom fields for font selection
GLOBAL_DEFAULTS_CUSTOM_FIELDS = {
    "Global Defaults": [
        {
            "fieldname": "typography_section",
            "fieldtype": "Section Break",
            "label": "Typography Settings",
            "insert_after": "disable_in_words",
            "collapsible": 1,
            "description": "Configure system-wide font preferences"
        },
        {
            "fieldname": "primary_font_family",
            "fieldtype": "Select",
            "label": "Primary Font Family",
            "options": "System Default\nSarabun (Thai)\nNoto Sans Thai\nIBM Plex Sans Thai\nKanit (Thai)\nPrompt (Thai)\nMitr (Thai)\nPridi (Thai)\nInter\nRoboto\nOpen Sans\nLato\nNunito Sans",
            "default": "Sarabun (Thai)",
            "insert_after": "typography_section",
            "description": "Primary font family for the system interface and documents. Thai fonts provide optimal Unicode support for Thai text."
        },
        {
            "fieldname": "font_preferences_column",
            "fieldtype": "Column Break",
            "insert_after": "primary_font_family"
        },
        {
            "fieldname": "enable_thai_font_support",
            "fieldtype": "Check",
            "label": "Enable Thai Font Support",
            "default": "1",
            "insert_after": "font_preferences_column",
            "description": "Enable system-wide Thai font support and optimizations"
        },
        {
            "fieldname": "custom_font_stack",
            "fieldtype": "Small Text",
            "label": "Custom Font Stack",
            "insert_after": "enable_thai_font_support",
            "depends_on": "eval:doc.primary_font_family == 'System Default'",
            "description": "Comma-separated list of font families for custom font stack. Example: 'Sarabun', 'Noto Sans Thai', 'Arial', sans-serif"
        },
        {
            "fieldname": "custom_typography_css",
            "fieldtype": "Long Text",
            "label": "Custom Typography CSS",
            "insert_after": "custom_font_stack",
            "hidden": 1,
            "read_only": 1,
            "description": "Generated CSS for typography override - managed automatically"
        }
    ],
    "Supplier": [
        {
            "fieldname": "pd_custom_branch_code",
            "fieldtype": "Data",
            "label": "Branch Code",
            "insert_after": "tax_id",
            "print_hide": 0,
            "allow_on_submit": 1,
            "translatable": 1,
            "default": "00000",
            "description": "Branch code for supplier tax documentation",
            "length": 20,
        }
    ]
}

# Combine Print Designer fields with Signature fields, Delivery Note fields, and Global Defaults fields
CUSTOM_FIELDS = {**PRINT_DESIGNER_CUSTOM_FIELDS, **get_signature_fields(), **DELIVERY_NOTE_CUSTOM_FIELDS, **GLOBAL_DEFAULTS_CUSTOM_FIELDS}
