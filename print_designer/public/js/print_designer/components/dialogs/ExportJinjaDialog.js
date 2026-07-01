/**
 * ExportJinjaDialog — Design View "Export to Jinja HTML + CSS" dialog.
 *
 * Phase 1 MVP scope:
 *   - read-only export of the current Print Designer format
 *   - shows the Jinja template SOURCE (not a rendered snapshot) and the
 *     layout/wrapper CSS in two scrollable <pre> blocks with separate
 *     Copy buttons
 *   - the HTML block is a self-contained Jinja template: macros inlined,
 *     Print Designer data embedded via frappe.parse_json, userProvidedJinja
 *     preserved as source — paste it into a standard Jinja Print Format
 *     (type = Jinja) and it will render against any doc of the right doctype
 *   - does NOT modify the source Print Format
 *   - does NOT auto-create a new Print Format (that's Phase 2, gated)
 *
 * Loaded into the bundle via the AppHeader.vue import — see
 * `print_designer/components/layout/AppHeader.vue`.
 */

export function showExportJinjaDialog(formatName) {
  if (!formatName) {
    frappe.msgprint({
      title: __("Export to Jinja"),
      message: __("No Print Format is currently loaded."),
      indicator: "orange",
    });
    return;
  }

  const dialog = new frappe.ui.Dialog({
    title: __("Export to Jinja HTML + CSS"),
    fields: [
      {
        fieldname: "bundle_html",
        fieldtype: "HTML",
        options: `
					<div id="export-jinja-bundle" style="font-size: 12px;">
						<p style="color: var(--text-muted); margin: 0;">
							${frappe.utils.escape_html(__("Rendering…"))}
						</p>
					</div>
				`,
      },
    ],
    primary_action_label: __("Close"),
    primary_action: () => dialog.hide(),
  });

  dialog.show();

  const $container = dialog.$wrapper.find("#export-jinja-bundle");

  frappe.call({
    method:
      "print_designer.api.print_format_export_import.export_print_format_as_jinja_bundle",
    args: { print_format_name: formatName },
    freeze: true,
    freeze_message: __("Exporting Print Designer format…"),
    callback: (r) => {
      if (r && r.message) {
        renderBundle($container, r.message, formatName);
      } else {
        showExportError($container, __("Export returned no data."));
      }
    },
    error: (r) => {
      const msg =
        (r && (r._server_messages || r.message || r.exc)) ||
        __("Unknown error");
      showExportError($container, String(msg));
    },
  });
}

function renderBundle($container, bundle, formatName) {
  const html = bundle.html || "";
  const css = bundle.css || "";
  const htmlEscaped = frappe.utils.escape_html(html);
  const cssEscaped = frappe.utils.escape_html(css);
  const htmlLen = html.length.toLocaleString();
  const cssLen = css.length.toLocaleString();
  const formatNameEscaped = frappe.utils.escape_html(formatName);
  const schemaVersion = frappe.utils.escape_html(bundle.schema_version || "?");
  const bridgeVersion = frappe.utils.escape_html(
    bundle.bridge_contract_version || "?",
  );

  $container.html(`
		<div>
			<p
				style="color: var(--text-muted); margin: 0 0 12px 0; font-size: 11px; line-height: 1.4;"
				${frappe.utils.escape_html(
          __(
            "Jinja source template exported from Print Designer format '{0}'. Paste each block into a standard Jinja Print Format (type = Jinja). The HTML is self-contained (macros inlined + data embedded) — it will render against any doc of the right doctype. The CSS is raw, ready for the Print Format's css field.",
          ).replace("'{0}'", formatNameEscaped),
        )}
			</p>

			<div style="margin-bottom: 16px;">
				<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
					<strong style="font-size: 12px;">${frappe.utils.escape_html(
            __("Jinja HTML"),
          )}</strong>
					<span style="color: #999; font-size: 10px;">${htmlLen} chars</span>
					<button
						class="btn btn-xs btn-default export-jinja-copy-btn"
						data-target="html"
						style="margin-left: auto; width: 60px;"
					>
						${frappe.utils.escape_html(__("Copy"))}
					</button>
				</div>
				<pre
					data-pre="html"
					style="max-height: 260px; overflow: auto; background: var(--bg-color); color: var(--text-color); padding: 10px; border-radius: 4px; font-size: 11px; white-space: pre-wrap; word-wrap: break-word; margin: 0;"
				>${htmlEscaped}</pre>
			</div>

			<div>
				<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
					<strong style="font-size: 12px;">${frappe.utils.escape_html(
            __("Jinja CSS"),
          )}</strong>
					<span style="color: #999; font-size: 10px;">${cssLen} chars</span>
					<button
						class="btn btn-xs btn-default export-jinja-copy-btn"
						data-target="css"
						style="margin-left: auto; width: 60px;"
					>
						${frappe.utils.escape_html(__("Copy"))}
					</button>
				</div>
				<pre
					data-pre="css"
					style="max-height: 260px; overflow: auto; background: var(--bg-color); color: var(--text-color); padding: 10px; border-radius: 4px; font-size: 11px; white-space: pre-wrap; word-wrap: break-word; margin: 0;"
				>${cssEscaped}</pre>
			</div>

			<p style="color: #888; font-size: 10px; margin: 12px 0 0 0;">
				${frappe.utils.escape_html(__("Print Designer schema:"))}
				<code>${schemaVersion}</code>
				·
				${frappe.utils.escape_html(__("Bridge contract:"))}
				<code>${bridgeVersion}</code>
				·
				${frappe.utils.escape_html(__("Source:"))}
				<code>${frappe.utils.escape_html(bundle.source || "?")}</code>
			</p>
		</div>
	`);

  $container.find(".export-jinja-copy-btn").on("click", function () {
    const target = $(this).data("target");
    const text = target === "html" ? html : css;
    const label = target === "html" ? __("HTML") : __("CSS");
    copyToClipboard(text, label);
  });
}

function showExportError($container, message) {
  $container.html(`
		<div class="alert alert-danger" style="margin: 0;">
			${frappe.utils.escape_html(__("Export failed"))}:
			${frappe.utils.escape_html(message)}
		</div>
	`);
}

function copyToClipboard(text, label) {
  const onSuccess = () => {
    frappe.show_alert({
      message: __("{0} copied to clipboard", [label]),
      indicator: "green",
    });
  };

  if (
    typeof navigator !== "undefined" &&
    navigator.clipboard &&
    typeof navigator.clipboard.writeText === "function"
  ) {
    navigator.clipboard
      .writeText(text)
      .then(onSuccess)
      .catch(() => {
        fallbackCopy(text, onSuccess);
      });
    return;
  }

  fallbackCopy(text, onSuccess);
}

function fallbackCopy(text, onSuccess) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.top = "0";
  ta.style.left = "0";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (e) {
    copied = false;
  }
  document.body.removeChild(ta);

  if (copied && onSuccess) {
    onSuccess();
  } else {
    frappe.msgprint({
      title: __("Copy failed"),
      message: __(
        "Could not copy to clipboard automatically. Please select the text manually.",
      ),
      indicator: "red",
    });
  }
}

// Expose on window as well so non-bundler callers (e.g. doctype_js) can use it.
if (typeof window !== "undefined") {
  window.showExportJinjaDialog = showExportJinjaDialog;
}
