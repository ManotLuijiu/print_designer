# Print Designer Client Scripts Documentation

This document describes the client-side JavaScript functionality for the Print Designer's Thai WHT and QR Delivery Approval systems.

## Overview

The `delivery_approval.js` client script provides enhanced user interface functionality for:
- **Delivery Note QR Code Generation and Management**
- **Payment Entry Thai Withholding Tax Certificate Generation**

## Features Implemented

### 🚚 Delivery Note Enhancements

#### Automatic QR Code Generation
- **Trigger**: Automatically generates QR code when Delivery Note is submitted
- **Manual Option**: "Generate QR Code" button for manual generation
- **Visual Feedback**: Progress indicators and success messages

#### Interactive QR Code Dialog
- **Professional UI**: Bootstrap-styled dialog with QR code display
- **Instructions**: Clear customer instructions for scanning
- **Status Display**: Real-time approval status with color indicators
- **URL Access**: Clickable approval URL with copy-to-clipboard functionality

#### Custom Buttons Added
```javascript
// Buttons automatically added based on document state:
- "Generate QR Code" (when submitted but no QR exists)
- "View Approval Page" (when approval URL exists)  
- "Show QR Code" (when QR code exists)
- "Print with QR" (for QR-enabled print format)
```

#### Dashboard Indicators
- **Approved**: Green indicator with approval date
- **Rejected**: Red indicator with rejection reason
- **Pending**: Orange indicator with QR code status

### 💰 Payment Entry WHT Enhancements

#### Automatic Tax Calculation
- **Real-time Calculation**: Updates as amounts or rates change
- **Visual Feedback**: Shows calculation formula in alerts
- **Default Rates**: Suggests common WHT rates (3% services, 1% rental, 5% royalty)

#### Certificate Generation
- **Validation**: Ensures required fields (Tax ID) are present
- **Auto-numbering**: Generates unique certificate numbers
- **Print Integration**: Direct printing with proper format

#### Custom Buttons Added
```javascript
// Buttons automatically added based on document state:
- "Generate WHT Certificate" (when submitted with WHT enabled)
- "Print WHT Certificate" (when certificate is generated)
```

## Technical Implementation

### File Structure
```
print_designer/public/js/delivery_approval.js    # Main client script
print_designer/public/css/delivery_approval.bundle.scss    # Enhanced styling
```

### Hook Integration
```javascript
// In hooks.py
doctype_js = {
    "Delivery Note": "print_designer/public/js/delivery_approval.js",
    "Payment Entry": "print_designer/public/js/delivery_approval.js",
}

app_include_css = [
    "delivery_approval.bundle.css",
]
```

### Key Functions

#### QR Code Management
```javascript
generate_qr_code(frm)              // Generate QR for delivery note
show_qr_code_dialog(frm)           // Display interactive QR dialog
print_delivery_note_with_qr(frm)   // Print with QR format
update_approval_status_indicator(frm) // Update dashboard status
```

#### WHT Certificate Management
```javascript
calculate_withholding_tax_amount(frm)  // Real-time tax calculation
generate_wht_certificate(frm)          // Generate and print certificate
generate_certificate_number(frm)       // Auto-generate cert numbers
update_wht_status_indicator(frm)       // Update dashboard status
```

### API Integration

#### QR Code APIs
```javascript
// Generate QR code
frappe.call({
    method: 'print_designer.custom.delivery_note_qr.generate_delivery_approval_qr',
    args: { delivery_note_name: frm.doc.name }
});
```

#### Error Handling
- **Progress Indicators**: Visual feedback during API calls
- **Error Messages**: User-friendly error handling
- **Validation**: Client-side validation before API calls
- **Global Error Handler**: Catches and handles system errors

### UI/UX Enhancements

#### QR Code Dialog Features
- **Responsive Design**: Mobile-friendly layout
- **Visual Polish**: Hover effects and animations
- **Information Hierarchy**: Clear sections for different content types
- **Action Buttons**: Primary/secondary action patterns

#### Form Enhancements
- **Field Styling**: Custom CSS for QR and WHT fields
- **Section Highlighting**: Visual separation of feature sections
- **Status Indicators**: Color-coded status with meaningful icons
- **Button Grouping**: Logical grouping of related actions

