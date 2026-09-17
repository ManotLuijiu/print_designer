# Copyright (c) 2026, AWS Solution Ltd. and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
    context.brand_html = "Get Original VAT"
    context.title = "Get Original VAT"


def flt(v):
    try:
        return float(v or 0)
    except (ValueError, TypeError):
        return 0.0


@frappe.whitelist()
def get_all_vat_transactions():
    """
    Return all VAT transactions by Import Clearance Item rows.
    Each row = one VAT record from the PI's Customs Entries (tabImport Clearance Item).
    """
    if not frappe.has_permission("Purchase Invoice", "read"):
        frappe.throw(frappe._("No permission to read Purchase Invoice"))

    # Query Import Clearance Item rows that have VAT
    # parenttype='Purchase Invoice' means this is a PI customs entry row
    rows = frappe.db.sql(
        """
        SELECT
            ici.name,
            ici.parent,
            ici.idx,
            ici.vendor_name,
            ici.vendor_display_name,
            ici.vat_type,
            ici.base_amount,
            ici.vat_amount,
            ici.is_vat,
            ici.tax_amount,
            ici.description,
            COALESCE(s.supplier_name, ici.vendor_name) AS vendor_display_name,
            pi.supplier_name AS pi_supplier_name,
            pi.supplier AS pi_supplier,
            pi.posting_date,
            pi.docstatus,
            pi.tbs_custom_po_type
        FROM `tabImport Clearance Item` ici
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = ici.parent
        LEFT JOIN `tabSupplier` s ON s.name = ici.vendor_name
        WHERE ici.parenttype = 'Purchase Invoice'
          AND ici.vat_amount > 0
        ORDER BY pi.posting_date DESC, ici.idx ASC
        LIMIT 500
        """,
        as_dict=True,
    )

    transactions = []
    for r in rows:
        # Determine the display vendor name
        vendor = r.vendor_display_name or r.pi_supplier_name or r.pi_supplier or r.vendor_name or "-"

        transactions.append({
            # Core identifiers — name+idx uniquely identify an ICI row
            "name": r.name,
            "row_idx": r.idx,
            # PI link
            "pi_name": r.parent,
            "pi_posting_date": r.posting_date,
            "pi_docstatus": r.docstatus,
            # Vendor / party
            "vendor": vendor,
            "description": r.description or "",
            # VAT details
            "vat_type": r.vat_type or "No VAT",
            "base_amount": flt(r.base_amount),
            "vat_amount": flt(r.vat_amount),
            # Status — will be populated below
            "has_original": 0,
            "is_input_vat_used": 0,
            "tpv_name": "",
            # Display type
            "doctype": "Import Clearance Item",
        })

    # Look up TPV records and mark status
    pi_names = list({t["pi_name"] for t in transactions})
    if pi_names:
        tpvs = frappe.db.sql(
            """
            SELECT tpv.name, tpv.purchase_invoice, tpv.has_original,
                   tpv.is_input_vat_used, tpv.vat_type
            FROM `tabThai Purchase VAT` tpv
            WHERE tpv.purchase_invoice IN %(pi_names)s
            """,
            {"pi_names": pi_names},
            as_dict=True,
        )
        tpv_map = {t.purchase_invoice: t for t in tpvs}

        for t in transactions:
            tpv = tpv_map.get(t["pi_name"])
            if tpv:
                t["has_original"] = tpv.has_original or 0
                t["is_input_vat_used"] = tpv.is_input_vat_used or 0
                t["tpv_name"] = tpv.name

    # Also include IUV records
    iuvs = frappe.db.sql(
        """
        SELECT name, purchase_invoice, supplier, supplier_name,
               posting_date, base_amount, vat_amount,
               source_doctype AS vat_type,
               has_original, docstatus
        FROM `tabInput VAT Undue`
        WHERE docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 100
        """,
        as_dict=True,
    )
    for i in iuvs:
        transactions.append({
            "name": i.name,
            "row_idx": 0,
            "pi_name": i.purchase_invoice,
            "pi_posting_date": i.posting_date,
            "pi_docstatus": i.docstatus,
            "vendor": i.supplier_name or i.supplier or "-",
            "description": "",
            "vat_type": i.vat_type or "-",
            "base_amount": flt(i.base_amount),
            "vat_amount": flt(i.vat_amount),
            "has_original": i.has_original or 0,
            "is_input_vat_used": 0,
            "tpv_name": "",
            "doctype": "Input VAT Undue",
        })

    # Sort by posting date desc
    transactions.sort(key=lambda t: t.get("pi_posting_date") or "", reverse=True)

    # Counts
    draft_count = sum(1 for t in transactions if t["pi_docstatus"] == 0)
    pending_reconcile = sum(1 for t in transactions if t["pi_docstatus"] == 1 and not t["has_original"])
    pending_use = sum(1 for t in transactions if t["has_original"] and not t["is_input_vat_used"])

    return {
        "transactions": transactions,
        "total": len(transactions),
        "pending_pi_draft": draft_count,
        "pending_pi_reconcile": pending_reconcile,
        "pending_pi_use": pending_use,
    }


