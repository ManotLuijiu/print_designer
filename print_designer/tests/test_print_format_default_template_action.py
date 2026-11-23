"""The Desk actions of a saved Print Designer format (Phase 2).

The plan of Phase 2 asks for three things on the Print Format form:

* the action **Export as Default Template**,
* the existing backup action **Export Format**,
* the existing action **Import Format**.

The menu of a saved Print Designer format carries each of them exactly
once, and the backup action keeps its own endpoint.  The executable proof
of the behaviour of the actions is
``print_designer/tests/test_print_format_default_template_action.cjs``;
this module reads the registered client code, so the check also runs with
the suite.
"""

import pathlib
import shutil
import subprocess
import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

CLIENT_SCRIPTS = [
    "public/js/print_format/print_format.js",
    "public/js/print_format/print_format_conversion_dialog.js",
]

EXPORT_TEMPLATE_LABEL = '__("Export as Default Template")'
EXPORT_BACKUP_LABEL = '__("Export Format")'
IMPORT_LABEL = '__("Import Format")'

TEMPLATE_EXPORT_METHOD = "print_designer.api.default_template_export.export_as_default_template"
BACKUP_EXPORT_METHOD = "print_designer.api.print_format_export_import.export_print_format"

# The behavioural proof of the actions.  It runs the client code of the
# form in a Node sandbox.
CLIENT_PROOF = "print_designer/tests/test_print_format_default_template_action.cjs"


def print_format_client_code() -> str:
    """The client code of the Print Format form, as the desk assembles it.

    The hooks of every app are read fresh, so the result does not depend
    on the cache of the site.
    """
    from frappe.desk.form.meta import get_code_files_via_hooks

    code = []
    for path in get_code_files_via_hooks("doctype_js", "Print Format"):
        code.append(frappe.read_file(path) or "")

    return "\n".join(code)


def menu_item_labels(code: str) -> list[str]:
    """The label of every menu item that the code registers."""
    labels = []
    index = code.find("add_menu_item")

    while index != -1:
        start = code.find("(", index)
        if start == -1:
            break

        depth = 0
        end = None
        for position in range(start, len(code)):
            if code[position] == "(":
                depth += 1
            elif code[position] == ")":
                depth -= 1
                if depth == 0:
                    end = position
                    break

        if end is None:
            break

        arguments = code[start + 1 : end]
        labels.append(arguments.split(",")[0].strip())
        index = code.find("add_menu_item", end)

    return labels


class TestThePrintFormatDeskActions(FrappeTestCase):
    """The actions of a saved Print Designer format."""

    def setUp(self):
        self.code = print_format_client_code()
        self.labels = menu_item_labels(self.code)

    def test_the_client_scripts_are_registered(self):
        hooks = frappe.get_hooks("doctype_js", default={}, app_name="print_designer")

        for script in CLIENT_SCRIPTS:
            self.assertIn(script, hooks["Print Format"])

    def test_the_export_as_default_template_is_registered_once(self):
        occurrences = [label for label in self.labels if label == EXPORT_TEMPLATE_LABEL]

        self.assertEqual(
            len(occurrences),
            1,
            "the action that exports a default template is not registered exactly once",
        )

    def test_the_backup_export_is_still_registered_once(self):
        occurrences = [label for label in self.labels if label == EXPORT_BACKUP_LABEL]

        self.assertEqual(
            len(occurrences),
            1,
            "the backup action of the format is not registered exactly once",
        )

    def test_the_import_is_still_registered_once(self):
        occurrences = [label for label in self.labels if label == IMPORT_LABEL]

        self.assertEqual(
            len(occurrences),
            1,
            "the import action of the format is not registered exactly once",
        )

    def test_the_export_of_a_template_calls_its_endpoint(self):
        self.assertIn(TEMPLATE_EXPORT_METHOD, self.code)

    def test_the_backup_export_calls_its_own_endpoint(self):
        """The backup action keeps the endpoint that it always had."""
        self.assertIn(BACKUP_EXPORT_METHOD, self.code)

    def test_the_export_asks_for_the_name_the_filename_and_the_category(self):
        for fieldname in ("template_name", "filename", "category"):
            self.assertIn(f'fieldname: "{fieldname}"', self.code)

    @unittest.skipUnless(shutil.which("node"), "node is not available on this host")
    def test_the_client_proof_runs(self):
        """The behavioural proof of the actions runs with the suite.

        The proof is a Node script that runs the client code of the
        actions.  Without this test the proof would only run when it is
        called by hand, and a client script that the browser refuses
        would stay unnoticed.
        """
        app_path = pathlib.Path(frappe.get_app_path("print_designer")).parent

        result = subprocess.run(
            ["node", str(app_path / CLIENT_PROOF)],
            cwd=app_path,
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
