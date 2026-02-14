// File: print_designer/public/js/print_watermark.js

/**
 * Watermark functionality for Print Designer
 * Integrates with new DocType-based watermark system
 */

frappe.provide('print_designer.watermark');

print_designer.watermark = {
    current_config: null,
    watermark_element: null,
    templates: [],

    /**
     * Initialize watermark system for print designer
     */
    init: function(print_format_name) {
        this.print_format_name = print_format_name;
        this.load_watermark_config();
        this.load_available_templates();
        this.setup_sidebar_controls();
    },

    /**
     * Load watermark configuration for current print format
     */
    load_watermark_config: function() {
        frappe.call({
            method: 'print_designer.api.watermark.get_watermark_config_for_print_format',
            args: {
                print_format: this.print_format_name
            },
            callback: (r) => {
                if (r.message && r.message.enabled) {
                    this.current_config = r.message;
                    this.apply_watermark();
                } else {
                    this.remove_watermark();
                }
            },
            error: (r) => {
                console.error('Failed to load watermark config:', r);
                frappe.msgprint({
                    title: __('Watermark Error'),
                    message: __('Failed to load watermark configuration'),
                    indicator: 'red'
                });
            }
        });
    },

    /**
     * Load available watermark templates
     */
    load_available_templates: function() {
        frappe.call({
            method: 'print_designer.api.watermark.get_available_watermark_templates',
            callback: (r) => {
                if (r.message) {
                    this.templates = r.message;
                    this.update_template_selector();
                }
            }
        });
    },

    /**
     * Setup sidebar controls for watermark configuration
     */
    setup_sidebar_controls: function() {
        // Add watermark section to sidebar
        const sidebar = $('.print-format-sidebar');
        if (!sidebar.length) return;

        const watermark_section = $(`
            <div class="watermark-controls">
                <h6>${__('Watermark Settings')}</h6>
                <div class="form-group">
                    <label>${__('Template')}</label>
                    <select class="form-control watermark-template-select">
                        <option value="">${__('No Watermark')}</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>${__('Mode')}</label>
                    <select class="form-control watermark-mode-select">
                        <option value="None">${__('None')}</option>
                        <option value="Original on First Page">${__('Original on First Page')}</option>
                        <option value="Copy on All Pages">${__('Copy on All Pages')}</option>
                        <option value="Original,Copy on Sequence">${__('Original,Copy on Sequence')}</option>
                    </select>
                </div>
                <div class="watermark-advanced-settings" style="display: none;">
                    <div class="form-group">
                        <label>${__('Position')}</label>
                        <select class="form-control watermark-position-select">
                            <option value="Top Left">${__('Top Left')}</option>
                            <option value="Top Center">${__('Top Center')}</option>
                            <option value="Top Right">${__('Top Right')}</option>
                            <option value="Middle Left">${__('Middle Left')}</option>
                            <option value="Middle Center">${__('Middle Center')}</option>
                            <option value="Middle Right">${__('Middle Right')}</option>
                            <option value="Bottom Left">${__('Bottom Left')}</option>
                            <option value="Bottom Center">${__('Bottom Center')}</option>
                            <option value="Bottom Right">${__('Bottom Right')}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${__('Font Size')}</label>
                        <input type="number" class="form-control watermark-font-size" min="8" max="72" value="24">
                    </div>
                    <div class="form-group">
                        <label>${__('Color')}</label>
                        <input type="color" class="form-control watermark-color" value="#999999">
                    </div>
                    <div class="form-group">
                        <label>${__('Opacity')}</label>
                        <input type="range" class="form-control watermark-opacity" min="0" max="1" step="0.1" value="0.6">
                        <small class="text-muted opacity-value">0.6</small>
                    </div>
                    <div class="form-group">
                        <label>${__('Custom Text')}</label>
                        <input type="text" class="form-control watermark-custom-text" placeholder="${__('Optional custom text')}">
                    </div>
                </div>
                <div class="btn-group w-100">
                    <button class="btn btn-sm btn-secondary toggle-advanced">${__('Advanced')}</button>
                    <button class="btn btn-sm btn-primary save-watermark-config">${__('Save')}</button>
                </div>
            </div>
        `);

        sidebar.append(watermark_section);
        this.bind_sidebar_events();
        this.populate_current_config();
    },

    /**
     * Bind events to sidebar controls
     */
    bind_sidebar_events: function() {
        // Template selection
        $('.watermark-template-select').on('change', (e) => {
            const template_name = $(e.target).val();
            if (template_name) {
                this.load_template_config(template_name);
            } else {
                this.current_config = { enabled: false };
                this.remove_watermark();
            }
        });

        // Mode selection
        $('.watermark-mode-select').on('change', (e) => {
            if (this.current_config) {
                this.current_config.watermark_mode = $(e.target).val();
                this.apply_watermark();
            }
        });

        // Advanced settings toggle
        $('.toggle-advanced').on('click', () => {
            $('.watermark-advanced-settings').toggle();
        });

        // Real-time preview updates
        $('.watermark-position-select, .watermark-font-size, .watermark-color, .watermark-custom-text').on('change input', () => {
            this.update_config_from_controls();
            this.apply_watermark();
        });

        $('.watermark-opacity').on('input', (e) => {
            const value = $(e.target).val();
            $('.opacity-value').text(value);
            this.update_config_from_controls();
            this.apply_watermark();
        });

        // Save configuration
        $('.save-watermark-config').on('click', () => {
            this.save_configuration();
        });
    },

    /**
     * Update template selector with available templates
     */
    update_template_selector: function() {
        const selector = $('.watermark-template-select');
        selector.empty().append('<option value="">' + __('No Watermark') + '</option>');
        
        this.templates.forEach(template => {
            selector.append(`<option value="${template.name}">${template.name}</option>`);
        });
    },

    /**
     * Load template configuration and apply it
     */
    load_template_config: function(template_name) {
        frappe.call({
            method: 'print_designer.api.watermark.get_watermark_template_config',
            args: {
                template_name: template_name
            },
            callback: (r) => {
                if (r.message) {
                    this.current_config = {
                        enabled: true,
                        source: 'template',
                        template_name: template_name,
                        ...r.message
                    };
                    this.populate_current_config();
                    this.apply_watermark();
                }
            },
            error: (r) => {
                frappe.msgprint({
                    title: __('Template Error'),
                    message: __('Failed to load template configuration'),
                    indicator: 'red'
                });
            }
        });
    },

    /**
     * Populate sidebar controls with current configuration
     */
    populate_current_config: function() {
        if (!this.current_config || !this.current_config.enabled) return;

        $('.watermark-template-select').val(this.current_config.template_name || '');
        $('.watermark-mode-select').val(this.current_config.watermark_mode || 'None');
        $('.watermark-position-select').val(this.current_config.position || 'Top Right');
        $('.watermark-font-size').val(this.current_config.font_size || 24);
        $('.watermark-color').val(this.current_config.color || '#999999');
        $('.watermark-opacity').val(this.current_config.opacity || 0.6);
        $('.watermark-custom-text').val(this.current_config.custom_text || '');
        $('.opacity-value').text(this.current_config.opacity || 0.6);
    },

    /**
     * Update configuration from sidebar controls
     */
    update_config_from_controls: function() {
        if (!this.current_config) {
            this.current_config = { enabled: true };
        }

        this.current_config.watermark_mode = $('.watermark-mode-select').val();
        this.current_config.position = $('.watermark-position-select').val();
        this.current_config.font_size = parseInt($('.watermark-font-size').val()) || 24;
        this.current_config.color = $('.watermark-color').val();
        this.current_config.opacity = parseFloat($('.watermark-opacity').val()) || 0.6;
        this.current_config.custom_text = $('.watermark-custom-text').val();
    },

    /**
     * Apply watermark to the print preview
     */
    apply_watermark: function() {
        if (!this.current_config || !this.current_config.enabled || this.current_config.watermark_mode === 'None') {
            this.remove_watermark();
            return;
        }

        this.remove_watermark(); // Remove existing watermark first

        const print_area = $('.print-format-container, .print-preview-wrapper').first();
        if (!print_area.length) return;

        const watermark_text = this.get_watermark_text();
        const position_style = this.get_position_style();

        if (watermark_text === 'sequence') {
            // Special handling for sequence watermarks in preview
            // Show both Original and Copy to indicate sequence mode
            this.watermark_element = $(`
                <div class="watermark-sequence-preview" style="
                    position: absolute;
                    pointer-events: none;
                    z-index: 1000;
                    font-family: ${this.current_config.font_family || 'Sarabun'};
                    font-size: ${this.current_config.font_size || 24}px;
                    color: ${this.current_config.color || '#999999'};
                    opacity: ${this.current_config.opacity || 0.6};
                    font-weight: bold;
                    text-transform: uppercase;
                    ${position_style}
                ">
                    <div class="sequence-original">${__('ORIGINAL')}</div>
                    <div class="sequence-copy" style="margin-top: 10px; font-size: 0.8em; font-style: italic;">(${__('COPY')} on pages 2+)</div>
                </div>
            `);
        } else {
            this.watermark_element = $(`
                <div class="watermark-overlay" style="
                    position: absolute;
                    pointer-events: none;
                    z-index: 1000;
                    font-family: ${this.current_config.font_family || 'Sarabun'};
                    font-size: ${this.current_config.font_size || 24}px;
                    color: ${this.current_config.color || '#999999'};
                    opacity: ${this.current_config.opacity || 0.6};
                    font-weight: bold;
                    text-transform: uppercase;
                    ${position_style}
                ">${watermark_text}</div>
            `);
        }

        print_area.css('position', 'relative').append(this.watermark_element);

        // Handle different watermark modes
        this.apply_watermark_mode();
    },

    /**
     * Get watermark text based on configuration
     */
    get_watermark_text: function() {
        if (this.current_config.custom_text) {
            return this.current_config.custom_text;
        }

        const mode = this.current_config.watermark_mode;
        if (mode === 'Original on First Page') {
            return __('ORIGINAL');
        } else if (mode === 'Copy on All Pages') {
            return __('COPY');
        } else if (mode === 'Original,Copy on Sequence') {
            // For preview, show both Original and Copy to indicate sequence mode
            return 'sequence'; // Special marker for sequence handling
        }

        return __('WATERMARK');
    },

    /**
     * Get CSS positioning style based on position setting
     */
    get_position_style: function() {
        const position = this.current_config.position || 'Top Right';
        
        const positions = {
            'Top Left': 'top: 10px; left: 10px;',
            'Top Center': 'top: 10px; left: 50%; transform: translateX(-50%);',
            'Top Right': 'top: 10px; right: 10px;',
            'Middle Left': 'top: 50%; left: 10px; transform: translateY(-50%);',
            'Middle Center': 'top: 50%; left: 50%; transform: translate(-50%, -50%);',
            'Middle Right': 'top: 50%; right: 10px; transform: translateY(-50%);',
            'Bottom Left': 'bottom: 10px; left: 10px;',
            'Bottom Center': 'bottom: 10px; left: 50%; transform: translateX(-50%);',
            'Bottom Right': 'bottom: 10px; right: 10px;'
        };

        return positions[position] || positions['Top Right'];
    },

    /**
     * Apply watermark mode specific logic
     */
    apply_watermark_mode: function() {
        const mode = this.current_config.watermark_mode;
        
        if (mode === 'Copy on All Pages') {
            // Clone watermark to all pages if multiple pages exist
            const pages = $('.print-format-page');
            if (pages.length > 1) {
                pages.each((index, page) => {
                    if (index > 0) { // Skip first page as it already has watermark
                        const cloned_watermark = this.watermark_element.clone();
                        $(page).css('position', 'relative').append(cloned_watermark);
                    }
                });
            }
        }
        // Add more mode-specific logic as needed
    },

    /**
     * Remove watermark from print preview
     */
    remove_watermark: function() {
        $('.watermark-overlay, .watermark-sequence-preview').remove();
        this.watermark_element = null;
    },

    /**
     * Save watermark configuration for current print format
     */
    save_configuration: function() {
        if (!this.current_config) return;

        this.update_config_from_controls();

        const config_data = {
            watermark_template: $('.watermark-template-select').val() || null,
            override_settings: $('.watermark-template-select').val() ? 0 : 1,
            watermark_mode: this.current_config.watermark_mode,
            font_size: this.current_config.font_size,
            position: this.current_config.position,
            font_family: this.current_config.font_family,
            color: this.current_config.color,
            opacity: this.current_config.opacity,
            custom_text: this.current_config.custom_text
        };

        frappe.call({
            method: 'print_designer.api.watermark.save_print_format_watermark_config',
            args: {
                print_format: this.print_format_name,
                config: config_data
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint({
                        title: __('Save Error'),
                        message: r.message.error || __('Failed to save configuration'),
                        indicator: 'red'
                    });
                }
            },
            error: (r) => {
                frappe.msgprint({
                    title: __('Save Error'),
                    message: __('Failed to save watermark configuration'),
                    indicator: 'red'
                });
            }
        });
    },

    /**
     * Create new watermark template
     */
    create_template: function(template_data) {
        return frappe.call({
            method: 'print_designer.api.watermark.create_watermark_template',
            args: {
                template_data: template_data
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.load_available_templates(); // Refresh template list
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                    return r.message.template_name;
                } else {
                    frappe.msgprint({
                        title: __('Template Creation Error'),
                        message: r.message.error || __('Failed to create template'),
                        indicator: 'red'
                    });
                }
            }
        });
    },

    /**
     * Show template creation dialog
     */
    show_template_dialog: function() {
        const dialog = new frappe.ui.Dialog({
            title: __('Create Watermark Template'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'template_name',
                    label: __('Template Name'),
                    reqd: 1
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'watermark_mode',
                    label: __('Watermark Mode'),
                    options: 'None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence',
                    default: 'Copy on All Pages',
                    reqd: 1
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Int',
                    fieldname: 'font_size',
                    label: __('Font Size (px)'),
                    default: 24
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'position',
                    label: __('Position'),
                    options: 'Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right',
                    default: 'Top Right'
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'font_family',
                    label: __('Font Family'),
                    options: 'Arial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri\nSarabun',
                    default: 'Sarabun'
                },
                {
                    fieldtype: 'Color',
                    fieldname: 'color',
                    label: __('Text Color'),
                    default: '#999999'
                },
                {
                    fieldtype: 'Float',
                    fieldname: 'opacity',
                    label: __('Opacity'),
                    default: 0.6,
                    precision: 2
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'custom_text',
                    label: __('Custom Text'),
                    description: __('Override default text (Original/Copy) with custom text')
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'description',
                    label: __('Description')
                }
            ],
            primary_action_label: __('Create Template'),
            primary_action: (values) => {
                this.create_template(values).then(() => {
                    dialog.hide();
                });
            }
        });

        dialog.show();
    }
};

