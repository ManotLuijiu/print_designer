/**
 * Dynamic Typography Injection System
 * 
 * This script dynamically injects typography CSS from Global Defaults
 * to ensure real-time font changes without requiring page refresh.
 */

(function() {
    'use strict';
    
    // Create a style element for dynamic typography
    let dynamicTypographyStyle = null;
    
    /**
     * Initialize dynamic typography injection
     */
    function initDynamicTypography() {
        // Create style element if it doesn't exist
        if (!dynamicTypographyStyle) {
            dynamicTypographyStyle = document.createElement('style');
            dynamicTypographyStyle.id = 'dynamic-typography-override';
            dynamicTypographyStyle.type = 'text/css';
            document.head.appendChild(dynamicTypographyStyle);
        }
        
        // Load and apply typography CSS
        loadTypographyCSS();
    }
    
    /**
     * Load typography CSS from Global Defaults
     */
    function loadTypographyCSS() {
        // Make API call to get current typography CSS
        frappe.call({
            method: 'print_designer.api.global_typography.get_typography_css',
            callback: function(response) {
                if (response.message && dynamicTypographyStyle) {
                    // Inject the CSS
                    dynamicTypographyStyle.textContent = response.message;
                    
                    // Extract font stack from CSS for immediate application
                    const fontStackMatch = response.message.match(/--font-stack:\s*([^;]+);/);
                    if (fontStackMatch) {
                        const fontStack = fontStackMatch[1].trim();
                        // Apply immediately to CSS custom property
                        document.documentElement.style.setProperty('--font-stack', fontStack, 'important');
                    }
                }
            },
            error: function(error) {
                console.warn('Failed to load dynamic typography CSS:', error);
            }
        });
    }
    
    /**
     * Refresh typography when settings change
     */
    function refreshTypography() {
        loadTypographyCSS();
    }
    
    // Make refreshTypography globally available
    window.refreshTypography = refreshTypography;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDynamicTypography);
    } else {
        initDynamicTypography();
    }
    
    // Listen for typography update events
    $(document).on('typography-updated', function() {
        refreshTypography();
    });
    
    // Auto-refresh every 30 seconds to catch external changes
    setInterval(function() {
        loadTypographyCSS();
    }, 30000);
    
})();