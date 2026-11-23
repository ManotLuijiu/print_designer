# Watermark Settings DocType Architecture

## Overview
Replace fragile custom fields with dedicated DocTypes for watermark configuration management.

## Core DocTypes Design

### 1. Watermark Settings (Master DocType)
```json
{
    "doctype": "Watermark Settings",
    "naming_series": "WMRK-SETTINGS-.#####",
    "is_single": 1,
    "fields": [
        {
            "fieldname": "enabled",
            "fieldtype": "Check",
            "label": "Enable Watermark System",
            "default": 1,
            "description": "Global toggle for watermark functionality"
        },
        {
            "fieldname": "default_mode",
            "fieldtype": "Select", 
            "label": "Default Watermark Mode",
            "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            "default": "None"
        },
        {
            "fieldname": "global_settings_section",
            "fieldtype": "Section Break",
            "label": "Global Settings"
        },
        {
            "fieldname": "default_font_size",
            "fieldtype": "Int",
            "label": "Default Font Size (px)",
            "default": 24
        },
        {
            "fieldname": "default_position",
            "fieldtype": "Select",
            "label": "Default Position",
            "options": "Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right",
            "default": "Top Right"
        },
        {
            "fieldname": "default_font_family",
            "fieldtype": "Select",
            "label": "Default Font Family",
            "options": "Arial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri\nSarabun",
            "default": "Sarabun"
        },
        {
            "fieldname": "templates_section",
            "fieldtype": "Section Break", 
            "label": "Watermark Templates"
        },
        {
            "fieldname": "watermark_templates",
            "fieldtype": "Table",
            "label": "Watermark Templates",
            "options": "Watermark Template"
        }
    ]
}
```

### 2. Watermark Template (Child DocType)
```json
{
    "doctype": "Watermark Template",
    "istable": 1,
    "fields": [
        {
            "fieldname": "template_name",
            "fieldtype": "Data",
            "label": "Template Name",
            "reqd": 1
        },
        {
            "fieldname": "watermark_mode",
            "fieldtype": "Select",
            "label": "Watermark Mode",
            "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            "reqd": 1
        },
        {
            "fieldname": "font_size",
            "fieldtype": "Int",
            "label": "Font Size (px)",
            "default": 24
        },
        {
            "fieldname": "position",
            "fieldtype": "Select",
            "label": "Position",
            "options": "Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right",
            "default": "Top Right"
        },
        {
            "fieldname": "font_family",
            "fieldtype": "Select", 
            "label": "Font Family",
            "options": "Arial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri\nSarabun",
            "default": "Sarabun"
        },
        {
            "fieldname": "custom_text",
            "fieldtype": "Data",
            "label": "Custom Text",
            "description": "Override default text (Original/Copy) with custom text"
        },
        {
            "fieldname": "color",
            "fieldtype": "Color",
            "label": "Text Color",
            "default": "#999999"
        },
        {
            "fieldname": "opacity",
            "fieldtype": "Float",
            "label": "Opacity",
            "default": 0.6,
            "precision": 2
        }
    ]
}
```

### 3. Print Format Watermark Config (Child DocType)
```json
{
    "doctype": "Print Format Watermark Config",
    "istable": 1,
    "fields": [
        {
            "fieldname": "print_format",
            "fieldtype": "Link",
            "label": "Print Format",
            "options": "Print Format",
            "reqd": 1
        },
        {
            "fieldname": "watermark_template",
            "fieldtype": "Link",
            "label": "Watermark Template", 
            "options": "Watermark Template"
        },
        {
            "fieldname": "override_settings",
            "fieldtype": "Check",
            "label": "Override Template Settings"
        },
        {
            "fieldname": "watermark_mode",
            "fieldtype": "Select",
            "label": "Watermark Mode",
            "options": "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            "depends_on": "override_settings"
        }
    ]
}
```

## Benefits of DocType Approach

### 1. **Stability & Reliability**
- Proper database schema management
- Version controlled through fixtures
- Automated migration handling
- No field type conflicts

### 2. **Advanced Features**
- Custom validation logic
- Business rules and workflows
- Proper permissions model
- Audit trail and versioning

### 3. **Extensibility**
- Easy to add new features
- Template-based configuration
- Per-format overrides
- Integration with other DocTypes

### 4. **User Experience**
- Dedicated configuration interface
- Bulk configuration management
- Import/export capabilities
- Search and filter options

## Implementation Strategy

### Phase 1: Create DocTypes
1. Create Watermark Settings (Single)
2. Create Watermark Template (Child)
3. Create Print Format Watermark Config (Child)

### Phase 2: Migration Utilities
1. Export existing custom field data
2. Import into new DocType structure
3. Update client scripts to use DocTypes
4. Remove custom field dependencies

### Phase 3: Enhanced Client Integration
1. Update print.js to fetch from DocTypes
2. Add template selection in sidebar
3. Implement real-time preview
4. Add configuration caching

## API Integration Points

### JavaScript Client Updates
```javascript
// Instead of reading from print_settings custom fields
frappe.call({
    method: 'frappe.client.get_single',
    args: {doctype: 'Watermark Settings'},
    callback: (r) => {
        this.watermark_config = r.message;
        this.setup_watermark_selector();
    }
});

// Template-based selection
this.watermark_template_selector = this.add_sidebar_item({
    fieldtype: "Link",
    fieldname: "watermark_template", 
    options: "Watermark Template",
    label: __("Watermark Template"),
    change: () => this.apply_watermark_template()
});
```

### Backend Integration
```python
@frappe.whitelist()
def get_watermark_config_for_print_format(print_format):
    """Get watermark configuration for specific print format"""
    settings = frappe.get_single('Watermark Settings')
    
    # Check for format-specific overrides
    format_config = frappe.db.get_value(
        'Print Format Watermark Config',
        {'print_format': print_format},
        ['watermark_template', 'watermark_mode']
    )
    
    if format_config:
        return get_template_config(format_config.watermark_template)
    
    return settings.as_dict()
```

## Migration Path

### 1. Backward Compatibility
- Keep custom fields during transition period
- Dual-read from both sources
- Gradual migration of existing data

### 2. Data Migration Script
```python
def migrate_custom_fields_to_doctype():
    """Migrate existing watermark custom field data to DocTypes"""
    
    # Get existing Print Settings data
    print_settings = frappe.get_single('Print Settings')
    
    # Create Watermark Settings
    watermark_settings = frappe.new_doc('Watermark Settings')
    watermark_settings.default_mode = print_settings.get('watermark_settings', 'None')
    watermark_settings.default_font_size = print_settings.get('watermark_font_size', 24)
    watermark_settings.default_position = print_settings.get('watermark_position', 'Top Right')
    watermark_settings.save()
    
    # Migrate Print Format specific settings
    migrate_print_format_settings()
```

This DocType-based approach would provide a much more stable and extensible foundation for watermark functionality.