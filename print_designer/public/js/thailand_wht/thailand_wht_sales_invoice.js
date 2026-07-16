// Thailand Withholding Tax Client Script for Sales Invoice
// ENHANCED DEBUGGING: Tracking form dirty state and field changes for Linear BUN-6

console.log("🔧 Sales Invoice Client Script Loading - Enhanced Debug Mode for BUN-6...");

// Global tracking variables
let originalDoc = {};
let trackingChanges = false;

// Enhanced change tracking with focus on dirty-state triggers
function trackFieldChanges(frm, context) {
    const changes = {};
    const currentFields = JSON.stringify(frm.doc);
    const originalFields = JSON.stringify(originalDoc);
    
    if (currentFields !== originalFields && Object.keys(originalDoc).length > 0) {
        // Find specific field differences
        for (let field in frm.doc) {
            if (frm.doc[field] !== originalDoc[field]) {
                changes[field] = {
                    old: originalDoc[field],
                    new: frm.doc[field]
                };
            }
        }
        
        console.log(`🔍 ${context} - Field changes detected:`, changes);
        console.log(`🔍 ${context} - __unsaved:`, frm.doc.__unsaved);
        console.log(`🔍 ${context} - is_dirty():`, frm.is_dirty());
        
        // Special focus on critical fields that affect submit button logic
        const criticalFields = ['__unsaved', 'docstatus', '__islocal', 'modified', 'modified_by', 'owner', 'creation'];
        const criticalChanges = {};
        for (let field of criticalFields) {
            if (field in changes) {
                criticalChanges[field] = changes[field];
            }
        }
        if (Object.keys(criticalChanges).length > 0) {
            console.log(`🚨 ${context} - CRITICAL field changes that affect submit logic:`, criticalChanges);
        }
        
        // Track calculated/computed fields that might trigger dirty state
        const calculatedFields = ['grand_total', 'total', 'net_total', 'outstanding_amount', 'paid_amount'];
        const calculatedChanges = {};
        for (let field of calculatedFields) {
            if (field in changes) {
                calculatedChanges[field] = changes[field];
            }
        }
        if (Object.keys(calculatedChanges).length > 0) {
            console.log(`💰 ${context} - Calculated field changes:`, calculatedChanges);
        }
    }
    
    return Object.keys(changes).length > 0;
}

// Monkey patch to track when form becomes dirty
function monitorFormDirtyState(frm) {
    if (frm.set_dirty_original) return; // Already patched
    
    frm.set_dirty_original = frm.set_dirty;
    frm.set_dirty = function() {
        console.log("🚨 set_dirty() called from:", new Error().stack.split('\n')[1]);
        console.log("🚨 Current dirty state:", this.is_dirty());
        return frm.set_dirty_original.apply(this, arguments);
    };
}

frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        console.log("📋 Sales Invoice onload triggered", {
            docname: frm.doc.name,
            docstatus: frm.doc.docstatus,
            is_new: frm.is_new(),
            status: frm.doc.status
        });
        
        // Store original document state
        originalDoc = JSON.parse(JSON.stringify(frm.doc));
        monitorFormDirtyState(frm);
        
        // Fetch company Thai fields on form load if company is already set
        if (frm.doc.company) {
            setTimeout(() => pd_fetch_company_thai_fields(frm), 100);
        }
    },
    
    refresh: function(frm) {
        console.log("🔄 Sales Invoice refresh triggered", {
            docname: frm.doc.name,
            docstatus: frm.doc.docstatus,
            is_new: frm.is_new(),
            status: frm.doc.status,
            is_dirty: frm.is_dirty(),
            country: frm.doc.pd_custom_company_country,
            taxes_count: frm.doc.taxes ? frm.doc.taxes.length : 0,
            toolbar_buttons: frm.page.btn_primary ? frm.page.btn_primary.text() : 'No primary button'
        });
        
        // Log button state
        if (frm.page.btn_primary) {
            console.log("🔘 Primary button text:", frm.page.btn_primary.text());
            console.log("🔘 Primary button visible:", frm.page.btn_primary.is(':visible'));
        }
        
        // Check for submit button
        const submitBtn = frm.page.wrapper.find('.btn-primary:contains("Submit")');
        const saveBtn = frm.page.wrapper.find('.btn-primary:contains("Save")');
        console.log("🔍 Submit button found:", submitBtn.length > 0);
        console.log("🔍 Save button found:", saveBtn.length > 0);
        
        // Track any changes during refresh
        if (trackingChanges) {
            trackFieldChanges(frm, "REFRESH");
        }
        
        // ADDED: Populate Company fields on form load if company is set but fields are undefined
        // Check for undefined specifically, not falsy values (0 is valid)
        if (frm.doc.company && 
            frm.doc.thailand_service_business === undefined && 
            frm.doc.construction_service === undefined) {
            // Trigger company event to populate fields
            frm.events.company(frm);
        }
        
        // Calculate WHT amounts
        pd_calculate_wht_amounts(frm);
        console.log('🇹🇭 WHT calculated on refresh');
    },
    
    before_save: function(frm) {
        console.log("💾 Before save - storing current state");
        originalDoc = JSON.parse(JSON.stringify(frm.doc));
        trackingChanges = false;
    },
    
    after_save: function(frm) {
        console.log("💾 Sales Invoice after_save triggered", {
            docname: frm.doc.name,
            docstatus: frm.doc.docstatus,
            status: frm.doc.status,
            is_dirty: frm.is_dirty(),
            __unsaved: frm.doc.__unsaved
        });
        
        // Start tracking changes immediately after save
        trackingChanges = true;
        originalDoc = JSON.parse(JSON.stringify(frm.doc));
        
        // Enhanced monitoring with immediate dirty state detection
        let checkCount = 0;
        let wasClean = !frm.is_dirty();
        
        const checkInterval = setInterval(() => {
            checkCount++;
            const isDirty = frm.is_dirty();
            const hasChanges = trackFieldChanges(frm, `CHECK_${checkCount}`);
            
            // Detect the exact moment form becomes dirty
            if (wasClean && isDirty) {
                console.log(`🚨 DIRTY STATE TRANSITION DETECTED on check ${checkCount}!`);
                console.log("🚨 Form just became dirty - investigating...");
                console.log("   - Previous state: CLEAN");
                console.log("   - Current state: DIRTY");
                console.log("   - frm.doc.__unsaved:", frm.doc.__unsaved);
                console.log("   - Button text:", frm.page.btn_primary ? frm.page.btn_primary.text() : 'No button');
                
                // Deep investigation of what changed
                console.log("🔍 Deep analysis of dirty trigger:");
                console.log("   - frm.dirty_fields:", frm.dirty_fields);
                console.log("   - Document changed fields:", hasChanges ? "YES" : "NO");
                
                // Check for submit conditions
                const canSubmit = (
                    frm.doc.docstatus === 0 &&
                    !frm.doc.__islocal &&
                    !frm.doc.__unsaved &&
                    frm.perm[0].submit
                );
                console.log("   - Can submit conditions:", {
                    docstatus_0: frm.doc.docstatus === 0,
                    not_local: !frm.doc.__islocal,
                    not_unsaved: !frm.doc.__unsaved,
                    has_submit_perm: frm.perm[0].submit,
                    final_result: canSubmit
                });
            }
            wasClean = !isDirty;
            
            console.log(`⏰ Post-save check ${checkCount}:`, {
                timestamp: new Date().toISOString(),
                docstatus: frm.doc.docstatus,
                is_dirty: isDirty,
                has_field_changes: hasChanges,
                button_text: frm.page.btn_primary ? frm.page.btn_primary.text() : 'No button',
                __unsaved: frm.doc.__unsaved
            });
            
            // Stop checking after 10 seconds or if we find the issue
            if (checkCount >= 20 || (isDirty && hasChanges)) {
                clearInterval(checkInterval);
                console.log(`🏁 Stopped monitoring after ${checkCount} checks`);
                trackingChanges = false;
            }
        }, 500);
    },
    
    on_submit: function(frm) {
        console.log("🚀 Sales Invoice on_submit triggered", {
            docname: frm.doc.name,
            docstatus: frm.doc.docstatus,
            status: frm.doc.status
        });
    },
    
    // Handle WHT income type changes for description updates (language-aware)
    pd_custom_wht_income_type: function(frm) {
        if (frm.doc.pd_custom_wht_income_type && frm.doc.pd_custom_subject_to_wht) {
            const lang = frappe.boot.lang || 'en';
            const desc_field = lang === 'th' ? 'income_description_th' : 'income_description';
            const category_field = lang === 'th' ? 'income_category_th' : 'income_category';

            frappe.db.get_value('Thai WHT Income Type', frm.doc.pd_custom_wht_income_type,
                [desc_field, category_field, 'tax_rate'], function(r) {
                    if (r) {
                        const category = r[category_field] || '';
                        const description = r[desc_field] || '';
                        const display_text = category ? `${category} - ${description}` : description;
                        frm.set_value('pd_custom_wht_description', display_text);
                    }
                });
        } else if (!frm.doc.pd_custom_wht_income_type) {
            frm.set_value('pd_custom_wht_description', '');
        }
    },

    // Fetch company Thai fields manually (fetch_from doesn't work reliably for hidden fields)
    // This populates hidden fields for depends_on evaluation
    company: function(frm) {
        pd_fetch_company_thai_fields(frm);
    },
    
    // Override tax template charge_type for Thai companies
    // When tax template is selected, set charge_type to 'Thai Tax Compliance'
    taxes_and_charges: function(frm) {
        console.log('🇹🇭 Thailand WHT: taxes_and_charges event triggered');
        pd_override_thai_tax_charge_type(frm);
    }
});

