"""Tests for the background tax contract of a Sales Invoice (SI-01).

``print_designer/custom/sales_invoice_tax_contract.py`` is the one
authoritative, read only contract between a Sales Invoice and the VAT
tracking ledger and the VAT reports.

The tests cover the matrix of the plan:

* a registered company with a deferred service supply,
* a company that is not registered,
* an exempt supply of a registered company,
* a zero rated supply,
* a supply whose VAT is already due,
* the legacy value ``Standard VAT``,
* an unconfirmed, a missing and a not yet effective registration,
* a mixed invoice and a non stock item that is not a service,
* VAT next to an unrelated charge,
* withholding tax and retention,
* a foreign currency and the rounding of the amounts.

Reading the contract must never save the invoice and must never create a tax
record or a GL entry.
"""

import unittest

import frappe

from print_designer.custom.sales_invoice_tax_contract import (
    CLASSIFICATION_GOODS,
    CLASSIFICATION_MIXED,
    CLASSIFICATION_SERVICES,
    CLASSIFICATION_UNKNOWN,
    REASON_ALREADY_DUE,
    REASON_DEFERRED_SERVICE,
    REASON_EXEMPT_SUPPLY,
    REASON_NON_REGISTERED,
    REASON_UNCONFIRMED_REGISTRATION,
    REASON_UNKNOWN,
    REASON_ZERO_RATED,
    VAT_SOURCE_CONFIGURED_ACCOUNTS,
    VAT_SOURCE_KEYWORD_FALLBACK,
    VAT_SOURCE_NONE,
    VAT_TREATMENT_DUE,
    VAT_TREATMENT_EXEMPT,
    VAT_TREATMENT_LEGACY_STANDARD,
    VAT_TREATMENT_UNDUE,
    VAT_TREATMENT_ZERO_RATED,
    build_service_tax_snapshot,
    classify_supply,
    collect_tax_rows,
    derive_treatment_reason,
    doc_has_field,
    doc_value,
    get_tax_invoice_reference,
    normalize_vat_treatment,
    select_vat_rows,
    service_base_amount,
    sum_vat_rows,
)
from print_designer.custom.thai_company_registration import (
    VAT_STATUS_NOT_REGISTERED,
    VAT_STATUS_REGISTERED,
    VAT_STATUS_UNCONFIRMED,
    VAT_STATUS_UNKNOWN,
    CompanyRegistration,
    classify_vat_status,
    get_company_registration,
    vat_status_is_effective,
)

VAT_ACCOUNT = "Output VAT - 7% - Test Company"
CHARGE_ACCOUNT = "Delivery Charges - Test Company"
WITHHOLDING_ACCOUNT = "Withholding Tax - 3% - Test Company"

SERVICE_ITEM = "SERVICE-001"
GOODS_ITEM = "GOODS-001"
UNCLASSIFIED_ITEM = "NONSTOCK-001"


def _site_available():
    """Return True when the tests run against a connected site."""
    try:
        frappe.db.sql("select 1")
        return True
    except Exception:
        return False


def make_registration(kind=VAT_STATUS_REGISTERED, warning=None):
    """A registration snapshot of a company."""
    status = {
        VAT_STATUS_REGISTERED: "Registered",
        VAT_STATUS_NOT_REGISTERED: "Not Registered",
        VAT_STATUS_UNCONFIRMED: "Unconfirmed",
    }.get(kind)
    return CompanyRegistration(
        company="Test Company",
        status=status,
        kind=kind,
        effective_from="2024-01-01",
        is_effective=True,
        source="thai_company_settings",
        warning=warning,
    )


def service_row(item_code=SERVICE_ITEM, base=1000.0, currency=1000.0):
    return {
        "item_code": item_code,
        "is_service": True,
        "is_stock": False,
        "base_net_amount": base,
        "net_amount": currency,
    }


def goods_row(item_code=GOODS_ITEM, base=500.0, currency=500.0):
    return {
        "item_code": item_code,
        "is_service": False,
        "is_stock": True,
        "base_net_amount": base,
        "net_amount": currency,
    }


