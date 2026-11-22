"""Per-company VAT registration source for Print Designer.

Print Designer owns the essential Thai VAT behaviour and must work without the
Thai Business Suite app.  The VAT registration of the selling company is still
stored in the ``Thai Company Settings`` DocType, which is owned by TBS and is
*not* part of the eight relocated tax DocTypes.  This module therefore reads it
defensively and turns it into a normalised snapshot that the rest of Print
Designer can rely on.

Rules
-----
* A missing DocType, a missing field, a missing record or an empty value is a
  configuration problem - never a confirmed exemption.
* The stored value is compared case sensitively; a translated display label is
  never compared.
* A status that only applies from a later date is not effective for a
  backdated transaction.
* The Thai Tax Settings singleton is a different DocType.  It is never read as
  the registration of a company.

The module never imports TBS: on a site without TBS the DocType simply does
not exist and the snapshot reports the missing configuration.
"""

from dataclasses import dataclass

import frappe
from frappe import _


def _text(message: str) -> str:
    # Return the translated message - also without a site context.
    try:
        return _(message)
    except Exception:
        return message


# --- the persisted source --------------------------------------------------

THAI_COMPANY_SETTINGS_DOCTYPE = "Thai Company Settings"
COMPANY_VAT_STATUS_FIELD = "vat_registration_status"
COMPANY_VAT_EFFECTIVE_FROM_FIELD = "vat_status_effective_from"
COMPANY_VAT_NON_REGISTRATION_REASON_FIELD = "vat_non_registration_reason"
COMPANY_VAT_REGISTRATION_NUMBER_FIELD = "vat_registration_number"
COMPANY_BRANCH_CODE_FIELD = "branch_code"

#: The stored values of ``Thai Company Settings.vat_registration_status``.
COMPANY_VAT_STATUS_UNCONFIRMED = "Unconfirmed"
COMPANY_VAT_STATUS_NOT_REGISTERED = "Not Registered"
COMPANY_VAT_STATUS_REGISTERED = "Registered"

#: The kinds the resolver distinguishes.
VAT_STATUS_REGISTERED = "registered"
VAT_STATUS_NOT_REGISTERED = "not_registered"
VAT_STATUS_UNCONFIRMED = "unconfirmed"
VAT_STATUS_UNKNOWN = "unknown"

#: Where the snapshot came from - used for the audit trail.
SOURCE_SETTINGS = "thai_company_settings"
SOURCE_NO_COMPANY = "no_company"
SOURCE_MISSING_SCHEMA = "missing_schema"
SOURCE_MISSING_FIELD = "missing_field"
SOURCE_MISSING_RECORD = "missing_record"
SOURCE_EMPTY_STATUS = "empty_status"


@dataclass(frozen=True)
class CompanyRegistration:
    """The VAT registration of one company at one point in time."""

    company: str | None = None
    #: The raw stored value (``Registered`` / ``Not Registered`` / ``Unconfirmed``).
    status: str | None = None
    #: The normalised kind, see the ``VAT_STATUS_*`` constants.
    kind: str = VAT_STATUS_UNKNOWN
    effective_from: str | None = None
    #: True when the status applies to the date of the transaction.
    is_effective: bool = False
    non_registration_reason: str | None = None
    registration_number: str | None = None
    branch_code: str | None = None
    #: Where the values were read from, see the ``SOURCE_*`` constants.
    source: str = SOURCE_MISSING_SCHEMA
    #: A message for the accountant when the status cannot be used as it is.
    warning: str | None = None

    @property
    def is_registered(self) -> bool:
        """True when the company is confirmed as registered."""
        return self.kind == VAT_STATUS_REGISTERED

    @property
    def is_not_registered(self) -> bool:
        """True when the company is confirmed as not registered."""
        return self.kind == VAT_STATUS_NOT_REGISTERED

    @property
    def is_unconfirmed(self) -> bool:
        """True when the registration status is not confirmed yet."""
        return self.kind == VAT_STATUS_UNCONFIRMED

    @property
    def is_exempt_seller(self) -> bool:
        """True when the seller is outside the VAT system.

        An unconfirmed status is *not* a confirmed exemption, but the historic
        behaviour of the site treats it like one.  The distinction is kept in
        :attr:`kind` so that the audit reason can tell them apart.
        """
        return self.kind in (VAT_STATUS_NOT_REGISTERED, VAT_STATUS_UNCONFIRMED)

    def as_dict(self) -> dict:
        """Return the snapshot as a plain dictionary."""
        return {
            "company": self.company,
            "status": self.status,
            "kind": self.kind,
            "effective_from": self.effective_from,
            "is_effective": self.is_effective,
            "non_registration_reason": self.non_registration_reason,
            "registration_number": self.registration_number,
            "branch_code": self.branch_code,
            "source": self.source,
            "warning": self.warning,
        }


