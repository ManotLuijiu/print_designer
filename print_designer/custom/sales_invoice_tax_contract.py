"""The background tax contract of a Sales Invoice (SI-01).

Print Designer owns the essential Thai VAT behaviour and must work without the
Thai Business Suite app.  This module is the one authoritative, read only
contract between a Sales Invoice and everything that tracks or reports its VAT:

* the Output VAT Undue ledger (SI-02) and
* the VAT Due / VAT Undue reports (SI-03).

Rules
-----
* Reading the contract never writes.  It does not save the invoice, does not
  create a tax record and does not create a GL entry.
* The Sales Invoice keeps its fields and its layout.  The contract reads the
  values that are stored already; it never adds a control and it never moves
  one.
* Only VAT is a VAT.  Withholding tax, retention and unrelated charges are
  reported separately and are never part of a VAT base.
* A missing registration, a missing treatment or a missing account is a
  configuration problem.  It is reported in the warnings of the snapshot and
  it never turns into a confirmed exemption.
* ``Standard VAT`` is the legacy name of ``VAT Due``.  It is read as
  ``VAT Due`` and it is never written back.
* An exempt supply and a seller that is not registered stay apart, even though
  the Sales Invoice stores both as ``Exempt from VAT``.
"""

from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import flt

from print_designer.custom.service_item_wht import is_service_item_group
from print_designer.custom.thai_company_registration import (
    VAT_STATUS_NOT_REGISTERED,
    VAT_STATUS_UNCONFIRMED,
    VAT_STATUS_UNKNOWN,
    CompanyRegistration,
    get_company_registration,
)


def _text(message: str) -> str:
    # Return the translated message - also without a site context.
    try:
        return _(message)
    except Exception:
        return message


# --- the VAT treatment vocabulary -------------------------------------------

VAT_TREATMENT_FIELD = "pd_custom_vat_treatment"

VAT_TREATMENT_DUE = "VAT Due"
VAT_TREATMENT_LEGACY_STANDARD = "Standard VAT"
VAT_TREATMENT_UNDUE = "VAT Undue"
VAT_TREATMENT_EXEMPT = "Exempt from VAT"
VAT_TREATMENT_ZERO_RATED = "Zero-rated for Export"

#: Every stored value that means "the VAT is due".
VAT_DUE_TREATMENTS = (VAT_TREATMENT_DUE, VAT_TREATMENT_LEGACY_STANDARD)

#: Deliberate manual choices - they are never overwritten.
MANUAL_VAT_TREATMENTS = (VAT_TREATMENT_EXEMPT, VAT_TREATMENT_ZERO_RATED)

#: The audit reason of a tracking row.  The reason is more precise than the
#: stored treatment: it separates the reason of the exemption.
REASON_ALREADY_DUE = "already_due"
REASON_DEFERRED_SERVICE = "deferred_service"
REASON_NON_REGISTERED = "non_registered"
REASON_UNCONFIRMED_REGISTRATION = "unconfirmed_registration"
REASON_EXEMPT_SUPPLY = "exempt_supply"
REASON_ZERO_RATED = "zero_rated"
REASON_UNKNOWN = "unknown"

#: The reasons that carry a VAT liability.
LIABILITY_REASONS = (REASON_ALREADY_DUE, REASON_DEFERRED_SERVICE)

# --- the classification vocabulary ------------------------------------------

CLASSIFICATION_SERVICES = "services"
CLASSIFICATION_GOODS = "goods"
CLASSIFICATION_MIXED = "mixed"
CLASSIFICATION_UNKNOWN = "unknown"

# --- the sources of the values ----------------------------------------------

TREATMENT_SOURCE_PERSISTED = "persisted"
TREATMENT_SOURCE_DERIVED = "derived"

VAT_SOURCE_CONFIGURED_ACCOUNTS = "configured_accounts"
VAT_SOURCE_KEYWORD_FALLBACK = "keyword_fallback"
VAT_SOURCE_NONE = "none"

#: The Item field that marks an item as a service.
SERVICE_ITEM_FIELD = "pd_custom_is_service_item"

#: The fields that can carry the number of the tax invoice.  The contract
#: reads the first one that exists on the document; it never adds one.
TAX_INVOICE_FIELD_PAIRS = (
    ("pd_custom_tax_invoice_number", "pd_custom_tax_invoice_date"),
    ("thai_tax_invoice_number", "thai_tax_invoice_date"),
    ("tax_invoice_number", "tax_invoice_date"),
)


