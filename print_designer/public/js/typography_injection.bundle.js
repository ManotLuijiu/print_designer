// Typography CSS Dynamic Injection for Print Designer
// Loads typography settings from Global Defaults and injects CSS

(function() {
  'use strict';
  
  function injectTypographyCSS() {
    // Remove any existing typography override
    const existingStyle = document.getElementById("global-typography-override");
    if (existingStyle) {
      existingStyle.remove();
    }

    // Check if frappe is available
    if (typeof frappe === 'undefined' || !frappe.call) {
      console.log("Frappe not ready yet, retrying in 500ms...");
      setTimeout(injectTypographyCSS, 500);
      return;
    }

    // Fetch and inject dynamic typography CSS
    frappe.call({
      method: "print_designer.api.global_typography.get_typography_css",
      type: "POST",
      callback: function (r) {
        if (r.message) {
          const style = document.createElement("style");
          style.id = "global-typography-override";
          style.type = "text/css";
          style.innerText = r.message;
          document.head.appendChild(style);
          
          // Debug log
          console.log("Typography CSS injected:", style.innerText.substring(0, 100) + "...");
          
          // Extract font stack for immediate CSS variable update
          const fontStackMatch = r.message.match(/--font-stack:\s*([^;]+);/);
          if (fontStackMatch) {
            const fontStack = fontStackMatch[1].trim();
            document.documentElement.style.setProperty('--font-stack', fontStack, 'important');
            console.log("Font stack applied:", fontStack);
          }
        } else {
          console.warn("No typography CSS returned from server");
        }
      },
      error: function(err) {
        console.error("Failed to load typography CSS:", err);
      }
    });
  }
  
  // Start injection when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectTypographyCSS);
  } else {
    injectTypographyCSS();
  }
  
  // Listen for typography updates (for real-time changes)
  document.addEventListener('DOMContentLoaded', function() {
    if (typeof $ !== 'undefined') {
      $(document).on('typography-updated', function() {
        // Reload typography CSS when settings change
        injectTypographyCSS();
      });
    }
  });
  
})();