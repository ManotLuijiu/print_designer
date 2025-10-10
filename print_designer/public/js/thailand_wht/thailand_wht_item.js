// Thailand Withholding Tax Client Script for Item
// Provides guidance for service item classification

frappe.ui.form.on("Item", {
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
			show_wht_service_info(frm);
		} else {
			hide_wht_service_info(frm);
		}
	},

	item_group: function (frm) {
		// Auto-suggest service classification based on item group
		suggest_service_classification(frm);
	},
});

function add_service_classification_help(frm) {
	const field = frm.get_field('pd_custom_is_service_item');
	if (field && !field.df.description) {
		field.df.description = 'Check this for consulting, software development, maintenance, training, and other service-based items subject to 3% WHT in Thailand. Examples: Consulting Services, IT Support, Training Programs';
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
        <strong>⚠️ Service Item:</strong> This item will automatically trigger 3% withholding tax 
        calculation in Sales Invoices for companies with Thailand Service Business enabled.
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
		frappe.msgprint({
			title: __("Service Item Suggestion"),
			message: __(
				'Based on the Item Group "{0}", this might be a service item. Consider checking "Is Service" if this item represents a service subject to withholding tax.',
				[frm.doc.item_group],
			),
			indicator: "blue",
		});
	}
}
