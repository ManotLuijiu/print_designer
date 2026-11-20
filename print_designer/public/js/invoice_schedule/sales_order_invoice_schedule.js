// Milestone billing (Invoice Schedule) for Sales Order
//
// The Sales Order stays the contractual commitment. The Invoice Schedule is
// the billing plan: it can be seeded from the Payment Schedule, but rows can
// also be added by hand so the order can be split into more invoices than the
// Payment Schedule has rows.
//
// The milestone buttons live in the toolbar of the child table, next to the
// grid's own "Add row" button, so the milestones and the actions that
// change them stay in one row.
//
// "Generate Invoice" creates one draft Sales Invoice per milestone that does
// not have one yet. The workflow is: save the Sales Order, generate the
// invoices, submit the Sales Order, and submit the invoices afterwards.

const CHILD_DOCTYPE = "Invoice Schedule";
const CHILD_FIELD = "pd_custom_invoice_schedule";
const ENABLE_FIELD = "pd_custom_enable_invoice_schedule";
const GENERATE_INVOICE_FIELD = "pd_custom_add_invoice_schedule_row";
const COPY_PAYMENT_SCHEDULE_FIELD = "pd_custom_copy_payment_schedule";

// the open help cards of the milestone buttons, so they can be closed and
// cleaned up when the form is refreshed
var milestone_help = [];

$(document).on("click", function (e) {
	milestone_help.forEach(function (entry) {
		var path =
			e.originalEvent && e.originalEvent.composedPath
				? e.originalEvent.composedPath()
				: [];

		if (!path.includes(entry.container[0])) {
			entry.card.hide();
		}
	});
});

frappe.ui.form.on("Sales Order", {
	refresh: function (frm) {
		setup_milestone_payment_terms(frm);
		setup_invoice_schedule_help(frm);
		sync_milestone_buttons(frm);
		sync_milestone_navbar_button(frm);
	},

	// the buttons are rendered in the toolbar of the child table, these
	// handlers keep them working when they are shown as form fields
	pd_custom_add_invoice_schedule_row: function (frm) {
		on_generate_invoices(frm);
	},

	pd_custom_copy_payment_schedule: function (frm) {
		on_copy_payment_schedule(frm);
	},
});

// Keep the Portion and the Milestone Amount in step - either one can be
// edited, the other one follows.
frappe.ui.form.on(CHILD_DOCTYPE, {
	invoice_portion: function (frm, cdt, cdn) {
		var base = flt(frm.doc.net_total);
		if (!base) {
			return;
		}

		var row = get_row(frm, cdn);
		if (!row) {
			return;
		}

		var amount = flt((flt(row.invoice_portion) * base) / 100, 2);

		if (amount !== flt(row.invoice_amount, 2)) {
			frappe.model.set_value(cdt, cdn, "invoice_amount", amount);
		}
	},

	invoice_amount: function (frm, cdt, cdn) {
		var base = flt(frm.doc.net_total);
		if (!base) {
			return;
		}

		var row = get_row(frm, cdn);
		if (!row) {
			return;
		}

		var portion = flt((flt(row.invoice_amount) / base) * 100, 2);

		if (portion !== flt(row.invoice_portion, 2)) {
			frappe.model.set_value(cdt, cdn, "invoice_portion", portion);
		}
	},
});

