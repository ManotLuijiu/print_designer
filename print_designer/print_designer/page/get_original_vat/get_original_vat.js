// Copyright (c) 2026, AWS Solution Ltd. and contributors
// For license information, please see license.txt

frappe.pages["get-original-vat"].on_page_load = function (wrapper) {
    var $wrapper = $(wrapper);
    load_and_render($wrapper);
};

function load_and_render($wrapper) {
    $wrapper.html('<div class="text-muted text-center p-5"><i class="fa fa-spinner fa-spin fa-2x"></i></div>');
    frappe.call({
        method: "print_designer.print_designer.page.get_original_vat.get_original_vat.get_all_vat_transactions",
        callback: function (r) {
            if (r.message) render_page($wrapper, r.message);
        },
        error: function () {
            $wrapper.html('<div class="p-4">' + __("Failed to load data") + "</div>");
        },
    });
}

function render_page($wrapper, data) {
    var html = '<div class="desk-page p-4">';
    html += '<style>';
    html += '.desk-page .card { background-color: var(--bg-color); border-color: var(--border-color); }';
    html += '.desk-page .card-header { background-color: var(--bg-color); border-bottom-color: var(--border-color); }';
    html += '.desk-page .card-body { background-color: var(--bg-color); }';
    html += '.desk-page .table { color: var(--text-color); }';
    html += '.desk-page th { background-color: var(--bg-color); }';
    html += '.desk-page .text-muted { color: var(--text-muted) !important; }';
    html += '.desk-page .toggle-reconciled, .desk-page .toggle-vat-used { cursor: pointer; }';
    html += '</style>';

    // Summary row
    html += '<div class="row mb-4">';
    html += summary_card(__("Total Records"), data.total || 0);
    html += summary_card(__("PI Draft"), data.pending_pi_draft || 0);
    html += summary_card(__("Pending Reconcile"), data.pending_pi_reconcile || 0);
    html += summary_card(__("Pending VAT Declaration"), data.pending_pi_use || 0);
    html += "</div>";

    // Table
    html += '<div class="card">';
    html += '<div class="card-header d-flex justify-content-between align-items-center">';
    html += '<h5 class="mb-0">' + __("VAT Transactions") + "</h5>";
    html += '<div>';
    html += '<button class="btn btn-sm btn-secondary mr-1" id="bulk-reconciled">' + __("Mark Reconciled") + "</button>";
    html += '<button class="btn btn-sm btn-secondary" id="bulk-vat-used">' + __("Mark VAT Used") + "</button>";
    html += "</div></div>";
    html += '<div class="card-body p-0"><div class="table-responsive">';
    html += '<table class="table table-hover"><thead><tr>';
    html += '<th style="width:40px;"><input type="checkbox" id="select-all"></th>';
    html += "<th>" + __("PI Name") + "</th>";
    html += "<th>" + __("Posting Date") + "</th>";
    html += "<th>" + __("Vendor / Party") + "</th>";
    html += "<th>" + __("Description") + "</th>";
    html += "<th>" + __("VAT Type") + "</th>";
    html += '<th class="text-right">' + __("Base Amount") + "</th>";
    html += '<th class="text-right">' + __("VAT Amount") + "</th>";
    html += '<th class="text-center">' + __("Reconciled") + "</th>";
    html += '<th class="text-center">' + __("Used") + "</th>";
    html += '<th class="text-center">' + __("Actions") + "</th>";
    html += "</tr></thead><tbody>";

    if (data.transactions && data.transactions.length > 0) {
        data.transactions.forEach(function (r) {
            var is_iuv = r.doctype === "Input VAT Undue";
            var is_draft = r.pi_docstatus === 0;
            var is_reconciled = r.has_original === 1;
            var is_used = r.is_input_vat_used === 1;

            // Format numbers
            var fmt_base = r.base_amount
                ? parseFloat(r.base_amount).toLocaleString("en-US", {minimumFractionDigits: 2})
                : "0.00";
            var fmt_vat = r.vat_amount
                ? parseFloat(r.vat_amount).toLocaleString("en-US", {minimumFractionDigits: 2})
                : "0.00";
            var posting_date = r.pi_posting_date ? frappe.format(r.pi_posting_date, "Date") : "-";

            // App link
            var app = is_iuv ? "input-vat-undue" : "purchase-invoice";
            var pi_link = '<a href="/app/' + app + '/' + r.pi_name + '" target="_blank">' + r.pi_name + '</a>';

            // VAT type badge
            var vat_badge_class = "badge-secondary";
            if (r.vat_type === "Customs VAT") vat_badge_class = "badge-primary";
            else if (r.vat_type === "Inclusive VAT") vat_badge_class = "badge-warning";
            else if (r.vat_type === "Exclusive VAT") vat_badge_class = "badge-info";
            var vat_type_badge = '<span class="badge ' + vat_badge_class + '">' + (r.vat_type || "-") + "</span>";

            html += "<tr data-name='" + r.name + "' data-pi='" + r.pi_name + "'>";
            html += '<td><input type="checkbox" class="record-checkbox" data-pi="' + r.pi_name + '"></td>';
            html += "<td>" + pi_link + "</td>";
            html += "<td>" + posting_date + "</td>";
            html += "<td>" + (r.vendor || "-") + "</td>";
            html += "<td>" + (r.description || "-") + "</td>";
            html += "<td>" + vat_type_badge + "</td>";
            html += '<td class="text-right">' + fmt_base + "</td>";
            html += '<td class="text-right"><strong>' + fmt_vat + "</strong></td>";

            // Reconciled toggle
            if (is_reconciled) {
                html += '<td class="text-center"><i class="fa fa-check text-success toggle-reconciled" data-pi="' + r.pi_name + '" title="' + __("Reconciled — click to undo") + '"></i></td>';
            } else {
                html += '<td class="text-center"><input type="checkbox" class="toggle-reconciled" data-pi="' + r.pi_name + '"></td>';
            }

            // Used toggle — same pattern as Reconciled: always a toggle
            if (is_used) {
                html += '<td class="text-center"><i class="fa fa-check text-success toggle-vat-used" data-pi="' + r.pi_name + '" title="' + __("Used — click to undo") + '"></i></td>';
            } else {
                html += '<td class="text-center"><input type="checkbox" class="toggle-vat-used" data-pi="' + r.pi_name + '"></td>';
            }

            // Actions — always 3 icons: eye, pencil, trash
            html += '<td class="text-center">';
            html += '<a href="/app/' + app + '/' + r.pi_name + '" target="_blank" class="btn btn-xs btn-secondary" title="' + __("View") + '"><i class="fa fa-eye"></i></a> ';
            html += '<a href="/app/' + app + '/' + r.pi_name + '?order=Edit" target="_blank" class="btn btn-xs btn-secondary" title="' + __("Edit") + '"><i class="fa fa-pencil"></i></a> ';
            html += '<button class="btn btn-xs btn-secondary btn-delete" data-pi="' + r.pi_name + '" title="' + __("Delete") + '"><i class="fa fa-trash"></i></button>';
            html += "</td></tr>";
        });
    } else {
        html += '<tr><td colspan="11" class="text-center text-muted p-4">' + __("No records found") + "</td></tr>";
    }

    html += "</tbody></table></div></div></div></div>";
    $wrapper.html(html);

    // --- Event bindings ---

    // Select all
    $wrapper.find("#select-all").on("change", function () {
        $wrapper.find(".record-checkbox").prop("checked", $(this).prop("checked"));
    });

    // Reconciled toggle (checkbox or undo icon)
    $wrapper.find(".toggle-reconciled").on("change", function () {
        var pi = $(this).data("pi");
        toggle_reconciled($wrapper, [pi]);
    });
    $wrapper.find(".toggle-reconciled.fa-check").on("click", function () {
        var pi = $(this).data("pi");
        toggle_reconciled($wrapper, [pi], true); // true = undo
    });

    // Used toggle (checkbox or undo icon)
    $wrapper.find(".toggle-vat-used").on("change", function () {
        var pi = $(this).data("pi");
        toggle_vat_used($wrapper, [pi]);
    });
    $wrapper.find(".toggle-vat-used.fa-check").on("click", function () {
        var pi = $(this).data("pi");
        toggle_vat_used($wrapper, [pi], true); // true = undo
    });

    // Delete
    $wrapper.find(".btn-delete").on("click", function () {
        var pi = $(this).data("pi");
        frappe.confirm(__("Delete customs entry for PI {0}?", [pi]), function () {
            delete_transaction($wrapper, pi);
        });
    });

    // Bulk Mark Reconciled
    $wrapper.find("#bulk-reconciled").on("click", function () {
        var names = [];
        $wrapper.find(".record-checkbox:checked").each(function () {
            names.push($(this).data("pi"));
        });
        if (!names.length) { frappe.msgprint(__("Select records first")); return; }
        toggle_reconciled($wrapper, names);
    });

    // Bulk Mark VAT Used
    $wrapper.find("#bulk-vat-used").on("click", function () {
        var names = [];
        $wrapper.find(".record-checkbox:checked").each(function () {
            names.push($(this).data("pi"));
        });
        if (!names.length) { frappe.msgprint(__("Select records first")); return; }
        toggle_vat_used($wrapper, names);
    });
}