def unclassified_row(item_code=UNCLASSIFIED_ITEM, base=100.0, currency=100.0):
    return {
        "item_code": item_code,
        "is_service": False,
        "is_stock": False,
        "base_net_amount": base,
        "net_amount": currency,
    }


def vat_row(account=VAT_ACCOUNT, rate=7.0, amount=70.0, base=70.0, **extra):
    row = {
        "account_head": account,
        "description": "VAT",
        "charge_type": "On Net Total",
        "rate": rate,
        "tax_amount": amount,
        "base_tax_amount": base,
        "is_tax_withholding_account": 0,
    }
    row.update(extra)
    return row


def build(**kwargs):
    """Build a snapshot with sensible defaults."""
    params = {
        "identity": {
            "sales_invoice": "SINV-0001",
            "docstatus": 1,
            "posting_date": "2026-01-15",
            "company": "Test Company",
            "currency": "THB",
            "company_currency": "THB",
            "net_total": 1000.0,
        },
        "registration": make_registration(),
        "treatment": VAT_TREATMENT_UNDUE,
        "item_rows": [service_row()],
        "vat_rows": [vat_row()],
    }
    params.update(kwargs)
    return build_service_tax_snapshot(**params)


class TestNormalizeVatTreatment(unittest.TestCase):
    """The stored treatment is read with its canonical name."""

    def test_legacy_standard_is_read_as_vat_due(self):
        self.assertEqual(normalize_vat_treatment(VAT_TREATMENT_LEGACY_STANDARD), VAT_TREATMENT_DUE)

    def test_known_treatments_are_kept(self):
        self.assertEqual(normalize_vat_treatment(VAT_TREATMENT_UNDUE), VAT_TREATMENT_UNDUE)
        self.assertEqual(normalize_vat_treatment(VAT_TREATMENT_EXEMPT), VAT_TREATMENT_EXEMPT)
        self.assertEqual(
            normalize_vat_treatment(VAT_TREATMENT_ZERO_RATED), VAT_TREATMENT_ZERO_RATED
        )

    def test_empty_treatment_is_none(self):
        self.assertIsNone(normalize_vat_treatment(None))
        self.assertIsNone(normalize_vat_treatment(""))

    def test_the_value_is_trimmed(self):
        self.assertEqual(normalize_vat_treatment("  VAT Due  "), VAT_TREATMENT_DUE)


class TestDeriveTreatmentReason(unittest.TestCase):
    """The audit reason is more precise than the stored treatment."""

    def test_deferred_service(self):
        reason = derive_treatment_reason(VAT_TREATMENT_UNDUE, make_registration())
        self.assertEqual(reason, REASON_DEFERRED_SERVICE)

    def test_already_due(self):
        reason = derive_treatment_reason(VAT_TREATMENT_DUE, make_registration())
        self.assertEqual(reason, REASON_ALREADY_DUE)

    def test_zero_rated(self):
        reason = derive_treatment_reason(VAT_TREATMENT_ZERO_RATED, make_registration())
        self.assertEqual(reason, REASON_ZERO_RATED)

    def test_exempt_supply_of_a_registered_company(self):
        reason = derive_treatment_reason(VAT_TREATMENT_EXEMPT, make_registration())
        self.assertEqual(reason, REASON_EXEMPT_SUPPLY)

    def test_a_seller_that_is_not_registered(self):
        registration = make_registration(VAT_STATUS_NOT_REGISTERED)
        reason = derive_treatment_reason(VAT_TREATMENT_EXEMPT, registration)
        self.assertEqual(reason, REASON_NON_REGISTERED)

    def test_an_unconfirmed_registration_is_not_a_confirmed_exemption(self):
        registration = make_registration(VAT_STATUS_UNCONFIRMED)
        reason = derive_treatment_reason(VAT_TREATMENT_EXEMPT, registration)
        self.assertEqual(reason, REASON_UNCONFIRMED_REGISTRATION)

    def test_an_unknown_registration_is_not_a_confirmed_exemption(self):
        registration = make_registration(VAT_STATUS_UNKNOWN)
        reason = derive_treatment_reason(VAT_TREATMENT_EXEMPT, registration)
        self.assertEqual(reason, REASON_EXEMPT_SUPPLY)

    def test_without_a_treatment_the_reason_is_unknown(self):
        self.assertEqual(derive_treatment_reason(None, make_registration()), REASON_UNKNOWN)


