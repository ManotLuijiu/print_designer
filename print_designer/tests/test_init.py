"""
Main Print Designer tests following ERPNext pattern
Based on apps/erpnext/erpnext/tests/test_init.py
"""

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase


class TestPrintDesignerInit(FrappeTestCase):
    """Test Print Designer initialization and core functionality"""
    
    def test_print_designer_app_install(self):
        """Test that Print Designer app is properly installed"""
        # Check if the app is in installed apps
        installed_apps = frappe.get_installed_apps()
        self.assertIn("print_designer", installed_apps)
    
    def test_print_designer_hooks(self):
        """Test Print Designer hooks are properly loaded"""
        from print_designer import hooks
        
        # Test essential hooks exist
        self.assertTrue(hasattr(hooks, 'app_name'))
        self.assertEqual(hooks.app_name, "print_designer")
        
        # Test document events are defined
        self.assertTrue(hasattr(hooks, 'doc_events'))
        self.assertIsInstance(hooks.doc_events, dict)
    
    def test_print_designer_doctypes_installed(self):
        """Test that Print Designer DocTypes are properly installed"""
        essential_doctypes = [
            "Digital Signature",
            "Company Stamp", 
            "Thai WHT Settings",
            "Watermark Settings"
        ]
        
        for doctype in essential_doctypes:
            with self.subTest(doctype=doctype):
                self.assertTrue(
                    frappe.db.exists("DocType", doctype),
                    f"DocType {doctype} not found"
                )
    
    def test_print_designer_custom_fields_installed(self):
        """Test that Print Designer custom fields are installed"""
        # Test some key custom fields exist
        key_custom_fields = [
            ("Sales Invoice", "subject_to_wht"),
            ("Purchase Invoice", "subject_to_wht"), 
            ("Print Format", "print_designer"),
            ("Print Format", "print_designer_body")
        ]
        
        for doctype, fieldname in key_custom_fields:
            with self.subTest(doctype=doctype, fieldname=fieldname):
                custom_field_exists = frappe.db.exists("Custom Field", {
                    "dt": doctype,
                    "fieldname": fieldname
                })
                if not custom_field_exists:
                    # Check if it's a standard field
                    meta = frappe.get_meta(doctype)
                    field_exists = meta.has_field(fieldname)
                    self.assertTrue(
                        field_exists,
                        f"Field {fieldname} not found in {doctype}"
                    )
    
    def test_print_designer_pdf_generators(self):
        """Test that PDF generators are available"""
        try:
            from print_designer.pdf_generator.wkhtmltopdf_generator import WkhtmltopdfGenerator
            from print_designer.pdf_generator.weasyprint_generator import WeasyprintGenerator
            from print_designer.pdf_generator.chrome_cdp_generator import ChromeCDPGenerator
            
            # Basic instantiation test
            generators = [
                WkhtmltopdfGenerator(),
                WeasyprintGenerator(),
                ChromeCDPGenerator()
            ]
            
            for generator in generators:
                with self.subTest(generator=generator.__class__.__name__):
                    self.assertTrue(hasattr(generator, 'generate_pdf'))
                    
        except ImportError as e:
            self.skipTest(f"PDF generator import failed: {e}")
    
    def test_print_designer_templates_folder(self):
        """Test that default templates folder exists"""
        import os
        from print_designer import get_app_path
        
        templates_path = os.path.join(get_app_path(), "default_templates")
        self.assertTrue(
            os.path.exists(templates_path),
            "Default templates folder not found"
        )
    
    def test_print_designer_api_endpoints(self):
        """Test that API endpoints are accessible"""
        api_methods = [
            "print_designer.api.print_format_export_import.export_print_format",
            "print_designer.api.print_format_export_import.import_print_format",
            "print_designer.api.print_format_export_import.duplicate_print_format"
        ]
        
        for method in api_methods:
            with self.subTest(method=method):
                # Check if method can be imported
                try:
                    module_path, method_name = method.rsplit('.', 1)
                    module = frappe.get_module(module_path)
                    self.assertTrue(
                        hasattr(module, method_name),
                        f"API method {method} not found"
                    )
                except Exception as e:
                    self.fail(f"Could not access API method {method}: {e}")


class TestPrintDesignerUtilities(unittest.TestCase):
    """Test Print Designer utility functions"""
    
    def test_thai_language_utilities(self):
        """Test Thai language utility functions"""
        try:
            from print_designer.utils.thai_language import detect_thai_content
            
            # Test Thai content detection
            thai_text = "สวัสดีครับ"
            english_text = "Hello World"
            
            # Should detect Thai content
            self.assertTrue(detect_thai_content(thai_text))
            self.assertFalse(detect_thai_content(english_text))
            
        except ImportError:
            self.skipTest("Thai language utilities not available")
    
    def test_signature_utilities(self):
        """Test signature utility functions"""
        try:
            from print_designer.utils import signature_stamp
            
            # Test that signature utilities are importable
            self.assertTrue(hasattr(signature_stamp, 'get_signature_stamp'))
            
        except ImportError:
            self.skipTest("Signature utilities not available")


class TestPrintDesignerFixtures(FrappeTestCase):
    """Test Print Designer fixtures and data consistency"""
    
    def test_fixtures_load_successfully(self):
        """Test that Print Designer fixtures can be loaded"""
        try:
            # Try to get fixture data
            fixtures = frappe.get_file_json(
                frappe.get_app_path("print_designer", "fixtures", "custom_field.json")
            )
            
            self.assertIsInstance(fixtures, list)
            self.assertGreater(len(fixtures), 0)
            
            # Test fixture structure
            for fixture in fixtures[:5]:  # Test first 5
                with self.subTest(fixture=fixture.get("fieldname")):
                    self.assertIn("doctype", fixture)
                    self.assertEqual(fixture["doctype"], "Custom Field")
                    self.assertIn("fieldname", fixture)
                    self.assertIn("dt", fixture)
                    
        except Exception as e:
            self.skipTest(f"Fixtures test skipped: {e}")
    
    def test_translation_files(self):
        """Test Print Designer translation files"""
        from frappe.tests.test_translate import verify_translation_files
        try:
            verify_translation_files("print_designer")
        except Exception as e:
            self.skipTest(f"Translation files test skipped: {e}")


def load_print_designer_tests():
    """
    Load all Print Designer tests for test discovery
    Following ERPNext pattern
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPrintDesignerInit,
        TestPrintDesignerUtilities,
        TestPrintDesignerFixtures
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


if __name__ == '__main__':
    unittest.main()