@dataclass(frozen=True)
class VatTaxRow:
    """One VAT row of the taxes of a Sales Invoice."""

    account_head: str | None = None
    description: str | None = None
    charge_type: str | None = None
    rate: float = 0.0
    tax_amount: float = 0.0
    base_tax_amount: float = 0.0
    #: True when the tax is included in the amount of the row (an inclusive
    #: VAT): the row total does not grow by the tax.
    is_inclusive: bool = False


@dataclass(frozen=True)
class ServiceTaxSnapshot:
    """The tax snapshot of one Sales Invoice.

    The snapshot is the only thing the tracking ledger and the reports read.
    It is a value object: it is never written back to the invoice.
    """

    # --- identity ------------------------------------------------------------
    sales_invoice: str | None = None
    docstatus: int = 0
    posting_date: str | None = None
    company: str | None = None
    branch: str | None = None
    customer: str | None = None
    currency: str | None = None
    company_currency: str | None = None
    tax_category: str | None = None
    taxes_and_charges: str | None = None

    # --- classification ------------------------------------------------------
    classification: str = CLASSIFICATION_UNKNOWN
    service_item_codes: tuple = ()
    goods_item_codes: tuple = ()
    unclassified_item_codes: tuple = ()
    #: True for a pure service invoice - the scope of the first pilot.
    is_service_sale: bool = False

    # --- registration --------------------------------------------------------
    registration: CompanyRegistration | None = None

    # --- treatment -----------------------------------------------------------
    treatment: str | None = None
    treatment_source: str = TREATMENT_SOURCE_PERSISTED
    treatment_reason: str = REASON_UNKNOWN
    #: True when the stored value was the legacy name of ``VAT Due``.
    treatment_is_legacy_alias: bool = False
    derived_treatment: str | None = None

    # --- the amounts ---------------------------------------------------------
    #: The net total of the whole invoice, in the currency of the company.
    net_total: float = 0.0
    #: The net total of the service rows only, in the currency of the company.
    eligible_service_base: float = 0.0
    #: The same amount in the currency of the invoice.
    eligible_service_base_currency: float = 0.0
    #: The VAT of the invoice, in the currency of the company.
    vat_amount: float = 0.0
    #: The same amount in the currency of the invoice.
    vat_amount_currency: float = 0.0
    #: The VAT that belongs to the service rows.  It is None for a mixed
    #: invoice: the VAT of a mixed supply is not allocated here.
    service_vat_amount: float | None = None
    vat_rate: float | None = None
    vat_rows: tuple = ()
    vat_source: str = VAT_SOURCE_NONE
    #: True when one of the VAT rows is included in the amount of its row.
    has_inclusive_vat: bool = False

    # --- the company context -------------------------------------------------
    #: True when the company is a service business (a context, not a proof
    #: that every item of the invoice is a service).
    company_service_business: bool = False
    #: True when the company is a construction service company.
    company_construction_service: bool = False
    #: The branch code of the company (the VAT branch of the registration).
    company_branch_code: str | None = None

    # --- withheld and retained money (never a part of the VAT base) ----------
    subject_to_wht: bool = False
    wht_percentage: float = 0.0
    wht_amount: float = 0.0
    #: True when the invoice has to carry a withholding tax certificate.
    wht_certificate_required: bool = False
    subject_to_retention: bool = False
    retention_percentage: float = 0.0
    retention_amount: float = 0.0
    net_total_after_wht: float = 0.0
    net_total_after_wht_and_retention: float = 0.0

    # --- the tax point --------------------------------------------------------
    tax_invoice_number: str | None = None
    tax_invoice_date: str | None = None
    tax_invoice_number_field: str | None = None

    # --- diagnostics ----------------------------------------------------------
    warnings: tuple = ()

    @property
    def has_vat_liability(self) -> bool:
        """True when the invoice carries a VAT that has to be accounted for."""
        return self.treatment_reason in LIABILITY_REASONS

    @property
    def is_deferred(self) -> bool:
        """True when the VAT of the invoice is not due yet."""
        return self.treatment_reason == REASON_DEFERRED_SERVICE

    @property
    def is_non_taxable(self) -> bool:
        """True when the invoice must not create a VAT liability."""
        return self.treatment_reason in (
            REASON_NON_REGISTERED,
            REASON_UNCONFIRMED_REGISTRATION,
            REASON_EXEMPT_SUPPLY,
            REASON_ZERO_RATED,
        )

    def as_dict(self) -> dict:
        """Return the snapshot as a plain dictionary."""
        data = {
            "sales_invoice": self.sales_invoice,
            "docstatus": self.docstatus,
            "posting_date": self.posting_date,
            "company": self.company,
            "branch": self.branch,
            "customer": self.customer,
            "currency": self.currency,
            "company_currency": self.company_currency,
            "tax_category": self.tax_category,
            "taxes_and_charges": self.taxes_and_charges,
            "classification": self.classification,
            "service_item_codes": list(self.service_item_codes),
            "goods_item_codes": list(self.goods_item_codes),
            "unclassified_item_codes": list(self.unclassified_item_codes),
            "is_service_sale": self.is_service_sale,
            "registration": self.registration.as_dict() if self.registration else None,
            "treatment": self.treatment,
            "treatment_source": self.treatment_source,
            "treatment_reason": self.treatment_reason,
            "treatment_is_legacy_alias": self.treatment_is_legacy_alias,
            "derived_treatment": self.derived_treatment,
            "net_total": self.net_total,
            "eligible_service_base": self.eligible_service_base,
            "eligible_service_base_currency": self.eligible_service_base_currency,
            "vat_amount": self.vat_amount,
            "vat_amount_currency": self.vat_amount_currency,
            "service_vat_amount": self.service_vat_amount,
            "vat_rate": self.vat_rate,
            "vat_rows": [row.__dict__ for row in self.vat_rows],
            "vat_source": self.vat_source,
            "has_inclusive_vat": self.has_inclusive_vat,
            "company_service_business": self.company_service_business,
            "company_construction_service": self.company_construction_service,
            "company_branch_code": self.company_branch_code,
            "subject_to_wht": self.subject_to_wht,
            "wht_percentage": self.wht_percentage,
            "wht_amount": self.wht_amount,
            "wht_certificate_required": self.wht_certificate_required,
            "subject_to_retention": self.subject_to_retention,
            "retention_percentage": self.retention_percentage,
            "retention_amount": self.retention_amount,
            "net_total_after_wht": self.net_total_after_wht,
            "net_total_after_wht_and_retention": self.net_total_after_wht_and_retention,
            "tax_invoice_number": self.tax_invoice_number,
            "tax_invoice_date": self.tax_invoice_date,
            "tax_invoice_number_field": self.tax_invoice_number_field,
            "warnings": list(self.warnings),
        }
        return data


