// Client script for Global Defaults typography management
frappe.ui.form.on("Global Defaults", {
    // Generate font stack based on selected primary font
    primary_font_family: function(frm) {
        const fontMappings = {
            "Sarabun (Thai)": '"Sarabun", "Noto Sans Thai", "IBM Plex Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Noto Sans Thai": '"Noto Sans Thai", "Sarabun", "IBM Plex Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "IBM Plex Sans Thai": '"IBM Plex Sans Thai", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Kanit (Thai)": '"Kanit", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Prompt (Thai)": '"Prompt", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Mitr (Thai)": '"Mitr", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Pridi (Thai)": '"Pridi", "Sarabun", "Noto Sans Thai", "InterVariable", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Inter": '"InterVariable", "Inter", "Sarabun", "Noto Sans Thai", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Roboto": '"Roboto", "InterVariable", "Inter", "Sarabun", "Noto Sans Thai", "-apple-system", "BlinkMacSystemFont", "Segoe UI", sans-serif',
            "Open Sans": '"Open Sans", "InterVariable", "Inter", "Sarabun", "Noto Sans Thai", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Lato": '"Lato", "InterVariable", "Inter", "Sarabun", "Noto Sans Thai", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif',
            "Nunito Sans": '"Nunito Sans", "InterVariable", "Inter", "Sarabun", "Noto Sans Thai", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", sans-serif'
        };

        if (frm.doc.primary_font_family && frm.doc.primary_font_family !== "System Default") {
            frm._generated_font_stack = fontMappings[frm.doc.primary_font_family] || fontMappings["Sarabun (Thai)"];
            frm._apply_font_preview();
        }
    },

    // Handle custom font stack changes
    custom_font_stack: function(frm) {
        if (frm.doc.primary_font_family === "System Default" && frm.doc.custom_font_stack) {
            frm._generated_font_stack = frm.doc.custom_font_stack;
            frm._apply_font_preview();
        }
    },

    // Enable/disable Thai font support
    enable_thai_font_support: function(frm) {
        frm._apply_font_preview();
    },

    // Form setup and preview
    refresh: function(frm) {
        frm._setup_font_preview();
        frm._add_typography_buttons();
        
        // Trigger initial font stack generation
        if (frm.doc.primary_font_family) {
            frm.trigger('primary_font_family');
        }
    },

    // Apply typography settings system-wide
    validate: function(frm) {
        return frm._apply_typography_settings();
    }
});

