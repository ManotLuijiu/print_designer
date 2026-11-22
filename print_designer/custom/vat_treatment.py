"""The VAT treatment resolver of Print Designer.

Print Designer owns the essential Thai VAT behaviour.  The VAT treatment of a
supply is the decision that every other part relies on: the tax rows of the
invoice, the Output VAT Undue ledger and the VAT reports all read it.

This module is the authoritative implementation of that decision.  It works
without the Thai Business Suite app: it only uses ERPNext master data (the
Sales Taxes and Charges Template and the Tax Category) and the VAT
registration of the selling company, which is read by
:mod:`print_designer.custom.thai_company_registration`.

The precedence of the decision
------------------------------

1. the company is not registered (or its registration is unconfirmed)
   -> ``Exempt from VAT``
2. the selected tax template is the exempt template
   -> ``Exempt from VAT``
3. the selected tax template is the zero rated template
   -> ``Zero-rated for Export``
4. the selected tax template is the "output VAT undue" template
   -> ``VAT Undue``
5. a taxable template -> ``VAT Due``

A missing schema, a missing settings record or an invalid status is a
configuration error: a warning is returned and the decision falls back to the
Tax Category - never to a silent exemption.

A deliberate manual choice (``Exempt from VAT`` /
``Zero-rated for Export``) is never overwritten.
"""

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from print_designer.custom.thai_company_registration import (
    VAT_STATUS_NOT_REGISTERED,
    VAT_STATUS_UNCONFIRMED,
    VAT_STATUS_UNKNOWN,
    classify_vat_status,
    get_company_vat_status,
    vat_status_is_effective,
)

# --- Tax Category values used by the Thai VAT rules -------------------------

EXEMPT_TAX_CATEGORY = "Exempt"
ZERO_RATED_TAX_CATEGORY = "Zero-Rated"
UNDUE_TAX_CATEGORY = "Services Tax"

# --- Behaviours -------------------------------------------------------------

BEHAVIOUR_EXEMPT = "exempt"
BEHAVIOUR_ZERO_RATED = "zero_rated"
BEHAVIOUR_UNDUE = "undue"
BEHAVIOUR_STANDARD = "standard"

DEFAULT_TAX_TEMPLATE_DOCTYPE = "Sales Taxes and Charges Template"
TAXES_CHILD_DOCTYPE = "Sales Taxes and Charges"

# Generic (site independent) labels of the VAT templates.
#
# Every site names its templates differently - the label is the title of the
# template, the name usually carries the company suffix ("VAT Exempt",
# "VAT Exempt - <company>", ...).  Only these labels are matched, never a
# full template name, so the rules work on every site.
EXEMPT_TEMPLATE_LABEL = "VAT Exempt"
ZERO_RATED_TEMPLATE_LABEL = "Zero-Rated"
UNDUE_TEMPLATE_LABEL = "Output VAT Undue"

# Loose keywords, used as the last resort when a site uses a completely
# different wording.
EXEMPT_TEMPLATE_KEYWORD = "exempt"
ZERO_RATED_TEMPLATE_KEYWORD = "zero-rated"
UNDUE_TEMPLATE_KEYWORD = "undue"

#: A label that negates the exemption is not an exempt template: a company
#: that offers "Output VAT Non-exempt" must not have it applied to an
#: exempt supply.
NEGATED_EXEMPT_KEYWORDS = ("non-exempt", "non exempt", "not exempt")

# --- VAT treatment (the "VAT Treatment" field of the transaction) -----------

VAT_TREATMENT_FIELD = "pd_custom_vat_treatment"

#: Canonical stored value of a taxable supply whose VAT is due (the tax
#: point has been reached).  Replaces the legacy value "Standard VAT".
VAT_TREATMENT_DUE = "VAT Due"

#: Legacy value that is still stored in documents created before the rename.
#: It is read (and understood as "VAT Due"), but it is never written again.
VAT_TREATMENT_LEGACY_STANDARD = "Standard VAT"

#: Kept for the modules that imported the old constant name.
VAT_TREATMENT_STANDARD = VAT_TREATMENT_DUE

VAT_TREATMENT_UNDUE = "VAT Undue"
VAT_TREATMENT_EXEMPT = "Exempt from VAT"
VAT_TREATMENT_ZERO_RATED = "Zero-rated for Export"

