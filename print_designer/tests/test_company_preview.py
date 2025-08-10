# File: print_designer/tests/test_company_preview.py

import frappe
import unittest
from frappe.test_runner import make_test_records


class TestCompanyPreview(unittest.TestCase):
    """Test suite for Company Preview API system"""

    @classmethod
    def setUpClass(cls):
        """Setup test data"""
        frappe.db.rollback()
        frappe.clear_cache()

        # Create test company
        if not frappe.db.exists("Company", "Test Company Preview"):
            company = frappe.new_doc("Company")
            company.company_name = "Test Company Preview" 
            company.default_currency = "USD"
            company.country = "United States"
            company.insert()

    def setUp(self):
        """Setup for each test"""
        self.test_company = "Test Company Preview"
        
        # Clean up any existing test data
        frappe.db.delete("Company Stamp", {"company": self.test_company})
        frappe.db.delete("Digital Signature", {"company": self.test_company})
        frappe.db.delete("Signature Basic Information", {"company": self.test_company})
        frappe.db.commit()

    def test_api_get_company_stamps_and_signatures_empty(self):
        """Test API with no stamps or signatures"""
        from print_designer.api.company_preview_api import get_company_stamps_and_signatures
        
        result = get_company_stamps_and_signatures(self.test_company)
        
        self.assertIsInstance(result, dict)
        self.assertIn("stamps", result)
        self.assertIn("signatures", result)
        self.assertIn("summary", result)
        
        self.assertEqual(len(result["stamps"]), 0)
        self.assertEqual(len(result["signatures"]), 0)
        self.assertEqual(result["summary"]["total_stamps"], 0)
        self.assertEqual(result["summary"]["total_signatures"], 0)
        self.assertEqual(result["summary"]["company"], self.test_company)

    def test_api_get_company_stamps_and_signatures_with_data(self):
        """Test API with sample stamps and signatures"""
        from print_designer.api.company_preview_api import get_company_stamps_and_signatures
        
        # Create test company stamp
        stamp = frappe.new_doc("Company Stamp")
        stamp.title = "Test Official Stamp"
        stamp.company = self.test_company
        stamp.stamp_type = "Official"
        stamp.usage_purpose = "Invoice"
        stamp.is_active = 1
        stamp.description = "Test stamp for API"
        stamp.stamp_image = "/files/test_stamp.png"  # Mock image path
        stamp.insert(ignore_mandatory=True)
        
        # Create test digital signature
        signature = frappe.new_doc("Digital Signature")
        signature.title = "Test Manager Signature"
        signature.company = self.test_company
        signature.is_active = 1
        signature.description = "Test signature for API"
        signature.signature_image = "/files/test_signature.png"  # Mock image path
        signature.insert(ignore_mandatory=True)
        
        # Create test basic signature
        basic_sig = frappe.new_doc("Signature Basic Information")
        basic_sig.signature_name = "Test Basic Signature"
        basic_sig.company = self.test_company
        basic_sig.signature_category = "Signature"
        basic_sig.signature_title = "Director"
        basic_sig.is_active = 1
        basic_sig.signature_image = "/files/test_basic_signature.png"  # Mock image path
        basic_sig.insert(ignore_mandatory=True)
        
        frappe.db.commit()
        
        # Test API
        result = get_company_stamps_and_signatures(self.test_company)
        
        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertIn("stamps", result)
        self.assertIn("signatures", result)
        self.assertIn("summary", result)
        
        # Verify counts
        self.assertEqual(len(result["stamps"]), 1)
        self.assertEqual(len(result["signatures"]), 2)  # Digital + Basic
        self.assertEqual(result["summary"]["total_stamps"], 1)
        self.assertEqual(result["summary"]["total_signatures"], 2)
        
        # Verify stamp data
        stamp_data = result["stamps"][0]
        self.assertEqual(stamp_data["title"], "Test Official Stamp")
        self.assertEqual(stamp_data["stamp_type"], "Official")
        self.assertEqual(stamp_data["usage_purpose"], "Invoice")
        
        # Verify signature data
        signatures = result["signatures"]
        digital_sig = next(s for s in signatures if s["source_type"] == "Digital Signature")
        basic_sig = next(s for s in signatures if s["source_type"] == "Signature Basic Information")
        
        self.assertEqual(digital_sig["title"], "Test Manager Signature")
        self.assertEqual(basic_sig["title"], "Test Basic Signature")
        self.assertIn("Director", basic_sig["subtitle"])

    def test_api_get_stamp_preview_html(self):
        """Test stamp preview HTML generation"""
        from print_designer.api.company_preview_api import get_stamp_preview_html
        
        # Create test stamp
        stamp = frappe.new_doc("Company Stamp")
        stamp.title = "Test HTML Stamp"
        stamp.company = self.test_company
        stamp.stamp_type = "Approval"
        stamp.usage_purpose = "General"
        stamp.description = "Test stamp for HTML preview"
        stamp.is_active = 1
        stamp.stamp_image = "/files/test_html_stamp.png"  # Mock image path
        stamp.insert(ignore_mandatory=True)
        
        frappe.db.commit()
        
        # Test HTML generation
        html = get_stamp_preview_html(stamp.name)
        
        self.assertIsInstance(html, str)
        self.assertIn("Test HTML Stamp", html)
        self.assertIn("Approval", html)
        self.assertIn("General", html)
        self.assertIn("Test stamp for HTML preview", html)
        self.assertIn("stamp-preview", html)

    def test_api_get_signature_preview_html_digital(self):
        """Test digital signature preview HTML generation"""
        from print_designer.api.company_preview_api import get_signature_preview_html
        
        # Create test digital signature
        signature = frappe.new_doc("Digital Signature")
        signature.title = "Test HTML Digital Signature"
        signature.company = self.test_company
        signature.description = "Test digital signature for HTML"
        signature.is_active = 1
        signature.signature_image = "/files/test_html_digital.png"  # Mock image path
        signature.insert(ignore_mandatory=True)
        
        frappe.db.commit()
        
        # Test HTML generation
        html = get_signature_preview_html(signature.name, "Digital Signature")
        
        self.assertIsInstance(html, str)
        self.assertIn("Test HTML Digital Signature", html)
        self.assertIn("Digital Signature", html)
        self.assertIn("signature-preview", html)

    def test_api_get_signature_preview_html_basic(self):
        """Test basic signature preview HTML generation"""
        from print_designer.api.company_preview_api import get_signature_preview_html
        
        # Create test basic signature
        signature = frappe.new_doc("Signature Basic Information")
        signature.signature_name = "Test HTML Basic Signature"
        signature.company = self.test_company
        signature.signature_category = "Company Stamp"
        signature.signature_title = "Director"
        signature.is_active = 1
        signature.signature_image = "/files/test_html_basic.png"  # Mock image path
        signature.insert(ignore_mandatory=True)
        
        frappe.db.commit()
        
        # Test HTML generation  
        html = get_signature_preview_html(signature.name, "Signature Basic Information")
        
        self.assertIsInstance(html, str)
        self.assertIn("Test HTML Basic Signature", html)
        self.assertIn("Director", html)
        self.assertIn("Signature Basic Information", html)
        self.assertIn("signature-preview", html)

    def test_api_with_nonexistent_company(self):
        """Test API with non-existent company"""
        from print_designer.api.company_preview_api import get_company_stamps_and_signatures
        
        result = get_company_stamps_and_signatures("Non Existent Company")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result["stamps"]), 0)
        self.assertEqual(len(result["signatures"]), 0)
        self.assertEqual(result["summary"]["total_stamps"], 0)
        self.assertEqual(result["summary"]["total_signatures"], 0)

    def test_api_with_empty_company(self):
        """Test API with empty company parameter"""
        from print_designer.api.company_preview_api import get_company_stamps_and_signatures
        
        result = get_company_stamps_and_signatures("")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result["stamps"]), 0)
        self.assertEqual(len(result["signatures"]), 0)

    def test_api_inactive_items_filtered(self):
        """Test that inactive stamps and signatures are filtered out"""
        from print_designer.api.company_preview_api import get_company_stamps_and_signatures
        
        # Create active stamp
        active_stamp = frappe.new_doc("Company Stamp")
        active_stamp.title = "Active Stamp"
        active_stamp.company = self.test_company
        active_stamp.is_active = 1
        active_stamp.stamp_image = "/files/active_stamp.png"
        active_stamp.insert(ignore_mandatory=True)
        
        # Create inactive stamp
        inactive_stamp = frappe.new_doc("Company Stamp")
        inactive_stamp.title = "Inactive Stamp"
        inactive_stamp.company = self.test_company
        inactive_stamp.is_active = 0
        inactive_stamp.stamp_image = "/files/inactive_stamp.png"
        inactive_stamp.insert(ignore_mandatory=True)
        
        # Create active signature
        active_sig = frappe.new_doc("Digital Signature")
        active_sig.title = "Active Signature"
        active_sig.company = self.test_company
        active_sig.is_active = 1
        active_sig.signature_image = "/files/active_signature.png"
        active_sig.insert(ignore_mandatory=True)
        
        # Create inactive signature
        inactive_sig = frappe.new_doc("Digital Signature")
        inactive_sig.title = "Inactive Signature"
        inactive_sig.company = self.test_company
        inactive_sig.is_active = 0
        inactive_sig.signature_image = "/files/inactive_signature.png"
        inactive_sig.insert(ignore_mandatory=True)
        
        frappe.db.commit()
        
        # Test API only returns active items
        result = get_company_stamps_and_signatures(self.test_company)
        
        self.assertEqual(len(result["stamps"]), 1)
        self.assertEqual(len(result["signatures"]), 1)
        self.assertEqual(result["stamps"][0]["title"], "Active Stamp")
        self.assertEqual(result["signatures"][0]["title"], "Active Signature")

    def tearDown(self):
        """Cleanup after each test"""
        frappe.db.rollback()

    @classmethod  
    def tearDownClass(cls):
        """Cleanup after all tests"""
        frappe.db.rollback()


