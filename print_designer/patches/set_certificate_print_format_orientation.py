import frappe

CERTIFICATE_DOCTYPE = "Withholding Tax Certificate"
ORIENTATION_FIELD = "page_orientation"
PORTRAIT = "Portrait"


def execute():
    """Give the certificate print formats an explicit A4 Portrait default.

    ``page_orientation`` is a Print Designer custom field on Print Format.
    Certificate formats that were created before that field existed carry no
    orientation, so the desk preview falls back to the global Print Settings
    and can start in Landscape.  Only empty values are filled here, an
    orientation that was chosen explicitly is never changed.
    """
    if not frappe.db.exists("DocType", CERTIFICATE_DOCTYPE):
        return
    if not frappe.db.exists("Custom Field", {"dt": "Print Format", "fieldname": ORIENTATION_FIELD}):
        return

    print_formats = frappe.get_all(
        "Print Format",
        filters={"doc_type": CERTIFICATE_DOCTYPE},
        fields=["name", ORIENTATION_FIELD],
    )
    for print_format in print_formats:
        if print_format.get(ORIENTATION_FIELD):
            continue
        frappe.db.set_value(
            "Print Format",
            print_format["name"],
            ORIENTATION_FIELD,
            PORTRAIT,
            update_modified=False,
        )