#: Every stored value that means "the VAT is due".
VAT_DUE_TREATMENTS = (VAT_TREATMENT_DUE, VAT_TREATMENT_LEGACY_STANDARD)

#: Deliberate manual choices - they are never overwritten.
MANUAL_VAT_TREATMENTS = (VAT_TREATMENT_EXEMPT, VAT_TREATMENT_ZERO_RATED)

#: Tax Category -> VAT treatment.
TAX_CATEGORY_VAT_TREATMENT = {
    EXEMPT_TAX_CATEGORY: VAT_TREATMENT_EXEMPT,
    ZERO_RATED_TAX_CATEGORY: VAT_TREATMENT_ZERO_RATED,
    UNDUE_TAX_CATEGORY: VAT_TREATMENT_UNDUE,
}


# ---------------------------------------------------------------------------
# Pure helpers (unit testable without a site)
# ---------------------------------------------------------------------------


def resolve_behaviour(tax_category: str | None) -> str:
    """Map a Tax Category value to the Thai VAT behaviour.

    ``Exempt``     -> no VAT row at all (customer outside the VAT system)
    ``Zero-Rated`` -> 0% VAT row (export supply, still inside the VAT system)
    ``Services Tax`` -> output VAT that is not yet due (services supplied to
    a customer that cannot deduct the VAT); the VAT row keeps the normal
    rate but sits on the "output VAT undue" account.
    anything else  -> standard ERPNext behaviour
    """
    if not tax_category:
        return BEHAVIOUR_STANDARD

    category = str(tax_category).strip()
    if category == EXEMPT_TAX_CATEGORY:
        return BEHAVIOUR_EXEMPT
    if category == ZERO_RATED_TAX_CATEGORY:
        return BEHAVIOUR_ZERO_RATED
    if category == UNDUE_TAX_CATEGORY:
        return BEHAVIOUR_UNDUE
    return BEHAVIOUR_STANDARD


def template_label_matches(template: dict[str, Any], label: str) -> bool:
    """True when the title (or the name without the company suffix) equals the label.

    The title of a Sales Taxes and Charges Template is the site independent
    label ("VAT Exempt"), while the name carries the company suffix
    ("VAT Exempt - <company>").  Both are compared, so the lookup works on
    every site without hardcoding a template name.
    """
    label = (label or "").strip().lower()
    if not label:
        return False

    title = (template.get("title") or "").strip().lower()
    if title == label:
        return True

    name = (template.get("name") or "").strip().lower()
    if name == label:
        return True

    # "VAT Exempt - <company>" -> the part before the company suffix
    return name.split(" - ")[0].strip() == label


def find_zero_rated_template(
    templates: list[dict[str, Any]] | None,
    is_zero_rated: Any = None,
) -> dict[str, Any] | None:
    """Pick the zero-rated template out of a list of template rows.

    Preference order:

    1. the template whose ``tax_category`` is ``Zero-Rated`` (explicit),
    2. the template whose label mentions ``Zero-Rated`` (fallback for sites
       where the templates were never tagged with a tax category),
    3. the only template whose tax rows are all 0% (last resort, only when
       the choice is unambiguous).

    ``is_zero_rated`` is an optional callable ``template_name -> bool``; it
    is injected so the lookup stays unit testable without a database.
    """
    if not templates:
        return None

    for template in templates:
        if template.get("tax_category") == ZERO_RATED_TAX_CATEGORY:
            return template

    for template in templates:
        label = f"{template.get('title') or ''} {template.get('name') or ''}".lower()
        if ZERO_RATED_TEMPLATE_KEYWORD in label:
            return template

    if is_zero_rated:
        candidates = [template for template in templates if is_zero_rated(template.get("name"))]
        if len(candidates) == 1:
            return candidates[0]

    return None


def template_starts_with_label(template: dict[str, Any], label: str) -> bool:
    """True when the title (or the name without the company suffix) starts
    with the label.

    Some sites add the rate to the label ("Output VAT Undue 7%"), so the
    label is matched as a prefix.
    """
    label = (label or "").strip().lower()
    if not label:
        return False

    title = (template.get("title") or "").strip().lower()
    if title.startswith(label):
        return True

    name = (template.get("name") or "").strip().lower()
    if name.startswith(label):
        return True

    return name.split(" - ")[0].strip().startswith(label)


