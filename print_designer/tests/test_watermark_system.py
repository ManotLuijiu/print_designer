# File: print_designer/tests/test_watermark_system.py

import unittest

import frappe


def get_watermark_settings():
    """Return the Watermark Settings document (or None).

    The DocType is not a Single DocType, so `frappe.get_single` and
    `frappe.db.exists(dt, dt)` do not resolve the record. The record is
    looked up by its actual name.
    """
    name = frappe.db.get_value("Watermark Settings", {}, "name")
    if not name:
        return None
    return frappe.get_doc("Watermark Settings", name)


class TestWatermarkSystem(unittest.TestCase):
    """Test suite for watermark DocType system"""

    @classmethod
    def setUpClass(cls):
        """Setup test data"""
        frappe.db.rollback()
        frappe.clear_cache()

        # Create test print format
        if not frappe.db.exists("Print Format", "Test Watermark Format"):
            print_format = frappe.new_doc("Print Format")
            print_format.name = "Test Watermark Format"
            print_format.doc_type = "Sales Invoice"
            print_format.module = "Print Designer"
            print_format.standard = "No"
            print_format.html = "<div>Test Print Format</div>"
            print_format.insert()

        # The print format is referenced by the print format configs, it has
        # to survive the rollback of every single test.
        frappe.db.commit()

    def get_settings(self):
        """Return the Watermark Settings document."""
        return get_watermark_settings()

    def setUp(self):
        """Setup for each test

        The Watermark Settings record of the site is reused and reset inside
        the test transaction. The test never deletes the record and never
        commits, so the site data is restored by the rollback of the tearDown.
        """
        settings = get_watermark_settings()
        if settings is None:
            settings = frappe.new_doc("Watermark Settings")
            settings.insert(ignore_permissions=True)

        # Reset the record for the test
        settings.watermark_templates = []
        settings.print_format_configs = []
        settings.enabled = 1
        settings.default_mode = "Copy on All Pages"
        settings.default_font_size = 24
        settings.default_position = "Top Right"
        settings.default_font_family = "Sarabun"
        settings.default_color = "#999999"
        settings.default_opacity = 0.6
        settings.save(ignore_permissions=True)

        self.settings_name = settings.name

    def test_watermark_settings_creation(self):
        """Test Watermark Settings DocType creation and validation"""
        settings = self.get_settings()
        self.assertTrue(settings.enabled)
        self.assertEqual(settings.default_mode, "Copy on All Pages")
        self.assertEqual(settings.default_font_size, 24)
        self.assertEqual(settings.default_position, "Top Right")

    def test_watermark_settings_validation(self):
        """Test validation rules for Watermark Settings"""
        settings = self.get_settings()

        # Test invalid font size
        settings.default_font_size = 100
        with self.assertRaises(frappe.ValidationError):
            settings.save()

        # Test invalid opacity
        settings.default_font_size = 24
        settings.default_opacity = 1.5
        with self.assertRaises(frappe.ValidationError):
            settings.save()

    def test_watermark_template_creation(self):
        """Test Watermark Template creation"""
        settings = self.get_settings()

        template_data = {
            "template_name": "Test Template",
            "watermark_mode": "Original on First Page",
            "font_size": 28,
            "position": "Top Left",
            "font_family": "Arial",
            "color": "#ff0000",
            "opacity": 0.8,
            "custom_text": "TEST",
            "description": "Test template",
        }

        settings.append("watermark_templates", template_data)
        settings.save()

        # Verify template was added
        self.assertEqual(len(settings.watermark_templates), 1)
        template = settings.watermark_templates[0]
        self.assertEqual(template.template_name, "Test Template")
        self.assertEqual(template.watermark_mode, "Original on First Page")
        self.assertEqual(template.font_size, 28)

    def test_print_format_config_creation(self):
        """Test Print Format specific configuration"""
        settings = self.get_settings()

        config_data = {
            "print_format": "Test Watermark Format",
            "watermark_template": None,
            "override_settings": 1,
            "watermark_mode": "Copy on All Pages",
            "font_size": 32,
            "position": "Bottom Center",
            "color": "#0000ff",
        }

        settings.append("print_format_configs", config_data)
        settings.save()

        # Verify config was added
        self.assertEqual(len(settings.print_format_configs), 1)
        config = settings.print_format_configs[0]
        self.assertEqual(config.print_format, "Test Watermark Format")
        self.assertTrue(config.override_settings)
        self.assertEqual(config.font_size, 32)

    def test_api_get_watermark_config(self):
        """Test API method for getting watermark configuration"""
        from print_designer.api.watermark import get_watermark_config_for_print_format

        # Test default configuration
        config = get_watermark_config_for_print_format("Test Watermark Format")
        self.assertTrue(config["enabled"])
        self.assertEqual(config["source"], "default")
        self.assertEqual(config["watermark_mode"], "Copy on All Pages")
        self.assertEqual(config["font_size"], 24)

    def test_api_get_watermark_config_with_template(self):
        """Test API with template configuration"""
        from print_designer.api.watermark import (
            get_watermark_config_for_print_format,
            save_print_format_watermark_config,
        )

        # Create template first
        settings = self.get_settings()
        template_data = {
            "template_name": "API Test Template",
            "watermark_mode": "Original on First Page",
            "font_size": 30,
            "position": "Middle Center",
            "color": "#00ff00",
            "opacity": 0.5,
        }
        settings.append("watermark_templates", template_data)
        settings.save()

        # Create print format config using template
        result = save_print_format_watermark_config(
            "Test Watermark Format",
            {
                "watermark_template": "API Test Template",
                "override_settings": 0,
            },
        )
        self.assertTrue(result["success"])

        # Test API response
        config = get_watermark_config_for_print_format("Test Watermark Format")
        self.assertTrue(config["enabled"])
        self.assertEqual(config["source"], "template")
        self.assertEqual(config["template_name"], "API Test Template")
        self.assertEqual(config["watermark_mode"], "Original on First Page")
        self.assertEqual(config["font_size"], 30)

    def test_api_get_watermark_config_with_override(self):
        """Test API with override configuration"""
        from print_designer.api.watermark import get_watermark_config_for_print_format

        settings = self.get_settings()

        # Create print format config with overrides
        config_data = {
            "print_format": "Test Watermark Format",
            "watermark_template": None,
            "override_settings": 1,
            "watermark_mode": "Copy on All Pages",
            "font_size": 36,
            "position": "Bottom Left",
            "color": "#ff00ff",
            "opacity": 0.9,
            "custom_text": "OVERRIDE TEST",
        }
        settings.append("print_format_configs", config_data)
        settings.save()

        # Test API response
        config = get_watermark_config_for_print_format("Test Watermark Format")
        self.assertTrue(config["enabled"])
        self.assertEqual(config["source"], "override")
        self.assertEqual(config["watermark_mode"], "Copy on All Pages")
        self.assertEqual(config["font_size"], 36)
        self.assertEqual(config["custom_text"], "OVERRIDE TEST")

    def test_api_get_available_templates(self):
        """Test API for getting available templates"""
        from print_designer.api.watermark import get_available_watermark_templates

        # Add multiple templates
        settings = self.get_settings()

        templates = [
            {
                "template_name": "Template 1",
                "watermark_mode": "Original on First Page",
                "description": "First template",
            },
            {
                "template_name": "Template 2",
                "watermark_mode": "Copy on All Pages",
                "description": "Second template",
            },
        ]

        for template_data in templates:
            settings.append("watermark_templates", template_data)

        settings.save()

        # Test API response
        available_templates = get_available_watermark_templates()
        self.assertEqual(len(available_templates), 2)
        self.assertEqual(available_templates[0]["name"], "Template 1")
        self.assertEqual(available_templates[1]["name"], "Template 2")

    def test_api_save_print_format_config(self):
        """Test API for saving print format configuration"""
        from print_designer.api.watermark import save_print_format_watermark_config

        config_data = {
            "watermark_template": None,
            "override_settings": 1,
            "watermark_mode": "Copy on All Pages",
            "font_size": 26,
            "position": "Top Center",
            "color": "#333333",
            "opacity": 0.7,
        }

        result = save_print_format_watermark_config(
            "Test Watermark Format", config_data
        )
        self.assertTrue(result["success"])

        # Verify saved configuration
        settings = self.get_settings()
        self.assertEqual(len(settings.print_format_configs), 1)

        config = settings.print_format_configs[0]
        self.assertEqual(config.print_format, "Test Watermark Format")
        self.assertEqual(config.font_size, 26)
        self.assertEqual(config.position, "Top Center")

    def test_api_create_watermark_template(self):
        """Test API for creating watermark template"""
        from print_designer.api.watermark import create_watermark_template

        template_data = {
            "template_name": "New API Template",
            "watermark_mode": "Original on First Page",
            "font_size": 22,
            "position": "Bottom Right",
            "font_family": "Times New Roman",
            "color": "#800080",
            "opacity": 0.4,
            "description": "Created via API",
        }

        result = create_watermark_template(template_data)
        self.assertTrue(result["success"])
        self.assertEqual(result["template_name"], "New API Template")

        # Verify template was created
        settings = self.get_settings()
        template_names = [t.template_name for t in settings.watermark_templates]
        self.assertIn("New API Template", template_names)

    def test_watermark_disabled_scenario(self):
        """Test behavior when watermark system is disabled"""
        from print_designer.api.watermark import get_watermark_config_for_print_format

        # Disable watermark system
        settings = self.get_settings()
        settings.enabled = 0
        settings.save()

        # Test API response
        config = get_watermark_config_for_print_format("Test Watermark Format")
        self.assertFalse(config["enabled"])

    def test_nonexistent_print_format(self):
        """Test API with non-existent print format"""
        from print_designer.api.watermark import get_watermark_config_for_print_format

        config = get_watermark_config_for_print_format("Non Existent Format")
        self.assertTrue(config["enabled"])  # Should return default settings
        self.assertEqual(config["source"], "default")

    def tearDown(self):
        """Cleanup after each test"""
        frappe.db.rollback()

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        frappe.db.rollback()

        # Remove the test print format again
        if frappe.db.exists("Print Format", "Test Watermark Format"):
            frappe.delete_doc("Print Format", "Test Watermark Format", ignore_permissions=True)
            frappe.db.commit()


