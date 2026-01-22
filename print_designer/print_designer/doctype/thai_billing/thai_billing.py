# Copyright (c) 2025, Print Designer and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_days, nowdate
from frappe.utils import money_in_words

class ThaiBilling(Document):
	def validate(self):
		"""Validate Thai Billing document"""
		self.validate_dates()
		self.validate_customer()
		self.validate_invoice_items()
		self.calculate_totals()
		self.set_title()
		self.set_status()

	def before_save(self):
		"""Before save operations"""
		self.calculate_totals()

	def on_submit(self):
		"""On submit operations"""
		self.status = "Submitted"
		self.update_invoice_billing_status()

	def on_cancel(self):
		"""On cancel operations"""
		self.status = "Cancelled"
		self.clear_invoice_billing_status()

	def validate_dates(self):
		"""Validate date fields"""
		if self.billing_period_from and self.billing_period_to:
			if getdate(self.billing_period_from) > getdate(self.billing_period_to):
				frappe.throw(_("Billing Period From Date cannot be greater than To Date"))

		if self.posting_date and self.due_date:
			if getdate(self.posting_date) > getdate(self.due_date):
				frappe.throw(_("Posting Date cannot be greater than Due Date"))

	def validate_customer(self):
		"""Validate customer details"""
		if not self.customer:
			frappe.throw(_("Customer is required"))

		# Auto-fetch customer details
		if self.customer and not self.customer_name:
			customer_doc = frappe.get_doc("Customer", self.customer)
			self.customer_name = customer_doc.customer_name
			self.customer_tax_id = customer_doc.tax_id

	def validate_invoice_items(self):
		"""Validate invoice items"""
		if not self.invoice_items:
			frappe.throw(_("At least one invoice item is required"))

		# Validate each invoice item
		for item in self.invoice_items:
			if not item.sales_invoice:
				frappe.throw(_("Sales Invoice is required in row {0}").format(item.idx))

			# Check if invoice belongs to same customer
			invoice_customer = frappe.db.get_value("Sales Invoice", item.sales_invoice, "customer")
			if invoice_customer != self.customer:
				frappe.throw(_("Sales Invoice {0} does not belong to customer {1}").format(
					item.sales_invoice, self.customer_name))

			# Check if invoice is already included in another billing
			existing_billing = frappe.db.sql("""
				SELECT parent FROM `tabThai Billing Item`
				WHERE sales_invoice = %s AND parent != %s AND docstatus != 2
			""", (item.sales_invoice, self.name))

			if existing_billing:
				frappe.throw(_("Sales Invoice {0} is already included in Thai Billing {1}").format(
					item.sales_invoice, existing_billing[0][0]))

	def calculate_totals(self):
		"""Calculate totals from invoice items including payment status"""
		total_invoices = 0
		total_amount = 0.0
		total_outstanding = 0.0

		for item in self.invoice_items:
			if item.sales_invoice:
				# Fetch fresh values from Sales Invoice
				invoice_data = frappe.db.get_value(
					"Sales Invoice",
					item.sales_invoice,
					["grand_total", "outstanding_amount"],
					as_dict=True
				)
				if invoice_data:
					item.invoice_amount = flt(invoice_data.grand_total)
					item.outstanding_amount = flt(invoice_data.outstanding_amount)

					total_invoices += 1
					total_amount += flt(item.invoice_amount)
					total_outstanding += flt(item.outstanding_amount)

		self.total_invoices = total_invoices
		self.total_amount = total_amount
		self.grand_total = total_amount
		self.total_paid = flt(total_amount) - flt(total_outstanding)
		self.total_outstanding = total_outstanding

		# Auto-calculate grand_total_in_words
		self.set_grand_total_in_words()

	def set_grand_total_in_words(self):
		"""Set grand total in words with automatic language detection"""
		if self.grand_total:
			try:
				# Use standard Frappe money_in_words function
				# This will be enhanced by Print Designer's Thai conversion in print formats
				currency = frappe.get_cached_value("Company", self.company, "default_currency") if self.company else "THB"
				self.grand_total_in_words = money_in_words(self.grand_total, currency)
			except Exception:
				# Fallback to basic conversion
				self.grand_total_in_words = money_in_words(self.grand_total)
		else:
			self.grand_total_in_words = ""

	def set_title(self):
		"""Set document title for better identification"""
		if self.customer_name and self.posting_date:
			self.title = f"{self.customer_name} - {self.posting_date}"

	def set_status(self, update=False):
		"""Set document status based on submission and payment status"""
		if self.docstatus == 2:
			self.status = "Cancelled"
		elif self.docstatus == 1:
			# Check payment status first
			if flt(self.total_outstanding) <= 0:
				self.status = "Paid"
			elif flt(self.total_paid) > 0:
				self.status = "Partially Paid"
			# Check if overdue (only for unpaid/partially paid)
			elif self.due_date and getdate(self.due_date) < getdate(nowdate()):
				self.status = "Overdue"
			else:
				self.status = "Submitted"
		else:
			self.status = "Draft"

		if update:
			self.db_set("status", self.status)
			self.db_set("total_paid", self.total_paid)
			self.db_set("total_outstanding", self.total_outstanding)

	def update_status(self):
		"""Update status based on linked invoices - can be called externally"""
		self.calculate_totals()
		self.set_status(update=True)

	def update_invoice_billing_status(self):
		"""Update Sales Invoice billing status when submitted"""
		# Simplified - no custom fields needed
		# Business logic: billing status tracked through Thai Billing Item relationship
		pass

	def clear_invoice_billing_status(self):
		"""Clear Sales Invoice billing status when cancelled"""
		# Simplified - no custom fields needed
		# Business logic: billing status tracked through Thai Billing Item relationship
		pass

	@frappe.whitelist()
	def get_pending_invoices(self):
		"""Get pending invoices for the customer"""
		if not self.customer:
			return []

		# Build filters - simplified to show all outstanding invoices by default
		filters = {
			"customer": self.customer,
			"docstatus": 1,
			"outstanding_amount": [">", 0]
		}

		# Add date filters if specified
		if self.billing_period_from:
			filters["posting_date"] = [">=", self.billing_period_from]
		if self.billing_period_to:
			filters["posting_date"] = ["<=", self.billing_period_to]

		# Get pending invoices
		invoices = frappe.get_all("Sales Invoice",
			filters=filters,
			fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount", "remarks"]
		)

		return invoices

	@frappe.whitelist()
	def add_pending_invoices(self):
		"""Add all pending invoices to the billing"""
		pending_invoices = self.get_pending_invoices()

		# Clear existing items
		self.invoice_items = []

		# Add pending invoices
		for invoice in pending_invoices:
			self.append("invoice_items", {
				"sales_invoice": invoice.name,
				"invoice_date": invoice.posting_date,
				"due_date": invoice.due_date,
				"invoice_amount": invoice.grand_total,
				"outstanding_amount": invoice.outstanding_amount,
				"invoice_description": invoice.project or "Credit Sales"
			})

		# Recalculate totals
		self.calculate_totals()

		frappe.msgprint(_("Added {0} pending invoices").format(len(pending_invoices)))

