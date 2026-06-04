/**
 * Payment Entry Thai Tax Enhancement
 * 
 * This script enhances the Payment Entry form to automatically populate
 * Thai tax fields when fetching outstanding invoices.
 */

frappe.ui.form.on('Payment Entry', {
    refresh: function(frm) {
        console.log('🔄 Payment Entry refresh triggered:', frm.doc.name || 'New');
        console.log('📊 Form state:', {
            is_new: frm.is_new(),
            docstatus: frm.doc.docstatus,
            references_count: frm.doc.references ? frm.doc.references.length : 0
        });
        // Collapse pd_custom_wht_preview_section after save (keep clean UI)
        // Only collapse for non-new documents (after initial save)
        if (!frm.is_new() && frm.fields_dict['pd_custom_wht_preview_section']) {
            console.log('📂 Collapsing Thai Ecosystem section after save');
            frm.fields_dict['pd_custom_wht_preview_section'].collapse();
        }
        // Add custom logic after refresh
        if (!frm.is_new()) {
            console.log('📄 Existing Payment Entry - populating Thai tax fields');
            populate_thai_tax_fields_for_existing_references(frm);
        } else {
            console.log('🆕 New Payment Entry - scheduling Thai tax field population');
            // For new Payment Entry (created from Sales Invoice via "Create > Payment")
            // Check if references are already populated and Thai tax fields are missing
            setTimeout(() => {
                populate_thai_tax_fields_for_new_payment_entry(frm);
            }, 500);
        }
    },
});

frappe.ui.form.on('Payment Entry Reference', {
    reference_name: function(frm, cdt, cdn) {
        console.log('🔗 Reference name changed:', cdn);
        // When reference name is set or changed
        const row = locals[cdt][cdn];
        console.log('📄 Reference details:', {
            doctype: row.reference_doctype,
            name: row.reference_name,
            allocated: row.allocated_amount
        });
        if (row.reference_doctype && row.reference_name) {
            console.log('🔍 Fetching Thai tax fields for changed reference');
            fetch_and_populate_thai_tax_fields(frm, row);
        }
    },
    
    allocated_amount: function(frm, cdt, cdn) {
        console.log('💰 Allocated amount changed for:', cdn);
        // Recalculate net payable when allocated amount changes
        const row = locals[cdt][cdn];
        console.log('💵 New allocated amount:', row.allocated_amount);
        calculate_net_payable_for_row(row);
        frm.refresh_field('references');
        calculate_thai_tax_totals(frm);
    }
});

// Override the get_outstanding_invoices function to add Thai tax population
const original_get_outstanding_invoices = cur_frm.events.get_outstanding_invoices;
if (original_get_outstanding_invoices) {
    frappe.ui.form.on('Payment Entry', {
        get_outstanding_invoices: function(frm) {
            // Call original function
            if (typeof original_get_outstanding_invoices === 'function') {
                original_get_outstanding_invoices(frm);
            } else if (frm.events && frm.events.get_outstanding_invoices_or_orders) {
                frm.events.get_outstanding_invoices_or_orders(frm, true, false);
            }
            
            // After outstanding invoices are fetched, populate Thai tax fields
            setTimeout(() => {
                populate_thai_tax_fields_after_fetch(frm);
            }, 1000);
        }
    });
}

