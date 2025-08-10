# Watermark Settings Migration Strategy

## Phase-Based Migration Plan

### Phase 1: Create DocType Foundation (Immediate)
**Goal**: Establish DocType infrastructure while maintaining custom field compatibility

#### 1.1 Create Core DocTypes
```bash
# Create DocType JSON files
mkdir -p print_designer/print_designer/doctype/watermark_settings
mkdir -p print_designer/print_designer/doctype/watermark_template
```

#### 1.2 Watermark Settings DocType (Single)
```json
{
    "doctype": "Watermark Settings",
    "is_single": 1,
    "module": "Print Designer",
    "fields": [
        {
            "fieldname": "enabled",
            "fieldtype": "Check", 
            "label": "Enable Watermark System",
            "default": 1
        },
        {
            "fieldname": "migration_status",
            "fieldtype": "Select",
            "label": "Migration Status",
            "options": "Custom Fields\nHybrid\nDocType Only",
            "default": "Custom Fields",
            "read_only": 1
        },
        {
            "fieldname": "templates_section", 
            "fieldtype": "Section Break",
            "label": "Watermark Templates"
        },
        {
            "fieldname": "templates",
            "fieldtype": "Table",
            "label": "Templates",
            "options": "Watermark Template"
        }
    ]
}
```

#### 1.3 Backward Compatibility Layer
```python
# print_designer/utils/watermark_compat.py

class WatermarkSettings:
    """Compatibility layer for watermark settings"""
    
    @staticmethod
    def get_watermark_config():
        """Get watermark config from either DocType or custom fields"""
        
        # Try DocType first (future)
        try:
            doctype_settings = frappe.get_single('Watermark Settings')
            if doctype_settings.migration_status == 'DocType Only':
                return WatermarkSettings._get_from_doctype()
        except:
            pass
            
        # Fallback to custom fields (current)
        return WatermarkSettings._get_from_custom_fields()
    
    @staticmethod
    def _get_from_custom_fields():
        """Get from Print Settings custom fields (current method)"""
        print_settings = frappe.get_single('Print Settings')
        return {
            'mode': print_settings.get('watermark_settings', 'None'),
            'font_size': print_settings.get('watermark_font_size', 24),
            'position': print_settings.get('watermark_position', 'Top Right'),
            'font_family': print_settings.get('watermark_font_family', 'Sarabun'),
            'source': 'custom_fields'
        }
    
    @staticmethod 
    def _get_from_doctype():
        """Get from Watermark Settings DocType (future method)"""
        settings = frappe.get_single('Watermark Settings')
        return {
            'mode': settings.default_mode,
            'font_size': settings.default_font_size,
            'position': settings.default_position, 
            'font_family': settings.default_font_family,
            'source': 'doctype'
        }
```

### Phase 2: Update Client Integration (Week 2)
**Goal**: Modify client scripts to use compatibility layer

#### 2.1 Update print.js
```javascript
// Replace direct custom field access
// OLD:
// this.print_settings.watermark_settings

// NEW: 
this.get_watermark_config = () => {
    return frappe.call({
        method: 'print_designer.utils.watermark_compat.get_watermark_config',
        callback: (r) => {
            this.watermark_config = r.message;
            this.setup_watermark_selector();
        }
    });
};

this.setup_watermark_selector = () => {
    this.watermark_selector = this.add_sidebar_item({
        fieldtype: "Select",
        fieldname: "watermark_settings",
        label: __("Watermark per Page"),
        options: [
            "None",
            "Original on First Page", 
            "Copy on All Pages",
            "Original,Copy on Sequence"
        ].join('\n'),
        default: this.watermark_config.mode,
        change: () => this.preview(),
    }).$input;
};
```

#### 2.2 Add Template Selection (Future Enhancement)
```javascript
// Add template selector (when DocType is primary)
if (this.watermark_config.source === 'doctype') {
    this.watermark_template_selector = this.add_sidebar_item({
        fieldtype: "Link",
        fieldname: "watermark_template",
        options: "Watermark Template", 
        label: __("Watermark Template"),
        change: () => this.apply_template()
    });
}
```

### Phase 3: Server-Side Migration (Week 3)
**Goal**: Update all server-side code to use compatibility layer

