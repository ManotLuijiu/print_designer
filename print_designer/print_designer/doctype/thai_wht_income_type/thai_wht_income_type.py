# Copyright (c) 2026, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ThaiWHTIncomeType(Document):
	def autoname(self):
		# Doc name format: {income_category} {recipient_type} {tax_rate} {form_type}
		# Example: "Advertising Income Corporation 2 PND53"
		# All English, space-separated, no special characters
		tax_rate = str(self.tax_rate) if self.tax_rate else "0"
		self.name = f"{self.income_category} {self.recipient_type} {tax_rate} {self.form_type}"
