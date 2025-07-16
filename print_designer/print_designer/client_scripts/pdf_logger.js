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
        return `pdf_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
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
                method: 'print_designer.print_designer.page.print_designer.print_designer.log_pdf_generation_issue',
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
            mimeTypes: navigator.mimeTypes && navigator.mimeTypes['application/pdf']
        };
    }

    // Utility methods
    async getRecentLogs(limit = 50, logLevel = null) {
        try {
            const response = await frappe.call({
                method: 'print_designer.print_designer.page.print_designer.print_designer.get_pdf_generation_logs',
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
                method: 'print_designer.print_designer.page.print_designer.print_designer.clear_pdf_generation_logs'
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
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PDFGenerationLogger;
}