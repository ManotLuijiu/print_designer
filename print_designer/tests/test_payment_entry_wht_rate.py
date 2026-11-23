from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import frappe

from print_designer.custom import payment_entry_wht_rate as wht


def _receipt(**values):
    payment = {
        "payment_type": "Receive",
        "party_type": "Customer",
        "references": [
            SimpleNamespace(reference_doctype="Sales Invoice", reference_name="SI-1", allocated_amount=100)
        ],
        **values,
    }
    return SimpleNamespace(
        get=payment.get,
        meta=Mock(),
        set=Mock(),
        company="Company",
        party="Customer",
    )


def test_receipt_uses_rate_stored_on_sales_invoice():
    payment = _receipt()
    with patch.object(wht, "frappe") as api:
        field = SimpleNamespace(fieldtype="Link", options="Tax Withholding Category")
        payment.meta.get_field.return_value = field
        api.get_meta.return_value.get_field.return_value = field
        api.get_all.return_value = [frappe._dict(
            pd_custom_withholding_tax_pct=3, pd_custom_wht_income_type="Service Fees 3% (PND53)"
        )]
        assert wht.apply_sales_invoice_wht_details(payment) == 3
        assert api.get_all.call_args.kwargs["fields"] == ["pd_custom_withholding_tax_pct", "pd_custom_wht_income_type"]
        assert api.get_all.call_args.kwargs["filters"]["name"] == ["in", ["SI-1"]]

    assert payment.set.call_args_list == [
        call("pd_custom_withholding_tax_pct_details", 3),
        call("pd_custom_wht_income_type", "Service Fees 3% (PND53)"),
    ]


def test_multiple_distinct_rates_do_not_pick_an_arbitrary_invoice():
    payment = _receipt()
    with patch.object(wht, "frappe") as api:
        api.get_all.return_value = [frappe._dict(pd_custom_withholding_tax_pct=rate) for rate in (1, 3)]
        assert wht.apply_sales_invoice_wht_details(payment) == 0

    payment.set.assert_called_once_with("pd_custom_withholding_tax_pct_details", 0)


def test_supplier_payment_does_not_use_sales_invoice_rate():
    payment = _receipt(payment_type="Pay")
    with patch.object(wht, "frappe") as api:
        assert wht.apply_sales_invoice_wht_details(payment) is None
        api.get_all.assert_not_called()
    payment.set.assert_not_called()
