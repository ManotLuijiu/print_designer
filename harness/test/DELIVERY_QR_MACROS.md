# Delivery QR Code Macros for Print Designer

This document provides comprehensive documentation for using delivery QR code macros in Print Designer templates.

## Overview

The delivery QR code system provides Jinja macros and functions that can be used in print formats to display customer approval status, QR codes, and digital signatures for delivery notes.

## Available Macros

### 1. Main Delivery Approval QR Macro

#### Template File: `macros/delivery_qr.html`

```html
{% macro delivery_approval_qr(delivery_note) -%}
    {% if delivery_note.customer_approval_status == 'Pending' %}
        <div class="approval-section">
            <h3>Customer Approval Required</h3>
            <div class="qr-code-container">
                {% if delivery_note.approval_qr_code %}
                    <img src="data:image/png;base64,{{ delivery_note.approval_qr_code }}" 
                         alt="Scan to approve delivery" 
                         style="width: 150px; height: 150px;">
                {% endif %}
                <p>Scan QR code to approve goods received</p>
            </div>
        </div>
    {% elif delivery_note.customer_approval_status == 'Approved' %}
        <div class="approval-section approved">
            <h3>✓ Approved by Customer</h3>
            <p>Approved by: {{ delivery_note.customer_approved_by }}</p>
            <p>Date: {{ delivery_note.customer_approved_on }}</p>
            {% if delivery_note.customer_signature %}
                <div class="signature">
                    <p>Digital Signature:</p>
                    <img src="{{ delivery_note.customer_signature }}" 
                         alt="Customer Signature" 
                         style="max-width: 200px; height: auto;">
                </div>
            {% endif %}
        </div>
    {% endif %}
{%- endmacro %}
```

## Available Jinja Functions

### 1. `render_delivery_approval_qr(delivery_note_name)`

**Purpose**: Renders the complete delivery approval section with QR code for pending deliveries and approval status for completed ones.

**Usage in Templates**:
```html
<!-- In Print Format HTML -->
{{ render_delivery_approval_qr(doc.name) }}
```

**Output**:
- **Pending Status**: Shows QR code with instructions
- **Approved Status**: Shows approval details with signature
- **Rejected Status**: No output (use other macros for rejection display)

### 2. `render_delivery_qr_compact(delivery_note_name)`

**Purpose**: Renders a compact version of the delivery approval status.

**Usage in Templates**:
```html
{{ render_delivery_qr_compact(doc.name) }}
```

**Features**:
- Smaller QR code (100x100px) for space-constrained layouts
- Colored status boxes (green for approved, red for rejected, yellow for pending)
- Minimal text and information

### 3. `render_delivery_status_badge(delivery_note_name)`

**Purpose**: Renders a small status badge showing current approval status.

**Usage in Templates**:
```html
Status: {{ render_delivery_status_badge(doc.name) }}
```

**Output**:
- ✓ APPROVED (green badge)
- ✗ REJECTED (red badge)
- ⏳ PENDING (yellow badge)

### 4. `render_delivery_approval_summary(delivery_note_name)`

**Purpose**: Renders a comprehensive summary box with all approval information.

**Usage in Templates**:
```html
{{ render_delivery_approval_summary(doc.name) }}
```

**Features**:
- Complete approval status with colored background
- QR code for pending approvals
- Digital signature display for approved deliveries
- Rejection reason for rejected deliveries
- Professional styling with borders and backgrounds

### 5. `render_delivery_qr_with_instructions(delivery_note_name)`

**Purpose**: Renders QR code with detailed customer instructions (only for pending deliveries).

**Usage in Templates**:
```html
{{ render_delivery_qr_with_instructions(doc.name) }}
```

**Features**:
- Large QR code (150x150px) with blue border
- Step-by-step instructions for customers
- Professional blue-themed design
- Only displays for pending approvals

### 6. `render_legacy_delivery_qr(delivery_note_name)`

**Purpose**: Backward compatibility function for existing templates using legacy field names.

**Usage in Templates**:
```html
{{ render_legacy_delivery_qr(doc.name) }}
```

**Note**: Uses `custom_goods_received_status` and `custom_approval_qr_code` fields.

## Field Mapping

The system uses standardized field names with legacy compatibility:

| **New Field Name** | **Legacy Field Name** | **Description** |
|-------------------|----------------------|-----------------|
| `customer_approval_status` | `custom_goods_received_status` | Approval status (Pending/Approved/Rejected) |
| `approval_qr_code` | `custom_approval_qr_code` | Base64 QR code image |
| `customer_signature` | `custom_customer_signature` | Digital signature data |
| `customer_approved_by` | `custom_approved_by` | Customer name |
| `customer_approved_on` | `custom_customer_approval_date` | Approval timestamp |
| - | `custom_approval_url` | Approval page URL |
| - | `custom_rejection_reason` | Rejection reason text |

## Usage Examples

### Example 1: Simple QR Code in Header
```html
<div class="delivery-header">
    <h2>Delivery Note: {{ doc.name }}</h2>
    {{ render_delivery_qr_compact(doc.name) }}
</div>
```

### Example 2: Full Approval Section in Footer
```html
<div class="delivery-footer">
    {{ render_delivery_approval_summary(doc.name) }}
</div>
```