// Auto-initialize when print designer loads
$(document).ready(() => {
    // Hook into print designer initialization
    if (window.cur_frm && cur_frm.doctype === 'Print Format') {
        frappe.after_ajax(() => {
            if (cur_frm.doc.name) {
                print_designer.watermark.init(cur_frm.doc.name);
            }
        });
    }
});

/**
 * Print button overrides:
 *
 * 1. Form Print button (print_doc):
 *    - Chrome CDP format → open PDF in new tab (preview)
 *    - Raw printing + TBS agent → submit directly to dot matrix (no preview)
 *    - Other → original Frappe print preview (window.print)
 *
 * 2. Print page Print button (printit):
 *    - Raw printing + TBS agent → submit to TBS agent (replaces QZ Tray)
 *    - No TBS agent → fall back to original QZ Tray flow
 */
(function() {
    // ── 1. Override print_doc on Form ──────────────────────────────
    const _original_print_doc = frappe.ui.form.Form.prototype.print_doc;

    frappe.ui.form.Form.prototype.print_doc = function() {
        if (this.is_dirty()) {
            frappe.toast({
                message: __(
                    "This document has unsaved changes which might not appear in the output. <br> Consider saving the document before printing."
                ),
                indicator: "yellow",
            });
        }

        const print_format = this.get_print_format();

        frappe.xcall("print_designer.overrides.print_button.get_print_config", {
            print_format: print_format,
        }).then((config) => {
            if (config.raw_printing && config.tbs_agent_available) {
                // Raw printing → send directly to dot matrix via TBS agent
                this._submit_raw_print_via_tbs(print_format, config);
            } else if (config.pdf_generator === "chrome") {
                // Chrome CDP → open PDF preview in new tab
                const params = new URLSearchParams({
                    doctype: this.doctype,
                    name: this.doc.name,
                    format: print_format,
                    no_letterhead: this.get_letterhead ? 0 : 1,
                    _lang: frappe.boot.lang || "en",
                });
                const pdf_url = `/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`;
                window.open(pdf_url, "_blank");
            } else {
                // Original Frappe print preview
                _original_print_doc.call(this);
            }
        }).catch(() => {
            _original_print_doc.call(this);
        });
    };

    /**
     * Submit raw print job to TBS Print Agent from the form view.
     */
    frappe.ui.form.Form.prototype._submit_raw_print_via_tbs = function(print_format, config) {
        frappe.show_alert({
            message: __("Sending to printer..."),
            indicator: "blue",
        });

        frappe.xcall("print_designer.overrides.print_button.submit_raw_print", {
            doc: this.doctype,
            name: this.doc.name,
            print_format: print_format,
            agent: config.default_agent,
            printer: config.default_printer,
        }).then((result) => {
            if (result && result.success) {
                frappe.show_alert({
                    message: __("Print job submitted successfully"),
                    indicator: "green",
                });
            }
        }).catch((err) => {
            frappe.msgprint({
                title: __("Print Error"),
                message: err.message || __("Failed to submit print job"),
                indicator: "red",
            });
        });
    };

    /**
     * Helper: get the currently selected print format name.
     */
    frappe.ui.form.Form.prototype.get_print_format = function() {
        const user_settings = frappe.get_user_settings(this.doctype);
        if (user_settings && user_settings.print_format) {
            return user_settings.print_format;
        }
        const meta = frappe.get_meta(this.doctype);
        if (meta && meta.default_print_format) {
            return meta.default_print_format;
        }
        return "Standard";
    };

    // ── 2. Override printit on PrintView (print page) ─────────────
    // Wait for PrintView class to be available, then patch it
    const _patch_print_view = function() {
        if (!frappe.ui.form.PrintView) return;

        const _original_printit = frappe.ui.form.PrintView.prototype.printit;

        frappe.ui.form.PrintView.prototype.printit = function() {
            const me = this;

            // Only intercept if this is a raw printing format
            if (!me.is_raw_printing()) {
                // Not raw printing — use original behavior
                // (network printer, browser print, etc.)
                return _original_printit.call(me);
            }

            // Raw printing — check if TBS agent is available
            const print_format_name = me.selected_format();

            frappe.xcall("print_designer.overrides.print_button.get_print_config", {
                print_format: print_format_name,
            }).then((config) => {
                if (config.tbs_agent_available) {
                    // TBS agent available — submit raw print job
                    me._tbs_raw_print(print_format_name, config);
                } else {
                    // No TBS agent — fall back to original QZ Tray flow
                    _original_printit.call(me);
                }
            }).catch(() => {
                _original_printit.call(me);
            });
        };

        /**
         * Submit raw print via TBS agent from the print page.
         */
        frappe.ui.form.PrintView.prototype._tbs_raw_print = function(print_format, config) {
            frappe.show_alert({
                message: __("Sending to printer via TBS agent..."),
                indicator: "blue",
            });

            frappe.xcall("print_designer.overrides.print_button.submit_raw_print", {
                doc: this.frm.doctype || this.frm.doc.doctype,
                name: this.frm.docname || this.frm.doc.name,
                print_format: print_format,
                agent: config.default_agent,
                printer: config.default_printer,
            }).then((result) => {
                if (result && result.success) {
                    frappe.show_alert({
                        message: __("Print job submitted successfully"),
                        indicator: "green",
                    });
                }
            }).catch((err) => {
                frappe.msgprint({
                    title: __("Print Error"),
                    message: err.message || __("Failed to submit print job to TBS agent"),
                    indicator: "red",
                });
            });
        };
    };

    // Patch immediately if PrintView exists, otherwise defer
    if (frappe.ui.form.PrintView) {
        _patch_print_view();
    } else {
        $(document).on("page-change", function() {
            if (frappe.ui.form.PrintView && !frappe.ui.form.PrintView.prototype._tbs_raw_print) {
                _patch_print_view();
            }
        });
    }
})();
