// Shared VAT Treatment auto-detection helper
// Used by SI, SO, QT, PI, PO to auto-set pd_custom_vat_treatment based on Item properties

/**
 * Check all items in the transaction and auto-set VAT treatment.
 * Rule: If ANY item is a service (pd_custom_is_service_item=1), set "VAT Undue".
 *       If ALL items are goods, set "Standard VAT".
 *       User can still override manually.
 *
 * @param {Object} frm - Frappe form object
 * @param {Object} [trigger_item] - Optional: the item that triggered the check (for alert message)
 */
function pd_check_vat_treatment_from_items(frm, trigger_item) {
	if (!frm.doc.items || !frm.doc.items.length) return;

	// Skip if user has manually set to Exempt or Zero-rated (deliberate override)
	const current = frm.doc.pd_custom_vat_treatment;
	if (current === 'Exempt from VAT' || current === 'Zero-rated for Export') return;

	// Collect all unique item codes
	const item_codes = [...new Set(
		frm.doc.items
			.filter(row => row.item_code)
			.map(row => row.item_code)
	)];

	if (!item_codes.length) return;

	// Batch fetch service flag for all items
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Item',
			filters: { name: ['in', item_codes] },
			fields: ['name', 'pd_custom_is_service_item'],
			limit_page_length: 0
		},
		async: false,
		callback: function(r) {
			if (!r.message) return;

			const service_map = {};
			r.message.forEach(item => {
				service_map[item.name] = item.pd_custom_is_service_item;
			});

			const has_service = item_codes.some(code => service_map[code]);
			const suggested = has_service ? 'VAT Undue' : 'Standard VAT';

			if (current !== suggested) {
				frm.set_value('pd_custom_vat_treatment', suggested);

				const item_name = trigger_item ? trigger_item.item_code : '';
				if (has_service) {
					frappe.show_alert({
						message: item_name
							? __('VAT Treatment → VAT Undue (service item: {0})', [item_name])
							: __('VAT Treatment → VAT Undue (service items detected)'),
						indicator: 'blue'
					}, 5);
				}
			}
		}
	});
}

/**
 * Check a single item and auto-set VAT treatment.
 * Called from item_code change handler — fetches only the changed item.
 *
 * @param {Object} frm - Frappe form object
 * @param {string} item_code - The item code that was just selected
 */
function pd_check_single_item_vat(frm, item_code) {
	if (!item_code) return;

	// Skip if user has manually set to Exempt or Zero-rated
	const current = frm.doc.pd_custom_vat_treatment;
	if (current === 'Exempt from VAT' || current === 'Zero-rated for Export') return;

	frappe.db.get_value('Item', item_code, 'pd_custom_is_service_item').then(r => {
		if (r.message && r.message.pd_custom_is_service_item) {
			// This item is a service — set VAT Undue
			if (current !== 'VAT Undue') {
				frm.set_value('pd_custom_vat_treatment', 'VAT Undue');
				frappe.show_alert({
					message: __('VAT Treatment → VAT Undue (service item: {0})', [item_code]),
					indicator: 'blue'
				}, 5);
			}
		} else if (current === 'VAT Undue' || !current) {
			// This item is NOT a service. Re-check all items —
			// maybe VAT Undue was set by a previous service item that's still in the list
			pd_check_vat_treatment_from_items(frm);
		}
	});
}
