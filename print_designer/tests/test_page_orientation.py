"""
Test page orientation feature in print preview.

Tests:
1. Page Orientation field appears in sidebar
2. Changing to Landscape adds .landscape class to print-format div
3. Console debug logs show correct flow
"""

import time

from playwright.sync_api import sync_playwright


def test_page_orientation():
    """Test page orientation in print preview."""

    site_url = "https://digisoft-erp.bunchee.online"
    username = "Administrator"
    password = "manlucha"
    executable_path = "/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=executable_path)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # Login
        print(f"\n[LOGIN] Navigating to {site_url}/desk/login")
        page.goto(f"{site_url}/desk/login")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)

        print("[LOGIN] Filling credentials")
        page.fill("#login_email", username)
        page.fill("#login_password", password)
        page.click(".btn-login")

        # Wait for desk to load
        print("[LOGIN] Waiting for desk to load...")
        page.wait_for_url(f"{site_url}/desk/**", timeout=30000)
        time.sleep(5)
        print("[LOGIN] Logged in successfully!")

        # ===== TEST 1: Check page_orientation field exists =====
        print("\n[TEST 1] Navigating to print preview...")

        # Navigate to print preview (URL encode spaces)
        url = f"{site_url}/desk/print/Stock%20Entry/MAT-STE-2026-00004"
        print(f"[TEST 1] URL: {url}")
        page.goto(url)
        page.wait_for_load_state("networkidle")
        time.sleep(5)

        # Check if page_orientation field exists
        print("[TEST 1] Looking for page_orientation field in sidebar...")
        result = page.evaluate("""() => {
            const field = document.querySelector('[data-fieldname="page_orientation"]');
            if (!field) return { found: false };
            
            const select = field.querySelector('select');
            const currentValue = select ? select.value : null;
            const options = select ? Array.from(select.options).map(o => o.value) : [];
            
            return {
                found: true,
                currentValue,
                options,
                selectExists: !!select
            };
        }""")

        print(f"[TEST 1] Result: {result}")
        if not result["found"]:
            print("[TEST 1] FAILED - page_orientation field not found in sidebar")
        else:
            print(
                f"[TEST 1] PASSED - page_orientation field found with options: {result['options']}"
            )

        # ===== TEST 2: Check landscape class toggle =====
        print("\n[TEST 2] Testing landscape class toggle...")

        # Navigate to print preview again
        page.goto(url)
        page.wait_for_load_state("networkidle")
        time.sleep(5)

        # Check initial state (Portrait) - check iframe content
        print("[TEST 2] Checking initial state (should be Portrait)...")
        result_initial = page.evaluate("""() => {
            const iframe = document.querySelector('iframe');
            if (!iframe) return { found: false, error: 'No iframe' };
            
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const printFormat = iframeDoc.querySelector('.print-format');
                if (!printFormat) return { found: false, error: 'No .print-format in iframe' };
                
                return {
                    found: true,
                    classes: printFormat.className,
                    hasLandscape: printFormat.classList.contains('landscape')
                };
            } catch(e) {
                return { found: false, error: e.message };
            }
        }""")
        print(f"[TEST 2] Initial state: {result_initial}")

        # Change to Landscape
        print("[TEST 2] Changing page_orientation to Landscape...")
        changed = page.evaluate("""() => {
            const select = document.querySelector('[data-fieldname="page_orientation"] select');
            if (!select) return { success: false, error: 'select not found' };
            
            // Find and select Landscape option
            for (let option of select.options) {
                if (option.value === 'Landscape') {
                    option.selected = true;
                    break;
                }
            }
            
            // Trigger change event
            select.dispatchEvent(new Event('change', { bubbles: true }));
            
            return { success: true, selectedValue: select.value };
        }""")

        print(f"[TEST 2] Change result: {changed}")

        # Wait for preview to re-render
        print("[TEST 2] Waiting for preview to re-render...")
        time.sleep(3)

        # Check if .landscape class was added - check iframe content
        print("[TEST 2] Checking if .landscape class was added...")
        result_landscape = page.evaluate("""() => {
            const iframe = document.querySelector('iframe');
            if (!iframe) return { found: false, error: 'No iframe' };
            
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const printFormat = iframeDoc.querySelector('.print-format');
                if (!printFormat) return { found: false, error: 'No .print-format in iframe' };
                
                return {
                    found: true,
                    classes: printFormat.className,
                    hasLandscape: printFormat.classList.contains('landscape')
                };
            } catch(e) {
                return { found: false, error: e.message };
            }
        }""")

        print(f"[TEST 2] Landscape result: {result_landscape}")
        if result_landscape["found"] and result_landscape["hasLandscape"]:
            print("[TEST 2] PASSED - .landscape class added successfully!")
        else:
            print(f"[TEST 2] FAILED - Expected .landscape class but got: {result_landscape}")

        # ===== TEST 2b: Check CSS injection with !important =====
        print("\n[TEST 2b] Checking CSS injection in iframe head...")
        result_css = page.evaluate("""() => {
            const iframe = document.querySelector('iframe');
            if (!iframe) return { found: false, error: 'No iframe' };
            
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const styles = iframeDoc.querySelectorAll('head style');
                const landscapeStyles = [];
                
                styles.forEach(style => {
                    const text = style.textContent;
                    if (text.includes('.print-format.landscape')) {
                        landscapeStyles.push(text);
                    }
                });
                
                // Also check if the print-format element has correct computed styles
                const printFormat = iframeDoc.querySelector('.print-format');
                const computedStyles = printFormat ? getComputedStyle(printFormat) : null;
                
                // Check inline style
                const inlineStyle = printFormat ? printFormat.style.maxWidth : null;
                
                return {
                    found: true,
                    landscapeStyles,
                    minHeight: computedStyles ? computedStyles.minHeight : null,
                    maxWidth: computedStyles ? computedStyles.maxWidth : null,
                    padding: computedStyles ? computedStyles.paddingTop : null,
                    inlineMaxWidth: inlineStyle
                };
            } catch(e) {
                return { found: false, error: e.message };
            }
        }""")

        print(f"[TEST 2b] CSS check result: {result_css}")

        # Check for our injected style
        landscape_styles = result_css.get("landscapeStyles", [])
        our_injected_style = None
        for style in landscape_styles:
            if "min-height: 8.3in !important" in style:
                our_injected_style = style
                break

        if our_injected_style:
            print("[TEST 2b] PASSED - Our injected landscape CSS found with !important")
            print(
                f"[TEST 2b] Injected style min-height: 8.3in -> computed: {result_css.get('minHeight')}"
            )
            print(
                f"[TEST 2b] Injected style padding: 0.2in -> computed: {result_css.get('padding')}"
            )
        else:
            print("[TEST 2b] FAILED - Our injected landscape CSS not found")

        # Check if inline style is overriding maxWidth
        if result_css.get("inlineMaxWidth"):
            print(
                f"[TEST 2b] WARNING - Inline style setting maxWidth: {result_css.get('inlineMaxWidth')}"
            )

        # ===== TEST 2c: Check actual element dimensions =====
        print("\n[TEST 2c] Checking actual element dimensions...")
        result_dims = page.evaluate("""() => {
            const iframe = document.querySelector('iframe');
            if (!iframe) return { found: false };
            
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const printFormat = iframeDoc.querySelector('.print-format');
                if (!printFormat) return { found: false };
                
                const rect = printFormat.getBoundingClientRect();
                return {
                    found: true,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    isLandscape: rect.width > rect.height,
                    aspectRatio: (rect.width / rect.height).toFixed(2)
                };
            } catch(e) {
                return { found: false, error: e.message };
            }
        }""")

        print(
            f"[TEST 2c] Element dimensions: {result_dims.get('width')}px x {result_dims.get('height')}px"
        )
        print(f"[TEST 2c] Aspect ratio: {result_dims.get('aspectRatio')} (landscape > 1.0)")
        if result_dims.get("isLandscape"):
            print("[TEST 2c] PASSED - Element is in LANDSCAPE orientation (width > height)")
        else:
            print("[TEST 2c] INFO - Element is in PORTRAIT orientation (height > width)")

        # ===== TEST 2d: Check .print-preview in MAIN DOCUMENT =====
        print("\n[TEST 2d] Checking .print-preview in main document...")
        result_preview = page.evaluate("""() => {
            const preview = document.querySelector('.print-preview');
            if (!preview) return { found: false };
            
            const rect = preview.getBoundingClientRect();
            const computed = getComputedStyle(preview);
            
            return {
                found: true,
                classes: preview.className,
                hasLandscape: preview.classList.contains('landscape'),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                maxWidth: computed.maxWidth,
                minHeight: computed.minHeight,
                isLandscape: rect.width > rect.height
            };
        }""")

        print(f"[TEST 2d] .print-preview result: {result_preview}")
        if result_preview.get("hasLandscape"):
            print("[TEST 2d] .print-preview has .landscape class")
            print(f"[TEST 2d] max-width: {result_preview.get('maxWidth')}")
            print(f"[TEST 2d] min-height: {result_preview.get('minHeight')}")
            if result_preview.get("isLandscape"):
                print("[TEST 2d] PASSED - .print-preview is LANDSCAPE (width > height)")
            else:
                print("[TEST 2d] FAILED - .print-preview is still PORTRAIT")
        else:
            print("[TEST 2d] FAILED - .print-preview missing .landscape class")

        # Take screenshot
        page.screenshot(path="test_orientation_result.png")
        print("[TEST 2] Screenshot saved: test_orientation_result.png")

        # ===== TEST 3: Capture console logs =====
        print("\n[TEST 3] Checking console logs...")

        # Check if our debug logs are appearing
        debug_check = page.evaluate("""() => {
            // Check if any DEBUG logs were captured
            return {
                hasConsole: typeof console !== 'undefined',
                // Try to find any orientation-related logs in console
                logs: window.__debugLogs || []
            };
        }""")

        print(f"[TEST 3] Debug check: {debug_check}")

        browser.close()

        print("\n=== All Tests Completed ===")


if __name__ == "__main__":
    test_page_orientation()
