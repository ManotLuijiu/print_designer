# File: print_designer/tests/test_company_tab_installation.py

import frappe
import unittest

class TestCompanyTabInstallation(unittest.TestCase):
    """Test Company Stamps & Signatures tab installation"""
    
    def setUp(self):
        """Setup for each test"""
        frappe.clear_cache()
    
    def test_company_tab_exists(self):
        """Test that the Company Stamps & Signatures tab custom field exists"""
        
        # Check if custom field exists
        tab_field = frappe.db.exists("Custom Field", {
            "dt": "Company", 
            "fieldname": "stamps_signatures_tab"
        })
        
        self.assertTrue(tab_field, "Company Stamps & Signatures tab custom field should exist")
        
        # Get the custom field details
        if tab_field:
            field_doc = frappe.get_doc("Custom Field", tab_field)
            self.assertEqual(field_doc.fieldtype, "Tab Break")
            self.assertEqual(field_doc.label, "Stamps & Signatures")
            self.assertEqual(field_doc.dt, "Company")
    
    def test_company_client_script_registered(self):
        """Test that Company client script is registered in hooks"""
        
        try:
            import print_designer.hooks as hooks
            
            # Check if Company client script is registered
            self.assertTrue(hasattr(hooks, 'doctype_js'))
            self.assertIn('Company', hooks.doctype_js)
            self.assertEqual(
                hooks.doctype_js['Company'], 
                'print_designer/client_scripts/company.js'
            )
            
        except ImportError:
            self.fail("Could not import print_designer hooks")
    
    def test_css_bundle_registered(self):
        """Test that company_preview CSS bundle is registered"""
        
        try:
            import print_designer.hooks as hooks
            
            # Check if CSS bundle is registered
            self.assertTrue(hasattr(hooks, 'app_include_css'))
            self.assertIn('company_preview.bundle.css', hooks.app_include_css)
            
        except ImportError:
            self.fail("Could not import print_designer hooks")
    
    def test_api_accessibility(self):
        """Test that Company preview API methods are accessible"""
        
        try:
            from print_designer.api.company_preview_api import (
                get_company_stamps_and_signatures,
                get_stamp_preview_html,
                get_signature_preview_html
            )
            
            # Test with a test company
            test_company = "Test Company API"
            result = get_company_stamps_and_signatures(test_company)
            
            # Verify API response structure
            self.assertIsInstance(result, dict)
            self.assertIn('stamps', result)
            self.assertIn('signatures', result)
            self.assertIn('summary', result)
            
        except ImportError as e:
            self.fail(f"Could not import Company preview API: {e}")
    
    def test_installation_functions(self):
        """Test that installation functions work correctly"""
        
        try:
            from print_designer.custom.company_tab import (
                create_company_stamps_signatures_tab,
                remove_company_stamps_signatures_tab
            )
            
            # Test that functions are callable
            self.assertTrue(callable(create_company_stamps_signatures_tab))
            self.assertTrue(callable(remove_company_stamps_signatures_tab))
            
            # Test creation (should return True since it already exists)
            result = create_company_stamps_signatures_tab()
            self.assertTrue(result)
            
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
    
    print(f"\nTest Results:")
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
    
    # Check if custom field exists
    tab_exists = frappe.db.exists("Custom Field", {
        "dt": "Company", 
        "fieldname": "stamps_signatures_tab"
    })
    checks.append(("Company Stamps & Signatures tab custom field exists", tab_exists))
    
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
    
    # Check if CSS bundle is registered
    try:
        import print_designer.hooks as hooks
        css_registered = (
            hasattr(hooks, 'app_include_css') and 
            'company_preview.bundle.css' in hooks.app_include_css
        )
    except ImportError:
        css_registered = False
    checks.append(("Company preview CSS bundle registered", css_registered))
    
    # Print results
    print("\nValidation Results:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 All validation checks passed! Company Stamps & Signatures tab is properly installed.")
        
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
        print(f"\n❌ Some validation checks failed. Please review the installation.")
    
    return all_passed


if __name__ == "__main__":
    # Run validation if executed directly
    validate_company_tab_installation()