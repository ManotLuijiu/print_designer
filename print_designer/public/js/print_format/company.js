/**
 * Company DocType Client Script
 * Adds Company Stamps and Signatures preview in a dedicated tab
 */
/** biome-ignore-all lint/complexity/useArrowFunction: <explanation> */

/**
 * Professional approach: Wait for ERPNext tabs to be fully rendered
 * Uses polling with exponential backoff instead of guessing timeout values
 */
function waitForTabsToRender(frm, maxAttempts = 15) {
	return new Promise((resolve, reject) => {
		let attempts = 0;

		const checkTabs = () => {
			attempts++;
			const expectedTabs = [
				"#company-accounts_tab",
				"#company-stock_tab",
				"#company-dashboard_tab",
			];
			const missingTabs = expectedTabs.filter(
				(tab) => frm.page.wrapper.find(tab).length === 0,
			);

			if (missingTabs.length === 0) {
				console.log(`✅ All tabs ready after ${attempts} attempts`);
				resolve();
				return;
			}

			if (attempts >= maxAttempts) {
				reject(
					new Error(
						`Tabs not ready after ${attempts} attempts. Missing: ${missingTabs.join(", ")}`,
					),
				);
				return;
			}

			// Exponential backoff: 50ms, 100ms, 200ms, 400ms, 800ms, max 1000ms
			const delay = Math.min(50 * Math.pow(2, attempts - 1), 1000);
			console.log(
				`⏳ Attempt ${attempts}: Waiting ${delay}ms for tabs:`,
				missingTabs,
			);
			setTimeout(checkTabs, delay);
		};

		// Start checking immediately
		checkTabs();
	});
}

frappe.ui.form.on("Company", {
	refresh: function (frm) {
		// Stamps & Signatures tab has been removed - functionality disabled
		console.log("ℹ️ Stamps & Signatures tab functionality has been disabled");
	},
});

