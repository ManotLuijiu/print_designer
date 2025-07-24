# Copyright (c) 2024, Frappe Technologies Pvt Ltd. and Contributors
# See license.txt

import unittest
import frappe
from frappe.utils import now_datetime, add_days


class TestDeliveryNoteApproval(unittest.TestCase):
	"""Test cases for Delivery Note Approval DocType"""
	
	def setUp(self):
		"""Set up test data"""
		# Create a test delivery note if it doesn't exist
		if not frappe.db.exists("Delivery Note", "TEST-DN-001"):
			self.create_test_delivery_note()
	
	def create_test_delivery_note(self):
		"""Create a test delivery note for testing"""
		delivery_note = frappe.get_doc({
			"doctype": "Delivery Note",
			"name": "TEST-DN-001",
			"customer": "_Test Customer",
			"posting_date": frappe.utils.today(),
			"items": [{
				"item_code": "_Test Item",
				"qty": 1,
				"rate": 100
			}]
		})
		delivery_note.insert(ignore_permissions=True)
		return delivery_note
	
	def test_approval_creation(self):
		"""Test creating a delivery note approval record"""
		approval = frappe.get_doc({
			"doctype": "Delivery Note Approval",
			"delivery_note": "TEST-DN-001",
			"customer_mobile": "+66123456789",
			"status": "Pending"
		})
		approval.insert(ignore_permissions=True)
		
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
		approval = frappe.get_doc({
			"doctype": "Delivery Note Approval",
			"delivery_note": "TEST-DN-001",
			"customer_mobile": "+66123456789",
			"status": "Pending"
		})
		approval.insert(ignore_permissions=True)
		
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
		approval = frappe.get_doc({
			"doctype": "Delivery Note Approval",
			"delivery_note": "TEST-DN-001",
			"customer_mobile": "+66123456789",
			"status": "Pending"
		})
		approval.insert(ignore_permissions=True)
		
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
		approval = frappe.get_doc({
			"doctype": "Delivery Note Approval",
			"delivery_note": "TEST-DN-001",
			"customer_mobile": "+66123456789",
			"status": "Pending",
			"generated_on": add_days(now_datetime(), -8)  # 8 days ago
		})
		approval.insert(ignore_permissions=True)
		
		# Test that approval is expired
		self.assertTrue(approval.is_expired())
		
		# Test that expired approval cannot be approved
		with self.assertRaises(frappe.ValidationError):
			approval.approve_delivery("Test Customer")
		
		# Cleanup
		approval.delete(ignore_permissions=True)
	
	def test_guest_api_functions(self):
		"""Test guest API functions"""
		approval = frappe.get_doc({
			"doctype": "Delivery Note Approval",
			"delivery_note": "TEST-DN-001",
			"customer_mobile": "+66123456789",
			"status": "Pending"
		})
		approval.insert(ignore_permissions=True)
		
		# Test get_approval_details
		from print_designer.print_designer.doctype.delivery_note_approval.delivery_note_approval import get_approval_details
		
		details = get_approval_details(approval.approval_token)
		self.assertTrue(details.get("success"))
		self.assertEqual(details["approval"]["delivery_note"], "TEST-DN-001")
		
		# Test submit_approval_decision
		from print_designer.print_designer.doctype.delivery_note_approval.delivery_note_approval import submit_approval_decision
		
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
		test_approvals = frappe.get_all("Delivery Note Approval", 
			filters={"delivery_note": "TEST-DN-001"})
		
		for approval in test_approvals:
			frappe.delete_doc("Delivery Note Approval", approval.name, 
				ignore_permissions=True)
		
		# Clean up test delivery note
		if frappe.db.exists("Delivery Note", "TEST-DN-001"):
			frappe.delete_doc("Delivery Note", "TEST-DN-001", 
				ignore_permissions=True)