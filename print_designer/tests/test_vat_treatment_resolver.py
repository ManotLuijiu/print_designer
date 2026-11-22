"""The VAT treatment resolver of Print Designer must stay equivalent.

``print_designer/custom/vat_treatment.py`` is the port of the resolver that
used to live in the Thai Business Suite app.  Print Designer owns the
decision now, so the app must not be needed - but the decision itself must
not change: a site that runs both apps has to get the same treatment before
and after the relocation.

The test therefore compares the two implementations with each other.  It is
skipped when the Thai Business Suite app is not installed - on such a site
there is nothing to compare with.

Run with:
    bench --site <site> execute print_designer.commands.run_tests.main \
      --kwargs '{"modules": ["print_designer.tests.test_vat_treatment_resolver"]}'
"""

import unittest
from typing import Any

from print_designer.custom import vat_treatment as pd_vat

TEMPLATES = [
    {
        "name": "VAT Exempt - Test Company",
        "title": "VAT Exempt",
        "tax_category": "Exempt",
        "is_default": 0,
    },
    {
        "name": "Zero-Rated - Test Company",
        "title": "Zero-Rated",
        "tax_category": "Zero-Rated",
        "is_default": 0,
    },
    {
        "name": "Output VAT Undue - Test Company",
        "title": "Output VAT Undue",
        "tax_category": "Services Tax",
        "is_default": 0,
    },
    {
        "name": "Output VAT Non-exempt - Test Company",
        "title": "Output VAT Non-exempt",
        "tax_category": None,
        "is_default": 0,
    },
    {
        "name": "Output VAT - Test Company",
        "title": "Output VAT",
        "tax_category": None,
        "is_default": 1,
    },
]

STATUSES = ["Registered", "Not Registered", "Unconfirmed", "", "registered", None]
EFFECTIVE_FROM = [None, "2026-01-01"]
POSTING_DATES = [None, "2025-12-31", "2026-01-01"]
TEMPLATE_KINDS = [None, "due", "exempt", "zero_rated", "undue"]
TAX_CATEGORIES = [None, "Exempt", "Zero-Rated", "Services Tax", "Other"]


def _tbs_vat() -> Any:
    """Return the resolver of the Thai Business Suite app, or None."""
    try:
        from thai_business_suite.overrides import thai_tax_category
    except Exception:
        return None
    return thai_tax_category


