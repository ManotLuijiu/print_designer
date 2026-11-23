// Copyright (c) 2024, AWS Solution Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		const field = frm.fields_dict.pd_custom_wht_certificate;
		const wrapper = field?.$wrapper?.[0];
		wrapper?.querySelector(".pd-enter-received-wht")?.remove();
		if (
			frm.doc.payment_type !== "Receive" ||
			frm.doc.party_type !== "Customer" ||
			frm.is_new() ||
			frm.doc.docstatus === 2
		) {
			return;
		}

		const register =
			frm.doc.pd_custom_wht_certificate_doctype === "Receive WHT Register"
				? frm.doc.pd_custom_wht_certificate
				: null;
		if (register) {
			frm.add_custom_button(
				__("View WHT Register"),
				() => {
					frappe.set_route("Form", "Receive WHT Register", register);
				},
				__("Actions"),
			);
		} else if (field && frappe.model.can_create("Receive WHT Register")) {
			const enterCertificate = () =>
				prompt_for_received_wht_certificate(frm);
			if (wrapper) {
				const button = document.createElement("button");
				button.type = "button";
				button.className =
					"btn btn-default btn-xs mt-1 pd-enter-received-wht";
				button.textContent = __("Enter WHT Certificate");
				button.addEventListener("click", enterCertificate);
				wrapper.append(button);
			}
		}
	},
});

function prompt_for_received_wht_certificate(frm) {
	if (frm.is_dirty()) {
		frappe.msgprint(
			__("Save the Payment Entry before creating a WHT Register."),
		);
		return;
	}
	frappe.prompt(
		[
			{
				fieldname: "certificate_no",
				fieldtype: "Data",
				label: __("WHT Certificate Number"),
				reqd: 1,
			},
			{
				fieldname: "certificate_date",
				fieldtype: "Date",
				label: __("WHT Certificate Date"),
				reqd: 1,
			},
		],
		async (values) => {
			const response = await frappe.call({
				method: "print_designer.print_designer.doctype.receive_wht_register.receive_wht_register.create_from_payment_entry",
				args: { payment_entry: frm.doc.name, ...values },
				freeze: true,
			});
			if (response.message?.name) {
				await frm.reload_doc();
				frappe.set_route(
					"Form",
					"Receive WHT Register",
					response.message.name,
				);
			}
		},
		__("Create WHT Register"),
		__("Create"),
	);
}