function summary_card(label, value) {
    return '<div class="col-md-3"><div class="card"><div class="card-body">' +
        '<div class="text-muted small mb-1">' + label + "</div>" +
        '<div class="text-large font-weight-bold">' + value + "</div>" +
        "</div></div></div>";
}

function toggle_reconciled($wrapper, names, undo) {
    if (undo) {
        // For now just reload — undo would need backend support
        frappe.msgprint(__("Undo not yet implemented"));
        return;
    }
    frappe.call({
        method: "print_designer.print_designer.page.get_original_vat.get_original_vat.toggle_reconciled",
        args: { names: names },
        callback: function (r) {
            if (r.message) {
                var ok = r.message.filter(function (x) { return x.success; }).length;
                frappe.msgprint({ title: __("Done"), message: __("{0} of {1} marked as reconciled", [ok, names.length]) });
            }
            load_and_render($wrapper);
        },
    });
}

function toggle_vat_used($wrapper, names, undo) {
    if (undo) {
        frappe.msgprint(__("Undo not yet implemented"));
        return;
    }
    frappe.call({
        method: "print_designer.print_designer.page.get_original_vat.get_original_vat.toggle_vat_used",
        args: { names: names },
        callback: function (r) {
            if (r.message) {
                var ok = r.message.filter(function (x) { return x.success; }).length;
                frappe.msgprint({ title: __("Done"), message: __("{0} of {1} marked as used", [ok, names.length]) });
            }
            load_and_render($wrapper);
        },
    });
}

function delete_transaction($wrapper, pi_name) {
    frappe.call({
        method: "print_designer.print_designer.page.get_original_vat.get_original_vat.delete_transaction",
        args: { doctype: "Input VAT Undue", name: pi_name },
        callback: function (r) {
            if (r.message && r.message.success) {
                frappe.msgprint({ title: __("Deleted"), message: pi_name + " " + __("deleted") });
                load_and_render($wrapper);
            } else {
                frappe.msgprint({ title: __("Error"), message: r.message && r.message.error || __("Cannot delete this record type") });
            }
        },
    });
}
