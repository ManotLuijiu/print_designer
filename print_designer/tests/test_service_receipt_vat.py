from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe
import pytest

from print_designer.custom import service_receipt_vat as receipt_vat
from print_designer.custom.sales_invoice_tax_contract import (
    CLASSIFICATION_SERVICES,
    REASON_DEFERRED_SERVICE,
    VAT_TREATMENT_EXEMPT,
    VAT_TREATMENT_UNDUE,
    ServiceTaxSnapshot,
)


def _receipt(allocated=107, **values):
    payment = frappe._dict(
        name="RV-1", company="Company", party="Customer", party_type="Customer",
        payment_type="Receive", posting_date="2026-09-04", docstatus=0,
        references=[SimpleNamespace(
            reference_doctype="Sales Invoice", reference_name="SI-1",
            allocated_amount=allocated, total_amount=107,
        )],
    )
    payment.update(values)
    payment.meta = Mock()
    payment.meta.has_field.return_value = True
    payment.flags = frappe._dict(in_insert=True)
    payment.precision = Mock(return_value=2)
    payment.is_new = Mock(return_value=True)
    return payment


def test_registered_receipt_projects_vat_and_uses_its_own_number_and_date():
    invoice = frappe._dict(name="SI-1", company="Company", customer="Customer", docstatus=1)
    snapshot = ServiceTaxSnapshot(
        classification=CLASSIFICATION_SERVICES, treatment=VAT_TREATMENT_UNDUE,
        treatment_reason=REASON_DEFERRED_SERVICE, vat_amount=7,
    )
    payment = _receipt(allocated=53.5)
    with (
        patch.object(receipt_vat.frappe, "get_doc", return_value=invoice),
        patch.object(receipt_vat, "get_service_tax_snapshot", return_value=snapshot),
        patch.object(receipt_vat, "get_company_registration", return_value=SimpleNamespace(is_registered=True)) as registration,
    ):
        values = receipt_vat.apply_service_receipt_vat(payment)

    registration.assert_called_once_with("Company", "2026-09-04")
    assert values == {
        "pd_custom_vat_amount": 3.5,
        "pd_custom_tax_invoice_number": "RV-1",
        "pd_custom_tax_invoice_date": "2026-09-04",
    }
    assert not payment.get("pd_custom_vat_ref")


def test_exempt_receipt_uses_receipt_number_and_date_with_zero_vat():
    payment = _receipt()
    snapshot = ServiceTaxSnapshot(classification=CLASSIFICATION_SERVICES, treatment=VAT_TREATMENT_EXEMPT)
    with (
        patch.object(receipt_vat, "_service_allocations", return_value=[(None, snapshot, 107, 107)]),
        patch.object(receipt_vat, "get_company_registration") as registration,
    ):
        assert receipt_vat.apply_service_receipt_vat(payment) == {
            "pd_custom_vat_amount": 0,
            "pd_custom_vat_treatment": VAT_TREATMENT_EXEMPT,
            "pd_custom_tax_invoice_number": "RV-1",
            "pd_custom_tax_invoice_date": "2026-09-04",
        }
    registration.assert_not_called()
    assert not payment.get("pd_custom_vat_ref")


def test_unconfirmed_seller_cannot_project_a_tax_invoice():
    payment = _receipt()
    snapshot = ServiceTaxSnapshot(
        treatment=VAT_TREATMENT_UNDUE, treatment_reason=REASON_DEFERRED_SERVICE, vat_amount=7,
    )
    with (
        patch.object(receipt_vat, "_service_allocations", return_value=[(None, snapshot, 107, 107)]),
        patch.object(receipt_vat, "get_company_registration", return_value=SimpleNamespace(is_registered=False)),
    ):
        assert receipt_vat.apply_service_receipt_vat(payment) == {"pd_custom_vat_amount": 0}


def test_taxable_report_requires_both_sides_of_the_existing_vat_transfer():
    payment = _receipt(docstatus=1)
    rows = [
        frappe._dict(account="VAT Due", debit=0, credit=7),
        frappe._dict(account="VAT Undue", debit=7, credit=0),
    ]
    with (
        patch.object(receipt_vat.frappe, "get_cached_value", return_value=frappe._dict(
            default_output_vat_account="VAT Due", default_output_vat_undue_account="VAT Undue",
        )),
        patch.object(receipt_vat.frappe, "get_all", side_effect=[rows, rows[:1]]) as query,
        patch.object(receipt_vat.frappe, "throw", side_effect=frappe.ValidationError),
    ):
        receipt_vat._verify_posted_output_vat(payment, 7)
        with pytest.raises(frappe.ValidationError):
            receipt_vat._verify_posted_output_vat(payment, 7)
    assert query.call_args.kwargs["filters"]["voucher_no"] == "RV-1"