// Helper methods for typography management
frappe.ui.form.on("Global Defaults", {
    // Setup font preview functionality
    _setup_font_preview: function(frm) {
        // Add preview area after typography section
        if (!frm.$preview_area) {
            const typography_section = frm.fields_dict.typography_section?.$wrapper;
            if (typography_section) {
                frm.$preview_area = $(`
                    <div class="font-preview-area" style="margin: 15px 0; padding: 15px; border: 1px solid #d1d8dd; border-radius: 6px; background: #f8f9fa;">
                        <div class="font-preview-header" style="font-weight: 600; margin-bottom: 10px; color: #36414c;">Font Preview</div>
                        <div class="font-preview-text" style="font-size: 14px; line-height: 1.5; color: #36414c;">
                            <div>The quick brown fox jumps over the lazy dog. 1234567890</div>
                            <div style="margin-top: 8px;">ด่วน บริษัท จำกัด ใบกำกับภาษี ฟอนต์ไทย กบฏแปลกใหม่</div>
                            <div style="margin-top: 8px; font-size: 12px; color: #8d99a6;">Applied Font Stack: <span class="current-font-stack"></span></div>
                        </div>
                    </div>
                `);
                typography_section.after(frm.$preview_area);
            }
        }
    },

    // Apply font preview
    _apply_font_preview: function(frm) {
        if (frm.$preview_area && frm._generated_font_stack) {
            const preview_text = frm.$preview_area.find('.font-preview-text');
            const font_stack_display = frm.$preview_area.find('.current-font-stack');
            
            preview_text.css('font-family', frm._generated_font_stack);
            font_stack_display.text(frm._generated_font_stack);
            
            // Add special styling for Thai font support
            if (frm.doc.enable_thai_font_support) {
                preview_text.addClass('thai-font-optimized');
            } else {
                preview_text.removeClass('thai-font-optimized');
            }
        }
    },

    // Add typography management buttons
    _add_typography_buttons: function(frm) {
        // Apply Typography Settings button
        if (!frm.custom_buttons.__("Apply Typography")) {
            frm.add_custom_button(__("Apply Typography"), function() {
                frm._apply_typography_settings().then(() => {
                    frappe.msgprint({
                        title: __("Typography Applied"),
                        message: __("Typography settings have been applied system-wide. Please refresh the page to see changes."),
                        indicator: "green"
                    });
                });
            }).addClass("btn-primary");
        }

        // Reset to Default button
        if (!frm.custom_buttons.__("Reset to Default")) {
            frm.add_custom_button(__("Reset to Default"), function() {
                frappe.confirm(
                    __("This will reset typography settings to Sarabun (Thai) with Thai font support. Continue?"),
                    function() {
                        frm.set_value('primary_font_family', 'Sarabun (Thai)');
                        frm.set_value('enable_thai_font_support', 1);
                        frm.set_value('custom_font_stack', '');
                        frm.save();
                    }
                );
            });
        }
    },

    // Apply typography settings system-wide
    _apply_typography_settings: function(frm) {
        return new Promise((resolve, reject) => {
            if (!frm._generated_font_stack) {
                resolve();
                return;
            }

            // Generate CSS for font stack override
            const css_content = `
/* Global Defaults Typography Override - Generated by Print Designer */
html:root, :root {
    --font-stack: ${frm._generated_font_stack} !important;
}

/* Enhanced form elements font family */
html, body, input, button, select, optgroup, textarea,
.form-control, .form-select, .btn, .navbar, .sidebar, .page-container,
.page-content, .page-title, .navbar-brand, .menu-item, .list-item,
.doctype-list, .form-section, .section-head, .form-group, .field-label,
.form-message, .modal-header, .modal-body, .modal-footer,
.frappe-control, .control-input, .control-label, .like-disabled-input,
.comment-box, .timeline-item, .list-row, .list-row-col,
.desk-sidebar, .navbar-collapse, .dropdown-menu, .dropdown-item,
p, span, div, h1, h2, h3, h4, h5, h6, td, th, label {
    font-family: var(--font-stack) !important;
}

${frm.doc.enable_thai_font_support ? `
/* Thai font optimizations */
.thai-font-optimized {
    font-feature-settings: "liga" 1, "kern" 1;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Thai unicode support enhancements */
[lang="th"], .thai-text {
    font-family: var(--font-stack) !important;
    word-break: break-word;
    overflow-wrap: break-word;
}
` : ''}
`;

            // Apply CSS via Print Designer API
            frappe.call({
                method: "print_designer.api.global_typography.apply_typography_settings",
                args: {
                    font_stack: frm._generated_font_stack,
                    enable_thai_support: frm.doc.enable_thai_font_support,
                    css_content: css_content
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        // Trigger typography update event for dynamic injection
                        $(document).trigger('typography-updated');
                        
                        // Refresh typography in current page
                        if (window.refreshTypography) {
                            window.refreshTypography();
                        }
                        
                        resolve(r.message);
                    } else {
                        frappe.msgprint({
                            title: __("Error"),
                            message: r.message?.error || __("Failed to apply typography settings"),
                            indicator: "red"
                        });
                        reject(r.message?.error);
                    }
                },
                error: function(err) {
                    frappe.msgprint({
                        title: __("Error"),
                        message: __("Failed to communicate with typography API"),
                        indicator: "red"
                    });
                    reject(err);
                }
            });
        });
    }
});