def _flt(value, precision=None) -> float:
    """Return the value as a number, never None."""
    try:
        return flt(float(str(value or 0)), precision)
    except (TypeError, ValueError):
        return 0.0


def _cint(value) -> int:
    """Return the value as an integer, never None."""
    try:
        return int(float(str(value or 0)))
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def doc_value(doc, field, default=None):
    """Read a field of a document or of a plain dictionary.

    ``BaseDocument.get`` only reads the fields of the document itself, so a
    value that is a property (the company currency of a Sales Invoice) needs
    the fallback.
    """
    if doc is None:
        return default

    if isinstance(doc, dict):
        value = doc.get(field, default)
    else:
        value = doc.get(field) if hasattr(doc, "get") else None
        if value in (None, ""):
            value = getattr(doc, field, None)

    if value in (None, ""):
        return default
    return value


def doc_has_field(doc, field) -> bool:
    """True when the document carries the given field."""
    meta = getattr(doc, "meta", None)
    if meta is not None:
        try:
            return bool(meta.has_field(field))
        except Exception:
            return False

    if isinstance(doc, dict):
        return field in doc
    return True


def normalize_vat_treatment(value):
    """Return the canonical name of a stored VAT treatment.

    ``Standard VAT`` is the legacy name of ``VAT Due``.  It is understood, it
    is never written again.
    """
    if not value:
        return None

    text = str(value).strip()
    if text == VAT_TREATMENT_LEGACY_STANDARD:
        return VAT_TREATMENT_DUE
    return text


