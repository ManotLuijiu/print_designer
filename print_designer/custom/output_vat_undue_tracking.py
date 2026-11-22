"""The Output VAT Undue tracking of a submitted service Sales Invoice.

Print Designer owns the tracking ledger of the sales whose VAT is not due
yet.  The ledger is the ``Output VAT Undue`` document; this module is the
one orchestration path that writes it.

The rules of the ledger:

* exactly one row per source Sales Invoice, and the name of the row is the
  name of the invoice.  The database enforces the uniqueness - the primary
  key of the table - and not an ``exists()`` check, which is only an
  optimisation.  Two transactions that create the row of the same invoice at
  the same time are therefore a normal event, not an error: the second one
  loses the race of the database and carries on with the row of the first
  one,
* the identity of a row is the invoice it belongs to.  The name of the row
  is the name of the invoice - the document names itself after the field
  ``sales_invoice`` and the insert sets the name as well - so the primary
  key of the table is the uniqueness of the ledger.  There is no unique
  index on the ``sales_invoice`` column on purpose: the rows of the old
  implementation carry a name of their own and a table that holds more than
  one row for an invoice cannot take such an index without a rewrite of the
  history of the ledger,
* a draft invoice creates no row,
* a service sale without a VAT liability (an exempt supply, a seller that is
  not registered, a zero rated supply) is tracked as well - it keeps the
  service base and carries a VAT of zero,
* the row keeps an immutable snapshot of the decision of the invoice, so a
  later change of the company settings never rewrites the history,
* the row never creates a GL entry.  The VAT of the invoice is posted by the
  tax row of the invoice itself; the ledger only tracks it,
* the work stays inside the transaction of the invoice.  There is no commit
  in a hook.

The tax decision itself comes from
:mod:`print_designer.custom.sales_invoice_tax_contract` - this module never
reads the fields of the invoice on its own.
"""

from uuid import uuid4

import frappe
from frappe import _
from frappe.utils import flt, getdate

from print_designer.custom.sales_invoice_tax_contract import (
    CLASSIFICATION_SERVICES,
    REASON_ALREADY_DUE,
    REASON_DEFERRED_SERVICE,
    REASON_EXEMPT_SUPPLY,
    REASON_NON_REGISTERED,
    REASON_UNCONFIRMED_REGISTRATION,
    REASON_ZERO_RATED,
    get_service_tax_snapshot,
)

# --- the statuses of the ledger ---------------------------------------------

STATUS_PENDING = "Pending"
STATUS_PARTIALLY_CONVERTED = "Partially Converted"
STATUS_CONVERTED = "Converted to Output VAT"
STATUS_NOT_APPLICABLE = "Not Applicable"
STATUS_ALREADY_DUE = "Already Due"
STATUS_CANCELLED = "Cancelled"

#: The statuses that carry an active undue balance.
ACTIVE_STATUSES = (STATUS_PENDING, STATUS_PARTIALLY_CONVERTED)

#: The statuses that never carry a balance, whatever the invoice carried.
CLOSED_STATUSES = (
    STATUS_CONVERTED,
    STATUS_NOT_APPLICABLE,
    STATUS_ALREADY_DUE,
    STATUS_CANCELLED,
)

#: The reasons of a sale that creates no VAT liability.
ZERO_LIABILITY_REASONS = (
    REASON_NON_REGISTERED,
    REASON_EXEMPT_SUPPLY,
    REASON_ZERO_RATED,
    REASON_UNCONFIRMED_REGISTRATION,
)

#: The reasons that are tracked as a row of the ledger.
TRACKED_REASONS = (
    REASON_DEFERRED_SERVICE,
    REASON_ALREADY_DUE,
) + ZERO_LIABILITY_REASONS

#: The prefix of the transaction local savepoint of the insert.
SAVEPOINT_PREFIX = "pd_ovu_insert_"


def is_service_invoice_in_scope(doc):
    """True when the invoice belongs to the scope of the tracking.

    The scope of the first rollout is a service only invoice: a mixed invoice
    needs a tested allocation of the VAT and is left out until it has one.
    """
    if getattr(doc, "doctype", None) != "Sales Invoice":
        return False

    if getattr(doc, "docstatus", 0) != 1:
        return False

    snapshot = get_service_tax_snapshot(doc)
    return snapshot.classification == CLASSIFICATION_SERVICES


