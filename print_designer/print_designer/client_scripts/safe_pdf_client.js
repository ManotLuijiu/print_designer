/**
 * Safe PDF Client for Print Designer
 * Automatically detects third-party app conflicts and uses safe endpoints
 */

class SafePDFClient {
    constructor() {
        this.conflictsChecked = false;
        this.conflictsFound = false;
        this.safeEndpointsRecommended = false;
        this.conflictsList = [];
        this.initialized = false;
    }

    /**
     * Initialize the safe PDF client
     */
    async initialize() {
        if (this.initialized) return;

        try {
            // Check for third-party conflicts
            const response = await frappe.call({
                method: 'print_designer.utils.safe_pdf_api.check_third_party_conflicts',
                freeze: false,
                freeze_message: __('Checking for PDF conflicts...')
            });

            if (response.message) {
                this.conflictsFound = response.message.conflicts_found;
                this.safeEndpointsRecommended = response.message.safe_endpoints_recommended;
                this.conflictsList = response.message.conflicts || [];
                this.conflictsChecked = true;

                // Log conflicts if found
                if (this.conflictsFound) {
                    console.warn('Print Designer: Third-party conflicts detected:', this.conflictsList);
                    console.warn('Print Designer: Using safe endpoints for PDF generation');
                    
                    // Log to PDF logger if available
                    if (window.pdfLogger) {
                        window.pdfLogger.log('PDF_THIRD_PARTY_CONFLICT', 'Third-party conflicts detected', {
                            conflicts: this.conflictsList,
                            safeEndpointsEnabled: true
                        });
                    }
                }
            }

        } catch (error) {
            console.error('Print Designer: Failed to check for conflicts:', error);
            // Default to safe endpoints if check fails
            this.safeEndpointsRecommended = true;
            this.conflictsFound = true;
        }

        this.initialized = true;
    }

    /**
     * Get the appropriate PDF download URL
     */
    async getPDFDownloadURL(params) {
        await this.initialize();

        if (this.safeEndpointsRecommended) {
            // Use safe endpoint
            return this.buildSafeURL('print_designer.utils.safe_pdf_api.safe_download_pdf', params);
        } else {
            // Use standard endpoint
            return this.buildStandardURL('frappe.utils.print_format.download_pdf', params);
        }
    }

    /**
     * Get HTML for preview
     */
    async getHTMLPreview(params) {
        await this.initialize();

        if (this.safeEndpointsRecommended) {
            // Use safe endpoint
            try {
                const response = await frappe.call({
                    method: 'print_designer.utils.safe_pdf_api.safe_get_print_html',
                    args: params,
                    freeze: false
                });
                return response.message.html;
            } catch (error) {
                console.error('Print Designer: Safe HTML generation failed:', error);
                throw error;
            }
        } else {
            // Use standard method
            return frappe.get_print(params);
        }
    }

    /**
     * Build safe API URL
     */
    buildSafeURL(method, params) {
        const urlParams = new URLSearchParams();
        
        // Add method
        urlParams.append('method', method);
        
        // Add parameters
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                urlParams.append(key, params[key]);
            }
        });

        return `${window.location.origin}/api/method/${method}?${urlParams.toString()}`;
    }

    /**
     * Build standard API URL
     */
    buildStandardURL(method, params) {
        const urlParams = new URLSearchParams();
        
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== null) {
                urlParams.append(key, params[key]);
            }
        });

        return `${window.location.origin}/api/method/${method}?${urlParams.toString()}`;
    }

    /**
     * Get PDF generation information
     */
    async getPDFGenerationInfo() {
        try {
            const response = await frappe.call({
                method: 'print_designer.utils.safe_pdf_api.get_pdf_generation_info',
                freeze: false
            });
            return response.message;
        } catch (error) {
            console.error('Print Designer: Failed to get PDF generation info:', error);
            return null;
        }
    }

    /**
     * Check if safe endpoints are being used
     */
    isUsingSafeEndpoints() {
        return this.safeEndpointsRecommended;
    }

    /**
     * Get detected conflicts
     */
    getDetectedConflicts() {
        return this.conflictsList;
    }
}

// Create global instance
window.safePDFClient = new SafePDFClient();

// Extend the existing PDF generation function to use safe endpoints
if (typeof generatePDF !== 'undefined') {
    const originalGeneratePDF = generatePDF;
    
    generatePDF = async function(params) {
        try {
            // Use safe PDF client
            const url = await window.safePDFClient.getPDFDownloadURL(params);
            
            // Log the URL being used
            if (window.pdfLogger) {
                window.pdfLogger.log('PDF_SAFE_CLIENT_URL', 'Using safe PDF client URL', {
                    url: url,
                    safeEndpoints: window.safePDFClient.isUsingSafeEndpoints(),
                    conflicts: window.safePDFClient.getDetectedConflicts()
                });
            }
            
            // Open the PDF
            window.open(url, '_blank');
            
        } catch (error) {
            console.error('Print Designer: Safe PDF generation failed, falling back to original:', error);
            
            // Fallback to original function
            return originalGeneratePDF(params);
        }
    };
}

// Add debug information to the global scope
frappe.provide('frappe.print_designer');
frappe.print_designer.safe_pdf_client = window.safePDFClient;

// Initialize on page load
frappe.ready(() => {
    window.safePDFClient.initialize();
});

console.log('Print Designer: Safe PDF Client loaded');