class TestClassifySupply(unittest.TestCase):
    """The rows of an invoice are classified explicitly."""

    def test_a_service_invoice(self):
        result = classify_supply([service_row()])
        self.assertEqual(result["classification"], CLASSIFICATION_SERVICES)
        self.assertTrue(result["is_service_sale"])
        self.assertEqual(result["service_item_codes"], (SERVICE_ITEM,))

    def test_a_goods_invoice(self):
        result = classify_supply([goods_row()])
        self.assertEqual(result["classification"], CLASSIFICATION_GOODS)
        self.assertFalse(result["is_service_sale"])

    def test_a_mixed_invoice(self):
        result = classify_supply([service_row(), goods_row()])
        self.assertEqual(result["classification"], CLASSIFICATION_MIXED)
        self.assertFalse(result["is_service_sale"])

    def test_a_non_stock_item_is_not_a_service(self):
        result = classify_supply([unclassified_row()])
        self.assertEqual(result["classification"], CLASSIFICATION_UNKNOWN)
        self.assertEqual(result["unclassified_item_codes"], (UNCLASSIFIED_ITEM,))
        self.assertFalse(result["is_service_sale"])

    def test_an_unclassified_row_takes_the_invoice_out_of_the_pilot(self):
        result = classify_supply([service_row(), unclassified_row()])
        self.assertEqual(result["classification"], CLASSIFICATION_SERVICES)
        self.assertFalse(result["is_service_sale"])

    def test_an_invoice_without_rows(self):
        result = classify_supply([])
        self.assertEqual(result["classification"], CLASSIFICATION_UNKNOWN)


class TestSelectVatRows(unittest.TestCase):
    """Only the VAT rows are read - and the source is reported."""

    def test_the_configured_accounts_win(self):
        rows = [vat_row(VAT_ACCOUNT), vat_row(CHARGE_ACCOUNT)]
        selected, source = select_vat_rows(rows, [VAT_ACCOUNT], {})
        self.assertEqual(source, VAT_SOURCE_CONFIGURED_ACCOUNTS)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["account_head"], VAT_ACCOUNT)

    def test_a_withholding_row_is_never_a_vat(self):
        row = vat_row(WITHHOLDING_ACCOUNT)
        row["is_tax_withholding_account"] = 1
        selected, source = select_vat_rows([row], [WITHHOLDING_ACCOUNT], {})
        self.assertEqual(selected, [])
        self.assertEqual(source, VAT_SOURCE_NONE)

    def test_the_keyword_fallback_is_reported(self):
        rows = [vat_row(VAT_ACCOUNT)]
        meta = {VAT_ACCOUNT: {"account_type": "Tax", "account_name": "Output VAT - 7%"}}
        selected, source = select_vat_rows(rows, [], meta)
        self.assertEqual(source, VAT_SOURCE_KEYWORD_FALLBACK)
        self.assertEqual(len(selected), 1)

    def test_a_tax_account_without_vat_in_its_name_is_not_a_vat(self):
        rows = [vat_row(WITHHOLDING_ACCOUNT)]
        meta = {WITHHOLDING_ACCOUNT: {"account_type": "Tax", "account_name": "Withholding Tax"}}
        selected, source = select_vat_rows(rows, [], meta)
        self.assertEqual(selected, [])
        self.assertEqual(source, VAT_SOURCE_NONE)

    def test_a_charge_row_is_not_a_vat(self):
        rows = [vat_row(CHARGE_ACCOUNT)]
        meta = {CHARGE_ACCOUNT: {"account_type": "Chargeable", "account_name": "Delivery"}}
        selected, source = select_vat_rows(rows, [], meta)
        self.assertEqual(selected, [])
        self.assertEqual(source, VAT_SOURCE_NONE)


