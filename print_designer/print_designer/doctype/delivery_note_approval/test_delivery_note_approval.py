# Copyright (c) 2024, Frappe Technologies Pvt Ltd. and Contributors
# See license.txt

import unittest

import frappe
from frappe.utils import add_days, now_datetime


class TestDeliveryNoteApproval(unittest.TestCase):
	"""Test cases for Delivery Note Approval DocType"""

	def setUp(self):
		"""Set up test data"""
		self.delivery_note = None
		self.delivery_note = self.create_test_delivery_note()

	def get_test_data(self):
		"""Return the site data the test needs.

		Returns a tuple (company, customer, item) or None when the site has
		no usable record.
		"""
		company = frappe.defaults.get_defaults().get("company") or frappe.db.get_value(
			"Company", {}, "name"
		)
		customer = frappe.db.get_value("Customer", {"disabled": 0}, "name")
		item = frappe.db.get_value("Item", {"is_stock_item": 0, "disabled": 0}, "name")

		if not (company and customer and item):
			return None

		return company, customer, item

	def create_test_delivery_note(self):
		"""Create a test delivery note for testing"""
		test_data = self.get_test_data()
		if not test_data:
			self.skipTest("No company, customer or non stock item available on this site")

		company, customer, item = test_data

		delivery_note = frappe.get_doc({
			"doctype": "Delivery Note",
			"customer": customer,
			"company": company,
			"posting_date": frappe.utils.today(),
			"items": [{
				"item_code": item,
				"qty": 1,
				"rate": 100
			}]
		})
		delivery_note.insert(ignore_permissions=True)
		return delivery_note

	def get_approval(self, **kwargs):
		"""Create a pending approval for the test delivery note"""
		approval = frappe.get_doc({
			"doctype": "Delivery Note Approval",
			"delivery_note": self.delivery_note.name,
			"customer_mobile": "+66123456789",
			"status": "Pending"
		})
		for key, value in kwargs.items():
			approval.set(key, value)
		approval.insert(ignore_permissions=True)
		return approval

	def test_approval_creation(self):
		"""Test creating a delivery note approval record"""
		approval = self.get_approval()

		# Check that approval token was generated
		self.assertTrue(approval.approval_token)

		# Check that generated_on was set
		self.assertTrue(approval.generated_on)

		# Test approval URL generation
		approval_url = approval.get_approval_url()
		self.assertIn(approval.approval_token, approval_url)

		# Cleanup
		approval.delete(ignore_permissions=True)

	def test_approval_process(self):
		"""Test the approval process"""
		approval = self.get_approval()

		# Test approval
		result = approval.approve_delivery(
			customer_name="Test Customer",
			digital_signature="test_signature_data",
			remarks="Goods received in good condition"
		)

		self.assertEqual(result["status"], "success")
		self.assertEqual(approval.status, "Approved")
		self.assertEqual(approval.customer_name, "Test Customer")
		self.assertTrue(approval.approved_on)

		# Cleanup
		approval.delete(ignore_permissions=True)

	def test_rejection_process(self):
		"""Test the rejection process"""
		approval = self.get_approval()

		# Test rejection
		result = approval.reject_delivery(
			customer_name="Test Customer",
			remarks="Goods were damaged"
		)

		self.assertEqual(result["status"], "success")
		self.assertEqual(approval.status, "Rejected")
		self.assertEqual(approval.customer_name, "Test Customer")
		self.assertEqual(approval.remarks, "Goods were damaged")

		# Cleanup
		approval.delete(ignore_permissions=True)

	def test_expiry_check(self):
		"""Test approval expiry functionality"""
		approval = self.get_approval()
		approval.generated_on = add_days(now_datetime(), -8)  # 8 days ago
		approval.save(ignore_permissions=True)

		# Test that approval is expired
		self.assertTrue(approval.is_expired())

		# Test that expired approval cannot be approved
		with self.assertRaises(frappe.ValidationError):
			approval.approve_delivery("Test Customer")

		# Cleanup
		approval.delete(ignore_permissions=True)

	def test_guest_api_functions(self):
		"""Test guest API functions"""
		approval = self.get_approval()

		# Test get_approval_details
		from print_designer.print_designer.doctype.delivery_note_approval.delivery_note_approval import (
			get_approval_details,
		)

		details = get_approval_details(approval.approval_token)
		self.assertTrue(details.get("success"))
		self.assertEqual(details["approval"]["delivery_note"], self.delivery_note.name)

		# Test submit_approval_decision
		from print_designer.print_designer.doctype.delivery_note_approval.delivery_note_approval import (
			submit_approval_decision,
		)

		result = submit_approval_decision(
			approval.approval_token,
			"approve",
			"Test Customer",
			"signature_data",
			"All good"
		)
		self.assertEqual(result["status"], "success")

		# Cleanup
		approval.reload()
		approval.delete(ignore_permissions=True)

	def tearDown(self):
		"""Clean up test data"""
		# Clean up any remaining test records
		if self.delivery_note and frappe.db.exists("Delivery Note", self.delivery_note.name):
			frappe.delete_doc("Delivery Note", self.delivery_note.name, ignore_permissions=True)
