(() => {
  // ../print_designer/print_designer/public/js/dynamic_typography.bundle.js
  (function() {
    "use strict";
    let dynamicTypographyStyle = null;
    function initDynamicTypography() {
      if (!dynamicTypographyStyle) {
        dynamicTypographyStyle = document.createElement("style");
        dynamicTypographyStyle.id = "dynamic-typography-override";
        dynamicTypographyStyle.type = "text/css";
        document.head.appendChild(dynamicTypographyStyle);
      }
      loadTypographyCSS();
    }
    function loadTypographyCSS() {
      frappe.call({
        method: "print_designer.api.global_typography.get_typography_css",
        callback: function(response) {
          if (response.message && dynamicTypographyStyle) {
            dynamicTypographyStyle.textContent = response.message;
            const fontStackMatch = response.message.match(/--font-stack:\s*([^;]+);/);
            if (fontStackMatch) {
              const fontStack = fontStackMatch[1].trim();
              document.documentElement.style.setProperty("--font-stack", fontStack, "important");
            }
          }
        },
        error: function(error) {
          console.warn("Failed to load dynamic typography CSS:", error);
        }
      });
    }
    function refreshTypography() {
      loadTypographyCSS();
    }
    window.refreshTypography = refreshTypography;
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initDynamicTypography);
    } else {
      initDynamicTypography();
    }
    $(document).on("typography-updated", function() {
      refreshTypography();
    });
    setInterval(function() {
      loadTypographyCSS();
    }, 3e4);
  })();
})();
//# sourceMappingURL=dynamic_typography.bundle.4S2PCYGB.js.map
