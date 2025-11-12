// Thailand Withholding Tax Client Script for Purchase Order
// Smart automation for better UX when apply_thai_wht_compliance is enabled

console.log('🚀 Purchase Order TDS Client Script Loaded Successfully');

frappe.ui.form.on('Purchase Order', {
    // Smart automation: When Thai WHT compliance is enabled, auto-select VAT Undue and enable subject_to_wht
    apply_thai_wht_compliance: function(frm) {
        console.log('🔥 Purchase Order Thai WHT Compliance Script Triggered!', {
            apply_thai_wht_compliance: frm.doc.apply_thai_wht_compliance,
            current_vat_treatment: frm.doc.vat_treatment,
            current_subject_to_wht: frm.doc.subject_to_wht
        });
        if (frm.doc.apply_thai_wht_compliance) {
            // Auto-enable subject_to_wht for TDS transactions
            if (!frm.doc.subject_to_wht) {
                frm.set_value('subject_to_wht', 1);
            }

            // Auto-select VAT Undue for better UX
            console.log('🎯 Checking VAT Treatment field...', {
                current_value: frm.doc.vat_treatment,
                field_exists: !!frm.get_field('vat_treatment'),
                field_options: frm.get_field('vat_treatment') ? frm.get_field('vat_treatment').df.options : 'field not found'
            });

            // Auto-change from Standard VAT to VAT Undue for TDS transactions
            if (!frm.doc.vat_treatment || frm.doc.vat_treatment === '' || frm.doc.vat_treatment === 'Standard VAT') {
                console.log('⚡ Setting VAT Treatment to VAT Undue...');
                frm.set_value('vat_treatment', 'VAT Undue');
            } else {
                console.log('⏭️ VAT Treatment already set to:', frm.doc.vat_treatment);
            }

            // Show user-friendly message
            frappe.show_alert({
                message: __('Thai WHT Compliance enabled: Subject to WHT and VAT Treatment automatically configured'),
                indicator: 'blue'
            }, 4);

            console.log('Purchase Order Thai WHT: Auto-enabled subject_to_wht and VAT Undue');
        } else {
            // When Thai WHT compliance is disabled, clear auto-set fields
            if (frm.doc.subject_to_wht) {
                frm.set_value('subject_to_wht', 0);
            }

            if (frm.doc.vat_treatment === 'VAT Undue') {
                frm.set_value('vat_treatment', 'Standard VAT');
            }

            frappe.show_alert({
                message: __('Thai WHT Compliance disabled: WHT and VAT settings cleared'),
                indicator: 'orange'
            }, 3);
        }
    },

    // Handle WHT income type changes for description updates
    wht_income_type: function(frm) {
        if (frm.doc.wht_income_type && frm.doc.subject_to_wht) {
            const descriptions = {
                'professional_services': 'ค่าจ้างวิชาชีพ (Professional Services)',
                'rental': 'ค่าเช่า (Rental)',
                'service_fees': 'ค่าบริการ (Service Fees)',
                'construction': 'ค่าก่อสร้าง (Construction)',
                'advertising': 'ค่าโฆษณา (Advertising)',
                'other_services': 'ค่าบริการอื่น ๆ (Other Services)'
            };

            frm.set_value('wht_description', descriptions[frm.doc.wht_income_type] || '');
        }
    },

    // Auto-populate WHT note when subject_to_wht is enabled
    subject_to_wht: function(frm) {
        if (frm.doc.subject_to_wht && frm.doc.apply_thai_wht_compliance) {
            // Auto-populate WHT note if empty
            if (!frm.doc.wht_note || frm.doc.wht_note === '') {
                frm.set_value('wht_note',
                    'หมายเหตุ: จำนวนเงินภาษีหัก ณ ที่จ่าย จะถูกหักเมื่อชำระเงิน\n' +
                    'Note: Withholding tax amount will be deducted upon payment'
                );
            }
        }
    },

    // Smart validation: Warn if VAT treatment doesn't match Thai WHT settings
    vat_treatment: function(frm) {
        if (frm.doc.apply_thai_wht_compliance && frm.doc.vat_treatment) {
            // Recommend VAT Undue for TDS transactions
            if (frm.doc.vat_treatment !== 'VAT Undue') {
                frappe.show_alert({
                    message: __('Consider using "VAT Undue" for TDS transactions to comply with Thai tax regulations'),
                    indicator: 'yellow'
                }, 5);
            }
        }
    },

    // Form refresh: Apply smart defaults
    refresh: function(frm) {
        // Add custom button for Thai WHT setup if Thai WHT compliance is enabled
        if (frm.doc.apply_thai_wht_compliance && !frm.is_new()) {
            frm.add_custom_button(__('Setup TDS Fields'), function() {
                // Smart setup for common TDS scenarios
                let d = new frappe.ui.Dialog({
                    title: __('Quick TDS Setup'),
                    fields: [
                        {
                            fieldtype: 'Select',
                            fieldname: 'wht_income_type',
                            label: __('Income Type'),
                            options: [
                                '', 'professional_services', 'rental', 'service_fees',
                                'construction', 'advertising', 'other_services'
                            ],
                            default: frm.doc.wht_income_type || ''
                        },
                        {
                            fieldtype: 'Check',
                            fieldname: 'subject_to_wht',
                            label: __('Subject to Withholding Tax'),
                            default: frm.doc.subject_to_wht || 0
                        },
                        {
                            fieldtype: 'Check',
                            fieldname: 'subject_to_retention',
                            label: __('Subject to Retention'),
                            default: frm.doc.custom_subject_to_retention || 0
                        }
                    ],
                    primary_action_label: __('Apply'),
                    primary_action: function(values) {
                        // Apply selected values
                        if (values.wht_income_type) {
                            frm.set_value('wht_income_type', values.wht_income_type);
                        }
                        if (values.subject_to_wht) {
                            frm.set_value('subject_to_wht', values.subject_to_wht);
                        }
                        if (values.subject_to_retention) {
                            frm.set_value('custom_subject_to_retention', values.subject_to_retention);
                        }

                        // Auto-set VAT Undue if not already set
                        if (!frm.doc.vat_treatment) {
                            frm.set_value('vat_treatment', 'VAT Undue');
                        }

                        d.hide();
                        frappe.show_alert({
                            message: __('TDS fields configured successfully'),
                            indicator: 'green'
                        }, 3);
                    }
                });
                d.show();
            }, __('Thai Tax'));
        }

        // Add help text for Thai WHT users
        if (frm.doc.apply_thai_wht_compliance) {
            frm.set_df_property('apply_thai_wht_compliance', 'description',
                'Thai WHT Compliance enabled: VAT Treatment will be auto-set to "VAT Undue" for compliance'
            );
        }

        // Add smart workflow guidance for services
        if (frm.doc.docstatus === 1 && frm.doc.apply_thai_wht_compliance) {
            check_service_items_and_show_workflow_guidance(frm);
        }
    }
});

