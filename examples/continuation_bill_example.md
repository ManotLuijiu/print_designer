# Continuation Bill Implementation Guide

This guide shows how to implement the continuation bill feature similar to the sample invoice image provided, which offers two modes for handling long tables across multiple pages.

## Overview

The continuation bill feature offers two distinct modes:

### Before Mode (Separate Tables)
- Creates separate complete tables per page (like the "Before" in the sample image)
- Each page has its own table with page totals
- Optional overall summary page with grand totals
- Mimics multiple separate invoices

### After Mode (Continuation Table) 
- Single continuous table with balance forward (like the "After" in the sample image)
- Shows "Continued from previous page" headers
- Running totals with balance forward rows
- Professional continuation formatting

## Key Features

- **Mode Selection**: Choose between "Before" (separate tables) or "After" (continuation table)
- Split long tables across multiple pages
- Show running totals and balance forward (After mode)
- Page-specific totals (Before mode)
- Add continuation headers and footers
- Configure which columns to total
- Maintain professional invoice formatting

## Implementation Steps

### 1. Enable Continuation in Print Format

In your Print Format design, add the continuation configuration to any table element:

```javascript
// In your table element configuration
element.continuationConfig = {
    enabled: true,
    mode: "after",                      // "before" (separate tables) or "after" (continuation table)
    rowsPerPage: 10,                    // Number of rows per page
    showRunningTotals: true,            // Show totals on each page
    showBalanceForward: true,           // Show balance forward on subsequent pages (After mode)
    continuationHeader: "Continued from previous page",
    continuationFooter: "Continued on next page",
    totalColumns: ["amount", "tax_amount", "total"],  // Columns to calculate totals for
    pageNumbering: true,
    showPageTotals: true
};
```

### 2. Configure Total Columns

Specify which columns should be totaled across pages:

```javascript
// Example for Sales Invoice
totalColumns: [
    "qty",           // Quantity
    "amount",        // Line total
    "tax_amount",    // Tax amount
    "total"          // Grand total
]
```

### 3. Usage in Jinja Template

The enhanced table macro automatically detects continuation configuration:

```html
{% macro invoice_table(element, send_to_jinja, heightType) %}
    <!-- The table macro will automatically handle continuation -->
    {{ table(element, send_to_jinja, heightType) }}
{% endmacro %}
```

### 4. API Integration

Use the API endpoints to preview and configure continuation:

```javascript
// Get preview of how data will be split
frappe.call({
    method: "print_designer.api.continuation_table.get_continuation_table_preview",
    args: {
        doctype: "Sales Invoice",
        docname: "SINV-2024-00001",
        fieldname: "items",
        rows_per_page: 10
    },
    callback: function(r) {
        console.log("Total pages:", r.message.total_pages);
        console.log("Pages:", r.message.pages);
    }
});

// Calculate totals for specified columns
frappe.call({
    method: "print_designer.api.continuation_table.calculate_continuation_totals",
    args: {
        doctype: "Sales Invoice",
        docname: "SINV-2024-00001",
        fieldname: "items",
        total_columns: ["qty", "amount", "tax_amount"]
    },
    callback: function(r) {
        console.log("Totals:", r.message.totals);
    }
});
```

## Frontend Configuration Component

Use the `ContinuationTableConfig.vue` component in the properties panel:

```vue
<template>
    <div class="table-properties">
        <!-- Other table properties -->
        
        <ContinuationTableConfig
            :element="selectedElement"
            @update-config="handleContinuationUpdate"
        />
    </div>
</template>

<script setup>
import ContinuationTableConfig from './ContinuationTableConfig.vue';

const handleContinuationUpdate = (config) => {
    selectedElement.value.continuationConfig = config;
    // Trigger re-render or update
};
</script>
```

## Example Output Structure

The continuation bill will generate HTML like this:

```html
<!-- Page 1 -->
<div class="continuation-table-page">
    <table class="continuation-table">
        <thead>
            <tr><th>Item</th><th>Qty</th><th>Rate</th><th>Amount</th></tr>
        </thead>
        <tbody>
            <!-- First 10 rows -->
        </tbody>
        <tfoot>
            <tr class="totals-row">
                <td>Subtotal (Page 1)</td>
                <td>50</td>
                <td></td>
                <td>5,000.00</td>
            </tr>
        </tfoot>
    </table>
    <div class="continuation-footer">Continued on next page</div>
</div>

<!-- Page break -->
<div style="page-break-before: always;"></div>

<!-- Page 2 -->
<div class="continuation-table-page">
    <div class="continuation-header">Continued from previous page</div>
    <table class="continuation-table">
        <thead>
            <tr><th>Item</th><th>Qty</th><th>Rate</th><th>Amount</th></tr>
        </thead>
        <tbody class="balance-forward">
            <tr class="balance-forward-row">
                <td>Balance Forward</td>
                <td>50</td>
                <td></td>
                <td>5,000.00</td>
            </tr>
        </tbody>
        <tbody>
            <!-- Remaining rows -->
        </tbody>
        <tfoot>
            <tr class="totals-row">
                <td>Grand Total</td>
                <td>100</td>
                <td></td>
                <td>10,000.00</td>
            </tr>
        </tfoot>
    </table>
</div>
```

## CSS Styling

The continuation tables use predefined CSS classes:

```scss
.continuation-table-page {
    page-break-inside: avoid;
    margin-bottom: 20px;
}

.continuation-header,
.continuation-footer {
    text-align: center;
    font-weight: bold;
    background-color: #f8f9fa;
    padding: 8px;
    border: 1px solid #dee2e6;
}

.balance-forward-row {
    background-color: #fff3cd !important;
    font-weight: bold;
    color: #856404;
}

.totals-row {
    background-color: #d1ecf1 !important;
    font-weight: bold;
    color: #0c5460;
    border-top: 3px solid #0c5460;
}
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | false | Enable continuation functionality |
| `rowsPerPage` | number | 10 | Number of rows per page |
| `showRunningTotals` | boolean | true | Show totals on each page |
| `showBalanceForward` | boolean | true | Show balance forward row |
| `continuationHeader` | string | "Continued from previous page" | Header text for continuation pages |
| `continuationFooter` | string | "Continued on next page" | Footer text for pages with continuation |
| `totalColumns` | array | [] | List of column fieldnames to total |
| `pageNumbering` | boolean | true | Enable page numbering |
| `showPageTotals` | boolean | true | Show subtotals on each page |

## Testing

Test your continuation table configuration:

```javascript
frappe.call({
    method: "print_designer.api.continuation_table.test_continuation_table",
    args: {
        doctype: "Sales Invoice",
        docname: "SINV-2024-00001",
        fieldname: "items",
        config_json: JSON.stringify({
            enabled: true,
            rowsPerPage: 10,
            showRunningTotals: true,
            totalColumns: ["qty", "amount"]
        })
    },
    callback: function(r) {
        if (r.message.success) {
            console.log("Configuration is valid");
            console.log("Preview:", r.message.preview);
            console.log("Totals:", r.message.totals);
        } else {
            console.error("Configuration error:", r.message.error);
        }
    }
});
```

## Integration with Print Designer UI

To integrate with the Print Designer interface:

1. Add the continuation config component to the table properties panel
2. Save the configuration in the element's `continuationConfig` property
3. The Jinja template will automatically detect and render continuation tables
4. Test with preview functionality to ensure proper formatting

## Troubleshooting

### Common Issues

1. **Tables not breaking properly**: Ensure `page-break-inside: avoid` is set on table containers
2. **Totals not calculating**: Verify column fieldnames match exactly with table data
3. **Headers not repeating**: Check that continuation headers are enabled and configured
4. **Styling issues**: Ensure the continuation_table.bundle.css is loaded

### Debug Mode

Enable debug mode to see detailed continuation information:

```javascript
element.continuationConfig.debug = true;
```

This will log additional information about page splits and calculations to the browser console.

## Best Practices

1. **Keep row counts reasonable**: 5-15 rows per page works best for most formats
2. **Test with real data**: Always test with actual documents that have many rows
3. **Consider paper size**: Adjust rows per page based on your target paper size
4. **Use meaningful headers**: Clear continuation messages help readers follow the document
5. **Total relevant columns only**: Only total numeric columns that make business sense
6. **Test printing**: Always test the actual PDF output, not just screen preview

## Migration from Standard Tables

To convert existing tables to continuation tables:

1. Add `continuationConfig` to your table element
2. Identify numeric columns for totaling
3. Set appropriate rows per page based on your format
4. Test with documents that have many line items
5. Adjust styling as needed for your brand requirements

This implementation provides a professional continuation bill format that matches the sample invoice image while being fully configurable and integrated with the Print Designer system.