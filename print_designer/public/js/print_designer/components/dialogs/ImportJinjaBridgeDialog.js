/**
 * ImportJinjaBridgeDialog - Design View "Import from Jinja Bridge" dialog.
 *
 * Phase 1 MVP: template-first Import. Accepts only a bundle with required
 * PD:METADATA / PD:HEADER / PD:CONTENT / PD:FOOTER / PD:CSS markers. Validates
 * before any save. Shows blockers + warnings, then enables Import when valid.
 *
 * Loaded into the bundle via the AppHeader.vue import.
 */

const REQUIRED_MARKERS = [
  "PD:METADATA",
  "PD:HEADER",
  "PD:CONTENT",
  "PD:FOOTER",
  "PD:CSS",
];

export function showImportJinjaBridgeDialog(formatName) {
  if (!formatName) {
    frappe.msgprint({
      title: __("Import from Jinja Bridge"),
      message: __("No Print Format is currently loaded."),
      indicator: "orange",
    });
    return;
  }

  const dialog = new frappe.ui.Dialog({
    title: __("Import from Jinja Bridge Template"),
    fields: [
      {
        fieldname: "help",
        fieldtype: "HTML",
        options: `<p style="margin: 0 0 8px 0; font-size: 12px; color: var(--text-muted);">
          ${frappe.utils.escape_html(
            __(
              "Template-first Import. Paste a bundle that uses the required PD:HEADER / PD:CONTENT / PD:FOOTER / PD:CSS markers. The MVP supports a small subset only (static text, images, simple rectangles). Tables, barcodes, and flex/grid layouts are not supported.",
            ),
          )}
        </p>
        <p style="margin: 0 0 12px 0; font-size: 11px; color: var(--text-muted);">
          <button class="btn btn-xs btn-default import-download-btn" type="button" style="margin-right: 6px;">
            ${frappe.utils.escape_html(__("Download Import Template"))}
          </button>
          <span>${frappe.utils.escape_html(__("or paste a completed template below."))}</span>
        </p>`,
      },
      {
        fieldname: "bundle_text",
        fieldtype: "Code",
        options: "HTML",
        label: __("Bundle Text"),
        description: __("Paste the full template text including markers."),
        reqd: 1,
      },
      {
        fieldname: "validation_html",
        fieldtype: "HTML",
        options: `<div id="import-bridge-validation" style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
          ${frappe.utils.escape_html(__("Awaiting validation\u2026"))}
        </div>`,
      },
    ],
    primary_action_label: __("Import"),
    primary_action: () => {
      const bundle = dialog.get_value("bundle_text");
      if (!bundle || !state.lastReport || !state.lastReport.valid) {
        frappe.msgprint({
          title: __("Cannot Import"),
          message: __("Bundle is not valid. Resolve blockers first."),
          indicator: "red",
        });
        return;
      }
      doImport(dialog, formatName, bundle);
    },
  });

  const state = { lastReport: null, $validation: null };

  dialog.show();
  setImportEnabled(dialog, false);

  // Wire the "Download Import Template" button
  const $dl = dialog.$wrapper.find(".import-download-btn");
  if ($dl.length) {
    $dl.on("click", () => downloadTemplate(formatName));
  }

  // After dialog is shown, run initial validation on whatever the user
  // has already pasted. We use a small debounce so we don't hammer the
  // server while they are typing.
  state.$validation = dialog.$wrapper.find("#import-bridge-validation");
  const $bundleField = dialog.$wrapper.find("[data-fieldname='bundle_text']");
  let timer = null;
  const runValidation = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const bundle = dialog.get_value("bundle_text");
      if (!bundle || !bundle.trim()) {
        renderValidation(state.$validation, null);
        return;
      }
      validate(bundle, state, dialog);
    }, 300);
  };
  $bundleField.on("input", runValidation);
  // Initial pass for any prefilled content
  runValidation();

  // Expose the dialog for debugging
  dialog.$wrapper.data("bridge-dialog", { dialog, state });
}

