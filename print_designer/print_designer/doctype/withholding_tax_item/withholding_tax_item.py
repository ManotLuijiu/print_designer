# Copyright (c) 2026, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class WithholdingTaxItem(Document):
	def validate(self):
		self.calculate_amounts()

	def calculate_amounts(self):
		gross = flt(self.gross_amount)
		rate = flt(self.tax_rate)
		self.tax_amount = flt(gross * rate / 100, self.precision("tax_amount"))
		self.net_amount = flt(gross - self.tax_amount, self.precision("net_amount"))