def derive_treatment_reason(treatment, registration):
    """Return the audit reason of a treatment.

    The stored treatment alone is not precise enough: the Sales Invoice stores
    ``Exempt from VAT`` for an exempt supply and for a seller that is not
    registered.  The registration of the company tells them apart, and an
    unconfirmed registration is never reported as a confirmed exemption.
    """
    if not treatment:
        return REASON_UNKNOWN

    if treatment == VAT_TREATMENT_UNDUE:
        return REASON_DEFERRED_SERVICE

    if treatment == VAT_TREATMENT_ZERO_RATED:
        return REASON_ZERO_RATED

    if treatment == VAT_TREATMENT_EXEMPT:
        kind = registration.kind if registration else VAT_STATUS_UNKNOWN
        if kind == VAT_STATUS_NOT_REGISTERED:
            return REASON_NON_REGISTERED
        if kind == VAT_STATUS_UNCONFIRMED:
            return REASON_UNCONFIRMED_REGISTRATION
        return REASON_EXEMPT_SUPPLY

    if treatment == VAT_TREATMENT_DUE:
        return REASON_ALREADY_DUE

    return REASON_UNKNOWN


def derive_treatment(registration, has_service_items=False, is_pos=False):
    """The treatment that the registration and the supply lead to.

    This is the fallback of Print Designer.  It does not use the tax template
    of the company: the template rules are still owned by the Thai Business
    Suite app and are ported with the relocated controllers.
    """
    kind = registration.kind if registration else VAT_STATUS_UNKNOWN
    if kind in (VAT_STATUS_NOT_REGISTERED, VAT_STATUS_UNCONFIRMED):
        return VAT_TREATMENT_EXEMPT

    if has_service_items and not is_pos:
        return VAT_TREATMENT_UNDUE

    return VAT_TREATMENT_DUE


def classify_supply(rows):
    """Classify the rows of an invoice.

    Every row is classified explicitly.  A non stock item is not a service
    unless it is flagged as one, so a mixed invoice is never routed as a
    service invoice.

    :return: a dictionary with the classification, the item codes per class
            and the flag ``is_service_sale``.
    """
    service_codes = []
    goods_codes = []
    unclassified_codes = []

    for row in rows or []:
        code = row.get("item_code")
        if row.get("is_service"):
            service_codes.append(code)
        elif row.get("is_stock"):
            goods_codes.append(code)
        else:
            unclassified_codes.append(code)

    if service_codes and goods_codes:
        classification = CLASSIFICATION_MIXED
    elif service_codes:
        classification = CLASSIFICATION_SERVICES
    elif goods_codes:
        classification = CLASSIFICATION_GOODS
    else:
        classification = CLASSIFICATION_UNKNOWN

    return {
        "classification": classification,
        "service_item_codes": tuple(service_codes),
        "goods_item_codes": tuple(goods_codes),
        "unclassified_item_codes": tuple(unclassified_codes),
        #: The pilot scope is a pure service invoice without an unclassified
        #: row.
        "is_service_sale": classification == CLASSIFICATION_SERVICES and not unclassified_codes,
    }


def select_vat_rows(rows, configured_accounts=(), account_meta=None):
    """Return the VAT rows of the taxes of an invoice.

    The rows of the accounts that the company configured as its VAT accounts
    win.  Only when no row matches them, a row of a tax account whose name
    contains ``VAT`` is used - and the source is reported, so the fallback
    never hides itself.

    Withholding tax rows are never a VAT.
    """
    account_meta = account_meta or {}
    configured = {account for account in (configured_accounts or []) if account}

    selected = [
        row
        for row in (rows or [])
        if row.get("account_head") in configured and not row.get("is_tax_withholding_account")
    ]
    if selected:
        return selected, VAT_SOURCE_CONFIGURED_ACCOUNTS

    fallback = []
    for row in rows or []:
        if row.get("is_tax_withholding_account"):
            continue
        account = row.get("account_head") or ""
        meta = account_meta.get(account) or {}
        if meta.get("account_type") != "Tax":
            continue
        if "VAT" not in str(meta.get("account_name") or account).upper():
            continue
        fallback.append(row)

    if fallback:
        return fallback, VAT_SOURCE_KEYWORD_FALLBACK

    return [], VAT_SOURCE_NONE


def sum_vat_rows(vat_rows, precision=2):
    """Return ``(base_total, currency_total)`` of the VAT rows."""
    base_total = 0.0
    currency_total = 0.0

    for row in vat_rows or []:
        base_total += _flt(row.get("base_tax_amount"), precision)
        currency_total += _flt(row.get("tax_amount"), precision)

    return _flt(base_total, precision), _flt(currency_total, precision)


