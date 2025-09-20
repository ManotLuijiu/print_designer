# Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PND1Form(Document):
	def before_save(self):
		"""Auto-populate WHT certificates and calculate totals before saving"""
		self.populate_wht_certificates()
		self.calculate_totals()

	def populate_wht_certificates(self):
		"""Automatically populate WHT certificates based on tax period and form type"""
		if not self.tax_period_year or not self.tax_period_month:
			return

		# Clear existing items first
		self.items = []

		# Format tax month to match WHT certificate format
		tax_month_formatted = f"{self.tax_period_month:02d}"

		# Get all WHT certificates and filter manually for complex matching
		all_certificates = frappe.get_all(
			"Withholding Tax Certificate",
			filters={
				"docstatus": 1,  # Only submitted certificates
				"status": "Issued",  # Only issued certificates
				"tax_year": self.tax_period_year,
				"pnd_form_type": "PND1 Form",  # Only PND1 type
			},
			fields=[
				"name", "supplier_name", "supplier_tax_id", "income_type", "tax_month",
				"income_description", "tax_base_amount", "wht_rate", "wht_amount",
				"custom_pnd_form", "supplier_type_classification"
			],
			order_by="certificate_date asc"
		)

		# Filter certificates that match this period and are eligible for PND1
		wht_certificates = []
		for cert in all_certificates:
			# Check if tax month matches
			cert_month = cert.tax_month
			if cert_month and (cert_month.startswith(tax_month_formatted) or cert_month == str(self.tax_period_month)):
				# Check if supplier classification is for individuals (PND1 target)
				classification = cert.supplier_type_classification or ""
				if any(keyword in classification for keyword in ["Individual", "Personal", "PND.1"]):
					# Allow certificates already assigned to THIS PND form or unassigned
					if not cert.custom_pnd_form or cert.custom_pnd_form == self.name:
						wht_certificates.append(cert)

		sequence = 1
		for cert in wht_certificates:
			# Add to PND1 Items child table
			self.append("items", {
				"sequence_number": sequence,
				"withholding_tax_cert": cert.name,
				"company_name": cert.supplier_name,
				"company_tax_id": cert.supplier_tax_id,
				"income_type": cert.income_type,
				"income_description": cert.income_description,
				"gross_amount": cert.tax_base_amount,
				"wht_rate": cert.wht_rate,
				"tax_amount": cert.wht_amount
			})
			sequence += 1

	def calculate_totals(self):
		"""Calculate summary totals from items"""
		self.total_certificates = len(self.items)
		self.total_gross_amount = sum(flt(item.gross_amount) for item in self.items)
		self.total_tax_amount = sum(flt(item.tax_amount) for item in self.items)

		# Calculate average tax rate
		if self.total_gross_amount > 0:
			self.average_tax_rate = (self.total_tax_amount / self.total_gross_amount) * 100
		else:
			self.average_tax_rate = 0

	def on_submit(self):
		"""Update WHT certificates to link them to this PND form"""
		for item in self.items:
			if item.withholding_tax_cert:
				frappe.db.set_value(
					"Withholding Tax Certificate",
					item.withholding_tax_cert,
					"custom_pnd_form",
					self.name
				)

		frappe.db.commit()

	def on_cancel(self):
		"""Remove PND form link from WHT certificates"""
		for item in self.items:
			if item.withholding_tax_cert:
				frappe.db.set_value(
					"Withholding Tax Certificate",
					item.withholding_tax_cert,
					"custom_pnd_form",
					""
				)

		frappe.db.commit()

	@frappe.whitelist()
	def refresh_certificates(self):
		"""Manual refresh of certificates (callable from frontend)"""
		self.populate_wht_certificates()
		self.calculate_totals()
		self.save()

		frappe.msgprint(f"Refreshed with {len(self.items)} WHT certificates for {self.tax_period_month}/{self.tax_period_year}")

		return {
			"total_certificates": self.total_certificates,
			"total_amount": self.total_tax_amount
		}
