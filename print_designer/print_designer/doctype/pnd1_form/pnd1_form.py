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

	def autoname(self):
		"""Custom naming using YYMM-NNNNN pattern with monthly reset"""
		if self.tax_period_month and self.tax_period_year:
			# Convert Buddhist year to 2-digit format (e.g., 2568 -> 68)
			yy = str(self.tax_period_year)[-2:]
			# Zero-pad month (e.g., 9 -> 09)
			mm = str(self.tax_period_month).zfill(2)
			# Create YYMM period identifier
			period = f"{yy}{mm}"

			# Generate sequential number with monthly reset
			from frappe.model.naming import make_autoname
			self.name = make_autoname(f"PND1-{period}-.#####.")

	def populate_wht_certificates(self):
		"""Populate PND1 Items from Employee Tax Ledger entries for the specified month"""
		if not self.tax_period_year or not self.tax_period_month:
			return

		# Clear existing items first
		self.items = []

		# Convert Buddhist year to Christian year for month filtering
		christian_year = int(self.tax_period_year) - 543

		# Build month filter string (format: "MM - MonthName")
		month_filter = f"{str(self.tax_period_month).zfill(2)} - {self._get_month_name(self.tax_period_month)}"

		# Get ALL Employee Tax Ledger entries for the specified period
		# This includes employees with ฿0 income tax (as per requirement)
		ledger_entries = frappe.get_all(
			"Employee Tax Ledger Entry",
			filters={
				"year": str(christian_year),
				"month": month_filter
			},
			fields=[
				"parent", "salary_slip", "posting_date", "month", "year",
				"gross_salary", "income_tax_amount", "social_security",
				"provident_fund", "net_pay"
			],
			order_by="posting_date asc"
		)

		# Group entries by employee (parent Employee Tax Ledger)
		employee_data = {}
		for entry in ledger_entries:
			# Get employee details from the parent Employee Tax Ledger
			if entry.parent not in employee_data:
				ledger = frappe.get_doc("Employee Tax Ledger", entry.parent)
				employee_data[entry.parent] = {
					"employee": ledger.employee,
					"employee_name": ledger.employee_name,
					"employee_tax_id": ledger.employee_tax_id or "",
					"total_gross": 0,
					"total_tax": 0,
					"entries_count": 0,
					"employment_type": self._get_employee_employment_type(ledger.employee)
				}

			# Accumulate totals for this employee
			emp_data = employee_data[entry.parent]
			emp_data["total_gross"] += flt(entry.gross_salary)
			emp_data["total_tax"] += flt(entry.income_tax_amount)
			emp_data["entries_count"] += 1

		# Add all employees to PND1 Items (including those with ฿0 tax)
		sequence = 1
		for emp_data in employee_data.values():
			# Calculate WHT rate
			wht_rate = 0
			if emp_data["total_gross"] > 0:
				wht_rate = (emp_data["total_tax"] / emp_data["total_gross"]) * 100

			# Determine income type based on employment type
			income_type = self._determine_income_type(emp_data["employment_type"])
			income_description = f"เงินเดือนประจำเดือน {self._get_thai_month_name(self.tax_period_month)} {self.tax_period_year}"

			self.append("items", {
				"sequence_number": sequence,
				"withholding_tax_cert": "",  # Optional field for PND1
				"employee_name": emp_data["employee_name"],
				"employee_tax_id": emp_data["employee_tax_id"],
				"income_type": income_type,
				"income_description": income_description,
				"gross_amount": emp_data["total_gross"],
				"wht_rate": wht_rate,
				"tax_amount": emp_data["total_tax"]
			})
			sequence += 1

	def _get_employee_employment_type(self, employee):
		"""Get employee employment type"""
		try:
			emp_doc = frappe.get_doc("Employee", employee)
			return getattr(emp_doc, 'employment_type', 'Permanent')
		except:
			return 'Permanent'

	def _get_month_name(self, month_num):
		"""Get English month name"""
		month_names = {
			1: "January", 2: "February", 3: "March", 4: "April",
			5: "May", 6: "June", 7: "July", 8: "August",
			9: "September", 10: "October", 11: "November", 12: "December"
		}
		return month_names.get(int(month_num), "")

	def _get_thai_month_name(self, month_num):
		"""Get Thai month name"""
		thai_months = {
			1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
			5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
			9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"
		}
		return thai_months.get(int(month_num), "")

	def _determine_income_type(self, employment_type):
		"""Determine income type based on employee employment type"""
		if employment_type == "Contract":
			return "2. เงินได้ตามมาตรา 40 (2) - Fee/Commission"
		else:
			return "1. เงินได้ตามมาตรา 40 (1) เงินเดือน ค่าจ้าง ฯลฯ - Salary"

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
		"""PND1 Form submission - no certificate linking required"""
		# PND1 is independent of WHT Certificate status
		# Just commit the form submission
		frappe.db.commit()

	def on_cancel(self):
		"""PND1 Form cancellation - no certificate unlinking required"""
		# PND1 is independent of WHT Certificate status
		# Just commit the form cancellation
		frappe.db.commit()

	@frappe.whitelist()
	def refresh_employee_data(self):
		"""Manual refresh of employee data from Tax Ledger (callable from frontend)"""
		self.populate_wht_certificates()
		self.calculate_totals()
		self.save()

		frappe.msgprint(f"Refreshed with {len(self.items)} employees for {self.tax_period_month}/{self.tax_period_year}")

		return {
			"total_employees": self.total_certificates,  # Field name kept for compatibility
			"total_amount": self.total_tax_amount
		}