def run_company_preview_tests():
    """
    Standalone function to run company preview tests
    Can be executed from Frappe console or command line
    """
    print("Starting Company Preview API Tests...")
    
    # Run the test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompanyPreview)
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


def validate_company_preview_installation():
    """
    Validation script to check if company preview system is properly installed
    """
    print("Validating Company Preview System Installation...")
    
    checks = []
    
    # Check if API methods are accessible
    try:
        from print_designer.api.company_preview_api import get_company_stamps_and_signatures
        from print_designer.api.company_preview_api import get_stamp_preview_html
        from print_designer.api.company_preview_api import get_signature_preview_html
        api_accessible = True
    except ImportError as e:
        api_accessible = False
        print(f"Import error: {e}")
    checks.append(("API methods accessible", api_accessible))
    
    # Check if client script is registered
    hooks_registered = False
    try:
        import print_designer.hooks as hooks
        if hasattr(hooks, 'doctype_js') and 'Company' in hooks.doctype_js:
            hooks_registered = True
    except:
        pass
    checks.append(("Client script registered in hooks", hooks_registered))
    
    # Check if CSS bundle is registered
    css_registered = False
    try:
        import print_designer.hooks as hooks
        if hasattr(hooks, 'app_include_css'):
            css_registered = 'company_preview.bundle.css' in hooks.app_include_css
    except:
        pass
    checks.append(("CSS bundle registered in hooks", css_registered))
    
    # Check if required DocTypes exist
    doctypes = ["Company Stamp", "Digital Signature", "Signature Basic Information"]
    for doctype in doctypes:
        exists = frappe.db.exists("DocType", doctype)
        checks.append((f"DocType '{doctype}' exists", exists))
    
    # Print results
    print("\nValidation Results:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 All validation checks passed! Company Preview system is properly installed.")
        
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
    validate_company_preview_installation()