### Example 3: QR Code with Instructions (Customer Copy)
```html
<div class="customer-instructions">
    <h3>Customer Approval Required</h3>
    {{ render_delivery_qr_with_instructions(doc.name) }}
</div>
```

### Example 4: Status Badge in List View
```html
<div class="status-line">
    Delivery Status: {{ render_delivery_status_badge(doc.name) }}
    <span class="date">{{ doc.posting_date }}</span>
</div>
```

### Example 5: Using Direct Macro (if macro file imported)
```html
{% from "macros/delivery_qr.html" import delivery_approval_qr %}
{{ delivery_approval_qr(doc) }}
```

## Styling and Customization

### CSS Classes Used

The macros generate HTML with specific CSS classes for customization:

```css
/* Main approval section */
.approval-section { 
    border: 1px solid #ddd; 
    padding: 15px; 
    margin: 10px 0; 
}

/* Approved status styling */
.approval-section.approved { 
    background-color: #d4edda; 
    border-color: #c3e6cb; 
}

/* QR code container */
.qr-code-container { 
    text-align: center; 
    margin: 10px 0; 
}

/* Digital signature display */
.signature { 
    margin-top: 10px; 
    padding: 10px; 
    border: 1px solid #ddd; 
}

/* Delivery approval summary */
.delivery-approval-summary {
    border: 1px solid #ddd;
    padding: 15px;
    margin: 10px 0;
    border-radius: 5px;
    background-color: #f9f9f9;
}
```

### Custom Styling

You can override the default styles by adding CSS to your print format:

```html
<style>
.approval-section {
    border: 2px solid #007bff;
    border-radius: 10px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.qr-code-container img {
    border: 3px solid #007bff;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
```

## Error Handling

All macro functions include comprehensive error handling:

- **Invalid Delivery Note**: Returns empty string
- **Missing Fields**: Falls back to legacy field names
- **Database Errors**: Logs error and returns safe fallback content
- **Template Errors**: Displays error message in debug mode

## Performance Considerations

- **Caching**: QR codes are cached in the database to avoid regeneration
- **Conditional Loading**: Macros only load necessary data based on status
- **Optimized Queries**: Single document fetch per macro call
- **Lazy Generation**: QR codes generated only when needed

## Troubleshooting

### Common Issues

1. **QR Code Not Displaying**
   - Check if `approval_qr_code` field has data
   - Verify QR code generation is working: `generate_delivery_approval_qr(doc.name)`
   - Check browser console for base64 image errors

2. **Status Not Updating**
   - Verify field synchronization is working
   - Check both new and legacy field values
   - Ensure hooks are properly configured

3. **Macro Not Found**
   - Verify hooks.py includes the macro functions
   - Check if custom fields are installed
   - Clear cache and restart bench

4. **Styling Issues**
   - Check CSS conflicts with existing styles
   - Verify print format has proper HTML structure
   - Test in different browsers

### Debug Commands

```bash
# Test field installation
bench execute print_designer.test_delivery_fields.test_delivery_fields

# Test QR generation
bench execute "
delivery_note = frappe.get_doc('Delivery Note', 'DN-001')
from print_designer.utils.delivery_qr_macros import render_delivery_approval_qr
print(render_delivery_approval_qr('DN-001'))
"

# Check field synchronization
bench execute "
delivery_note = frappe.get_doc('Delivery Note', 'DN-001')
print(f'New status: {delivery_note.get(\"customer_approval_status\")}')
print(f'Legacy status: {delivery_note.get(\"custom_goods_received_status\")}')
"
```

## Integration with Print Designer

### Adding to Existing Print Formats

1. **Open Print Designer** for your Delivery Note format
2. **Add HTML Element** where you want the QR code
3. **Insert Macro Call** in the HTML content:
   ```html
   {{ render_delivery_approval_qr(doc.name) }}
   ```
4. **Preview and Save** the format

### Creating New Print Formats

1. **Create New Print Format** for Delivery Note
2. **Design Layout** with sections for QR code
3. **Add Macro Calls** in appropriate sections
4. **Test with Sample Data** to verify rendering
5. **Apply Styles** for professional appearance

## Security Considerations

- **Token Validation**: QR codes use secure tokens for approval
- **Guest Access**: Approval pages have proper guest access controls
- **Data Sanitization**: All user inputs are properly sanitized
- **Audit Trail**: All approvals are logged with timestamps

---

## Quick Reference

### Most Common Usage Patterns

```html
<!-- Simple QR for pending, status for approved -->
{{ render_delivery_qr_compact(doc.name) }}

<!-- Complete approval summary with all details -->
{{ render_delivery_approval_summary(doc.name) }}

<!-- Just the status badge -->
{{ render_delivery_status_badge(doc.name) }}

<!-- QR with customer instructions (pending only) -->
{{ render_delivery_qr_with_instructions(doc.name) }}
```

### Field Access

```html
<!-- Direct field access (use with caution) -->
Status: {{ doc.customer_approval_status or doc.custom_goods_received_status }}
QR Code: {% if doc.approval_qr_code or doc.custom_approval_qr_code %}Present{% endif %}
```

This documentation provides everything needed to implement delivery QR codes in your Print Designer templates! 🎉