// Copyright (c) 2026, MooCoding and contributors
// For license information, please see license.txt

// The steps of the intake of a tax invoice.
//
// Every step of the workflow is a POST, because a GET may be triggered by a
// link or by a crawler, and none of those may change the books of a
// company.  The buttons of the form therefore call the server methods of the
// document and never write the fields of the form from the browser.
//
// The methods are called on the document itself, so the form follows the
// controller that owns the DocType, whether that is Print Designer or the
// compatibility shim of Thai Business Suite.

frappe.ui.form.on("Thai Tax Invoice Intake", {
	verify_invoice(frm) {
		call_the_step(frm, "set_verification_status", { status: "Verified" });
	},

	reject_invoice(frm) {
		call_the_step(frm, "set_verification_status", { status: "Rejected" });
	},

	create_purchase_invoice(frm) {
		call_the_step(frm, "sync_to_purchase_invoice");
	},

	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		const is_synchronized = Boolean(frm.doc.purchase_invoice);
		const is_verified = frm.doc.verification_status === "Verified";

		// The purchase invoice is only offered when the invoice of the
		// intake is verified and no purchase invoice was created yet.
		frm.set_df_property(
			"create_purchase_invoice",
			"hidden",
			!(is_verified && !is_synchronized),
		);

		frm.set_df_property(
			"verify_invoice",
			"hidden",
			is_synchronized || is_verified,
		);

		frm.set_df_property(
			"reject_invoice",
			"hidden",
			is_synchronized || frm.doc.verification_status === "Rejected",
		);
	},
});

// Call a step of the workflow of the intake.
//
// The call goes to the server, which asks for the right to write the
// intake before it changes a state.  The form is reloaded afterwards, so
// the states of the form and of the database are the same.
function call_the_step(frm, method, args = {}) {
	return frm.call({
		method: method,
		args: args,
		doc: frm.doc,
		type: "POST",
		freeze: true,
		freeze_message: __("Working..."),
		callback: () => {
			frm.reload_doc();
		},
	});
}
