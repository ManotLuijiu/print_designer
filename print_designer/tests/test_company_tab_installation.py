# File: print_designer/tests/test_company_tab_installation.py

import os
import unittest

import frappe


class TestCompanyTabInstallation(unittest.TestCase):
    """Test the Company stamps & signatures integration

    The legacy ``print_designer.custom.company_tab`` module created a
    "Stamps & Signatures" tab break on the Company form. The tab itself is
    optional: the fields are installed as a section break and the stamps and
    signatures are managed with the "Signature Basic Information",
    "Digital Signature" and "Company Stamp" DocTypes. The tests below
    therefore assert the integration that is actually used (the client
    script, the DocTypes and the preview API) instead of a specific field
    layout.
    """

    def setUp(self):
        """Setup for each test"""
        frappe.clear_cache()

    def test_company_signature_fields_available(self):
        """Test that the Company form exposes the stamps & signatures fields"""
        meta = frappe.get_meta("Company")

        has_section = meta.has_field("company_signatures_section")
        has_tab = meta.has_field("stamps_signatures_tab")

        self.assertTrue(
            has_section or has_tab,
            "Company has no stamps & signatures section",
        )

    def test_company_client_script_registered(self):
        """Test that Company client script is registered in hooks"""
        try:
            import print_designer.hooks as hooks

            # Check if Company client script is registered
            self.assertTrue(hasattr(hooks, 'doctype_js'))
            self.assertIn('Company', hooks.doctype_js)

            # The hook accepts a list of scripts
            company_scripts = hooks.doctype_js['Company']
            if isinstance(company_scripts, str):
                company_scripts = [company_scripts]

            self.assertIn('public/js/print_format/company.js', company_scripts)

            # Every registered script has to exist
            for script in company_scripts:
                script_path = frappe.get_app_path("print_designer", script)
                self.assertTrue(
                    os.path.exists(script_path),
                    f"Company script {script} not found",
                )

        except ImportError:
            self.fail("Could not import print_designer hooks")

    def test_company_preview_css_exists(self):
        """Test that the company preview stylesheet source exists"""
        css_path = frappe.get_app_path(
            "print_designer", "public", "css", "company_preview.bundle.scss"
        )
        self.assertTrue(
            os.path.exists(css_path),
            "company_preview.bundle.scss not found",
        )

    def test_api_accessibility(self):
        """Test that Company preview API methods are accessible"""
        try:
            from print_designer.api.company_preview_api import (
                get_company_stamps_and_signatures,
                get_signature_preview_html,
                get_stamp_preview_html,
            )

            # Test with a test company
            test_company = "Test Company API"
            result = get_company_stamps_and_signatures(test_company)

            # Verify API response structure
            self.assertIsInstance(result, dict)
            self.assertIn('stamps', result)
            self.assertIn('signatures', result)
            self.assertIn('summary', result)

            # The preview helpers are callable
            self.assertTrue(callable(get_stamp_preview_html))
            self.assertTrue(callable(get_signature_preview_html))

        except ImportError as e:
            self.fail(f"Could not import Company preview API: {e}")

    def test_signature_doctypes_installed(self):
        """Test that the signature and stamp DocTypes are installed"""
        for doctype in (
            "Company Stamp",
            "Digital Signature",
            "Signature Basic Information",
        ):
            with self.subTest(doctype=doctype):
                self.assertTrue(
                    frappe.db.exists("DocType", doctype),
                    f"DocType {doctype} not found",
                )

    def test_installation_functions(self):
        """Test that the installation helpers are available

        The helpers are not called here: they create a Custom Field and
        commit, which must not happen inside a test run.
        """
        try:
            from print_designer.custom.company_tab import (
                create_company_stamps_signatures_tab,
                remove_company_stamps_signatures_tab,
            )

            # Test that functions are callable
            self.assertTrue(callable(create_company_stamps_signatures_tab))
            self.assertTrue(callable(remove_company_stamps_signatures_tab))

            # The preview API has to be importable as well
            from print_designer.api.company_preview_api import (
                get_signature_preview_html,
                get_stamp_preview_html,
            )

            self.assertTrue(callable(get_stamp_preview_html))
            self.assertTrue(callable(get_signature_preview_html))

        except ImportError as e:
            self.fail(f"Could not import Company tab installation functions: {e}")


def run_company_tab_tests():
    """
    Standalone function to run company tab installation tests
    Can be executed from Frappe console or command line
    """
    print("Starting Company Tab Installation Tests...")

    # Run the test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompanyTabInstallation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\nTest Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")

    if result.errors:
        print("\nErrors:")
        for test, error in result.errors:
            print(f"- {test}: {error}")

    return result.wasSuccessful()


def validate_company_tab_installation():
    """
    Quick validation script to check if Company tab system is properly installed
    """
    print("Validating Company Stamps & Signatures Tab Installation...")

    checks = []

    # Check if the Company form exposes the stamps & signatures fields
    meta = frappe.get_meta("Company")
    fields_available = meta.has_field("company_signatures_section") or meta.has_field(
        "stamps_signatures_tab"
    )
    checks.append(("Company Stamps & Signatures fields exist", fields_available))

    # Check if API methods are accessible
    try:
        from print_designer.api.company_preview_api import get_company_stamps_and_signatures
        api_accessible = True
    except ImportError:
        api_accessible = False
    checks.append(("Company preview API accessible", api_accessible))

    # Check if client script is registered
    try:
        import print_designer.hooks as hooks
        client_script_registered = (
            hasattr(hooks, 'doctype_js') and
            'Company' in hooks.doctype_js
        )
    except ImportError:
        client_script_registered = False
    checks.append(("Company client script registered", client_script_registered))

    # Check if the stylesheet source exists
    css_path = frappe.get_app_path(
        "print_designer", "public", "css", "company_preview.bundle.scss"
    )
    checks.append(("Company preview stylesheet exists", os.path.exists(css_path)))

    # Print results
    print("\nValidation Results:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All validation checks passed! Company Stamps & Signatures tab is properly installed.")

        # Test basic functionality
        try:
            from print_designer.api.company_preview_api import get_company_stamps_and_signatures
            companies = frappe.get_all("Company", limit=1)
            if companies:
                test_company = companies[0].name
                result = get_company_stamps_and_signatures(test_company)
                print(f"\nTest API call successful for company: {test_company}")
                print(f"Found {result['summary']['total_stamps']} stamps and {result['summary']['total_signatures']} signatures")
        except Exception as e:
            print(f"\nWarning: Could not test API functionality: {e}")
    else:
        print("\n❌ Some validation checks failed. Please review the installation.")

    return all_passed


if __name__ == "__main__":
    # Run validation if executed directly
    validate_company_tab_installation()
