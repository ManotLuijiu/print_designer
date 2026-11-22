// Submitted invoices open the posted VAT registers. Drafts use Preview.
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		frm.remove_custom_button(__("Output VAT Report"), __("Tools"));
		const filters = {
			company: frm.doc.company,
			invoice_name: frm.doc.name,
		};
		const due = frappe.boot?.print_designer_output_vat_report;
		const undue = frappe.boot?.print_designer_output_vat_undue_report;
		if (due?.available && due.report) {
			frm.add_custom_button(
				__("Output VAT Report"),
				() => frappe.set_route("query-report", due.report, { ...filters }),
				__("View"),
			);
		}
		if (undue?.available && undue.report) {
			frm.add_custom_button(
				__("Output VAT Undue Report"),
				() => frappe.set_route("query-report", undue.report, { ...filters }),
				__("View"),
			);
		}
	},
});
