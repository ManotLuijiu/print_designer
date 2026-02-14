import frappe
from frappe import _


@frappe.whitelist()
def get_pdf_generator(print_format: str) -> str:
	"""Return the pdf_generator configured for a Print Format.

	Used by the frontend Print button override to decide whether to open
	a Chrome CDP PDF (identical to the PDF button) or fall back to the
	standard browser print dialog.
	"""
	if not print_format or print_format == "Standard":
		return frappe.db.get_single_value("Print Settings", "pdf_generator") or "wkhtmltopdf"

	generator = frappe.db.get_value("Print Format", print_format, "pdf_generator")
	if generator:
		return generator

	return frappe.db.get_single_value("Print Settings", "pdf_generator") or "wkhtmltopdf"


@frappe.whitelist()
def get_print_config(print_format=None):
	"""Check TBS Print Agent availability and PDF generator type.

	Returns a config dict used by the frontend to decide:
	- Whether to open PDF preview (Chrome CDP)
	- Whether to route raw printing through TBS Print Agent (instead of QZ Tray)
	"""
	config = {
		"pdf_generator": get_pdf_generator(print_format) if print_format else "wkhtmltopdf",
		"tbs_agent_available": False,
		"raw_printing": False,
	}

	# Check if this print format uses raw printing
	if print_format and print_format != "Standard":
		config["raw_printing"] = bool(
			frappe.db.get_value("Print Format", print_format, "raw_printing")
		)

	# Dynamic check for thai_business_suite TBS Print Agent
	if "thai_business_suite" in frappe.get_installed_apps():
		try:
			tbs_config = frappe.get_single("TBS Print Agent Config")
			if tbs_config.enabled:
				agents = frappe.get_all(
					"TBS Print Agent",
					filters={"enabled": 1, "status": "Active"},
					fields=["name", "agent_name"],
				)
				if agents:
					config["tbs_agent_available"] = True
					config["default_agent"] = agents[0].name
					# Find default dot matrix printer on the first active agent
					config["default_printer"] = _get_default_printer(agents[0].name)
		except Exception:
			pass

	return config


def _get_default_printer(agent_name):
	"""Get the default printer for an agent, preferring Dot Matrix type."""
	printers = frappe.get_all(
		"TBS Print Agent Printer",
		filters={"parent": agent_name, "enabled": 1},
		fields=["printer_name", "is_default", "printer_type"],
		order_by="is_default desc",
	)

	if not printers:
		return None

	# Prefer dot matrix printer
	for p in printers:
		if p.printer_type == "Dot Matrix":
			return p.printer_name

	# Fall back to default printer
	for p in printers:
		if p.is_default:
			return p.printer_name

	# Fall back to first enabled printer
	return printers[0].printer_name


@frappe.whitelist()
def submit_raw_print(doc, name=None, print_format=None, agent=None, printer=None):
	"""Render raw_commands and submit to TBS Print Job Queue.

	This replaces QZ Tray for raw printing by routing through the
	TBS Print Agent system from thai_business_suite.
	"""
	if "thai_business_suite" not in frappe.get_installed_apps():
		frappe.throw(_("Thai Business Suite is not installed. Cannot use TBS Print Agent."))

	# Render the raw commands server-side (same as Frappe's get_rendered_raw_commands)
	from frappe.www.printview import get_rendered_raw_commands

	result = get_rendered_raw_commands(doc=doc, name=name, print_format=print_format)
	raw_commands = result.get("raw_commands")

	if not raw_commands:
		frappe.throw(_("No raw commands were generated from the print format."))

	# Resolve agent and printer if not provided
	if not agent or not printer:
		config = get_print_config(print_format)
		if not config.get("tbs_agent_available"):
			frappe.throw(_("No active TBS Print Agent found. Please configure one first."))
		agent = agent or config.get("default_agent")
		printer = printer or config.get("default_printer")

	if not agent or not printer:
		frappe.throw(_("No printer configured. Please set up a printer in TBS Print Agent."))

	# Resolve document info for the job queue
	if isinstance(name, str):
		document_type = doc
		document_name = name
	else:
		import json as json_lib
		doc_dict = json_lib.loads(doc) if isinstance(doc, str) else doc
		document_type = doc_dict.get("doctype")
		document_name = doc_dict.get("name")

	# Submit to TBS Print Job Queue
	from thai_business_suite.api.printing import submit_print_job

	return submit_print_job(
		agent=agent,
		printer=printer,
		data=raw_commands,
		job_type="Raw",
		document_type=document_type,
		document_name=document_name,
		print_format=print_format,
	)
