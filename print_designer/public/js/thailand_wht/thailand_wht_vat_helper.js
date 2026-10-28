// Shared VAT Treatment auto-detection helper
// Used by SI, SO, QT, PI, PO to auto-set pd_custom_vat_treatment based on Item properties

// Tax Category -> VAT treatment.  A supply of an "Exempt" or "Zero-Rated"
// customer is outside the standard VAT, so the items must not change the
// treatment of the document (the Tax Category decides).
const PD_CATEGORY_TREATMENTS = {
	'Exempt': 'Exempt from VAT',
	'Zero-Rated': 'Zero-rated for Export',
};

// The Tax Category of the document as a plain string.  `frappe.db.get_value`
// can hand over an object ({field: null}) for an empty field, which must not
// be used as a key.
function pd_tax_category(frm) {
	const category = frm && frm.doc && frm.doc.tax_category;
	return typeof category === 'string' ? category : '';
}

/**
 * Fill the WHT fields of the form from the items of the document.
 *
 * - pd_custom_wht_income_type  <- Item.pd_custom_wht_income_type
 *   (the Tax Withholding Category of the first item that defines one; a
 *   value the user entered manually is kept)
 * - pd_custom_withholding_tax_pct <- the rate of that income type (only
 *   when the field is still empty; a manual rate is kept)
 * - pd_custom_vat_treatment <- "VAT Undue" when one of the items is flagged
 *   as a service item (Item.pd_custom_is_service_item).  A deliberate manual
 *   choice ("Exempt from VAT" / "Zero-rated for Export") is kept.
 *
 * Mirrors the server side in print_designer/custom/item_wht_config.py.
 *
 * @param {Object} frm - Frappe form object
 */
/**
 * Fill the description of the selected WHT income type.
 *
 * The description is taken from the linked "Tax Withholding Category"
 * (Thai or English label, depending on the user language).
 *
 * @param {Object} frm - Frappe form object
 * @param {String} [income_type] - Income type, defaults to the current value
 */
function pd_set_wht_description(frm, income_type) {
	if (!frm) return;

	const name = income_type || (frm.doc && frm.doc.pd_custom_wht_income_type);
	if (!name) {
		if (frm.doc && frm.doc.pd_custom_wht_description) {
			frm.set_value('pd_custom_wht_description', '');
		}
		return;
	}

	const lang = frappe.boot.lang || 'en';
	const desc_field = lang === 'th' ? 'category_name' : 'category_name_en';

	frappe.db.get_value('Tax Withholding Category', name, [desc_field], function(r) {
		if (r) {
			frm.set_value('pd_custom_wht_description', r[desc_field] || '');
		}
	});
}

function pd_apply_item_wht_config(frm) {
	if (!frm || !frm.doc || !frm.doc.items || !frm.doc.items.length) return;

	const item_codes = [...new Set(
		frm.doc.items
			.filter(row => row.item_code)
			.map(row => row.item_code)
	)];
	if (!item_codes.length) return;

	frappe.call({
		method: 'print_designer.custom.item_wht_config.get_item_wht_config',
		args: { item_codes: item_codes },
		callback: function(r) {
			const config = (r && r.message) || {};
			const changes = [];

			if (config.income_type && !frm.doc.pd_custom_wht_income_type) {
				frm.set_value('pd_custom_wht_income_type', config.income_type);
				// The description is filled here as well: the WHT flag may
				// only be set after this call returns.
				pd_set_wht_description(frm, config.income_type);
				changes.push(__('WHT Income Type: {0}', [config.income_type]));
			}

			if (config.wht_rate && !frm.doc.pd_custom_withholding_tax_pct) {
				frm.set_value('pd_custom_withholding_tax_pct', config.wht_rate);
				changes.push(__('WHT Rate: {0}%', [config.wht_rate]));
			}

			if (config.is_service_item &&
				(!frm.doc.pd_custom_vat_treatment || frm.doc.pd_custom_vat_treatment === 'Standard VAT')) {
				frm.set_value('pd_custom_vat_treatment', 'VAT Undue');
				changes.push(__('VAT Treatment: VAT Undue'));
			}

			if (changes.length) {
				frappe.show_alert({
					message: changes.join(' | '),
					indicator: 'blue'
				}, 5);
			}
		}
	});
}

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

	// The Tax Category of the customer decides the treatment of the supply
	// (Exempt / Zero-Rated), the items must not override it.
	if (PD_CATEGORY_TREATMENTS[pd_tax_category(frm)]) return;

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

	// The Tax Category of the customer decides the treatment of the supply
	// (Exempt / Zero-Rated), the items must not override it.
	if (PD_CATEGORY_TREATMENTS[pd_tax_category(frm)]) return;

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
const PD_WHT_PREVIEW_SECTION = 'pd_custom_wht_preview_section';

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
 * Keep the "Thai Ecosystem (Withholding Tax & Retention)" section in sync with
 * the items of the document.
 *
 * - document subject to withholding tax (service item or manually enabled
 *   flag) -> the section is always open and cannot be collapsed
 *   (collapsible = 0)
 * - no service item -> the section stays collapsible and is collapsed by
 *   default (collapsible = 1)
 *
 * Mirrors the server side definition in
 * print_designer/custom/service_item_wht.py (CLIENT_SERVICE_ITEM_CONDITION).
 *
 * @param {Object} frm - Frappe form object
 * @param {string[]} [service_codes] - optional resolved service item codes
 */
