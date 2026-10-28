"""Test bootstrap for the Print Designer test suite.

On a site that already runs a local (non-Indian) company, the ERPNext test
bootstrap tries to create its India preset records again, which fails with a
duplicate entry error for the "Standard Buying" / "Standard Selling" price
lists.

The compatibility shim lives in ``thai_business_suite`` because it knows about
the Thai site data.  When that app is not installed the shim is skipped and the
ERPNext bootstrap keeps its default behaviour.
"""


def prepare_test_bootstrap() -> None:
	"""Apply the site wide ERPNext test bootstrap compatibility shim."""
	try:
		from thai_business_suite.overrides.test_bootstrap import prepare_test_bootstrap as _prepare
	except ImportError:
		return

	_prepare()
