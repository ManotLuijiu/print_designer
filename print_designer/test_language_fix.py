import frappe
from print_designer.pdf import before_print, get_effective_language, is_thai_language


def test_language_dependent_conversion():
    """
    Test that Thai amount conversion only happens when language is Thai.
    """
    print("=== Testing Language-Dependent Thai Conversion ===")
    
    try:
        # Create a mock document
        class MockDoc:
            def __init__(self):
                self.doctype = "Sales Invoice"
                self.name = "TEST-001"
                self.grand_total = 500.0
                self.in_words = "THB Five Hundred only."
                self.company = "Moo Coding"
        
        mock_doc = MockDoc()
        
        # Test 1: English language should NOT convert to Thai
        print("\n--- Test 1: English Language (_lang=en) ---")
        frappe.form_dict["_lang"] = "en"
        frappe.form_dict["format"] = "Sales Invoice - MooCoding"
        
        kwargs = {"args": {}}
        result = before_print(doc=mock_doc, method="before_print", **kwargs)
        
        effective_lang = get_effective_language("Sales Invoice - MooCoding")
        is_thai = is_thai_language(effective_lang)
        
        print(f"Effective language: {effective_lang}")
        print(f"Is Thai language: {is_thai}")
        print(f"Final in_words: {mock_doc.in_words}")
        print(f"use_thai_language: {result['args'].get('use_thai_language', 'Not set')}")
        
        if mock_doc.in_words == "THB Five Hundred only.":
            print("✅ PASS: English language preserved original in_words")
        else:
            print(f"❌ FAIL: English language converted to Thai: {mock_doc.in_words}")
        
        # Reset for next test
        mock_doc.in_words = "THB Five Hundred only."
        
        # Test 2: Thai language should convert to Thai
        print("\n--- Test 2: Thai Language (_lang=ไทย) ---")
        frappe.form_dict["_lang"] = "ไทย"
        
        kwargs = {"args": {}}
        result = before_print(doc=mock_doc, method="before_print", **kwargs)
        
        effective_lang = get_effective_language("Sales Invoice - MooCoding")
        is_thai = is_thai_language(effective_lang)
        
        print(f"Effective language: {effective_lang}")
        print(f"Is Thai language: {is_thai}")
        print(f"Final in_words: {mock_doc.in_words}")
        print(f"use_thai_language: {result['args'].get('use_thai_language', 'Not set')}")
        
        if "ห้าร้อยบาทถ้วน" in mock_doc.in_words:
            print("✅ PASS: Thai language converted to Thai")
        else:
            print(f"❌ FAIL: Thai language did not convert: {mock_doc.in_words}")
        
        # Test 3: No language parameter (should use fallback)
        print("\n--- Test 3: No Language Parameter ---")
        frappe.form_dict.pop("_lang", None)
        mock_doc.in_words = "THB Five Hundred only."
        
        kwargs = {"args": {}}
        result = before_print(doc=mock_doc, method="before_print", **kwargs)
        
        effective_lang = get_effective_language("Sales Invoice - MooCoding")
        is_thai = is_thai_language(effective_lang)
        
        print(f"Effective language: {effective_lang}")
        print(f"Is Thai language: {is_thai}")
        print(f"Final in_words: {mock_doc.in_words}")
        print(f"use_thai_language: {result['args'].get('use_thai_language', 'Not set')}")
        
    except Exception as e:
        print(f"❌ Error in language test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        frappe.form_dict.pop("_lang", None)
        frappe.form_dict.pop("format", None)
    
    print("\n=== Language Test Complete ===")


def test_language_priority():
    """
    Test the language priority system.
    """
    print("\n=== Testing Language Priority ===")
    
    # Test various language indicators
    test_cases = [
        ("ไทย", True, "Thai script"),
        ("thai", True, "English 'thai'"),
        ("th", True, "ISO code 'th'"),
        ("TH", True, "Uppercase 'TH'"),
        ("en", False, "English"),
        ("english", False, "English word"),
        ("fr", False, "French"),
        ("", False, "Empty string"),
        (None, False, "None value"),
    ]
    
    for lang, expected, description in test_cases:
        result = is_thai_language(lang)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: {description} ('{lang}') -> {result} (expected: {expected})")


if __name__ == "__main__":
    test_language_dependent_conversion()
    test_language_priority()
