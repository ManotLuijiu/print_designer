/**
 * Company DocType Client Script
 * Adds Company Stamps and Signatures preview in a dedicated tab
 */

frappe.ui.form.on("Company", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            add_stamps_and_signatures_content(frm);
        }
    }
});

function add_stamps_and_signatures_content(frm) {
    console.log('🚀 add_stamps_and_signatures_content called');
    
    // Check if content already exists
    if (frm.page.wrapper.find('.stamps-signatures-content').length > 0) {
        console.log('⚠️ Content already exists, skipping');
        return;
    }
    
    // Find the custom field tab and add content
    setTimeout(() => {
        console.log('🔍 Starting tab search...');
        console.log('📋 Form object:', frm);
        console.log('📋 Page wrapper exists:', !!frm.page.wrapper);
        
        // Debug: Show all tab-related elements
        console.log('🔎 All .tab-pane elements:');
        frm.page.wrapper.find('.tab-pane').each(function(index) {
            console.log(`  Tab ${index}:`, {
                id: this.id,
                classes: this.className,
                dataFieldname: $(this).data('fieldname'),
                hasContent: $(this).children().length > 0
            });
        });
        
        console.log('🔎 All nav-tab links:');
        frm.page.wrapper.find('.nav-tabs a, .nav-link').each(function(index) {
            console.log(`  Nav Link ${index}:`, {
                href: this.href,
                text: $(this).text().trim(),
                target: $(this).attr('href'),
                classes: this.className
            });
        });
        
        // Try multiple selectors to find the stamps tab
        console.log('🎯 Attempting tab selection methods...');
        
        // Method 1: Direct ID selector
        let stampsTab = frm.page.wrapper.find('#company-stamps_signatures_tab');
        console.log('Method 1 - Direct ID (#company-stamps_signatures_tab):', stampsTab.length);
        
        if (stampsTab.length === 0) {
            // Method 2: data-fieldname selector
            stampsTab = frm.page.wrapper.find('[data-fieldname="stamps_signatures_tab"]');
            console.log('Method 2 - data-fieldname direct:', stampsTab.length);
            if (stampsTab.length > 0) {
                console.log('Found element with data-fieldname:', stampsTab[0]);
                stampsTab = stampsTab.closest('.tab-pane');
                console.log('Closest .tab-pane:', stampsTab.length);
            }
        }
        
        if (stampsTab.length === 0) {
            // Method 3: partial match
            stampsTab = frm.page.wrapper.find('.tab-pane').filter(function() {
                const hasStampsInId = this.id && this.id.includes('stamps_signatures_tab');
                if (hasStampsInId) {
                    console.log('Found tab with stamps in ID:', this.id);
                }
                return hasStampsInId;
            });
            console.log('Method 3 - partial ID match:', stampsTab.length);
        }
        
        if (stampsTab.length === 0) {
            // Method 4: Search in current tab structure more broadly
            console.log('🔍 Searching for any stamps-related elements...');
            frm.page.wrapper.find('*').each(function() {
                if (this.id && this.id.includes('stamps')) {
                    console.log('Found stamps element:', this.tagName, this.id, this.className);
                }
                if ($(this).data('fieldname') && $(this).data('fieldname').includes('stamps')) {
                    console.log('Found element with stamps fieldname:', this.tagName, $(this).data('fieldname'));
                }
            });
        }
        
        console.log('✅ Final stamps tab selection:', stampsTab.length);
        if (stampsTab.length > 0) {
            console.log('Selected tab details:', {
                id: stampsTab[0].id,
                classes: stampsTab[0].className,
                tagName: stampsTab[0].tagName,
                hasChildren: stampsTab.children().length
            });
        }
        
        if (stampsTab.length === 0) {
            console.error('❌ Stamps & Signatures tab not found!');
            console.log('Available tabs:', frm.page.wrapper.find('.tab-pane').map(function() { return this.id; }).get());
            return;
        }
        
        // Move the stamps tab to be the last tab (after dashboard tab)
        console.log('🔄 Attempting to move tab to last position...');
        let tabNavItem = frm.page.wrapper.find('a[href="#company-stamps_signatures_tab"]').closest('li');
        let dashboardTabNavItem = frm.page.wrapper.find('a[href="#company-dashboard_tab"]').closest('li');
        
        console.log('Stamps tab nav item found:', tabNavItem.length);
        console.log('Dashboard tab nav item found:', dashboardTabNavItem.length);
        
        if (tabNavItem.length > 0 && dashboardTabNavItem.length > 0) {
            console.log('Moving stamps tab after dashboard tab...');
            tabNavItem.insertAfter(dashboardTabNavItem);
            console.log('✅ Moved stamps tab to last position');
        } else {
            console.log('⚠️ Could not move tab - nav items not found');
        }
        
        // Add our content directly to the tab pane - Fixed double div structure
        const content_wrapper = $(`
            <div class="stamps-signatures-content">
                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center" 
                                 style="background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; padding: 12px 20px;">
                                <h5 class="card-title mb-0" style="color: #495057;">
                                    <i class="fa fa-certificate" style="margin-right: 8px;"></i>
                                    Company Stamps & Signatures Preview
                                </h5>
                                <button class="btn btn-sm btn-primary refresh-preview-btn">
                                    <i class="fa fa-refresh"></i> Refresh
                                </button>
                            </div>
                            <div class="card-body" style="padding: 20px;">
                                <div class="loading-message text-center" style="padding: 40px;">
                                    <i class="fa fa-spinner fa-spin" style="font-size: 24px; color: #6c757d;"></i>
                                    <p style="margin-top: 10px; color: #6c757d;">Loading stamps and signatures...</p>
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
        
        // Ensure the stamps tab is completely separate and clear any existing content
        console.log('🧹 Ensuring tab separation...');
        
        // Clear the stamps tab completely first
        stampsTab.empty();
        console.log('Stamps tab cleared');
        
        // Ensure stock tab is properly isolated
        const stockTab = frm.page.wrapper.find('#company-stock_tab');
        if (stockTab.length > 0) {
            stockTab.removeClass('show').addClass('hide');
            console.log('Stock tab hidden to prevent conflicts');
        }
        
        // Ensure stamps tab has proper classes
        stampsTab.removeClass('hide').addClass('show');
        console.log('Stamps tab visibility ensured');
        
        // Add content to the tab
        console.log('📝 Adding content to tab...');
        console.log('Content wrapper created:', !!content_wrapper);
        console.log('Stamps tab element:', stampsTab[0]);
        
        stampsTab.append(content_wrapper);
        console.log('✅ Content appended to tab');
        
        // Verify content was added
        const addedContent = stampsTab.find('.stamps-signatures-content');
        console.log('Content verification - found in tab:', addedContent.length);
        
        // Load initial content
        console.log('🔄 Loading initial content...');
        load_stamps_and_signatures(frm, content_wrapper);
        
        // Refresh button handler
        content_wrapper.find('.refresh-preview-btn').on('click', function() {
            console.log('🔄 Refresh button clicked');
            load_stamps_and_signatures(frm, content_wrapper);
        });
        
        // Add tab click handler to ensure proper isolation
        const stampsTabLink = frm.page.wrapper.find('a[href="#company-stamps_signatures_tab"]');
        stampsTabLink.on('shown.bs.tab', function() {
            console.log('🎯 Stamps tab activated - ensuring content isolation');
            
            // Hide all other tabs
            frm.page.wrapper.find('.tab-pane').not('#company-stamps_signatures_tab').removeClass('show').addClass('hide');
            
            // Show only stamps tab
            stampsTab.removeClass('hide').addClass('show active');
            
            // Ensure our content is visible
            const stampsContent = stampsTab.find('.stamps-signatures-content');
            if (stampsContent.length > 0) {
                stampsContent.show();
                console.log('Stamps content visibility confirmed');
            }
        });
        
        console.log('✅ Setup complete!');
    }, 2000); // Increased delay to allow tab structure to be ready
}

// Manual tab creation functions removed to prevent duplicate div containers
// The app now relies solely on the Tab Break custom field for tab creation

function load_stamps_and_signatures(frm, container) {
    console.log('📊 load_stamps_and_signatures called');
    console.log('Container:', container);
    console.log('Form doc:', frm.doc);
    
    const company_name = frm.doc.name;
    console.log('Company name:', company_name);
    
    if (!company_name) {
        console.log('❌ No company name found');
        container.find('.loading-message').html('<p class="text-muted">Company name is required</p>');
        return;
    }
    
    // Show loading
    container.find('.loading-message').show();
    container.find('.preview-content').hide();
    
    // Fetch data
    frappe.call({
        method: "print_designer.api.company_preview_api.get_company_stamps_and_signatures",
        args: {
            company: company_name
        },
        callback: function(response) {
            if (response.message) {
                render_preview_content(container, response.message);
            } else {
                container.find('.loading-message').html('<p class="text-muted">Failed to load data</p>');
            }
        },
        error: function(error) {
            console.error('Error loading stamps and signatures:', error);
            container.find('.loading-message').html('<p class="text-danger">Error loading data</p>');
        }
    });
}

function render_preview_content(container, data) {
    const { stamps, signatures, summary } = data;
    
    let html = `
        <div class="summary-section" style="margin-bottom: 25px;">
            <div class="row">
                <div class="col-md-6">
                    <div class="summary-card text-center" style="background: #e3f2fd; padding: 15px; border-radius: 8px;">
                        <h4 style="color: #1976d2; margin-bottom: 5px;">${summary.total_stamps}</h4>
                        <p style="margin: 0; color: #424242;">Company Stamps</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="summary-card text-center" style="background: #f3e5f5; padding: 15px; border-radius: 8px;">
                        <h4 style="color: #7b1fa2; margin-bottom: 5px;">${summary.total_signatures}</h4>
                        <p style="margin: 0; color: #424242;">Signatures</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Company Stamps Section
    if (stamps.length > 0) {
        html += `
            <div class="stamps-section" style="margin-bottom: 30px;">
                <h6 style="color: #1976d2; margin-bottom: 15px; border-bottom: 2px solid #e3f2fd; padding-bottom: 5px;">
                    <i class="fa fa-certificate" style="margin-right: 8px;"></i>
                    Company Stamps (${stamps.length})
                </h6>
                <div class="row">
        `;
        
        stamps.forEach(stamp => {
            html += `
                <div class="col-md-4 col-sm-6" style="margin-bottom: 20px;">
                    <div class="stamp-card" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; height: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div class="stamp-preview-container" data-stamp="${stamp.name}">
                            <div class="text-center">
                                ${stamp.stamp_image ? 
                                    `<img src="${stamp.stamp_image}" alt="${stamp.title}" style="max-width: 100px; max-height: 100px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer;" onclick="preview_image('${stamp.stamp_image}', '${stamp.title}')">` :
                                    '<div style="width: 100px; height: 100px; background: #f5f5f5; border: 1px dashed #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto;"><i class="fa fa-image text-muted"></i></div>'
                                }
                            </div>
                            <div style="margin-top: 10px;">
                                <h6 style="margin-bottom: 5px; color: #333; text-align: center;">${stamp.title}</h6>
                                <p style="margin: 2px 0; font-size: 11px; color: #666; text-align: center;">
                                    <strong>Type:</strong> ${stamp.stamp_type || 'N/A'}
                                </p>
                                <p style="margin: 2px 0; font-size: 11px; color: #666; text-align: center;">
                                    <strong>Usage:</strong> ${stamp.usage_purpose || 'General'}
                                </p>
                                ${stamp.description ? `<p style="margin-top: 8px; font-size: 10px; color: #888; text-align: center; font-style: italic;">${stamp.description}</p>` : ''}
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
                <h6 style="color: #1976d2; margin-bottom: 15px;">
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
                <h6 style="color: #7b1fa2; margin-bottom: 15px; border-bottom: 2px solid #f3e5f5; padding-bottom: 5px;">
                    <i class="fa fa-pencil-square-o" style="margin-right: 8px;"></i>
                    Signatures (${signatures.length})
                </h6>
                <div class="row">
        `;
        
        signatures.forEach(signature => {
            html += `
                <div class="col-md-4 col-sm-6" style="margin-bottom: 20px;">
                    <div class="signature-card" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; height: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div class="signature-preview-container" data-signature="${signature.name}" data-source="${signature.source_type}">
                            <div class="text-center">
                                ${signature.signature_image ? 
                                    `<img src="${signature.signature_image}" alt="${signature.title}" style="max-width: 120px; max-height: 60px; border: 1px solid #ddd; border-radius: 4px; background: white; padding: 3px; cursor: pointer;" onclick="preview_image('${signature.signature_image}', '${signature.title}')">` :
                                    '<div style="width: 120px; height: 60px; background: #f5f5f5; border: 1px dashed #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto;"><i class="fa fa-signature text-muted"></i></div>'
                                }
                            </div>
                            <div style="margin-top: 10px;">
                                <h6 style="margin-bottom: 5px; color: #333; text-align: center;">${signature.title}</h6>
                                ${signature.subtitle ? `<p style="margin: 2px 0; font-size: 11px; color: #666; text-align: center;">${signature.subtitle}</p>` : ''}
                                <p style="margin: 2px 0; font-size: 10px; color: #888; text-align: center;">
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
                <h6 style="color: #7b1fa2; margin-bottom: 15px;">
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
    container.find('.loading-message').hide();
    container.find('.preview-content').html(html).show();
}

// Global function for image preview
window.preview_image = function(image_url, title) {
    const dialog = new frappe.ui.Dialog({
        title: title || 'Image Preview',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'image_preview',
                options: `
                    <div style="text-align: center; padding: 20px;">
                        <img src="${image_url}" alt="${title}" style="max-width: 100%; max-height: 70vh; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    </div>
                `
            }
        ],
        primary_action_label: 'Close',
        primary_action: function() {
            dialog.hide();
        }
    });
    
    dialog.show();
};