// Legacy controller handlers run for child fields with the same name, even
// when their child DocType is different. Milestone names are free text and
// must never enter ERPNext's Payment Schedule payment-term lookup.
function setup_milestone_payment_terms(frm) {
	const original = frm.cscript?.payment_term;
	if (original && !original.pd_milestone_scoped) {
		const scoped = function (doc, cdt, cdn) {
			if (cdt === CHILD_DOCTYPE) {
				return;
			}
			return original.call(this, doc, cdt, cdn);
		};
		scoped.pd_milestone_scoped = true;
		frm.cscript.payment_term = scoped;
	}

	const grid = frm.fields_dict[CHILD_FIELD]?.grid;
	if (!grid?.get_field || !grid.update_docfield_property) {
		return;
	}
	const field = grid.docfields?.find((df) => df.fieldname === "payment_term");
	if (!field) {
		return;
	}
	// Use a permission-checked app lookup as suggestions. Unlike a
	// Link, Autocomplete can keep existing/custom milestone names as text.
	grid.get_field("payment_term").get_query = {
		query: "print_designer.custom.invoice_schedule.search_milestone_payment_terms",
	};
	if (field.fieldtype !== "Autocomplete") {
		grid.update_docfield_property("payment_term", "fieldtype", "Autocomplete");
	}
	if (!field.ignore_validation) {
		grid.update_docfield_property("payment_term", "ignore_validation", 1);
	}
}

function setup_invoice_schedule_help(frm) {
	const help = __(
		"Bill this Sales Order in milestones. Each milestone creates its own draft Sales Invoice. Seed the Invoice Schedule from the Payment Schedule, add your own rows, or split the plan into as many invoices as you need. Generate the draft invoices before submitting the Sales Order, then review and submit the invoices afterward.",
	);
	const enable = frm.fields_dict[ENABLE_FIELD];
	if (enable) {
		enable.df.description = help;
		enable.df.show_description_on_click = 1;
		if (!enable.$wrapper.find(".info-trigger").length) {
			enable.show_description_on_click();
		}
		// Native InfoCard keeps its initial text when the field label is unchanged.
		enable.$wrapper.find(".sidebar-card-description").text(help);
		enable.$wrapper.find(".help-box").empty().hide();
	}
	const schedule = frm.fields_dict[CHILD_FIELD];
	if (schedule?.grid) {
		schedule.df.description = "";
		schedule.grid.df.description = "";
		schedule.grid.set_grid_description();
	}
}

// The navbar action only makes sense while the order can still be worked on.
// A submitted or cancelled order has frozen milestones, so the action is not
// offered there - the grid buttons follow the same rule.
function sync_milestone_navbar_button(frm) {
	var label = __("Generate Invoice");
	var group = __("Milestones");

	if (frm.doc.docstatus !== 0 || !frm.doc.pd_custom_enable_invoice_schedule) {
		if (frm.custom_buttons && frm.custom_buttons[label]) {
			frm.remove_custom_button(label, group);
		}
		return;
	}

	frm.add_custom_button(
		label,
		function () {
			on_generate_invoices(frm);
		},
		group,
	);
}

// Put the two milestone buttons in the toolbar of the child table, right
// next to the grid's own "Add row" button.
function sync_milestone_buttons(frm) {
	reset_milestone_help();

	var field = frm.fields_dict[CHILD_FIELD];
	if (!field || !field.grid) {
		return;
	}

	var $buttons = field.grid.wrapper.find(".grid-footer .grid-buttons");
	if (!$buttons.length) {
		return;
	}

	$buttons.find(".milestone-button, .milestone-help-trigger").remove();

	// the milestones of a submitted order are frozen
	if (frm.doc.docstatus !== 0) {
		return;
	}

	add_milestone_button(
		$buttons,
		frm,
		GENERATE_INVOICE_FIELD,
		on_generate_invoices,
		__("Generate Invoice"),
		__(
			"Create draft Sales Invoices for the milestones, then submit the Sales Order before submitting the invoices.",
		),
	);
	add_milestone_button(
		$buttons,
		frm,
		COPY_PAYMENT_SCHEDULE_FIELD,
		on_copy_payment_schedule,
	);
}

function add_milestone_button(
	$buttons,
	frm,
	fieldname,
	handler,
	fallback_label,
	fallback_description,
) {
	var df = fieldname
		? frappe.meta.get_docfield(frm.doctype, fieldname) || {}
		: {};

	var $button = $(
		'<button type="button" class="btn btn-xs btn-secondary milestone-button"></button>',
	)
		// Explicit action text wins over metadata left over from older installs.
		.text(fallback_label || df.label || fieldname)
		.attr("data-milestone-action", fieldname)
		.on("click", function () {
			handler(frm);
		});

	$buttons.append($button);
	attach_help_to_button($button, fallback_description || df.description);
}

