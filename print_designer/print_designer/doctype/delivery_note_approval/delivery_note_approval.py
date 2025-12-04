# Copyright (c) 2024, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days


class DeliveryNoteApproval(Document):
	"""
	DocType for managing delivery note approval tokens and status tracking
	"""
	
	def validate(self):
		"""Validate the delivery note approval record"""
		# Generate approval token if not exists
		if not self.approval_token:
			self.approval_token = frappe.generate_hash(self.delivery_note + str(now_datetime()))
		
		# Set generated_on if not set
		if not self.generated_on:
			self.generated_on = now_datetime()
		
		# Validate status transitions
		if self.status == "Approved" and not self.approved_on:
			self.approved_on = now_datetime()
	
	def before_save(self):
		"""Before save operations"""
		# Update delivery note status if approval status changes
		if self.has_value_changed("status") and self.status in ["Approved", "Rejected"]:
			self.update_delivery_note_status()
	
	def update_delivery_note_status(self):
		"""Update the linked delivery note with approval status"""
		try:
			# Use db_set to bypass allow_on_submit restrictions for submitted DNs
			update_values = {}

			if self.status == "Approved":
				# Update both new standardized and legacy fields for compatibility
				update_values = {
					"customer_approval_status": "Approved",
					"custom_goods_received_status": "Approved",  # Legacy
					"customer_approved_on": self.approved_on or now_datetime(),
					"custom_customer_approval_date": self.approved_on or now_datetime(),  # Legacy
					"customer_approved_by": self.customer_name,
					"custom_approved_by": self.customer_name,  # Legacy
					"customer_signature": self.digital_signature,
					"custom_customer_signature": self.digital_signature  # Legacy
				}
			elif self.status == "Rejected":
				update_values = {
					"customer_approval_status": "Rejected",
					"custom_goods_received_status": "Rejected",  # Legacy
					"custom_rejection_reason": self.remarks
				}

			if update_values:
				frappe.db.set_value("Delivery Note", self.delivery_note, update_values, update_modified=True)

		except Exception as e:
			frappe.log_error(title="DN Status Update Error", message=str(e)[:1000])
	
	def get_approval_url(self):
		"""Get the approval URL for this record"""
		base_url = frappe.utils.get_url()
		return f"{base_url}/delivery-approval?dn={self.delivery_note}&token={self.approval_token}"
	
	def is_expired(self):
		"""Check if the approval token has expired (7 days default)"""
		if not self.generated_on:
			return True

		# Try to get expiry days from settings, default to 7 if not configured
		try:
			expiry_days = frappe.db.get_single_value("Print Designer Settings", "approval_expiry_days") or 7
		except Exception:
			expiry_days = 7

		expiry_date = add_days(self.generated_on, expiry_days)

		return now_datetime() > expiry_date
	
	@frappe.whitelist()
	def approve_delivery(self, customer_name, digital_signature=None, remarks=None):
		"""Approve the delivery with customer details"""
		if self.is_expired():
			frappe.throw("Approval link has expired")

		if self.status != "Pending":
			frappe.throw("Delivery has already been processed")

		# Use db_set for submitted documents to bypass allow_on_submit restrictions
		frappe.db.set_value(self.doctype, self.name, {
			"status": "Approved",
			"approved_on": now_datetime(),
			"customer_name": customer_name,
			"digital_signature": digital_signature,
			"remarks": remarks
		}, update_modified=True)

		# Reload to get updated values
		self.reload()

		# Update linked Delivery Note status (non-blocking)
		try:
			self.update_delivery_note_status()
		except Exception:
			pass  # Don't fail approval if DN update fails

		# Send notification (non-blocking)
		try:
			self.send_approval_notification()
		except Exception:
			pass  # Don't fail approval if notification fails

		return {"status": "success", "message": "Delivery approved successfully"}
	
	@frappe.whitelist()
	def reject_delivery(self, customer_name, remarks):
		"""Reject the delivery with reason"""
		if self.is_expired():
			frappe.throw("Approval link has expired")

		if self.status != "Pending":
			frappe.throw("Delivery has already been processed")

		# Use db_set for submitted documents to bypass allow_on_submit restrictions
		frappe.db.set_value(self.doctype, self.name, {
			"status": "Rejected",
			"customer_name": customer_name,
			"remarks": remarks
		}, update_modified=True)

		# Reload to get updated values
		self.reload()

		# Update linked Delivery Note status (non-blocking)
		try:
			self.update_delivery_note_status()
		except Exception:
			pass  # Don't fail rejection if DN update fails

		# Send notification (non-blocking)
		try:
			self.send_rejection_notification()
		except Exception:
			pass  # Don't fail rejection if notification fails

		return {"status": "success", "message": "Delivery rejected"}
	
	def send_approval_notification(self):
		"""Send email notification when delivery is approved"""
		try:
			delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)

			# Get owner's email (not username)
			owner_email = frappe.db.get_value("User", delivery_note.owner, "email")
			recipients = []

			# Only add if valid email
			if owner_email and "@" in owner_email:
				recipients.append(owner_email)

			# Add sales manager if exists
			if delivery_note.get("sales_partner"):
				sales_manager = frappe.db.get_value("Sales Partner", delivery_note.sales_partner, "email_id")
				if sales_manager and "@" in sales_manager:
					recipients.append(sales_manager)

			# Only send if we have valid recipients
			if not recipients:
				return

			frappe.sendmail(
				recipients=recipients,
				subject=f"Delivery Note {delivery_note.name} Approved",
				message=f"""
				<p>Delivery Note <strong>{delivery_note.name}</strong> has been approved by the customer.</p>
				<p><strong>Customer:</strong> {self.customer_name}</p>
				<p><strong>Approved On:</strong> {frappe.format(self.approved_on, 'Datetime')}</p>
				{f'<p><strong>Remarks:</strong> {self.remarks}</p>' if self.remarks else ''}
				<p>You can view the delivery note <a href="{frappe.utils.get_url()}/app/delivery-note/{delivery_note.name}">here</a>.</p>
				""",
				now=True
			)

		except Exception as e:
			# Log error with truncated title to avoid cascading errors
			frappe.log_error(title="Approval Notification Error", message=str(e)[:1000])
	
	def send_rejection_notification(self):
		"""Send email notification when delivery is rejected"""
		try:
			delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)

			# Get owner's email (not username)
			owner_email = frappe.db.get_value("User", delivery_note.owner, "email")
			recipients = []

			# Only add if valid email
			if owner_email and "@" in owner_email:
				recipients.append(owner_email)

			# Add sales manager if exists
			if delivery_note.get("sales_partner"):
				sales_manager = frappe.db.get_value("Sales Partner", delivery_note.sales_partner, "email_id")
				if sales_manager and "@" in sales_manager:
					recipients.append(sales_manager)

			# Only send if we have valid recipients
			if not recipients:
				return

			frappe.sendmail(
				recipients=recipients,
				subject=f"Delivery Note {delivery_note.name} Rejected",
				message=f"""
				<p>Delivery Note <strong>{delivery_note.name}</strong> has been rejected by the customer.</p>
				<p><strong>Customer:</strong> {self.customer_name}</p>
				<p><strong>Reason:</strong> {self.remarks}</p>
				<p>Please contact the customer to resolve the issue.</p>
				<p>You can view the delivery note <a href="{frappe.utils.get_url()}/app/delivery-note/{delivery_note.name}">here</a>.</p>
				""",
				now=True
			)

		except Exception as e:
			# Log error with truncated title to avoid cascading errors
			frappe.log_error(title="Rejection Notification Error", message=str(e)[:1000])