function populate_thai_tax_fields_after_fetch(frm) {
    /**
     * Populate Thai tax fields for all references after fetching outstanding invoices
     */
    console.log('📋 populate_thai_tax_fields_after_fetch called');
    console.log('📊 References count:', frm.doc.references ? frm.doc.references.length : 0);

    if (!frm.doc.references || frm.doc.references.length === 0) {
        console.log('⚠️ No references found, skipping Thai tax population');
        return;
    }

    let promises = [];
    console.log('🔄 Processing references for Thai tax field population');
    
    frm.doc.references.forEach(function(ref, idx) {
        console.log(`📄 Processing reference ${idx + 1}:`, {
            doctype: ref.reference_doctype,
            name: ref.reference_name,
            allocated: ref.allocated_amount
        });

        if (ref.reference_doctype === 'Sales Invoice' && ref.reference_name) {
            console.log(`🔍 Fetching Thai tax data for: ${ref.reference_name}`);
            promises.push(fetch_thai_tax_fields(ref.reference_doctype, ref.reference_name)
                .then(data => {
                    console.log(`📊 Thai tax data received for ${ref.reference_name}:`, data);
                    if (data) {
                        // Map API response fields to Payment Entry Reference fields (corrected mapping)
                        ref.pd_custom_has_retention = data.has_retention || 0;
                        ref.pd_custom_retention_amount = data.retention_amount || 0;
                        ref.pd_custom_retention_percentage = data.retention || 0;
                        ref.pd_custom_wht_amount = data.wht_amount || 0;
                        ref.pd_custom_wht_percentage = data.wht || 0;
                        ref.pd_custom_vat_undue_amount = data.vat_undue || 0;
                        ref.pd_custom_base_net_total = data.base_net_total || 0;  // Store base amount

                        console.log(`✅ Thai tax fields populated for ${ref.reference_name}:`, {
                            retention: ref.pd_custom_retention_amount,
                            wht: ref.pd_custom_wht_amount,
                            vat_undue: ref.pd_custom_vat_undue_amount
                        });

                        // Calculate net payable
                        calculate_net_payable_for_row(ref);
                    } else {
                        console.log(`⚠️ No Thai tax data returned for ${ref.reference_name}`);
                    }
                })
            );
        } else {
            console.log(`⏭️ Skipping reference ${idx + 1} (not Sales Invoice or no name)`);
        }
    });
    
    Promise.all(promises).then(() => {
        console.log('✅ All Thai tax field fetching completed');
        frm.refresh_field('references');
        calculate_thai_tax_totals(frm);
        console.log('🔄 Form refreshed and totals calculated');
    }).catch(error => {
        console.error('❌ Error in Thai tax field population:', error);
    });
}

function populate_thai_tax_fields_for_existing_references(frm) {
    /**
     * Populate Thai tax fields for existing Payment Entry
     */
    if (!frm.doc.references || frm.doc.references.length === 0) {
        return;
    }
    
    // Check if Thai tax fields are already populated
    let needs_population = false;
    frm.doc.references.forEach(function(ref) {
        if (ref.reference_doctype === 'Sales Invoice' && ref.reference_name) {
            // Check if any Thai tax field is missing (check for undefined/null, not falsy values)
            if (typeof ref.pd_custom_has_retention === 'undefined' && 
                typeof ref.pd_custom_wht_amount === 'undefined' && 
                typeof ref.pd_custom_vat_undue_amount === 'undefined') {
                needs_population = true;
            }
        }
    });
    
    if (needs_population) {
        populate_thai_tax_fields_after_fetch(frm);
    }
}

function populate_thai_tax_fields_for_new_payment_entry(frm) {
    /**
     * Populate Thai tax fields for new Payment Entry created from Sales Invoice
     * This handles the "Create > Payment" scenario
     */
    if (!frm.doc.references || frm.doc.references.length === 0) {
        return;
    }
    
    // For new Payment Entry, the server should have already populated Thai tax fields
    // But if they're missing (due to timing), populate them
    let needs_population = false;
    frm.doc.references.forEach(function(ref) {
        if (ref.reference_doctype === 'Sales Invoice' && ref.reference_name) {
            // Check if Thai tax fields are missing
            if (typeof ref.pd_custom_has_retention === 'undefined' && 
                typeof ref.pd_custom_wht_amount === 'undefined' && 
                typeof ref.pd_custom_vat_undue_amount === 'undefined') {
                needs_population = true;
            }
        }
    });
    
    if (needs_population) {
        console.log('Thai tax fields missing for new Payment Entry, fetching...');
        populate_thai_tax_fields_after_fetch(frm);
    } else {
        // Fields are already populated by server, just refresh and calculate totals
        frm.refresh_field('references');
        
        // Force refresh Check fields to ensure proper display
        refresh_thai_tax_check_fields(frm);
        
        calculate_thai_tax_totals(frm);
    }
}
/**
 * Force refresh checkboxes in the Thai tax section to ensure proper display
 */
