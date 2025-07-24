// Copyright (c) 2024, Frappe Technologies Pvt Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Note Approval', {
	refresh: function(frm) {
		// Add custom buttons based on status
		if (frm.doc.status === "Pending") {
			frm.add_custom_button(__('View Approval Page'), function() {
				const approval_url = frm.call({
					method: 'get_approval_url',
					callback: function(r) {
						if (r.message) {
							window.open(r.message, '_blank');
						}
					}
				});
			}, __("Actions"));
			
			frm.add_custom_button(__('Copy Approval Link'), function() {
				frm.call({
					method: 'get_approval_url',
					callback: function(r) {
						if (r.message) {
							navigator.clipboard.writeText(r.message).then(function() {
								frappe.show_alert({
									message: __('Approval link copied to clipboard'),
									indicator: 'green'
								});
							});
						}
					}
				});
			}, __("Actions"));
		}
		
		// Add resend notification button
		if (frm.doc.status === "Approved") {
			frm.add_custom_button(__('Resend Notification'), function() {
				frm.call({
					method: 'send_approval_notification',
					callback: function(r) {
						frappe.show_alert({
							message: __('Notification sent successfully'),
							indicator: 'green'
						});
					}
				});
			}, __("Actions"));
		}
		
		// Add view delivery note button
		if (frm.doc.delivery_note) {
			frm.add_custom_button(__('View Delivery Note'), function() {
				frappe.set_route('Form', 'Delivery Note', frm.doc.delivery_note);
			});
		}
		
		// Set indicator based on status
		if (frm.doc.status === "Approved") {
			frm.dashboard.set_headline_alert('<div class="row"><div class="col-xs-12"><span class="indicator-pill green">Approved</span></div></div>');
		} else if (frm.doc.status === "Rejected") {
			frm.dashboard.set_headline_alert('<div class="row"><div class="col-xs-12"><span class="indicator-pill red">Rejected</span></div></div>');
		} else if (frm.doc.status === "Expired") {
			frm.dashboard.set_headline_alert('<div class="row"><div class="col-xs-12"><span class="indicator-pill orange">Expired</span></div></div>');
		} else {
			frm.dashboard.set_headline_alert('<div class="row"><div class="col-xs-12"><span class="indicator-pill yellow">Pending</span></div></div>');
		}
	},
	
	delivery_note: function(frm) {
		// Auto-populate customer mobile from delivery note
		if (frm.doc.delivery_note) {
			frappe.db.get_doc('Delivery Note', frm.doc.delivery_note).then(function(doc) {
				if (doc.contact_mobile && !frm.doc.customer_mobile) {
					frm.set_value('customer_mobile', doc.contact_mobile);
				}
			});
		}
	},
	
	status: function(frm) {
		// Update form based on status changes
		if (frm.doc.status === "Approved" && !frm.doc.approved_on) {
			frm.set_value('approved_on', frappe.datetime.now_datetime());
		}
	}
});

// Auto-refresh form every 30 seconds for pending approvals
frappe.ui.form.on('Delivery Note Approval', {
	refresh: function(frm) {
		if (frm.doc.status === "Pending" && !frm.is_new()) {
			// Set up auto-refresh for pending approvals
			if (frm.auto_refresh_interval) {
				clearInterval(frm.auto_refresh_interval);
			}
			
			frm.auto_refresh_interval = setInterval(function() {
				if (frm.doc.status === "Pending") {
					frm.reload_doc();
				} else {
					clearInterval(frm.auto_refresh_interval);
				}
			}, 30000); // Refresh every 30 seconds
		}
	},
	
	onload: function(frm) {
		// Clear auto-refresh on form unload
		$(window).on('beforeunload', function() {
			if (frm.auto_refresh_interval) {
				clearInterval(frm.auto_refresh_interval);
			}
		});
	}
});