class TestAmountHelpers(unittest.TestCase):
    """The amounts are summed with the precision of the currency."""

    def test_the_vat_rows_are_summed(self):
        base, currency = sum_vat_rows(
            [vat_row(amount=70.0, base=70.0), vat_row(amount=30.0, base=28.5)]
        )
        self.assertEqual(base, 98.5)
        self.assertEqual(currency, 100.0)

    def test_only_the_service_rows_are_the_service_base(self):
        rows = [service_row(base=1000.0), goods_row(base=500.0)]
        base, currency = service_base_amount(rows, (SERVICE_ITEM,))
        self.assertEqual(base, 1000.0)
        self.assertEqual(currency, 1000.0)

    def test_the_amounts_are_rounded(self):
        rows = [vat_row(amount=0.1, base=0.1), vat_row(amount=0.2, base=0.2)]
        base, currency = sum_vat_rows(rows)
        self.assertEqual(base, 0.3)
        self.assertEqual(currency, 0.3)


class TestSnapshotMatrix(unittest.TestCase):
    """The matrix of the plan."""

    def test_a_registered_deferred_service(self):
        snapshot = build()
        self.assertEqual(snapshot.treatment, VAT_TREATMENT_UNDUE)
        self.assertEqual(snapshot.treatment_reason, REASON_DEFERRED_SERVICE)
        self.assertEqual(snapshot.classification, CLASSIFICATION_SERVICES)
        self.assertTrue(snapshot.is_service_sale)
        self.assertTrue(snapshot.has_vat_liability)
        self.assertTrue(snapshot.is_deferred)
        self.assertEqual(snapshot.vat_amount, 70.0)
        self.assertEqual(snapshot.service_vat_amount, 70.0)
        self.assertEqual(snapshot.eligible_service_base, 1000.0)

    def test_a_seller_that_is_not_registered_tracks_the_sale_without_a_liability(self):
        snapshot = build(
            registration=make_registration(VAT_STATUS_NOT_REGISTERED),
            treatment=VAT_TREATMENT_EXEMPT,
            vat_rows=[],
        )
        self.assertEqual(snapshot.treatment_reason, REASON_NON_REGISTERED)
        self.assertEqual(snapshot.vat_amount, 0.0)
        self.assertEqual(snapshot.service_vat_amount, 0.0)
        self.assertFalse(snapshot.has_vat_liability)
        self.assertTrue(snapshot.is_non_taxable)
        # the revenue is kept
        self.assertEqual(snapshot.eligible_service_base, 1000.0)

    def test_an_exempt_supply_of_a_registered_company(self):
        snapshot = build(treatment=VAT_TREATMENT_EXEMPT, vat_rows=[])
        self.assertEqual(snapshot.treatment_reason, REASON_EXEMPT_SUPPLY)
        self.assertEqual(snapshot.vat_amount, 0.0)
        self.assertFalse(snapshot.has_vat_liability)

    def test_a_zero_rated_supply(self):
        snapshot = build(
            treatment=VAT_TREATMENT_ZERO_RATED,
            vat_rows=[vat_row(rate=0.0, amount=0.0, base=0.0)],
        )
        self.assertEqual(snapshot.treatment_reason, REASON_ZERO_RATED)
        self.assertEqual(snapshot.vat_amount, 0.0)
        self.assertFalse(snapshot.has_vat_liability)

    def test_a_supply_whose_vat_is_already_due(self):
        snapshot = build(treatment=VAT_TREATMENT_DUE)
        self.assertEqual(snapshot.treatment_reason, REASON_ALREADY_DUE)
        self.assertFalse(snapshot.is_deferred)
        self.assertTrue(snapshot.has_vat_liability)
        self.assertEqual(snapshot.vat_amount, 70.0)

    def test_the_legacy_value_is_read_and_flagged(self):
        snapshot = build(treatment=VAT_TREATMENT_LEGACY_STANDARD)
        self.assertEqual(snapshot.treatment, VAT_TREATMENT_DUE)
        self.assertTrue(snapshot.treatment_is_legacy_alias)
        self.assertEqual(snapshot.treatment_reason, REASON_ALREADY_DUE)

    def test_an_unconfirmed_registration_is_reported(self):
        registration = make_registration(VAT_STATUS_UNCONFIRMED, warning="not confirmed")
        snapshot = build(
            registration=registration,
            treatment=VAT_TREATMENT_EXEMPT,
            vat_rows=[],
        )
        self.assertEqual(snapshot.treatment_reason, REASON_UNCONFIRMED_REGISTRATION)
        self.assertFalse(snapshot.has_vat_liability)
        self.assertIn("not confirmed", " ".join(snapshot.warnings))

    def test_an_unknown_registration_is_reported(self):
        registration = make_registration(VAT_STATUS_UNKNOWN, warning="not configured")
        snapshot = build(
            registration=registration,
            treatment=VAT_TREATMENT_EXEMPT,
            vat_rows=[],
        )
        self.assertTrue(any("not configured" in warning for warning in snapshot.warnings))

    def test_an_invoice_without_a_treatment_is_reported(self):
        snapshot = build(treatment=None)
        self.assertEqual(snapshot.treatment_reason, REASON_UNKNOWN)
        self.assertTrue(any("VAT treatment" in warning for warning in snapshot.warnings))

    def test_a_mixed_invoice_does_not_allocate_the_vat(self):
        snapshot = build(item_rows=[service_row(), goods_row()])
        self.assertEqual(snapshot.classification, CLASSIFICATION_MIXED)
        self.assertIsNone(snapshot.service_vat_amount)
        self.assertTrue(any("mixes services and goods" in warning for warning in snapshot.warnings))

    def test_an_unrelated_charge_is_not_a_vat(self):
        rows = [vat_row(VAT_ACCOUNT), vat_row(CHARGE_ACCOUNT, rate=0.0, amount=150.0, base=150.0)]
        selected, source = select_vat_rows(rows, [VAT_ACCOUNT], {})
        self.assertEqual(source, VAT_SOURCE_CONFIGURED_ACCOUNTS)
        base, _currency = sum_vat_rows(selected)
        self.assertEqual(base, 70.0)

    def test_the_withholding_tax_is_not_part_of_the_vat_base(self):
        snapshot = build(
            wht={
                "subject_to_wht": 1,
                "percentage": 3.0,
                "amount": 30.0,
                "net_total_after_wht": 970.0,
            },
            retention={
                "subject_to_retention": 1,
                "percentage": 5.0,
                "amount": 50.0,
                "net_total_after_wht_and_retention": 920.0,
            },
        )
        self.assertEqual(snapshot.vat_amount, 70.0)
        self.assertEqual(snapshot.eligible_service_base, 1000.0)
        self.assertEqual(snapshot.wht_amount, 30.0)
        self.assertEqual(snapshot.retention_amount, 50.0)
        self.assertEqual(snapshot.net_total_after_wht, 970.0)
        self.assertEqual(snapshot.net_total_after_wht_and_retention, 920.0)

    def test_a_foreign_currency_keeps_the_amounts_apart(self):
        snapshot = build(
            identity={
                "sales_invoice": "SINV-0002",
                "docstatus": 1,
                "company": "Test Company",
                "currency": "USD",
                "company_currency": "THB",
                "net_total": 32000.0,
            },
            item_rows=[service_row(base=32000.0, currency=1000.0)],
            vat_rows=[vat_row(amount=70.0, base=2240.0)],
        )
        self.assertEqual(snapshot.vat_amount, 2240.0)
        self.assertEqual(snapshot.vat_amount_currency, 70.0)
        self.assertEqual(snapshot.eligible_service_base, 32000.0)
        self.assertEqual(snapshot.eligible_service_base_currency, 1000.0)

    def test_the_snapshot_is_a_value_object(self):
        snapshot = build()
        data = snapshot.as_dict()
        self.assertEqual(data["treatment"], VAT_TREATMENT_UNDUE)
        self.assertEqual(data["registration"]["kind"], VAT_STATUS_REGISTERED)
        self.assertEqual(len(data["vat_rows"]), 1)


