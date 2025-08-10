import frappe
from print_designer.pdf import before_print


def test_function_signature():
    """
    Test the before_print function signature to ensure it matches Frappe's expectations.
    """
    print("=== Testing Function Signature ===")
    
    try:
        # Create a mock document
        class MockDoc:
            def __init__(self):
                self.doctype = "Sales Invoice"
                self.name = "TEST-001"
                self.grand_total = 1000.50
                self.in_words = "One Thousand and Fifty Cents only"
        
        mock_doc = MockDoc()
        
        # Test 1: Call with 3 arguments (as Frappe does)
        print("Test 1: Calling with 3 arguments (doc, method, print_settings)")
        result = before_print(mock_doc, "before_print", {})
        print("✅ Success: Function accepts 3 arguments")
        
        # Test 2: Call with keyword arguments
        print("Test 2: Calling with keyword arguments")
        frappe.form_dict["format"] = "Sales Invoice"
        result = before_print(doc=mock_doc, method="before_print", print_settings={})
        print("✅ Success: Function accepts keyword arguments")
        
        # Test 3: Call with additional kwargs
        print("Test 3: Calling with additional kwargs")
        result = before_print(
            doc=mock_doc, 
            method="before_print", 
            print_settings={}, 
            args={"test": "value"}
        )
        print("✅ Success: Function accepts additional kwargs")
        
        print("=== All signature tests passed! ===")
        
    except Exception as e:
        print(f"❌ Error in signature test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        frappe.form_dict.pop("format", None)


def test_with_real_document():
    """
    Test with a real Sales Invoice document if available.
    """
    print("=== Testing with Real Document ===")
    
    try:
        # Try to get a real Sales Invoice
        sales_invoices = frappe.get_all("Sales Invoice", limit=1)
        if not sales_invoices:
            print("No Sales Invoice found, skipping real document test")
            return
        
        doc = frappe.get_doc("Sales Invoice", sales_invoices[0].name)
        print(f"Testing with Sales Invoice: {doc.name}")
        
        # Set up form_dict as if coming from a print request
        frappe.form_dict["format"] = "Sales Invoice"
        frappe.form_dict["_lang"] = "en"
        
        # Call the before_print function
        result = before_print(doc, "before_print", {})
        
        print("✅ Success: Real document test passed")
        print(f"Result type: {type(result)}")
        
        if isinstance(result, dict) and "args" in result:
            print(f"Args keys: {list(result['args'].keys())}")
        
    except Exception as e:
        print(f"❌ Error in real document test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        frappe.form_dict.pop("format", None)
        frappe.form_dict.pop("_lang", None)


if __name__ == "__main__":
    test_function_signature()
    test_with_real_document()
