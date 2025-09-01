/**
 * Payment Entry Thai Tax Enhancement
 * 
 * This script enhances the Payment Entry form to automatically populate
 * Thai tax fields when fetching outstanding invoices.
 */

frappe.ui.form.on('Payment Entry', {
    refresh: function(frm) {
        // Add custom logic after refresh
        if (!frm.is_new()) {
            populate_thai_tax_fields_for_existing_references(frm);
        } else {
            // For new Payment Entry (created from Sales Invoice via "Create > Payment")
            // Check if references are already populated and Thai tax fields are missing
            setTimeout(() => {
                populate_thai_tax_fields_for_new_payment_entry(frm);
            }, 500);
        }
    },
    
    validate: function(frm) {
        // Calculate totals before saving
        calculate_thai_tax_totals(frm);
    },
    
    references_add: function(frm, cdt, cdn) {
        // When a new reference is added manually
        const row = locals[cdt][cdn];
        if (row.reference_doctype && row.reference_name) {
            fetch_and_populate_thai_tax_fields(frm, row);
        }
    }
});

frappe.ui.form.on('Payment Entry Reference', {
    reference_name: function(frm, cdt, cdn) {
        // When reference name is set or changed
        const row = locals[cdt][cdn];
        if (row.reference_doctype && row.reference_name) {
            fetch_and_populate_thai_tax_fields(frm, row);
        }
    },
    
    allocated_amount: function(frm, cdt, cdn) {
        // Recalculate net payable when allocated amount changes
        const row = locals[cdt][cdn];
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
    if (!frm.doc.references || frm.doc.references.length === 0) {
        return;
    }
    
    let promises = [];
    
    frm.doc.references.forEach(function(ref) {
        if (ref.reference_doctype === 'Sales Invoice' && ref.reference_name) {
            promises.push(fetch_thai_tax_fields(ref.reference_doctype, ref.reference_name)
                .then(data => {
                    if (data) {
                        // Populate the fields
                        ref.pd_custom_has_retention = data.pd_custom_has_retention || 0;
                        ref.pd_custom_retention_amount = data.pd_custom_retention_amount || 0;
                        ref.pd_custom_retention_percentage = data.pd_custom_retention_percentage || 0;
                        ref.pd_custom_wht_amount = data.pd_custom_wht_amount || 0;
                        ref.pd_custom_wht_percentage = data.pd_custom_wht_percentage || 0;
                        ref.pd_custom_vat_undue_amount = data.pd_custom_vat_undue_amount || 0;
                        
                        // Calculate net payable
                        calculate_net_payable_for_row(ref);
                    }
                })
            );
        }
    });
    
    Promise.all(promises).then(() => {
        frm.refresh_field('references');
        calculate_thai_tax_totals(frm);
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

function fetch_and_populate_thai_tax_fields(frm, row) {
    /**
     * Fetch Thai tax fields for a specific reference row
     */
    if (row.reference_doctype === 'Sales Invoice' && row.reference_name) {
        fetch_thai_tax_fields(row.reference_doctype, row.reference_name)
            .then(data => {
                if (data) {
                    row.pd_custom_has_retention = data.pd_custom_has_retention || 0;
                    row.pd_custom_retention_amount = data.pd_custom_retention_amount || 0;
                    row.pd_custom_retention_percentage = data.pd_custom_retention_percentage || 0;
                    row.pd_custom_wht_amount = data.pd_custom_wht_amount || 0;
                    row.pd_custom_wht_percentage = data.pd_custom_wht_percentage || 0;
                    row.pd_custom_vat_undue_amount = data.pd_custom_vat_undue_amount || 0;
                    
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
    return frappe.call({
        method: 'print_designer.custom.payment_entry_thai_tax_population.get_invoice_thai_tax_details',
        args: {
            invoice_type: invoice_type,
            invoice_name: invoice_name
        }
    }).then(r => {
        if (r.message) {
            return r.message;
        }
        return null;
    });
}

function calculate_net_payable_for_row(row) {
    /**
     * Calculate net payable amount for a reference row
     */
    let net_payable = row.allocated_amount || 0;
    
    if (row.pd_custom_retention_amount) {
        net_payable -= row.pd_custom_retention_amount;
    }
    
    if (row.pd_custom_wht_amount) {
        net_payable -= row.pd_custom_wht_amount;
    }
    
    row.pd_custom_net_payable_amount = net_payable;
}

function calculate_thai_tax_totals(frm) {
    /**
     * Calculate total Thai tax amounts across all references
     */
    let total_retention = 0;
    let total_wht = 0;
    let total_vat_undue = 0;
    let has_thai_taxes = false;
    
    if (frm.doc.references) {
        frm.doc.references.forEach(function(ref) {
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
        });
    }
    
    // Update summary fields if they exist
    if (frm.fields_dict.pd_custom_has_thai_taxes) {
        frm.set_value('pd_custom_has_thai_taxes', has_thai_taxes ? 1 : 0);
    }
    
    if (frm.fields_dict.pd_custom_total_retention_amount) {
        frm.set_value('pd_custom_total_retention_amount', total_retention);
    }
    
    if (frm.fields_dict.pd_custom_total_wht_amount) {
        frm.set_value('pd_custom_total_wht_amount', total_wht);
    }
    
    if (frm.fields_dict.pd_custom_total_vat_undue_amount) {
        frm.set_value('pd_custom_total_vat_undue_amount', total_vat_undue);
    }
    
    if (frm.fields_dict.pd_custom_has_retention) {
        frm.set_value('pd_custom_has_retention', total_retention > 0 ? 1 : 0);
    }
    
    if (frm.fields_dict.pd_custom_net_payment_after_retention) {
        frm.set_value('pd_custom_net_payment_after_retention', 
            (frm.doc.total_allocated_amount || 0) - total_retention);
    }
}

function refresh_thai_tax_check_fields(frm) {
    /**
     * Force refresh Thai tax Check fields to ensure proper display
     * Check fields with value 1 sometimes don't display as checked immediately
     */
    if (!frm.doc.references || frm.doc.references.length === 0) {
        return;
    }
    
    frm.doc.references.forEach(function(ref, idx) {
        if (ref.reference_doctype === 'Sales Invoice' && ref.reference_name) {
            // Force trigger change events for Check fields
            if (typeof ref.pd_custom_has_retention !== 'undefined') {
                // Trigger field refresh by setting the value explicitly
                frappe.model.set_value('Payment Entry Reference', ref.name, 'pd_custom_has_retention', ref.pd_custom_has_retention);
            }
        }
    });
    
    // Additional full form refresh to ensure UI updates
    setTimeout(() => {
        frm.refresh_field('references');
    }, 100);
}