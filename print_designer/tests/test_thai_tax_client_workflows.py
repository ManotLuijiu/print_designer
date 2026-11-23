"""The client workflows of the Thai tax are covered by the test suite.

The server side of the Thai tax owns the rules, and the client side of the
settings and of the intake of a tax invoice only shows the state of the
document and asks the server to change it.  The two client scripts below are
therefore checked with the real script in a sandbox with a stubbed ``frappe``,
the same way the client of the withholding tax is checked:

    print_designer/tests/test_thai_tax_invoice_intake.cjs
    print_designer/tests/test_thai_tax_settings_client.cjs

The tests are written as a node script, so they can be run by hand with

    node print_designer/tests/test_thai_tax_invoice_intake.cjs

and they are also run by this module, so the client workflow is part of the
suite of the app and not only a proof that has to be repeated by hand.
"""

import shutil
import subprocess
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).parents[2]
TESTS_DIR = APP_ROOT / "print_designer/tests"

CLIENT_SCRIPTS = (
    "test_thai_tax_invoice_intake.cjs",
    "test_thai_tax_settings_client.cjs",
)


class TestThaiTaxClientWorkflows(unittest.TestCase):
    """The client scripts of the Thai tax run and pass their own checks."""

    def test_every_client_script_passes(self):
        node = shutil.which("node")
        if not node:
            raise unittest.SkipTest("node is not available")

        for script in CLIENT_SCRIPTS:
            with self.subTest(script=script):
                path = TESTS_DIR / script
                self.assertTrue(path.exists(), f"{script} is missing")

                completed = subprocess.run(
                    [node, str(path)],
                    cwd=APP_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )

                self.assertEqual(
                    completed.returncode,
                    0,
                    f"{script} failed:\n{completed.stdout}\n{completed.stderr}",
                )