// Smart Item-based WHT Automation
frappe.ui.form.on('Purchase Order Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.item_code) {
            console.log('🔍 Item selected:', row.item_code);

            // Get item WHT configuration
            frappe.db.get_value('Item', row.item_code, [
                'wht_income_type',
                'pd_custom_is_service_item'
            ]).then(r => {
                if (r.message) {
                    console.log('📋 Item WHT config:', r.message);

                    // Auto-configure WHT if item is a service with WHT type
                    if (r.message.pd_custom_is_service_item && r.message.wht_income_type) {
                        smart_configure_wht_from_item(frm, r.message, row.item_code);
                    }
                }
            }).catch(err => {
                console.log('⚠️ Error fetching item WHT config:', err);
            });
        }
    },

    // Also trigger on item removal to check if WHT should be disabled
    items_remove: function(frm) {
        // Small delay to let DOM update
        setTimeout(() => {
            check_remaining_wht_items(frm);
        }, 100);
    }
});

// Smart WHT Configuration Function
function smart_configure_wht_from_item(frm, item_wht_config, item_code) {
    console.log('🎯 Smart configuring WHT from item:', item_code);

    let changes_made = [];

    // Auto-enable Thai WHT compliance if not already enabled
    if (!frm.doc.apply_thai_wht_compliance) {
        frm.set_value('apply_thai_wht_compliance', 1);
        changes_made.push('Thai WHT compliance enabled');
        console.log('✅ Auto-enabled apply_thai_wht_compliance');
    }

    // Auto-enable subject to WHT if not already enabled
    if (!frm.doc.subject_to_wht) {
        frm.set_value('subject_to_wht', 1);
        changes_made.push('WHT enabled');
        console.log('✅ Auto-enabled subject_to_wht');
    }

    // Set WHT Income Type from item (only if not already set or different)
    if (item_wht_config.wht_income_type &&
        (!frm.doc.wht_income_type || frm.doc.wht_income_type !== item_wht_config.wht_income_type)) {
        frm.set_value('wht_income_type', item_wht_config.wht_income_type);
        changes_made.push(`WHT type: ${item_wht_config.wht_income_type}`);
        console.log('✅ Set wht_income_type to:', item_wht_config.wht_income_type);
    }

    // Auto-select VAT Undue if Standard VAT is set
    if (frm.doc.vat_treatment === 'Standard VAT') {
        frm.set_value('vat_treatment', 'VAT Undue');
        changes_made.push('VAT → VAT Undue');
        console.log('✅ Changed VAT treatment to VAT Undue');
    }

    // Show intelligent alert with changes made
    if (changes_made.length > 0) {
        frappe.show_alert({
            message: __('Smart WHT: Auto-configured from item "{0}": {1}', [item_code, changes_made.join(', ')]),
            indicator: 'green'
        }, 5);
    }
}

