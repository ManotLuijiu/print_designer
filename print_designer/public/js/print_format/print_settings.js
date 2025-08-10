// Print Settings client script for Print Designer app
/** biome-ignore-all lint/correctness/noInnerDeclarations: <explanation> */
/** biome-ignore-all lint/complexity/useArrowFunction: <explanation> */
// Handles signature statistics display

frappe.ui.form.on("Print Settings", {
	refresh: function (frm) {
		console.log("Print Settings refresh", frm);
		setTimeout(function () {
			frappe.call({
				method: "frappe.client.get_count",
				args: {
					doctype: "Signature Basic Information",
				},
				callback: function (r) {
					if (r.message !== undefined) {
						var el = document.getElementById("total-signatures");
						if (el) el.textContent = r.message;
					}
				},
			});

			frappe.call({
				method: "frappe.client.get_count",
				args: {
					doctype: "Signature Basic Information",
					filters: { signature_category: "Company Stamp" },
				},
				callback: function (r) {
					if (r.message !== undefined) {
						var el = document.getElementById("company-stamps");
						if (el) el.textContent = r.message;
					}
				},
			});

			frappe.call({
				method: "frappe.client.get_count",
				args: {
					doctype: "Signature Basic Information",
					filters: { is_active: 1 },
				},
				callback: function (r) {
					if (r.message !== undefined) {
						var el = document.getElementById("active-signatures");
						if (el) el.textContent = r.message;
					}
				},
			});
		}, 1000);
	},
});
