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
      "watermark_top",
      "watermark_right",
      "watermark_bottom",
      "watermark_left",
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
      (s) => s.fieldname === "watermark_bottom",
    );
    if (marginBottomIndex > 0) {
      reorderedSettings.splice(marginBottomIndex, 0, {
        fieldname: "watermark_col_break",
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

      // 0. COPY COUNT + PDF PAGE SIZE IN 1:1 GRID
      // Enable Multiple Copies stays standalone
      const copyFields = ["default_copy_count", "pdf_page_size"];
      const copyWrapper = document.createElement("div");
      copyWrapper.className = "copy-controls-grid";
      copyWrapper.style.cssText =
        "display: grid; grid-template-columns: 1fr 1fr; column-gap: 10px; margin-top: 10px;";
      copyFields.forEach((fieldname) => {
        const fieldDiv = container.querySelector(
          `[data-fieldname="${fieldname}"]`,
        );
        if (fieldDiv) copyWrapper.appendChild(fieldDiv);
      });
      container.appendChild(copyWrapper);

      // 1. WRAP COPY LABELS (Original Label, Copy Label) IN 2-COLUMN GRID
      // This comes after Copy Count, before Watermark settings
      const labelFields = ["default_original_label", "default_copy_label"];
      const labelWrapper = document.createElement("div");
      labelWrapper.className = "copy-labels-grid";
      labelWrapper.style.cssText =
        "display: grid; grid-template-columns: 1fr 1fr; column-gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color);";
      labelFields.forEach((fieldname) => {
        const fieldDiv = container.querySelector(
          `[data-fieldname="${fieldname}"]`,
        );
        if (fieldDiv) labelWrapper.appendChild(fieldDiv);
      });
      container.appendChild(labelWrapper);

      // Disable label fields in preview sidebar - Watermark per Page is source of truth.
      ["default_original_label", "default_copy_label"].forEach((fieldname) => {
        const input = container.querySelector(
          `[data-fieldname="${fieldname}"] input`,
        );
        const field = container.querySelector(
          `[data-fieldname="${fieldname}"]`,
        );
        if (input) {
          input.readOnly = true;
          input.disabled = true;
          input.classList.add("disabled");
        }
        if (field) {
          field.style.opacity = "0.7";
          field.style.pointerEvents = "none";
        }
      });

      // 2. WRAP WATERMARK SETTINGS (4 fields) IN 2-COLUMN GRID
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

      // DEBUG: Track watermark_font_size changes
      const fontSizeInput = container.querySelector(
        '[data-fieldname="watermark_font_size"] input',
      );
      if (fontSizeInput) {
        console.log(
          "[DEBUG] watermark_font_size input found:",
          fontSizeInput.value,
        );
        fontSizeInput.addEventListener("input", (e) => {
          console.log(
            "[DEBUG] watermark_font_size CHANGED to:",
            e.target.value,
          );
        });
        fontSizeInput.addEventListener("change", (e) => {
          console.log("[DEBUG] watermark_font_size onchange:", e.target.value);
        });
      }

      // DEBUG: Track watermark_font_family changes
      const fontFamilySelect = container.querySelector(
        '[data-fieldname="watermark_font_family"] select',
      );
      if (fontFamilySelect) {
        console.log(
          "[DEBUG] watermark_font_family found, current value:",
          fontFamilySelect.value,
        );
        fontFamilySelect.addEventListener("change", (e) => {
          console.log(
            "[DEBUG] watermark_font_family CHANGED to:",
            e.target.value,
          );
        });
      }

      // DEBUG: Track margin changes
      [
        "watermark_top",
        "watermark_right",
        "watermark_bottom",
        "watermark_left",
      ].forEach((fieldname) => {
        const marginInput = container.querySelector(
          `[data-fieldname="${fieldname}"] input`,
        );
        if (marginInput) {
          marginInput.addEventListener("input", (e) => {
            console.log(`[DEBUG] ${fieldname} CHANGED to:`, e.target.value);
          });
        }
      });

      // SMART DEFAULT: when Top Right is selected for the first time,
      // seed Top/Right margins with 10mm if those fields are still untouched/zero.
      const positionSelect = container.querySelector(
        '[data-fieldname="watermark_position"] select',
      );
      const topInput = container.querySelector(
        '[data-fieldname="watermark_top"] input',
      );
      const rightInput = container.querySelector(
        '[data-fieldname="watermark_right"] input',
      );

      const syncFieldValue = (input, value) => {
        if (!input) return;
        input.value = String(value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
      };

      const shouldSeedTopRightDefaults = () => {
        const topValue = (topInput?.value || "").trim();
        const rightValue = (rightInput?.value || "").trim();
        return ["", "0"].includes(topValue) && ["", "0"].includes(rightValue);
      };

      const applySmartPositionDefaults = () => {
        if (!positionSelect || positionSelect.value !== "Top Right") return;
        if (!shouldSeedTopRightDefaults()) return;

        console.log(
          "[DEBUG] Auto-seeding Top Right watermark margins to top=10, right=10",
        );
        syncFieldValue(topInput, 10);
        syncFieldValue(rightInput, 10);
      };

      if (positionSelect && !positionSelect.dataset.pdSmartDefaultsBound) {
        positionSelect.dataset.pdSmartDefaultsBound = "1";
        positionSelect.addEventListener("change", () => {
          setTimeout(applySmartPositionDefaults, 0);
        });
        setTimeout(applySmartPositionDefaults, 0);
      }

      // SMART DEFAULT: Page Number Position auto-set margins to align with watermark
      const pagePositionSelect = container.querySelector(
        '[data-fieldname="page_number_position"] select',
      );
      const pnTopInput = container.querySelector(
        '[data-fieldname="page_number_top"] input',
      );
      const pnRightInput = container.querySelector(
        '[data-fieldname="page_number_right"] input',
      );
      const pnBottomInput = container.querySelector(
        '[data-fieldname="page_number_bottom"] input',
      );
      const pnLeftInput = container.querySelector(
        '[data-fieldname="page_number_left"] input',
      );

      const shouldSeedPnMargins = () => {
        const topVal = (pnTopInput?.value || "").trim();
        const rightVal = (pnRightInput?.value || "").trim();
        const bottomVal = (pnBottomInput?.value || "").trim();
        const leftVal = (pnLeftInput?.value || "").trim();
        return (
          ["", "0", "2"].includes(topVal) &&
          ["", "0", "2"].includes(rightVal) &&
          ["", "0", "2"].includes(bottomVal) &&
          ["", "0", "2"].includes(leftVal)
        );
      };

      const applyPnSmartDefaults = () => {
        if (!pagePositionSelect || !shouldSeedPnMargins()) return;
        const pos = pagePositionSelect.value;
        console.log("[DEBUG] Applying page number smart margins for:", pos);

        // Reset all to 2 (default)
        syncFieldValue(pnTopInput, 2);
        syncFieldValue(pnRightInput, 2);
        syncFieldValue(pnBottomInput, 2);
        syncFieldValue(pnLeftInput, 2);

        // Add 8 to align with watermark (watermark default is 10mm)
        // Function already adds 2, so 2 + 8 = 10
        if (pos === "Top Right") {
          syncFieldValue(pnRightInput, 8); // 2 + 8 = 10
        } else if (pos === "Top Left") {
          syncFieldValue(pnLeftInput, 8); // 2 + 8 = 10
        } else if (pos === "Bottom Right") {
          syncFieldValue(pnRightInput, 8);
        } else if (pos === "Bottom Left") {
          syncFieldValue(pnLeftInput, 8);
        }
        // Top Center, Bottom Center, Middle positions keep default 2
      };

      if (pagePositionSelect && !pagePositionSelect.dataset.pdPnSmartBound) {
        pagePositionSelect.dataset.pdPnSmartBound = "1";
        pagePositionSelect.addEventListener("change", () => {
          setTimeout(applyPnSmartDefaults, 0);
        });
        setTimeout(applyPnSmartDefaults, 0);
      }

      // Disable label fields in preview sidebar - Watermark per Page is source of truth.

      // 2. WRAP MARGIN FIELDS (4 fields) IN 2-COLUMN GRID
      const marginFields = [
        "watermark_top",
        "watermark_right",
        "watermark_bottom",
        "watermark_left",
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
      // NOTE: page_number_col_break and page_number_col_break_02 are internal - not included
      const pageNumberFields = [
        "page_number_display",
        "page_number_position",
        "page_number_font_family",
        "page_number_font_size",
        "page_number_font_color",
        "page_number_border",
        "page_number_top",
        "page_number_right",
        "page_number_bottom",
        "page_number_left",
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

      // 6. HIDE ALL DESCRIPTION (HELP-BOX) IN SIDEBAR - saves space
      document
        .querySelectorAll(".print-preview-sidebar .help-box")
        .forEach((el) => {
          el.style.display = "none";
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

/**
 * Patch setup_print_format_dom to add id to print-format div
 * Line 514: this.$print_format_body.find("body").html(`<div class="print-format print-format-preview">`)
 */
function patch_setup_print_format_dom() {
  const PV = frappe.ui.form && frappe.ui.form.PrintView;

  if (!PV || !PV.prototype) {
    setTimeout(patch_setup_print_format_dom, 200);
    return;
  }

  if (PV.prototype._pdSetupPrintFormatDomPatched) return;

  const original = PV.prototype.setup_print_format_dom;
  PV.prototype.setup_print_format_dom = function (_out, _$print_format) {
    original.apply(this, arguments);

    // Add id to the print-format div (line 514 equivalent)
    this.$print_format_body
      .find(".print-format")
      .attr("id", "tbs__print__page__preview");

    // Add max-width unset (lines 518-521 equivalent)
    // Need !important because .print-format has max-width: 210.0mm !important
    this.$print_format_body
      .find(".print-format")
      .css("max-width", "unset !important");
  };

  PV.prototype._pdSetupPrintFormatDomPatched = true;
}

// Start the patch
patch_setup_print_format_dom();

/**
 * Override set_default_print_language() to PRIORITIZE Print Format language over document language.
 *
 * Frappe core priority (WRONG for our use case):
 *   print_format.default_print_language || frm.doc.language || frappe.boot.lang
 *
 * Print Designer priority (CORRECT):
 *   frm.doc.language || print_format.default_print_language || frappe.boot.lang
 *
 * Why: Document may have language="en" from customer/system defaults,
 * but Print Format has its own default_print_language="th" which should WIN.
 */
function patch_set_default_print_language() {
  const PV = frappe.ui.form && frappe.ui.form.PrintView;
  if (!PV || !PV.prototype) {
    setTimeout(patch_set_default_print_language, 200);
    return;
  }
  if (PV.prototype._pdSetDefaultLangPatched) return;

  const original = PV.prototype.set_default_print_language;
  PV.prototype.set_default_print_language = function () {
    // Call original to get all the Frappe-side initialization
    original.apply(this, arguments);

    // FIXED PRIORITY: Print Format > Document > System
    // This ensures Print Format's default_print_language wins over document's language
    if (this.frm && this.frm.doc) {
      const docLang = this.frm.doc.language;
      // Access print_format from this context (it's set by core before this method is called)
      const pfLang =
        this.print_format && this.print_format.default_print_language;
      const systemLang = frappe.boot.lang;

      // Priority: Print Format > Document > System
      const resolvedLang = pfLang || docLang || systemLang;

      if (resolvedLang !== this.lang_code) {
        console.log(
          "[PD Language Override] set_default_print_language - NEW priority:",
        );
        console.log("  Original lang_code:", this.lang_code);
        console.log("  Print Format language:", pfLang, "(WINS!)");
        console.log("  Document language:", docLang, "(fallback)");
        console.log("  System language:", systemLang, "(last fallback)");
        console.log("  NEW lang_code:", resolvedLang);
        this.lang_code = resolvedLang;
      }
    }
  };

  PV.prototype._pdSetDefaultLangPatched = true;
  console.log("[PD Language Override] set_default_print_language() patched!");
}

/**
 * DEBUG: Track print format column labels when rendered
 * Logs column labels from print_designer_print_format to help debug mixed language issues
 */
function patch_print_format_render() {
  const PV = frappe.ui.form && frappe.ui.form.PrintView;
  if (!PV || !PV.prototype) {
    setTimeout(patch_print_format_render, 200);
    return;
  }
  if (PV.prototype._pdPrintFormatRenderPatched) return;

  // Override the method that sets up print format content
  const original_render = PV.prototype.render_page;
  PV.prototype.render_page = function () {
    // Call original
    const result = original_render.apply(this, arguments);

    // DEBUG: Log print format data after render
    setTimeout(() => {
      console.log(
        "[PD Column Labels DEBUG] ════════════════════════════════════════",
      );
      console.log("[PD Column Labels DEBUG] Print Format columns from DB:");

      // Find table columns in the DOM
      const tables = document.querySelectorAll(
        '.print-format-table, [data-fieldname="items"]',
      );
      tables.forEach((table, tIdx) => {
        console.log(`[PD Column Labels DEBUG] Table ${tIdx}:`, table.tagName);
        const headers = table.querySelectorAll("th, .column-header");
        headers.forEach((header, hIdx) => {
          const text = header.textContent.trim();
          const hasThai = /[\u0e00-\u0e7f]/.test(text);
          const lang = hasThai ? "TH" : "EN";
          console.log(
            `[PD Column Labels DEBUG]   [${lang}] Column ${hIdx}: "${text}"`,
          );
        });
      });

      // Also log print format name and language
      const pfInput = document.querySelector(
        'input[data-fieldname="print_format"]',
      );
      const langInput = document.querySelector(
        'input[data-fieldname="language"]',
      );
      console.log(
        "[PD Column Labels DEBUG] Print Format:",
        pfInput ? pfInput.value : "unknown",
      );
      console.log(
        "[PD Column Labels DEBUG] Language:",
        langInput ? langInput.value : "unknown",
      );
      console.log(
        "[PD Column Labels DEBUG] URL _lang param:",
        new URLSearchParams(window.location.search).get("_lang"),
      );
      console.log(
        "[PD Column Labels DEBUG] ════════════════════════════════════════",
      );
    }, 100);

    return result;
  };

  PV.prototype._pdPrintFormatRenderPatched = true;
  console.log("[PD Column Labels DEBUG] render_page() patched!");
}

// Start the patch
patch_set_default_print_language();
patch_print_format_render();

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
