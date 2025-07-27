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
    // Wait for form to be fully loaded and try multiple times
    let attempts = 0;
    const maxAttempts = 10;
    const attemptInterval = 500;
    
    function tryAddContent() {
        attempts++;
        
        // Check if content already exists
        if (frm.page.wrapper.find('.stamps-signatures-content').length > 0) {
            return;
        }
        
        // Try to find the custom field tab first
        let stampsTab = frm.page.wrapper.find('[data-fieldname="stamps_signatures_tab"]');
        let tabContent = null;
        
        if (stampsTab.length > 0) {
            // Found custom field tab - find its content area
            tabContent = stampsTab.closest('.form-tab').find('.form-section').first();
            
            if (tabContent.length === 0) {
                // Try alternative selectors for tab content
                tabContent = stampsTab.closest('.tab-pane').find('.form-section').first();
            }
            
            if (tabContent.length === 0) {
                // Create a section inside the tab
                const tabPane = stampsTab.closest('.tab-pane');
                if (tabPane.length > 0) {
                    tabContent = $('<div class="form-section"></div>');
                    tabPane.append(tabContent);
                }
            }
        }
        
        // If still no tab content found, try to create tab manually
        if (!tabContent || tabContent.length === 0) {
            if (attempts <= 3) {
                // Try to find existing tabs structure
                create_stamps_signatures_tab_manually(frm);
                return;
            } else {
                console.warn('Could not find or create tab content area for Stamps & Signatures');
                return;
            }
        }
        
        // Add our content to the tab
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
        
        // Add content to the tab
        tabContent.append(content_wrapper);
        
        // Load initial content
        load_stamps_and_signatures(frm, content_wrapper);
        
        // Refresh button handler
        content_wrapper.find('.refresh-preview-btn').on('click', function() {
            load_stamps_and_signatures(frm, content_wrapper);
        });
    }
    
    function retryAddContent() {
        if (attempts < maxAttempts) {
            setTimeout(tryAddContent, attemptInterval);
        }
    }
    
    // Start trying immediately, then retry if needed
    tryAddContent();
    retryAddContent();
}

function create_stamps_signatures_tab_manually(frm) {
    // Fallback: Create tab manually if Custom Field doesn't exist
    console.log('Creating Stamps & Signatures tab manually...');
    
    // Check if tab already exists
    if (frm.page.wrapper.find('#stamps-signatures-tab').length > 0) {
        console.log('Manual tab already exists');
        return;
    }
    
    // Debug: Log the form structure to understand the layout
    console.log('Debugging form structure:');
    console.log('Form wrapper classes:', frm.page.wrapper.attr('class'));
    console.log('Available tabs:', frm.page.wrapper.find('.nav-link').map((i, el) => $(el).text().trim()).get());
    
    // Try different selectors for tabs - be more comprehensive
    let tabsList = frm.page.wrapper.find('.form-tabs ul.nav');
    let tabContent = frm.page.wrapper.find('.form-tab-content');
    
    // Alternative selectors
    if (tabsList.length === 0) {
        tabsList = frm.page.wrapper.find('.nav-tabs');
    }
    if (tabsList.length === 0) {
        tabsList = frm.page.wrapper.find('ul.nav');
    }
    if (tabsList.length === 0) {
        // Look for any nav structure
        tabsList = frm.page.wrapper.find('.form-tabs').find('ul');
    }
    
    if (tabContent.length === 0) {
        tabContent = frm.page.wrapper.find('.tab-content');
    }
    if (tabContent.length === 0) {
        tabContent = frm.page.wrapper.find('.form-body');
    }
    
    console.log('Found tabs list:', tabsList.length, 'Found tab content:', tabContent.length);
    
    if (tabsList.length === 0 || tabContent.length === 0) {
        console.warn('Could not find tabs structure for manual creation. Available elements:');
        console.log('- .form-tabs ul.nav:', frm.page.wrapper.find('.form-tabs ul.nav').length);
        console.log('- .nav-tabs:', frm.page.wrapper.find('.nav-tabs').length);
        console.log('- .form-tab-content:', frm.page.wrapper.find('.form-tab-content').length);
        console.log('- .tab-content:', frm.page.wrapper.find('.tab-content').length);
        
        // Try a simpler approach - just add to the form body
        addContentToFormBody(frm);
        return;
    }
    
    // Create new tab button
    const newTabId = 'stamps-signatures-tab';
    const newTabButton = $(`
        <li class="nav-item">
            <a class="nav-link" data-toggle="tab" href="#${newTabId}" role="tab" aria-controls="${newTabId}">
                <span><i class="fa fa-stamp" style="margin-right: 5px;"></i>Stamps & Signatures</span>
            </a>
        </li>
    `);
    
    // Create new tab content
    const newTabContent = $(`
        <div class="form-tab tab-pane fade" id="${newTabId}" role="tabpanel">
            <div class="form-section">
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
            </div>
        </div>
    `);
    
    // Add tab button and content
    tabsList.append(newTabButton);
    tabContent.append(newTabContent);
    
    // Initialize Bootstrap tab functionality
    newTabButton.find('a').on('click', function(e) {
        e.preventDefault();
        $(this).tab('show');
    });
    
    // Load initial content
    load_stamps_and_signatures(frm, newTabContent.find('.stamps-signatures-content'));
    
    // Refresh button handler
    newTabContent.find('.refresh-preview-btn').on('click', function() {
        load_stamps_and_signatures(frm, newTabContent.find('.stamps-signatures-content'));
    });
    
    console.log('✅ Manual tab created successfully');
}

function addContentToFormBody(frm) {
    // Fallback: Add content directly to form body as a section
    console.log('Adding Stamps & Signatures as a section to form body...');
    
    // Check if content already exists
    if (frm.page.wrapper.find('.stamps-signatures-content').length > 0) {
        console.log('Content already exists in form body');
        return;
    }
    
    // Find the form body or any container
    let formContainer = frm.page.wrapper.find('.form-body').first();
    if (formContainer.length === 0) {
        formContainer = frm.page.wrapper.find('.frappe-control').last().parent();
    }
    if (formContainer.length === 0) {
        formContainer = frm.page.wrapper.find('.form-section').last().parent();
    }
    
    if (formContainer.length === 0) {
        console.warn('Could not find any form container');
        return;
    }
    
    // Create a section-style layout instead of tab
    const sectionWrapper = $(`
        <div class="form-section stamps-signatures-section" style="margin-top: 30px; border-top: 3px solid #1976d2; background: #fafbfc; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div class="section-head" style="background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white; padding: 15px 20px; margin: 0; border-radius: 0;">
                <h3 class="section-title" style="margin: 0; font-size: 1.2rem; font-weight: 600; color: white;">
                    <i class="fa fa-stamp" style="margin-right: 8px;"></i>
                    Stamps & Signatures
                </h3>
            </div>
            <div class="section-body" style="padding: 0; background: white;">
                <div class="stamps-signatures-content">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="card" style="border: none; border-radius: 0;">
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
            </div>
        </div>
    `);
    
    // Add to the form
    formContainer.append(sectionWrapper);
    
    // Load initial content
    load_stamps_and_signatures(frm, sectionWrapper.find('.stamps-signatures-content'));
    
    // Refresh button handler
    sectionWrapper.find('.refresh-preview-btn').on('click', function() {
        load_stamps_and_signatures(frm, sectionWrapper.find('.stamps-signatures-content'));
    });
    
    console.log('✅ Added Stamps & Signatures section to form body');
}

function load_stamps_and_signatures(frm, container) {
    const company_name = frm.doc.name;
    
    if (!company_name) {
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