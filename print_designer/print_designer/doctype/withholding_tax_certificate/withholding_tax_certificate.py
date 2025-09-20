# Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class WithholdingTaxCertificate(Document):
	def after_insert(self):
		"""Auto-create PND form item entry when certificate is created"""
		self.create_or_update_pnd_form_item()

	def on_submit(self):
		"""Update PND form item when certificate is submitted"""
		self.create_or_update_pnd_form_item(update_only=True)

	def on_cancel(self):
		"""Remove PND form item when certificate is cancelled"""
		self.remove_pnd_form_item()

	def create_or_update_pnd_form_item(self, update_only=False):
		"""
		Create or update appropriate PND Items child table entry based on PND form type.
		This enables accounting automation where PND forms are pre-populated and ready for review.
		"""
		if not self.pnd_form_type:
			return

		# Determine the PND form and items doctype based on form type
		pnd_form_mapping = {
			"PND1 Form": ("PND1 Form", "PND1 Items"),
			"PND3 Form": ("PND3 Form", "PND3 Items"),
			"PND53 Form": ("PND53 Form", "PND53 Items"),
			"PND54 Form": ("PND54 Form", "PND54 Items")
		}

		if self.pnd_form_type not in pnd_form_mapping:
			frappe.log_error(f"Unknown PND form type: {self.pnd_form_type}", "WHT Certificate")
			return

		pnd_form_doctype, pnd_items_doctype = pnd_form_mapping[self.pnd_form_type]

		# Get or create the PND form for this tax period
		pnd_form = self.get_or_create_pnd_form(pnd_form_doctype)
		if not pnd_form:
			return

		# Check if item already exists
		existing_item = frappe.db.exists(pnd_items_doctype, {
			"parent": pnd_form.name,
			"withholding_tax_cert": self.name
		})

		if existing_item and not update_only:
			return  # Item already exists, no need to recreate

		if existing_item and update_only:
			# Update existing item
			self.update_pnd_item(pnd_items_doctype, existing_item)
		elif not update_only:
			# Create new item
			self.create_pnd_item(pnd_form, pnd_items_doctype)

	def get_or_create_pnd_form(self, pnd_form_doctype):
		"""Get existing PND form for the tax period or create a new one in draft"""
		# Extract year and month from tax fields
		tax_year = self.tax_year
		tax_month = self.tax_month.split(" - ")[0] if self.tax_month else None

		# Remove leading zero from month (convert "09" to "9")
		if tax_month:
			tax_month = str(int(tax_month))

		if not tax_year or not tax_month:
			frappe.log_error(f"Missing tax period for WHT Certificate {self.name}", "WHT Certificate")
			return None

		# Check if PND form already exists for this period
		existing_forms = frappe.get_all(
			pnd_form_doctype,
			filters={
				"tax_period_year": tax_year,
				"tax_period_month": tax_month,
				"docstatus": 0  # Draft only
			},
			limit=1
		)

		if existing_forms:
			return frappe.get_doc(pnd_form_doctype, existing_forms[0].name)

		# Create new PND form in draft
		pnd_form = frappe.new_doc(pnd_form_doctype)
		pnd_form.tax_period_year = tax_year
		pnd_form.tax_period_month = tax_month
		pnd_form.company = self.company
		pnd_form.submission_status = "Draft"

		# Set form-specific fields
		if pnd_form_doctype == "PND53 Form":
			pnd_form.form_number = f"PND53-{tax_year}-{tax_month}-DRAFT"
		elif pnd_form_doctype == "PND3 Form":
			pnd_form.form_number = f"PND3-{tax_year}-{tax_month}-DRAFT"
		elif pnd_form_doctype == "PND1 Form":
			pnd_form.form_number = f"PND1-{tax_year}-{tax_month}-DRAFT"
		elif pnd_form_doctype == "PND54 Form":
			pnd_form.form_number = f"PND54-{tax_year}-{tax_month}-DRAFT"

		pnd_form.insert(ignore_permissions=True)

		frappe.msgprint(
			f"Created draft {pnd_form_doctype} for period {tax_month}/{tax_year}",
			alert=True,
			indicator="blue"
		)

		return pnd_form

	def create_pnd_item(self, pnd_form, pnd_items_doctype):
		"""Create new PND item entry"""
		# Get the next sequence number
		existing_items = frappe.get_all(
			pnd_items_doctype,
			filters={"parent": pnd_form.name},
			fields=["sequence_number"],
			order_by="sequence_number desc",
			limit=1
		)

		next_sequence = 1
		if existing_items:
			next_sequence = (existing_items[0].sequence_number or 0) + 1

		# Create the item
		pnd_item = frappe.new_doc(pnd_items_doctype)
		pnd_item.parent = pnd_form.name
		pnd_item.parenttype = pnd_form.doctype
		pnd_item.parentfield = "items"
		pnd_item.sequence_number = next_sequence
		pnd_item.withholding_tax_cert = self.name

		# Set common fields based on the specific PND Items doctype
		if pnd_items_doctype == "PND53 Items":
			pnd_item.company_name = self.supplier_name
			pnd_item.company_tax_id = self.supplier_tax_id
		elif pnd_items_doctype == "PND3 Items":
			# PND3 uses supplier_name field
			pnd_item.supplier_name = self.supplier_name
			pnd_item.supplier_tax_id = self.supplier_tax_id
		else:
			# For PND1, PND54 - check their field names
			# Using supplier_name as default fallback
			if hasattr(pnd_item, 'person_name'):
				pnd_item.person_name = self.supplier_name
				pnd_item.person_tax_id = self.supplier_tax_id
			else:
				pnd_item.supplier_name = self.supplier_name
				pnd_item.supplier_tax_id = self.supplier_tax_id

		pnd_item.income_type = self.income_type
		pnd_item.income_description = self.income_description
		pnd_item.gross_amount = self.tax_base_amount
		pnd_item.wht_rate = self.wht_rate
		pnd_item.tax_amount = self.wht_amount

		pnd_item.insert(ignore_permissions=True)

		# Update PND form totals
		pnd_form.reload()
		if hasattr(pnd_form, 'calculate_totals'):
			pnd_form.calculate_totals()
			pnd_form.save(ignore_permissions=True)

		# Link this certificate to the PND form
		self.custom_pnd_form = pnd_form.name
		self.save(ignore_permissions=True)

		frappe.msgprint(
			f"Added WHT Certificate to {pnd_form.doctype} items",
			alert=True,
			indicator="green"
		)

	def update_pnd_item(self, pnd_items_doctype, item_name):
		"""Update existing PND item with latest certificate data"""
		pnd_item = frappe.get_doc(pnd_items_doctype, item_name)

		# Update amounts and rates
		pnd_item.gross_amount = self.tax_base_amount
		pnd_item.wht_rate = self.wht_rate
		pnd_item.tax_amount = self.wht_amount
		pnd_item.income_type = self.income_type
		pnd_item.income_description = self.income_description

		pnd_item.save(ignore_permissions=True)

		# Update parent form totals
		parent_form = frappe.get_doc(pnd_item.parenttype, pnd_item.parent)
		if hasattr(parent_form, 'calculate_totals'):
			parent_form.calculate_totals()
			parent_form.save(ignore_permissions=True)

	def remove_pnd_form_item(self):
		"""Remove PND form item when certificate is cancelled"""
		if not self.custom_pnd_form or not self.pnd_form_type:
			return

		pnd_form_mapping = {
			"PND1 Form": "PND1 Items",
			"PND3 Form": "PND3 Items",
			"PND53 Form": "PND53 Items",
			"PND54 Form": "PND54 Items"
		}

		if self.pnd_form_type not in pnd_form_mapping:
			return

		pnd_items_doctype = pnd_form_mapping[self.pnd_form_type]

		# Find and delete the item
		items_to_delete = frappe.get_all(
			pnd_items_doctype,
			filters={
				"withholding_tax_cert": self.name
			}
		)

		for item in items_to_delete:
			frappe.delete_doc(pnd_items_doctype, item.name, ignore_permissions=True)

		# Clear the PND form link
		self.custom_pnd_form = ""
		self.save(ignore_permissions=True)

		frappe.msgprint(
			f"Removed WHT Certificate from PND form items",
			alert=True,
			indicator="orange"
		)
