# Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CompanyStamp(Document):
	def validate(self):
		"""Validate company stamp settings."""
		self.validate_unique_stamp_per_company()
		self.set_default_title()
	
	def validate_unique_stamp_per_company(self):
		"""Ensure unique stamp type per company (if needed)."""
		if self.stamp_type and self.company:
			# Check for duplicate active stamps of same type for same company
			existing = frappe.db.exists("Company Stamp", {
				"company": self.company,
				"stamp_type": self.stamp_type,
				"is_active": 1,
				"name": ["!=", self.name]
			})
			
			if existing:
				frappe.msgprint(
					frappe._("An active {0} stamp already exists for {1}. Consider deactivating the existing one or using a different stamp type.").format(
						self.stamp_type, self.company
					),
					alert=True,
					indicator="orange"
				)
	
	def set_default_title(self):
		"""Set default title if not provided."""
		if not self.title and self.company:
			company_name = frappe.db.get_value("Company", self.company, "company_name")
			stamp_type = self.stamp_type or "Official"
			self.title = f"{company_name} - {stamp_type} Stamp"
	
	def get_company_stamps(self, company=None):
		"""Get all active stamps for a company."""
		if not company:
			company = self.company
			
		return frappe.get_all("Company Stamp", 
			filters={
				"company": company,
				"is_active": 1
			},
			fields=["name", "title", "stamp_type", "stamp_image", "usage_purpose"]
		)
