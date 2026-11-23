# Watermark Settings DocType Installation Guide

## File Locations and Structure

```
print_designer/
├── print_designer/
│   ├── doctype/
│   │   ├── watermark_settings/
│   │   │   ├── __init__.py
│   │   │   ├── watermark_settings.json
│   │   │   └── watermark_settings.py
│   │   ├── watermark_template/
│   │   │   ├── __init__.py
│   │   │   ├── watermark_template.json
│   │   │   └── watermark_template.py
│   │   └── print_format_watermark_config/
│   │       ├── __init__.py
│   │       ├── print_format_watermark_config.json
│   │       └── print_format_watermark_config.py
│   ├── api/
│   │   └── watermark.py
│   ├── patches/
│   │   └── migrate_watermark_settings.py
│   └── hooks.py
├── public/
│   ├── js/
│   │   └── print_watermark.js
│   └── css/
│       └── watermark.css
└── fixtures.py
```

## Step 1: Create DocType Directories

Create the directory structure for the new DocTypes:

```bash
# From your print_designer app root directory
mkdir -p print_designer/doctype/watermark_settings
mkdir -p print_designer/doctype/watermark_template  
mkdir -p print_designer/doctype/print_format_watermark_config
mkdir -p print_designer/api
mkdir -p print_designer/patches
mkdir -p public/js
mkdir -p public/css
```

## Step 2: Create DocType Files

### Watermark Settings DocType

**File: `print_designer/doctype/watermark_settings/__init__.py`**
```python
# Empty file
```

**File: `print_designer/doctype/watermark_settings/watermark_settings.py`**
```python
import frappe
from frappe.model.document import Document

class WatermarkSettings(Document):
    def validate(self):
        """Validate watermark settings"""
        if self.default_font_size and (self.default_font_size < 8 or self.default_font_size > 72):
            frappe.throw("Font size must be between 8 and 72 pixels")
        
        if self.default_opacity and (self.default_opacity < 0 or self.default_opacity > 1):
            frappe.throw("Opacity must be between 0 and 1")
    
    def on_update(self):
        """Clear cache when settings are updated"""
        frappe.cache().delete_key("watermark_settings")
```

**File: `print_designer/doctype/watermark_settings/watermark_settings.json`**
Use the JSON content from the first artifact above.

### Watermark Template DocType

**File: `print_designer/doctype/watermark_template/__init__.py`**
```python
# Empty file
```

**File: `print_designer/doctype/watermark_template/watermark_template.py`**
```python
import frappe
from frappe.model.document import Document

class WatermarkTemplate(Document):
    def validate(self):
        """Validate template settings"""
        if self.font_size and (self.font_size < 8 or self.font_size > 72):
            frappe.throw("Font size must be between 8 and 72 pixels")
        
        if self.opacity and (self.opacity < 0 or self.opacity > 1):
            frappe.throw("Opacity must be between 0 and 1")
```

**File: `print_designer/doctype/watermark_template/watermark_template.json`**
Use the JSON content from the second artifact above.

### Print Format Watermark Config DocType

**File: `print_designer/doctype/print_format_watermark_config/__init__.py`**
```python
# Empty file
```

**File: `print_designer/doctype/print_format_watermark_config/print_format_watermark_config.py`**
```python
import frappe
from frappe.model.document import Document

class PrintFormatWatermarkConfig(Document):
    def validate(self):
        """Validate configuration"""
        if self.override_settings:
            if self.font_size and (self.font_size < 8 or self.font_size > 72):
                frappe.throw("Font size must be between 8 and 72 pixels")
            
            if self.opacity and (self.opacity < 0 or self.opacity > 1):
                frappe.throw("Opacity must be between 0 and 1")
```

**File: `print_designer/doctype/print_format_watermark_config/print_format_watermark_config.json`**
Use the JSON content from the third artifact above.

## Step 3: Create API and Frontend Files

**File: `print_designer/api/__init__.py`**
```python
# Empty file
```

**File: `print_designer/api/watermark.py`**
Use the Python code from the watermark API methods artifact.

**File: `print_designer/public/js/print_watermark.js`**
Use the JavaScript code from the client script artifact.

**File: `print_designer/public/css/watermark.css`**
Use the CSS code from the watermark CSS artifact.

## Step 4: Update Hooks

**File: `print_designer/hooks.py`**
Add the entries from the hooks configuration artifact to your existing hooks.py file.

## Step 5: Create Migration Script

**File: `print_designer/patches/migrate_watermark_settings.py`**
Use the migration script from the migration artifact.

## Step 6: Update Fixtures

**File: `print_designer/fixtures.py`**
Use the fixtures configuration from the fixtures artifact.

## Step 7: Installation Commands

Run these commands in your Frappe environment:

```bash
# Navigate to your site directory
cd /path/to/your/frappe-bench

# Install/update the app
bench --site your-site-name install-app print_designer

# Or if already installed, migrate
bench --site your-site-name migrate

# Clear cache
bench --site your-site-name clear-cache

# Restart if needed
bench restart
```

## Step 8: Run Migration

After installation, run the migration to convert existing custom fields:

```bash
# Execute the migration script
bench --site your-site-name execute print_designer.patches.migrate_watermark_settings.execute
```

## Step 9: Verification

1. **Check DocTypes Created:**
   - Go to "DocType List" in your Frappe desk
   - Verify "Watermark Settings", "Watermark Template", and "Print Format Watermark Config" exist

2. **Access Watermark Settings:**
   - Search for "Watermark Settings" in the awesome bar
   - Open the single document and configure default settings

3. **Test Print Format Integration:**
   - Open any Print Format
   - Look for watermark controls in the sidebar
   - Test applying different templates and settings

## Step 10: Create Default Templates

After successful installation, you can create default templates either through the UI or programmatically:

```python
# Execute in Frappe console (bench --site your-site console)
from print_designer.patches.migrate_watermark_settings import create_default_templates
create_default_templates()
```

## Troubleshooting

### Common Issues:

1. **DocType Not Found Error:**
   - Ensure all JSON files are properly formatted
   - Run `bench --site your-site migrate` again

2. **Import Errors:**
   - Check that all `__init__.py` files exist
   - Verify Python file syntax

3. **JavaScript Not Loading:**
   - Clear browser cache
   - Check browser console for errors
   - Verify file paths in hooks.py

4. **CSS Not Applied:**
   - Clear Frappe cache: `bench --site your-site clear-cache`
   - Check CSS file exists in public/css/

5. **Migration Fails:**
   - Check if Print Settings doctype exists
   - Verify custom field names match your existing setup
   - Run migration script manually with error handling

### Debug Commands:

```bash
# Check app status
bench --site your-site list-apps

# View migration logs
tail -f sites/your-site/logs/worker.log

# Check DocType integrity
bench --site your-site console
>>> frappe.get_meta("Watermark Settings").fields

# Clear specific cache
bench --site your-site console
>>> frappe.cache().delete_key("watermark_settings")
```

## Post-Installation Setup

1. **Configure Global Settings:**
   - Open Watermark Settings
   - Set default font, position, colors
   - Enable watermark system

2. **Create Templates:**
   - Add templates for common use cases
   - Test different configurations

3. **Set Print Format Configs:**
   - Configure specific print formats
   - Test watermark display in print preview

4. **Train Users:**
   - Show how to apply watermarks
   - Explain template vs. custom settings
   - Demonstrate print preview functionality

This completes the installation and setup of the DocType-based watermark system for your Frappe/ERPNext Print Designer.