def find_undue_template(
    templates: list[dict[str, Any]] | None,
    has_non_zero_rate: Any = None,
) -> dict[str, Any] | None:
    """Pick the "output VAT undue" template out of a list of template rows.

    The undue template carries the **normal** VAT rate - the VAT is not due
    yet, it is not zero rated - so a candidate whose rows are all 0% is
    rejected on every path (posting 0% VAT would drop the VAT of a taxable
    supply).

    Preference order:

    1. the template whose ``tax_category`` is ``Services Tax`` (explicit),
    2. the template labelled ``Output VAT Undue`` (site independent label,
       the rate may be appended to the label),
    3. a template that mentions ``undue``.

    ``has_non_zero_rate`` is an optional callable ``template_name -> bool``;
    it is injected so the lookup stays unit testable without a database.
    """
    if not templates:
        return None

    def _acceptable(template: dict[str, Any]) -> bool:
        """True when the template may be used (it carries a normal rate)."""
        if not has_non_zero_rate:
            return True
        return bool(has_non_zero_rate(template.get("name")))

    for template in templates:
        if template.get("tax_category") == UNDUE_TAX_CATEGORY and _acceptable(template):
            return template

    for template in templates:
        if template_starts_with_label(template, UNDUE_TEMPLATE_LABEL) and _acceptable(template):
            return template

    candidates = [
        template
        for template in templates
        if UNDUE_TEMPLATE_KEYWORD
        in f"{template.get('title') or ''} {template.get('name') or ''}".lower()
    ]
    for template in candidates:
        if _acceptable(template):
            return template

    return None


def is_negated_exempt_template(template: dict[str, Any]) -> bool:
    """True when the label of a template negates the exemption.

    "Non-exempt" and "Not exempt" are not exempt templates.  The keyword
    "exempt" is inside those labels, so the negation has to be checked
    before such a template is used for an exempt supply.
    """
    label = f"{template.get('title') or ''} {template.get('name') or ''}".lower()
    return any(keyword in label for keyword in NEGATED_EXEMPT_KEYWORDS)


def find_exempt_template(
    templates: list[dict[str, Any]] | None,
    is_zero_rated: Any = None,
) -> dict[str, Any] | None:
    """Pick the exempt template out of a list of template rows.

    Preference order:

    1. the template whose ``tax_category`` is ``Exempt`` (explicit),
    2. the template labelled ``VAT Exempt`` (site independent label),
    3. any template that mentions ``exempt``.  When several templates match,
       the first one whose tax rows are all 0% wins - a template with a real
       VAT rate would be wrong for an exempt supply.

    A template whose label negates the exemption ("Non-exempt", "Not
    exempt") is never used - it is not an exempt template.

    ``is_zero_rated`` is an optional callable ``template_name -> bool``; it
    is injected so the lookup stays unit testable without a database.
    """
    if not templates:
        return None

    for template in templates:
        if template.get("tax_category") == EXEMPT_TAX_CATEGORY:
            return template

    for template in templates:
        if template_label_matches(template, EXEMPT_TEMPLATE_LABEL):
            return template

    candidates = [
        template
        for template in templates
        if EXEMPT_TEMPLATE_KEYWORD
        in f"{template.get('title') or ''} {template.get('name') or ''}".lower()
        and not is_negated_exempt_template(template)
    ]
    if not candidates:
        return None

    if is_zero_rated:
        for template in candidates:
            if is_zero_rated(template.get("name")):
                return template

    return candidates[0]