function downloadTemplate(formatName) {
  frappe.call({
    method:
      "print_designer.api.print_format_export_import.download_print_designer_import_template",
    args: { print_format_name: formatName },
    callback: (r) => {
      if (!r || !r.message) return;
      const text = r.message;
      const blob = new Blob([text], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `print_designer_import_template${formatName ? "_" + formatName : ""}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    error: () => {
      frappe.msgprint({
        title: __("Download failed"),
        message: __(
          "Could not download the import template right now. Please try again.",
        ),
        indicator: "red",
      });
    },
  });
}

function validate(bundle, state, dialog) {
  if (!state.$validation || !state.$validation.length) return;
  setImportEnabled(dialog, false);
  renderValidation(state.$validation, { loading: true });
  frappe.call({
    method:
      "print_designer.api.print_format_export_import.validate_print_designer_import_bundle",
    args: { bundle_text: bundle },
    callback: (r) => {
      const report = r && r.message;
      state.lastReport = report;
      setImportEnabled(dialog, !!(report && report.valid));
      renderValidation(state.$validation, { report });
    },
    error: () => {
      state.lastReport = null;
      setImportEnabled(dialog, false);
      renderValidation(state.$validation, {
        error: __("Validation request failed."),
      });
    },
  });
}

function setImportEnabled(dialog, enabled) {
  const $btn =
    dialog && dialog.get_primary_btn ? dialog.get_primary_btn() : null;
  if ($btn && $btn.length) {
    $btn.prop("disabled", !enabled);
    $btn.toggleClass("btn-disabled", !enabled);
  }
}

function renderValidation($el, payload) {
  if (!$el || !$el.length) return;
  if (!payload) {
    $el.html(
      `<div style="color: var(--text-muted);">${frappe.utils.escape_html(
        __("Awaiting validation\u2026"),
      )}</div>`,
    );
    return;
  }
  if (payload.loading) {
    $el.html(
      `<div style="color: var(--text-muted);">${frappe.utils.escape_html(
        __("Validating\u2026"),
      )}</div>`,
    );
    return;
  }
  if (payload.error) {
    $el.html(
      `<div class="alert alert-danger" style="margin: 0;">${frappe.utils.escape_html(
        payload.error,
      )}</div>`,
    );
    return;
  }
  const r = payload.report || {};
  const sections = r.sections || {};
  const sectionLabels = {
    metadata: __("Metadata"),
    header: __("Header"),
    content: __("Content"),
    footer: __("Footer"),
    css: __("CSS"),
  };
  const sectionRows = Object.keys(sectionLabels)
    .map((k) => {
      const s = sections[k] || {};
      const present = s.present;
      const cls = present ? "ok" : "missing";
      const tag = present
        ? `<span style="color: var(--green-600);">✓</span>`
        : `<span style="color: var(--red-600);">✗</span>`;
      return `<li style="margin: 0; padding: 2px 0;">
        ${tag}
        <strong>${sectionLabels[k]}</strong>
        <span style="color: var(--text-muted); font-size: 10px;">
          ${present ? `(${s.length || 0} chars)` : __("missing")}
        </span>
      </li>`;
    })
    .join("");

  const blockers = r.blockers || [];
  const warnings = r.warnings || [];
  const unsupported = r.unsupported_detected || [];

  const blockersHtml = blockers.length
    ? `<div style="margin-top: 8px;"><strong style="color: var(--red-600);">${frappe.utils.escape_html(
        __("Blockers"),
      )}</strong><ul style="margin: 4px 0 0 16px; padding: 0;">${blockers
        .map(
          (b) =>
            `<li style="color: var(--red-600);">${frappe.utils.escape_html(b)}</li>`,
        )
        .join("")}</ul></div>`
    : "";

  const warningsHtml = warnings.length
    ? `<div style="margin-top: 8px;"><strong style="color: var(--yellow-600);">${frappe.utils.escape_html(
        __("Warnings"),
      )}</strong><ul style="margin: 4px 0 0 16px; padding: 0;">${warnings
        .map(
          (w) =>
            `<li style="color: var(--text-muted);">${frappe.utils.escape_html(w)}</li>`,
        )
        .join("")}</ul></div>`
    : "";

  const unsupportedHtml = unsupported.length
    ? `<div style="margin-top: 4px; font-size: 11px; color: var(--text-muted);">
        <strong>${frappe.utils.escape_html(__("Unsupported detected:"))}</strong>
        ${unsupported.map(frappe.utils.escape_html).join(", ")}
      </div>`
    : "";

  const statusBanner = r.valid
    ? `<div style="color: var(--green-600); margin-bottom: 4px;">✓ ${frappe.utils.escape_html(
        __("Valid. Import is allowed."),
      )}</div>`
    : `<div style="color: var(--red-600); margin-bottom: 4px;">✗ ${frappe.utils.escape_html(
        __("Invalid. Resolve blockers before importing."),
      )}</div>`;

  $el.html(`
    ${statusBanner}
    <ul style="list-style: none; margin: 0 0 4px 0; padding: 0;">${sectionRows}</ul>
    ${blockersHtml}
    ${warningsHtml}
    ${unsupportedHtml}
  `);
}

function doImport(dialog, formatName, bundle) {
  frappe.call({
    method:
      "print_designer.api.print_format_export_import.import_print_designer_from_jinja_bundle",
    args: {
      print_format_name: formatName,
      bundle_text: bundle,
    },
    freeze: true,
    freeze_message: __("Importing Print Designer format\u2026"),
    callback: (r) => {
      const result = r && r.message;
      frappe.show_alert({
        message: __("Imported {0} sections into {1}").format(
          Object.keys(result && result.sections ? result.sections : {})
            .filter((k) => result.sections[k] && result.sections[k].present)
            .join(", "),
          formatName,
        ),
        indicator: "green",
      });
      dialog.hide();
      // Offer to reload the designer
      frappe.confirm(
        __("Reload the Print Designer to see the imported format?"),
        () => {
          frappe.set_route("print-designer", formatName);
        },
      );
    },
    error: (r) => {
      const msg =
        (r && (r._server_messages || r.message || r.exc)) ||
        __("Unknown error");
      frappe.msgprint({
        title: __("Import failed"),
        message: String(msg),
        indicator: "red",
      });
    },
  });
}

if (typeof window !== "undefined") {
  window.showImportJinjaBridgeDialog = showImportJinjaBridgeDialog;
}
