"""Regression tests for the Jinja namespace compatibility shim.

Exported Print Designer templates embed their design as a JSON blob and parse
it with ``frappe.parse_json(...)``. Frappe v16 exposes a restricted ``frappe``
namespace to Jinja templates, so the helper was missing and rendering such a
template failed with::

    AttributeError: module has no attribute 'parse_json'
"""

import unittest

import frappe

from print_designer.utils.jinja_namespace import install_jinja_namespace_compat, is_installed


class TestJinjaNamespaceCompat(unittest.TestCase):
	def test_shim_is_installed(self):
		self.assertTrue(
			is_installed(),
			"The Jinja namespace compatibility shim must be installed when the "
			"app package is imported.",
		)

	def test_installation_is_idempotent(self):
		self.assertTrue(install_jinja_namespace_compat())
		self.assertTrue(install_jinja_namespace_compat())
		self.assertTrue(is_installed())

	def test_parse_json_is_available_in_templates(self):
		env = frappe.get_jenv()
		out = env.from_string("{% set d = frappe.parse_json('{\"a\": 1}') %}{{ d.a }}").render({})
		self.assertEqual(out.strip(), "1")

	def test_parse_json_is_available_for_a_fresh_environment(self):
		"""The namespace is rebuilt per request - the helper must survive that."""
		from frappe.utils.safe_exec import get_safe_globals

		namespace = get_safe_globals()["frappe"]
		self.assertIn("parse_json", namespace)
		self.assertEqual(namespace["parse_json"]('{"b": 2}'), {"b": 2})

	def test_sandbox_namespace_stays_restricted(self):
		"""The shim only adds the JSON helper - it must not expose write access."""
		from frappe.utils.safe_exec import get_safe_globals

		namespace = get_safe_globals()["frappe"]
		self.assertNotIn("db_set", namespace)
		self.assertNotIn("db_commit", namespace)


if __name__ == "__main__":
	unittest.main()
