frappe.listview_settings['Signature Basic Information'] = {
    onload: function(listview) {
        // Add a button to the list view to refresh the stats
        listview.page.add_inner_button(__('Refresh Stats'), function() {
            update_signature_stats(listview);
        });

        // Initial update of the stats
        update_signature_stats(listview);
    }
};

function update_signature_stats(listview) {
    // Fetch the signature statistics from the server
    frappe.call({
        method: 'print_designer.api.signature_sync.get_signature_stats',
        callback: function(r) {
            if (r.message) {
                // Update the total signatures count
                let total_signatures_badge = $('#total-signatures');
                if (total_signatures_badge.length) {
                    total_signatures_badge.text(r.message.total_signatures || 0);
                }

                // Update the company stamps count
                let company_stamps_badge = $('#company-stamps');
                if (company_stamps_badge.length) {
                    company_stamps_badge.text(r.message.company_stamps || 0);
                }

                // Update the active signatures count
                let active_signatures_badge = $('#active-signatures');
                if (active_signatures_badge.length) {
                    active_signatures_badge.text(r.message.active_signatures || 0);
                }
            }
        }
    });
}
