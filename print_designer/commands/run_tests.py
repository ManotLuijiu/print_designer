import importlib
import unittest
from pathlib import Path

import frappe
from frappe.tests.utils import toggle_test_mode

TESTS_PACKAGE = "print_designer.tests"


def discover_test_modules() -> list[str]:
    """The test modules of the app, in a stable order."""
    package = importlib.import_module(TESTS_PACKAGE)
    package_file = package.__file__
    if not package_file:
        raise frappe.ValidationError(f"The package {TESTS_PACKAGE} has no file")

    directory = Path(package_file).parent

    return [f"{TESTS_PACKAGE}.{path.stem}" for path in sorted(directory.glob("test_*.py"))]


def main(modules: list[str] | None = None) -> dict:
    """Run the Print Designer tests on the site of the current bench command.

    Frappe's own test runner preloads the test records of every installed app
    before it runs the first test. That preload dies on a site whose other
    apps carry incomplete fixture data: on the demo site HRMS is installed
    without its payroll module, so the Leave Type records that HRMS generates
    link to the Earning Component, a DocType that is not installed there, and
    the preload fails with a LinkValidationError before any Print Designer
    test has run.

    The preload is not needed for the Print Designer tests, so this command
    runs the app's own modules directly. The environment is set up the way
    Frappe's runner sets it up, so the tests behave the same way.

    bench --site <site> execute print_designer.commands.run_tests.main
    bench --site <site> execute print_designer.commands.run_tests.main --kwargs '{"modules": ["print_designer.tests.test_invoice_schedule_flow"]}'
    """
    if not frappe.db:
        frappe.connect()

    toggle_test_mode(True)
    frappe.flags.print_messages = False

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module in modules or discover_test_modules():
        suite.addTests(loader.loadTestsFromName(module))

    result = unittest.TextTestRunner(verbosity=1).run(suite)
    frappe.db.rollback()

    summary = {
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
    }
    print()
    print(f"Print Designer tests: {summary}")

    if not result.wasSuccessful():
        raise frappe.ValidationError(f"The Print Designer tests failed: {summary}")

    return summary
