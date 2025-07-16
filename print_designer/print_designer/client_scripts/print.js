// TODO: revisit and properly implement this client script

/**
 * Print Designer PDF Generation Logger
 * 
 * Client-side utility for logging PDF generation issues to server-side log files.
 * This helps debug PDF generation freezing and other issues.
 */
class PDFGenerationLogger {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.logQueue = [];
        this.isProcessing = false;
        this.maxQueueSize = 100;
        this.enableConsoleLogging = true;
        this.enableServerLogging = true;
        
        // Performance monitoring
        this.performanceMetrics = {
            startTime: null,
            endTime: null,
            retryCount: 0,
            generatorAttempts: []
        };
    }

    generateSessionId() {
        return `pdf_session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    }

    /**
     * Log a PDF generation event
     * @param {string} eventType - Type of event (PDF_GENERATION_START, PDF_GENERATION_ERROR, etc.)
     * @param {string} message - Human-readable message
     * @param {object} details - Additional details
     * @param {string} logLevel - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
     */
    async log(eventType, message, details = {}, logLevel = 'INFO') {
        const timestamp = new Date().toISOString();
        const logEntry = {
            sessionId: this.sessionId,
            eventType,
            message,
            timestamp,
            details: {
                ...details,
                url: window.location.href,
                userAgent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            },
            logLevel
        };

        // Add to queue
        this.logQueue.push(logEntry);
        
        // Limit queue size
        if (this.logQueue.length > this.maxQueueSize) {
            this.logQueue.shift();
        }

        // Console logging
        if (this.enableConsoleLogging) {
            const consoleMethod = this.getConsoleMethod(logLevel);
            consoleMethod(`[PDFLogger] [${eventType}] ${message}`, details);
        }

        // Server logging
        if (this.enableServerLogging) {
            await this.sendToServer(logEntry);
        }

        return logEntry;
    }

    getConsoleMethod(logLevel) {
        switch (logLevel.toUpperCase()) {
            case 'DEBUG':
                return console.debug;
            case 'INFO':
                return console.info;
            case 'WARNING':
                return console.warn;
            case 'ERROR':
            case 'CRITICAL':
                return console.error;
            default:
                return console.log;
        }
    }

    async sendToServer(logEntry) {
        if (this.isProcessing) {
            return;
        }

        try {
            this.isProcessing = true;
            
            await frappe.call({
                method: 'print_designer.pdf_logging.log_pdf_generation_issue',
                args: {
                    event_type: logEntry.eventType,
                    message: logEntry.message,
                    details: JSON.stringify(logEntry.details),
                    log_level: logEntry.logLevel
                },
                callback: (response) => {
                    if (!response.message.success) {
                        console.error('Failed to log to server:', response.message.message);
                    }
                }
            });
        } catch (error) {
            console.error('Error sending log to server:', error);
        } finally {
            this.isProcessing = false;
        }
    }

    // Performance monitoring methods
    startPerformanceMonitoring() {
        this.performanceMetrics.startTime = performance.now();
        this.performanceMetrics.retryCount = 0;
        this.performanceMetrics.generatorAttempts = [];
        
        this.log('PDF_GENERATION_START', 'PDF generation started', {
            startTime: this.performanceMetrics.startTime
        });
    }

    endPerformanceMonitoring(success = true) {
        this.performanceMetrics.endTime = performance.now();
        const duration = this.performanceMetrics.endTime - this.performanceMetrics.startTime;
        
        this.log(
            success ? 'PDF_GENERATION_SUCCESS' : 'PDF_GENERATION_FAILED',
            `PDF generation ${success ? 'completed' : 'failed'} in ${duration.toFixed(2)}ms`,
            {
                duration,
                retryCount: this.performanceMetrics.retryCount,
                generatorAttempts: this.performanceMetrics.generatorAttempts,
                endTime: this.performanceMetrics.endTime
            },
            success ? 'INFO' : 'ERROR'
        );
    }

    recordGeneratorAttempt(generator, success = false) {
        this.performanceMetrics.generatorAttempts.push({
            generator,
            success,
            timestamp: performance.now()
        });
        
        if (!success) {
            this.performanceMetrics.retryCount++;
        }
    }

    // Specialized logging methods for common events
    logPDFStart(url, generator, format) {
        this.startPerformanceMonitoring();
        return this.log('PDF_GENERATION_START', 'Starting PDF generation', {
            url,
            generator,
            format,
            browserInfo: {
                browser: this.getBrowserInfo(),
                pdfSupport: this.checkPDFSupport()
            }
        });
    }

    logPDFError(url, generator, format, error) {
        this.recordGeneratorAttempt(generator, false);
        return this.log('PDF_GENERATION_ERROR', 'PDF generation failed', {
            url,
            generator,
            format,
            error: error.toString(),
            stackTrace: error.stack
        }, 'ERROR');
    }

    logPDFFreeze(url, generator, format, timeoutDuration) {
        return this.log('PDF_GENERATION_FREEZE', 'PDF generation appears to be frozen', {
            url,
            generator,
            format,
            timeoutDuration,
            possibleCauses: [
                'Network timeout',
                'Server overload',
                'Browser compatibility issue',
                'PDF generation process stuck'
            ]
        }, 'ERROR');
    }

    logPDFRetry(url, newGenerator, previousGenerator, retryCount) {
        this.recordGeneratorAttempt(previousGenerator, false);
        return this.log('PDF_GENERATION_RETRY', `Retrying PDF generation with ${newGenerator}`, {
            url,
            newGenerator,
            previousGenerator,
            retryCount,
            retryReason: `${previousGenerator} failed or timed out`
        }, 'WARNING');
    }

    logPDFSuccess(url, generator, format) {
        this.recordGeneratorAttempt(generator, true);
        this.endPerformanceMonitoring(true);
        return this.log('PDF_GENERATION_SUCCESS', 'PDF generation completed successfully', {
            url,
            generator,
            format
        }, 'INFO');
    }

    // Browser detection and support checking
    getBrowserInfo() {
        const userAgent = navigator.userAgent;
        let browser = 'Unknown';
        
        if (userAgent.includes('Chrome')) browser = 'Chrome';
        else if (userAgent.includes('Firefox')) browser = 'Firefox';
        else if (userAgent.includes('Safari')) browser = 'Safari';
        else if (userAgent.includes('Edge')) browser = 'Edge';
        
        return {
            name: browser,
            userAgent,
            version: this.getBrowserVersion(userAgent)
        };
    }

    getBrowserVersion(userAgent) {
        const match = userAgent.match(/(Chrome|Firefox|Safari|Edge)\/(\d+)/);
        return match ? match[2] : 'Unknown';
    }

    checkPDFSupport() {
        return {
            objectTag: 'object' in document.createElement('object'),
            embedTag: 'embed' in document.createElement('embed'),
            plugins: navigator.plugins && navigator.plugins.length > 0,
            mimeTypes: navigator.mimeTypes && navigator.mimeTypes['application/pdf'],
            // Modern PDF support detection
            pdfViewerSupported: 'PDFViewer' in window || 'chrome' in window && 'webstore' in window.chrome
        };
    }

    // Utility methods
    async getRecentLogs(limit = 50, logLevel = null) {
        try {
            const response = await frappe.call({
                method: 'print_designer.pdf_logging.get_pdf_generation_logs',
                args: {
                    limit,
                    log_level: logLevel
                }
            });
            
            return response.message;
        } catch (error) {
            console.error('Error fetching logs:', error);
            return { success: false, message: error.toString() };
        }
    }

    async clearLogs() {
        try {
            const response = await frappe.call({
                method: 'print_designer.pdf_logging.clear_pdf_generation_logs'
            });
            
            return response.message;
        } catch (error) {
            console.error('Error clearing logs:', error);
            return { success: false, message: error.toString() };
        }
    }

    // Export current session logs
    exportSessionLogs() {
        const sessionLogs = this.logQueue.filter(log => log.sessionId === this.sessionId);
        const blob = new Blob([JSON.stringify(sessionLogs, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pdf_logs_${this.sessionId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Create global instance
if (!window.pdfLogger) {
    window.pdfLogger = new PDFGenerationLogger();
    // Log initialization for testing
    window.pdfLogger.log('LOGGER_INITIALIZED', 'PDF Logger initialized successfully', {
        loggerVersion: '1.0',
        initTime: new Date().toISOString()
    }, 'INFO');
}

frappe.pages['print'].on_page_load = function (wrapper) {
  frappe.require(['pdfjs.bundle.css', 'print_designer.bundle.css']);
  
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
  
  createPdfFallback(url, wrapperContainer) {
    // Create an iframe fallback for browsers without PDF plugin support
    let iframeEl = document.getElementById('pd-pdf-iframe');
    if (!iframeEl) {
      iframeEl = document.createElement('iframe');
      iframeEl.id = 'pd-pdf-iframe';
      iframeEl.style.width = '100%';
      iframeEl.style.height = 'calc(100vh - var(--page-head-height) - var(--navbar-height))';
      iframeEl.style.border = 'none';
      wrapperContainer.appendChild(iframeEl);
    }
    
    iframeEl.src = url;
    return iframeEl;
  }
  
  createDownloadFallback(url, wrapperContainer) {
    // Create download fallback when PDF can't be displayed
    let downloadEl = document.getElementById('pd-pdf-download');
    if (!downloadEl) {
      downloadEl = document.createElement('div');
      downloadEl.id = 'pd-pdf-download';
      downloadEl.style.textAlign = 'center';
      downloadEl.style.padding = '50px';
      downloadEl.style.backgroundColor = '#f8f9fa';
      downloadEl.style.border = '2px dashed #dee2e6';
      downloadEl.style.borderRadius = '8px';
      downloadEl.innerHTML = `
        <div style="margin-bottom: 20px;">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10,9 9,9 8,9"/>
          </svg>
        </div>
        <h4 style="margin-bottom: 10px; color: #495057;">${__('PDF Preview Unavailable')}</h4>
        <p style="color: #6c757d; margin-bottom: 20px;">${__('Your browser cannot display PDFs inline. Please download the PDF to view it.')}</p>
        <a href="${url}" target="_blank" class="btn btn-primary" style="text-decoration: none; display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; border-radius: 5px;">${__('Download PDF')}</a>
      `;
      wrapperContainer.appendChild(downloadEl);
    }
    
    // Update the download link
    const downloadLink = downloadEl.querySelector('a');
    if (downloadLink) {
      downloadLink.href = url;
    }
    
    return downloadEl;
  }
  
  async checkPDFUrl(url) {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      return {
        valid: response.ok && response.headers.get('content-type')?.includes('application/pdf'),
        status: response.status,
        statusText: response.statusText,
        contentType: response.headers.get('content-type'),
        isPermissionError: response.status === 403,
        isServerError: response.status >= 500,
        isClientError: response.status >= 400 && response.status < 500
      };
    } catch (error) {
      return {
        valid: false,
        error: error.message,
        isNetworkError: true
      };
    }
  }
  
  showDownloadFallback(url, wrapperContainer, canvasContainer) {
    // Log final failure
    if (window.pdfLogger) {
      window.pdfLogger.log('PDF_GENERATION_FINAL_FAILURE', 'All PDF generation and display attempts failed', {
        url: url,
        attempts: this.pdf_retry_attempted ? 2 : 1,
        iframe_attempted: this.iframe_fallback_attempted || false,
        fallback_type: 'download'
      }, 'CRITICAL');
    }
    
    // Hide loading indicator
    canvasContainer.style.display = 'none';
    
    // Hide any existing PDF elements
    const existingPdfEl = document.getElementById('pd-pdf-viewer');
    if (existingPdfEl) {
      existingPdfEl.style.display = 'none';
    }
    
    const existingIframeEl = document.getElementById('pd-pdf-iframe');
    if (existingIframeEl) {
      existingIframeEl.style.display = 'none';
    }
    
    // Show download fallback
    const downloadEl = this.createDownloadFallback(url, wrapperContainer);
    downloadEl.style.display = 'block';
    
    // Show detailed error with suggestions
    frappe.show_alert(
      {
        message: __('PDF cannot be displayed inline. Please download the PDF to view it, or try using a different PDF generator from the sidebar.'),
        indicator: 'orange',
      },
      8,
    );
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
    
    let params = new URLSearchParams({
      doctype: this.frm.doc.doctype,
      name: this.frm.doc.name,
      format: this.selected_format(),
      _lang: this.lang_code,
    });

    // Add PDF generator parameter - only send if not auto
    const selected_generator = this.selected_pdf_generator || 'auto';
    if (selected_generator !== 'auto') {
      params.set('pdf_generator', selected_generator);
    }

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

    // Show enhanced loading state with generator information
    const loadingHTML = `
      <div class="print-loading-container" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 40px; background: #f8f9fa; border-radius: 8px; margin: 20px;">
        <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem; margin-bottom: 20px;">
          <span class="sr-only">Loading...</span>
        </div>
        <h4 style="color: #495057; margin-bottom: 10px;">${__('Generating PDF...')}</h4>
        <p style="color: #6c757d; text-align: center; margin-bottom: 15px;">
          ${__('Generator')}: <strong>${params.get('pdf_generator')}</strong><br>
          ${__('Format')}: <strong>${params.get('format')}</strong>
        </p>
        <div class="progress" style="width: 200px; height: 4px; background-color: #e9ecef; border-radius: 2px; overflow: hidden;">
          <div class="progress-bar progress-bar-striped progress-bar-animated" 
               role="progressbar" 
               style="width: 100%; background-color: #007bff; animation: progress-bar-stripes 1s linear infinite;">
          </div>
        </div>
        <small style="color: #6c757d; margin-top: 15px; text-align: center;">
          ${__('This may take a few moments...')}<br>
          ${__('If it takes too long, try switching to a different PDF generator from the sidebar.')}
        </small>
      </div>
    `;
    canvasContainer.innerHTML = loadingHTML;

    // Log PDF generation start
    if (window.pdfLogger) {
      window.pdfLogger.logPDFStart(url, params.get('pdf_generator') || 'auto', params.get('format'));
    }

    // Reset retry flags for each new PDF generation
    this.pdf_retry_attempted = false;
    this.iframe_fallback_attempted = false;
    this.letterhead_retry_attempted = false;

    const pdfEl = this.createPdfEl(url, wrapperContainer);
    const onError = () => {
      // Log the error with comprehensive details
      if (window.pdfLogger) {
        window.pdfLogger.logPDFError(
          url,
          params.get('pdf_generator') || 'auto',
          params.get('format'),
          new Error('PDF Object failed to load')
        );
      }
      
      // Try to get more specific error information
      console.error('PDF Generation Error:', {
        url: url,
        generator: params.get('pdf_generator') || 'auto',
        format: params.get('format')
      });
      
      // Before trying retries or fallbacks, check if the PDF URL is valid
      this.checkPDFUrl(url).then(urlCheck => {
        // Handle specific error types
        if (urlCheck.isPermissionError) {
          // 403 Forbidden - This might be due to letterhead permissions
          if (window.pdfLogger) {
            window.pdfLogger.log('PDF_PERMISSION_ERROR', 'PDF generation failed due to permission error', {
              url: url,
              status: urlCheck.status,
              statusText: urlCheck.statusText,
              generator: params.get('pdf_generator') || 'auto',
              format: params.get('format'),
              hasLetterhead: !!(this.letterhead_selector && this.letterhead_selector.val())
            }, 'ERROR');
          }
          
          // If letterhead is selected, try without it
          if (this.letterhead_selector && this.letterhead_selector.val() && !this.letterhead_retry_attempted) {
            this.letterhead_retry_attempted = true;
            
            frappe.show_alert({
              message: __('Permission denied with letterhead. Retrying without letterhead...'),
              indicator: 'orange'
            }, 3);
            
            // Remove letterhead and retry
            const originalLetterhead = this.letterhead_selector.val();
            this.letterhead_selector.val('');
            params.delete('letterhead');
            
            const retryUrl = `${window.location.origin}/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`;
            
            setTimeout(() => {
              if (pdfEl.parentNode) {
                pdfEl.parentNode.removeChild(pdfEl);
              }
              
              // Create a new PDF object for the retry
              const newPdfEl = this.createPdfEl(retryUrl, wrapperContainer);
              
              // Set up event listeners for the new PDF object
              newPdfEl.addEventListener('load', () => {
                if (freezeTimeout) {
                  clearTimeout(freezeTimeout);
                }
                onPdfLoad();
                
                // Notify user about successful retry without letterhead
                frappe.show_alert({
                  message: __('PDF generated successfully without letterhead'),
                  indicator: 'green'
                }, 3);
              });
              
              newPdfEl.addEventListener('error', () => {
                if (freezeTimeout) {
                  clearTimeout(freezeTimeout);
                }
                // Restore letterhead selection for user
                this.letterhead_selector.val(originalLetterhead);
                onError();
              });
              
              // Reset freeze timeout for retry
              resetFreezeTimeout();
            }, 1000);
            
            return;
          }
          
          let errorMessage = __('PDF generation failed: Access denied (403)');
          if (this.letterhead_selector && this.letterhead_selector.val()) {
            errorMessage += '. ' + __('This might be due to letterhead permissions. Try generating without letterhead.');
          }
          
          frappe.show_alert({
            message: errorMessage,
            indicator: 'red'
          }, 10);
          
          this.showDownloadFallback(url, wrapperContainer, canvasContainer);
          return;
        }
        
        if (urlCheck.isServerError) {
          // 500+ Server Error - Don't retry with different generators, this is a server issue
          if (window.pdfLogger) {
            window.pdfLogger.log('PDF_SERVER_ERROR', 'PDF generation failed due to server error', {
              url: url,
              status: urlCheck.status,
              statusText: urlCheck.statusText,
              generator: params.get('pdf_generator') || 'auto',
              format: params.get('format')
            }, 'ERROR');
          }
          
          frappe.show_alert({
            message: __('PDF generation failed: Server error ({0}). Please try again later.', [urlCheck.status]),
            indicator: 'red'
          }, 8);
          
          this.showDownloadFallback(url, wrapperContainer, canvasContainer);
          return;
        }
        
        if (urlCheck.isNetworkError) {
          // Network error - Don't retry with different generators
          if (window.pdfLogger) {
            window.pdfLogger.log('PDF_NETWORK_ERROR', 'PDF generation failed due to network error', {
              url: url,
              error: urlCheck.error,
              generator: params.get('pdf_generator') || 'auto',
              format: params.get('format')
            }, 'ERROR');
          }
          
          frappe.show_alert({
            message: __('PDF generation failed: Network error. Please check your connection.'),
            indicator: 'red'
          }, 8);
          
          this.showDownloadFallback(url, wrapperContainer, canvasContainer);
          return;
        }
        
        // Try alternative PDF generators if auto-selection failed (only for client-side display issues)
        const currentGenerator = params.get('pdf_generator');
        const alternativeGenerators = ['wkhtmltopdf', 'chrome'].filter(g => g !== currentGenerator);
        
        if (alternativeGenerators.length > 0 && !this.pdf_retry_attempted && !urlCheck.isClientError) {
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
          
          // Remove the failed PDF object and create a new one
          setTimeout(() => {
            if (pdfEl.parentNode) {
              pdfEl.parentNode.removeChild(pdfEl);
            }
            
            // Create a new PDF object for the retry
            const newPdfEl = this.createPdfEl(retryUrl, wrapperContainer);
            
            // Set up event listeners for the new PDF object
            newPdfEl.addEventListener('load', () => {
              if (freezeTimeout) {
                clearTimeout(freezeTimeout);
              }
              onPdfLoad();
            });
            
            newPdfEl.addEventListener('error', () => {
              if (freezeTimeout) {
                clearTimeout(freezeTimeout);
              }
              onError();
            });
            
            // Reset freeze timeout for retry
            resetFreezeTimeout();
          }, 1000);
          
          return;
        }
        
        // For other client errors or when retries are exhausted, continue with fallback logic
        if (!urlCheck.valid) {
          // Other unhandled errors
          if (window.pdfLogger) {
            window.pdfLogger.log('PDF_UNKNOWN_ERROR', 'PDF generation failed with unknown error', {
              url: url,
              urlCheck: urlCheck,
              generator: params.get('pdf_generator') || 'auto',
              format: params.get('format')
            }, 'ERROR');
          }
          
          this.showDownloadFallback(url, wrapperContainer, canvasContainer);
          return;
        }
        
        // PDF URL is valid, try iframe fallback if we haven't already
        if (!this.iframe_fallback_attempted) {
          this.iframe_fallback_attempted = true;
          
          // Log iframe fallback attempt
          if (window.pdfLogger) {
            window.pdfLogger.log('PDF_FALLBACK_IFRAME', 'Attempting iframe fallback for PDF display', {
              url: url,
              generator: params.get('pdf_generator'),
              format: params.get('format')
            }, 'INFO');
          }
          
          // Hide the failed object element
          pdfEl.style.display = 'none';
          
          // Try iframe fallback
          const iframeEl = this.createPdfFallback(url, wrapperContainer);
          
          // Set up iframe error handling
          iframeEl.onload = () => {
            canvasContainer.style.display = 'none';
            iframeEl.style.display = 'block';
            
            if (window.pdfLogger) {
              window.pdfLogger.log('PDF_FALLBACK_SUCCESS', 'Iframe fallback successful', {
                url: url,
                generator: params.get('pdf_generator'),
                format: params.get('format')
              }, 'INFO');
            }
          };
          
          iframeEl.onerror = () => {
            // Even iframe failed, show download fallback
            this.showDownloadFallback(url, wrapperContainer, canvasContainer);
          };
          
          return;
        }
        
        // Both object and iframe failed, show download fallback
        this.showDownloadFallback(url, wrapperContainer, canvasContainer);
      }).catch(error => {
        // Error checking URL, proceed with fallback
        console.error('Error checking PDF URL:', error);
        this.showDownloadFallback(url, wrapperContainer, canvasContainer);
      });
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
      // Keep sidebar visible for print designer formats but hide redundant sections
      this.sidebar.show();
      // Hide specific form elements that are now in the toolbar
      if (this.print_format_item) {
        this.print_format_item.$wrapper.hide();
      }
      if (this.language_item) {
        this.language_item.$wrapper.hide();
      }
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
    // Restore sidebar form elements for non-print designer formats
    if (this.print_format_item) {
      this.print_format_item.$wrapper.show();
    }
    if (this.language_item) {
      this.language_item.$wrapper.show();
    }
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
          'wkhtmltopdf',
          'chrome'
        ].join('\n'),
        default: 'auto',
        description: __('Auto lets server choose the best available generator'),
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

    // Add PDF generator parameter - only send if not auto
    const selected_generator = this.selected_pdf_generator || 'auto';
    if (selected_generator !== 'auto') {
      params.set('pdf_generator', selected_generator);
    }

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
