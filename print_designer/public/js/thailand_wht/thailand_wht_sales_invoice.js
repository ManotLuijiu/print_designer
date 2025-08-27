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
    },
    
    refresh: function(frm) {
        console.log("🔄 Sales Invoice refresh triggered", {
            docname: frm.doc.name,
            docstatus: frm.doc.docstatus,
            is_new: frm.is_new(),
            status: frm.doc.status,
            is_dirty: frm.is_dirty(),
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
        
        // ADDED: Populate Company fields on form load if company is set but fields are empty
        if (frm.doc.company && !frm.doc.thailand_service_business && !frm.doc.construction_service) {
            // Trigger company event to populate fields
            frm.events.company(frm);
        }
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
    
    // Populate Company fields when company is selected - ADDED FOR FIELD VISIBILITY
    company: function(frm) {
        if (frm.doc.company) {
            // Get Company configuration and populate fields for depends_on visibility
            frappe.db.get_value('Company', frm.doc.company, [
                'thailand_service_business', 
                'construction_service'
            ]).then(r => {
                if (r.message) {
                    // Populate fields silently for depends_on conditions
                    frm.doc.thailand_service_business = r.message.thailand_service_business || 0;
                    frm.doc.construction_service = r.message.construction_service || 0;
                    
                    // Refresh the form to trigger depends_on evaluation
                    frm.refresh();
                    
                    console.log('Thailand WHT: Company fields populated', {
                        thailand_service_business: frm.doc.thailand_service_business,
                        construction_service: frm.doc.construction_service
                    });
                }
            });
        } else {
            // Clear fields when company is cleared
            frm.doc.thailand_service_business = 0;
            frm.doc.construction_service = 0;
            frm.refresh();
        }
    }
});

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

/*
Original Thailand WHT functionality disabled to prevent excessive API calls to:
- frappe.db.get_value('Company', company, 'thailand_service_business')

This was causing performance issues and interfering with form operations.
The Thailand WHT integration needs to be properly configured before re-enabling.
*/