@frappe.whitelist()
def toggle_reconciled(names, doctype=None):
    """
    Toggle has_original on TPV record for given PI names.
    Creates TPV if it doesn't exist.
    """
    if isinstance(names, str):
        import json
        names = json.loads(names)

    results = []
    for pi_name in names:
        try:
            # Get PI details
            pi = frappe.get_doc("Purchase Invoice", pi_name)
            pd = pi.posting_date

            tpv_name = frappe.db.exists("Thai Purchase VAT", {"purchase_invoice": pi_name})
            if tpv_name:
                frappe.db.set_value("Thai Purchase VAT", tpv_name, "has_original", 1)
            else:
                # Create new TPV via DB insert
                total_vat = flt(getattr(pi, "tbs_import_vat_amount", 0) or 0) + \
                            flt(getattr(pi, "tbs_local_vat_amount", 0) or 0) + \
                            flt(getattr(pi, "tbs_forwarder_vat_amount", 0) or 0) + \
                            flt(getattr(pi, "tbs_3rd_party_vat_amount", 0) or 0)
                po_type = getattr(pi, "tbs_custom_po_type", "General") or "General"
                vat_type = "Import" if po_type == "Import" else ("Undue" if po_type == "Service" else "General")
                tpv_name_new = "THVAT-PI-" + pi_name
                frappe.db.sql(
                    """
                    INSERT INTO `tabThai Purchase VAT` (
                        name, purchase_invoice, purchase_for_company, supplier, supplier_name,
                        posting_date, vat_month, vat_year, vat_type,
                        base_amount, vat_amount, total_amount,
                        has_original, workflow_state, docstatus,
                        owner, modified_by
                    ) VALUES (
                        %(name)s, %(purchase_invoice)s, %(company)s, %(supplier)s, %(supplier_name)s,
                        %(posting_date)s, %(vat_month)s, %(vat_year)s, %(vat_type)s,
                        0, %(vat_amount)s, %(vat_amount)s,
                        1, 'Completed', 0,
                        %(owner)s, %(owner)s
                    )
                    """,
                    {
                        "name": tpv_name_new,
                        "purchase_invoice": pi_name,
                        "company": pi.company,
                        "supplier": pi.supplier,
                        "supplier_name": pi.supplier_name,
                        "posting_date": pd,
                        "vat_month": str(pd.month) if pd else None,
                        "vat_year": str(pd.year) if pd else None,
                        "vat_type": vat_type,
                        "vat_amount": total_vat,
                        "owner": frappe.session.user,
                    },
                )
            results.append({"name": pi_name, "success": True, "tpv_name": tpv_name or tpv_name_new})
        except Exception as e:
            results.append({"name": pi_name, "success": False, "error": str(e)})

    frappe.db.commit()
    return results


@frappe.whitelist()
def toggle_vat_used(names, doctype=None):
    """
    Mark PI (via TPV) or TPV as used in VAT declaration.
    """
    if isinstance(names, str):
        import json
        names = json.loads(names)

    results = []
    for name in names:
        try:
            pi_exists = frappe.db.exists("Purchase Invoice", name)
            if pi_exists:
                # First ensure reconciled (TPV exists)
                toggle_reconciled([name])
                # Then mark TPV as used
                tpv_name = frappe.db.exists("Thai Purchase VAT", {"purchase_invoice": name})
                if tpv_name:
                    pi = frappe.get_doc("Purchase Invoice", name)
                    pd = pi.posting_date
                    frappe.db.set_value("Thai Purchase VAT", tpv_name, "is_input_vat_used", 1)
                    frappe.db.set_value("Thai Purchase VAT", tpv_name, "input_vat_used_month", str(pd.month))
                    frappe.db.set_value("Thai Purchase VAT", tpv_name, "input_vat_used_year", str(pd.year))
                results.append({"name": name, "success": True})
            else:
                # TPV — mark directly
                frappe.db.set_value("Thai Purchase VAT", name, "is_input_vat_used", 1)
                results.append({"name": name, "success": True})
        except Exception as e:
            results.append({"name": name, "success": False, "error": str(e)})

    frappe.db.commit()
    return results


@frappe.whitelist()
def delete_transaction(doctype, name):
    """Delete a VAT transaction record."""
    if doctype == "Input VAT Undue":
        if not frappe.has_permission("Input VAT Undue", "delete"):
            frappe.throw(frappe._("No permission to delete Input VAT Undue"))
        frappe.delete_doc("Input VAT Undue", name, ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "name": name}
    return {"success": False, "error": "Cannot delete this record type"}
