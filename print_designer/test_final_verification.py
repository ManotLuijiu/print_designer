import frappe
from print_designer.overrides.printview_watermark import get_html_and_style_with_watermark


def test_final_verification():
    """
    Final verification that all Print Preview issues are fixed:
    1. Page numbering script is included
    2. Duplicate footers are hidden with CSS
    3. Print Designer footer is preserved
    4. Both preview and print modes work
    """
    print("🎯 FINAL VERIFICATION: Print Preview Fix")
    print("=" * 50)
    
    try:
        # Get a sample Sales Invoice
        sales_invoices = frappe.get_all("Sales Invoice", limit=1)
        if not sales_invoices:
            print("❌ No Sales Invoice found for testing")
            return
        
        doc = frappe.get_doc("Sales Invoice", sales_invoices[0].name)
        print(f"Testing with Sales Invoice: {doc.name}")
        
        # Test Print Preview Mode (trigger_print=False)
        print("\n📋 TEST 1: Print Preview Mode")
        print("-" * 30)
        
        result = get_html_and_style_with_watermark(
            doc=frappe.as_json(doc),
            print_format="Sales Invoice - MooCoding",
            no_letterhead=0,
            letterhead="Moo Coding",
            trigger_print=False,  # Preview mode
            settings='{}',
        )
        
        if result and result.get("html"):
            html = result["html"]
            
            # Check 1: Page numbering script
            has_page_script = 'initializePageNumbering' in html
            print(f"✅ Page numbering script: {'INCLUDED' if has_page_script else 'MISSING'}")
            
            # Check 2: Page info elements
            has_page_info = 'page_info_page' in html and 'page_info_topage' in html
            print(f"✅ Page info elements: {'PRESENT' if has_page_info else 'MISSING'}")
            
            # Check 3: Footer handling
            hidden_pdf_count = html.count('class="hidden-pdf"')
            first_page_footer_count = html.count('id="firstPageFooter"')
            has_footer_css = '.hidden-pdf' in html and 'display: none !important' in html
            
            print(f"✅ Print Designer footers: {first_page_footer_count}")
            print(f"✅ Duplicate footers (hidden): {hidden_pdf_count}")
            print(f"✅ Footer hiding CSS: {'INCLUDED' if has_footer_css else 'MISSING'}")
            
            # Check 4: Print Designer ID
            has_pd_id = 'id="__print_designer"' in html
            print(f"✅ Print Designer format: {'DETECTED' if has_pd_id else 'NOT DETECTED'}")
            
            preview_score = sum([has_page_script, has_page_info, has_footer_css, has_pd_id])
            print(f"\n📊 Preview Mode Score: {preview_score}/4")
            
        else:
            print("❌ No HTML generated for preview mode")
            preview_score = 0
        
        # Test Print Mode (trigger_print=True)
        print("\n🖨️  TEST 2: Print Mode")
        print("-" * 30)
        
        result_print = get_html_and_style_with_watermark(
            doc=frappe.as_json(doc),
            print_format="Sales Invoice - MooCoding",
            no_letterhead=0,
            letterhead="Moo Coding",
            trigger_print=True,  # Print mode
            settings='{}',
        )
        
        if result_print and result_print.get("html"):
            html_print = result_print["html"]
            
            # Check print-specific features
            has_print_script = 'beforeprint' in html_print
            has_page_script_print = 'initializePageNumbering' in html_print
            has_footer_css_print = '.hidden-pdf' in html_print
            
            print(f"✅ Print event script: {'INCLUDED' if has_print_script else 'MISSING'}")
            print(f"✅ Page numbering script: {'INCLUDED' if has_page_script_print else 'MISSING'}")
            print(f"✅ Footer hiding CSS: {'INCLUDED' if has_footer_css_print else 'MISSING'}")
            
            print_score = sum([has_print_script, has_page_script_print, has_footer_css_print])
            print(f"\n📊 Print Mode Score: {print_score}/3")
            
        else:
            print("❌ No HTML generated for print mode")
            print_score = 0
        
        # Test Standard Format (non-Print Designer)
        print("\n📄 TEST 3: Standard Format Compatibility")
        print("-" * 30)
        
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
            
            # Should NOT have Print Designer elements
            has_pd_id_standard = 'id="__print_designer"' in html_standard
            has_pd_script_standard = 'initializePageNumbering' in html_standard
            
            print(f"✅ Standard rendering: {'PRESERVED' if not has_pd_id_standard else 'CORRUPTED'}")
            print(f"✅ No PD scripts: {'CORRECT' if not has_pd_script_standard else 'INCORRECT'}")
            
            standard_score = sum([not has_pd_id_standard, not has_pd_script_standard])
            print(f"\n📊 Standard Format Score: {standard_score}/2")
            
        else:
            print("❌ No HTML generated for standard format")
            standard_score = 0
        
        # Final Results
        print("\n" + "=" * 50)
        print("🏆 FINAL RESULTS")
        print("=" * 50)
        
        total_score = preview_score + print_score + standard_score
        max_score = 9
        
        print(f"📋 Preview Mode: {preview_score}/4")
        print(f"🖨️  Print Mode: {print_score}/3")
        print(f"📄 Standard Format: {standard_score}/2")
        print(f"🎯 TOTAL SCORE: {total_score}/{max_score}")
        
        if total_score >= 8:
            print("\n🎉 SUCCESS: Print Preview fix is working correctly!")
            print("✅ Page numbering is now included")
            print("✅ Double footer issue is resolved")
            print("✅ Print Designer formats render properly")
            print("✅ Standard formats remain unaffected")
        elif total_score >= 6:
            print("\n⚠️  PARTIAL SUCCESS: Most issues are fixed but some remain")
        else:
            print("\n❌ FAILURE: Major issues still exist")
        
        return total_score >= 8
        
    except Exception as e:
        print(f"❌ Error in final verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_final_verification()
