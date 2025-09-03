"""
Test utilities for Print Designer following ERPNext pattern
Based on apps/erpnext/erpnext/tests/utils.py
"""

import json
import frappe
from frappe.tests.utils import FrappeTestCase


def create_test_print_format(name=None, doctype="Sales Invoice", designer_settings=None):
    """
    Create a test Print Designer format for testing purposes
    
    Args:
        name: Name of the print format
        doctype: DocType for the print format
        designer_settings: Custom designer settings
    
    Returns:
        Print Format doc
    """
    if not name:
        name = f"Test Print Format - {frappe.utils.random_string(5)}"
    
    # Default designer settings
    if not designer_settings:
        designer_settings = {
            "page_size": "A4",
            "orientation": "portrait", 
            "margins": {"top": 10, "bottom": 10, "left": 15, "right": 15}
        }
    
    # Check if format already exists
    if frappe.db.exists("Print Format", name):
        return frappe.get_doc("Print Format", name)
    
    print_format = frappe.get_doc({
        "doctype": "Print Format",
        "name": name,
        "doc_type": doctype,
        "print_designer": 1,
        "print_designer_header": json.dumps({
            "elements": [
                {"type": "text", "content": "Test Company Header", "style": {"fontSize": "18px", "fontWeight": "bold"}}
            ]
        }),
        "print_designer_body": json.dumps({
            "elements": [
                {"type": "field", "fieldname": "name", "label": f"{doctype} No"},
                {"type": "field", "fieldname": "customer", "label": "Customer"} if doctype in ["Sales Invoice", "Sales Order"] else {"type": "text", "content": "Test Body"},
                {"type": "table", "fieldname": "items", "columns": [
                    {"fieldname": "item_code", "label": "Item Code"},
                    {"fieldname": "qty", "label": "Qty"},
                    {"fieldname": "rate", "label": "Rate"},
                    {"fieldname": "amount", "label": "Amount"}
                ]} if hasattr(frappe.get_meta(doctype), "get_field") and frappe.get_meta(doctype).get_field("items") else {"type": "text", "content": "No items table"}
            ]
        }),
        "print_designer_after_table": json.dumps({
            "elements": [
                {"type": "field", "fieldname": "grand_total", "label": "Grand Total"} if doctype in ["Sales Invoice", "Purchase Invoice"] else {"type": "text", "content": "Test Footer"}
            ]
        }),
        "print_designer_settings": json.dumps(designer_settings)
    })
    
    print_format.insert(ignore_permissions=True)
    frappe.db.commit()
    return print_format


def create_test_digital_signature(name=None, company=None):
    """
    Create a test Digital Signature for testing
    
    Args:
        name: Name of the signature
        company: Company name
        
    Returns:
        Digital Signature doc
    """
    if not name:
        name = f"Test Signature - {frappe.utils.random_string(5)}"
    
    if not company:
        company = frappe.defaults.get_user_default("Company") or "Test Company"
    
    if frappe.db.exists("Digital Signature", name):
        return frappe.get_doc("Digital Signature", name)
    
    signature = frappe.get_doc({
        "doctype": "Digital Signature",
        "name": name,
        "company": company,
        "signature_type": "Company Seal",
        "position": "Bottom Right",
        "width": 100,
        "height": 50
    })
    
    signature.insert(ignore_permissions=True)
    frappe.db.commit()
    return signature


def create_test_company_stamp(name=None, company=None):
    """
    Create a test Company Stamp for testing
    
    Args:
        name: Name of the stamp
        company: Company name
        
    Returns:
        Company Stamp doc
    """
    if not name:
        name = f"Test Stamp - {frappe.utils.random_string(5)}"
    
    if not company:
        company = frappe.defaults.get_user_default("Company") or "Test Company"
    
    if frappe.db.exists("Company Stamp", name):
        return frappe.get_doc("Company Stamp", name)
    
    stamp = frappe.get_doc({
        "doctype": "Company Stamp", 
        "name": name,
        "company": company,
        "stamp_type": "Official Seal",
        "position": "Bottom Center",
        "width": 80,
        "height": 80
    })
    
    stamp.insert(ignore_permissions=True)
    frappe.db.commit()
    return stamp


