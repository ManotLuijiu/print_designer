/**
 * Print Designer - Print Page Language Override
 *
 * Safe client-only helper:
 * - wait for the print page inputs to exist
 * - ignore placeholder "Standard"
 * - fetch Print Format.default_print_language when a real format is selected
 * - apply it through the existing Language control
 */

console.log("[DEBUG] print_designer/public/js/print.js LOADED!");

// DEBUG: Intercept API calls to get_print_settings_to_show
const originalXcall = frappe.xcall.bind(frappe);
frappe.xcall = function () {
  const args = Array.from(arguments);
  const methodName =
    typeof args[0] === "string" ? args[0] : (args[0] && args[0].method) || "";
  if (methodName.includes("get_print_settings_to_show")) {
    console.log("[DEBUG] API CALLED: get_print_settings_to_show", args);
    // Intercept the promise and log response
    if (args[0] && typeof args[0].then === "function") {
      args[0] = args[0].then(function (result) {
        console.log("[DEBUG] API RESPONSE: get_print_settings_to_show", result);
        console.log(
          "[DEBUG] Number of fields returned:",
          result ? result.length : 0,
        );
        if (result) {
          result.forEach((field, i) => {
            console.log(
              `[DEBUG] Field ${i}:`,
              field.fieldname,
              "-",
              field.label,
            );
          });
        }
        return result;
      });
    }
  }
  return originalXcall.apply(this, arguments);
};

// DEBUG: Watch for sidebar items being added
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
      mutation.addedNodes.forEach((node) => {
        if (node.classList && node.classList.contains("dynamic-settings")) {
          console.log("[DEBUG] dynamic-settings container added to DOM!");
          const fields = node.querySelectorAll("[data-fieldname]");
          console.log(
            "[DEBUG] Fields in dynamic-settings:",
            Array.from(fields).map((f) => f.dataset.fieldname),
          );
        }
      });
    }
  });
});

