// TODO: revisit and properly implement this client script
frappe.pages['print'].on_page_load = function (wrapper) {
  frappe.require(['pdfjs.bundle.css', 'print_designer.bundle.css']);
  
  // Load PDF logger utility
  frappe.require(['/assets/print_designer/js/pdf_logger.js'], () => {
    console.log('PDF Logger loaded successfully');
  });
  
  frappe.ui.make_app_page({
    parent: wrapper,
  });

  let print_view = new frappe.ui.form.PrintView(wrapper);

  $(wrapper).bind('show', () => {
    const route = frappe.get_route();
    const doctype = route[1];
    const docname = route.slice(2).join('/');
    if (!frappe.route_options || !frappe.route_options.frm) {
      frappe.model.with_doc(doctype, docname, () => {
        let frm = { doctype: doctype, docname: docname };
        frm.doc = frappe.get_doc(doctype, docname);
        frappe.model.with_doctype(doctype, () => {
          frm.meta = frappe.get_meta(route[1]);
          print_view.show(frm);
        });
      });
    } else {
      print_view.frm = frappe.route_options.frm.doctype
        ? frappe.route_options.frm
        : frappe.route_options.frm.frm;
      frappe.route_options.frm = null;
      print_view.show(print_view.frm);
    }
  });
};
frappe.ui.form.PrintView = class PrintView extends frappe.ui.form.PrintView {
  constructor(wrapper) {
    super(wrapper);
  }
  make() {
    super.make();
    this.print_wrapper = this.page.main.append(
      `<div class="print-designer-wrapper">
				<div id="preview-container" class="preview-container"
					style="background-color: white; position: relative;">
					${frappe.render_template('print_skeleton_loading')}
				</div>
			</div>`,
    );
    this.header_prepend_container = $(
      `<div class="print_selectors flex col align-items-center"></div>`,
    ).prependTo(this.page.page_actions);
    this.toolbar_print_format_selector = frappe.ui.form.make_control({
      df: {
        fieldtype: 'Link',
        fieldname: 'print_format',
        options: 'Print Format',
        placeholder: __('Print Format'),
        get_query: () => {
          return { filters: { doc_type: this.frm.doctype } };
        },
        change: () => {
          if (
            this.toolbar_print_format_selector.value ==
            this.toolbar_print_format_selector.last_value
          )
            return;
          this.print_format_item.set_value(
            this.toolbar_print_format_selector.value,
          );
        },
      },
      parent: this.header_prepend_container,
      only_input: true,
      render_input: true,
    });
    this.toolbar_language_selector = frappe.ui.form.make_control({
      df: {
        fieldtype: 'Link',
        fieldname: 'language',
        placeholder: __('Language'),
        options: 'Language',
        change: () => {
          if (
            this.toolbar_language_selector.value ==
            this.toolbar_language_selector.last_value
          )
            return;
          this.language_item.set_value(this.toolbar_language_selector.value);
        },
      },
      parent: this.header_prepend_container,
      only_input: true,
      render_input: true,
    });

    this.toolbar_print_format_selector.$input_area.addClass(
      'my-0 px-3 hidden-xs hidden-md',
    );
    this.toolbar_language_selector.$input_area.addClass(
      'my-0 px-3 hidden-xs hidden-md',
    );
    this.sidebar_toggle = $('.page-head').find('.sidebar-toggle-btn');
    $(document.body).on('toggleSidebar', () => {
      if (this.sidebar.is(':hidden')) {
        this.toolbar_print_format_selector.$wrapper.show();
        this.toolbar_language_selector.$wrapper.show();
      } else {
        this.toolbar_print_format_selector.$wrapper.hide();
        this.toolbar_language_selector.$wrapper.hide();
      }
    });
  }
  createPdfEl(url, wrapperContainer) {
    const mainSectionWidth =
      document.getElementsByClassName('main-section')[0].offsetWidth + 'px';

    let pdfEl = document.getElementById('pd-pdf-viewer');
    if (!pdfEl) {
      pdfEl = document.createElement('object');
      pdfEl.id = 'pd-pdf-viewer';
      pdfEl.type = 'application/pdf';
      wrapperContainer.appendChild(pdfEl);
    }
    pdfEl.style.height = '0px';

    pdfEl.data = url;

    pdfEl.style.width = mainSectionWidth;

    return pdfEl;
  }
  async designer_pdf(print_format) {
    // Initialize logging for this PDF generation session
    if (window.pdfLogger) {
      window.pdfLogger.log('PDF_GENERATION_INIT', 'Starting PDF generation process', {
        print_format: print_format.name,
        doctype: this.frm.doc.doctype,
        docname: this.frm.doc.name
      });
    }
    
    let print_designer_settings = JSON.parse(
      print_format.print_designer_settings,
    );
    let page_settings = print_designer_settings.page;
    let canvasContainer = document.getElementById('preview-container');
    canvasContainer.style.display = 'block';
    const wrapperContainer = document.getElementsByClassName(
      'print-designer-wrapper',
    )[0];
    canvasContainer.style.minHeight = page_settings.height + 'px';
    canvasContainer.style.width = page_settings.width + 'px';
    canvasContainer.innerHTML = `${frappe.render_template('print_skeleton_loading')}`;
    let params = new URLSearchParams({
      doctype: this.frm.doc.doctype,
      name: this.frm.doc.name,
      format: this.selected_format(),
      _lang: this.lang_code,
    });

    // Add PDF generator parameter
    const selected_generator = this.selected_pdf_generator || 'auto';
    params.set('pdf_generator', selected_generator);

    // Add copy parameters if enabled
    if (this.enable_copies_item && this.enable_copies_item.value) {
      params.set('copy_count', this.copy_count_item.value || 2);
      if (this.copy_labels_item.value) {
        params.set('copy_labels', this.copy_labels_item.value);
      }
      
      // For copies, prefer wkhtmltopdf unless Chrome is explicitly selected
      if (!this.selected_pdf_generator || this.selected_pdf_generator === 'auto') {
        params.set('pdf_generator', 'wkhtmltopdf');
      }
      
      console.log('Copy parameters added to preview:', {
        copy_count: this.copy_count_item.value || 2,
        copy_labels: this.copy_labels_item.value,
        pdf_generator: params.get('pdf_generator')
      });
    }

    // Add letterhead if selected (works with wkhtmltopdf)
    if (this.letterhead_selector && this.letterhead_selector.val()) {
      params.set('letterhead', this.letterhead_selector.val());
    }
    console.log('params', params);
    let url = `${
      window.location.origin
    }/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`;

    // Log PDF generation start
    if (window.pdfLogger) {
      window.pdfLogger.logPDFStart(url, params.get('pdf_generator'), params.get('format'));
    }

    const pdfEl = this.createPdfEl(url, wrapperContainer);
    const onError = () => {
      // Log the error with comprehensive details
      if (window.pdfLogger) {
        window.pdfLogger.logPDFError(
          url,
          params.get('pdf_generator'),
          params.get('format'),
          new Error('PDF Object failed to load')
        );
      }
      
      // Try to get more specific error information
      console.error('PDF Generation Error:', {
        url: url,
        generator: params.get('pdf_generator'),
        format: params.get('format')
      });
      
      // Try alternative PDF generators if auto-selection failed
      const currentGenerator = params.get('pdf_generator');
      const alternativeGenerators = ['wkhtmltopdf', 'WeasyPrint', 'chrome'].filter(g => g !== currentGenerator);
      
      if (alternativeGenerators.length > 0 && !this.pdf_retry_attempted) {
        this.pdf_retry_attempted = true;
        const nextGenerator = alternativeGenerators[0];
        
        // Log the retry attempt
        if (window.pdfLogger) {
          window.pdfLogger.logPDFRetry(
            url,
            nextGenerator,
            currentGenerator,
            1
          );
        }
        
        frappe.show_alert({
          message: __('Retrying with {0} generator...', [nextGenerator]),
          indicator: 'blue'
        }, 3);
        
        // Retry with different generator
        params.set('pdf_generator', nextGenerator);
        const retryUrl = `${window.location.origin}/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`;
        
        setTimeout(() => {
          pdfEl.data = retryUrl;
        }, 1000);
        
        return;
      }
      
      // Log final failure
      if (window.pdfLogger) {
        window.pdfLogger.log('PDF_GENERATION_FINAL_FAILURE', 'All PDF generation attempts failed', {
          url: url,
          attempts: this.pdf_retry_attempted ? 2 : 1,
          finalGenerator: params.get('pdf_generator'),
          alternativeGenerators: alternativeGenerators
        }, 'CRITICAL');
      }
      
      // Show fallback UI
      this.print_wrapper.find('.print-designer-wrapper').hide();
      this.inner_msg.show();
      this.full_page_btn.show();
      this.pdf_btn.show();
      this.letterhead_selector.show();
      this.sidebar_dynamic_section.show();
      this.print_btn.show();
      this.sidebar.show();
      this.toolbar_print_format_selector.$wrapper.hide();
      this.toolbar_language_selector.$wrapper.hide();
      super.preview();
      
      // Show detailed error with suggestions
      frappe.show_alert(
        {
          message: __('PDF generation failed. Try: 1) Refreshing the page, 2) Clearing browser cache, 3) Using a different PDF generator from the sidebar.'),
          indicator: 'red',
        },
        8,
      );
    };
    const onPdfLoad = () => {
      // Log successful PDF generation
      if (window.pdfLogger) {
        window.pdfLogger.logPDFSuccess(
          url,
          params.get('pdf_generator'),
          params.get('format')
        );
      }
      
      canvasContainer.style.display = 'none';
      pdfEl.style.display = 'block';
      pdfEl.style.height =
        'calc(100vh - var(--page-head-height) - var(--navbar-height))';
    };
    // Add freeze detection with timeout
    const FREEZE_TIMEOUT = 30000; // 30 seconds
    let freezeTimeout;
    
    const resetFreezeTimeout = () => {
      if (freezeTimeout) {
        clearTimeout(freezeTimeout);
      }
      freezeTimeout = setTimeout(() => {
        if (window.pdfLogger) {
          window.pdfLogger.logPDFFreeze(
            url,
            params.get('pdf_generator'),
            params.get('format'),
            FREEZE_TIMEOUT
          );
        }
        
        // Show freeze alert
        frappe.show_alert({
          message: __('PDF generation appears to be stuck. This may be due to server overload or network issues.'),
          indicator: 'orange'
        }, 10);
        
        // Auto-retry after showing freeze alert
        setTimeout(() => {
          if (confirm(__('PDF generation seems frozen. Would you like to retry?'))) {
            location.reload();
          }
        }, 2000);
      }, FREEZE_TIMEOUT);
    };
    
    // Start freeze detection
    resetFreezeTimeout();
    
    pdfEl.addEventListener('load', () => {
      if (freezeTimeout) {
        clearTimeout(freezeTimeout);
      }
      onPdfLoad();
    });
    
    pdfEl.addEventListener('error', () => {
      if (freezeTimeout) {
        clearTimeout(freezeTimeout);
      }
      onError();
    });
    
    // Clear timeout on component cleanup
    $(document).on('beforeunload', () => {
      if (freezeTimeout) {
        clearTimeout(freezeTimeout);
      }
    });
  }
  printit() {
    // If copy functionality is enabled, use our custom logic
    if (this.enable_copies_item && this.enable_copies_item.value) {
      // For copies, redirect to PDF download instead of direct printing
      // since browser printing doesn't support our copy logic
      frappe.show_alert({
        message: __('Multiple copies detected. Downloading PDF for printing...'),
        indicator: 'blue'
      });
      this.render_pdf();
      return;
    }
    
    // Enable Network Printing
    if (parseInt(this.print_settings.enable_print_server)) {
      super.printit();
      return;
    }
    super.printit();
  }
  show(frm) {
    super.show(frm);
    // Restore user's preferred language after parent initialization
    this.restore_user_language();
    this.inner_msg = this.page.add_inner_message(`
				<a style="line-height: 2.4" href="/app/print-designer?doctype=${this.frm.doctype}">
					${__('Try the new Print Designer')}
				</a>
			`);
  }
  preview() {
    let print_format = this.get_print_format();
    if (print_format.print_designer && print_format.print_designer_body) {
      this.inner_msg.hide();
      this.print_wrapper.find('.print-preview-wrapper').hide();
      this.print_wrapper.find('.preview-beta-wrapper').hide();
      this.print_wrapper.find('.print-designer-wrapper').show();
      this.designer_pdf(print_format);
      this.full_page_btn.hide();
      this.pdf_btn.hide();
      this.page.add_menu_item('Download PDF', () => this.render_pdf());
      
      // Add debug menu for PDF generation logs
      this.page.add_menu_item('View PDF Logs', () => this.showPDFLogs());
      this.page.add_menu_item('Export PDF Logs', () => this.exportPDFLogs());
      this.page.add_menu_item('Clear PDF Logs', () => this.clearPDFLogs());
      this.print_btn.hide();
      this.letterhead_selector.hide();
      this.sidebar_dynamic_section.hide();
      this.sidebar.hide();
      this.toolbar_print_format_selector.$wrapper.show();
      this.toolbar_language_selector.$wrapper.show();
      return;
    }
    this.print_wrapper.find('.print-designer-wrapper').hide();
    this.inner_msg.show();
    this.full_page_btn.show();
    this.pdf_btn.show();
    this.print_btn.show();
    this.letterhead_selector.show();
    this.sidebar_dynamic_section.show();
    this.sidebar.show();
    this.toolbar_print_format_selector.$wrapper.hide();
    this.toolbar_language_selector.$wrapper.hide();
    super.preview();
  }
  setup_toolbar() {
    this.print_btn = this.page.set_primary_action(
      __('Print'),
      () => this.printit(),
      'printer',
    );

    this.full_page_btn = this.page.add_button(
      __('Full Page'),
      () => this.render_page('/printview?'),
      {
        icon: 'full-page',
      },
    );

    this.pdf_btn = this.page.add_button(__('PDF'), () => this.render_pdf(), {
      icon: 'small-file',
    });

    this.refresh_btn = this.page.add_button(
      __('Refresh'),
      () => this.refresh_print_format(),
      {
        icon: 'refresh',
      },
    );

    this.page.add_action_icon(
      'file',
      () => {
        this.go_to_form_view();
      },
      '',
      __('Form'),
    );
  }
  setup_sidebar() {
    this.sidebar = this.page.sidebar.addClass('print-preview-sidebar');

    this.print_format_item = this.add_sidebar_item({
      fieldtype: 'Link',
      fieldname: 'print_format',
      options: 'Print Format',
      placeholder: __('Print Format'),
      get_query: () => {
        return { filters: { doc_type: this.frm.doctype } };
      },
      change: () => {
        if (this.print_format_item.value == this.print_format_item.last_value)
          return;
        this.toolbar_print_format_selector.set_value(
          this.print_format_item.value,
        );
        this.refresh_print_format();
      },
    });
    this.print_format_selector = this.print_format_item.$input;

    this.language_item = this.add_sidebar_item({
      fieldtype: 'Link',
      fieldname: 'language',
      placeholder: __('Language'),
      options: 'Language',
      change: () => {
        if (this.language_item.value == this.language_item.last_value) return;
        this.toolbar_language_selector.set_value(this.language_item.value);
        this.set_user_lang();
        this.refresh_copy_options_labels();
        this.preview();
      },
    });
    this.language_selector = this.language_item.$input;

    this.letterhead_selector = this.add_sidebar_item({
      fieldtype: 'Link',
      fieldname: 'letterhead',
      options: 'Letter Head',
      placeholder: __('Letter Head'),
      change: () => this.preview(),
    }).$input;
    this.sidebar_dynamic_section = $(
      `<div class="dynamic-settings"></div>`,
    ).appendTo(this.sidebar);

    // Add PDF generator selection section
    if (!this.pdf_generator_initialized) {
      this.pdf_generator_initialized = true;
      
      this.pdf_generator_section = $(`
        <div class="pdf-generator-section" style="margin-top: 20px; padding: 10px; border-top: 1px solid #e6e6e6;">
          <div style="font-weight: bold; margin-bottom: 10px; color: #555;">${__('PDF Generator')}</div>
        </div>
      `).appendTo(this.sidebar);

      // PDF Generator selector
      this.pdf_generator_item = this.add_sidebar_item({
        fieldtype: 'Select',
        fieldname: 'pdf_generator',
        label: __('PDF Generator'),
        options: [
          'auto',
          'WeasyPrint', 
          'wkhtmltopdf',
          'chrome'
        ].join('\n'),
        default: 'auto',
        description: __('Auto selects the best available generator'),
        change: () => {
          if (this.pdf_generator_item.value === 'auto') {
            // Let the system choose the best generator
            this.selected_pdf_generator = null;
          } else {
            this.selected_pdf_generator = this.pdf_generator_item.value;
          }
          this.preview(); // Refresh preview with new generator
        },
      });
    }

    // Add copy options section only if not already added
    if (!this.copy_options_initialized) {
      this.copy_options_initialized = true;
      
      this.copy_section = $(`
        <div class="copy-options-section" style="margin-top: 20px; padding: 10px; border-top: 1px solid #e6e6e6;">
          <div style="font-weight: bold; margin-bottom: 10px; color: #555;">${__('Copy Options')}</div>
        </div>
      `).appendTo(this.sidebar);

      // Enable copies checkbox
      this.enable_copies_item = this.add_sidebar_item({
        fieldtype: 'Check',
        fieldname: 'enable_copies',
        label: __('Generate Multiple Copies'),
        default: 0,
        change: () => {
          if (this.enable_copies_item.value) {
            this.copy_count_item.$wrapper.show();
            this.copy_labels_item.$wrapper.show();
          } else {
            this.copy_count_item.$wrapper.hide();
            this.copy_labels_item.$wrapper.hide();
          }
        },
      });

      // Number of copies
      this.copy_count_item = this.add_sidebar_item({
        fieldtype: 'Int',
        fieldname: 'copy_count',
        label: __('Number of Copies'),
        default: 2,
        description: __('Total number of copies to generate'),
      });

      // Custom labels
      this.copy_labels_item = this.add_sidebar_item({
        fieldtype: 'Small Text',
        fieldname: 'copy_labels',
        label: __('Copy Labels'),
        placeholder: __('Original, Copy') + ' (' + __('Optional') + ')',
        description: __('Comma-separated labels for each copy'),
      });

      // Initially hide copy options
      this.copy_count_item.$wrapper.hide();
      this.copy_labels_item.$wrapper.hide();
    }
  }
  refresh_copy_options_labels() {
    // Refresh copy options section title and labels after language change
    if (this.copy_section) {
      this.copy_section.find('div:first').text(__('Copy Options'));
    }
    
    // Refresh field labels
    if (this.enable_copies_item) {
      this.enable_copies_item.df.label = __('Generate Multiple Copies');
      this.enable_copies_item.refresh();
    }
    
    if (this.copy_count_item) {
      this.copy_count_item.df.label = __('Number of Copies');
      this.copy_count_item.df.description = __('Total number of copies to generate');
      this.copy_count_item.refresh();
    }
    
    if (this.copy_labels_item) {
      this.copy_labels_item.df.label = __('Copy Labels');
      this.copy_labels_item.df.placeholder = __('Original, Copy') + ' (' + __('Optional') + ')';
      this.copy_labels_item.df.description = __('Comma-separated labels for each copy');
      this.copy_labels_item.refresh();
    }
  }
  set_default_print_language() {
    super.set_default_print_language();
    this.toolbar_language_selector.$input.val(this.lang_code);
  }
  set_user_lang() {
    // Update lang_code when language is changed
    this.lang_code = this.language_item.value || 'en';
    // Store user's language preference in localStorage
    localStorage.setItem('print_designer_language', this.lang_code);
    super.set_user_lang();
  }
  restore_user_language() {
    // Restore user's preferred language from localStorage
    const stored_lang = localStorage.getItem('print_designer_language');
    if (stored_lang && stored_lang !== this.lang_code) {
      this.lang_code = stored_lang;
      if (this.language_item) {
        this.language_item.set_value(stored_lang);
      }
      if (this.toolbar_language_selector) {
        this.toolbar_language_selector.set_value(stored_lang);
      }
    }
  }
  set_default_print_format() {
    super.set_default_print_format();
    if (
      frappe.meta
        .get_print_formats(this.frm.doctype)
        .includes(this.toolbar_print_format_selector.$input.val())
    )
      return;
    if (!this.frm.meta.default_print_format) {
      let pd_print_format = '';
      if (this.frm.doctype == 'Sales Invoice') {
        pd_print_format = 'Sales Invoice PD Format v2';
      } else if (this.frm.doctype == 'Sales Order') {
        pd_print_format = 'Sales Order PD v2';
      }
      if (pd_print_format) {
        this.print_format_selector.val(pd_print_format);
        this.toolbar_print_format_selector.$input.val(pd_print_format);
      }
      return;
    }
    this.toolbar_print_format_selector.$input.empty();
    this.toolbar_print_format_selector.$input.val(
      this.frm.meta.default_print_format,
    );
  }
  render_pdf() {
    // Construct PDF URL like the parent class
    let params = new URLSearchParams({
      doctype: this.frm.doctype,
      name: this.frm.docname,
      format: this.selected_format(),
      _lang: this.lang_code,
    });

    // Add PDF generator parameter
    const selected_generator = this.selected_pdf_generator || 'auto';
    params.set('pdf_generator', selected_generator);

    // Add copy parameters if enabled
    if (this.enable_copies_item && this.enable_copies_item.value) {
      params.set('copy_count', this.copy_count_item.value || 2);
      if (this.copy_labels_item.value) {
        params.set('copy_labels', this.copy_labels_item.value);
      }
      
      // For copies, prefer wkhtmltopdf unless Chrome is explicitly selected
      if (!this.selected_pdf_generator || this.selected_pdf_generator === 'auto') {
        params.set('pdf_generator', 'wkhtmltopdf');
        
        // Inform user about the change
        frappe.show_alert({
          message: __('Copy functionality works best with wkhtmltopdf. Letter Head is available.'),
          indicator: 'blue'
        }, 5);
      }
    }

    // Add letterhead if selected (works with wkhtmltopdf)
    if (this.letterhead_selector && this.letterhead_selector.val()) {
      params.set('letterhead', this.letterhead_selector.val());
    }
    
    // Construct the full URL
    let url = `${window.location.origin}/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`;
    console.log('PDF URL with copy parameters:', url);
    
    // Open the PDF download
    window.open(url, '_blank');
  }

  download_pdf() {
    this.pdfDoc.getData().then((arrBuff) => {
      const downloadFile = (blob, fileName) => {
        const link = document.createElement('a');
        // create a blobURI pointing to our Blob
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        // some browser needs the anchor to be in the doc
        document.body.append(link);
        link.click();
        link.remove();
        // in case the Blob uses a lot of memory
        setTimeout(() => URL.revokeObjectURL(link.href), 7000);
      };
      downloadFile(
        new Blob([arrBuff], { type: 'application/pdf' }),
        `${frappe.get_route().slice(2).join('/')}.pdf`,
      );
    });
  }

  // Debug methods for PDF generation logs
  async showPDFLogs() {
    if (!window.pdfLogger) {
      frappe.show_alert({
        message: __('PDF Logger not available'),
        indicator: 'red'
      });
      return;
    }

    try {
      const response = await window.pdfLogger.getRecentLogs(100);
      if (response.success) {
        const logs = response.logs.join('\n');
        frappe.msgprint({
          title: __('PDF Generation Logs'),
          message: `<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 400px; overflow-y: auto;">${logs}</pre>`,
          wide: true
        });
      } else {
        frappe.show_alert({
          message: __('Failed to retrieve logs: {0}', [response.message]),
          indicator: 'red'
        });
      }
    } catch (error) {
      frappe.show_alert({
        message: __('Error retrieving logs: {0}', [error.message]),
        indicator: 'red'
      });
    }
  }

  exportPDFLogs() {
    if (!window.pdfLogger) {
      frappe.show_alert({
        message: __('PDF Logger not available'),
        indicator: 'red'
      });
      return;
    }

    try {
      window.pdfLogger.exportSessionLogs();
      frappe.show_alert({
        message: __('PDF logs exported successfully'),
        indicator: 'green'
      });
    } catch (error) {
      frappe.show_alert({
        message: __('Error exporting logs: {0}', [error.message]),
        indicator: 'red'
      });
    }
  }

  async clearPDFLogs() {
    if (!window.pdfLogger) {
      frappe.show_alert({
        message: __('PDF Logger not available'),
        indicator: 'red'
      });
      return;
    }

    if (confirm(__('Are you sure you want to clear all PDF generation logs?'))) {
      try {
        const response = await window.pdfLogger.clearLogs();
        if (response.success) {
          frappe.show_alert({
            message: __('PDF logs cleared successfully'),
            indicator: 'green'
          });
        } else {
          frappe.show_alert({
            message: __('Failed to clear logs: {0}', [response.message]),
            indicator: 'red'
          });
        }
      } catch (error) {
        frappe.show_alert({
          message: __('Error clearing logs: {0}', [error.message]),
          indicator: 'red'
        });
      }
    }
  }
};