// Hook into Sales Taxes and Charges child table
// Recalculate WHT when any tax row changes
frappe.ui.form.on('Sales Taxes and Charges', {
    charge_type: function(frm, cdt, cdn) {
        const tax_row = locals[cdt][cdn];
        console.log('🇹🇭 Thailand WHT: charge_type changed to:', tax_row.charge_type);
        // Calculate WHT amounts
        pd_calculate_wht_amounts(frm);
    }
});

// Fetch company Thai fields and populate hidden fields for depends_on
function pd_fetch_company_thai_fields(frm) {
    if (!frm.doc.company) return;
    
    frappe.db.get_value('Company', frm.doc.company, [
        'thailand_service_business',
        'construction_service',
        'country'
    ]).then(r => {
        if (r && r.message) {
            // Populate hidden fields for depends_on evaluation
            frm.doc.pd_custom_company_thailand_service_business = r.message.thailand_service_business || 0;
            frm.doc.pd_custom_company_construction_service = r.message.construction_service || 0;
            frm.doc.pd_custom_company_country = r.message.country;
            
            console.log('Thailand WHT: Company fields fetched', {
                thailand_service_business: frm.doc.pd_custom_company_thailand_service_business,
                construction_service: frm.doc.pd_custom_company_construction_service,
                country: frm.doc.pd_custom_company_country
            });
            
            // Refresh fields to trigger depends_on evaluation
            frm.refresh_fields(['pd_custom_company_thailand_service_business', 'pd_custom_company_construction_service', 'pd_custom_company_country']);
        }
    });
}

// Override tax charge_type for Thai companies
// When tax template is applied, set charge_type to 'Thai Tax Compliance'
// The backend (taxes_and_totals_thai_wht.py) handles the negation
function pd_override_thai_tax_charge_type(frm) {
    console.log('🇹🇭 Thailand WHT: pd_override_thai_tax_charge_type called');
    console.log('  - company:', frm.doc.company);
    console.log('  - country:', frm.doc.pd_custom_company_country);
    console.log('  - taxes count:', frm.doc.taxes ? frm.doc.taxes.length : 0);
    
    if (!frm.doc.company || !frm.doc.taxes || frm.doc.taxes.length === 0) {
        console.log('  - SKIP: No company or taxes');
        return;
    }
    
    // Check if company is Thailand
    if (frm.doc.pd_custom_company_country !== 'Thailand') {
        console.log('  - SKIP: Not Thailand company');
        return;
    }
    
    // Override charge_type for all tax rows
    let overridden = 0;
    frm.doc.taxes.forEach(function(tax, idx) {
        console.log(`  - Tax row ${idx}: charge_type='${tax.charge_type}', amount=${tax.tax_amount}`);
        // Only override percentage-based taxes (On Net Total, Actual)
        if (tax.charge_type && !['Thai Tax Compliance', 'On Previous Row Amount', 'On Previous Row Total', 'On Item Quantity'].includes(tax.charge_type)) {
            // Store original charge_type
            if (!tax.custom_original_charge_type) {
                tax.custom_original_charge_type = tax.charge_type;
            }
            // Set to Thai Tax Compliance
            tax.charge_type = 'Thai Tax Compliance';
            console.log(`  - Tax row ${idx}: OVERRIDE to 'Thai Tax Compliance'`);
            overridden++;
        }
    });
    
    if (overridden > 0) {
        console.log('🇹🇭 Thailand WHT: Set charge_type to Thai Tax Compliance for', overridden, 'tax rows');
        frm.refresh_field('taxes');
    }
}

// Monitor any field value changes
$(document).on('change', '[data-fieldname]', function() {
    if (trackingChanges) {
        const fieldname = $(this).data('fieldname');
        console.log("🔧 Field change detected:", fieldname, "New value:", $(this).val());
    }
});

// Monitor API calls that might affect the form
const originalCall = frappe.call;
frappe.call = function(opts) {
    if (trackingChanges && opts.method) {
        console.log("📡 API call during tracking:", opts.method, opts.args || '');
    }
    return originalCall.apply(this, arguments);
};

