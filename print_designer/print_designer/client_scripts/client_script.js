// Override for Client Script DocType to fix "Go to Print Settings" button
// This fixes the issue where single DocTypes like Print Settings get incorrect /view/list URLs

frappe.ui.form.on("Client Script", {
	refresh(frm) {
		// Remove the original "Go to DocType" button if it exists
		frm.remove_custom_button(__("Go to {0}", [frm.doc.dt]));

		// Add our fixed version
		if (frm.doc.dt && frm.doc.script) {
			frm.add_custom_button(__("Go to {0}", [frm.doc.dt]), () => {
				// Check if it's a single DocType (like Print Settings)
				if (frappe.boot.single_types?.includes(frm.doc.dt)) {
					frappe.set_route("Form", frm.doc.dt, frm.doc.dt);
				} else {
					frappe.set_route("List", frm.doc.dt, "List");
				}
			});
		}
	},
});
