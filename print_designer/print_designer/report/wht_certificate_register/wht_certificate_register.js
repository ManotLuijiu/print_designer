// File: print_designer/print_designer/report/wht_certificate_register/wht_certificate_register.js

frappe.query_reports["WHT Certificate Register"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
			width: "80px",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
			width: "80px",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "100px",
		},
		{
			fieldname: "party",
			label: __("Party"),
			fieldtype: "Link",
			options: "Supplier",
			width: "100px",
		},
		{
			fieldname: "income_type",
			label: __("Income Type"),
			fieldtype: "Select",
			options: [
				"",
				"1 - เงินเดือน ค่าจ้าง",
				"2 - ค่าธรรมเนียม ค่านายหน้า",
				"3 - ค่าลิขสิทธิ์ ค่าบริการทางเทคนิค",
				"4.1 - ดอกเบี้ย",
				"4.2 - เงินปันผล กำไรสุทธิ",
				"5 - ค่าเช่าทรัพย์สิน",
				"6 - อื่น ๆ",
			],
			width: "100px",
		},
		{
			fieldname: "submission_status",
			label: __("Submission Status"),
			fieldtype: "Select",
			options: ["", "Submitted", "Pending", "Draft"],
			width: "100px",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		// Format currency values
		if (["amount_paid", "tax_withheld"].includes(column.fieldname)) {
			if (value) {
				return `<div style="text-align: right;">${format_currency(value)}</div>`;
			}
		}

		// Format tax rate
		if (column.fieldname === "tax_rate" && value) {
			return `<div style="text-align: center;">${value}%</div>`;
		}

		// Format status with indicators
		if (column.fieldname === "status") {
			let color = get_status_color(value);
			return `<span class="indicator ${color}">${value}</span>`;
		}

		// Format Payment Entry as clickable link
		if (column.fieldname === "name") {
			return `<a href="/app/payment-entry/${value}" target="_blank">${value}</a>`;
		}

		return default_formatter(value, row, column, data);
	},

	onload: function (report) {
		// Add custom buttons
		report.page.add_inner_button(__("Export to Excel"), function () {
			export_to_excel(report);
		});

		report.page.add_inner_button(__("Generate Certificates"), function () {
			generate_batch_certificates(report);
		});

		report.page.add_inner_button(__("ภ.ง.ด.1ก Summary"), function () {
			show_pnd_summary(report);
		});

		// Add refresh button with custom styling
		report.page.add_inner_button(
			__("Refresh"),
			function () {
				report.refresh();
			},
			__("Actions"),
		);
	},

	get_datatable_options: function (options) {
		// Customize datatable appearance
		return Object.assign(options, {
			checkboxColumn: true,
			events: {
				onCheckRow: function (data) {
					// Handle row selection for batch operations
					console.log("Selected rows:", data);
				},
			},
		});
	},
};

// Helper functions
function get_status_color(status) {
	const colors = {
		Submitted: "green",
		Pending: "orange",
		Draft: "red",
	};
	return colors[status] || "gray";
}

function format_currency(value) {
	if (!value) return "0.00";
	return new Intl.NumberFormat("th-TH", {
		style: "currency",
		currency: "THB",
		minimumFractionDigits: 2,
	}).format(value);
}

function export_to_excel(report) {
	// Export report data to Excel
	const data = report.data;
	if (!data || data.length === 0) {
		frappe.msgprint(__("No data to export"));
		return;
	}

	frappe.call({
		method: "print_designer.custom.reports.export_wht_register_excel",
		args: {
			data: data,
			filters: report.get_filter_values(),
		},
		callback: function (r) {
			if (r.message) {
				window.open(r.message);
			}
		},
	});
}

function generate_batch_certificates(report) {
	// Generate certificates for selected entries
	const selected_rows = report.datatable.getCheckedRows();

	if (selected_rows.length === 0) {
		frappe.msgprint(__("Please select rows to generate certificates"));
		return;
	}

	frappe.confirm(
		__("Generate WHT certificates for {0} selected entries?", [
			selected_rows.length,
		]),
		function () {
			frappe.call({
				method:
					"print_designer.custom.batch_wht_certificates.generate_batch_certificates",
				args: {
					payment_entries: selected_rows.map((row) => row[1]), // Payment Entry names
				},
				callback: function (r) {
					if (r.message) {
						frappe.msgprint(
							__("Generated {0} certificates successfully", [r.message.length]),
						);
						report.refresh();
					}
				},
			});
		},
	);
}

function show_pnd_summary(report) {
	// Show ภ.ง.ด.1ก summary dialog
	const filters = report.get_filter_values();

	frappe.call({
		method: "print_designer.custom.withholding_tax.create_wht_summary_report",
		args: {
			from_date: filters.from_date,
			to_date: filters.to_date,
			company: filters.company,
		},
		callback: function (r) {
			if (r.message) {
				show_summary_dialog(r.message);
			}
		},
	});
}

function show_summary_dialog(summary_data) {
	// Display summary in a dialog
	const dialog = new frappe.ui.Dialog({
		title: __("ภ.ง.ด.1ก Summary Report"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "summary_html",
				options: generate_summary_html(summary_data),
			},
		],
	});

	dialog.show();
}

function generate_summary_html(data) {
	return `
        <div class="row">
            <div class="col-md-6">
                <h5>Summary Statistics</h5>
                <table class="table table-bordered">
                    <tr><td>Total Certificates:</td><td>${data.count}</td></tr>
                    <tr><td>Total Amount Paid:</td><td>${format_currency(data.total_paid)}</td></tr>
                    <tr><td>Total Tax Withheld:</td><td>${format_currency(data.total_tax)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h5>By Income Type</h5>
                <div id="income-type-chart"></div>
            </div>
        </div>
    `;
}