// Frappe empties the help box of a Button field and hides its label, so the
// "?" is placed next to the button itself. It opens the same card that
// Frappe uses for the fields that do support a description.
function attach_help_to_button($button, description) {
	if (!description) {
		return;
	}

	var $icon = $(
		frappe.utils.icon(
			"message-circle-question-mark",
			"sm",
			"",
			"margin-left: 4px; align-self: center;",
			"cursor-pointer milestone-help-trigger",
		),
	);
	$icon.attr("role", "button");
	$icon.insertAfter($button);

	var $card = $("<div class='info-card'></div>").appendTo($button.parent());

	var card = new frappe.ui.SidebarCard({
		message: description,
		parent: $card,
		trigger: $icon.get(0),
		close_button: true,
		popper: true,
		primary_button_width: "full",
	});

	$icon.on("click", function (event) {
		event.preventDefault();
		event.stopPropagation();
		card.toggle();
	});

	$card.on("click", function (event) {
		event.stopPropagation();
	});

	milestone_help.push({
		card: card,
		container: $button.parent(),
		$card: $card,
	});
}

function reset_milestone_help() {
	milestone_help.forEach(function (entry) {
		entry.card.hide();
		entry.$card.remove();
	});
	milestone_help = [];
}

// The server works on the saved Sales Order, so a change that is still in the
// form - a ticked "Enable Invoice Schedule", an edited Payment Schedule - has
// to be written first. Saving also lets the automatic copy from the Payment
// Schedule run.
function save_then_run(frm, run) {
	if (!frm.is_dirty()) {
		run();
		return;
	}

	frm.save(
		null,
		function (r) {
			if (r && r.exc) {
				// the server already reported the problem
				return;
			}
			run();
		},
		null,
		function () {
			frappe.msgprint({
				title: __("Could not save"),
				message: __(
					"Save the Sales Order before the milestones can be changed.",
				),
				indicator: "orange",
			});
		},
	);
}

function on_copy_payment_schedule(frm) {
	if (frm.is_new()) {
		frappe.msgprint({
			title: __("Save first"),
			message: __(
				"Save the Sales Order before copying the Payment Schedule.",
			),
			indicator: "orange",
		});
		return;
	}

	if (frm.doc.docstatus !== 0) {
		frappe.msgprint({
			title: __("Not a draft"),
			message: __(
				"Amend the Sales Order to change the milestones of a submitted order.",
			),
			indicator: "orange",
		});
		return;
	}

	// saving the order can already copy the plan, so the number of rows is
	// remembered to tell a real import from a no-op
	var rows_before = (frm.doc[CHILD_FIELD] || []).length;

	save_then_run(frm, function () {
		copy_payment_schedule(frm, rows_before);
	});
}

function get_row(frm, cdn) {
	var rows = frm.doc[CHILD_FIELD] || [];
	return rows.find(function (row) {
		return row.name === cdn;
	});
}

function copy_payment_schedule(frm, rows_before) {
	if (!frm.doc.payment_schedule || !frm.doc.payment_schedule.length) {
		frappe.show_alert(
			{ message: __("Nothing to import"), indicator: "orange" },
			5,
		);
		return;
	}

	frappe.call({
		method: "print_designer.custom.invoice_schedule.seed_invoice_schedule",
		args: { sales_order: frm.doc.name },
		freeze: true,
		freeze_message: __("Copying Payment Schedule..."),
		callback: function (r) {
			var result = r.message || {};
			var added = result.added || 0;
			var rows_after = (frm.doc[CHILD_FIELD] || []).length;

			if (added || rows_after > rows_before) {
				frappe.show_alert(
					{ message: __("Success Imported"), indicator: "green" },
					5,
				);
			} else if (result.skipped) {
				frappe.show_alert(
					{ message: __("Already imported"), indicator: "orange" },
					5,
				);
			} else {
				frappe.show_alert(
					{ message: __("Nothing to import"), indicator: "orange" },
					5,
				);
			}

			frm.reload_doc();
		},
	});
}