def service_base_amount(rows, service_codes, precision=2):
    """Return ``(base_total, currency_total)`` of the service rows."""
    service_codes = set(service_codes or [])
    base_total = 0.0
    currency_total = 0.0

    for row in rows or []:
        if row.get("item_code") not in service_codes:
            continue
        base_total += _flt(row.get("base_net_amount"), precision)
        currency_total += _flt(row.get("net_amount"), precision)

    return _flt(base_total, precision), _flt(currency_total, precision)


# ---------------------------------------------------------------------------
# Reading the database
# ---------------------------------------------------------------------------


def get_item_tax_info(item_codes):
    """Return the tax relevant master data of the given items.

    :return: a map of item code -> ``{"is_service", "is_stock", "item_group"}``
    """
    item_codes = [code for code in (item_codes or []) if code]
    if not item_codes:
        return {}

    fields = ["name", "is_stock_item", "item_group"]
    try:
        if frappe.get_meta("Item").has_field(SERVICE_ITEM_FIELD):
            fields.append(SERVICE_ITEM_FIELD)
    except Exception:
        pass

    rows = frappe.get_all(
        "Item",
        filters={"name": ["in", item_codes]},
        fields=fields,
        limit_page_length=0,
    )

    info = {}
    for row in rows:
        is_service = bool(_cint(row.get(SERVICE_ITEM_FIELD) or 0)) or is_service_item_group(
            row.get("item_group")
        )
        info[row.get("name")] = {
            "is_service": is_service,
            "is_stock": bool(_cint(row.get("is_stock_item") or 0)),
            "item_group": row.get("item_group"),
        }

    return info


def get_company_vat_accounts(company):
    """Return the VAT accounts that the company configured."""
    if not company:
        return []

    try:
        meta = frappe.get_meta("Company")
    except Exception:
        return []

    fields = [
        fieldname
        for fieldname in ("default_output_vat_account", "default_output_vat_undue_account")
        if meta.has_field(fieldname)
    ]
    if not fields:
        return []

    rows = frappe.get_all("Company", filters={"name": company}, fields=fields, limit=1)
    if not rows:
        return []

    accounts = []
    for row in rows:
        for fieldname in fields:
            if row.get(fieldname):
                accounts.append(row.get(fieldname))

    return accounts


def get_account_meta(accounts):
    """Return the master data of the given accounts."""
    accounts = [account for account in (accounts or []) if account]
    if not accounts:
        return {}

    try:
        rows = frappe.get_all(
            "Account",
            filters={"name": ["in", accounts]},
            fields=["name", "account_type", "account_name"],
            limit_page_length=0,
        )
    except Exception:
        return {}

    return {
        row.get("name"): {
            "account_type": row.get("account_type"),
            "account_name": row.get("account_name"),
        }
        for row in rows
    }


def collect_tax_rows(doc):
    """Return the tax rows of a Sales Invoice as plain dictionaries."""
    rows = []
    for row in doc_value(doc, "taxes") or []:
        rows.append(
            {
                "account_head": doc_value(row, "account_head"),
                "description": doc_value(row, "description"),
                "charge_type": doc_value(row, "charge_type"),
                "rate": _flt(doc_value(row, "rate", 0)),
                "tax_amount": _flt(doc_value(row, "tax_amount", 0)),
                "base_tax_amount": _flt(doc_value(row, "base_tax_amount", 0)),
                "is_tax_withholding_account": _cint(
                    doc_value(row, "is_tax_withholding_account", 0)
                ),
                "is_inclusive": _is_inclusive_tax_row(row),
            }
        )
    return rows


def _is_inclusive_tax_row(row):
    """True when the tax of the row is included in the amount of the row.

    ERPNext adds the tax of an exclusive row to the row total, so the total
    of an exclusive row is bigger than its net amount.  An inclusive row
    keeps both values equal.
    """
    tax_amount = _flt(doc_value(row, "tax_amount", 0))
    if not tax_amount:
        return False

    total = _flt(doc_value(row, "total", 0))
    net_amount = _flt(doc_value(row, "net_amount", 0))
    if not total and not net_amount:
        return False

    return abs(total - net_amount) < 0.01


