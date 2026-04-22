import frappe


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def twc_search(doctype, txt, searchfield, start, page_len, filters):
    """
    Custom search for Tax Withholding Category.
    Returns (name, category_name, category_name_en) tuples.

    Frappe's build_for_autosuggest expects: (value, label, description)
    - label = category_name (Thai) shown as bold dropdown text
    - description = category_name_en (English) shown as secondary text
    - value = name (saved when user selects)
    """
    results = frappe.db.sql("""
        SELECT name, category_name, COALESCE(category_name_en, '') as category_name_en
        FROM `tabTax Withholding Category`
        WHERE (name LIKE %(txt)s
           OR category_name LIKE %(txt)s
           OR category_name_en LIKE %(txt)s)
        LIMIT %(page_len)s OFFSET %(start)s
    """, {"txt": f"%{txt}%", "start": start, "page_len": page_len})

    # Return tuples: (value, label, description)
    # label = category_name already contains "{thai_name} {rate}% (ภงด.x)"
    return [(r[0], r[1], "") for r in results]
