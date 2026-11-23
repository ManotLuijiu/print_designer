"""Project and report VAT for customer payments of service Sales Invoices."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt, getdate

from print_designer.custom.output_vat_undue_tracking import (
    STATUS_CONVERTED,
    STATUS_PENDING,
    convert_to_output_vat,
)
from print_designer.custom.sales_invoice_tax_contract import (
    CLASSIFICATION_SERVICES,
    VAT_TREATMENT_EXEMPT,
    get_service_tax_snapshot,
)
from print_designer.custom.thai_company_registration import get_company_registration


def _service_allocations(payment):
    if payment.get("payment_type") != "Receive" or payment.get("party_type") != "Customer":
        return []

    allocations = defaultdict(float)
    invoice_totals = {}
    for ref in payment.get("references") or []:
        if not flt(ref.allocated_amount):
            continue
        if (
            flt(ref.allocated_amount) < 0 or ref.reference_doctype != "Sales Invoice"
            or not ref.reference_name or flt(ref.total_amount) <= 0
        ):
            return []
        allocations[ref.reference_name] += flt(ref.allocated_amount)
        invoice_totals[ref.reference_name] = flt(ref.total_amount)

    result = []
    for invoice_name, allocated in allocations.items():
        invoice = frappe.get_doc("Sales Invoice", invoice_name)
        if (
            invoice.docstatus != 1 or invoice.get("is_return")
            or invoice.company != payment.company or invoice.customer != payment.party
        ):
            return []
        snapshot = get_service_tax_snapshot(invoice)
        if snapshot.classification != CLASSIFICATION_SERVICES or not snapshot.treatment:
            return []
        result.append((invoice, snapshot, allocated, invoice_totals[invoice_name]))
    return result


def apply_service_receipt_vat(payment):
    """Populate the draft/submit values without posting VAT or creating rows."""
    if (
        payment.get("payment_type") != "Receive" or payment.get("party_type") != "Customer"
        or not payment.meta.has_field("pd_custom_vat_amount")
    ):
        return {}

    allocations = _service_allocations(payment)
    if not allocations:
        if not payment.name or payment.get("pd_custom_tax_invoice_number") != payment.name:
            return {}
        values = {
            field: value for field, value in {
                "pd_custom_vat_amount": 0,
                "pd_custom_tax_invoice_number": None,
                "pd_custom_tax_invoice_date": None,
            }.items() if payment.meta.has_field(field)
        }
        payment.update(values)
        return values

    treatments = {snapshot.treatment for _, snapshot, _, _ in allocations}
    values = {"pd_custom_vat_amount": 0}
    exempt_receipt = treatments == {VAT_TREATMENT_EXEMPT}
    if exempt_receipt:
        values["pd_custom_vat_treatment"] = VAT_TREATMENT_EXEMPT
    if any(snapshot.is_deferred for _, snapshot, _, _ in allocations):
        if get_company_registration(payment.company, payment.posting_date).is_registered:
            vat_amount = sum(
                snapshot.vat_amount * min(allocated / total, 1)
                for _, snapshot, allocated, total in allocations if snapshot.is_deferred
            )
            values["pd_custom_vat_amount"] = flt(vat_amount, payment.precision("pd_custom_vat_amount"))
    has_receipt_number = payment.name and (payment.flags.in_insert or not payment.is_new())
    if has_receipt_number and (exempt_receipt or values["pd_custom_vat_amount"] > 0):
        values.update(
            pd_custom_tax_invoice_number=payment.name,
            pd_custom_tax_invoice_date=payment.posting_date,
        )
    elif payment.get("pd_custom_tax_invoice_number") == payment.name and payment.name:
        values.update(pd_custom_tax_invoice_number=None, pd_custom_tax_invoice_date=None)

    values = {field: value for field, value in values.items() if payment.meta.has_field(field)}
    payment.update(values)
    return values


def record_service_receipt_vat(payment):
    """Mirror one fully settled service invoice in the one-row-per-invoice ledger."""
    if (
        payment.get("payment_type") != "Receive" or payment.docstatus != 1
        or not frappe.db.exists("DocType", "Thai Sales VAT")
    ):
        return

    allocations = _service_allocations(payment)
    if len(allocations) != 1:
        return
    invoice, snapshot, allocated, total = allocations[0]
    if flt(allocated - total, payment.precision("paid_amount")):
        return

    exempt = snapshot.treatment == VAT_TREATMENT_EXEMPT
    vat_amount = flt(payment.get("pd_custom_vat_amount"))
    if not exempt and (not snapshot.is_deferred or vat_amount <= 0):
        return
    if payment.get("pd_custom_tax_invoice_number") != payment.name or not payment.get("pd_custom_tax_invoice_date"):
        frappe.throw(_("The receipt is missing its tax invoice number or date."))
    if not exempt:
        _verify_posted_output_vat(payment, vat_amount)

    name = frappe.db.get_value("Thai Sales VAT", {"sales_invoice": invoice.name}, "name")
    record = frappe.get_doc("Thai Sales VAT", name, for_update=True) if name else frappe.new_doc("Thai Sales VAT")
    if name and record.get("vat_type") == "VAT Due":
        if record.payment_entry_reference == payment.name:
            record.rename_for_receipt()
            return
        frappe.throw(_("Sales Invoice {0} already has an Output VAT record.").format(invoice.name))

    date = getdate(payment.posting_date)
    record.update({
        "sales_invoice": invoice.name,
        "customer": invoice.customer,
        "customer_name": invoice.customer_name,
        "posting_date": invoice.posting_date,
        "due_date": invoice.due_date,
        "invoice_no": invoice.name,
        "customer_tax_id": invoice.get("tax_id") or frappe.db.get_value("Customer", invoice.customer, "tax_id"),
        "vat_type": "VAT Due",
        "payment_entry_reference": payment.name,
        "tax_invoice_number": payment.pd_custom_tax_invoice_number,
        "tax_invoice_date": payment.pd_custom_tax_invoice_date,
        "vat_conversion_date": date,
        "base_amount": snapshot.eligible_service_base,
        "vat_amount": 0 if exempt else vat_amount,
        "total_amount": flt(invoice.base_grand_total),
        "is_vat_exempt": int(exempt),
        "vat_month": f"{date.month:02d}",
        "vat_year": str(date.year),
    })
    tracking_name = None
    if frappe.db.exists("DocType", "Output VAT Undue"):
        tracking_name = frappe.db.get_value("Output VAT Undue", {"sales_invoice": invoice.name}, "name")
    if tracking_name:
        record.customer_branch = frappe.db.get_value("Output VAT Undue", tracking_name, "customer_branch")
    record.flags.service_receipt_amounts = {
        field: record.get(field) for field in ("base_amount", "vat_amount", "total_amount")
    }
    record.save(ignore_permissions=True)
    record.rename_for_receipt()
    if tracking_name and not exempt:
        convert_to_output_vat(invoice.name, payment.pd_custom_tax_invoice_number, date, vat_amount)


def _verify_posted_output_vat(payment, vat_amount):
    accounts = frappe.get_cached_value(
        "Company", payment.company, ["default_output_vat_undue_account", "default_output_vat_account"], as_dict=True
    )
    undue = accounts.default_output_vat_undue_account
    due = accounts.default_output_vat_account
    rows = frappe.get_all(
        "GL Entry",
        filters={
            "voucher_type": "Payment Entry", "voucher_no": payment.name,
            "company": payment.company, "is_cancelled": 0,
            "account": ["in", [account for account in (undue, due) if account]],
        },
        fields=["account", "debit", "credit"],
    )
    payable = sum(flt(row.credit) - flt(row.debit) for row in rows if row.account == due)
    transferred = sum(flt(row.debit) - flt(row.credit) for row in rows if row.account == undue)
    precision = payment.precision("pd_custom_vat_amount")
    if not undue or not due or flt(payable - vat_amount, precision) or flt(transferred - vat_amount, precision):
        frappe.throw(_("The receipt's posted Output VAT does not match its Sales Invoice VAT. Review the VAT accounts."))


def reverse_service_receipt_vat(payment):
    if payment.get("payment_type") != "Receive" or not frappe.db.exists("DocType", "Thai Sales VAT"):
        return
    for name in frappe.get_all(
        "Thai Sales VAT",
        filters={"payment_entry_reference": payment.name, "vat_type": "VAT Due"},
        pluck="name",
    ):
        record = frappe.get_doc("Thai Sales VAT", name, for_update=True)
        if not record.is_vat_exempt and record.tax_invoice_number != payment.name:
            continue
        if record.is_output_vat_reported:
            frappe.throw(_("This receipt is already included in a filed Output VAT report."))
        invoice = frappe.get_doc("Sales Invoice", record.sales_invoice)
        snapshot = get_service_tax_snapshot(invoice)
        record.update({
            "vat_type": "VAT Undue",
            "payment_entry_reference": None,
            "tax_invoice_number": snapshot.tax_invoice_number,
            "tax_invoice_date": snapshot.tax_invoice_date,
            "vat_conversion_date": None,
            "vat_month": f"{getdate(invoice.posting_date).month:02d}",
            "vat_year": str(getdate(invoice.posting_date).year),
        })
        record.save(ignore_permissions=True)
        if not frappe.db.exists("DocType", "Output VAT Undue"):
            continue
        tracking = frappe.db.get_value(
            "Output VAT Undue",
            {"sales_invoice": invoice.name, "status": STATUS_CONVERTED, "tax_invoice_number": payment.name},
            ["name", "vat_amount"], as_dict=True,
        )
        if tracking:
            frappe.db.set_value("Output VAT Undue", tracking.name, {
                "status": STATUS_PENDING,
                "tax_invoice_number": None,
                "tax_invoice_date": None,
                "converted_date": None,
                "converted_by": None,
                "recognized_vat_amount": 0,
                "remaining_vat_amount": tracking.vat_amount,
            })