def harmonise_base_amounts(tax_rows, currency, company_currency, conversion_rate=None):
    """Use the invoice amount as the base amount when both are the same.

    ERPNext leaves ``base_tax_amount`` empty on a row that was not recomputed.
    On a document in the currency of the company, the tax amount is the base
    amount.  On a document in another currency, the base amount is the tax
    amount converted with the rate of the document - the way ERPNext computes
    it (``tax_amount * conversion_rate``).

    A row that keeps its tax amount but has no base amount has no VAT in the
    currency of the company; the caller reports it as a warning.
    """
    if currency and company_currency and currency != company_currency:
        rate = _flt(conversion_rate)
        if rate:
            for row in tax_rows or []:
                if not row.get("base_tax_amount") and row.get("tax_amount"):
                    row["base_tax_amount"] = _flt(row.get("tax_amount")) * rate
        return tax_rows

    for row in tax_rows or []:
        if not row.get("base_tax_amount") and row.get("tax_amount"):
            row["base_tax_amount"] = row["tax_amount"]

    return tax_rows


def rows_without_base_amount(tax_rows):
    """Return the tax rows that carry a tax amount but no base amount."""
    return [
        row for row in tax_rows or [] if row.get("tax_amount") and not row.get("base_tax_amount")
    ]


def get_tax_invoice_reference(doc):
    """Return ``(number, date, number_field)`` of the tax invoice.

    Only a field that exists on the document is read.  The contract never adds
    a field and it never assumes that a number proves a legal issuance.
    """
    for number_field, date_field in TAX_INVOICE_FIELD_PAIRS:
        if not doc_has_field(doc, number_field):
            continue

        number = doc_value(doc, number_field)
        if not number:
            continue

        date = doc_value(doc, date_field) if doc_has_field(doc, date_field) else None
        return number, date, number_field

    return None, None, None


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------


