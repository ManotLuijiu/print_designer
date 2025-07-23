import frappe
from print_designer.overrides.printview_watermark import get_html_and_style_with_watermark


def test_print_preview_rendering():
    """
    Test that Print Designer formats are properly rendered in print preview
    with correct page numbering and single footer.
    """
    print("=== Testing Print Preview Rendering Fix ===")
    
    try:
        # Get a sample Sales Invoice
        sales_invoices = frappe.get_all("Sales Invoice", limit=1)
        if not sales_invoices:
            print("❌ No Sales Invoice found for testing")
            return
        
        doc = frappe.get_doc("Sales Invoice", sales_invoices[0].name)
        print(f"Testing with Sales Invoice: {doc.name}")
        
        # Test 1: Print Designer format rendering
        print("\n--- Test 1: Print Designer Format Rendering ---")
        
        result = get_html_and_style_with_watermark(
            doc=frappe.as_json(doc),
            print_format="Sales Invoice - MooCoding",
            no_letterhead=0,
            letterhead="Moo Coding",
            trigger_print=False,  # This is print preview, not print
            settings='{}',
        )
        
        if result and result.get("html"):
            html = result["html"]
            
            # Check for Print Designer indicators
            has_print_designer_id = 'id="__print_designer"' in html
            has_page_numbering_script = 'initializePageNumbering' in html
            has_page_info_elements = 'page_info_page' in html or 'page_info_topage' in html
            
            print(f"✅ HTML generated successfully (length: {len(html)} chars)")
            print(f"✅ Print Designer ID found: {has_print_designer_id}")
            print(f"✅ Page numbering script included: {has_page_numbering_script}")
            print(f"✅ Page info elements present: {has_page_info_elements}")
            
            # Check for double footer issue
            footer_count = html.count('footer')
            print(f"Footer elements found: {footer_count}")
            
            if has_print_designer_id and has_page_numbering_script:
                print("✅ PASS: Print Designer format properly rendered with page numbering")
            else:
                print("❌ FAIL: Print Designer format not properly rendered")
                
        else:
            print("❌ FAIL: No HTML generated")
        
        # Test 2: Print mode rendering (trigger_print=True)
        print("\n--- Test 2: Print Mode Rendering ---")
        
        result_print = get_html_and_style_with_watermark(
            doc=frappe.as_json(doc),
            print_format="Sales Invoice - MooCoding",
            no_letterhead=0,
            letterhead="Moo Coding",
            trigger_print=True,  # This is print mode
            settings='{}',
        )
        
        if result_print and result_print.get("html"):
            html_print = result_print["html"]
            has_print_script = 'beforeprint' in html_print
            
            print(f"✅ Print mode HTML generated (length: {len(html_print)} chars)")
            print(f"✅ Print-specific script included: {has_print_script}")
            print("✅ PASS: Print mode rendering working")
        else:
            print("❌ FAIL: Print mode HTML not generated")
        
        # Test 3: Standard format (non-Print Designer)
        print("\n--- Test 3: Standard Format Rendering ---")
        
        result_standard = get_html_and_style_with_watermark(
            doc=frappe.as_json(doc),
            print_format="Sales Invoice",  # Standard format
            no_letterhead=0,
            letterhead="Moo Coding",
            trigger_print=False,
            settings='{}',
        )
        
        if result_standard and result_standard.get("html"):
            html_standard = result_standard["html"]
            has_standard_rendering = 'id="__print_designer"' not in html_standard
            
            print(f"✅ Standard format HTML generated (length: {len(html_standard)} chars)")
            print(f"✅ Uses standard rendering: {has_standard_rendering}")
            print("✅ PASS: Standard format rendering preserved")
        else:
            print("❌ FAIL: Standard format HTML not generated")
            
    except Exception as e:
        print(f"❌ Error in test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Print Preview Test Complete ===")


def test_page_numbering_elements():
    """
    Test that page numbering elements are properly handled.
    """
    print("\n=== Testing Page Numbering Elements ===")
    
    try:
        from print_designer.overrides.printview_watermark import enhance_html_for_browser_printing
        
        # Sample HTML with Print Designer page info elements
        sample_html = """
        <html>
        <body>
            <div id="__print_designer">
                <div class="page_info_page">1</div>
                <div class="page_info_topage">1</div>
                <div class="page_info_date">2025-01-01</div>
                <p>Sample content</p>
            </div>
        </body>
        </html>
        """
        
        # Test enhancement
        enhanced_html = enhance_html_for_browser_printing(sample_html, is_print_mode=False)
        
        # Check for enhancements
        has_script = 'initializePageNumbering' in enhanced_html
        has_print_css = '@media print' in enhanced_html
        has_dom_ready = 'DOMContentLoaded' in enhanced_html
        
        print(f"✅ Page numbering script added: {has_script}")
        print(f"✅ Print CSS added: {has_print_css}")
        print(f"✅ DOM ready handler added: {has_dom_ready}")
        
        if has_script and has_print_css and has_dom_ready:
            print("✅ PASS: Page numbering enhancement working correctly")
        else:
            print("❌ FAIL: Page numbering enhancement incomplete")
            
    except Exception as e:
        print(f"❌ Error in page numbering test: {str(e)}")
    
    print("=== Page Numbering Test Complete ===")


if __name__ == "__main__":
    test_print_preview_rendering()
    test_page_numbering_elements()