def classify_vat_status(status) -> str:
    """Map a stored registration status to the kind the resolver works with.

    The stored values are ``Unconfirmed``, ``Not Registered`` and ``Registered``.
    The comparison is case sensitive and a translated display label is never
    compared.
    """
    value = str(status or "").strip()
    if value == COMPANY_VAT_STATUS_REGISTERED:
        return VAT_STATUS_REGISTERED
    if value == COMPANY_VAT_STATUS_NOT_REGISTERED:
        return VAT_STATUS_NOT_REGISTERED
    if value == COMPANY_VAT_STATUS_UNCONFIRMED:
        return VAT_STATUS_UNCONFIRMED
    return VAT_STATUS_UNKNOWN


def vat_status_is_effective(status, effective_from, posting_date) -> bool:
    """False when the confirmed status does not apply to the date yet.

    A backdated transaction must not be judged with a status that only applies
    from a later date on.
    """
    if not effective_from or not posting_date:
        return True

    try:
        from frappe.utils import getdate

        from_date = getdate(str(posting_date))
        effective = getdate(str(effective_from))
    except Exception:
        return True

    if not from_date or not effective:
        return True

    return from_date >= effective


def get_company_vat_status(company) -> tuple:
    """Return ``(status, effective_from)`` of the selling company.

    ``(None, None)`` is returned when the schema is not deployed, when the
    company has no settings record or when the status is empty.  The caller
    treats that as a configuration error - never as a confirmed exemption.
    """
    if not company:
        return None, None

    if not frappe.db.exists("DocType", THAI_COMPANY_SETTINGS_DOCTYPE):
        return None, None

    try:
        meta = frappe.get_meta(THAI_COMPANY_SETTINGS_DOCTYPE)
    except Exception:
        return None, None

    if not meta.has_field(COMPANY_VAT_STATUS_FIELD):
        return None, None

    rows = frappe.get_all(
        THAI_COMPANY_SETTINGS_DOCTYPE,
        filters={"company": company},
        fields=[COMPANY_VAT_STATUS_FIELD, COMPANY_VAT_EFFECTIVE_FROM_FIELD],
        limit=1,
    )
    if not rows:
        return None, None

    row = rows[0]
    return row.get(COMPANY_VAT_STATUS_FIELD), row.get(COMPANY_VAT_EFFECTIVE_FROM_FIELD)


