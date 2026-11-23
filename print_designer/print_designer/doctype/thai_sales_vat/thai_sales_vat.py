# Copyright (c) 2026, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.model.rename_doc import rename_doc


class ThaiSalesVAT(Document):
    def autoname(self):
        if self.payment_entry_reference:
            self.name = self.receipt_record_name()

    def receipt_record_name(self):
        return f"THVAT-PE-{self.payment_entry_reference}"

    def rename_for_receipt(self):
        """Use the receipt series for an existing unreported payment VAT row."""
        name = self.receipt_record_name()
        if self.name == name or self.is_output_vat_reported:
            return self.name
        return rename_doc(
            doc=self, new=name, force=True, ignore_permissions=True,
            show_alert=False, rebuild_search=False,
        )

    def validate(self):
        """Keep the receipt snapshot after Frappe fetches the invoice totals."""
        amounts = self.flags.get("service_receipt_amounts")
        previous = self.get_doc_before_save()
        if not amounts and previous and previous.payment_entry_reference and (
            previous.payment_entry_reference == self.payment_entry_reference
        ):
            amounts = {field: previous.get(field) for field in ("base_amount", "vat_amount", "total_amount")}
        if amounts:
            self.update(amounts)
