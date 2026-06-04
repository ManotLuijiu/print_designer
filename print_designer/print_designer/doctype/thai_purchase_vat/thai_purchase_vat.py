# Copyright (c) 2026, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ThaiPurchaseVAT(Document):
	pass


def create_thai_purchase_vat(doc, method):
    """Create Thai Purchase VAT record when Purchase Invoice is submitted"""
    if doc.doctype != "Purchase Invoice" or doc.docstatus != 1:
        return
    existing = frappe.db.exists("Thai Purchase VAT", {"purchase_invoice": doc.name})
    if existing:
        return
    if doc.base_total_taxes_and_charges <= 0:
        return
    thai_vat = frappe.new_doc("Thai Purchase VAT")
    thai_vat.purchase_invoice = doc.name
    thai_vat.purchase_for_company = doc.company
    thai_vat.save()
    frappe.msgprint(f"Thai Purchase VAT record created: {thai_vat.name}")
