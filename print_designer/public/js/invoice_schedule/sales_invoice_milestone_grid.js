// Keep the milestone share visible even when an older saved Items layout
// predates this field. This wraps only this Sales Invoice's Items grid.
console.log("[PD Milestone Grid] registering Items layout");
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		const grid = frm.fields_dict.items?.grid;
		const portion = "pd_custom_invoice_portion";
		console.log("[PD Milestone Grid] refresh", { grid: !!grid, fields: grid?.docfields?.length });
		if (!grid?.docfields?.some((df) => df.fieldname === portion)) return;
		if (grid.pd_milestone_columns) return;

		const original = grid.setup_user_defined_columns;
		grid.setup_user_defined_columns = function () {
			original.call(this);
			const saved = this.user_defined_columns || [];
			const defaults = [
				["item_code", 4], ["qty", 1], ["rate", 2], ["amount", 2],
			];
			let columns = saved.length
				? saved.map((df) => ({ ...df }))
				: defaults.map(([fieldname, width]) => {
					const df = this.docfields.find((field) => field.fieldname === fieldname);
					return df && { ...df, in_list_view: 1, columns: width };
				}).filter(Boolean);
			const rate = columns.findIndex((df) => df.fieldname === "rate");
			if (rate < 0) return; // A deliberate layout without Rate stays intact.

			const existing = columns.find((df) => df.fieldname === portion);
			const definition = this.docfields.find((df) => df.fieldname === portion);
			columns = columns.filter((df) => df.fieldname !== portion);
			columns.splice(columns.findIndex((df) => df.fieldname === "rate") + 1, 0, {
				...(existing || definition), in_list_view: 1, columns: 1,
			});

			// Reserve one grid unit for the row number. Reduce wide columns only
			// as needed; do not discard saved columns or persist over preferences.
			for (const df of columns) df.columns = Number(df.columns) || 2;
			let overflow = columns.reduce((sum, df) => sum + df.columns, 0) - 10;
			while (overflow > 0) {
				const widest = columns.reduce((best, df) => df.columns > best.columns ? df : best);
				if (widest.columns <= 1) break;
				widest.columns -= 1;
				overflow -= 1;
			}
			this.user_defined_columns = columns;
		};
		grid.pd_milestone_columns = true;
		grid.reset_grid();
	},
});
