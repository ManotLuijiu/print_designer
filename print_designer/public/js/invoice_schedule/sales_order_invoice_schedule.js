// Milestone billing (Invoice Schedule) for Sales Order
//
// The Sales Order stays the contractual commitment. The Invoice Schedule is
// the billing plan: it can be seeded from the Payment Schedule, but rows can
// also be added by hand so the order can be split into more invoices than the
// Payment Schedule has rows.
//
// The two milestone buttons live in the toolbar of the child table, next to
// the grid's own "Add row" button, so the milestones and the actions that
// change them stay in one row.

const CHILD_DOCTYPE = "Invoice Schedule";
const CHILD_FIELD = "pd_custom_invoice_schedule";
const ADD_MILESTONE_FIELD = "pd_custom_add_invoice_schedule_row";
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
		sync_milestone_buttons(frm);

		if (!frm.doc.pd_custom_enable_invoice_schedule) {
			return;
		}

		frm.add_custom_button(
			__("Create Milestone Invoices"),
			function () {
				create_milestone_invoices(frm);
			},
			__("Milestones")
		);
	},

	// the buttons are rendered in the toolbar of the child table, these
	// handlers keep them working when they are shown as form fields
	pd_custom_add_invoice_schedule_row: function (frm) {
		on_add_milestone(frm);
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

	add_milestone_button($buttons, frm, ADD_MILESTONE_FIELD, on_add_milestone);
	add_milestone_button($buttons, frm, COPY_PAYMENT_SCHEDULE_FIELD, on_copy_payment_schedule);
}

function add_milestone_button($buttons, frm, fieldname, handler) {
	var df = frm.meta.get_field(fieldname) || {};

	var $button = $(
		'<button type="button" class="btn btn-xs btn-secondary milestone-button"></button>'
	)
		.text(df.label || fieldname)
		.on("click", function () {
			handler(frm);
		});

	$buttons.append($button);
	attach_help_to_button($button, df.description);
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
			"cursor-pointer milestone-help-trigger"
		)
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

	milestone_help.push({ card: card, container: $button.parent(), $card: $card });
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
				message: __("Save the Sales Order before the milestones can be changed."),
				indicator: "orange",
			});
		}
	);
}

function on_add_milestone(frm) {
	if (frm.is_new()) {
		frappe.msgprint({
			title: __("Save first"),
			message: __("Save the Sales Order before adding a milestone."),
			indicator: "orange",
		});
		return;
	}

	if (frm.doc.docstatus !== 0) {
		frappe.msgprint({
			title: __("Not a draft"),
			message: __("Amend the Sales Order to change the milestones of a submitted order."),
			indicator: "orange",
		});
		return;
	}

	save_then_run(frm, function () {
		frappe.call({
			method: "print_designer.custom.invoice_schedule.add_invoice_schedule_row",
			args: { sales_order: frm.doc.name },
			freeze: true,
			freeze_message: __("Adding milestone..."),
			callback: function (r) {
				var result = r.message || {};
				if (result.payment_term) {
					frappe.msgprint({
						title: __("Milestone added"),
						message: __("{0} added. Set its portion and invoice date.", [
							result.payment_term,
						]),
						indicator: "green",
					});
				}
				frm.reload_doc();
			},
		});
	});
}

function on_copy_payment_schedule(frm) {
	if (frm.is_new()) {
		frappe.msgprint({
			title: __("Save first"),
			message: __("Save the Sales Order before copying the Payment Schedule."),
			indicator: "orange",
		});
		return;
	}

	if (frm.doc.docstatus !== 0) {
		frappe.msgprint({
			title: __("Not a draft"),
			message: __("Amend the Sales Order to change the milestones of a submitted order."),
			indicator: "orange",
		});
		return;
	}

	save_then_run(frm, function () {
		copy_payment_schedule(frm);
	});
}

function get_row(frm, cdn) {
	var rows = frm.doc[CHILD_FIELD] || [];
	return rows.find(function (row) {
		return row.name === cdn;
	});
}

function copy_payment_schedule(frm) {
	if (!frm.doc.payment_schedule || !frm.doc.payment_schedule.length) {
		frappe.msgprint({
			title: __("Nothing to copy"),
			message: __("This Sales Order has no Payment Schedule rows."),
			indicator: "orange",
		});
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

			if (added) {
				frappe.msgprint({
					title: __("Payment Schedule copied"),
					message: __("{0} milestones added, {1} already in the plan.", [
						added,
						result.skipped || 0,
					]),
					indicator: "green",
				});
			} else {
				frappe.msgprint({
					title: __("Nothing to copy"),
					message: __("The Payment Schedule is already in the plan."),
					indicator: "orange",
				});
			}
			frm.reload_doc();
		},
	});
}

function create_milestone_invoices(frm) {
	var pending = (frm.doc[CHILD_FIELD] || []).filter(function (row) {
		return row.milestone_status === "Not Invoiced";
	});

	if (!pending.length) {
		frappe.msgprint({
			title: __("Nothing to create"),
			message: __("Every milestone of this Sales Order has already been invoiced."),
			indicator: "orange",
		});
		return;
	}

	var without_date = pending.filter(function (row) {
		return !row.invoice_date;
	});

	if (without_date.length) {
		frappe.msgprint({
			title: __("Invoice date missing"),
			message: __("Set an Invoice Date on every milestone that should be invoiced."),
			indicator: "orange",
		});
		return;
	}

	var summary = pending
		.map(function (row) {
			return row.payment_term + " (" + row.invoice_portion + "%)";
		})
		.join(", ");

	frappe.confirm(
		__("Create draft Sales Invoices for these milestones: {0}?", [summary]),
		function () {
			frappe.call({
				method: "print_designer.custom.invoice_schedule.create_milestone_invoices",
				args: { sales_order: frm.doc.name },
				freeze: true,
				freeze_message: __("Creating milestone Sales Invoices..."),
				callback: function (r) {
					var result = r.message || {};
					var created = result.created || [];

					if (created.length) {
						frappe.msgprint({
							title: __("Milestone Sales Invoices created"),
							message: created
								.map(function (c) {
									return c.sales_invoice + " - " + c.milestone;
								})
								.join("<br>"),
							indicator: "green",
						});
					}

					frm.reload_doc();
				},
			});
		}
	);
}
