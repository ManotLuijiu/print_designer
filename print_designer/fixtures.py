# File: print_designer/fixtures.py

"""
Fixtures for Print Designer module
Ensures DocTypes are properly exported and imported across environments
"""

# Export DocTypes as fixtures to ensure they're included in app migrations
app_include_js = ["print_watermark.bundle.js"]

fixtures = [
    {
        "doctype": "DocType",
        "filters": [
            [
                "name",
                "in",
                [
                    "Watermark Settings",
                    "Watermark Template",
                    "Print Format Watermark Config",
                ],
            ]
        ],
    },
    {
        "doctype": "Custom Field",
        "filters": [
            ["dt", "=", "Print Settings"],
            ["fieldname", "like", "watermark_%"],
        ],
    },
]

# Boot session defaults
boot_session = """
window.watermark_enabled = {{ frappe.get_single('Watermark Settings').enabled if frappe.db.exists('Watermark Settings', 'Watermark Settings') else 0 }};
"""
