"""
Delivery Note Custom Logic - Server-Side QR Generation

Automatically generates QR code for delivery approval when DN is submitted.
Runs server-side to avoid client-side save conflicts and grid errors.
"""

import frappe
from frappe import _


def on_submit_delivery_note(doc, method=None):
	"""
	Auto-generate QR code for delivery approval when DN is submitted.

	This runs server-side to avoid:
	- Client-side save conflicts during form refresh
	- Grid access errors (accessing grid before it's loaded)
	- Disruptive modal popups during warehouse workflow

	The QR code is generated silently and can be viewed on-demand
	via the "Show QR Code" button.

	Triggered by: doc_events hook on Delivery Note on_submit
	"""
	try:
		# Import the QR generation function
		from print_designer.custom.delivery_note_qr import generate_delivery_approval_qr

		# Generate QR code (server-side, no client interaction)
		result = generate_delivery_approval_qr(doc.name)

		if result and result.get('qr_code'):
			frappe.msgprint(
				_("Delivery approval QR code generated. View it using 'Show QR Code' button."),
				alert=True,
				indicator="green"
			)

	except Exception as e:
		# Don't block DN submission if QR generation fails
		frappe.log_error(
			title="QR Generation Failed on DN Submit",
			message=f"Failed to generate QR for DN {doc.name}: {str(e)}"
		)
		frappe.msgprint(
			_("Warning: QR code generation failed. You can regenerate it later using 'Generate QR Code' button. Error: {0}").format(str(e)),
			alert=True,
			indicator="orange"
		)
