// Copyright (c) 2026, AWS Solution Ltd. and contributors
// For license information, please see license.txt

frappe.pages["get-original-vat"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Get Original VAT"),
        single_column: true,
    });

    wrapper.page = page;
    frappe.breadcrumbs.add("Print Designer", "Get Original VAT");

    // Load initial data
    frappe.call({
        method: "print_designer.page.get_original_vat.get_original_vat.get_pending_records",
        callback: function (r) {
            if (r.message) {
                render_page(page, r.message);
            }
        },
    });
};

function render_page(page, data) {
    page.set_title(__("Get Original VAT"));
    page.set_description(
        __("Mark original tax invoices as received — converts copy records to Thai Purchase VAT")
    );

    // Summary stats
    page.add_stat(__("Pending Records"), data.total_pending || 0);
    page.add_stat(__("Total Pending VAT"), data.total_pending_vat || "0.00 THB");
    page.add_stat(__("Converted"), data.converted_count || 0);

    // Pending records table
    if (data.pending_records && data.pending_records.length > 0) {
        render_table(page, data.pending_records);
    } else {
        page.main.html(
            '<div class="text-center text-muted p-5">' +
                '<i class="fa fa-check-circle fa-3x mb-3" style="color:#4caf50;"></i>' +
                "<h5>" + __("No pending records") + "</h5>" +
                "<p class='text-small'>" + __("All copy invoices have been processed.") + "</p>" +
            "</div>"
        );
    }
}

function render_table(page, records) {
    var html =
        '<div class="desk-page">' +
        '<div class="row">' +
        '<div class="col-md-12">' +
        '<div class="card">' +
        '<div class="card-header">' +
        '<h5 class="mb-0">' + __("Pending Copy Invoices") + "</h5>" +
        "</div>" +
        '<div class="card-body p-0">' +
        '<div class="table-responsive">' +
        '<table class="table table-hover">' +
        '<thead class="thead-light">' +
        "<tr>" +
        '<th style="width:40px;"><input type="checkbox" id="select-all"></th>' +
        "<th>" + __("Input VAT Undue") + "</th>" +
        "<th>" + __("Purchase Invoice") + "</th>" +
        "<th>" + __("Supplier") + "</th>" +
        "<th>" + __("Posting Date") + "</th>" +
        '<th class="text-right">' + __("Base Amount") + "</th>" +
        '<th class="text-right">' + __("VAT Amount") + "</th>" +
        "<th>" + __("Source") + "</th>" +
        "<th>" + __("Action") + "</th>" +
        "</tr>" +
        "</thead>" +
        "<tbody>";

    records.forEach(function (r) {
        var badge_class = r.source_doctype === "Import Clearance" ? "warning" : "info";
        var source = r.source_doctype || "Purchase Invoice";
        html +=
            "<tr data-name='" +
            r.name +
            "'>" +
            '<td><input type="checkbox" class="record-checkbox" data-name="' +
            r.name +
            '"></td>' +
            "<td><a href='/app/input-vat-undue/" +
            r.name +
            "' target='_blank'>" +
            r.name +
            "</a></td>" +
            "<td><a href='/app/purchase-invoice/" +
            r.purchase_invoice +
            "' target='_blank'>" +
            r.purchase_invoice +
            "</a></td>" +
            "<td>" +
            (r.supplier_name || r.supplier || "") +
            "</td>" +
            "<td>" +
            (r.posting_date ? frappe.format(r.posting_date, "Date") : "") +
            "</td>" +
            '<td class="text-right">' +
            fmt_money(r.base_amount, "THB") +
            "</td>" +
            '<td class="text-right"><strong>' +
            fmt_money(r.vat_amount, "THB") +
            "</strong></td>" +
            '<td><span class="badge badge-' +
            badge_class +
            '">' +
            source +
            "</span></td>" +
            '<td><button class="btn btn-sm btn-success mark-received" data-name="' +
            r.name +
            '">' +
            '<i class="fa fa-check mr-1"></i>' +
            __("Got Original") +
            "</button></td>" +
            "</tr>";
    });

    html += "</tbody></table></div></div>";

    // Bulk action bar
    html +=
        '<div class="card-footer" id="bulk-action-bar" style="display:none;">' +
        '<div class="d-flex align-items-center justify-content-between">' +
        '<span id="selected-count">0 selected</span>' +
        '<button class="btn btn-success" id="bulk-mark-received">' +
        '<i class="fa fa-check mr-1"></i>' +
        __("Mark Selected as Received") +
        "</button></div></div>";

    html += "</div></div></div></div>";
    page.main.html(html);

    // Select all toggle
    page.main.find("#select-all").on("change", function () {
        var checked = $(this).prop("checked");
        page.main.find(".record-checkbox").prop("checked", checked);
        update_bulk_bar();
    });

    // Individual checkbox toggle
    page.main.find(".record-checkbox").on("change", function () {
        update_bulk_bar();
    });

    // Single mark-received button
    page.main.find(".mark-received").on("click", function () {
        var name = $(this).data("name");
        mark_received([name]);
    });

    // Bulk mark-received button
    page.main.find("#bulk-mark-received").on("click", function () {
        var selected = [];
        page.main.find(".record-checkbox:checked").each(function () {
            selected.push($(this).data("name"));
        });
        if (selected.length === 0) {
            frappe.msgprint(__("No records selected"));
            return;
        }
        mark_received(selected);
    });
}

function update_bulk_bar() {
    var count = page.main.find(".record-checkbox:checked").length;
    page.main.find("#bulk-action-bar").toggle(count > 0);
    page.main.find("#selected-count").text(count + " " + __("selected"));
}

function mark_received(names) {
    if (names.length === 0) return;

    frappe.call({
        method: "print_designer.page.get_original_vat.get_original_vat.mark_bulk_received",
        args: { names: names },
        callback: function (r) {
            if (r.message) {
                var results = r.message;
                var success = 0,
                    failed = 0;
                results.forEach(function (res) {
                    if (res.success) success++;
                    else failed++;
                });
                frappe.msgprint({
                    title: __("Process Complete"),
                    indicator: failed === 0 ? "green" : "orange",
                    message:
                        __("{0} converted, {1} failed", [
                            success,
                            failed,
                        ]),
                });
                // Reload page
                frappe.call({
                    method:
                        "print_designer.page.get_original_vat.get_original_vat.get_pending_records",
                    callback: function (r2) {
                        if (r2.message) render_table(page, r2.message.pending_records || []);
                    },
                });
            }
        },
        error: function () {
            frappe.msgprint(__("Error processing records"));
        },
    });
}

function fmt_money(amount, currency) {
    if (!amount) return "0.00";
    return (
        amount
            .toFixed(2)
            .replace(/\B(?=(\d{3})+(?!\d))/g, ",") +
        " " +
        (currency || "")
    );
}