# API methods for external access
@frappe.whitelist()
def get_customer_billing_summary(customer, from_date=None, to_date=None):
	"""Get billing summary for a customer"""
	filters = {"customer": customer, "docstatus": ["!=", 2]}

	if from_date:
		filters["posting_date"] = [">=", from_date]
	if to_date:
		filters["posting_date"] = ["<=", to_date]

	billings = frappe.get_all("Thai Billing",
		filters=filters,
		fields=["name", "posting_date", "due_date", "total_amount", "status"]
	)

	return billings

@frappe.whitelist()
def create_billing_from_invoices(customer, invoice_list, due_date=None):
	"""Create Thai Billing from a list of invoices"""
	if isinstance(invoice_list, str):
		import json
		invoice_list = json.loads(invoice_list)

	if not due_date:
		due_date = add_days(getdate(), 30)  # Default 30 days

	# Create new billing document
	billing = frappe.new_doc("Thai Billing")
	billing.customer = customer
	billing.due_date = due_date
	billing.posting_date = getdate()

	# Add invoices
	for invoice_name in invoice_list:
		invoice = frappe.get_doc("Sales Invoice", invoice_name)
		billing.append("invoice_items", {
			"sales_invoice": invoice.name,
			"invoice_date": invoice.posting_date,
			"due_date": invoice.due_date,
			"invoice_amount": invoice.grand_total,
			"outstanding_amount": invoice.outstanding_amount,
			"invoice_description": invoice.project or "Credit Sales"
		})

	billing.save()

	return billing.name

