// Thailand Withholding Tax Client Script for Item
// Provides guidance for service item classification

frappe.ui.form.on("Item", {
	setup: function (frm) {
		// Wire custom search: show category_name (Thai) in dropdown, save name
		frm.set_query("pd_custom_wht_income_type", () => ({
			query: "print_designer.controllers.queries.twc_search",
		}));
	},

	refresh: function (frm) {
		// Add helpful guidance for service classification
		add_service_classification_help(frm);

		// Show service-related warnings
		if (frm.doc.pd_custom_is_service_item) {
			show_wht_service_info(frm);
		}
	},

	pd_custom_is_service_item: function (frm) {
		if (frm.doc.pd_custom_is_service_item) {
			// Automatically uncheck is_stock_item when service item is checked
			frm.set_value('is_stock_item', 0);
			show_wht_service_info(frm);
		} else {
			hide_wht_service_info(frm);
		}
		// Note: When user unchecks service item, do NOT auto-check is_stock_item back
		// Leave it to user's discretion
	},

	item_group: function (frm) {
		// Auto-suggest service classification based on item group
		suggest_service_classification(frm);
	},
});

function add_service_classification_help(frm) {
	const field = frm.get_field('pd_custom_is_service_item');
	if (field && !field.df.description) {
		field.df.description = __("Check this for consulting, software development, maintenance, training, and other service-based items subject to 3% WHT in Thailand. Examples: Consulting Services, IT Support, Training Programs");
		field.refresh();
	}
}

function show_wht_service_info(frm) {
	if (
		!frm
			.get_field("pd_custom_is_service_item")
			.$wrapper.find(".wht-service-info").length
	) {
		frm.get_field("pd_custom_is_service_item").$wrapper.append(`
      <div class="wht-service-info alert alert-warning" style="margin-top: 10px;">
        <strong>⚠️ ${__("Service Item")}:</strong> ${__("This item will automatically trigger 3% withholding tax calculation in Sales Invoices for companies with Thailand Service Business enabled.")}
      </div>
    `);
	}
}

function hide_wht_service_info(frm) {
	frm
		.get_field("pd_custom_is_service_item")
		.$wrapper.find(".wht-service-info")
		.remove();
}

function suggest_service_classification(frm) {
	if (!frm.doc.item_group) return;

	// Common service-related item group patterns
	const service_keywords = [
		"service",
		"services",
		"consulting",
		"consultancy",
		"software",
		"it",
		"training",
		"maintenance",
		"support",
		"development",
		"design",
	];

	const item_group_lower = frm.doc.item_group.toLowerCase();
	const is_likely_service = service_keywords.some((keyword) =>
		item_group_lower.includes(keyword),
	);

	if (is_likely_service && !frm.doc.pd_custom_is_service_item) {
		// Auto-enable service item field based on item group
		frm.set_value("pd_custom_is_service_item", 1);
	}
}
