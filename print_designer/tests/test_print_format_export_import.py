"""
Test cases for Print Designer Export/Import functionality
Following ERPNext testing standards from apps/erpnext/erpnext/tests/
"""

import json
import unittest
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.api.print_format_export_import import (
    export_print_format,
    import_print_format, 
    duplicate_print_format,
    validate_export_data
)


class TestPrintFormatExportImport(FrappeTestCase):
    """Test Print Designer Export/Import functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data"""
        super().setUpClass()
        cls.test_doctype = "Sales Invoice"
        cls.test_format_name = "Test Print Designer Format"
        
    def setUp(self):
        """Create test print format for each test"""
        # Clean up any existing test format
        if frappe.db.exists("Print Format", self.test_format_name):
            frappe.delete_doc("Print Format", self.test_format_name, force=True)
            
        # Create a test Print Designer format
        self.test_format = frappe.get_doc({
            "doctype": "Print Format",
            "name": self.test_format_name,
            "doc_type": self.test_doctype,
            "print_designer": 1,
            "print_designer_header": json.dumps({
                "elements": [{"type": "text", "content": "Test Header"}]
            }),
            "print_designer_body": json.dumps({
                "elements": [
                    {"type": "field", "fieldname": "name", "label": "Invoice No"},
                    {"type": "text", "content": "Test Body Content"}
                ]
            }),
            "print_designer_after_table": json.dumps({
                "elements": [{"type": "text", "content": "Test Footer"}]
            }),
            "print_designer_settings": json.dumps({
                "page_size": "A4",
                "orientation": "portrait",
                "margins": {"top": 10, "bottom": 10, "left": 15, "right": 15}
            })
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        
    def tearDown(self):
        """Clean up test data"""
        # Clean up test formats
        test_formats = [
            self.test_format_name,
            f"{self.test_format_name} Copy",
            f"{self.test_format_name} Imported"
        ]
        
        for format_name in test_formats:
            if frappe.db.exists("Print Format", format_name):
                frappe.delete_doc("Print Format", format_name, force=True)
        frappe.db.commit()
    
    def test_export_print_format_success(self):
        """Test successful export of Print Designer format"""
        result = export_print_format(self.test_format_name)
        
        # Validate export structure
        self.assertIsInstance(result, dict)
        self.assertIn("print_format", result)
        self.assertIn("metadata", result)
        self.assertIn("version", result)
        
        # Validate metadata
        metadata = result["metadata"]
        self.assertEqual(metadata["format_name"], self.test_format_name)
        self.assertEqual(metadata["doc_type"], self.test_doctype)
        self.assertIn("export_date", metadata)
        self.assertIn("exported_by", metadata)
        
        # Validate print format data
        print_format_data = result["print_format"]
        self.assertEqual(print_format_data["name"], self.test_format_name)
        self.assertEqual(print_format_data["print_designer"], 1)
        self.assertIn("print_designer_body", print_format_data)
    
    def test_export_nonexistent_format(self):
        """Test export of non-existent format raises error"""
        with self.assertRaises(frappe.DoesNotExistError):
            export_print_format("Non Existent Format")
    
    def test_export_non_designer_format(self):
        """Test export of non-Print Designer format raises error"""
        # Create a regular print format (not Print Designer)
        regular_format = frappe.get_doc({
            "doctype": "Print Format",
            "name": "Regular Format",
            "doc_type": "Sales Invoice",
            "print_designer": 0,
            "html": "<div>Regular HTML format</div>"
        }).insert(ignore_permissions=True)
        
        try:
            with self.assertRaises(frappe.ValidationError) as context:
                export_print_format("Regular Format")
            self.assertIn("Print Designer format", str(context.exception))
        finally:
            frappe.delete_doc("Print Format", "Regular Format", force=True)
    
    def test_validate_export_data_valid(self):
        """Test validation of valid export data"""
        export_data = export_print_format(self.test_format_name)
        export_json = json.dumps(export_data)
        
        # Should not raise any exception
        validate_export_data(export_json)
    
    def test_validate_export_data_invalid_json(self):
        """Test validation of invalid JSON"""
        with self.assertRaises(frappe.ValidationError) as context:
            validate_export_data("invalid json")
        self.assertIn("Invalid JSON", str(context.exception))
    
    def test_validate_export_data_missing_fields(self):
        """Test validation of export data with missing required fields"""
        invalid_data = json.dumps({"invalid": "data"})
        
        with self.assertRaises(frappe.ValidationError) as context:
            validate_export_data(invalid_data)
        self.assertIn("Missing required field", str(context.exception))
    
    def test_import_print_format_success(self):
        """Test successful import of Print Designer format"""
        # Export first
        export_data = export_print_format(self.test_format_name)
        export_json = json.dumps(export_data)
        
        # Delete original
        frappe.delete_doc("Print Format", self.test_format_name, force=True)
        
        # Import with new name
        imported_name = import_print_format(
            export_json, 
            new_name=f"{self.test_format_name} Imported"
        )
        
        # Validate import
        imported_format = frappe.get_doc("Print Format", imported_name)
        self.assertEqual(imported_format.doc_type, self.test_doctype)
        self.assertEqual(imported_format.print_designer, 1)
        self.assertIsNotNone(imported_format.print_designer_body)
    
    def test_import_with_existing_name_auto_rename(self):
        """Test import with existing name gets auto-renamed"""
        export_data = export_print_format(self.test_format_name)
        export_json = json.dumps(export_data)
        
        # Import without specifying new name (should auto-rename)
        imported_name = import_print_format(export_json)
        
        # Should be renamed
        self.assertNotEqual(imported_name, self.test_format_name)
        self.assertTrue(frappe.db.exists("Print Format", imported_name))
        
        # Clean up
        frappe.delete_doc("Print Format", imported_name, force=True)
    
    def test_import_with_overwrite(self):
        """Test import with overwrite option"""
        export_data = export_print_format(self.test_format_name)
        export_json = json.dumps(export_data)
        
        # Modify original format
        self.test_format.print_designer_header = json.dumps({
            "elements": [{"type": "text", "content": "Modified Header"}]
        })
        self.test_format.save()
        
        # Import with overwrite
        imported_name = import_print_format(
            export_json, 
            overwrite=True
        )
        
        # Should overwrite the existing format
        self.assertEqual(imported_name, self.test_format_name)
        
        # Check that the original data is restored
        restored_format = frappe.get_doc("Print Format", imported_name)
        header_data = json.loads(restored_format.print_designer_header or "{}")
        self.assertEqual(
            header_data["elements"][0]["content"], 
            "Test Header"  # Original content, not "Modified Header"
        )
    
    def test_duplicate_print_format_success(self):
        """Test successful duplication of Print Designer format"""
        new_name = f"{self.test_format_name} Copy"
        duplicated_name = duplicate_print_format(self.test_format_name, new_name)
        
        self.assertEqual(duplicated_name, new_name)
        
        # Validate duplicated format
        duplicated_format = frappe.get_doc("Print Format", duplicated_name)
        original_format = frappe.get_doc("Print Format", self.test_format_name)
        
        # Should have same settings but different name
        self.assertEqual(duplicated_format.doc_type, original_format.doc_type)
        self.assertEqual(duplicated_format.print_designer, 1)
        self.assertEqual(
            duplicated_format.print_designer_body, 
            original_format.print_designer_body
        )
    
    def test_duplicate_with_existing_name(self):
        """Test duplication with existing name raises error"""
        with self.assertRaises(frappe.DuplicateEntryError):
            duplicate_print_format(self.test_format_name, self.test_format_name)
    
    def test_export_import_round_trip(self):
        """Test complete export-import cycle preserves all data"""
        # Export
        export_data = export_print_format(self.test_format_name)
        export_json = json.dumps(export_data)
        
        # Import as new format
        imported_name = import_print_format(
            export_json, 
            new_name=f"{self.test_format_name} Round Trip"
        )
        
        # Compare original and imported
        original = frappe.get_doc("Print Format", self.test_format_name)
        imported = frappe.get_doc("Print Format", imported_name)
        
        # Key fields should match
        self.assertEqual(imported.doc_type, original.doc_type)
        self.assertEqual(imported.print_designer, original.print_designer)
        self.assertEqual(imported.print_designer_body, original.print_designer_body)
        self.assertEqual(imported.print_designer_header, original.print_designer_header)
        self.assertEqual(imported.print_designer_after_table, original.print_designer_after_table)
        self.assertEqual(imported.print_designer_settings, original.print_designer_settings)
        
        # Clean up
        frappe.delete_doc("Print Format", imported_name, force=True)
    
    @patch('print_designer.api.print_format_export_import.frappe.has_permission')
    def test_permissions_export(self, mock_has_permission):
        """Test export permission checking"""
        mock_has_permission.return_value = False
        
        with self.assertRaises(frappe.PermissionError):
            export_print_format(self.test_format_name)
    
    @patch('print_designer.api.print_format_export_import.frappe.has_permission')  
    def test_permissions_import(self, mock_has_permission):
        """Test import permission checking"""
        export_data = export_print_format(self.test_format_name)
        export_json = json.dumps(export_data)
        
        mock_has_permission.return_value = False
        
        with self.assertRaises(frappe.PermissionError):
            import_print_format(export_json, new_name="Test Import")


class TestPrintFormatValidation(unittest.TestCase):
    """Test validation functions independently"""
    
    def test_validate_export_data_structure(self):
        """Test export data structure validation"""
        # Valid structure
        valid_data = {
            "version": "1.0",
            "metadata": {
                "format_name": "Test",
                "doc_type": "Sales Invoice",
                "export_date": "2024-01-01",
                "exported_by": "Administrator"
            },
            "print_format": {
                "name": "Test",
                "doc_type": "Sales Invoice",
                "print_designer": 1
            }
        }
        
        # Should not raise exception
        validate_export_data(json.dumps(valid_data))
        
        # Invalid structure - missing version
        invalid_data = valid_data.copy()
        del invalid_data["version"]
        
        with self.assertRaises(frappe.ValidationError):
            validate_export_data(json.dumps(invalid_data))