// DEBUG: Intercept PrintView.add_settings_to_sidebar to reorder watermark fields
function patchPrintViewForDebug() {
  const PV = frappe.ui.form && frappe.ui.form.PrintView;
  if (!PV || !PV.prototype) {
    setTimeout(patchPrintViewForDebug, 200);
    return;
  }
  if (PV.prototype._debugPatched) return;

  const original_add = PV.prototype.add_settings_to_sidebar;
  PV.prototype.add_settings_to_sidebar = function (settings) {
    // REORDER: watermark_settings -> position -> font_family -> font_size -> margins
    const desiredOrder = [
      "watermark_settings",
      "watermark_position",
      "watermark_font_family",
      "watermark_font_size",
      "watermark_margin_top",
      "watermark_margin_right",
      "watermark_margin_bottom",
      "watermark_margin_left",
    ];

    // Find watermark fields in settings and reorder them
    const watermarkFields = settings.filter((s) =>
      desiredOrder.includes(s.fieldname),
    );
    const otherFields = settings.filter(
      (s) => !desiredOrder.includes(s.fieldname),
    );

    // Sort watermark fields by desired order
    watermarkFields.sort((a, b) => {
      return (
        desiredOrder.indexOf(a.fieldname) - desiredOrder.indexOf(b.fieldname)
      );
    });

    // Combine: ERPNext fields first, then reordered watermark fields
    const reorderedSettings = [...otherFields, ...watermarkFields];

    // INJECT COLUMN BREAK between 2nd and 3rd margin field
    // This splits margins into 2 columns: Top/Right | Bottom/Left
    const marginBottomIndex = reorderedSettings.findIndex(
      (s) => s.fieldname === "watermark_margin_bottom",
    );
    if (marginBottomIndex > 0) {
      reorderedSettings.splice(marginBottomIndex, 0, {
        fieldname: "watermark_margin_col_break",
        fieldtype: "Column Break",
      });
    }

    console.log(
      "[DEBUG] add_settings_to_sidebar - reordered settings:",
      reorderedSettings.map((s) => s.fieldname),
    );

    const result = original_add.call(this, reorderedSettings);

    // WRAP SIDEBAR FIELDS IN 2-COLUMN GRIDS
    // After rendering, find divs and wrap them in CSS grids
    setTimeout(() => {
      const container = document.querySelector(".dynamic-settings");
      if (!container) return;

      // 1. WRAP WATERMARK SETTINGS (4 fields) IN 2-COLUMN GRID
      const watermarkSettingsFields = [
        "watermark_settings",
        "watermark_position",
        "watermark_font_family",
        "watermark_font_size",
      ];
      const watermarkWrapper = document.createElement("div");
      watermarkWrapper.className = "watermark-settings-grid";
      watermarkWrapper.style.cssText =
        "display: grid; grid-template-columns: 1fr 1fr; column-gap: 10px; margin-top: 10px;";
      watermarkSettingsFields.forEach((fieldname) => {
        const fieldDiv = container.querySelector(
          `[data-fieldname="${fieldname}"]`,
        );
        if (fieldDiv) watermarkWrapper.appendChild(fieldDiv);
      });
      container.appendChild(watermarkWrapper);

      // 2. WRAP MARGIN FIELDS (4 fields) IN 2-COLUMN GRID
      const marginFields = [
        "watermark_margin_top",
        "watermark_margin_right",
        "watermark_margin_bottom",
        "watermark_margin_left",
      ];
      const marginWrapper = document.createElement("div");
      marginWrapper.className = "margin-fields-grid";
      marginWrapper.style.cssText =
        "display: grid; grid-template-columns: 1fr 1fr; column-gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color);";
      marginFields.forEach((fieldname) => {
        const fieldDiv = container.querySelector(
          `[data-fieldname="${fieldname}"]`,
        );
        if (fieldDiv) marginWrapper.appendChild(fieldDiv);
      });
      container.appendChild(marginWrapper);

      // 3. SET SIDEBAR MAX-WIDTH AND WRAP LANGUAGE + LETTER HEAD IN 2-COLUMN GRID
      const sidebar = document.querySelector(".print-preview-sidebar");
      if (sidebar) {
        // Set max-width on sidebar itself
        sidebar.style.maxWidth = "220px";

        const topFields = ["language", "letterhead"];
        const topWrapper = document.createElement("div");
        topWrapper.className = "top-fields-grid";
        topWrapper.style.cssText =
          "display: grid; grid-template-columns: 1fr 1fr; column-gap: 10px; margin-top: 10px;";
        topFields.forEach((fieldname) => {
          const fieldDiv = sidebar.querySelector(
            `[data-fieldname="${fieldname}"]`,
          );
          if (fieldDiv) topWrapper.appendChild(fieldDiv);
        });
        // Insert wrapper before dynamic-settings (right under Print Format)
        const dynamicSettings = sidebar.querySelector(".dynamic-settings");
        if (dynamicSettings) {
          sidebar.insertBefore(topWrapper, dynamicSettings);
        } else {
          sidebar.insertBefore(topWrapper, sidebar.firstChild.nextSibling);
        }
      }

      // 4. WRAP PAGE NUMBER FIELDS IN 2-COLUMN GRID
      const pageNumberFields = [
        "page_number_display",
        "page_number_position",
        "page_number_font_family",
        "page_number_font_size",
      ];
      const pageNumberWrapper = document.createElement("div");
      pageNumberWrapper.className = "page-number-grid";
      pageNumberWrapper.style.cssText =
        "display: grid; grid-template-columns: 1fr 1fr; column-gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color);";
      pageNumberFields.forEach((fieldname) => {
        const fieldDiv = container.querySelector(
          `[data-fieldname="${fieldname}"]`,
        );
        if (fieldDiv) pageNumberWrapper.appendChild(fieldDiv);
      });
      container.appendChild(pageNumberWrapper);

      // 5. SET MIN-HEIGHT ON ALL LABELS IN GRID WRAPPERS (prevent label overflow)
      document
        .querySelectorAll(
          ".watermark-settings-grid label, .margin-fields-grid label, .top-fields-grid label, .page-number-grid label",
        )
        .forEach((label) => {
          label.style.minHeight = "42px";
          label.style.display = "flex";
          label.style.alignItems = "flex-start";
        });

      console.log("[DEBUG] Sidebar fields wrapped in 2-column grids");
    }, 100);

    return result;
  };
  PV.prototype._debugPatched = true;
  console.log(
    "[DEBUG] PrintView.add_settings_to_sidebar patched for field reordering!",
  );
}
patchPrintViewForDebug();

