// Retention handler - completely frontend API-free version
// All field visibility and calculations handled server-side

console.log('🔄 Retention script loaded - API-free version');

frappe.ui.form.on('Sales Invoice', {
  refresh: function(frm) {
    console.log('🔄 Retention: refresh event - field visibility handled server-side');
    // Field visibility is now controlled server-side via form script
    // No API calls needed in frontend
  },
  company: function(frm) {
    console.log('🏢 Retention: company changed - field visibility handled server-side');
    // Field visibility and calculations handled server-side
    // No API calls needed in frontend
  }
});

// Note: All API calls eliminated - company field checks and calculations moved server-side