// Monitor frappe.model events that might trigger dirty state
function monitorModelEvents() {
    // Override frappe.model.set_value to track field changes
    if (!frappe.model.set_value_original) {
        frappe.model.set_value_original = frappe.model.set_value;
        frappe.model.set_value = function(doctype, docname, fieldname, value, skip_dirty_trigger) {
            if (trackingChanges && doctype === 'Sales Invoice') {
                console.log(`🔧 frappe.model.set_value called:`, {
                    doctype, docname, fieldname, 
                    value: value, 
                    skip_dirty_trigger: skip_dirty_trigger,
                    stack: new Error().stack.split('\n')[2]
                });
            }
            return frappe.model.set_value_original.apply(this, arguments);
        };
    }
    
    // Monitor when __unsaved gets set
    if (!frappe.model.set_unsaved_original) {
        const originalSetValue = frappe.model.set_value;
        // This will catch when __unsaved specifically gets modified
    }
}

// Initialize monitoring
monitorModelEvents();

// Expose functions globally for use by frappe.ui.form.on
window.pd_fetch_company_thai_fields = pd_fetch_company_thai_fields;
window.pd_calculate_wht_amounts = pd_calculate_wht_amounts;

// Calculate WHT amounts based on total and tax rate
// pd_custom_withholding_tax_amount = total * pd_custom_withholding_tax_pct / 100
// pd_custom_net_total_after_wht = total - pd_custom_withholding_tax_amount
function pd_calculate_wht_amounts(frm) {
    // Get values
    const total = frm.doc.total || 0;
    const whtPct = frm.doc.pd_custom_withholding_tax_pct || 0;
    
    // Calculate WHT amount = total * wht_pct / 100
    const whtAmount = total * whtPct / 100;
    
    // Calculate net total after WHT = total - WHT amount
    const netTotalAfterWHT = total - whtAmount;
    
    // Set the custom fields (skip dirty trigger for calculated fields)
    frm.set_value('pd_custom_withholding_tax_amount', whtAmount, null, true);
    frm.set_value('pd_custom_net_total_after_wht', netTotalAfterWHT, null, true);
    
    // Call server to convert to words
    if (netTotalAfterWHT > 0) {
        frappe.call({
            method: 'print_designer.thailand_wht_sales_invoice.calculate_net_total_words',
            args: { amount: netTotalAfterWHT, currency: frm.doc.currency },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('pd_custom_net_total_after_wht_words', r.message, null, true);
                    frm.refresh_fields(['pd_custom_net_total_after_wht_words']);
                }
            }
        });
    } else {
        frm.set_value('pd_custom_net_total_after_wht_words', '', null, true);
        frm.refresh_fields(['pd_custom_net_total_after_wht_words']);
    }
}

// Convert number to Thai Baht words
function pd_number_to_thai_words(num) {
    const units = ['', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า'];
    const positions = ['', 'สิบ', 'ร้อย', 'พัน', 'หมื่น', 'แสน', 'ล้าน'];
    
    if (num === 0) return 'ศูนย์บาทถ้วน';
    
    num = Math.round(num * 100) / 100;
    const parts = num.toString().split('.');
    const intPart = parseInt(parts[0]);
    const decPart = parts[1] ? parseInt(parts[1].padEnd(2, '0').substring(0, 2)) : 0;
    
    let result = '';
    let numStr = intPart.toString();
    let len = numStr.length;
    
    for (let i = 0; i < len; i++) {
        const digit = parseInt(numStr[i]);
        const pos = len - i - 1;
        const posGroup = Math.floor(pos / 6);
        const posInGroup = pos % 6;
        
        if (digit !== 0) {
            if (posInGroup === 1 && digit === 2) {
                result += 'ยี่';
            } else if (posInGroup === 1 && digit === 1) {
                result += '';
            } else if (posInGroup === 0 && digit === 1 && len > 1) {
                result += 'เอ็ด';
            } else {
                result += units[digit];
            }
            result += positions[posInGroup];
        }
        
        if (posInGroup === 5 && posGroup > 0) {
            result += 'ล้าน';
        }
    }
    
    result += 'บาท';
    
    if (decPart > 0) {
        let decStr = decPart.toString().padStart(2, '0');
        for (let i = 0; i < 2; i++) {
            const digit = parseInt(decStr[i]);
            const pos = 1 - i;
            if (digit !== 0) {
                if (pos === 1 && digit === 2) {
                    result += 'ยี่';
                } else if (pos === 1 && digit === 1) {
                    result += '';
                } else if (pos === 0 && digit === 1 && decPart > 10) {
                    result += 'เอ็ด';
                } else {
                    result += units[digit];
                }
                result += positions[pos];
            }
        }
        result += 'สตางค์';
    } else {
        result += 'ถ้วน';
    }
    
    return result;
}

// NOTE: tax_withholding_category is auto-populated by ERPNext's get_item_details()
// which reads from item.sales_tax_withholding_category (standard ERPNext field)