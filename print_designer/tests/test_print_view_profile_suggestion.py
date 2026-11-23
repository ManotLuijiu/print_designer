"""The advisory suggestion of the print view.

The plan of Phase 2 asks that the print view preselects a matching format
"only when nothing else was chosen" and that it "never overwrites the
selection of the user".

The server side of the suggestion is covered by
``print_designer/tests/test_print_format_suggestion.py``.  The behaviour
of the client is covered by
``print_designer/tests/test_print_view_profile_suggestion.cjs``, which
runs the real client script of the print view in a sandbox.  This module
runs that proof, so the behaviour of the client is part of the suite of
the app and not only a proof that has to be repeated by hand.
"""

import pathlib
import shutil
import subprocess
import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

# The behavioural proof of the suggestion of the print view.
CLIENT_PROOF = "print_designer/tests/test_print_view_profile_suggestion.cjs"


class TestThePrintViewProfileSuggestion(FrappeTestCase):
    """The suggestion of the print view is advisory."""

    @unittest.skipUnless(shutil.which("node"), "node is not available on this host")
    def test_the_client_proof_runs(self):
        """The behavioural proof of the print view runs with the suite.

        The proof runs the client script of the print view.  Without this
        test the proof would only run when it is called by hand, and a
        client script that the browser refuses would stay unnoticed.
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