#### 3.1 Update Key Files
```python
# Replace in signature_stamp.py, printview_watermark.py, etc.

# OLD:
print_settings = frappe.get_single('Print Settings')
watermark_settings = print_settings.get('watermark_settings', 'None')

# NEW:
from print_designer.utils.watermark_compat import WatermarkSettings
config = WatermarkSettings.get_watermark_config()
watermark_settings = config['mode']
```

#### 3.2 Data Migration Utility
```python
@frappe.whitelist()
def migrate_to_doctype():
    """Migrate custom field data to DocType"""
    
    print_settings = frappe.get_single('Print Settings')
    
    # Create/update Watermark Settings
    watermark_settings = frappe.get_single('Watermark Settings')  
    watermark_settings.enabled = 1
    watermark_settings.default_mode = print_settings.get('watermark_settings', 'None')
    watermark_settings.default_font_size = print_settings.get('watermark_font_size', 24)
    watermark_settings.default_position = print_settings.get('watermark_position', 'Top Right')
    watermark_settings.default_font_family = print_settings.get('watermark_font_family', 'Sarabun')
    watermark_settings.migration_status = 'Hybrid'
    watermark_settings.save()
    
    # Create default templates
    create_default_templates()
    
    frappe.msgprint("Migration completed successfully!")

def create_default_templates():
    """Create standard watermark templates"""
    templates = [
        {
            'template_name': 'Standard Original/Copy', 
            'watermark_mode': 'Original,Copy on Sequence',
            'font_size': 24,
            'position': 'Top Right'
        },
        {
            'template_name': 'Copy Only',
            'watermark_mode': 'Copy on All Pages', 
            'font_size': 18,
            'position': 'Top Right'
        }
    ]
    
    settings = frappe.get_single('Watermark Settings')
    settings.templates = []
    
    for template in templates:
        settings.append('templates', template)
    
    settings.save()
```

### Phase 4: Enhanced Features (Week 4)
**Goal**: Add DocType-only features while maintaining compatibility

#### 4.1 Advanced Template System
- Multiple watermark templates per company
- Per-format template overrides
- Custom positioning and styling
- Template import/export

#### 4.2 Enhanced UI
- Dedicated Watermark Settings page
- Template management interface
- Real-time preview in Print Designer
- Bulk configuration tools

### Phase 5: Deprecation (Month 2)
**Goal**: Phase out custom fields gradually

#### 5.1 Deprecation Warnings
```python
def show_deprecation_warning():
    """Show warning about custom field deprecation"""
    config = WatermarkSettings.get_watermark_config()
    
    if config['source'] == 'custom_fields':
        frappe.msgprint(
            _("Watermark custom fields are deprecated. Please migrate to the new Watermark Settings DocType."),
            alert=True,
            indicator='orange'
        )
```

#### 5.2 Migration Assistant 
- One-click migration tool
- Data validation
- Rollback capability
- Migration status dashboard

## Benefits of This Approach

### 1. **Zero Downtime Migration**
- Existing installations continue working
- No breaking changes to current functionality
- Gradual adoption of new features

### 2. **Backward Compatibility**
- Custom field installations still function
- Existing configurations preserved
- API compatibility maintained

### 3. **Enhanced Stability**
- DocType-based configuration is version-controlled
- Proper database schema management
- No custom field conflicts

### 4. **Future Extensibility**
- Template-based system
- Advanced configuration options
- Integration with other DocTypes

## Implementation Timeline

| Week | Phase | Tasks | Risk Level |
|------|-------|-------|-----------|
| 1 | Foundation | Create DocTypes, Compatibility layer | Low |
| 2 | Client Updates | Modify print.js, Add template support | Medium |
| 3 | Server Migration | Update all server files | Medium |
| 4 | New Features | Templates, Enhanced UI | Low |
| 8 | Deprecation | Warnings, Migration tools | Low |

## Risk Mitigation

### 1. **Testing Strategy**
- Parallel testing with both systems
- Extensive regression testing
- User acceptance testing

### 2. **Rollback Plan**
- Keep custom field definitions
- Feature flags for new functionality
- Quick rollback procedures

### 3. **Documentation**
- Migration guides
- API documentation updates
- User training materials

This hybrid approach ensures stability while enabling future enhancements.