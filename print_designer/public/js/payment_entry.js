frappe.ui.form.on("Payment Entry", {
    setup(frm) {
        frm.set_query("tax_withholding_category", () => ({
            query: "print_designer.controllers.queries.twc_search"
        }));
    },

    tax_withholding_category(frm) {
        // Auto-populate tax_withholding_group from Thai WHT Income Type
        if (frm.doc.tax_withholding_category) {
            frappe.call({
                method: "print_designer.custom.payment_tax_withholding.get_tax_withholding_group",
                args: {
                    tax_withholding_category: frm.doc.tax_withholding_category
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("tax_withholding_group", r.message);
                    }
                }
            });
        }
    }
});