def create_output_vat_undue_record(doc, method=None):
    """Create the tracking row of a submitted service Sales Invoice.

    The function is called from the ``on_submit`` hook of the Sales Invoice.
    It returns the row, or None when the invoice does not belong to the
    scope of the tracking.
    """
    if getattr(doc, "doctype", None) != "Sales Invoice":
        return None

    if getattr(doc, "docstatus", 0) != 1:
        return None

    snapshot = get_service_tax_snapshot(doc)
    if snapshot.classification != CLASSIFICATION_SERVICES:
        return None

    if snapshot.treatment_reason not in TRACKED_REASONS:
        frappe.log_error(
            title="Output VAT Undue: no tracking row created",
            message=(
                f"Sales Invoice {doc.name} is a service invoice, but its VAT treatment "
                f"({snapshot.treatment or 'not set'}) does not say whether the VAT is due, "
                "deferred, exempt or zero rated. No tracking row was created."
            ),
        )
        return None

    # The check is an optimisation only: it saves a round trip when the row
    # is already there.  The uniqueness itself is the work of the database,
    # so the race of two transactions is settled by the insert below.
    existing = frappe.db.exists("Output VAT Undue", {"sales_invoice": doc.name})
    if existing:
        return frappe.get_doc("Output VAT Undue", str(existing))

    record = _build_record(doc, snapshot)
    # The row is written by the system on the submit of the invoice.  It
    # stays inside the transaction of the invoice: a failure of the submit
    # takes the row with it.
    created = _insert_tracking_row(record, doc.name)
    if created is not None:
        return created

    # Another transaction created the row of this invoice while this one
    # was building it.  The row is the row of the ledger, whoever wrote it.
    return _read_tracking_row(doc.name)


def cancel_output_vat_undue_record(doc, method=None):
    """Cancel the tracking row of a cancelled Sales Invoice.

    The row is kept - it is the history of the sale - but it carries no
    active balance any more.
    """
    if getattr(doc, "doctype", None) != "Sales Invoice":
        return None

    record = _get_record(doc.name)
    if record is None:
        return None

    if record.get("status") == STATUS_CANCELLED:
        return record

    record.set("status", STATUS_CANCELLED)
    record.set("recognized_vat_amount", 0)
    record.set("remaining_vat_amount", 0)
    record.save(ignore_permissions=True)
    return record


def convert_to_output_vat(
    sales_invoice,
    tax_invoice_number,
    tax_invoice_date=None,
    recognized_amount=None,
):
    """Record the issuance of the tax invoice of a tracked sale.

    This is the explicit event service of the ledger.  The old behaviour -
    the conversion happened as soon as a number was typed into the invoice -
    is gone: a number in a field is not evidence that a tax invoice was
    issued.

    The function is idempotent: a second call with the same number does
    nothing.
    """
    record = _get_record(sales_invoice)
    if record is None:
        frappe.throw(
            _("There is no Output VAT Undue record for the Sales Invoice {0}.").format(
                sales_invoice
            ),
            title=_("Output VAT Undue"),
        )
        return None

    if record.get("status") == STATUS_CONVERTED:
        if record.get("tax_invoice_number") == tax_invoice_number:
            return record
        frappe.throw(
            _("The Sales Invoice {0} was already converted with the tax invoice {1}.").format(
                sales_invoice, record.get("tax_invoice_number")
            ),
            title=_("Output VAT Undue"),
        )

    if record.get("status") == STATUS_CANCELLED:
        frappe.throw(
            _("The Sales Invoice {0} was cancelled.").format(sales_invoice),
            title=_("Output VAT Undue"),
        )

    record.set("tax_invoice_number", tax_invoice_number)
    record.set("tax_invoice_date", tax_invoice_date)
    record.set("converted_date", getdate())
    record.set("converted_by", frappe.session.user)
    record.set("status", STATUS_CONVERTED)

    amount = (
        flt(recognized_amount)
        if recognized_amount is not None
        else flt(str(record.get("vat_amount") or 0))
    )
    record.set("recognized_vat_amount", amount)
    record.set("remaining_vat_amount", 0)
    record.save(ignore_permissions=True)
    return record