function refresh_thai_tax_check_fields(frm) {
    const check_fields = [
        'pd_custom_apply_thai_wht_compliance_details',
        'pd_custom_subject_to_wht_details',
        'pd_custom_wht_certificate_required',
        'pd_custom_wht_certificate_required_details',
        'pd_custom_subject_to_retention',
        'pd_custom_subject_to_retention_details'
    ];
    check_fields.forEach(fieldname => {
        if (frm.fields_dict[fieldname]) {
            frm.fields_dict[fieldname].refresh();
        }
    });
    // Refresh the section if it exists
    if (frm.fields_dict.pd_custom_wht_preview_section) {
        frm.fields_dict.pd_custom_wht_preview_section.refresh();
    }
}

function fetch_and_populate_thai_tax_fields(frm, row) {
    /**
     * Fetch Thai tax fields for a specific reference row
     */
    if (row.reference_doctype === 'Sales Invoice' && row.reference_name) {
        fetch_thai_tax_fields(row.reference_doctype, row.reference_name)
            .then(data => {
                if (data) {
                    // Map API response fields to Payment Entry Reference fields (corrected mapping)
                    row.pd_custom_has_retention = data.has_retention || 0;
                    row.pd_custom_retention_amount = data.retention_amount || 0;
                    row.pd_custom_retention_percentage = data.retention || 0;
                    row.pd_custom_wht_amount = data.wht_amount || 0;
                    row.pd_custom_wht_percentage = data.wht || 0;
                    row.pd_custom_vat_undue_amount = data.vat_undue || 0;
                    
                    calculate_net_payable_for_row(row);
                    frm.refresh_field('references');
                    calculate_thai_tax_totals(frm);
                }
            });
    }
}

function fetch_thai_tax_fields(invoice_type, invoice_name) {
    /**
     * Fetch Thai tax details from server
     */
    console.log('📞 API call to fetch Thai tax details:', {
        method: 'print_designer.custom.payment_entry_thai_tax_population.get_invoice_thai_tax_details',
        invoice_type: invoice_type,
        invoice_name: invoice_name
    });

    return frappe.call({
        method: 'print_designer.custom.payment_entry_thai_tax_population.get_invoice_thai_tax_details',
        args: {
            invoice_type: invoice_type,
            invoice_name: invoice_name
        }
    }).then(r => {
        console.log('📨 API response for', invoice_name, ':', r);
        if (r.message) {
            console.log('✅ Thai tax data extracted:', r.message);
            return r.message;
        }
        console.log('⚠️ No message in API response for', invoice_name);
        return null;
    }).catch(error => {
        console.error('❌ API call failed for', invoice_name, ':', error);
        return null;
    });
}

function calculate_net_payable_for_row(row) {
    /**
     * Calculate net payable amount for a reference row
     */
    console.log('💰 Calculating net payable for reference:', row.reference_name || 'Unknown');
    let net_payable = row.allocated_amount || 0;
    console.log('💵 Starting amount:', net_payable);

    if (row.pd_custom_retention_amount) {
        console.log('📉 Subtracting retention:', row.pd_custom_retention_amount);
        net_payable -= row.pd_custom_retention_amount;
    }

    if (row.pd_custom_wht_amount) {
        console.log('📉 Subtracting WHT:', row.pd_custom_wht_amount);
        net_payable -= row.pd_custom_wht_amount;
    }

    row.pd_custom_net_payable_amount = net_payable;
    console.log('✅ Final net payable amount:', net_payable);
}

