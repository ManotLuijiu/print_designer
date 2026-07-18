/**
 * Print Designer - Print Page Language Override
 *
 * Safe client-only helper:
 * - wait for the print page inputs to exist
 * - ignore placeholder "Standard"
 * - fetch Print Format.default_print_language when a real format is selected
 * - apply it through the existing Language control
 */

console.log("[PD PRINT] Print Designer print.js LOADED!");

const PDPrintLanguageState = {
  retries: 0,
  maxRetries: 20,
  applying: false,
  lastAppliedFormat: null,
};

apply_print_language();

$(document).on("change", 'input[data-fieldname="print_format"]', () => {
  queue_print_language_apply(150);
});

function apply_print_language() {
  const route = frappe.get_route();
  console.log("[PD PRINT] apply_print_language(), route:", route);
  if (route[0] !== "print") {
    console.log("[PD PRINT] Not on print page, skipping");
    return;
  }
  queue_print_language_apply(500);
}

function queue_print_language_apply(delay = 0) {
  setTimeout(() => {
    apply_language_from_print_format();
  }, delay);
}

function apply_language_from_print_format() {
  const route = frappe.get_route();
  console.log("[PD PRINT] apply_language_from_print_format(), route:", route);
  if (route[0] !== "print") return;

  const print_format = $('input[data-fieldname="print_format"]').val();
  const lang_input = $('input[data-fieldname="language"]');
  console.log(
    "[PD PRINT] print_format:",
    print_format,
    "lang_input found:",
    lang_input.length,
  );

  if (!lang_input.length || !print_format || print_format === "Standard") {
    console.log(
      "[PD PRINT] Waiting for elements... retries:",
      PDPrintLanguageState.retries,
    );
    if (PDPrintLanguageState.retries < PDPrintLanguageState.maxRetries) {
      PDPrintLanguageState.retries += 1;
      queue_print_language_apply(250);
    }
    return;
  }

  console.log(
    "[PD PRINT] Found elements, calling API for print format language",
  );

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
  console.log("[PD PRINT] set_language() called with:", lang_code);
  const lang_input = $('input[data-fieldname="language"]');
  const lang_display = $(
    '.frappe-control[data-fieldname="language"] .control-value a',
  );

  if (!lang_input.length || !lang_code) {
    console.log("[PD PRINT] No lang_input or lang_code");
    return;
  }
  if (lang_input.val() === lang_code) {
    console.log("[PD PRINT] Already set to:", lang_code);
    return;
  }

  console.log("[PD PRINT] Setting language to:", lang_code);
  lang_input.val(lang_code).trigger("change");

  if (lang_display.length) {
    lang_display.text(lang_code);
    lang_display.attr("href", "/desk/language/" + lang_code);
    lang_display.attr("data-name", lang_code);
    lang_display.attr("data-value", lang_code);
  }
}
