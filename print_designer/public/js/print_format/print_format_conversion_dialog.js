// Separate file for conversion dialog to avoid conflicts

function show_print_format_conversion_dialog() {
	const dialog = new frappe.ui.Dialog({
		title: __("Convert Print Format to Designer Export"),
		fields: [
			{
				fieldname: "source_file",
				fieldtype: "Data",
				label: __("Source File Path"),
				reqd: 1,
				description: __("Absolute path to .txt or .json Print Format file"),
			},
			{
				fieldname: "target_file",
				fieldtype: "Data",
				label: __("Target File Path"),
				reqd: 1,
				description: __("Absolute path where converted JSON will be saved"),
			},
			{
				fieldname: "help_section",
				fieldtype: "Section Break",
			},
			{
				fieldname: "help_html",
				fieldtype: "HTML",
				options: `
					<div style="padding: 10px; border-radius: 4px; font-size: 13px;">
						<p style="margin-bottom: 8px;"><strong>How it works:</strong></p>
						<ul style="margin: 0; padding-left: 20px;">
							<li>Source file must be a Print Format DocType JSON (.txt or .json)</li>
							<li>Target file will be created/overwritten with Designer Export format</li>
							<li>Converted file can be imported into Print Designer</li>
						</ul>
					</div>
				`,
			},
		],
		primary_action_label: __("Convert"),
		primary_action: function (values) {
			// Call conversion API
			frappe.call({
				method:
					"print_designer.api.print_format_export_import.convert_file_to_designer_export",
				args: {
					source_file: values.source_file,
					target_file: values.target_file,
				},
				freeze: true,
				freeze_message: __("Converting print format..."),
				callback: function (r) {
					if (r.message && r.message.success) {
						dialog.hide();

						frappe.msgprint({
							title: __("Conversion Successful"),
							message: `
								<div style="font-size: 14px;">
									<p><strong>✅ Conversion completed successfully!</strong></p>
									<hr>
									<p><strong>Print Format:</strong> ${r.message.name}</p>
									<p><strong>DocType:</strong> ${r.message.doc_type}</p>
									<p><strong>Output File:</strong><br><code>${r.message.output_file}</code></p>
									<hr>
									<p>You can now import this file into Print Designer</p>
								</div>
							`,
							indicator: "green",
							wide: true,
						});
					}
				},
				error: function (r) {
					frappe.msgprint({
						title: __("Conversion Failed"),
						message:
							__(
								"Failed to convert print format. Please check the file paths and try again.<br><br>Error: ",
							) + (r.message || "Unknown error"),
						indicator: "red",
					});
				},
			});
		},
	});

	dialog.show();
}

// Export function for use in print_format.js
window.show_print_format_conversion_dialog =
	show_print_format_conversion_dialog;
