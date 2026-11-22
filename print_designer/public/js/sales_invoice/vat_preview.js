// Read-only VAT preview of a draft Sales Invoice (SI-03, Task A).
//
// The two buttons live in the "Preview" group of the form, below the
// "Accounting Ledger" button of ERPNext.  They show a proposal of the VAT
// of the saved draft: nothing is written, no row of the Output VAT Undue
// ledger is created, no GL entry is posted and no report artifact is made.
//
// A new invoice has no stored values yet, so the buttons wait for a saved
// draft.  A submitted invoice has its own reports.

frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (frm.doc.docstatus !== 0 || frm.is_new()) return;

		frm.add_custom_button(
			__("Output VAT Report"),
			function () {
				show_vat_preview(frm, "due");
			},
			__("Preview"),
		);

		frm.add_custom_button(
			__("Output VAT Undue Report"),
			function () {
				show_vat_preview(frm, "undue");
			},
			__("Preview"),
		);
	},
});

function show_vat_preview(frm, part) {
	frappe.call({
		method: "print_designer.api.sales_invoice_vat_preview.get_draft_vat_preview",
		args: { sales_invoice: frm.doc.name },
		freeze: true,
		freeze_message: __("Reading the VAT of the draft..."),
		callback: function (r) {
			if (r.message) show_vat_preview_dialog(r.message, part);
		},
	});
}

function show_vat_preview_dialog(preview, part) {
	const title =
		part === "undue"
			? __("Output VAT Undue Report")
			: __("Output VAT Report");

	const dialog = new frappe.ui.Dialog({
		size: "large",
		title: title,
		fields: [
			{ fieldname: "banner", fieldtype: "HTML" },
			{ fieldname: "preview", fieldtype: "HTML" },
			{ fieldname: "warnings", fieldtype: "HTML" },
		],
		primary_action_label: __("Close"),
		primary_action: () => dialog.hide(),
	});

	dialog.show();
	dialog.set_df_property("banner", "options", banner_html(preview));
	dialog.set_df_property("preview", "options", preview_html(preview, part));
	dialog.set_df_property("warnings", "options", warnings_html(preview));
}

function banner_html(preview) {
	return `<div class="alert alert-warning" style="margin-bottom: 12px;">
		<div class="font-weight-bold">${escape(preview.marker)}</div>
		<div class="small">${escape(preview.note)}</div>
	</div>`;
}

function preview_html(preview, part) {
	const currency = preview.company_currency || preview.currency;
	const rows =
		part === "undue"
			? [
					["Tax Invoice No.", preview.sales_invoice],
					["Company", preview.company],
					["Posting Date", preview.posting_date],
					["Customer", preview.customer],
					["Status of the tracking", preview.status],
					["Treatment", preview.treatment],
					["Reason", preview.treatment_reason],
					["Classification", preview.classification],
					[
						"Tracked in the Output VAT Undue ledger",
						preview.is_tracked ? __("Yes") : __("No"),
					],
					[
						"Eligible service base",
						money(preview.service_base_amount, currency),
					],
					[
						"Prospective undue VAT",
						money(preview.undue_vat_amount, currency),
					],
					["VAT due now", money(preview.due_vat_amount, currency)],
				]
			: [
					["Tax Invoice No.", preview.sales_invoice],
					["Tax Invoice Date", preview.posting_date],
					["Customer Name", preview.customer_name],
					["Customer Tax ID", preview.customer_tax_id],
					["Base Amount", money(preview.base_net_total, currency)],
					["VAT Amount", money(preview.vat_amount, currency)],
					["Treatment", preview.treatment],
					["Reason", preview.treatment_reason],
					["VAT due now", money(preview.due_vat_amount, currency)],
				];

	return `<table class="table table-bordered" style="margin-top: 4px;">${rows
		.map(
			(row) =>
				`<tr><td class="text-muted" style="width: 45%;">${escape(row[0])}</td>` +
				`<td><b>${escape(row[1])}</b></td></tr>`,
		)
		.join("")}</table>`;
}

function warnings_html(preview) {
	const warnings = preview.warnings || [];
	if (!warnings.length) return "";

	return (
		`<div class="text-muted small" style="margin-top: 8px;"><b>${escape(
			__("Notes of the decision"),
		)}</b><ul>` +
		warnings.map((warning) => `<li>${escape(warning)}</li>`).join("") +
		"</ul></div>"
	);
}

function money(value, currency) {
	if (value === null || value === undefined || value === "") return "";

	const amount = Number(value);
	if (!isFinite(amount)) return "";

	return currency ? format_currency(amount, currency) : String(amount);
}

function escape(value) {
	if (value === null || value === undefined) return "";
	return frappe.utils.escape_html(String(value));
}
