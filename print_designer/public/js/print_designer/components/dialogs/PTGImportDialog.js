/**
 * PTGImportDialog - Design View "Import from PTG Template" dialog.
 *
 * Slice A: PTG-driven Import flow. Lets the user pick a PTG Template (an
 * annotation from the Print Template Generator app) and pulls the generated
 * html+css into the current Print Format.
 *
 * Workflow:
 *   1. User opens print-designer/{form_name} and clicks "Import PTG"
 *      under the Import dropdown.
 *   2. Dialog opens, user picks a PTG Template from the link field.
 *   3. Preview iframe loads via `get_ptg_preview_html`.
 *   4. "Import" primary action calls `import_from_ptg_template`, which
 *      writes html + css to the current Print Format (no new doc, no
 *      doc_type change).
 *   5. On success, offer to reload the page.
 *
 * Requires the print_template_generator app to be installed. If not, the
 * "Import PTG" menu item is hidden at the caller level (see AppHeader).
 */

export function showPTGImportDialog(formatName) {
  if (!formatName) {
    frappe.msgprint({
      title: __("Import from PTG Template"),
      message: __("No Print Format is currently loaded."),
      indicator: "orange",
    });
    return;
  }

  const dialog = new frappe.ui.Dialog({
    title: __("Import from PTG Template"),
    fields: [
      {
        fieldname: "info",
        fieldtype: "HTML",
        options: `<p style="margin: 0 0 8px 0; font-size: 12px; color: var(--text-muted);">
          ${frappe.utils.escape_html(
            __(
              "Pick a PTG Template (an annotation from the Print Template Generator app). The dialog pulls the generated HTML + CSS and writes them onto this Print Format. Existing doc_type and Print Designer flag are preserved.",
            ),
          )}
        </p>`,
      },
      {
        fieldname: "ptg_template",
        fieldtype: "Link",
        options: "PTG Template",
        label: __("PTG Template"),
        reqd: 1,
        get_query: () =>
          "filters=" +
          encodeURIComponent(JSON.stringify([["layout_json", "is", "set"]])),
        onchange: () => loadPreview(dialog),
      },
      {
        fieldname: "preview_html",
        fieldtype: "HTML",
        options: `<div id="ptg-import-preview" style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">
          ${frappe.utils.escape_html(
            __("Select a PTG Template to preview its generated output."),
          )}
        </div>`,
      },
    ],
    primary_action_label: __("Import"),
    primary_action: () => doImport(dialog, formatName),
  });

  dialog.show();
}

function loadPreview(dialog) {
  const templateName = dialog.get_value("ptg_template");
  if (!templateName) {
    const $preview = dialog.$wrapper.find("#ptg-import-preview");
    $preview.html(
      `<div style="color: var(--text-muted);">${frappe.utils.escape_html(
        __("Select a PTG Template to preview its generated output."),
      )}</div>`,
    );
    return;
  }
  const $preview = dialog.$wrapper.find("#ptg-import-preview");
  $preview.html(
    `<div style="color: var(--text-muted);">${frappe.utils.escape_html(
      __("Loading preview…"),
    )}</div>`,
  );

  frappe.call({
    method:
      "print_designer.api.print_format_export_import.get_ptg_preview_html",
    args: { ptg_template: templateName },
    callback: (r) => {
      if (!r || !r.message) {
        $preview.html(
          `<div class="alert alert-warning" style="margin: 0;">${frappe.utils.escape_html(
            __("Preview not available."),
          )}</div>`,
        );
        return;
      }
      // Wrap in a styled container with a title bar
      $preview.html(
        `<div style="border: 1px solid var(--gray-300); border-radius: 4px; overflow: hidden; background: var(--bg-color);">
          <div style="padding: 4px 8px; font-size: 11px; color: var(--text-muted); background: var(--control-bg); border-bottom: 1px solid var(--gray-300);">
            ${frappe.utils.escape_html(__("Preview"))}
          </div>
          <iframe
            srcdoc="${frappe.utils.escape_html(r.message).replace(/"/g, "&quot;")}"
            style="width: 100%; min-height: 320px; border: 0; background: white;"
            sandbox="allow-same-origin"
          ></iframe>
        </div>`,
      );
    },
    error: (r) => {
      const msg =
        (r && (r._server_messages || r.message || r.exc)) ||
        __("Preview request failed");
      $preview.html(
        `<div class="alert alert-danger" style="margin: 0;">${frappe.utils.escape_html(
          String(msg),
        )}</div>`,
      );
    },
  });
}

function doImport(dialog, formatName) {
  const templateName = dialog.get_value("ptg_template");
  if (!templateName) {
    frappe.msgprint({
      title: __("Cannot Import"),
      message: __("Pick a PTG Template first."),
      indicator: "orange",
    });
    return;
  }
  frappe.call({
    method:
      "print_designer.api.print_format_export_import.import_from_ptg_template",
    args: {
      print_format_name: formatName,
      ptg_template: templateName,
    },
    freeze: true,
    freeze_message: __("Importing from PTG Template…"),
    callback: (r) => {
      const result = r && r.message;
      if (!result) {
        frappe.msgprint({
          title: __("Import failed"),
          message: __("No result from server."),
          indicator: "red",
        });
        return;
      }
      const htmlKb = Math.round((result.html_length || 0) / 1024);
      const cssKb = Math.round((result.css_length || 0) / 1024);
      frappe.show_alert({
        message: __("Imported {0} ({1} KB) + CSS ({2} KB) from {3}").format(
          result.print_format_name,
          htmlKb,
          cssKb,
          result.ptg_template,
        ),
        indicator: "green",
      });
      dialog.hide();
      // Offer to reload the designer to see the imported content
      frappe.confirm(
        __("Reload the Print Designer to see the imported output?"),
        () => {
          frappe.set_route("print-designer", formatName);
        },
      );
    },
    error: (r) => {
      const msg =
        (r && (r._server_messages || r.message || r.exc)) ||
        __("Import failed");
      frappe.msgprint({
        title: __("Import failed"),
        message: String(msg),
        indicator: "red",
      });
    },
  });
}

if (typeof window !== "undefined") {
  window.showPTGImportDialog = showPTGImportDialog;
}