def _get_record(sales_invoice):
    """Return the tracking row of the invoice, or None.

    The oldest row of the invoice is the row of the ledger.  A site that
    carries the rows of the old implementation can hold more than one row
    for an invoice; the oldest one is the row that was written first and
    it is the row the ledger keeps.
    """
    name = frappe.db.get_value(
        "Output VAT Undue",
        {"sales_invoice": sales_invoice},
        "name",
        order_by="creation asc",
    )
    if not name:
        return None
    return frappe.get_doc("Output VAT Undue", str(name))


def _insert_tracking_row(record, name=None):
    """Insert the tracking row, tolerating a concurrent creation of it.

    The name of the row is the name of the source invoice, so a collision
    of the database is a collision of the identity of the ledger.  It is
    not an error of the sale: the row exists, the ledger is right and the
    submit of the invoice carries on.

    The name is given to the insert itself, so the identity of the row does
    not depend on the naming rules of the site: a document naming rule for
    the ledger would otherwise give the row a name of its own and the
    primary key of the table would not carry the identity of the invoice.

    The insert runs inside a transaction local savepoint.  On PostgreSQL a
    failed statement aborts the whole transaction, and only a rollback to
    the savepoint makes it usable again.  The savepoint is taken right
    before the insert, so the rollback undoes the refused insert and
    nothing else.

    Returns the inserted row, or None when the row was already there.
    """
    message_count = len(frappe.local.message_log)
    savepoint = SAVEPOINT_PREFIX + uuid4().hex[:10]

    frappe.db.savepoint(savepoint)
    try:
        record.insert(ignore_permissions=True, set_name=name)
    except (frappe.DuplicateEntryError, frappe.UniqueValidationError) as exc:
        # The rollback to the savepoint keeps the transaction of the invoice
        # usable.  It undoes the refused insert and nothing else: the
        # savepoint is taken right before it.  It does not run the rollback
        # watchers, so it does not touch the filesystem.
        frappe.db.rollback(save_point=savepoint)
        if not _is_duplicate_identity_error(exc):
            raise
        # The message of the refused insert is not a message of the sale.
        # Only the messages of the insert itself are dropped.
        del frappe.local.message_log[message_count:]
        return None

    frappe.db.release_savepoint(savepoint)
    return record


def _read_tracking_row(sales_invoice):
    """Return the committed tracking row of the invoice, or None.

    The read is a locking one, so a row that is written by another
    transaction cannot change while it is read.

    The read can still come back empty.  A transaction that lost the race
    of the database works in its own snapshot, and on PostgreSQL that
    snapshot does not hold the row of the winner yet.  The row is not lost
    by that: the transaction of the winner writes it and commits it.
    """
    name = frappe.db.get_value(
        "Output VAT Undue",
        {"sales_invoice": sales_invoice},
        "name",
        order_by="creation asc",
        for_update=True,
    )
    if not name:
        return None
    return frappe.get_doc("Output VAT Undue", str(name))


def _is_duplicate_identity_error(exc):
    """True when the error is a collision of the identity of the ledger.

    The identity of a row is the invoice it belongs to: the name of the
    row is the name of the invoice, so the primary key of the table is the
    uniqueness of the ledger.  Every other failure - a permission, a link,
    a validation, another database error - has to surface.
    """
    original = exc.args[2] if len(exc.args) > 2 else None
    if original is None:
        return False

    primary_key_check = getattr(frappe.db, "is_primary_key_violation", None)
    if callable(primary_key_check) and primary_key_check(original):
        return True

    unique_key_check = getattr(frappe.db, "is_unique_key_violation", None)
    if callable(unique_key_check) and unique_key_check(original):
        return _key_is_the_identity(original)

    return False


def _key_is_the_identity(exc):
    """True when the unique key of the error is a key of the ledger."""
    text = str(exc)
    return any(
        marker in text for marker in ("sales_invoice", "PRIMARY", "pkey", "'name'", '"name"')
    )


