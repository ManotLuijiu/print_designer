import frappe

from print_designer.pdf import before_print, debug_current_language_context


def test_before_print_hook():
    """
    Test the before_print hook to ensure it's working correctly.
    Run this from bench console:

    from print_designer.test_before_print import test_before_print_hook
    test_before_print_hook()
    """

    print("=== Testing before_print Hook ===")

    try:
        # Simulate URL parameters
        frappe.form_dict["_lang"] = "ไทย"
        frappe.form_dict["format"] = "Sales Invoice"

        # Get a sample print format
        print_format = frappe.get_doc("Print Format", "Sales Invoice")

        # Create a mock document
        class MockDoc:
            def __init__(self):
                self.doctype = "Sales Invoice"
                self.name = "TEST-001"
                self.grand_total = 1000.50
                self.in_words = "One Thousand and Fifty Cents only"

        mock_doc = MockDoc()

        # Test the before_print hook
        kwargs = {"args": {}, "print_format": print_format}
        result = before_print(doc=mock_doc, method="before_print", **kwargs)

        print(f"✅ before_print hook executed successfully")
        print(f"Args keys: {list(result['args'].keys())}")

        # Check if Thai enhancement was applied
        if "thai_in_words" in result["args"]:
            print(f"✅ Thai enhancement applied: {result['args']['thai_in_words']}")

        if "effective_lang" in result["args"]:
            print(f"✅ Effective language set: {result['args']['effective_lang']}")

        if "is_thai" in result["args"]:
            print(f"✅ Thai language detected: {result['args']['is_thai']}")

        # Debug language context
        debug_current_language_context()

    except Exception as e:
        print(f"❌ Error testing before_print hook: {str(e)}")
        frappe.log_error(f"Error in test_before_print_hook: {str(e)}")

    finally:
        # Clean up
        frappe.form_dict.pop("_lang", None)
        frappe.form_dict.pop("format", None)

    print("=== Test Complete ===")


def test_language_priority():
    """
    Test the language priority system.
    """
    print("=== Testing Language Priority ===")

    from print_designer.pdf import get_effective_language, is_thai_language

    # Test 1: URL parameter priority
    frappe.form_dict["_lang"] = "ไทย"
    lang = get_effective_language()
    print(f"Test 1 - URL lang 'ไทย': {lang} (is_thai: {is_thai_language(lang)})")

    # Test 2: Without URL parameter
    frappe.form_dict.pop("_lang", None)
    lang = get_effective_language()
    print(f"Test 2 - No URL lang: {lang} (is_thai: {is_thai_language(lang)})")

    # Test 3: Various Thai indicators
    thai_variants = ["ไทย", "thai", "th", "TH", "Thai", "THAI", "th-th"]
    for variant in thai_variants:
        is_thai = is_thai_language(variant)
        print(f"'{variant}' -> is_thai: {is_thai}")

    print("=== Language Priority Test Complete ===")


if __name__ == "__main__":
    test_before_print_hook()
    test_language_priority()
