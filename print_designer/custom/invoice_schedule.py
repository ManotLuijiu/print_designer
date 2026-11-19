# Copyright (c) 2026, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

"""Milestone billing for Sales Orders.

A Sales Order with ``pd_custom_enable_invoice_schedule`` enabled is billed in
milestones instead of in one go.

The milestones can be seeded from the Sales Order's own Payment Schedule, but
they are not limited to it. The Invoice Schedule is a free form plan: rows can
be added by hand, the portion of a row can be changed, and the plan may be
split into more invoices than the Payment Schedule has rows. The Payment
Schedule stays the collection plan, the Invoice Schedule stays the billing
plan, and the two are independent.

The Sales Order stays the contractual commitment. It keeps the full contract
quantity and amount and carries no ledger impact of its own. Each milestone
produces one Sales Invoice whose line quantity is the contract quantity
multiplied by the milestone portion, so the invoice line multiplies out:

	contract  40 @ 7,500.00 = 300,000.00
	milestone  8 @ 7,500.00 =  60,000.00   (20% of the contract)

The amount is never set by hand - it falls out of ``qty * rate`` exactly as
ERPNext expects, which keeps the tax base, the totals and the Sales Order's
``billed_amt`` / ``per_billed`` roll-up correct without any override.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt

from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

INVOICE_SCHEDULE_FIELD = "pd_custom_invoice_schedule"
ENABLE_FIELD = "pd_custom_enable_invoice_schedule"

STATUS_NOT_INVOICED = "Not Invoiced"
STATUS_DRAFT_CREATED = "Draft Created"
STATUS_INVOICED = "Invoiced"
STATUS_CANCELLED = "Cancelled"

SOURCE_PAYMENT_SCHEDULE = "Payment Schedule"
SOURCE_MANUAL = "Manual"


def is_invoice_schedule_enabled(doc):
	"""Is milestone billing switched on for this Sales Order?"""
	return cint(doc.get(ENABLE_FIELD)) == 1


def get_contract_base(doc):
	"""The contract value a milestone portion applies to.

	``net_total`` is the tax base of the whole order, so a milestone that is a
	percentage of the contract is a percentage of the amount that is actually
	subject to tax. Taxes are then charged on the milestone by the invoice
	itself.
	"""
	return flt(doc.get("net_total"))


def refresh_invoice_amounts(doc):
	"""Recompute the amount of every milestone that has not been invoiced yet.

	The portion is what the user drives, the amount follows from it. Milestones
	that already produced an invoice are frozen - they keep the amount they
	were billed at, even if the contract is edited afterwards.
	"""
	if not is_invoice_schedule_enabled(doc):
		return

	base = get_contract_base(doc)
	precision = doc.precision("net_total")

	for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
		if not row.milestone_status:
			row.milestone_status = STATUS_NOT_INVOICED

		if not row.milestone_source:
			row.milestone_source = SOURCE_MANUAL

		if row.milestone_status != STATUS_NOT_INVOICED:
			continue

		row.invoice_portion = flt(row.invoice_portion)
		row.invoice_amount = flt(base * row.invoice_portion / 100, precision)


def set_skip_delivery_note(doc):
	"""Service orders are never delivered, so no delivery note is needed.

	Without this the Sales Order can never reach ``per_delivered = 100`` and
	would be left sitting in the "To Bill" status even after the final
	milestone was invoiced.
	"""
	if not is_invoice_schedule_enabled(doc):
		return

	if cint(doc.get("skip_delivery_note")):
		return

	if not _is_service_order(doc):
		return

	doc.skip_delivery_note = 1


def _is_service_order(doc):
	"""True when no line of the order refers to a stock item."""
	item_codes = [d.item_code for d in doc.get("items") or [] if d.item_code]
	if not item_codes:
		return False

	stock_items = frappe.get_all(
		"Item",
		filters={"name": ["in", item_codes], "is_stock_item": 1},
		pluck="name",
	)
	return not stock_items


def sales_order_invoice_schedule(doc, method=None):
	"""Sales Order ``validate`` hook - keeps the milestone plan consistent."""
	sync_invoice_schedule_from_payment_schedule(doc)
	set_skip_delivery_note(doc)
	refresh_invoice_amounts(doc)
	_validate_portion_total(doc)


def sync_invoice_schedule_from_payment_schedule(doc):
	"""Copy the Payment Schedule into the Invoice Schedule when billing starts.

	Turning "Enable Invoice Schedule" on is the moment the billing plan comes
	into existence, so that is where the Payment Schedule is copied over.

	The copy is add only. A milestone that is already in the plan is never
	touched, and a milestone the user deleted stays deleted - from then on the
	plan belongs to the user.
	"""
	if doc.docstatus != 0:
		return

	if not is_invoice_schedule_enabled(doc):
		return

	if not _invoice_schedule_just_enabled(doc):
		return

	_seed_missing_milestones(doc)


def _invoice_schedule_just_enabled(doc):
	"""Did the user just turn milestone billing on?"""
	if not cint(doc.get(ENABLE_FIELD)):
		return False

	previous = doc.get_doc_before_save()
	if not previous:
		# a brand new document - the plan is created on its first save
		return True

	return cint(previous.get(ENABLE_FIELD)) != 1


def on_sales_order_submit(doc, method=None):
	"""Reset milestone state on a freshly submitted Sales Order.

	When a Sales Order is amended, its milestone rows are copied over to the
	amendment together with the links to the invoices that were already
	created. The amendment is a new contract, so it starts with a clean plan
	and its milestone amounts are worked out against the new contract value.
	"""
	base = get_contract_base(doc)
	precision = doc.precision("net_total")

	for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
		if row.get("sales_invoice"):
			amount = flt(base * flt(row.invoice_portion) / 100, precision)

			frappe.db.set_value(
				"Invoice Schedule",
				row.name,
				{
					"milestone_status": STATUS_NOT_INVOICED,
					"sales_invoice": None,
					"invoice_amount": amount,
				},
			)
			row.milestone_status = STATUS_NOT_INVOICED
			row.sales_invoice = None
			row.invoice_amount = amount


@frappe.whitelist()
def seed_invoice_schedule(sales_order):
	"""Copy the Sales Order's Payment Schedule rows into the Invoice Schedule.

	Only missing milestones are added. A milestone that is already in the
	Invoice Schedule is never overwritten - the user is free to change its
	portion, to rename it, or to split the plan further.
	"""
	doc = frappe.get_doc("Sales Order", sales_order)

	if not is_invoice_schedule_enabled(doc):
		frappe.throw(_("Enable Invoice Schedule before seeding milestones."))

	if doc.docstatus != 0:
		frappe.throw(_("Milestones can only be seeded on a draft Sales Order."))

	added, skipped = _seed_missing_milestones(doc)

	doc.save()

	return {"added": added, "skipped": skipped}


def _seed_missing_milestones(doc):
	"""Add the milestones of the Payment Schedule that the plan does not have yet.

	Only missing milestones are added. A milestone that is already in the
	Invoice Schedule is never overwritten - the user is free to change its
	portion, to rename it, or to split the plan further.

	Returns a ``(added, skipped)`` tuple.
	"""
	existing = {}
	for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
		term = (row.payment_term or "").strip()
		if term:
			existing.setdefault(term, row)

	added = 0
	skipped = 0

	for schedule_row in doc.get("payment_schedule") or []:
		term = (schedule_row.payment_term or "").strip()
		if not term:
			continue

		portion = flt(schedule_row.invoice_portion)
		if portion <= 0:
			continue

		if term in existing:
			skipped += 1
			continue

		doc.append(
			INVOICE_SCHEDULE_FIELD,
			{
				"payment_term": term,
				"invoice_portion": portion,
				"milestone_status": STATUS_NOT_INVOICED,
				"milestone_source": SOURCE_PAYMENT_SCHEDULE,
			},
		)
		existing[term] = doc.get(INVOICE_SCHEDULE_FIELD)[-1]
		added += 1

	return added, skipped


@frappe.whitelist()
def add_invoice_schedule_row(sales_order):
	"""Add one empty milestone to the Invoice Schedule.

	The new row starts with whatever portion of the contract is still not
	covered, so the user only has to change the number when they want a
	different split.
	"""
	doc = frappe.get_doc("Sales Order", sales_order)

	if not is_invoice_schedule_enabled(doc):
		frappe.throw(_("Enable Invoice Schedule before adding a milestone."))

	if doc.docstatus != 0:
		frappe.throw(
			_("Milestones can only be added on a draft Sales Order. Amend the Sales Order instead.")
		)

	remaining = _remaining_portion(doc)
	label = _next_milestone_label(doc)

	doc.append(
		INVOICE_SCHEDULE_FIELD,
		{
			"payment_term": label,
			"invoice_portion": remaining,
			"milestone_status": STATUS_NOT_INVOICED,
			"milestone_source": SOURCE_MANUAL,
		},
	)

	doc.save()

	return {"payment_term": label, "invoice_portion": remaining}


def _remaining_portion(doc):
	"""The part of the contract that no milestone covers yet."""
	total = sum(flt(row.invoice_portion) for row in doc.get(INVOICE_SCHEDULE_FIELD) or [])
	return max(0.0, flt(100 - total, 2))


def _next_milestone_label(doc):
	"""A label that does not collide with an existing milestone."""
	taken = {
		(row.payment_term or "").strip().lower() for row in doc.get(INVOICE_SCHEDULE_FIELD) or []
	}

	index = len(doc.get(INVOICE_SCHEDULE_FIELD) or []) + 1
	label = _("Milestone {0}").format(index)

	while label.lower() in taken:
		index += 1
		label = _("Milestone {0}").format(index)

	return label


@frappe.whitelist()
def create_milestone_invoices(sales_order):
	"""Create one draft Sales Invoice per milestone that is due.

	Only milestones that are still ``Not Invoiced`` and that carry an invoice
	date are processed. The invoices are created as drafts so the user can
	review the dates and the amounts before anything is posted.
	"""
	doc = frappe.get_doc("Sales Order", sales_order)

	if doc.docstatus != 1:
		frappe.throw(_("The Sales Order must be submitted before creating milestone invoices."))

	if not is_invoice_schedule_enabled(doc):
		frappe.throw(_("Enable Invoice Schedule before creating milestone invoices."))

	if not frappe.has_permission("Sales Invoice", "create"):
		frappe.throw(_("Not permitted to create a Sales Invoice."))

	_validate_portion_total(doc)

	created = []
	skipped = []

	for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
		if row.milestone_status != STATUS_NOT_INVOICED:
			skipped.append({"milestone": row.payment_term, "reason": row.milestone_status})
			continue

		if not row.invoice_date:
			skipped.append({"milestone": row.payment_term, "reason": _("no invoice date")})
			continue

		if not flt(row.invoice_portion):
			skipped.append({"milestone": row.payment_term, "reason": _("no portion")})
			continue

		invoice = _build_milestone_invoice(doc, row)
		invoice.insert(ignore_permissions=True)

		_set_milestone_state(row, STATUS_DRAFT_CREATED, invoice)

		created.append({"milestone": row.payment_term, "sales_invoice": invoice.name})

	return {"created": created, "skipped": skipped}


def _validate_portion_total(doc):
	"""The portions of all milestones have to add up to the whole contract."""
	total = sum(flt(row.invoice_portion) for row in doc.get(INVOICE_SCHEDULE_FIELD) or [])

	if total > 100.0001:
		frappe.throw(
			_("The milestone portions add up to {0}% - they cannot exceed 100%.").format(
				_flt(total)
			)
		)

	if total < 99.9999:
		frappe.msgprint(
			_("The milestone portions add up to {0}% - the contract is not fully covered.").format(
				_flt(total)
			),
			indicator="orange",
		)


def _build_milestone_invoice(so, row):
	"""Build a draft Sales Invoice for a single milestone of the Sales Order."""
	portion = flt(row.invoice_portion)

	# Re-use ERPNext's own mapper so the invoice keeps the address, the tax
	# template, the debit account and - importantly - the `so_detail` link
	# back to the Sales Order Item that the status updater relies on.
	invoice = make_sales_invoice(so.name)
	invoice.docstatus = 0
	invoice.status = "Draft"
	invoice.transaction_date = row.invoice_date
	invoice.posting_date = row.invoice_date

	so_items = {d.name: d for d in so.get("items") or []}

	for item in invoice.get("items") or []:
		so_item = so_items.get(item.so_detail)
		if not so_item:
			continue

		item.qty = _milestone_qty(so_item, portion)

		if flt(so_item.discount_amount):
			# an absolute discount has to be scaled with the milestone, a
			# percentage discount scales on its own
			item.discount_amount = flt(flt(so_item.discount_amount) * portion / 100)

		item.description = _build_item_description(so_item, row, portion)

	return invoice


def _milestone_qty(so_item, portion):
	"""The contract quantity multiplied by the milestone portion."""
	qty = flt(flt(so_item.qty) * portion / 100, 6)

	# keep whole quantities where the result is a whole number
	if abs(qty - round(qty)) < 1e-9:
		qty = float(round(qty))

	return qty


def _build_item_description(so_item, row, portion):
	"""Explain the milestone on the invoice line.

	The line itself is ``portion * qty`` at the contract rate, so the amount
	multiplies out. The description spells out where the number came from.
	"""
	contract_amount = flt(so_item.amount)
	milestone_amount = flt(contract_amount * portion / 100)

	lines = [
		_("Milestone: {0} ({1}%)").format(row.payment_term, _flt(portion)),
		_("Contract: {0} @ {1} = {2}").format(
			_flt(so_item.qty), _flt(so_item.rate), _flt(contract_amount)
		),
		_("This milestone: {0}% = {1}").format(_flt(portion), _flt(milestone_amount)),
	]

	if so_item.description:
		lines.append(so_item.description)

	return "<br>".join(lines)


def _set_milestone_state(row, status, invoice=None):
	"""Record the state of a milestone on the submitted Sales Order.

	The Sales Order is submitted, so the row is written straight to the
	database instead of saving the order - saving it would run the whole
	validate chain again on a submitted document.
	"""
	values = {"milestone_status": status}

	if invoice is not None:
		values["sales_invoice"] = invoice.name

	frappe.db.set_value("Invoice Schedule", row.name, values)

	# keep the in-memory row in step, otherwise a later save would write the
	# stale state back over the database
	row.milestone_status = status
	if invoice is not None:
		row.sales_invoice = invoice.name


def on_sales_invoice_submit(doc, method=None):
	"""Mark the milestone as invoiced once its Sales Invoice is submitted."""
	_sync_milestone(doc, STATUS_INVOICED)


def on_sales_invoice_cancel(doc, method=None):
	"""Release the milestone when its Sales Invoice is cancelled."""
	_sync_milestone(doc, STATUS_NOT_INVOICED, clear_invoice=True)


def on_sales_invoice_delete(doc, method=None):
	"""Release the milestone when its draft Sales Invoice is deleted.

	The Sales Order keeps a link to every milestone invoice. Without releasing
	that link the invoice could not be deleted, and the Sales Order cannot be
	cancelled first either - its cancellation is blocked while draft milestone
	invoices exist.
	"""
	rows = frappe.get_all(
		"Invoice Schedule",
		filters={
			"parenttype": "Sales Order",
			"sales_invoice": doc.name,
		},
		fields=["name", "parent"],
	)

	for row in rows:
		frappe.db.set_value(
			"Invoice Schedule",
			row.name,
			{"sales_invoice": None, "milestone_status": STATUS_NOT_INVOICED},
		)


def _sync_milestone(invoice, status, clear_invoice=False):
	"""Update the milestone rows that belong to this Sales Invoice."""
	order_names = {
		item.sales_order for item in invoice.get("items") or [] if item.sales_order
	}
	if not order_names:
		return

	for order_name in order_names:
		rows = frappe.get_all(
			"Invoice Schedule",
			filters={
				"parenttype": "Sales Order",
				"parent": order_name,
				"sales_invoice": invoice.name,
			},
			fields=["name"],
		)

		for row in rows:
			values = {"milestone_status": status}
			if clear_invoice:
				values["sales_invoice"] = None
			frappe.db.set_value("Invoice Schedule", row.name, values)


def on_sales_order_cancel(doc, method=None):
	"""Block the cancellation of an order that still has draft milestone invoices."""
	drafts = frappe.get_all(
		"Invoice Schedule",
		filters={
			"parenttype": "Sales Order",
			"parent": doc.name,
			"milestone_status": STATUS_DRAFT_CREATED,
		},
		fields=["sales_invoice"],
	)

	if drafts:
		frappe.throw(
			_(
				"Cancel the milestone Sales Invoices ({0}) before cancelling this Sales Order."
			).format(", ".join(d.sales_invoice for d in drafts))
		)


def _flt(value):
	"""Format a number the way it reads on an invoice."""
	return "{:,.2f}".format(flt(value))