def cleanup_test_data(print_formats=None, signatures=None, stamps=None):
    """
    Clean up test data after tests
    
    Args:
        print_formats: List of Print Format names to delete
        signatures: List of Digital Signature names to delete
        stamps: List of Company Stamp names to delete
    """
    # Clean up Print Formats
    if print_formats:
        for format_name in print_formats:
            if frappe.db.exists("Print Format", format_name):
                frappe.delete_doc("Print Format", format_name, force=True)
    
    # Clean up Digital Signatures
    if signatures:
        for signature_name in signatures:
            if frappe.db.exists("Digital Signature", signature_name):
                frappe.delete_doc("Digital Signature", signature_name, force=True)
    
    # Clean up Company Stamps
    if stamps:
        for stamp_name in stamps:
            if frappe.db.exists("Company Stamp", stamp_name):
                frappe.delete_doc("Company Stamp", stamp_name, force=True)
    
    frappe.db.commit()


class PrintDesignerTestCase(FrappeTestCase):
    """
    Base test case class for Print Designer tests
    Provides common setup and teardown for Print Designer testing
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level test data"""
        super().setUpClass()
        cls.test_company = frappe.defaults.get_user_default("Company") or "Test Company"
        cls.test_doctypes = ["Sales Invoice", "Purchase Invoice", "Quotation", "Sales Order"]
        cls.created_test_data = {
            "print_formats": [],
            "signatures": [],
            "stamps": []
        }
    
    @classmethod
    def tearDownClass(cls):
        """Clean up class-level test data"""
        cleanup_test_data(
            print_formats=cls.created_test_data.get("print_formats", []),
            signatures=cls.created_test_data.get("signatures", []),
            stamps=cls.created_test_data.get("stamps", [])
        )
        super().tearDownClass()
    
    def create_test_print_format(self, **kwargs):
        """Create test print format and track for cleanup"""
        print_format = create_test_print_format(**kwargs)
        self.created_test_data["print_formats"].append(print_format.name)
        return print_format
    
    def create_test_signature(self, **kwargs):
        """Create test signature and track for cleanup"""
        signature = create_test_digital_signature(**kwargs)
        self.created_test_data["signatures"].append(signature.name)
        return signature
    
    def create_test_stamp(self, **kwargs):
        """Create test stamp and track for cleanup"""
        stamp = create_test_company_stamp(**kwargs)
        self.created_test_data["stamps"].append(stamp.name)
        return stamp


def get_test_print_format_json():
    """
    Get a sample Print Designer format JSON for testing import functionality
    
    Returns:
        dict: Sample export data structure
    """
    return {
        "version": "1.0",
        "metadata": {
            "format_name": "Test Import Format",
            "doc_type": "Sales Invoice",
            "export_date": "2024-01-01T00:00:00.000Z",
            "exported_by": "Administrator",
            "app_version": "1.0.0"
        },
        "print_format": {
            "name": "Test Import Format",
            "doc_type": "Sales Invoice",
            "print_designer": 1,
            "print_designer_header": json.dumps({
                "elements": [{"type": "text", "content": "Imported Header"}]
            }),
            "print_designer_body": json.dumps({
                "elements": [
                    {"type": "field", "fieldname": "name", "label": "Invoice No"},
                    {"type": "field", "fieldname": "customer", "label": "Customer"}
                ]
            }),
            "print_designer_after_table": json.dumps({
                "elements": [{"type": "text", "content": "Imported Footer"}]
            }),
            "print_designer_settings": json.dumps({
                "page_size": "A4",
                "orientation": "portrait",
                "margins": {"top": 15, "bottom": 15, "left": 20, "right": 20}
            })
        }
    }


def validate_print_format_structure(print_format_doc, expected_doctype=None):
    """
    Validate that a print format has the expected Print Designer structure
    
    Args:
        print_format_doc: Print Format document to validate
        expected_doctype: Expected doc_type if specified
        
    Returns:
        bool: True if valid structure
    """
    if not print_format_doc:
        return False
    
    # Check basic Print Designer fields
    required_fields = [
        "print_designer",
        "print_designer_body"
    ]
    
    for field in required_fields:
        if not hasattr(print_format_doc, field):
            return False
        if field == "print_designer" and not print_format_doc.print_designer:
            return False
    
    # Check doc_type if specified
    if expected_doctype and print_format_doc.doc_type != expected_doctype:
        return False
    
    # Validate JSON structure
    try:
        if print_format_doc.print_designer_body:
            json.loads(print_format_doc.print_designer_body)
        if print_format_doc.print_designer_header:
            json.loads(print_format_doc.print_designer_header)
        if print_format_doc.print_designer_after_table:
            json.loads(print_format_doc.print_designer_after_table)
        if print_format_doc.print_designer_settings:
            json.loads(print_format_doc.print_designer_settings)
    except (json.JSONDecodeError, TypeError):
        return False
    
    return True