@frappe.whitelist()
def make_payment_entry(source_name, target_doc=None):
	"""Create Payment Entry from Thai Billing"""
	billing = frappe.get_doc("Thai Billing", source_name)

	if billing.status in ("Paid", "Cancelled"):
		frappe.throw(_("Cannot create payment for {0} Thai Billing").format(billing.status))

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.party_type = "Customer"
	pe.party = billing.customer
	pe.party_name = billing.customer_name
	pe.company = billing.company
	pe.posting_date = nowdate()
	pe.paid_amount = billing.total_outstanding
	pe.received_amount = billing.total_outstanding
	pe.custom_thai_billing = billing.name

	# Add references for each outstanding invoice
	for item in billing.invoice_items:
		if flt(item.outstanding_amount) > 0:
			pe.append(
				"references",
				{
					"reference_doctype": "Sales Invoice",
					"reference_name": item.sales_invoice,
					"allocated_amount": item.outstanding_amount,
				},
			)

	return pe


def update_thai_billing_on_payment(doc, method):
	"""
	Hook to update Thai Billing status when a Payment Entry is submitted/cancelled.
	Called via doc_events in hooks.py.
	"""
	# Check if this payment is linked to a Thai Billing
	thai_billing_name = doc.get("custom_thai_billing")
	if not thai_billing_name:
		return

	# Verify Thai Billing exists and is submitted
	if not frappe.db.exists("Thai Billing", thai_billing_name):
		return

	billing = frappe.get_doc("Thai Billing", thai_billing_name)
	if billing.docstatus != 1:
		return

	# Update billing totals and status
	billing.update_status()


# Jinja Methods for Print Formats
@frappe.whitelist()
def get_thai_billing_amount_in_words(doc_name, field_name="grand_total"):
	"""
	Get Thai Billing amount in words for print formats with Thai language support.

	Usage in Jinja templates:
	{{ get_thai_billing_amount_in_words(doc.name, "grand_total") }}

	Args:
		doc_name: Thai Billing document name
		field_name: Field name to convert (default: grand_total)

	Returns:
		str: Amount in words (Thai if Thai language detected, English otherwise)
	"""
	try:
		# Import Thai word conversion utility
		from print_designer.utils.thai_amount_to_word import smart_money_in_words

		# Get the document
		doc = frappe.get_doc("Thai Billing", doc_name)
		amount = getattr(doc, field_name, 0)

		if not amount:
			return ""

		# Use smart conversion that auto-detects Thai language context
		return smart_money_in_words(amount, doc.get("currency", "THB"))

	except Exception as e:
		frappe.log_error(f"Error in get_thai_billing_amount_in_words: {str(e)}")
		# Fallback to standard conversion
		try:
			doc = frappe.get_doc("Thai Billing", doc_name)
			amount = getattr(doc, field_name, 0)
			return money_in_words(amount) if amount else ""
		except:
			return ""
