__version__ = "1.25.0"


def _install_jinja_namespace_compat():
	"""Make ``frappe.parse_json`` available inside Jinja templates.

	Exported Print Designer templates parse their embedded design data with
	``frappe.parse_json(...)``. Frappe v16 restricts the ``frappe`` namespace
	that is exposed to Jinja, so those templates fail to render with
	``AttributeError: module has no attribute 'parse_json'``.

	The shim is installed when the app package is imported, so it applies to
	every process (web, worker, scheduler) and to every render path (PDF
	pipeline, desk print view, preview).
	"""
	try:
		from print_designer.utils.jinja_namespace import install_jinja_namespace_compat

		install_jinja_namespace_compat()
	except Exception:
		# never break app import: the shim only restores a template helper
		pass


_install_jinja_namespace_compat()