// Check if any remaining items require WHT
function check_remaining_wht_items(frm) {
    if (!frm.doc.items || frm.doc.items.length === 0) {
        // No items left, could disable WHT
        return;
    }

    console.log('🔍 Checking remaining items for WHT requirements...');

    let wht_items = [];
    let promises = [];

    // Check each remaining item
    frm.doc.items.forEach(item => {
        if (item.item_code) {
            promises.push(
                frappe.db.get_value('Item', item.item_code, [
                    'wht_income_type',
                    'pd_custom_is_service_item'
                ]).then(r => {
                    if (r.message && r.message.pd_custom_is_service_item && r.message.wht_income_type) {
                        wht_items.push({
                            item_code: item.item_code,
                            wht_income_type: r.message.wht_income_type
                        });
                    }
                })
            );
        }
    });

    // Process results
    Promise.all(promises).then(() => {
        if (wht_items.length === 0 && frm.doc.apply_thai_wht_compliance) {
            // No WHT items remaining, suggest disabling WHT
            frappe.confirm(
                __('No items requiring WHT found. Disable WHT settings?'),
                () => {
                    frm.set_value('apply_thai_wht_compliance', 0);
                    frm.set_value('subject_to_wht', 0);
                    frm.set_value('wht_income_type', '');
                    if (frm.doc.vat_treatment === 'VAT Undue') {
                        frm.set_value('vat_treatment', 'Standard VAT');
                    }

                    frappe.show_alert({
                        message: __('WHT settings cleared as no WHT items remain'),
                        indicator: 'orange'
                    }, 3);
                }
            );
        } else if (wht_items.length > 0) {
            console.log('✅ WHT items still present:', wht_items);
        }
    });
}