def build_service_tax_snapshot(
    *,
    identity=None,
    registration=None,
    treatment=None,
    treatment_source=TREATMENT_SOURCE_PERSISTED,
    item_rows=None,
    vat_rows=None,
    vat_source=VAT_SOURCE_NONE,
    wht=None,
    retention=None,
    tax_invoice=None,
    company_context=None,
    warnings=None,
    precision=2,
):
    """Build the snapshot from the gathered values.

    This part is pure: it never touches the database and it never writes.
    """
    identity = identity or {}
    wht = wht or {}
    retention = retention or {}
    tax_invoice = tax_invoice or {}
    company_context = company_context or {}
    warnings = list(warnings or [])
    registration = registration or CompanyRegistration()

    classification = classify_supply(item_rows)
    normalized = normalize_vat_treatment(treatment)
    reason = derive_treatment_reason(normalized, registration)

    if not normalized:
        warnings.append(
            _text(
                "The invoice has no VAT treatment. The treatment is derived from the registration."
            )
        )

    base_total, currency_total = sum_vat_rows(vat_rows, precision)
    service_base, service_base_currency = service_base_amount(
        item_rows, classification["service_item_codes"], precision
    )

    service_vat_amount = None
    if classification["classification"] == CLASSIFICATION_SERVICES:
        service_vat_amount = base_total
    elif classification["classification"] == CLASSIFICATION_MIXED:
        warnings.append(
            _text(
                "The invoice mixes services and goods. The VAT of the invoice is not "
                "allocated to the service rows."
            )
        )

    has_service_items = bool(classification["service_item_codes"])
    derived = derive_treatment(
        registration,
        has_service_items=has_service_items,
        is_pos=bool(identity.get("is_pos")),
    )

    if normalized and derived and normalized != derived:
        if normalized not in MANUAL_VAT_TREATMENTS:
            warnings.append(
                _text(
                    "The stored VAT treatment '{0}' differs from the treatment that the "
                    "registration and the supply lead to ('{1}')."
                ).format(normalized, derived)
            )

    if registration.warning:
        warnings.append(registration.warning)

    if normalized == VAT_TREATMENT_EXEMPT and registration.kind == VAT_STATUS_UNKNOWN:
        warnings.append(
            _text(
                "The invoice is exempt but the VAT registration of the company is not "
                "configured. It is not read as a confirmed exemption."
            )
        )

    return ServiceTaxSnapshot(
        sales_invoice=identity.get("sales_invoice"),
        docstatus=_cint(identity.get("docstatus")),
        posting_date=identity.get("posting_date"),
        company=identity.get("company"),
        branch=identity.get("branch"),
        customer=identity.get("customer"),
        currency=identity.get("currency"),
        company_currency=identity.get("company_currency"),
        tax_category=identity.get("tax_category"),
        taxes_and_charges=identity.get("taxes_and_charges"),
        classification=classification["classification"],
        service_item_codes=classification["service_item_codes"],
        goods_item_codes=classification["goods_item_codes"],
        unclassified_item_codes=classification["unclassified_item_codes"],
        is_service_sale=classification["is_service_sale"],
        registration=registration,
        treatment=normalized,
        treatment_source=treatment_source,
        treatment_reason=reason,
        treatment_is_legacy_alias=bool(
            treatment and str(treatment).strip() == VAT_TREATMENT_LEGACY_STANDARD
        ),
        derived_treatment=derived,
        net_total=_flt(identity.get("net_total"), precision),
        eligible_service_base=service_base,
        eligible_service_base_currency=service_base_currency,
        vat_amount=base_total,
        vat_amount_currency=currency_total,
        service_vat_amount=service_vat_amount,
        vat_rate=_vat_rate(vat_rows),
        has_inclusive_vat=any(bool(row.get("is_inclusive")) for row in (vat_rows or [])),
        company_service_business=bool(_cint(company_context.get("service_business"))),
        company_construction_service=bool(_cint(company_context.get("construction_service"))),
        company_branch_code=company_context.get("branch_code"),
        vat_rows=tuple(
            VatTaxRow(
                account_head=row.get("account_head"),
                description=row.get("description"),
                charge_type=row.get("charge_type"),
                rate=_flt(row.get("rate")),
                tax_amount=_flt(row.get("tax_amount"), precision),
                base_tax_amount=_flt(row.get("base_tax_amount"), precision),
                is_inclusive=bool(row.get("is_inclusive")),
            )
            for row in (vat_rows or [])
        ),
        vat_source=vat_source,
        subject_to_wht=bool(_cint(wht.get("subject_to_wht"))),
        wht_percentage=_flt(wht.get("percentage"), precision),
        wht_amount=_flt(wht.get("amount"), precision),
        wht_certificate_required=bool(_cint(wht.get("certificate_required"))),
        subject_to_retention=bool(_cint(retention.get("subject_to_retention"))),
        retention_percentage=_flt(retention.get("percentage"), precision),
        retention_amount=_flt(retention.get("amount"), precision),
        net_total_after_wht=_flt(wht.get("net_total_after_wht"), precision),
        net_total_after_wht_and_retention=_flt(
            retention.get("net_total_after_wht_and_retention"), precision
        ),
        tax_invoice_number=tax_invoice.get("number"),
        tax_invoice_date=tax_invoice.get("date"),
        tax_invoice_number_field=tax_invoice.get("number_field"),
        warnings=tuple(warnings),
    )


def _vat_rate(vat_rows):
    """Return the rate of the VAT rows, when they all share one."""
    rates = {_flt(row.get("rate")) for row in (vat_rows or [])}
    if len(rates) == 1:
        return rates.pop()
    return None


def get_company_context(company, doc=None):
    """Return the tax context of the company.

    The flags of the company are a context for the decision, not a proof that
    every item of the invoice is a service.  The branch code is the branch of
    the VAT registration of the company.
    """
    context = {
        "service_business": 0,
        "construction_service": 0,
        "branch_code": None,
    }
    if not company:
        return context

    fields = [
        fieldname
        for fieldname in (
            "thailand_service_business",
            "construction_service",
            "default_company_branch_code",
        )
        if _company_has_field(fieldname)
    ]
    if fields:
        try:
            rows = frappe.get_all("Company", filters={"name": company}, fields=fields, limit=1)
        except Exception:
            rows = []
        if rows:
            context["service_business"] = _cint(rows[0].get("thailand_service_business"))
            context["construction_service"] = _cint(rows[0].get("construction_service"))
            context["branch_code"] = rows[0].get("default_company_branch_code")

    if doc is not None:
        # The invoice carries the construction flag of the company as well.
        context["construction_service"] = context["construction_service"] or _cint(
            doc_value(doc, "pd_custom_company_construction_service", 0)
        )

    return context


def _company_has_field(fieldname):
    """True when the Company DocType carries the given field."""
    try:
        return bool(frappe.get_meta("Company").has_field(fieldname))
    except Exception:
        return False