### Styling Features

#### CSS Enhancements
```scss
// QR Dialog Styling
.qr-dialog-content {
    .qr-header { /* Gradient header */ }
    .qr-code-container { /* Hover effects */ }
    .qr-instructions { /* Structured list */ }
}

// Form Section Styling  
.delivery-approval-section { /* Blue accent border */ }
.wht-section { /* Green accent border */ }
```

#### Responsive Design
- **Mobile Optimization**: Smaller QR codes and compact layouts
- **Print Styles**: Print-friendly QR code styling
- **Dark Mode**: Automatic dark mode support

## Usage Examples

### Delivery Note Workflow
```javascript
// 1. User submits Delivery Note
// 2. QR code auto-generates after 1.5 seconds
// 3. User can click "Show QR Code" to display dialog
// 4. Customer scans QR and approves via web interface
// 5. Status automatically updates in form
```

### Payment Entry Workflow
```javascript
// 1. User enables "Apply Thai Withholding Tax"
// 2. Tax amount calculates automatically
// 3. User enters supplier Tax ID
// 4. User clicks "Generate WHT Certificate"
// 5. Certificate prints in Thai format
```

## Global Utility Object

The script exposes a global utility object for external access:

```javascript
window.print_designer_delivery_utils = {
    // QR Functions
    generateQRForDelivery: generate_qr_code,
    showQRDialog: show_qr_code_dialog,
    printDeliveryWithQR: print_delivery_note_with_qr,
    
    // WHT Functions
    generateWHTCertificate: generate_wht_certificate,
    printWHTCertificate: print_wht_certificate,
    calculateWHTAmount: calculate_withholding_tax_amount,
    
    // Utilities
    getStatusColor: get_status_color,
    formatCurrency: format_currency
};
```

## Error Handling Strategy

### Client-Side Validation
- **Required Fields**: Validates before API calls
- **Data Format**: Ensures proper data types
- **User Feedback**: Immediate visual feedback

### API Error Handling
- **Network Errors**: Graceful handling of connection issues
- **Server Errors**: User-friendly error messages
- **Timeout Handling**: Progress indicators with timeout protection

### Global Error Monitoring
```javascript
window.addEventListener('error', function(e) {
    if (e.message && e.message.includes('delivery_approval')) {
        // Log and display user-friendly message
    }
});
```

## Performance Considerations

### Lazy Loading
- **QR Generation**: Only generates when needed
- **Dialog Creation**: Created on-demand
- **API Calls**: Debounced for calculation functions

### Memory Management
- **Dialog Cleanup**: Properly destroys dialog instances
- **Event Listeners**: Removes listeners when not needed
- **CSS Optimization**: Minimal CSS impact

## Browser Compatibility

### Supported Features
- **Modern Browsers**: Chrome 80+, Firefox 75+, Safari 13+
- **Mobile Browsers**: iOS Safari, Chrome Mobile
- **Progressive Enhancement**: Fallbacks for older browsers

### Required APIs
- **Clipboard API**: For URL copying functionality
- **CSS Grid/Flexbox**: For responsive layouts
- **ES6 Features**: Arrow functions, template literals

## Troubleshooting

### Common Issues
1. **QR Code Not Generating**: Check API endpoint availability
2. **Dialog Not Showing**: Verify CSS bundle loading
3. **Calculation Errors**: Check field permissions and values
4. **Print Issues**: Verify print format existence

### Debug Mode
```javascript
// Enable debug logging
localStorage.setItem('print_designer_debug', 'true');
```

### Performance Monitoring
```javascript
// Monitor API call performance
console.time('qr_generation');
// ... API call ...
console.timeEnd('qr_generation');
```

## Future Enhancements

### Planned Features
- **Batch QR Generation**: Multiple delivery notes
- **QR Code Customization**: Logo embedding, colors
- **Mobile App Integration**: Deep linking support
- **Advanced Analytics**: Usage tracking and reporting

### Extension Points
- **Custom Validators**: Add custom validation rules
- **Theme Support**: Custom color schemes
- **Webhook Integration**: Real-time notifications
- **Multi-language**: Additional language support