class TestEquivalenceWithTheThaiBusinessSuite(unittest.TestCase):
    """Print Designer and the Thai Business Suite must decide the same."""

    def setUp(self):
        self.tbs: Any = _tbs_vat()
        if self.tbs is None:
            self.skipTest("the Thai Business Suite app is not installed")

    def test_the_vocabulary_is_the_same(self):
        self.assertEqual(pd_vat.VAT_TREATMENT_DUE, self.tbs.VAT_TREATMENT_DUE)
        self.assertEqual(pd_vat.VAT_TREATMENT_UNDUE, self.tbs.VAT_TREATMENT_UNDUE)
        self.assertEqual(pd_vat.VAT_TREATMENT_EXEMPT, self.tbs.VAT_TREATMENT_EXEMPT)
        self.assertEqual(pd_vat.VAT_TREATMENT_ZERO_RATED, self.tbs.VAT_TREATMENT_ZERO_RATED)
        self.assertEqual(
            pd_vat.VAT_TREATMENT_LEGACY_STANDARD, self.tbs.VAT_TREATMENT_LEGACY_STANDARD
        )
        self.assertEqual(pd_vat.VAT_DUE_TREATMENTS, self.tbs.VAT_DUE_TREATMENTS)
        self.assertEqual(pd_vat.MANUAL_VAT_TREATMENTS, self.tbs.MANUAL_VAT_TREATMENTS)
        self.assertEqual(pd_vat.EXEMPT_TAX_CATEGORY, self.tbs.EXEMPT_TAX_CATEGORY)
        self.assertEqual(pd_vat.ZERO_RATED_TAX_CATEGORY, self.tbs.ZERO_RATED_TAX_CATEGORY)
        self.assertEqual(pd_vat.UNDUE_TAX_CATEGORY, self.tbs.UNDUE_TAX_CATEGORY)

    def test_the_status_is_classified_the_same(self):
        for status in STATUSES:
            self.assertEqual(
                pd_vat.classify_vat_status(status),
                self.tbs.classify_vat_status(status),
                f"status {status!r}",
            )
            self.assertEqual(
                pd_vat.is_exempt_vat_status(status),
                self.tbs.is_exempt_vat_status(status),
                f"status {status!r}",
            )

    def test_the_effective_date_is_judged_the_same(self):
        for status in STATUSES:
            for effective_from in EFFECTIVE_FROM:
                for posting_date in POSTING_DATES:
                    self.assertEqual(
                        pd_vat.vat_status_is_effective(status, effective_from, posting_date),
                        self.tbs.vat_status_is_effective(status, effective_from, posting_date),
                        f"{status!r} {effective_from!r} {posting_date!r}",
                    )

    def test_the_tax_category_behaviour_is_the_same(self):
        for category in TAX_CATEGORIES:
            self.assertEqual(
                pd_vat.resolve_behaviour(category),
                self.tbs.resolve_behaviour(category),
                f"category {category!r}",
            )

    def test_the_templates_are_found_the_same(self):
        self.assertEqual(
            pd_vat.find_exempt_template(TEMPLATES),
            self.tbs.find_exempt_template(TEMPLATES),
        )
        self.assertEqual(
            pd_vat.find_zero_rated_template(TEMPLATES),
            self.tbs.find_zero_rated_template(TEMPLATES),
        )
        self.assertEqual(
            pd_vat.find_undue_template(TEMPLATES),
            self.tbs.find_undue_template(TEMPLATES),
        )

        for template in TEMPLATES:
            self.assertEqual(
                pd_vat.is_negated_exempt_template(template),
                self.tbs.is_negated_exempt_template(template),
                template["name"],
            )
            for label in ("VAT Exempt", "Output VAT Undue", "Zero-Rated"):
                self.assertEqual(
                    pd_vat.template_label_matches(template, label),
                    self.tbs.template_label_matches(template, label),
                    f"{template['name']} {label}",
                )
                self.assertEqual(
                    pd_vat.template_starts_with_label(template, label),
                    self.tbs.template_starts_with_label(template, label),
                    f"{template['name']} {label}",
                )

    def test_the_decision_is_the_same(self):
        for status in STATUSES:
            for effective_from in EFFECTIVE_FROM:
                for posting_date in POSTING_DATES:
                    for template_kind in TEMPLATE_KINDS:
                        for category in TAX_CATEGORIES:
                            for is_pos in (False, True):
                                for has_service_item in (False, True):
                                    pd_result = pd_vat.resolve_vat_treatment(
                                        company="Test Company",
                                        tax_template=None,
                                        tax_category=category,
                                        posting_date=posting_date,
                                        is_pos=is_pos,
                                        has_service_item=has_service_item,
                                        status=status,
                                        status_effective_from=effective_from,
                                        template_kind=template_kind,
                                    )
                                    tbs_result = self.tbs.resolve_vat_treatment(
                                        company="Test Company",
                                        tax_template=None,
                                        tax_category=category,
                                        posting_date=posting_date,
                                        is_pos=is_pos,
                                        has_service_item=has_service_item,
                                        status=status,
                                        status_effective_from=effective_from,
                                        template_kind=template_kind,
                                    )
                                    self.assertEqual(
                                        pd_result,
                                        tbs_result,
                                        f"{status!r} {effective_from!r} {posting_date!r} "
                                        f"{template_kind!r} {category!r} {is_pos!r} "
                                        f"{has_service_item!r}",
                                    )

    def test_the_treatment_of_a_template_and_a_category_is_the_same(self):
        for template_kind in TEMPLATE_KINDS:
            for category in TAX_CATEGORIES:
                for is_pos in (False, True):
                    for has_service_item in (False, True):
                        self.assertEqual(
                            pd_vat.treatment_from_template_and_category(
                                template_kind, category, is_pos, has_service_item
                            ),
                            self.tbs.treatment_from_template_and_category(
                                template_kind, category, is_pos, has_service_item
                            ),
                            f"{template_kind!r} {category!r} {is_pos!r} {has_service_item!r}",
                        )

    def test_a_company_without_a_registration_is_read_the_same(self):
        self.assertEqual(
            pd_vat.get_company_vat_status(None),
            self.tbs.get_company_vat_status(None),
        )
