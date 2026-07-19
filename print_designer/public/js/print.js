/**
 * Print Designer - Print Page Language Override
 *
 * Safe client-only helper:
 * - wait for the print page inputs to exist
 * - ignore placeholder "Standard"
 * - fetch Print Format.default_print_language when a real format is selected
 * - apply it through the existing Language control
 */

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