// "Generate Invoice" - the one handler behind the grid button, the form
// field and the navbar action.
function on_generate_invoices(frm) {
	if (frm.is_new()) {
		frappe.msgprint({
			title: __("Save first"),
			message: __("Save the Sales Order before generating invoices."),
			indicator: "orange",
		});
		return;
	}

	if (frm.doc.docstatus === 2) {
		frappe.msgprint({
			title: __("Not a draft"),
			message: __(
				"A cancelled Sales Order cannot have milestone invoices.",
			),
			indicator: "orange",
		});
		return;
	}

	save_then_run(frm, function () {
		generate_invoices(frm);
	});
}

// The plan comes from the server, so what is confirmed is what is created.
function generate_invoices(frm) {
	frappe.call({
		method: "print_designer.custom.invoice_schedule.generate_milestone_invoices",
		args: { sales_order: frm.doc.name, preview: 1 },
		freeze: true,
		freeze_message: __("Checking the milestones..."),
		callback: function (r) {
			var result = r.message || {};
			var plan = result.plan || [];

			if (!plan.length) {
				show_nothing_generated(result);
				return;
			}

			confirm_generation(frm, plan);
		},
	});
}

function confirm_generation(frm, plan) {
	var summary = plan
		.map(function (row) {
			return (
				frappe.utils.escape_html(row.milestone) +
				" (" +
				flt(row.invoice_portion) +
				"%, " +
				flt(row.invoice_amount) +
				", " +
				(row.invoice_date || __("no date")) +
				")"
			);
		})
		.join("<br>");

	frappe.confirm(
		__(
			"Create one draft Sales Invoice for each of these milestones?<br>{0}",
			[summary],
		),
		function () {
			create_generated_invoices(frm);
		},
	);
}

function create_generated_invoices(frm) {
	frappe.call({
		method: "print_designer.custom.invoice_schedule.generate_milestone_invoices",
		args: { sales_order: frm.doc.name },
		freeze: true,
		freeze_message: __("Generating the milestone invoices..."),
		callback: function (r) {
			var result = r.message || {};
			var created = result.created || [];

			if (created.length) {
				show_generated_invoices(created, result.skipped || []);
			} else {
				show_nothing_generated(result);
			}

			frm.reload_doc();
		},
	});
}

function show_generated_invoices(created, skipped) {
	var parts = created.map(function (c) {
		return (
			frappe.utils.get_form_link(
				"Sales Invoice",
				c.sales_invoice,
				true,
				frappe.utils.escape_html(c.sales_invoice),
			) +
			" - " +
			frappe.utils.escape_html(c.milestone)
		);
	});

	if (skipped.length) {
		parts.push("<b>" + __("Skipped") + "</b>");
		parts.push(
			skipped
				.map(function (s) {
					return (
						frappe.utils.escape_html(s.milestone) +
						" - " +
						frappe.utils.escape_html(s.reason)
					);
				})
				.join("<br>"),
		);
	}

	frappe.msgprint({
		title: __("Draft Sales Invoices created"),
		message: parts.join("<br>"),
		indicator: "green",
	});
}

function show_nothing_generated(result) {
	var skipped = result.skipped || [];
	var message;

	if (skipped.length) {
		message = skipped
			.map(function (s) {
				return (
					frappe.utils.escape_html(s.milestone) +
					" - " +
					frappe.utils.escape_html(s.reason)
				);
			})
			.join("<br>");
	} else {
		message = __(
			"Every milestone of this Sales Order already has an invoice.",
		);
	}

	frappe.msgprint({
		title: __("Nothing to generate"),
		message: message,
		indicator: "orange",
	});
}