def get_company_tax_templates(
    company: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> list[dict[str, Any]]:
    """Return the enabled tax templates of a company."""
    if not company:
        return []

    templates: list[dict[str, Any]] = frappe.get_all(
        doctype,
        filters={"company": company, "disabled": 0},
        fields=["name", "title", "tax_category", "is_default"],
        order_by="name",
    )
    return templates


def get_zero_rated_template(
    company: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> str | None:
    """Return the name of the zero-rated tax template of a company."""
    templates = get_company_tax_templates(company, doctype)
    template = find_zero_rated_template(
        templates,
        is_zero_rated=lambda name: template_is_zero_rated(name, doctype),
    )
    return str(template.get("name")) if template else None


def to_float(value: Any) -> float:
    """Safe float conversion - a broken template row must not raise."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def template_is_zero_rated(
    template: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> bool:
    """True when every tax row of a template has a 0% rate."""
    rows = get_template_taxes(template, doctype)
    if not rows:
        return False

    return all(to_float(row.get("rate")) == 0 for row in rows)


def template_has_non_zero_rate(
    template: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> bool:
    """True when at least one tax row of a template has a rate above 0%."""
    rows = get_template_taxes(template, doctype)
    if not rows:
        return False

    return any(to_float(row.get("rate")) != 0 for row in rows)


def get_undue_template(
    company: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> str | None:
    """Return the name of the "output VAT undue" template of a company.

    The template is found by its tax category, by the site independent label
    ``Output VAT Undue`` or - as the last resort - by any template that
    mentions ``undue`` and carries a normal (non zero) tax rate.
    """
    templates = get_company_tax_templates(company, doctype)
    template = find_undue_template(
        templates,
        has_non_zero_rate=lambda name: template_has_non_zero_rate(name, doctype),
    )
    return str(template.get("name")) if template else None


def get_exempt_template(
    company: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> str | None:
    """Return the name of the exempt tax template of a company.

    The template is found by its tax category, by the site independent label
    ``VAT Exempt`` or - as the last resort - by any template that mentions
    ``exempt`` and only carries 0% tax rows.
    """
    templates = get_company_tax_templates(company, doctype)
    template = find_exempt_template(
        templates,
        is_zero_rated=lambda name: template_is_zero_rated(name, doctype),
    )
    return str(template.get("name")) if template else None


def get_default_tax_template(
    company: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> str | None:
    """Return the name of the company default tax template."""
    if not company:
        return None

    template: Any = frappe.db.get_value(
        doctype, {"company": company, "is_default": 1, "disabled": 0}
    )
    return str(template) if template else None


def get_template_taxes(
    template: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> list[dict[str, Any]]:
    """Return the tax rows of a tax template."""
    if not template:
        return []

    rows: list[dict[str, Any]] = frappe.get_all(
        TAXES_CHILD_DOCTYPE,
        filters={"parent": template, "parenttype": doctype},
        fields=[
            "charge_type",
            "account_head",
            "rate",
            "description",
            "cost_center",
            "included_in_print_rate",
            "included_in_paid_amount",
        ],
        order_by="idx",
    )
    return rows


def get_template_tax_accounts(template: str | None) -> list[str]:
    """Return the account heads used by a tax template."""
    accounts = [row.get("account_head") for row in get_template_taxes(template)]
    return [str(account) for account in accounts if account]


def is_exempt_vat_status(status: Any) -> bool:
    """True for the statuses the user's rule treats as "not registered"."""
    return classify_vat_status(status) in (
        VAT_STATUS_NOT_REGISTERED,
        VAT_STATUS_UNCONFIRMED,
    )


def classify_tax_template(
    template: str | None,
    company: str | None,
    doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE,
) -> str:
    """Classify a Sales Taxes and Charges Template.

    Returns ``"exempt"``, ``"zero_rated"``, ``"undue"`` or ``"due"``.
    """
    if not template:
        return "due"

    exempt = get_exempt_template(company, doctype)
    if exempt and template == exempt:
        return "exempt"

    zero_rated = get_zero_rated_template(company, doctype)
    if zero_rated and template == zero_rated:
        return "zero_rated"

    undue = get_undue_template(company, doctype)
    if undue and template == undue:
        return "undue"

    return "due"


def evaluate_vat_status(
    company: str | None,
    status: Any,
    status_effective_from: Any,
    posting_date: Any,
) -> tuple[str, str | None]:
    """Return ``(kind, warning)`` for the VAT registration status.

    The kind is one of the ``VAT_STATUS_*`` values.  A warning is returned
    when the status cannot be used as it is: it does not apply to the date
    of the transaction yet, it is not a valid value, or it is not
    configured at all.
    """
    kind = classify_vat_status(status)

    if status and not vat_status_is_effective(status, status_effective_from, posting_date):
        # The confirmed status does not apply to this (backdated)
        # transaction yet - the template and the Tax Category decide.
        return VAT_STATUS_UNKNOWN, _(
            "The VAT registration status of company '{0}' only applies from {1}. "
            "The VAT treatment is derived from the tax template and the Tax Category."
        ).format(company, status_effective_from)

    if kind == VAT_STATUS_NOT_REGISTERED:
        return kind, None

    if kind == VAT_STATUS_UNCONFIRMED:
        return kind, _(
            "The VAT registration status of company '{0}' is not confirmed. "
            "Confirm it before the next VAT filing."
        ).format(company)

    if kind == VAT_STATUS_UNKNOWN:
        if status:
            return kind, _(
                "The VAT registration status of company '{0}' ('{1}') is not a valid value. "
                "The VAT treatment is derived from the tax template and the Tax Category."
            ).format(company, status)

        if company:
            # No settings record, no deployed field or an empty status: the
            # registration of the company is not configured.  It is never read
            # as a confirmed exemption, but the accountant has to see it.
            return kind, _(
                "The VAT registration status of company '{0}' is not configured. "
                "Set it in Thai Company Settings; until then the VAT treatment is "
                "derived from the tax template and the Tax Category."
            ).format(company)

    return kind, None


def treatment_from_template_and_category(
    template_kind: str,
    tax_category: str | None,
    is_pos: Any,
    has_service_item: bool,
) -> str:
    """The treatment the tax template and the Tax Category lead to."""
    if template_kind == "exempt":
        return VAT_TREATMENT_EXEMPT

    if template_kind == "zero_rated" and not is_pos:
        return VAT_TREATMENT_ZERO_RATED

    if template_kind == "undue" and not is_pos:
        return VAT_TREATMENT_UNDUE

    # No (or a standard) template: the Tax Category of the supply decides.
    behaviour = resolve_behaviour(tax_category)
    if behaviour == BEHAVIOUR_EXEMPT:
        return VAT_TREATMENT_EXEMPT
    if behaviour == BEHAVIOUR_ZERO_RATED and not is_pos:
        return VAT_TREATMENT_ZERO_RATED
    if behaviour == BEHAVIOUR_UNDUE and not is_pos:
        return VAT_TREATMENT_UNDUE

    # A service is not subject to the VAT before the payment is received,
    # but only a taxable supply can be undue.
    if has_service_item and not is_pos:
        return VAT_TREATMENT_UNDUE

    return VAT_TREATMENT_DUE


def resolve_vat_treatment(
    company: str | None = None,
    tax_template: str | None = None,
    tax_category: str | None = None,
    posting_date: Any = None,
    is_pos: Any = False,
    has_service_item: bool = False,
    status: Any = None,
    status_effective_from: Any = None,
    template_kind: str | None = None,
) -> tuple[str, str | None]:
    """Return ``(treatment, warning)`` for a supply.

    This is the one authoritative decision; the browser scripts mirror it.

    The precedence (the decision the user requested):

    1. the company is not registered (or its registration is unconfirmed)
       -> ``Exempt from VAT``
    2. the selected tax template is the exempt template
       -> ``Exempt from VAT``
    3. the selected tax template is the zero rated template
       -> ``Zero-rated for Export``
    4. the selected tax template is the "output VAT undue" template
       -> ``VAT Undue``
    5. a taxable template -> ``VAT Due``

    :param status: the VAT registration status of the company (read from the
            database when it is not given)
    :param template_kind: the classification of the tax template ("exempt",
            "zero_rated", "undue" or "due"); it is read from the database when it
            is not given

    A missing schema, a missing settings record or an invalid status is a
    configuration error: a warning is returned and the decision falls back
    to the Tax Category - never to a silent exemption.
    """
    if status is None and status_effective_from is None:
        status, status_effective_from = get_company_vat_status(company)

    kind, warning = evaluate_vat_status(company, status, status_effective_from, posting_date)

    if kind == VAT_STATUS_NOT_REGISTERED:
        return VAT_TREATMENT_EXEMPT, None

    if kind == VAT_STATUS_UNCONFIRMED:
        return VAT_TREATMENT_EXEMPT, warning

    template_kind = template_kind or classify_tax_template(tax_template, company)

    treatment = treatment_from_template_and_category(
        template_kind, tax_category, is_pos, has_service_item
    )

    return treatment, warning


def get_template_doctype(doc: Any) -> str:
    """Return the Sales Taxes and Charges Template doctype of the document."""
    field = doc.meta.get_field("taxes_and_charges")
    if field and field.options:
        return str(field.options)

    return DEFAULT_TAX_TEMPLATE_DOCTYPE


def resolve_effective_tax_template(doc: Any) -> str | None:
    """Return the tax template the Thai rules apply to the document.

    It is the template that is already on the document, unless the VAT
    registration of the selling company or the Tax Category of the supply
    asks for another one.
    """
    doctype = get_template_doctype(doc)
    company = doc.get("company")
    status, effective_from = get_company_vat_status(company)
    posting_date = doc.get("posting_date") or doc.get("transaction_date")

    if is_exempt_vat_status(status) and vat_status_is_effective(
        status, effective_from, posting_date
    ):
        return get_exempt_template(company, doctype)

    behaviour = resolve_behaviour(doc.get("tax_category"))

    if behaviour == BEHAVIOUR_EXEMPT:
        return get_exempt_template(company, doctype)
    if behaviour == BEHAVIOUR_ZERO_RATED and not doc.get("is_pos"):
        return get_zero_rated_template(company, doctype)
    if behaviour == BEHAVIOUR_UNDUE and not doc.get("is_pos"):
        return get_undue_template(company, doctype)

    return doc.get("taxes_and_charges") or get_default_tax_template(company, doctype)


def resolve_document_vat_treatment(doc: Any) -> tuple[str, str | None]:
    """Return ``(treatment, warning)`` for a transaction document."""
    status, effective_from = get_company_vat_status(doc.get("company"))

    return resolve_vat_treatment(
        company=doc.get("company"),
        tax_template=resolve_effective_tax_template(doc),
        tax_category=doc.get("tax_category"),
        posting_date=doc.get("posting_date") or doc.get("transaction_date"),
        is_pos=doc.get("is_pos"),
        status=status,
        status_effective_from=effective_from,
    )


@frappe.whitelist()
def get_tax_category_setup(
    company: str | None, doctype: str = DEFAULT_TAX_TEMPLATE_DOCTYPE
) -> dict[str, Any]:
    """Payload used by ``public/js/thai_tax_category.js``.

    Returns the exempt and the zero-rated template (with their 0% rows) and
    the company default template (with its rows) so the client can apply the
    same rules as the server without a round trip per keystroke.
    """
    zero_rated = get_zero_rated_template(company, doctype)
    exempt = get_exempt_template(company, doctype)
    undue = get_undue_template(company, doctype)
    default = get_default_tax_template(company, doctype)
    status, effective_from = get_company_vat_status(company)

    return {
        "exempt_category": EXEMPT_TAX_CATEGORY,
        "zero_rated_category": ZERO_RATED_TAX_CATEGORY,
        "undue_category": UNDUE_TAX_CATEGORY,
        "exempt_template": exempt,
        "exempt_taxes": get_template_taxes(exempt, doctype),
        "zero_rated_template": zero_rated,
        "zero_rated_taxes": get_template_taxes(zero_rated, doctype),
        "undue_template": undue,
        "undue_taxes": get_template_taxes(undue, doctype),
        "default_template": default,
        "default_taxes": get_template_taxes(default, doctype),
        "vat_registration_status": status,
        "vat_status_effective_from": (str(effective_from) if effective_from else None),
        "vat_treatments": {
            "due": VAT_TREATMENT_DUE,
            "undue": VAT_TREATMENT_UNDUE,
            "exempt": VAT_TREATMENT_EXEMPT,
            "zero_rated": VAT_TREATMENT_ZERO_RATED,
            "legacy_standard": VAT_TREATMENT_LEGACY_STANDARD,
        },
    }


@frappe.whitelist()
def get_vat_treatment_decision(
    company: str | None = None,
    tax_template: str | None = None,
    tax_category: str | None = None,
    posting_date: str | None = None,
    current: str | None = None,
    has_service_item: Any = 0,
) -> dict[str, Any]:
    """Return the VAT treatment the server would set on a document.

    The browser scripts mirror this decision instead of re-implementing it.
    A deliberate manual choice (``Exempt from VAT`` /
    ``Zero-rated for Export``) is never overwritten, so it is returned
    unchanged.
    """
    if current in MANUAL_VAT_TREATMENTS:
        return {
            "treatment": current,
            "warning": None,
            "vat_registration_status": None,
            "vat_status_effective_from": None,
        }

    status, effective_from = get_company_vat_status(company)

    treatment, warning = resolve_vat_treatment(
        company=company,
        tax_template=tax_template,
        tax_category=tax_category,
        posting_date=posting_date,
        has_service_item=bool(cint(has_service_item)),
        status=status,
        status_effective_from=effective_from,
    )

    return {
        "treatment": treatment,
        "warning": warning,
        "vat_registration_status": status,
        "vat_status_effective_from": (str(effective_from) if effective_from else None),
    }
