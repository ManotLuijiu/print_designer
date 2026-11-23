from unittest import TestCase
from unittest.mock import Mock, patch

import frappe

from print_designer.commands.install_payment_entry_fields import (
    get_payment_entry_custom_fields_definition,
    migrate_wht_certificate_link,
)
from print_designer.custom import payment_vat_link as vat_link


class TestPaymentVatLink(TestCase):
    def payment(self, payment_type, docstatus=1, **fields):
        doc = frappe._dict(name="PAY-1", payment_type=payment_type, docstatus=docstatus, **fields)
        doc.meta = Mock()
        doc.meta.has_field.return_value = True
        return doc

    def test_pay_links_the_only_uncancelled_purchase_record(self):
        payment = self.payment("Pay")
        with patch.object(vat_link, "frappe") as api:
            api.db.exists.return_value = True
            api.get_all.return_value = [
                frappe._dict(name="P-VAT-1", workflow_state="Draft"),
                frappe._dict(name="P-VAT-2", workflow_state="Cancelled"),
            ]
            vat_link.sync_payment_vat_link(payment)

        self.assertEqual(payment.pd_custom_vat_ref_doctype, "Thai Purchase VAT")
        self.assertEqual(payment.pd_custom_vat_ref, "P-VAT-1")
        self.assertEqual(api.get_all.call_args.kwargs["filters"]["payment_entry"], "PAY-1")

    def test_recognized_sales_record_is_linked_then_cleared_when_reversed(self):
        payment = self.payment("Receive")
        with patch.object(vat_link, "frappe") as api:
            api.db.exists.return_value = True
            api.get_all.return_value = ["S-VAT-1"]
            vat_link.sync_payment_vat_link(payment)
            self.assertEqual(payment.pd_custom_vat_ref_doctype, "Thai Sales VAT")
            self.assertEqual(payment.pd_custom_vat_ref, "S-VAT-1")
            self.assertEqual(api.get_all.call_args.kwargs["filters"]["vat_type"], "VAT Due")
            self.assertEqual(api.get_all.call_args.kwargs["filters"]["payment_entry_reference"], "PAY-1")

            api.get_all.return_value = []
            vat_link.sync_payment_vat_link(payment)
            self.assertIsNone(payment.pd_custom_vat_ref_doctype)
            self.assertIsNone(payment.pd_custom_vat_ref)

    def test_multiple_records_are_not_reduced_to_an_arbitrary_link(self):
        self.assertEqual(vat_link.get_payment_vat_link_values("Receive", ["A", "A"])["pd_custom_vat_ref"], "A")
        self.assertEqual(
            vat_link.get_payment_vat_link_values("Receive", ["A", "B"]),
            {"pd_custom_vat_ref_doctype": None, "pd_custom_vat_ref": None},
        )

    def test_payment_uses_the_consolidated_vat_treatment_field(self):
        payment = self.payment("Pay", pd_custom_vat_treatment="VAT Undue")
        self.assertEqual(vat_link.get_payment_vat_treatment(payment), "VAT Undue")

    def test_cancelled_payment_clears_the_pair(self):
        payment = self.payment(
            "Pay", docstatus=2, pd_custom_vat_ref_doctype="Thai Purchase VAT", pd_custom_vat_ref="A"
        )
        with patch.object(vat_link, "frappe") as api:
            vat_link.sync_payment_vat_link(payment)
            api.get_all.assert_not_called()
        self.assertIsNone(payment.pd_custom_vat_ref)

    def test_old_site_without_vat_link_pair_skips_the_write(self):
        payment = self.payment("Pay")
        payment.meta.has_field.return_value = False
        with patch.object(vat_link, "frappe") as api:
            vat_link.sync_payment_vat_link(payment)
            api.db.set_value.assert_not_called()

    def test_existing_wht_link_uses_a_narrow_metadata_migration(self):
        module = "print_designer.commands.install_payment_entry_fields"
        fields = get_payment_entry_custom_fields_definition()["Payment Entry"]
        with patch(module + ".frappe") as api, patch(module + ".create_custom_fields") as create:
            api.db.get_value.return_value = "Link"
            api.get_all.return_value = ["PAY-1"]
            migrate_wht_certificate_link(fields)
            create.assert_called_once()
            self.assertEqual(
                [field["fieldname"] for field in create.call_args.args[0]["Payment Entry"]],
                ["pd_custom_wht_certificate_doctype", "pd_custom_wht_certificate"],
            )
            api.db.set_value.assert_called_once_with(
                "Payment Entry", "PAY-1", "pd_custom_wht_certificate_doctype",
                "Withholding Tax Certificate", update_modified=False,
            )