function add_stamps_and_signatures_content(frm) {
	console.log("🚀 add_stamps_and_signatures_content called");

	// Check if content already exists
	if (frm.page.wrapper.find(".stamps-signatures-content").length > 0) {
		console.log("⚠️ Content already exists, skipping");
		return;
	}

	// Professional approach: Wait for tabs to be rendered using polling with timeout
	waitForTabsToRender(frm)
		.then(() => {
			console.log("🔍 All tabs ready, proceeding with stamps tab setup...");

			// Find the stamps tab (simplified)
			let stampsTab = frm.page.wrapper.find("#company-stamps_signatures_tab");
			console.log("🔍 Stamps tab:", stampsTab);

			if (stampsTab.length === 0) {
				stampsTab = frm.page.wrapper
					.find('[data-fieldname="stamps_signatures_tab"]')
					.closest(".tab-pane");
			}

			if (stampsTab.length === 0) {
				stampsTab = frm.page.wrapper.find(".tab-pane").filter(function () {
					return this.id && this.id.includes("stamps_signatures_tab");
				});
			}

			if (stampsTab.length === 0) {
				console.error("❌ Stamps & Signatures tab not found!");
				console.log(
					"Available tabs:",
					frm.page.wrapper
						.find(".tab-pane")
						.map(function () {
							return this.id;
						})
						.get(),
				);
				return;
			}

			// Move the stamps tab to be the last tab and make it visible
			let tabNavItem = frm.page.wrapper
				.find('a[href="#company-stamps_signatures_tab"]')
				.closest("li");
			let dashboardTabNavItem = frm.page.wrapper
				.find('a[href="#company-dashboard_tab"]')
				.closest("li");

			if (tabNavItem.length > 0 && dashboardTabNavItem.length > 0) {
				tabNavItem.insertAfter(dashboardTabNavItem);
				console.log("✅ Moved stamps tab to last position");
			}

			// Remove the 'hide' class to make the tab visible
			stampsTab.removeClass('hide');
			console.log("✅ Stamps tab made visible (removed 'hide' class)");

			// Also ensure the tab navigation item is visible
			if (tabNavItem.length > 0) {
				tabNavItem.removeClass('hide').show();
				console.log("✅ Tab navigation item made visible");
			}

			// Add our content directly to the tab pane - Fixed double div structure
			const content_wrapper = $(`
            <div class="stamps-signatures-content">
                <div class="row">
                    <div class="col-md-12">
                        <div id="company-stamps_signatures_tab_card" class="card">
                            <div id="company-stamps_signatures_tab_card_header" class="card-header d-flex justify-content-between align-items-center" 
                                 style="padding: 12px 20px;">
                                <h5 class="card-title mb-0">
                                    <i class="fa fa-certificate" style="margin-right: 8px;"></i>
                                    Company Stamps & Signatures Preview
                                </h5>
                                <button class="btn btn-sm refresh-preview-btn">
                                    <i class="fa fa-refresh"></i> Refresh
                                </button>
                            </div>
                            <div id="company-stamps_signatures_tab_card_body" class="card-body" style="padding: 20px;">
                                <div class="loading-message text-center" style="padding: 40px;">
                                    <i class="fa fa-spinner fa-spin" style="font-size: 24px;"></i>
                                    <p style="margin-top: 10px;">Loading stamps and signatures...</p>
                                </div>
                                <div class="preview-content" style="display: none;">
                                    <!-- Content will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);

			// Clear and add content to the stamps tab
			stampsTab.empty();
			stampsTab.append(content_wrapper);
			console.log("✅ Content added to stamps tab");

			// Load initial content and setup refresh button
			load_stamps_and_signatures(frm, content_wrapper);

			content_wrapper.find(".refresh-preview-btn").on("click", function () {
				load_stamps_and_signatures(frm, content_wrapper);
			});

			console.log("✅ Setup complete!");
		})
		.catch((error) => {
			console.error("❌ Failed to initialize stamps tab:", error);
			frappe.msgprint(
				"Failed to load stamps and signatures tab. Please refresh the page.",
			);
		});
}

// Manual tab creation functions removed to prevent duplicate div containers
// The app now relies solely on the Tab Break custom field for tab creation

function load_stamps_and_signatures(frm, container) {
	const company_name = frm.doc.name;

	if (!company_name) {
		container
			.find(".loading-message")
			.html('<p class="text-muted">Company name is required</p>');
		return;
	}

	// Show loading
	container.find(".loading-message").show();
	container.find(".preview-content").hide();

	// Fetch data
	frappe.call({
		method:
			"print_designer.api.company_preview_api.get_company_stamps_and_signatures",
		args: {
			company: company_name,
		},
		callback: function (response) {
			if (response.message) {
				render_preview_content(container, response.message);
			} else {
				container
					.find(".loading-message")
					.html('<p class="text-muted">Failed to load data</p>');
			}
		},
		error: function (error) {
			console.error("Error loading stamps and signatures:", error);
			container
				.find(".loading-message")
				.html('<p class="text-danger">Error loading data</p>');
		},
	});
}

function render_preview_content(container, data) {
	const { stamps, signatures, summary } = data;

	let html = `
        <div id="company-stamps_signatures_tab_card_body_summary_section" class="summary-section" style="margin-bottom: 25px;">
            <div class="row">
                <div class="col-md-6">
                    <div id="company-stamps_signatures_tab_card_body_summary_section_card" class="summary-card text-center" style="padding: 15px; border-radius: 8px;">
                        <h4 style="margin-bottom: 5px;">${summary.total_stamps}</h4>
                        <p style="margin: 0;">Company Stamps</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="summary-card text-center" style="padding: 15px; border-radius: 8px;">
                        <h4 style="margin-bottom: 5px;">${summary.total_signatures}</h4>
                        <p style="margin: 0;">Signatures</p>
                    </div>
                </div>
            </div>
        </div>
    `;

	// Company Stamps Section
	if (stamps.length > 0) {
		html += `
            <div id="company-stamps_signatures_tab_card_body_stamps_section" class="stamps-section" style="margin-bottom: 30px;">
                <h6 style="margin-bottom: 15px; padding-bottom: 5px;">
                    <i class="fa fa-certificate" style="margin-right: 8px;"></i>
                    Company Stamps (${stamps.length})
                </h6>
                <div class="row">
        `;

		stamps.forEach((stamp) => {
			html += `
                <div id="company-stamps_signatures_tab_stamps_preview_card" class="col-md-4 col-sm-6" style="margin-bottom: 20px;">
                    <div class="stamp-card" style=" border-radius: 8px; padding: 15px; height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div class="stamp-preview-container" data-stamp="${stamp.name}">
                            <div class="text-center">
                                ${
																	stamp.stamp_image
																		? `<img src="${stamp.stamp_image}" alt="${stamp.title}" style="max-width: 100px; max-height: 100px; border-radius: 4px; cursor: pointer;" onclick="preview_image('${stamp.stamp_image}', '${stamp.title}')">`
																		: '<div style="width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; margin: 0 auto;"><i class="fa fa-image text-muted"></i></div>'
																}
                            </div>
                            <div style="margin-top: 10px;">
                                <h6 style="margin-bottom: 5px; text-align: center;">${stamp.title}</h6>
                                <p style="margin: 2px 0; font-size: 11px; text-align: center;">
                                    <strong>Type:</strong> ${stamp.stamp_type || "N/A"}
                                </p>
                                <p style="margin: 2px 0; font-size: 11px; text-align: center;">
                                    <strong>Usage:</strong> ${stamp.usage_purpose || "General"}
                                </p>
                                ${stamp.description ? `<p style="margin-top: 8px; font-size: 10px; text-align: center; font-style: italic;">${stamp.description}</p>` : ""}
                            </div>
                        </div>
                    </div>
                </div>
            `;
		});

		html += `
                </div>
            </div>
        `;
	} else {
		html += `
            <div class="stamps-section" style="margin-bottom: 30px;">
                <h6 style="margin-bottom: 15px;">
                    <i class="fa fa-certificate" style="margin-right: 8px;"></i>
                    Company Stamps
                </h6>
                <div class="alert alert-info">
                    <i class="fa fa-info-circle"></i> 
                    No company stamps found. <a href="/app/signature-basic-information/new-signature-basic-information-1" target="_blank">Create your first stamp</a>
                </div>
            </div>
        `;
	}

	// Signatures Section
	if (signatures.length > 0) {
		html += `
            <div class="signatures-section">
                <h6 style="margin-bottom: 15px; padding-bottom: 5px;">
                    <i class="fa fa-pencil-square-o" style="margin-right: 8px;"></i>
                    Signatures (${signatures.length})
                </h6>
                <div class="row">
        `;

		signatures.forEach((signature) => {
			html += `
                <div id="company-stamps_signatures_tab_signatures_preview_card" class="col-md-4 col-sm-6" style="margin-bottom: 20px;">
                    <div class="signature-card" style="border-radius: 8px; padding: 15px; height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div class="signature-preview-container" data-signature="${signature.name}" data-source="${signature.source_type}">
                            <div class="text-center">
                                ${
																	signature.signature_image
																		? `<img src="${signature.signature_image}" alt="${signature.title}" style="max-width: 120px; max-height: 60px; border-radius: 4px; padding: 3px; cursor: pointer;" onclick="preview_image('${signature.signature_image}', '${signature.title}')">`
																		: '<div style="width: 120px; height: 60px; border: 1px dashed #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto;"><i class="fa fa-signature text-muted"></i></div>'
																}
                            </div>
                            <div style="margin-top: 10px;">
                                <h6 style="margin-bottom: 5px; text-align: center;">${signature.title}</h6>
                                ${signature.subtitle ? `<p style="margin: 2px 0; font-size: 11px; text-align: center;">${signature.subtitle}</p>` : ""}
                                <p style="margin: 2px 0; font-size: 10px; text-align: center;">
                                    <strong>Source:</strong> ${signature.source_type}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
		});

		html += `
                </div>
            </div>
        `;
	} else {
		html += `
            <div class="signatures-section">
                <h6 style="margin-bottom: 15px;">
                    <i class="fa fa-pencil-square-o" style="margin-right: 8px;"></i>
                    Signatures
                </h6>
                <div class="alert alert-info">
                    <i class="fa fa-info-circle"></i> 
                    No signatures found. Create signatures in <a href="/app/digital-signature/new-digital-signature-1" target="_blank">Digital Signature</a> or <a href="/app/signature-basic-information/new-signature-basic-information-1" target="_blank">Signature Basic Information</a>
                </div>
            </div>
        `;
	}

	// Update the container
	container.find(".loading-message").hide();
	container.find(".preview-content").html(html).show();
}

// Global function for image preview
window.preview_image = function (image_url, title) {
	const dialog = new frappe.ui.Dialog({
		title: title || "Image Preview",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "image_preview",
				options: `
                    <div style="text-align: center; padding: 20px;">
                        <img src="${image_url}" alt="${title}" style="max-width: 100%; max-height: 70vh; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    </div>
                `,
			},
		],
		primary_action_label: "Close",
		primary_action: function () {
			dialog.hide();
		},
	});

	dialog.show();
};