def get_service_tax_snapshot(doc, registration=None):
    """Return the tax snapshot of a Sales Invoice.

    The function only reads.  It does not save the invoice, it does not create
    a tax record and it does not create a GL entry.
    """
    company = doc_value(doc, "company")
    posting_date = doc_value(doc, "posting_date")
    currency = doc_value(doc, "currency")

    if registration is None:
        registration = get_company_registration(company, posting_date)

    company_currency = doc_value(doc, "company_currency")
    if not company_currency and company:
        try:
            from erpnext import get_company_currency

            company_currency = get_company_currency(company)
        except Exception:
            company_currency = None

    items = doc_value(doc, "items") or []
    item_codes = [doc_value(row, "item_code") for row in items]
    item_info = get_item_tax_info([code for code in item_codes if code])

    item_rows = []
    for row in items:
        code = doc_value(row, "item_code")
        info = item_info.get(code) or {}
        item_rows.append(
            {
                "item_code": code,
                "is_service": bool(info.get("is_service")),
                "is_stock": bool(info.get("is_stock")),
                "base_net_amount": _flt(doc_value(row, "base_net_amount", 0)),
                "net_amount": _flt(doc_value(row, "net_amount", 0)),
            }
        )

    tax_rows = harmonise_base_amounts(
        collect_tax_rows(doc),
        currency,
        company_currency,
        doc_value(doc, "conversion_rate"),
    )
    company_accounts = get_company_vat_accounts(company)
    account_meta = get_account_meta([row.get("account_head") for row in tax_rows])
    selected_rows, vat_source = select_vat_rows(tax_rows, company_accounts, account_meta)

    treatment = doc_value(doc, VAT_TREATMENT_FIELD)
    treatment_source = TREATMENT_SOURCE_PERSISTED
    if not treatment:
        treatment_source = TREATMENT_SOURCE_DERIVED

    tax_invoice_number, tax_invoice_date, tax_invoice_field = get_tax_invoice_reference(doc)

    warnings = []
    if vat_source == VAT_SOURCE_KEYWORD_FALLBACK:
        warnings.append(
            _text(
                "No row of the invoice matches a VAT account of the company. The VAT "
                "was read from the name of the tax account."
            )
        )

    if rows_without_base_amount(selected_rows):
        warnings.append(
            _text(
                "A VAT row of the invoice carries a tax amount but no base amount. "
                "The VAT of the invoice is not available in the currency of the company."
            )
        )

    identity = {
        "sales_invoice": doc_value(doc, "name"),
        "docstatus": doc_value(doc, "docstatus", 0),
        "posting_date": posting_date,
        "company": company,
        "branch": doc_value(doc, "branch"),
        "customer": doc_value(doc, "customer"),
        "currency": currency,
        "company_currency": company_currency,
        "tax_category": doc_value(doc, "tax_category"),
        "taxes_and_charges": doc_value(doc, "taxes_and_charges"),
        "net_total": doc_value(doc, "base_net_total", 0),
        "is_pos": doc_value(doc, "is_pos", 0),
    }

    return build_service_tax_snapshot(
        identity=identity,
        registration=registration,
        treatment=treatment,
        treatment_source=treatment_source,
        item_rows=item_rows,
        vat_rows=selected_rows,
        vat_source=vat_source,
        wht={
            "subject_to_wht": doc_value(doc, "pd_custom_subject_to_wht", 0),
            "percentage": doc_value(doc, "pd_custom_withholding_tax_pct", 0),
            "amount": doc_value(doc, "pd_custom_withholding_tax_amount", 0),
            "certificate_required": doc_value(doc, "pd_custom_wht_certificate_required", 0),
            "net_total_after_wht": doc_value(doc, "pd_custom_net_total_after_wht", 0),
        },
        retention={
            "subject_to_retention": doc_value(doc, "pd_custom_subject_to_retention", 0),
            "percentage": doc_value(doc, "pd_custom_retention_pct", 0),
            "amount": doc_value(doc, "pd_custom_retention_amount", 0),
            "net_total_after_wht_and_retention": doc_value(
                doc, "pd_custom_net_after_wht_retention", 0
            ),
        },
        tax_invoice={
            "number": tax_invoice_number,
            "date": tax_invoice_date,
            "number_field": tax_invoice_field,
        },
        company_context=get_company_context(company, doc),
        warnings=warnings,
    )
