(() => {
  // ../print_designer/print_designer/public/js/typography_injection.bundle.js
  (function() {
    "use strict";
    function injectTypographyCSS() {
      const existingStyle = document.getElementById("global-typography-override");
      if (existingStyle) {
        existingStyle.remove();
      }
      if (typeof frappe === "undefined" || !frappe.call) {
        console.log("Frappe not ready yet, retrying in 500ms...");
        setTimeout(injectTypographyCSS, 500);
        return;
      }
      frappe.call({
        method: "print_designer.api.global_typography.get_typography_css",
        type: "POST",
        callback: function(r) {
          if (r.message) {
            const style = document.createElement("style");
            style.id = "global-typography-override";
            style.type = "text/css";
            style.innerText = r.message;
            document.head.appendChild(style);
            console.log("Typography CSS injected:", style.innerText.substring(0, 100) + "...");
            const fontStackMatch = r.message.match(/--font-stack:\s*([^;]+);/);
            if (fontStackMatch) {
              const fontStack = fontStackMatch[1].trim();
              document.documentElement.style.setProperty("--font-stack", fontStack, "important");
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
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", injectTypographyCSS);
    } else {
      injectTypographyCSS();
    }
    document.addEventListener("DOMContentLoaded", function() {
      if (typeof $ !== "undefined") {
        $(document).on("typography-updated", function() {
          injectTypographyCSS();
        });
      }
    });
  })();
})();
//# sourceMappingURL=typography_injection.bundle.J2NT7KPO.js.map