// Start observing when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    observer.observe(document.body, { childList: true, subtree: true });
  });
} else {
  observer.observe(document.body, { childList: true, subtree: true });
}

const PDPrintLanguageState = {
  retries: 0,
  maxRetries: 20,
  applying: false,
  lastAppliedFormat: null,
  patchRetries: 0,
  patchMaxRetries: 50,
};

apply_print_language();
patch_refresh_print_format();

$(document).on("change", 'input[data-fieldname="print_format"]', () => {
  queue_print_language_apply(150);
});

function apply_print_language() {
  const route = frappe.get_route();
  if (route[0] !== "print") return;
  queue_print_language_apply(500);
}

/**
 * Option A: Patch PrintView.refresh_print_format so the navbar "Refresh"
 * button (and both Shift+R shortcuts) re-assert the Print Format's
 * default_print_language after core's refresh resets it to the doc/customer
 * language.
 *
 * Core flow on refresh:
 *   refresh_print_format() -> set_default_print_language()  (resets
 *   lang_code to this.frm.doc.language priority) -> preview()
 *
 * That reset uses language_selector.val(...) silently (no `change` event),
 * so the format-input listener above never fires. We defeat the
 * lastAppliedFormat guard and re-apply via the same path used on load.
 */
function patch_refresh_print_format() {
  const PV = frappe.ui.form && frappe.ui.form.PrintView;

  if (!PV || !PV.prototype) {
    // PrintView is defined lazily by the print page JS; retry until present.
    if (
      PDPrintLanguageState.patchRetries < PDPrintLanguageState.patchMaxRetries
    ) {
      PDPrintLanguageState.patchRetries += 1;
      setTimeout(patch_refresh_print_format, 200);
    }
    return;
  }

  if (PV.prototype._pdRefreshPatched) return;

  const original_refresh = PV.prototype.refresh_print_format;
  PV.prototype.refresh_print_format = function () {
    const result = original_refresh.apply(this, arguments);

    // Core just reset lang_code back to the customer's language; let the
    // original refresh settle, then re-assert the Print Format default.
    PDPrintLanguageState.lastAppliedFormat = null;
    queue_print_language_apply(250);

    return result;
  };
  PV.prototype._pdRefreshPatched = true;
}

function queue_print_language_apply(delay = 0) {
  setTimeout(() => {
    apply_language_from_print_format();
  }, delay);
}

function apply_language_from_print_format() {
  const route = frappe.get_route();
  if (route[0] !== "print") return;

  const print_format = $('input[data-fieldname="print_format"]').val();
  const lang_input = $('input[data-fieldname="language"]');

  if (!lang_input.length || !print_format || print_format === "Standard") {
    if (PDPrintLanguageState.retries < PDPrintLanguageState.maxRetries) {
      PDPrintLanguageState.retries += 1;
      queue_print_language_apply(250);
    }
    return;
  }

  PDPrintLanguageState.retries = 0;

  if (
    PDPrintLanguageState.applying ||
    PDPrintLanguageState.lastAppliedFormat === print_format
  ) {
    return;
  }

  PDPrintLanguageState.applying = true;

  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "Print Format",
      name: print_format,
    },
    callback: function (r) {
      PDPrintLanguageState.applying = false;

      if (r && r.message && r.message.default_print_language) {
        PDPrintLanguageState.lastAppliedFormat = print_format;
        set_language(r.message.default_print_language);
      }
    },
    error: function () {
      PDPrintLanguageState.applying = false;
    },
  });
}

function set_language(lang_code) {
  const lang_input = $('input[data-fieldname="language"]');
  const lang_display = $(
    '.frappe-control[data-fieldname="language"] .control-value a',
  );

  if (!lang_input.length || !lang_code) return;
  if (lang_input.val() === lang_code) return;

  lang_input.val(lang_code).trigger("change");

  if (lang_display.length) {
    lang_display.text(lang_code);
    lang_display.attr("href", "/desk/language/" + lang_code);
    lang_display.attr("data-name", lang_code);
    lang_display.attr("data-value", lang_code);
  }
}