def run_watermark_system_tests():
    """
    Standalone function to run watermark system tests
    Can be executed from Frappe console or command line
    """
    print("Starting Watermark System Tests...")

    # Run the test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWatermarkSystem)
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


def validate_watermark_installation():
    """
    Validation script to check if watermark system is properly installed
    """
    print("Validating Watermark System Installation...")

    checks = []

    # Check if DocTypes exist
    doctypes = [
        "Watermark Settings",
        "Watermark Template",
        "Print Format Watermark Config",
    ]
    for doctype in doctypes:
        exists = frappe.db.exists("DocType", doctype)
        checks.append((f"DocType '{doctype}' exists", exists))

    # Check if Watermark Settings document exists
    settings_exists = get_watermark_settings() is not None
    checks.append(("Watermark Settings document exists", settings_exists))

    # Check API methods are accessible
    try:
        from print_designer.api.watermark import get_watermark_config_for_print_format

        api_accessible = callable(get_watermark_config_for_print_format)
    except ImportError:
        api_accessible = False
    checks.append(("API methods accessible", api_accessible))

    # Check if JS files are accessible
    try:
        js_path = frappe.get_app_path(
            "print_designer", "public", "js", "print_watermark.js"
        )
        import os

        js_exists = os.path.exists(js_path)
    except Exception:
        js_exists = False
    checks.append(("JavaScript files exist", js_exists))

    # Check if CSS files are accessible
    try:
        css_path = frappe.get_app_path(
            "print_designer", "public", "css", "watermark.css"
        )
        import os

        css_exists = os.path.exists(css_path)
    except Exception:
        css_exists = False
    checks.append(("CSS files exist", css_exists))

    # Print results
    print("\nValidation Results:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print(
            "\n🎉 All validation checks passed! Watermark system is properly installed."
        )

        # Test basic functionality
        try:
            if settings_exists:
                settings = get_watermark_settings()
                print(
                    f"\nWatermark system status: {'Enabled' if settings.enabled else 'Disabled'}"
                )
                print(f"Default mode: {settings.default_mode}")
                print(f"Templates configured: {len(settings.watermark_templates)}")
        except Exception as e:
            print(f"\nWarning: Could not retrieve settings details: {e}")
    else:
        print("\n❌ Some validation checks failed. Please review the installation.")

    return all_passed


if __name__ == "__main__":
    # Run validation if executed directly
    validate_watermark_installation()
