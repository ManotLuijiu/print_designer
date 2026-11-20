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
quantity and amount and carries no ledger impact of its own. A milestone is a
part of the contract that is billed, not a part of the service that is
delivered, so the invoice line keeps the contract quantity and scales the
rate:

        contract  40 @ 7,500.00 = 300,000.00
        milestone  40 @ 1,500.00 =  60,000.00   (20% of the contract)

The portion of the milestone is written into the ``%`` column of the Sales
Invoice Item, so the invoice shows what part of the contract it bills.

The amount is never set by hand - it falls out of ``qty * rate`` exactly as
ERPNext expects, which keeps the tax base, the totals and the Sales Order's
``billed_amt`` / ``per_billed`` roll-up correct without any override.
"""

import contextlib
from typing import Any, cast

import frappe
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime

from print_designer.utils.db import set_values
from print_designer.utils.flags import is_truthy

INVOICE_SCHEDULE_FIELD = "pd_custom_invoice_schedule"
ENABLE_FIELD = "pd_custom_enable_invoice_schedule"

STATUS_NOT_INVOICED = "Not Invoiced"
STATUS_DRAFT_CREATED = "Draft Created"
STATUS_INVOICED = "Invoiced"
STATUS_CANCELLED = "Cancelled"

SOURCE_PAYMENT_SCHEDULE = "Payment Schedule"
SOURCE_MANUAL = "Manual"
# The name of the request scoped note that says "this mapping call belongs to
# the milestone invoice generation of this Sales Order". It lives on
# ``frappe.local``, so it is per request and cannot be set by a client.
DRAFT_GENERATION_CONTEXT = "pd_milestone_draft_generation"

# The custom field on the Sales Invoice Item that carries the part of the
# contract a line bills. It is the "%" column of the invoice.
MILESTONE_PORTION_FIELD = "pd_custom_invoice_portion"

# How close two numbers have to be to count as the same number.
QTY_TOLERANCE = 1e-6

# How far the amount of a milestone invoice may drift from the milestone
# amount before the milestone counts as broken. ERPNext works the rate of a
# line out again from the price list and the pricing rules, so a small
# difference is normal - a gross one is not.
AMOUNT_TOLERANCE_RATIO = 0.01
AMOUNT_TOLERANCE_MIN = 1.0


@frappe.whitelist()
def search_milestone_payment_terms(txt=""):
    """Suggest existing terms without interpreting free milestone text as a link.

    get_list enforces the current user's Payment Term permissions. Keep this
    lookup in the app: other installed apps can replace the Desk link-search
    endpoint with a signature that is incompatible with the running Frappe.
    """
    return frappe.get_list(
        "Payment Term",
        fields=["name as value"],
        filters={"name": ["like", "%" + str(txt or "") + "%"]},
        order_by="name asc",
        limit_page_length=20,
    )


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
    prepare_amended_schedule(doc)
    reconcile_milestone_links(doc)
    sync_invoice_schedule_from_payment_schedule(doc)
    set_skip_delivery_note(doc)
    refresh_invoice_amounts(doc)
    _validate_portion_total(doc)


def prepare_amended_schedule(doc):
    """Release the invoice links an amendment inherited from the order it amends.

    An amendment is a new contract. Its milestone rows are copied over from the
    cancelled order together with the links to the invoices that were created
    for that contract, so those links are released and the plan starts again.

    This happens while the amendment is still a draft, so the plan the user
    sees is the plan of the new contract. The invoices of the original order
    are never touched.
    """
    if doc.docstatus != 0 or not doc.get("amended_from"):
        return

    if not doc.is_new():
        return

    for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
        if not row.get("sales_invoice"):
            continue

        row.milestone_status = STATUS_NOT_INVOICED
        row.sales_invoice = None


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
    """Keep the milestone plan of a submitted Sales Order in step.

    The invoices that were generated before the order was submitted stay linked
    to their milestone - the Sales Order is the contract, the invoice is the
    billing of one milestone of it.

    A link that belongs to another order is released: when a Sales Order is
    amended, its milestone rows are copied over to the amendment together with
    the links to the invoices of the contract it amends. The amendment is a new
    contract, so it starts with a clean plan.
    """
    base = get_contract_base(doc)
    precision = doc.precision("net_total")

    for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
        if not row.get("sales_invoice"):
            continue

        if _invoice_belongs_to_order(row.sales_invoice, doc.name):
            # the invoice was generated for this order - the link stays
            continue

        amount = flt(base * flt(row.invoice_portion) / 100, precision)

        set_values(
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


@frappe.whitelist(methods=["POST"])
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


@frappe.whitelist(methods=["POST"])
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


@frappe.whitelist(methods=["POST"])
def generate_milestone_invoices(sales_order, preview=None):
    """Create one draft Sales Invoice per milestone of a Sales Order.

    The invoices are drafts - nothing is posted. The workflow is: save the
    Sales Order, generate the milestone invoices, submit the Sales Order, and
    submit the invoices afterwards.

    ``preview`` returns the plan without creating anything, so the user can
    confirm the milestones, the dates and the portions before the invoices are
    made.

    An already submitted Sales Order can still be used to catch up on the
    milestones that never got an invoice. Milestones that already have one are
    never regenerated.
    """
    doc = frappe.get_doc("Sales Order", sales_order)
    if not doc.get("name"):
        frappe.throw(_("Save the Sales Order before generating invoices."))

    doc.check_permission("read")
    doc.check_permission("write")

    if not frappe.has_permission("Sales Invoice", "create"):
        frappe.throw(_("Not permitted to create a Sales Invoice."))
    if not is_invoice_schedule_enabled(doc):
        frappe.throw(_("Enable Invoice Schedule before creating milestone invoices."))
    _lock_sales_order(doc.name)
    _refresh_milestone_rows(doc)
    _validate_portion_total(doc)
    eligible, skipped = _partition_milestones(doc)

    if _is_truthy(preview):
        return {"created": [], "skipped": skipped, "plan": _milestone_plan(doc, eligible)}

    if not eligible:
        return {"created": [], "skipped": skipped, "plan": []}
    created = []
    try:
        for row in eligible:
            invoice = _build_milestone_invoice(doc, row)
            invoice.insert(ignore_permissions=True)

            _set_milestone_state(row, STATUS_DRAFT_CREATED, invoice)

            created.append(
                {
                    "milestone": row.payment_term,
                    "sales_invoice": invoice.name,
                    "invoice_date": str(row.invoice_date) if row.invoice_date else None,
                    "invoice_portion": flt(row.invoice_portion),
                }
            )
    except Exception:
        frappe.db.rollback()
        raise

    return {"created": created, "skipped": skipped, "plan": []}


@frappe.whitelist(methods=["POST"])
def create_milestone_invoices(sales_order):
    """Create one draft Sales Invoice per milestone that is due.

    Kept for the callers that already use this endpoint - the actual work is
    done by :func:`generate_milestone_invoices`.
    """
    return generate_milestone_invoices(sales_order)


def _is_truthy(value):
    """Is the value one of the ways a client can say "yes"?"""
    return is_truthy(value)


def _lock_sales_order(name):
    """Lock the order so two generations cannot run at the same time."""
    frappe.db.sql("select name from `tabSales Order` where name = %s for update", (name,))


def _refresh_milestone_rows(doc):
    """Re-read the milestone rows while the order is locked.

    The rows of the document were read before the order was locked. A second
    generation that started at the same time therefore still sees the old
    statuses and would create a second invoice for the same milestone. A
    locking read returns the committed state of the rows, and the rows of the
    document are updated in place, so the decision is made on locked data.
    """
    rows = cast(
        "list[dict[str, Any]]",
        frappe.db.sql(
            """
			select name, milestone_status, sales_invoice, invoice_date, invoice_portion
			from `tabInvoice Schedule` where parent = %s for update
			""",
            (doc.name,),
            as_dict=True,
        ),
    )

    fresh = {row["name"]: row for row in rows}
    for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
        current = fresh.get(row.name)
        if not current:
            continue
        row.milestone_status = current["milestone_status"]
        row.sales_invoice = current["sales_invoice"]
        row.invoice_date = current["invoice_date"]
        row.invoice_portion = current["invoice_portion"]


def reconcile_milestone_links(doc):
    """Keep the links to the milestone invoices when the order is saved.

    The links belong to the server: they are written when the invoices are
    generated and when they are submitted, cancelled or deleted. A form that
    was opened before the generation still shows the milestones without their
    links, and saving that form would write that old state over the database
    and lose the link - a second generation would then create a second invoice
    for the same milestone.

    Frappe turns such a stale form away on its own, because the timestamp of
    the order moves when the invoices are generated. This is the second line of
    defence: a link that is in the database stays, whatever the client sends.
    """
    rows = doc.get(INVOICE_SCHEDULE_FIELD) or []

    if not rows:
        return

    names = [row.name for row in rows if row.get("name")]

    if not names:
        return

    stored = frappe.get_all(
        "Invoice Schedule",
        filters={
            "name": ["in", names],
            "parenttype": "Sales Order",
            "parent": doc.name,
        },
        fields=["name", "milestone_status", "sales_invoice"],
    )

    by_name = {row.name: row for row in stored}

    for row in rows:
        current = by_name.get(row.get("name"))

        if not current or not current.sales_invoice:
            continue

        if row.get("sales_invoice"):
            continue

        row.sales_invoice = current.sales_invoice
        row.milestone_status = current.milestone_status


def _partition_milestones(doc):
    """Split the milestones into the ones that get an invoice and the ones that do not.

    A milestone gets an invoice when it is still ``Not Invoiced``, carries no
    active invoice link and covers a positive part of the contract. A
    placeholder row that covers nothing is skipped before the invoice date is
    looked at, so an empty row never blocks the real ones.
    """
    eligible = []
    skipped = []

    for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
        portion = flt(row.invoice_portion)

        if portion < 0:
            frappe.throw(
                _("The milestone {0} has a negative portion ({1}%).").format(
                    row.payment_term, _flt(portion)
                )
            )

        if not portion:
            skipped.append({"milestone": row.payment_term, "reason": _("no portion")})
            continue
        if row.milestone_status != STATUS_NOT_INVOICED:
            skipped.append({"milestone": row.payment_term, "reason": row.milestone_status})
            continue
        linked = row.get("sales_invoice")
        if linked:
            if frappe.db.exists("Sales Invoice", linked):
                skipped.append(
                    {"milestone": row.payment_term, "reason": _("invoice already linked")}
                )
                continue

            # the linked invoice is gone - release the milestone and carry on
            set_values(
                "Invoice Schedule",
                row.name,
                {"sales_invoice": None, "milestone_status": STATUS_NOT_INVOICED},
            )
            row.sales_invoice = None
            row.milestone_status = STATUS_NOT_INVOICED
        if not row.invoice_date:
            frappe.throw(
                _("Set an Invoice Date on the milestone {0} before generating its invoice.").format(
                    row.payment_term
                )
            )

        eligible.append(row)

    return eligible, skipped


def _milestone_plan(doc, rows):
    """What is going to be invoiced - the summary the user confirms."""
    base = get_contract_base(doc)
    precision = doc.precision("net_total")

    plan = []

    for row in rows:
        portion = flt(row.invoice_portion)
        plan.append(
            {
                "milestone": row.payment_term,
                "invoice_portion": portion,
                "invoice_amount": flt(base * portion / 100, precision),
                "invoice_date": str(row.invoice_date) if row.invoice_date else None,
            }
        )

    return plan


def _validate_portion_total(doc):
    """The portions of all milestones have to add up to the whole contract."""
    total = sum(flt(row.invoice_portion) for row in doc.get(INVOICE_SCHEDULE_FIELD) or [])
    for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
        if flt(row.invoice_portion) < 0:
            frappe.throw(
                _("The milestone {0} has a negative portion ({1}%).").format(
                    row.payment_term, _flt(row.invoice_portion)
                )
            )
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


def on_sales_order_before_submit(doc, method=None):
    """Block the submission until every billable milestone has a valid invoice.

    The milestone workflow is: save the Sales Order, generate the milestone
    invoices, submit the Sales Order, submit the invoices afterwards. A
    Sales Order whose milestones are not billed yet must not be submitted, so
    no invoice can end up pointing at a contract that was never locked in.

    Nothing is created here. The message tells the user what to do.
    """
    if not is_invoice_schedule_enabled(doc):
        return

    problems = []

    for row in doc.get(INVOICE_SCHEDULE_FIELD) or []:
        problem = _milestone_invoice_problem(doc, row)
        if problem:
            problems.append(_("Milestone {0}: {1}").format(row.payment_term, problem))

    if not problems:
        return

    frappe.throw(
        _(
            "Use Generate Invoice to create the milestone invoices of this Sales Order before "
            "submitting it. ({0})"
        ).format(" ".join(problems)),
        title=_("The milestone invoices are not ready"),
    )


def _milestone_invoice_problem(doc, row):
    """Why the milestone is not ready to be submitted - ``None`` when it is.

    A milestone is ready when it has a draft Sales Invoice that bills this
    Sales Order and still matches the lines the milestone was built from.
    """
    portion = flt(row.invoice_portion)

    if portion <= 0:
        return None

    if row.milestone_status == STATUS_INVOICED:
        return None

    invoice_name = row.get("sales_invoice")

    if not invoice_name:
        return _("no invoice has been generated yet")

    if not frappe.db.exists("Sales Invoice", invoice_name):
        return _("the linked invoice {0} no longer exists").format(invoice_name)

    invoice_docstatus = frappe.db.get_value("Sales Invoice", invoice_name, "docstatus")
    invoice_company = frappe.db.get_value("Sales Invoice", invoice_name, "company")
    invoice_customer = frappe.db.get_value("Sales Invoice", invoice_name, "customer")
    invoice_currency = frappe.db.get_value("Sales Invoice", invoice_name, "currency")

    if cint(invoice_docstatus if isinstance(invoice_docstatus, (int, float, str)) else 0) != 0:
        return _("the linked invoice {0} is not a draft any more").format(invoice_name)

    if invoice_company != doc.company:
        return _("the linked invoice {0} belongs to another company").format(invoice_name)

    if invoice_customer != doc.customer:
        return _("the linked invoice {0} belongs to another customer").format(invoice_name)

    if invoice_currency != doc.currency:
        return _("the linked invoice {0} uses another currency").format(invoice_name)

    milestone_date = row.get("invoice_date")

    if milestone_date:
        invoice_date = _invoice_date(invoice_name)

        if invoice_date and str(invoice_date)[:10] != str(milestone_date)[:10]:
            return _stale_invoice(invoice_name, _("it has another date than the milestone"))

    return _invoice_lines_problem(doc, row, invoice_name, portion)


def _invoice_date(invoice_name):
    """The date of a Sales Invoice.

    ERPNext renamed the field of the invoice date from `transaction_date` to
    `posting_date`, so the name is looked up instead of being assumed.
    """
    meta = frappe.get_meta("Sales Invoice")

    if meta.has_field("posting_date"):
        return frappe.db.get_value("Sales Invoice", invoice_name, "posting_date")

    return frappe.db.get_value("Sales Invoice", invoice_name, "transaction_date")


def _stale_invoice(invoice_name, reason):
    """The message for a milestone invoice that no longer matches the order.

    The invoice was built from the Sales Order when the milestone was
    generated. When the order is changed afterwards, the invoice no longer
    bills the milestone it is linked to, so it has to be generated again.
    """
    return _(
        "the linked invoice {0} no longer matches this milestone: {1}."
        " Generate the milestone invoice again."
    ).format(invoice_name, reason)


def _invoice_lines_problem(doc, row, invoice_name, portion):
    """Compare the lines of the invoice with the milestone they were built from.

    A milestone line keeps the contract quantity, carries the part of the
    contract it bills in its own field and bills the milestone amount. A
    changed portion, a changed quantity or a changed amount of the Sales
    Order shows up here.

    The rate is deliberately not compared.  ERPNext works the rate of an
    invoice out again from the price list, the pricing rules and the margin
    of the line, so a generated invoice may legitimately carry a different
    rate than the Sales Order.  Comparing it would block the submission of
    the order for a difference that is normal in ERPNext.  The amount is
    compared instead, but only within a tolerance.

    The portion is only compared when the invoice carries it.  The percent
    column is a custom field, so a site that does not have it cannot say
    which part of the contract a line bills; the amount check still holds.
    """
    # Every line of the Sales Order is known here, including a line without a
    # quantity.  Only the lines that carry a quantity have to be covered by
    # the invoice, but a line that the invoice does have must be a line of
    # this Sales Order - otherwise the invoice would bill something the order
    # does not contain.
    so_items = {d.name: d for d in doc.get("items") or []}
    billable_items = {name for name, item in so_items.items() if flt(item.qty)}

    if not billable_items:
        return None

    invoice_items = frappe.get_all(
        "Sales Invoice Item",
        filters={
            "parent": invoice_name,
            "parenttype": "Sales Invoice",
            "sales_order": doc.name,
        },
        fields=_invoice_item_fields(),
    )

    if not invoice_items:
        return _("the linked invoice {0} has no lines of this Sales Order").format(invoice_name)

    seen = set()

    for item in invoice_items:
        so_item = so_items.get(item.so_detail)
        if not so_item:
            return _(
                "the linked invoice {0} has a line that is not part of this Sales Order"
            ).format(invoice_name)

        seen.add(item.so_detail)

        problem = _invoice_item_problem(invoice_name, item, so_item, portion)

        if problem:
            return problem

    if len(seen & billable_items) != len(billable_items):
        return _("the linked invoice {0} does not cover every line of the Sales Order").format(
            invoice_name
        )

    return None


def _invoice_identity_problem(invoice_name, item, so_item):
    """Compare what the line is about: item, unit of measure, factor, project."""
    if item.item_code and so_item.item_code and item.item_code != so_item.item_code:
        return _stale_invoice(invoice_name, _("it bills a different item"))

    if item.uom and so_item.uom and item.uom != so_item.uom:
        return _stale_invoice(invoice_name, _("it uses a different unit of measure"))

    so_conversion = flt(so_item.conversion_factor)
    invoice_conversion = flt(item.conversion_factor)

    if (
        so_conversion
        and invoice_conversion
        and abs(so_conversion - invoice_conversion) > QTY_TOLERANCE
    ):
        return _stale_invoice(invoice_name, _("it uses a different conversion factor"))

    if (item.project or "") != (so_item.project or ""):
        return _stale_invoice(invoice_name, _("it bills a different project"))

    return None


def _invoice_amount_problem(invoice_name, item, so_item, portion):
    """Compare the quantity, the part of the contract and the amount."""
    if abs(flt(item.qty) - flt(so_item.qty)) > QTY_TOLERANCE:
        return _("the linked invoice {0} no longer matches this milestone").format(invoice_name)

    billed_portion = flt(item.get(MILESTONE_PORTION_FIELD))

    if billed_portion and abs(billed_portion - portion) > QTY_TOLERANCE:
        return _("the linked invoice {0} bills another part of the contract").format(invoice_name)

    expected = _milestone_amount(so_item, portion)

    if abs(flt(item.amount) - expected) > _amount_tolerance(expected):
        return _("the linked invoice {0} does not bill the milestone amount").format(invoice_name)

    return None


def _invoice_item_problem(invoice_name, item, so_item, portion):
    """Compare one line of the invoice with the line of the Sales Order.

    A line that bills another item, another unit of measure, another
    conversion factor or another project does not belong to this milestone
    any more.  The same is true for a line whose quantity, part of the
    contract or amount has moved away from the milestone.
    """
    problem = _invoice_identity_problem(invoice_name, item, so_item)

    if problem:
        return problem

    return _invoice_amount_problem(invoice_name, item, so_item, portion)


def _invoice_item_fields():
    """The fields of a Sales Invoice Item the milestone check reads.

    Besides the size of the line the check reads what the line *is*: the item,
    the unit of measure, the conversion factor and the project. A line that
    bills something else than the order does is not a milestone of this order,
    even when its quantity and its amount happen to be the same.

    The percent column is a custom field, so it is only read when the site
    actually has it.
    """
    fields = [
        "so_detail",
        "qty",
        "amount",
        "item_code",
        "uom",
        "conversion_factor",
        "project",
    ]

    if frappe.get_meta("Sales Invoice Item").has_field(MILESTONE_PORTION_FIELD):
        fields.append(MILESTONE_PORTION_FIELD)

    return fields


def _draft_generation_context():
    """The request scoped note of a milestone invoice generation."""
    return getattr(frappe.local, DRAFT_GENERATION_CONTEXT, None)


def _set_draft_generation_context(context):
    setattr(frappe.local, DRAFT_GENERATION_CONTEXT, context)


def _clear_draft_generation_context():
    with contextlib.suppress(AttributeError):
        delattr(frappe.local, DRAFT_GENERATION_CONTEXT)


def on_sales_invoice_before_mapping(doc, method=None, source_doc=None, table_maps=None):
    """Let a milestone invoice be mapped from a Sales Order that is still a draft.

    ERPNext's mapper refuses to map a Sales Order that is not submitted. The
    milestone workflow needs the invoice first and the submission of the order
    afterwards, so this hook relaxes that one check - and only that one - for
    the request scoped generation of a milestone invoice.

    The mapping dictionary belongs to the call that is running, so relaxing it
    here changes nothing else. The note that says "this call is allowed" lives
    on ``frappe.local``, so a client cannot set it.

    Only the ``docstatus`` check of the source is removed. Every other
    validation of the source stays in place.
    """
    context = _draft_generation_context()

    if not context or not table_maps or source_doc is None:
        return

    if source_doc.doctype != "Sales Order":
        return

    if source_doc.name != context.get("sales_order"):
        return

    if cint(source_doc.docstatus) != 0:
        return

    if not is_invoice_schedule_enabled(source_doc):
        return

    if not _may_create_sales_invoice():
        return

    source_map = table_maps.get("Sales Order") or {}
    validation = source_map.get("validation") or {}

    if not validation:
        return

    validation = {key: value for key, value in validation.items() if key != "docstatus"}
    source_map["validation"] = validation
    table_maps["Sales Order"] = source_map


def _may_create_sales_invoice() -> bool:
    """May the current user create a Sales Invoice?"""
    try:
        return bool(frappe.has_permission("Sales Invoice", "create"))
    except Exception:
        return False


def _build_milestone_invoice(so, row):
    """Build a draft Sales Invoice for a single milestone of the Sales Order."""
    portion = flt(row.invoice_portion)

    # Re-use ERPNext's own mapper so the invoice keeps the address, the tax
    # template, the debit account and - importantly - the `so_detail` link
    # back to the Sales Order Item that the status updater relies on.
    #
    # The mapper only maps a submitted Sales Order, so the call is marked with
    # a request scoped note. That note is what the `before_mapping` hook of
    # this app looks at.
    _set_draft_generation_context({"sales_order": so.name, "milestone": row.name})
    try:
        invoice = make_sales_invoice(so.name)
    finally:
        _clear_draft_generation_context()
    invoice.docstatus = 0
    invoice.status = "Draft"

    # The invoice is dated at the date of the milestone. ERPNext works the
    # posting date out again on every save - it puts the date of the day into
    # it - unless the document says that the date was set on purpose. The
    # milestone owns that date, so the invoice has to keep it.
    invoice.posting_date = row.invoice_date
    invoice.set_posting_time = 1

    if invoice.meta.has_field("transaction_date"):
        invoice.transaction_date = row.invoice_date

    # The dates of the payment schedule belong to the date of the order. The
    # invoice is dated at the date of the milestone, so the dates of the
    # schedule move with it - otherwise the due date of the invoice would lie
    # before the date of the invoice and ERPNext refuses the invoice.
    _shift_payment_schedule(invoice, so, row.invoice_date)

    _drop_lines_without_quantity(invoice)

    so_items = {d.name: d for d in so.get("items") or []}

    for item in invoice.get("items") or []:
        so_item = so_items.get(item.so_detail)
        if not so_item:
            continue
        # A milestone bills a part of the contract, it does not deliver a part
        # of the quantity. The service quantity stays whole and the rate is
        # scaled instead, so the amount of the line is the milestone amount
        # while ERPNext's own arithmetic (qty * rate) stays untouched.
        line = _milestone_line(so_item, portion)

        item.qty = line["qty"]
        item.rate = line["rate"]
        item.price_list_rate = line["rate"]
        item.discount_percentage = 0
        item.discount_amount = 0

        # ERPNext works the rate of a line out again from the price list, the
        # margin and the pricing rules (erpnext/controllers/taxes_and_totals.py
        # ::calculate_margin). The mapper copies margin_type,
        # margin_rate_or_amount and pricing_rules from the Sales Order line, so
        # without this the margin of that line is applied a second time on top
        # of the milestone rate and the line no longer bills the milestone
        # amount. The milestone rate is derived from the contract, not priced,
        # so those inputs are cleared.
        item.margin_type = None
        item.margin_rate_or_amount = 0
        item.pricing_rules = None

        # the part of the contract this line bills - the percent column
        item.set(MILESTONE_PORTION_FIELD, line["portion"])
        item.description = _build_item_description(so_item, row, portion)

    # the flat charges and the fixed discount of the contract belong to the
    # whole contract, so they are split over the milestones
    _allocate_fixed_amounts(invoice, so, row)

    return invoice


def _shift_payment_schedule(invoice, so, milestone_date):
    """Move the dates of the payment schedule to the date of the milestone.

    The schedule of the order is worked out for the date of the order. The
    invoice is dated at the date of the milestone, so the dates of the schedule
    move by the same number of days.

    The dates are also normalised to date objects.  The mapped schedule mixes
    types: a date that ERPNext worked out from a posting date that was still a
    string stays a string, while a date that came from the database is a
    date.  ERPNext compares the dates of the schedule with `max()`, and that
    fails on mixed types, so the invoice is refused before it is saved.
    """
    if not milestone_date:
        return

    reference = so.get("transaction_date") or so.get("posting_date")

    if not reference:
        return

    milestone = getdate(milestone_date)
    reference_day = getdate(reference)

    if not milestone or not reference_day:
        return

    offset = (milestone - reference_day).days

    # The schedule is normalised even when the milestone falls on the date of
    # the order, so the types of the dates never depend on the milestone.
    for row in invoice.get("payment_schedule") or []:
        due_date = getdate(row.get("due_date")) if row.get("due_date") else None
        if due_date is not None:
            row.due_date = getdate(add_days(due_date, offset))

        discount_date = getdate(row.get("discount_date")) if row.get("discount_date") else None
        if discount_date is not None:
            row.discount_date = getdate(add_days(discount_date, offset))


def _drop_lines_without_quantity(invoice):
    """Take the lines without a quantity off the invoice.

    A Sales Order may carry a line without a quantity when the site allows
    it (Selling Settings > Allow Zero Qty In Sales Order).  ERPNext maps that
    line onto the invoice, and the invoice would then be refused by
    ``AccountsController.validate_qty_is_not_zero``.

    Such a line bills nothing: the amount of a line is always the rate times
    the quantity, so a line without a quantity is worth nothing in the
    contract either.  It stays on the Sales Order until the quantity is
    known, and a later milestone can bill it.
    """
    for item in list(invoice.get("items") or []):
        if not flt(item.qty):
            invoice.remove(item)


def _milestone_portion_plan(so, row):
    """The portions of the plan and the place of a milestone in it.

    The plan is the Invoice Schedule of the order, in the order the milestones
    stand in it.
    """
    rows = so.get(INVOICE_SCHEDULE_FIELD) or []
    portions = [flt(candidate.invoice_portion) for candidate in rows]
    index = None

    for position, candidate in enumerate(rows):
        if candidate.name == row.name:
            index = position
            break

    return portions, index


def _allocate_fixed_value(value, portions, index, precision):
    """Split a fixed amount of the contract over the milestones of the plan.

    A flat charge and a fixed discount belong to the whole contract, not to a
    single milestone. The milestones split them the same way they split the
    contract value, and the last milestone of the plan carries the rounding
    remainder, so the invoices of the whole plan add up to the contract amount.
    """
    value = flt(value)

    if not value or index is None or not portions:
        return value

    portion = flt(portions[index])

    if not portion:
        return 0

    if index < len(portions) - 1:
        return flt(value * portion / 100, precision)

    # the last milestone of the plan takes what the others leave
    remainder = value

    for earlier in portions[:-1]:
        remainder = flt(remainder - flt(value * flt(earlier) / 100, precision), precision)

    return flt(remainder, precision)


def _allocate_fixed_amounts(invoice, so, row):
    """Split the fixed amounts of the contract over the milestone invoices.

    The mapper copies the flat charges and the fixed discount of the Sales
    Order onto every invoice it builds, so a plan of three milestones would
    charge the flat fee three times. The contract amount is split over the
    milestones instead.

    A discount in percent is left alone: ERPNext works it out again from the
    total of the invoice, so it follows the milestone on its own.
    """
    portions, index = _milestone_portion_plan(so, row)

    if index is None:
        return

    if flt(invoice.get("discount_amount")) and not flt(
        invoice.get("additional_discount_percentage")
    ):
        invoice.discount_amount = _allocate_fixed_value(
            invoice.discount_amount, portions, index, invoice.precision("discount_amount")
        )

    for tax in invoice.get("taxes") or []:
        if tax.charge_type != "Actual":
            continue

        if not flt(tax.tax_amount):
            continue

        tax.tax_amount = _allocate_fixed_value(
            tax.tax_amount, portions, index, tax.precision("tax_amount")
        )


def _milestone_rate(so_item, portion):
    """The rate that turns the contract quantity into the milestone amount.

    ERPNext always works the amount of a line out as ``qty * rate``, so the
    milestone amount can only be reached by scaling the rate. The quantity
    stays the contract quantity - a service is not delivered in parts.
    """
    rate = flt(so_item.rate)

    if not portion:
        return rate

    return flt(rate * portion / 100, _precision(so_item, "rate"))


def _milestone_amount(so_item, portion):
    """The amount one line of the Sales Order bills in this milestone."""
    return flt(
        _milestone_rate(so_item, portion) * flt(so_item.qty),
        _precision(so_item, "amount"),
    )


def _milestone_line(so_item, portion):
    """The values of the invoice line that bills this milestone.

    The quantity of the contract stays whole - a milestone bills a part of the
    contract, it does not deliver a part of the service. The rate carries the
    part, so the amount of the line is the milestone amount.
    """
    return {
        "qty": flt(so_item.qty),
        "rate": _milestone_rate(so_item, portion),
        "amount": _milestone_amount(so_item, portion),
        "portion": flt(portion),
    }


def _precision(doc, fieldname: str, default: int = 2) -> int:
    """The precision of a field of a document.

    A plain dictionary has no precision of its own, so the default of the
    currency fields is used for it.
    """
    precision = getattr(doc, "precision", None)

    if callable(precision):
        value = precision(fieldname)

        if isinstance(value, int):
            return value

    return default


def _amount_tolerance(amount):
    """How far the amount of a milestone invoice may drift."""
    return max(AMOUNT_TOLERANCE_MIN, abs(flt(amount)) * AMOUNT_TOLERANCE_RATIO)


def _build_item_description(so_item, row, portion):
    """Explain the milestone on the invoice line.

    The line keeps the contract quantity and bills the milestone amount, so
    the description spells out where both numbers came from.
    """
    contract_amount = flt(so_item.amount)
    milestone_rate = _milestone_rate(so_item, portion)
    milestone_amount = _milestone_amount(so_item, portion)

    lines = [
        _("Milestone: {0} ({1}%)").format(row.payment_term, _flt(portion)),
        _("Contract: {0} @ {1} = {2}").format(
            _flt(so_item.qty), _flt(so_item.rate), _flt(contract_amount)
        ),
        _("This milestone: {0} @ {1} = {2}").format(
            _flt(so_item.qty), _flt(milestone_rate), _flt(milestone_amount)
        ),
    ]
    if so_item.description:
        lines.append(so_item.description)

    return "<br>".join(lines)


def _set_milestone_state(row, status, invoice=None):
    """Record the state of a milestone on the Sales Order.

    The row is written straight to the database instead of saving the order -
    saving it would run the whole validate chain again, and a submitted order
    must not be saved at all.
    """
    values = {"milestone_status": status}

    if invoice is not None:
        values["sales_invoice"] = invoice.name
    set_values("Invoice Schedule", row.name, values)
    # keep the in-memory row in step, otherwise a later save would write the
    # stale state back over the database
    row.milestone_status = status
    if invoice is not None:
        row.sales_invoice = invoice.name

    _touch_sales_order(row.parent)


def _touch_sales_order(name):
    """Move the timestamp of the order forward after its milestone state changed.

    The links to the milestone invoices live in the child rows of the order,
    and Frappe writes the whole child table when the order is saved. A form
    that was opened before the generation would write the rows without their
    links back over the database, and a second generation would then create a
    second invoice for the same milestone.

    Frappe compares the timestamp of a document with the one in the database
    when it is saved, so moving it forward here turns such a stale form into
    a "the document has been modified after you have opened it" error instead
    of a lost link.
    """
    if not name:
        return

    frappe.db.set_value("Sales Order", name, "modified", now_datetime(), update_modified=False)


def _invoice_belongs_to_order(invoice_name, order_name):
    """Does the invoice bill this Sales Order?"""
    if not invoice_name or not order_name:
        return False

    return bool(
        frappe.get_all(
            "Sales Invoice Item",
            filters={
                "parent": invoice_name,
                "parenttype": "Sales Invoice",
                "sales_order": order_name,
            },
            pluck="name",
        )
    )


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
        set_values(
            "Invoice Schedule",
            row.name,
            {"sales_invoice": None, "milestone_status": STATUS_NOT_INVOICED},
        )

    for order_name in {row.parent for row in rows}:
        _touch_sales_order(order_name)


def _sync_milestone(invoice, status, clear_invoice=False):
    """Update the milestone rows that belong to this Sales Invoice."""
    order_names = {item.sales_order for item in invoice.get("items") or [] if item.sales_order}
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
            set_values("Invoice Schedule", row.name, values)

        _touch_sales_order(order_name)


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