// Check for service items and show workflow guidance
function check_service_items_and_show_workflow_guidance(frm) {
    if (!frm.doc.items || frm.doc.items.length === 0) {
        return;
    }

    console.log('🔍 DEBUG: Checking for service items to provide workflow guidance');

    let service_items = [];
    let stock_items = [];
    let promises = [];

    // Check each item to determine if it's a service
    frm.doc.items.forEach(item => {
        if (item.item_code) {
            promises.push(
                frappe.db.get_value('Item', item.item_code, [
                    'pd_custom_is_service_item',
                    'is_stock_item',
                    'item_name'
                ]).then(r => {
                    if (r.message) {
                        if (r.message.pd_custom_is_service_item) {
                            service_items.push({
                                item_code: item.item_code,
                                item_name: r.message.item_name
                            });
                        } else if (r.message.is_stock_item) {
                            stock_items.push({
                                item_code: item.item_code,
                                item_name: r.message.item_name
                            });
                        }
                    }
                })
            );
        }
    });

    // Process results and show appropriate guidance
    Promise.all(promises).then(() => {
        console.log('📋 DEBUG: Service items analysis:', {
            service_items: service_items.length,
            stock_items: stock_items.length,
            total_items: frm.doc.items.length
        });

        if (service_items.length > 0) {
            show_workflow_guidance_dialog(frm, service_items, stock_items);
        }
    });
}

// Show workflow guidance dialog
function show_workflow_guidance_dialog(frm, service_items, stock_items) {
    const has_mixed_items = service_items.length > 0 && stock_items.length > 0;
    const all_services = service_items.length > 0 && stock_items.length === 0;

    let message = '';
    let indicator = 'blue';

    if (all_services) {
        message = `
            <div style="margin-bottom: 15px;">
                <h4 style="color: var(--success);">🎯 Service Items Detected - Direct Invoice Workflow</h4>
                <p><strong>All items in this Purchase Order are services.</strong></p>
            </div>
            <div style="margin-bottom: 15px;">
                <h5>📋 Recommended Workflow:</h5>
                <ol style="margin-left: 20px;">
                    <li><strong>Skip Purchase Receipt</strong> - Services don't require stock receiving</li>
                    <li><strong>Create Purchase Invoice directly</strong> from this Purchase Order</li>
                    <li><strong>WHT fields will auto-populate</strong> from Purchase Order data</li>
                </ol>
            </div>
            <div style="background-color: var(--alert-bg-success); border: 1px solid var(--alert-border-success); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <strong>💡 Why skip Purchase Receipt?</strong><br>
                Services have no physical stock to receive, so Purchase Receipt is unnecessary.
                Creating Purchase Invoice directly ensures WHT fields populate correctly.
            </div>
        `;
        indicator = 'green';
    } else if (has_mixed_items) {
        message = `
            <div style="margin-bottom: 15px;">
                <h4 style="color: var(--warning);">⚠️ Mixed Items Detected - Special Workflow Required</h4>
                <p>This Purchase Order contains both <strong>stock items</strong> and <strong>services</strong>.</p>
            </div>
            <div style="margin-bottom: 15px;">
                <h5>📋 Recommended Workflow:</h5>
                <ol style="margin-left: 20px;">
                    <li><strong>For Stock Items:</strong> Create Purchase Receipt first</li>
                    <li><strong>For Services:</strong> Create separate Purchase Order for services only</li>
                    <li><strong>Then create Purchase Invoices</strong> to ensure proper WHT auto-population</li>
                </ol>
            </div>
            <div style="background-color: var(--alert-bg-warning); border: 1px solid var(--alert-border-warning); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <strong>🔧 Service Items Found:</strong><br>
                ${service_items.map(item => `• ${item.item_code} - ${item.item_name}`).join('<br>')}
            </div>
            <div style="background-color: var(--alert-bg-info); border: 1px solid var(--alert-border-info); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <strong>📦 Stock Items Found:</strong><br>
                ${stock_items.map(item => `• ${item.item_code} - ${item.item_name}`).join('<br>')}
            </div>
        `;
        indicator = 'orange';
    }

    // Show the guidance dialog with auto fade-out
    frappe.show_alert({
        message: `<div><strong>Thai WHT Workflow Guidance</strong><br>${message}</div>`,
        indicator: indicator
    }, 8); // Auto fade-out after 8 seconds

    // Note: Removed custom Create buttons to preserve standard ERPNext Create dropdown
    // Standard Create menu includes: Purchase Receipt, Purchase Invoice, Payment, Payment Request
}