class TestCollectTaxRows(unittest.TestCase):
    """The tax rows are read from the invoice without a site."""

    def test_an_exclusive_vat_row_is_read(self):
        rows = collect_tax_rows(
            {
                "taxes": [
                    {
                        "account_head": VAT_ACCOUNT,
                        "description": "VAT",
                        "charge_type": "On Net Total",
                        "rate": 7.0,
                        "tax_amount": 70.0,
                        "base_tax_amount": 70.0,
                        "total": 1070.0,
                        "net_amount": 1000.0,
                    }
                ]
            }
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tax_amount"], 70.0)
        self.assertFalse(rows[0]["is_inclusive"])

    def test_an_inclusive_vat_row_is_flagged(self):
        rows = collect_tax_rows(
            {
                "taxes": [
                    {
                        "account_head": VAT_ACCOUNT,
                        "charge_type": "On Net Total",
                        "rate": 7.0,
                        "tax_amount": 70.0,
                        "base_tax_amount": 70.0,
                        "total": 1000.0,
                        "net_amount": 1000.0,
                    }
                ]
            }
        )
        self.assertTrue(rows[0]["is_inclusive"])

    def test_a_row_without_a_tax_is_not_inclusive(self):
        rows = collect_tax_rows({"taxes": [{"account_head": CHARGE_ACCOUNT, "tax_amount": 0.0}]})
        self.assertFalse(rows[0]["is_inclusive"])


class TestTheCompanyContext(unittest.TestCase):
    """The company context is a context, not a proof of a service sale."""

    def test_the_context_of_the_company_is_read(self):
        snapshot = build(
            company_context={
                "service_business": 1,
                "construction_service": 0,
                "branch_code": "BR-01",
            }
        )
        self.assertTrue(snapshot.company_service_business)
        self.assertFalse(snapshot.company_construction_service)
        self.assertEqual(snapshot.company_branch_code, "BR-01")

    def test_the_construction_flag_of_the_invoice_is_read(self):
        snapshot = build(
            company_context={
                "service_business": 0,
                "construction_service": 1,
                "branch_code": None,
            }
        )
        self.assertTrue(snapshot.company_construction_service)

    def test_the_context_does_not_change_the_classification(self):
        snapshot = build(
            company_context={"service_business": 1, "construction_service": 1},
            item_rows=[goods_row()],
        )
        self.assertEqual(snapshot.classification, CLASSIFICATION_GOODS)
        self.assertFalse(snapshot.is_service_sale)

    def test_an_inclusive_vat_is_flagged(self):
        snapshot = build(vat_rows=[vat_row(is_inclusive=True)])
        self.assertTrue(snapshot.has_inclusive_vat)
        self.assertTrue(snapshot.vat_rows[0].is_inclusive)

    def test_an_exclusive_vat_is_not_flagged(self):
        snapshot = build(vat_rows=[vat_row(is_inclusive=False)])
        self.assertFalse(snapshot.has_inclusive_vat)

    def test_the_certificate_requirement_is_read(self):
        snapshot = build(
            wht={
                "subject_to_wht": 1,
                "percentage": 3.0,
                "amount": 30.0,
                "certificate_required": 1,
            }
        )
        self.assertTrue(snapshot.wht_certificate_required)

    def test_the_new_values_are_in_the_dictionary(self):
        data = build(
            company_context={"service_business": 1, "branch_code": "BR-01"},
            wht={"certificate_required": 1},
            vat_rows=[vat_row(is_inclusive=True)],
        ).as_dict()
        self.assertTrue(data["company_service_business"])
        self.assertEqual(data["company_branch_code"], "BR-01")
        self.assertTrue(data["wht_certificate_required"])
        self.assertTrue(data["has_inclusive_vat"])


class TestDocHelpers(unittest.TestCase):
    """The helpers read a document and a plain dictionary."""

    def test_a_dictionary_is_read(self):
        self.assertEqual(doc_value({"company": "Test Company"}, "company"), "Test Company")
        self.assertIsNone(doc_value({"company": "Test Company"}, "customer"))
        self.assertEqual(doc_value({}, "company", "fallback"), "fallback")

    def test_an_empty_value_falls_back_to_the_default(self):
        self.assertEqual(doc_value({"company": ""}, "company", "fallback"), "fallback")
        self.assertEqual(doc_value({"company": 0}, "company", "fallback"), 0)

    def test_the_fields_of_a_dictionary(self):
        self.assertTrue(doc_has_field({"company": "Test Company"}, "company"))
        self.assertFalse(doc_has_field({"company": "Test Company"}, "customer"))

    def test_the_tax_invoice_number_is_read_from_the_field_that_exists(self):
        doc = {
            "pd_custom_tax_invoice_number": "INV-0001",
            "pd_custom_tax_invoice_date": "2026-01-16",
        }
        number, date, field = get_tax_invoice_reference(doc)
        self.assertEqual(number, "INV-0001")
        self.assertEqual(date, "2026-01-16")
        self.assertEqual(field, "pd_custom_tax_invoice_number")

    def test_without_a_tax_invoice_number_there_is_no_reference(self):
        number, date, field = get_tax_invoice_reference({"company": "Test Company"})
        self.assertIsNone(number)
        self.assertIsNone(date)
        self.assertIsNone(field)


class TestRegistrationRules(unittest.TestCase):
    """The pure rules of the registration."""

    def test_the_stored_values_are_classified(self):
        self.assertEqual(classify_vat_status("Registered"), VAT_STATUS_REGISTERED)
        self.assertEqual(classify_vat_status("Not Registered"), VAT_STATUS_NOT_REGISTERED)
        self.assertEqual(classify_vat_status("Unconfirmed"), VAT_STATUS_UNCONFIRMED)
        self.assertEqual(classify_vat_status(""), VAT_STATUS_UNKNOWN)
        self.assertEqual(classify_vat_status("registered"), VAT_STATUS_UNKNOWN)

    def test_a_status_that_is_not_effective_yet(self):
        self.assertFalse(vat_status_is_effective("Registered", "2026-06-01", "2026-01-15"))
        self.assertTrue(vat_status_is_effective("Registered", "2026-01-01", "2026-01-15"))
        self.assertTrue(vat_status_is_effective("Registered", None, "2026-01-15"))


class TestOnSite(unittest.TestCase):
    """The parts that read the database."""

    def setUp(self):
        if not _site_available():
            self.skipTest("no site")

    def test_a_company_without_a_settings_record_is_unknown(self):
        registration = get_company_registration("__no_such_company__")
        self.assertEqual(registration.kind, VAT_STATUS_UNKNOWN)
        self.assertIsNotNone(registration.warning)
        self.assertFalse(registration.is_registered)

    def test_a_document_without_a_company_is_unknown(self):
        registration = get_company_registration(None)
        self.assertEqual(registration.kind, VAT_STATUS_UNKNOWN)
        self.assertIsNotNone(registration.warning)

    def test_reading_the_contract_does_not_write(self):
        from print_designer.custom.sales_invoice_tax_contract import (
            get_service_tax_snapshot,
        )

        invoice = frappe.new_doc("Sales Invoice")
        companies = frappe.get_all("Company", limit=1)
        company = companies[0].name if companies else None
        invoice.set("company", company)
        if company:
            invoice.set("currency", frappe.get_cached_value("Company", company, "default_currency"))

        undue_before = frappe.db.count("Output VAT Undue")
        gl_before = frappe.db.count("GL Entry")

        get_service_tax_snapshot(invoice)

        self.assertTrue(invoice.get("__islocal"))
        self.assertEqual(frappe.db.count("Output VAT Undue"), undue_before)
        self.assertEqual(frappe.db.count("GL Entry"), gl_before)
