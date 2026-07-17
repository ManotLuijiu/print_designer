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
window.watermark_enabled = 0;
{% try %}
{% if frappe.db.exists('DocType', 'Watermark Settings') and frappe.db.exists('Watermark Settings', None) %}
{% set ws = frappe.get_single('Watermark Settings') %}
window.watermark_enabled = {{ ws.enabled if ws.enabled else 0 }};
{% endif %}
{% except %}
window.watermark_enabled = 0;
{% endtry %}
"""