def get_company_registration(company, posting_date=None) -> CompanyRegistration:
    """Return the VAT registration snapshot of ``company``.

    The snapshot is read from ``Thai Company Settings`` when the DocType is
    deployed.  Every missing piece is reported through :attr:`source` and
    :attr:`warning` - it never turns into a confirmed exemption.
    """
    if not company:
        return CompanyRegistration(
            company=None,
            kind=VAT_STATUS_UNKNOWN,
            source=SOURCE_NO_COMPANY,
            warning=_text("No company on the document - the VAT registration is unknown."),
        )

    if not frappe.db.exists("DocType", THAI_COMPANY_SETTINGS_DOCTYPE):
        return CompanyRegistration(
            company=company,
            kind=VAT_STATUS_UNKNOWN,
            source=SOURCE_MISSING_SCHEMA,
            warning=_text(
                "The DocType '{0}' is not installed. The VAT registration of company "
                "'{1}' cannot be read."
            ).format(THAI_COMPANY_SETTINGS_DOCTYPE, company),
        )

    try:
        meta = frappe.get_meta(THAI_COMPANY_SETTINGS_DOCTYPE)
    except Exception:
        return CompanyRegistration(
            company=company,
            kind=VAT_STATUS_UNKNOWN,
            source=SOURCE_MISSING_SCHEMA,
            warning=_text("The VAT registration of company '{0}' cannot be read.").format(company),
        )

    if not meta.has_field(COMPANY_VAT_STATUS_FIELD):
        return CompanyRegistration(
            company=company,
            kind=VAT_STATUS_UNKNOWN,
            source=SOURCE_MISSING_FIELD,
            warning=_text(
                "'{0}' has no field '{1}'. The VAT registration of company '{2}' cannot be read."
            ).format(
                THAI_COMPANY_SETTINGS_DOCTYPE,
                COMPANY_VAT_STATUS_FIELD,
                company,
            ),
        )

    fields = [COMPANY_VAT_STATUS_FIELD, COMPANY_VAT_EFFECTIVE_FROM_FIELD]
    for optional in (
        COMPANY_VAT_NON_REGISTRATION_REASON_FIELD,
        COMPANY_VAT_REGISTRATION_NUMBER_FIELD,
        COMPANY_BRANCH_CODE_FIELD,
    ):
        if meta.has_field(optional):
            fields.append(optional)

    rows = frappe.get_all(
        THAI_COMPANY_SETTINGS_DOCTYPE,
        filters={"company": company},
        fields=fields,
        limit=1,
    )
    if not rows:
        return CompanyRegistration(
            company=company,
            kind=VAT_STATUS_UNKNOWN,
            source=SOURCE_MISSING_RECORD,
            warning=_text(
                "Company '{0}' has no '{1}' record. The VAT registration is not "
                "configured; it is never read as a confirmed exemption."
            ).format(company, THAI_COMPANY_SETTINGS_DOCTYPE),
        )

    row = rows[0]
    status = row.get(COMPANY_VAT_STATUS_FIELD)
    effective_from = row.get(COMPANY_VAT_EFFECTIVE_FROM_FIELD)
    kind = classify_vat_status(status)

    if kind == VAT_STATUS_UNKNOWN:
        return CompanyRegistration(
            company=company,
            status=status,
            kind=VAT_STATUS_UNKNOWN,
            effective_from=effective_from,
            is_effective=False,
            non_registration_reason=row.get(COMPANY_VAT_NON_REGISTRATION_REASON_FIELD),
            registration_number=row.get(COMPANY_VAT_REGISTRATION_NUMBER_FIELD),
            branch_code=row.get(COMPANY_BRANCH_CODE_FIELD),
            source=SOURCE_EMPTY_STATUS if not status else SOURCE_SETTINGS,
            warning=_text(
                "The VAT registration status of company '{0}' is not a valid value. "
                "It is never read as a confirmed exemption."
            ).format(company),
        )

    is_effective = vat_status_is_effective(status, effective_from, posting_date)
    warning = None
    if not is_effective:
        warning = _text(
            "The VAT registration status of company '{0}' only applies from {1}. "
            "The transaction is dated before that date."
        ).format(company, effective_from)
    elif kind == VAT_STATUS_UNCONFIRMED:
        warning = _text(
            "The VAT registration status of company '{0}' is not confirmed. "
            "Confirm it before the next VAT filing."
        ).format(company)

    return CompanyRegistration(
        company=company,
        status=status,
        kind=kind,
        effective_from=effective_from,
        is_effective=is_effective,
        non_registration_reason=row.get(COMPANY_VAT_NON_REGISTRATION_REASON_FIELD),
        registration_number=row.get(COMPANY_VAT_REGISTRATION_NUMBER_FIELD),
        branch_code=row.get(COMPANY_BRANCH_CODE_FIELD),
        source=SOURCE_SETTINGS,
        warning=warning,
    )


def is_company_vat_exempt(company, posting_date=None) -> bool:
    """True when the selling company is outside the VAT system.

    This mirrors the historic behaviour of the site: a company that is not
    registered and a company whose status is not confirmed yet are both treated
    as exempt sellers.  The audit reason of the tax contract keeps them apart.
    """
    registration = get_company_registration(company, posting_date)
    return registration.is_exempt_seller