def _build_record(doc, snapshot):
    """Build the tracking row of the invoice from its tax snapshot."""
    record = frappe.new_doc("Output VAT Undue")

    record.set("sales_invoice", doc.name)
    record.set("company", doc.company)
    record.set("company_branch", snapshot.company_branch_code or doc.get("branch"))
    record.set("company_currency", doc.get("company_currency"))
    record.set("invoice_currency", doc.get("currency"))

    record.set("customer", doc.get("customer"))
    record.set("customer_name", doc.get("customer_name"))
    record.set("posting_date", doc.get("posting_date"))
    record.set("invoice_number", doc.name)

    record.set("customer_tax_id", _buyer_tax_id(doc))
    record.set("customer_branch", _buyer_branch(doc))

    # The amounts: the revenue of the service rows, the VAT of the VAT rows
    # and the total of the invoice.  The withholding tax and the retention
    # are never a part of them.
    record.set("base_amount", flt(doc.get("base_net_total")))
    record.set("service_base_amount", snapshot.eligible_service_base)
    record.set("vat_amount", snapshot.vat_amount)
    record.set("invoice_vat_amount", snapshot.vat_amount_currency)
    record.set("total_amount", flt(doc.get("base_grand_total")))

    # The snapshot of the decision.
    record.set("vat_treatment", snapshot.treatment)
    record.set("treatment_reason", snapshot.treatment_reason)
    record.set("service_classification", snapshot.classification)
    if snapshot.registration:
        record.set("registration_kind", snapshot.registration.kind)
        record.set("registration_status", snapshot.registration.status)

    record.set("status", status_for_snapshot(snapshot))
    record.set("recognized_vat_amount", 0)

    account, account_warning = _vat_account(doc, snapshot)
    record.set("output_vat_account", account)
    if account_warning:
        record.set("remarks", account_warning)

    return record


def status_for_snapshot(snapshot):
    """Return the status that a snapshot of a decision leads to.

    The vocabulary of the status belongs to the ledger, so the preview of a
    draft invoice uses the same one.
    """
    if snapshot.treatment_reason == REASON_DEFERRED_SERVICE:
        return STATUS_PENDING

    if snapshot.treatment_reason == REASON_ALREADY_DUE:
        return STATUS_ALREADY_DUE

    return STATUS_NOT_APPLICABLE


def _vat_account(doc, snapshot):
    """Return the account that holds the VAT of the invoice.

    The account of the tax row is the account that received the VAT, so the
    ledger and the GL of the invoice agree.  The account that the company
    configured for the undue VAT is checked against it: a difference is
    reported, it is never silently accepted.
    """
    if snapshot.vat_amount <= 0:
        # A sale without a VAT liability does not need an account.
        return None, None

    row_account = None
    for row in snapshot.vat_rows:
        if row.account_head:
            row_account = row.account_head
            break

    configured = None
    if doc.get("company"):
        configured = frappe.db.get_value("Company", doc.company, "default_output_vat_undue_account")

    if not configured and not row_account:
        return None, _(
            "The company {0} has no output VAT account configured and the invoice "
            "carries no tax row. The VAT of the sale cannot be reconciled."
        ).format(doc.company)

    if configured and row_account and configured != row_account:
        return row_account, _(
            "The VAT of the invoice was posted to the account {0}, but the company "
            "{1} is configured with the account {2} for the undue output VAT."
        ).format(row_account, doc.company, configured)

    return row_account or configured, None


def _buyer_tax_id(doc):
    """Return the tax id of the buyer.

    An unknown tax id stays empty: a made up value would be a false fact.
    """
    tax_id = doc.get("tax_id")
    if tax_id:
        return tax_id

    customer = doc.get("customer")
    if not customer:
        return None

    return frappe.db.get_value("Customer", customer, "tax_id")


def _buyer_branch(doc):
    """Return the branch of the buyer."""
    customer = doc.get("customer")
    if not customer:
        return None

    return frappe.db.get_value("Customer", customer, "pd_custom_branch_code")