@frappe.whitelist(allow_guest=True)
def get_approval_details(token):
	"""Get approval details by token for guest users"""
	try:
		approval = frappe.get_doc("Delivery Note Approval", {"approval_token": token})
		
		if approval.is_expired():
			return {"error": "Approval link has expired"}
		
		if approval.status != "Pending":
			return {"error": "Delivery has already been processed", "status": approval.status}
		
		delivery_note = frappe.get_doc("Delivery Note", approval.delivery_note)
		
		return {
			"success": True,
			"approval": {
				"name": approval.name,
				"delivery_note": approval.delivery_note,
				"customer_mobile": approval.customer_mobile,
				"status": approval.status,
				"generated_on": approval.generated_on
			},
			"delivery_note": {
				"name": delivery_note.name,
				"customer": delivery_note.customer,
				"customer_name": delivery_note.customer_name,
				"posting_date": delivery_note.posting_date,
				"grand_total": delivery_note.grand_total,
				"currency": delivery_note.currency,
				"items": [{
					"item_code": item.item_code,
					"item_name": item.item_name,
					"qty": item.qty,
					"rate": item.rate,
					"amount": item.amount
				} for item in delivery_note.items]
			}
		}
		
	except frappe.DoesNotExistError:
		return {"error": "Invalid approval token"}
	except Exception as e:
		frappe.log_error(f"Error getting approval details: {str(e)}")
		return {"error": "System error occurred"}


@frappe.whitelist(allow_guest=True)
def submit_approval_decision(token, decision, customer_name, digital_signature=None, remarks=None):
	"""Submit approval decision (approve/reject)"""
	try:
		approval = frappe.get_doc("Delivery Note Approval", {"approval_token": token})
		
		if decision == "approve":
			return approval.approve_delivery(customer_name, digital_signature, remarks)
		elif decision == "reject":
			return approval.reject_delivery(customer_name, remarks)
		else:
			return {"error": "Invalid decision"}
			
	except frappe.DoesNotExistError:
		return {"error": "Invalid approval token"}
	except Exception as e:
		frappe.log_error(f"Error submitting approval decision: {str(e)}")
		return {"error": str(e)}