function calculate_thai_tax_totals(frm) {
    /**
     * Calculate total Thai tax amounts across all references
     */
    console.log('🧮 =========================== CALCULATE THAI TAX TOTALS START ===========================');
    console.log('🧮 Calculating Thai tax totals for form:', frm.doc.name || 'New');
    console.log('📊 Form docstatus:', frm.doc.docstatus, '(0=Draft, 1=Submitted, 2=Cancelled)');
    console.log('💳 Payment type:', frm.doc.payment_type);
    console.log('💰 Paid amount:', frm.doc.paid_amount);
    console.log('💰 Total allocated amount:', frm.doc.total_allocated_amount);

    try {
        // DEBUG: Check field visibility status
        console.log('🔍 Checking pd_custom_wht_preview_section field visibility:');
        const thai_section_fields = [
            'pd_custom_vat_treatment_details', 'pd_custom_subject_to_wht_details', 'pd_custom_wht_income_type_details', 'pd_custom_wht_description_details',
            'pd_custom_wht_certificate_required_details', 'pd_custom_net_total_after_wht_details', 'pd_custom_net_total_after_wht_words_details',
            'pd_custom_wht_note_details', 'pd_custom_subject_to_retention_details', 'pd_custom_net_after_wht_retention_details',
            'pd_custom_net_after_wht_retention_words_details', 'pd_custom_retention_note_details'
        ];
        thai_section_fields.forEach(fieldname => {
            const field = frm.fields_dict[fieldname];
            if (field) {
                // Simple visibility check without eval
                const is_visible = !field.df.hidden;
                console.log(`   📋 ${fieldname}: ${is_visible ? '✅ VISIBLE' : '❌ HIDDEN'} (depends_on: ${field.df.depends_on || 'none'})`);
            } else {
                console.log(`   ❓ ${fieldname}: FIELD NOT FOUND`);
            }
        });
    } catch(e) {
        console.error('Error checking field visibility:', e);
    }

    let total_retention = 0;
    let total_wht = 0;
    let total_vat_undue = 0;
    let total_base_net = 0;  // Track total base amount (excluding VAT)
    let has_thai_taxes = false;

    if (frm.doc.references) {
        console.log('📋 Processing', frm.doc.references.length, 'references for totals');
        frm.doc.references.forEach(function(ref, idx) {
            console.log(`📄 Reference ${idx + 1} (${ref.reference_name}):`, {
                retention: ref.pd_custom_retention_amount,
                wht: ref.pd_custom_wht_amount,
                vat_undue: ref.pd_custom_vat_undue_amount,
                base_net_total: ref.pd_custom_base_net_total
            });

            if (ref.pd_custom_retention_amount) {
                total_retention += ref.pd_custom_retention_amount;
                has_thai_taxes = true;
            }

            if (ref.pd_custom_wht_amount) {
                total_wht += ref.pd_custom_wht_amount;
                has_thai_taxes = true;
            }

            if (ref.pd_custom_vat_undue_amount) {
                total_vat_undue += ref.pd_custom_vat_undue_amount;
                has_thai_taxes = true;
            }

            // Sum up base amounts for accurate tax base
            if (ref.pd_custom_base_net_total) {
                total_base_net += ref.pd_custom_base_net_total;
            }
        });

        console.log('📊 Calculated totals:', {
            total_retention: total_retention,
            total_wht: total_wht,
            total_vat_undue: total_vat_undue,
            has_thai_taxes: has_thai_taxes
        });
    } else {
        console.log('⚠️ No references found for totals calculation');
    }

    // ADDITIONAL: Check for header-level WHT amounts (Purchase Invoice → Payment Entry scenario)
    // If we don't have reference-level WHT amounts, check header fields
    if (total_wht === 0 && frm.doc.pd_custom_withholding_tax_amount) {
        total_wht = frm.doc.pd_custom_withholding_tax_amount;
        has_thai_taxes = true;
        console.log('📊 Using header-level WHT amount (Purchase Invoice scenario):', total_wht);
    }
    
    // Update summary fields if they exist (using correct field names)
    console.log('🔄 Updating Payment Entry summary fields');

    try {
        // Update Thai Tax Compliance tab fields
        if (frm.fields_dict.pd_custom_apply_withholding_tax) {
            console.log('✅ Setting apply_withholding_tax:', total_wht > 0 ? 1 : 0);
            frm.set_value('pd_custom_apply_withholding_tax', total_wht > 0 ? 1 : 0);
        }

        // Handle both field naming patterns - populate BOTH if they exist (mirror fields)
        if (frm.fields_dict.pd_custom_withholding_tax_amount) {
            console.log('🏛️ Setting pd_custom_withholding_tax_amount:', total_wht);
            frm.set_value('pd_custom_withholding_tax_amount', total_wht);
        }
        if (frm.fields_dict.pd_custom_withholding_tax_amount) {
            console.log('🏛️ Setting pd_custom_withholding_tax_amount (mirror field):', total_wht);
            frm.set_value('pd_custom_withholding_tax_amount', total_wht);
        }

        // Calculate tax base amount from base_net_total (amount before VAT)
        if (frm.fields_dict.pd_custom_tax_base_amount) {
            // Check if server already set a reasonable value (from Purchase Invoice hook)
            let current_tax_base = frm.doc.pd_custom_tax_base_amount || 0;
            let calculated_tax_base = 0;

            if (total_base_net > 0) {
                // Use accurate base amount from invoice
                calculated_tax_base = total_base_net;
            } else if (frm.doc.total_allocated_amount > 0) {
                // Fallback: calculate from allocated amount
                calculated_tax_base = frm.doc.total_allocated_amount - total_vat_undue;
            }

            // Prefer server-set value if it exists and is different from total_allocated_amount
            // (Server sets net_total, client calculates from allocated amount)
            let final_tax_base = calculated_tax_base;
            if (current_tax_base > 0 && current_tax_base !== frm.doc.total_allocated_amount) {
                console.log('💰 Using server-set tax_base_amount:', current_tax_base, '(preserving Purchase Invoice net_total)');
                final_tax_base = current_tax_base;
            } else if (calculated_tax_base > 0) {
                console.log('💰 Using calculated tax_base_amount:', calculated_tax_base, '(base_net:', total_base_net, ', allocated:', frm.doc.total_allocated_amount, ', VAT:', total_vat_undue, ')');
                final_tax_base = calculated_tax_base;
                frm.set_value('pd_custom_tax_base_amount', final_tax_base);
            }
        }

        if (frm.fields_dict.pd_custom_net_payment_amount) {
            const net_payment = (frm.doc.total_allocated_amount || 0) - total_wht - total_retention;
            console.log('💵 Setting net_payment_amount:', net_payment);
            frm.set_value('pd_custom_net_payment_amount', net_payment);
        }

        // Update Thai Ecosystem Preview fields
        // Use pd_custom_apply_thai_wht_compliance_details as source of truth
        // If compliance is applied, subject_to_wht should be True
        if (frm.fields_dict.pd_custom_subject_to_wht_details) {
            const new_value = frm.doc.pd_custom_apply_thai_wht_compliance_details === 1 ? 1 : 0;
            console.log('🏛️ Setting pd_custom_subject_to_wht_details:', new_value, '(current:', frm.doc.pd_custom_subject_to_wht_details, ')');
            frm.set_value('pd_custom_subject_to_wht_details', new_value);
        } else {
            console.log('❌ pd_custom_subject_to_wht_details field not found in form');
        }
        // Populate pd_custom_wht_description_details and pd_custom_net_total_after_wht_words_details from references
        if (frm.doc.references && frm.doc.references.length > 0) {
            // Collect pd_custom_wht_description_details values from all references
            let wht_descriptions = [];
            let net_totals_in_words = [];
            frm.doc.references.forEach(function(ref) {
                if (ref.reference_doctype === 'Sales Invoice' && ref.reference_name) {
                    // Get pd_custom_wht_description_details and pd_custom_net_total_after_wht_words_details from Sales Invoice
                    frappe.call({
                        method: 'print_designer.custom.payment_entry_thai_tax_population.get_invoice_thai_tax_details',
                        args: {
                            invoice_type: ref.reference_doctype,
                            invoice_name: ref.reference_name
                        },
                        callback: function(r) {
                            if (r.message) {
                                if (r.message.pd_custom_wht_description && wht_descriptions.indexOf(r.message.pd_custom_wht_description) === -1) {
                                    wht_descriptions.push(r.message.pd_custom_wht_description);
                                }
                                if (r.message.pd_custom_net_total_after_wht_words && net_totals_in_words.indexOf(r.message.pd_custom_net_total_after_wht_words) === -1) {
                                    net_totals_in_words.push(r.message.pd_custom_net_total_after_wht_words);
                                }
                                // Update the form fields with the first unique value
                                if (frm.fields_dict.pd_custom_wht_description_details && wht_descriptions.length > 0) {
                                    frm.set_value('pd_custom_wht_description_details', wht_descriptions[0]);
                                    console.log('📝 Setting pd_custom_wht_description_details:', wht_descriptions[0]);
                                }
                                if (frm.fields_dict.pd_custom_net_total_after_wht_words_details && net_totals_in_words.length > 0) {
                                    frm.set_value('pd_custom_net_total_after_wht_words_details', net_totals_in_words[0]);
                                    console.log('📝 Setting pd_custom_net_total_after_wht_words_details:', net_totals_in_words[0]);
                                }
                            }
                        }
                    });
                }
            });
        }
        if (frm.fields_dict.pd_custom_subject_to_retention_details) {
            // For Purchase Invoice scenario: Check header-level retention fields first
            // This preserves values set by server-side Python code
            const header_retention_amount = frm.doc.pd_custom_retention_amount_details || 0;
            const header_has_retention = frm.doc.pd_custom_subject_to_retention_details || 0;
            let new_value;
            if (header_retention_amount > 0 || header_has_retention === 1) {
                // Header-level retention exists (Purchase Invoice scenario)
                // Preserve the server-set checkbox value
                new_value = 1;
                console.log('📝 Preserving server-set pd_custom_subject_to_retention_details: 1 (header retention_amount:', header_retention_amount, ')');
            } else if (total_retention > 0) {
                // Reference-level retention exists (Sales Invoice scenario)
                new_value = 1;
                console.log('📝 Setting pd_custom_subject_to_retention_details: 1 (reference-level total_retention:', total_retention, ')');
            } else {
                // No retention at all
                new_value = 0;
                console.log('📝 Setting pd_custom_subject_to_retention_details: 0 (no retention found)');
            }
            frm.set_value('pd_custom_subject_to_retention_details', new_value);
        } else {
            console.log('❌ pd_custom_subject_to_retention_details field not found in form');
        }
        // Only update Net Total after WHT if compliance is NOT active (preserve PI values when active)
        if (frm.fields_dict.pd_custom_net_total_after_wht_details && frm.doc.pd_custom_apply_thai_wht_compliance_details !== 1) {
            const pd_custom_net_total_after_wht = (frm.doc.total_allocated_amount || 0) - total_wht;
            console.log('💵 Setting pd_custom_net_total_after_wht_details:', pd_custom_net_total_after_wht, '(current:', frm.doc.pd_custom_net_total_after_wht_details, ')');
            frm.set_value('pd_custom_net_total_after_wht_details', pd_custom_net_total_after_wht);
        } else if (frm.fields_dict.pd_custom_net_total_after_wht_details) {
            console.log('💵 Skipping pd_custom_net_total_after_wht_details update - preserving PI value:', frm.doc.pd_custom_net_total_after_wht_details);
        } else {
            console.log('❌ pd_custom_net_total_after_wht_details field not found in form');
        }
        // Only update Net Total after WHT AND Retention if compliance is NOT active
        if (frm.fields_dict.pd_custom_net_after_wht_retention_details && frm.doc.pd_custom_apply_thai_wht_compliance_details !== 1) {
            // Get retention amount using the same pattern as retention checkbox
            // Priority 1: Header-level retention (Purchase Invoice scenario)
            const header_retention_amount = frm.doc.pd_custom_retention_amount_details || 0;
            // Priority 2: Reference-level retention (Sales Invoice scenario)
            let retention_amount = header_retention_amount;
            if (retention_amount === 0) {
                retention_amount = total_retention;
            }
            // Calculate: Net Total after WHT and Retention = Net Total after WHT - Retention Amount
            const pd_custom_net_total_after_wht = (frm.doc.total_allocated_amount || 0) - total_wht;
            const pd_custom_net_after_wht_retention = pd_custom_net_total_after_wht - retention_amount;
            console.log('💵 Calculating pd_custom_net_after_wht_retention_details:');
            console.log('   📊 total_allocated_amount:', frm.doc.total_allocated_amount);
            console.log('   📊 total_wht:', total_wht);
            console.log('   📊 pd_custom_net_total_after_wht:', pd_custom_net_total_after_wht);
            console.log('   📊 header_retention_amount:', header_retention_amount);
            console.log('   📊 reference_retention_amount:', total_retention);
            console.log('   📊 final_retention_amount:', retention_amount);
            console.log('   💰 pd_custom_net_after_wht_retention_details:', pd_custom_net_after_wht_retention);
            console.log('   📋 current value:', frm.doc.pd_custom_net_after_wht_retention_details);
            frm.set_value('pd_custom_net_after_wht_retention_details', pd_custom_net_after_wht_retention);
        } else if (frm.fields_dict.pd_custom_net_after_wht_retention_details) {
            console.log('💵 Skipping pd_custom_net_after_wht_retention_details update - preserving PI value:', frm.doc.pd_custom_net_after_wht_retention_details);
        } else {
            console.log('❌ pd_custom_net_after_wht_retention_details field not found in form');
        }
    } catch(e) {
        console.error('Error updating Payment Entry summary fields:', e);
    }
};
