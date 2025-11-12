// Thailand Withholding Tax Client Script for Purchase Invoice
// Smart automation for better UX when apply_thai_wht_compliance is enabled

console.log('🚀 Purchase Invoice TDS Client Script Loaded Successfully');

frappe.ui.form.on('Purchase Invoice', {
    // Form refresh: Check for auto-populated fields + setup buttons
    refresh: function(frm) {
        if (!frm.is_new()) {
            console.log('🔄 DEBUG: Purchase Invoice refresh triggered', {
                doc_name: frm.doc.name,
                has_items: frm.doc.items ? frm.doc.items.length : 0,
                apply_thai_wht_compliance: frm.doc.apply_thai_wht_compliance,
                auto_populated_fields: _count_auto_populated_fields(frm)
            });
        }

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
    },

    // Smart automation: When Thai WHT compliance is enabled, auto-select VAT Undue and enable subject_to_wht
    apply_thai_wht_compliance: function(frm) {
        console.log('🔥 DEBUG: Purchase Invoice Thai WHT Compliance Script Triggered!', {
            apply_thai_wht_compliance: frm.doc.apply_thai_wht_compliance,
            current_vat_treatment: frm.doc.vat_treatment,
            current_subject_to_wht: frm.doc.subject_to_wht,
            doc_name: frm.doc.name
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

            console.log('Purchase Invoice Thai WHT: Auto-enabled subject_to_wht and VAT Undue');
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

    // Handle cash purchase (is_paid) - populate compliance section from preview
    is_paid: function(frm) {
        console.log('💰 DEBUG: is_paid checkbox changed:', {
            is_paid: frm.doc.is_paid,
            apply_thai_wht_compliance: frm.doc.apply_thai_wht_compliance,
            subject_to_wht: frm.doc.subject_to_wht
        });

        if (frm.doc.is_paid && frm.doc.apply_thai_wht_compliance && frm.doc.subject_to_wht) {
            console.log('🔄 DEBUG: Triggering compliance section population for cash purchase');

            // Call server method to populate compliance section
            frappe.call({
                method: 'print_designer.regional.purchase_invoice_wht_override.populate_compliance_section_from_preview',
                args: {
                    doc: frm.doc
                },
                callback: function(r) {
                    if (r.message) {
                        console.log('✅ DEBUG: Compliance section populated successfully');
                        frm.refresh();

                        frappe.show_alert({
                            message: __('Thai Tax Compliance section populated for cash purchase'),
                            indicator: 'green'
                        }, 3);
                    }
                },
                error: function(r) {
                    console.log('❌ DEBUG: Error populating compliance section:', r);
                }
            });
        } else if (!frm.doc.is_paid) {
            console.log('⏭️ DEBUG: Cash purchase disabled - compliance section not needed');

            frappe.show_alert({
                message: __('Cash purchase disabled - Thai Tax Compliance section cleared'),
                indicator: 'orange'
            }, 3);
        }
    }
});

// Helper function to count auto-populated fields for debugging
function _count_auto_populated_fields(frm) {
    let count = 0;
    const fields_to_check = [
        'pd_custom_tax_invoice_company_name', 'pd_custom_tax_invoice_address', 'pd_custom_tax_invoice_phone',
        'pd_custom_tax_invoice_fax', 'pd_custom_tax_invoice_email', 'pd_custom_tax_invoice_tax_id',
        'pd_custom_tax_invoice_branch_code', 'pd_custom_tax_invoice_bill_to', 'pd_custom_tax_invoice_bill_to_address',
        'pd_custom_wht_certificate_company_name', 'pd_custom_wht_certificate_address', 'pd_custom_wht_certificate_tax_id',
        'apply_thai_wht_compliance', 'subject_to_wht', 'wht_income_type', 'custom_withholding_tax'
    ];

    fields_to_check.forEach(field => {
        if (frm.doc[field]) count++;
    });

    console.log('🔍 DEBUG: Auto-populated field details:', {
        total_checked: fields_to_check.length,
        populated_count: count,
        populated_fields: fields_to_check.filter(f => frm.doc[f])
    });

    return count;
}

// Smart Item-based WHT Automation
frappe.ui.form.on('Purchase Invoice Item', {
    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.item_code) {
            console.log('🔍 DEBUG: Item selected in Purchase Invoice:', {
                item_code: row.item_code,
                row_idx: row.idx,
                current_wht_status: frm.doc.apply_thai_wht_compliance
            });

            // Get item WHT configuration
            frappe.db.get_value('Item', row.item_code, [
                'wht_income_type',
                'pd_custom_is_service_item'
            ]).then(r => {
                if (r.message) {
                    console.log('📋 DEBUG: Item WHT config fetched:', {
                        item_code: row.item_code,
                        config: r.message,
                        is_service: r.message.pd_custom_is_service_item,
                        wht_type: r.message.wht_income_type
                    });

                    // Auto-configure WHT if item is a service with WHT type
                    if (r.message.pd_custom_is_service_item && r.message.wht_income_type) {
                        console.log('🎯 DEBUG: Triggering smart WHT configuration from item');
                        smart_configure_wht_from_item(frm, r.message, row.item_code);
                    } else {
                        console.log('⏭️ DEBUG: Item does not require WHT configuration:', {
                            is_service: r.message.pd_custom_is_service_item,
                            has_wht_type: !!r.message.wht_income_type
                        });
                    }
                }
            }).catch(err => {
                console.log('⚠️ DEBUG: Error fetching item WHT config:', {
                    item_code: row.item_code,
                    error: err
                });
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
    console.log('🎯 DEBUG: Starting smart WHT configuration from item:', {
        item_code: item_code,
        item_config: item_wht_config,
        current_doc_state: {
            apply_thai_wht_compliance: frm.doc.apply_thai_wht_compliance,
            subject_to_wht: frm.doc.subject_to_wht,
            wht_income_type: frm.doc.wht_income_type,
            vat_treatment: frm.doc.vat_treatment
        }
    });

    let changes_made = [];

    // Auto-enable Thai WHT compliance if not already enabled
    if (!frm.doc.apply_thai_wht_compliance) {
        console.log('🔄 DEBUG: Enabling apply_thai_wht_compliance');
        frm.set_value('apply_thai_wht_compliance', 1);
        changes_made.push('Thai WHT compliance enabled');
        console.log('✅ DEBUG: Auto-enabled apply_thai_wht_compliance');
    } else {
        console.log('⏭️ DEBUG: apply_thai_wht_compliance already enabled');
    }

    // Auto-enable subject to WHT if not already enabled
    if (!frm.doc.subject_to_wht) {
        console.log('🔄 DEBUG: Enabling subject_to_wht');
        frm.set_value('subject_to_wht', 1);
        changes_made.push('WHT enabled');
        console.log('✅ DEBUG: Auto-enabled subject_to_wht');
    } else {
        console.log('⏭️ DEBUG: subject_to_wht already enabled');
    }

    // Set WHT Income Type from item (only if not already set or different)
    if (item_wht_config.wht_income_type &&
        (!frm.doc.wht_income_type || frm.doc.wht_income_type !== item_wht_config.wht_income_type)) {
        console.log('🔄 DEBUG: Setting wht_income_type from item:', {
            from_item: item_wht_config.wht_income_type,
            current_value: frm.doc.wht_income_type
        });
        frm.set_value('wht_income_type', item_wht_config.wht_income_type);
        changes_made.push(`WHT type: ${item_wht_config.wht_income_type}`);
        console.log('✅ DEBUG: Set wht_income_type to:', item_wht_config.wht_income_type);
    } else {
        console.log('⏭️ DEBUG: wht_income_type not changed:', {
            item_has_type: !!item_wht_config.wht_income_type,
            current_value: frm.doc.wht_income_type,
            values_match: frm.doc.wht_income_type === item_wht_config.wht_income_type
        });
    }

    // Auto-select VAT Undue if Standard VAT is set
    if (frm.doc.vat_treatment === 'Standard VAT') {
        console.log('🔄 DEBUG: Converting Standard VAT to VAT Undue');
        frm.set_value('vat_treatment', 'VAT Undue');
        changes_made.push('VAT → VAT Undue');
        console.log('✅ DEBUG: Changed VAT treatment to VAT Undue');
    } else {
        console.log('⏭️ DEBUG: VAT treatment not changed, current value:', frm.doc.vat_treatment);
    }

    // Show intelligent alert with changes made
    if (changes_made.length > 0) {
        console.log('🎉 DEBUG: Smart WHT configuration completed with changes:', changes_made);
        frappe.show_alert({
            message: __('Smart WHT: Auto-configured from item "{0}": {1}', [item_code, changes_made.join(', ')]),
            indicator: 'green'
        }, 5);
    } else {
        console.log('ℹ️ DEBUG: Smart WHT configuration completed with no changes needed');
    }
}

// Check if any remaining items require WHT
function check_remaining_wht_items(frm) {
    if (!frm.doc.items || frm.doc.items.length === 0) {
        console.log('ℹ️ DEBUG: No items in document, skipping WHT check');
        return;
    }

    console.log('🔍 DEBUG: Checking remaining items for WHT requirements:', {
        total_items: frm.doc.items.length,
        current_wht_status: frm.doc.apply_thai_wht_compliance,
        items: frm.doc.items.map(item => ({item_code: item.item_code, qty: item.qty}))
    });

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