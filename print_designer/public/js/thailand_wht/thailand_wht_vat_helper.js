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
// Auto-enable "Subject to Withholding Tax" when the document contains a service item.
//
// Rule (mirrors the server side in print_designer/custom/service_item_wht.py):
// an item whose Item Group is "Services" makes the document subject to
// withholding tax.  The server side stays authoritative - this script only gives
// immediate feedback while the user edits the form.

const PD_SERVICE_ITEM_GROUP = 'services';

/**
 * Resolve the item codes of the form that belong to the "Services" item group.
 *
 * @param {Object} frm - Frappe form object
 * @returns {Promise<string[]>} service item codes
 */
function pd_get_service_item_codes(frm) {
	const rows = (frm.doc.items || []).filter(row => row.item_code);
	if (!rows.length) return Promise.resolve([]);

	const item_codes = [...new Set(rows.map(row => row.item_code))];

	return new Promise(resolve => {
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Item',
				filters: { name: ['in', item_codes] },
				fields: ['name', 'item_group'],
				limit_page_length: 0
			},
			callback: function(r) {
				const group_map = {};
				((r && r.message) || []).forEach(item => {
					group_map[item.name] = item.item_group;
				});

				const codes = rows
					.filter(row => {
						const group = row.item_group || group_map[row.item_code];
						return group && String(group).trim().toLowerCase() === PD_SERVICE_ITEM_GROUP;
					})
					.map(row => row.item_code);

				resolve([...new Set(codes)]);
			}
		});
	});
}

/**
 * Tick "Subject to Withholding Tax" when the form contains a service item.
 * The flag is never unticked automatically - a user may still set it manually.
 *
 * @param {Object} frm - Frappe form object
 */
function pd_apply_subject_to_wht_from_items(frm) {
	if (!frm || !frm.doc) return;

	// The field is installed per doctype - do nothing when it is missing
	const meta = frm.meta || frappe.get_meta(frm.doc.doctype);
	const df = (meta.fields || []).find(f => f.fieldname === 'pd_custom_subject_to_wht');
	if (!df) return;

	// Already enabled - never untick it automatically
	if (frm.doc.pd_custom_subject_to_wht) return;

	return pd_get_service_item_codes(frm).then(codes => {
		if (!codes.length) return;
		if (frm.doc.pd_custom_subject_to_wht) return;

		frm.set_value('pd_custom_subject_to_wht', 1);
		frappe.show_alert({
			message: __('Subject to Withholding Tax enabled (service item: {0})', [codes[0]]),
			indicator: 'blue'
		}, 5);
	});
}
