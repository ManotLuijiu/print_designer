"""Regression tests for the Chart of Accounts import in the Company override.

The ``CustomCompany`` override in ``print_designer/overrides/company.py`` imports the
Chart of Accounts when a company is created. ``erpnext`` exposes the helper as::

    create_charts(company, chart_template=None, existing_company=None, ...)

The override used to pass the company *country* as the third positional argument.
``get_chart()`` then treated the country as an existing company, looked for an account
tree named after that country, found nothing and returned an empty chart. The import was
skipped silently, so every company created from a standard Chart of Accounts template
ended up without any account. The ERPNext test bootstrap later failed with::

    frappe.exceptions.LinkValidationError: Could not find Parent Account: Bank Accounts - _TC

Run standalone (no site required):

    cd /home/frappe/frappe-bench
    env/bin/python -m unittest apps.print_designer.print_designer.tests.test_company_coa_import
"""

import unittest
from unittest.mock import patch

import frappe

from print_designer.overrides.company import CustomCompany

CREATE_CHARTS = (
	"erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.create_charts"
)


class FakeCompany(CustomCompany):
	"""Minimal stand-in for a Company document (no Document.__init__ needed)."""

	def __init__(self, name="_Test Company", chart_of_accounts="Standard", existing_company=None):
		self.name = name
		self.chart_of_accounts = chart_of_accounts
		self.existing_company = existing_company
		self.country = "India"
		self.db_set_calls = []

	def db_set(self, fieldname, value, **kwargs):
		self.db_set_calls.append((fieldname, value))


class FakeDB:
	"""Stub for ``frappe.db`` so the ERPNext helper can run without a site."""

	def get_value(self, *args, **kwargs):
		return None


class TestCreateDefaultAccounts(unittest.TestCase):
	"""The Chart of Accounts import must receive the ERPNext arguments."""

	def setUp(self):
		if not getattr(frappe.local, "flags", None):
			frappe.local.flags = frappe._dict()
		self._previous_db = getattr(frappe.local, "db", None)
		frappe.local.db = FakeDB()

	def tearDown(self):
		if self._previous_db is None:
			try:
				del frappe.local.db
			except AttributeError:
				pass
		else:
			frappe.local.db = self._previous_db

	def _capture_create_charts(self, company):
		captured = {}

		def fake_create_charts(company_name, chart_template=None, existing_company=None, **kwargs):
			captured["company"] = company_name
			captured["chart_template"] = chart_template
			captured["existing_company"] = existing_company
			captured["kwargs"] = kwargs

		with patch(CREATE_CHARTS, side_effect=fake_create_charts):
			CustomCompany.create_default_accounts(company)

		return captured

	def test_existing_company_is_passed_instead_of_the_country(self):
		captured = self._capture_create_charts(FakeCompany())

		self.assertEqual(captured["company"], "_Test Company")
		self.assertEqual(captured["chart_template"], "Standard")
		self.assertIsNone(captured["existing_company"])
		self.assertNotEqual(captured["existing_company"], "India")

	def test_existing_company_is_forwarded_when_set(self):
		captured = self._capture_create_charts(FakeCompany(existing_company="AWS Solution Ltd."))

		self.assertEqual(captured["existing_company"], "AWS Solution Ltd.")

	def test_custom_chart_template_is_forwarded(self):
		captured = self._capture_create_charts(FakeCompany(chart_of_accounts="Thailand"))

		self.assertEqual(captured["chart_template"], "Thailand")


def _has_db_connection() -> bool:
	try:
		frappe.db.sql("select 1")
		return True
	except Exception:
		return False


class TestChartLookup(unittest.TestCase):
	"""The chart lookup must not resolve to an empty tree because of the country."""

	def test_standard_chart_contains_the_bank_accounts_group(self):
		from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_chart

		chart = get_chart("Standard", None)
		self.assertTrue(chart)
		self.assertIn("Bank Accounts", str(chart))

	@unittest.skipUnless(_has_db_connection(), "requires a site connection")
	def test_country_is_not_usable_as_existing_company(self):
		from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_chart

		# This is what the override used to pass and what broke the import.
		self.assertFalse(get_chart("Standard", "India"))


if __name__ == "__main__":
	unittest.main()
