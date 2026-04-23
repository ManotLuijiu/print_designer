// Override get_current_tax_amount to add Gross-up support.
// ERPNext's payment_entry.js handles Actual / On Paid Amount / On Previous Row Amount /
// On Previous Row Total but has no Gross-up branch, so it returns 0 for that type.
// Gross-up formula: WHT = (paid_amount / (1 - rate/100)) × (rate/100)
// i.e. gross = net / (1 - rate), withholding = gross × rate.
frappe.ui.form.on("Payment Entry", {
    get_current_tax_amount: function(frm, tax) {
        if (tax.charge_type !== "Gross-up") return;

        const tax_rate = flt(tax.rate);
        if (tax_rate <= 0) {
            // Rate is 0 on auto-generated Gross-up rows; keep the server-computed value.
            return flt(tax.tax_amount, precision("tax_amount", tax));
        }

        const paid = flt(frm.doc.paid_amount_after_tax);
        const gross = paid / (1 - tax_rate / 100.0);
        return flt(gross * (tax_rate / 100.0), precision("tax_amount", tax));
    }
});

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