function pd_sync_wht_preview_section(frm, service_codes) {
	if (!frm || !frm.doc) return;

	const section = frm.fields_dict && frm.fields_dict[PD_WHT_PREVIEW_SECTION];
	const meta_df = ((frm.meta && frm.meta.fields) || []).find(
		f => f.fieldname === PD_WHT_PREVIEW_SECTION
	);
	if (!section) return;

	// The section works on its own copy of the docfield, the meta entry is kept
	// in sync so both stay consistent
	const df = section.df || meta_df;
	if (!df) return;

	const rows = frm.doc.items || [];
	const has_service_item = rows.some(row =>
		row.item_group && String(row.item_group).trim().toLowerCase() === PD_SERVICE_ITEM_GROUP
	);

	const is_subject_to_wht = !!frm.doc.pd_custom_subject_to_wht;
	const has_service_codes = Array.isArray(service_codes) && service_codes.length > 0;

	// The section stays open when the document is subject to withholding tax
	const expanded = is_subject_to_wht || has_service_item || has_service_codes;
	const is_collapsible = !expanded;

	df.collapsible = is_collapsible ? 1 : 0;
	if (meta_df && meta_df !== df) meta_df.collapsible = df.collapsible;

	if (section.head) {
		section.head.toggleClass('collapsible', is_collapsible);
		section.indicator && section.indicator.toggle(is_collapsible);

		// Guard the click handler - a section that has to stay open cannot be collapsed
		if (!section.pd_collapse_guarded) {
			section.head.off('click').on('click', () => {
				if (section.df.collapsible) section.collapse();
			});
			section.pd_collapse_guarded = true;
		}
	}

	section.collapse(!expanded);
}

/**
 * Tick "Subject to Withholding Tax" when the form contains a service item.
 * The flag is never unticked automatically - a user may still set it manually.
 *
 * @param {Object} frm - Frappe form object
 */
async function pd_apply_subject_to_wht_from_items(frm) {
	if (!frm || !frm.doc) return;

	// The field is installed per doctype - do nothing when it is missing
	const meta = frm.meta || frappe.get_meta(frm.doc.doctype);
	const df = (meta.fields || []).find(f => f.fieldname === 'pd_custom_subject_to_wht');
	if (!df) return;

	// Already enabled - never untick it automatically
	if (frm.doc.pd_custom_subject_to_wht) {
		pd_sync_wht_preview_section(frm);
		return;
	}

	const codes = await pd_get_service_item_codes(frm);
	if (!codes.length) {
		pd_sync_wht_preview_section(frm, codes);
		return;
	}
	if (frm.doc.pd_custom_subject_to_wht) {
		pd_sync_wht_preview_section(frm, codes);
		return;
	}

	frm.set_value('pd_custom_subject_to_wht', 1);
	frappe.show_alert({
		message: __('Subject to Withholding Tax enabled (service item: {0})', [codes[0]]),
		indicator: 'blue'
	}, 5);
	pd_sync_wht_preview_section(frm, codes);
}
