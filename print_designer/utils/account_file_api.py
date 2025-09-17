"""
Account File-based API - Direct access to Account Thai translations

Provides file-based access to account glossary for external servers through
shared file system or file synchronization. Automatically generates JSON files
during install/migrate for external system consumption.
"""

import os
import json
import frappe
from frappe.utils import now_datetime, get_site_path
from pathlib import Path


def generate_account_files_for_external_access():
    """
    Generate JSON files for external server access during install/migrate
    Creates multiple formats in accessible locations
    """
    try:
        from print_designer.utils.account_glossary import ACCOUNT_GLOSSARY, ACCOUNT_GLOSSARY_METADATA

        print("🔄 Generating Account Thai translation files for external access...")

        # Define output directory (accessible to external servers)
        site_path = get_site_path()
        output_dir = os.path.join(site_path, "public", "files", "account_translations")

        # Ensure directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 1. Generate simple mapping file (most common use case)
        simple_mapping = {
            "version": "1.0",
            "generated_at": now_datetime().isoformat(),
            "total_translations": len(ACCOUNT_GLOSSARY),
            "mapping": ACCOUNT_GLOSSARY
        }

        simple_file = os.path.join(output_dir, "account_mapping.json")
        with open(simple_file, 'w', encoding='utf-8') as f:
            json.dump(simple_mapping, f, ensure_ascii=False, indent=2)

        # 2. Generate reverse mapping (Thai to English)
        reverse_mapping = {
            "version": "1.0",
            "generated_at": now_datetime().isoformat(),
            "total_translations": len(ACCOUNT_GLOSSARY),
            "mapping": {thai: english for english, thai in ACCOUNT_GLOSSARY.items()}
        }

        reverse_file = os.path.join(output_dir, "reverse_account_mapping.json")
        with open(reverse_file, 'w', encoding='utf-8') as f:
            json.dump(reverse_mapping, f, ensure_ascii=False, indent=2)

        # 3. Generate database-synchronized file with current account data
        database_mapping = generate_database_mapping()
        db_file = os.path.join(output_dir, "current_accounts.json")
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(database_mapping, f, ensure_ascii=False, indent=2)

        # 4. Generate metadata file
        metadata = {
            **ACCOUNT_GLOSSARY_METADATA,
            "generated_at": now_datetime().isoformat(),
            "files_generated": [
                "account_mapping.json",
                "reverse_account_mapping.json",
                "current_accounts.json",
                "metadata.json"
            ],
            "access_urls": {
                "account_mapping": f"/files/account_translations/account_mapping.json",
                "reverse_mapping": f"/files/account_translations/reverse_account_mapping.json",
                "current_accounts": f"/files/account_translations/current_accounts.json",
                "metadata": f"/files/account_translations/metadata.json"
            },
            "usage_examples": {
                "direct_url": "https://your-domain.com/files/account_translations/account_mapping.json",
                "local_file": f"{output_dir}/account_mapping.json"
            }
        }

        metadata_file = os.path.join(output_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 5. Generate README file for external developers
        readme_content = generate_readme_content()
        readme_file = os.path.join(output_dir, "README.md")
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"✅ Generated 5 files in: {output_dir}")
        print(f"   📁 account_mapping.json ({len(ACCOUNT_GLOSSARY)} translations)")
        print(f"   📁 reverse_account_mapping.json (Thai → English)")
        print(f"   📁 current_accounts.json (Database synchronized)")
        print(f"   📁 metadata.json (File information)")
        print(f"   📁 README.md (Usage documentation)")

        return {
            "success": True,
            "output_directory": output_dir,
            "files_generated": 5,
            "translations_count": len(ACCOUNT_GLOSSARY),
            "access_urls": metadata["access_urls"]
        }

    except Exception as e:
        error_msg = f"Error generating account files: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg)
        return {"success": False, "error": error_msg}


def generate_database_mapping():
    """Generate mapping with current database account data"""
    try:
        # Get current accounts from database
        accounts = frappe.get_all("Account",
            fields=["name", "account_name", "account_name_th", "account_type", "company"],
            filters={"account_name_th": ["!=", ""]},
            order_by="account_name"
        )

        database_data = {
            "version": "1.0",
            "generated_at": now_datetime().isoformat(),
            "source": "database",
            "total_accounts": len(accounts),
            "accounts": []
        }

        for account in accounts:
            database_data["accounts"].append({
                "id": account.name,
                "english_name": account.account_name,
                "thai_name": account.account_name_th,
                "account_type": account.account_type,
                "company": account.company
            })

        # Also include simple mapping for quick lookup
        database_data["simple_mapping"] = {
            account.account_name: account.account_name_th
            for account in accounts
        }

        return database_data

    except Exception as e:
        print(f"⚠️ Could not generate database mapping: {str(e)}")
        # Fallback to glossary file
        from print_designer.utils.account_glossary import ACCOUNT_GLOSSARY
        return {
            "version": "1.0",
            "generated_at": now_datetime().isoformat(),
            "source": "glossary_fallback",
            "total_accounts": len(ACCOUNT_GLOSSARY),
            "simple_mapping": ACCOUNT_GLOSSARY,
            "note": "Database access failed, using static glossary"
        }


def generate_readme_content():
    """Generate README content for external developers"""
    return """# Account Thai Translations - File Access

## Overview
This directory contains Account Name Thai translations in JSON format, automatically generated during Frappe app installation/migration.

## Files Available

### 1. account_mapping.json
Simple English → Thai mapping for account names.
```json
{
  "version": "1.0",
  "generated_at": "2025-01-17T12:30:45",
  "total_translations": 88,
  "mapping": {
    "Cash": "เงินสด",
    "Bank Account": "บัญชีธนาคาร",
    "Accounts Receivable": "ลูกหนี้การค้า"
  }
}
```

### 2. reverse_account_mapping.json
Thai → English mapping for reverse lookups.

### 3. current_accounts.json
Database-synchronized account data with detailed information.

### 4. metadata.json
File metadata and access information.

## Access Methods

### Direct HTTP Access
```bash
# Download mapping file
curl "https://your-domain.com/files/account_translations/account_mapping.json"

# Using wget
wget "https://your-domain.com/files/account_translations/account_mapping.json"
```

### File System Access
```bash
# Direct file access (if on same server)
cat "/path/to/site/public/files/account_translations/account_mapping.json"
```

### Programming Examples

#### JavaScript/Node.js
```javascript
const fs = require('fs');
const https = require('https');

// Method 1: HTTP Download
https.get('https://your-domain.com/files/account_translations/account_mapping.json', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const mapping = JSON.parse(data).mapping;
    console.log('Thai name for Cash:', mapping['Cash']);
  });
});

// Method 2: Direct file access (same server)
const mapping = JSON.parse(
  fs.readFileSync('/path/to/site/public/files/account_translations/account_mapping.json')
).mapping;
```

#### Python
```python
import json
import requests

# Method 1: HTTP Download
response = requests.get('https://your-domain.com/files/account_translations/account_mapping.json')
mapping = response.json()['mapping']
print(f"Thai name for Cash: {mapping['Cash']}")

# Method 2: Direct file access
with open('/path/to/site/public/files/account_translations/account_mapping.json') as f:
    data = json.load(f)
    mapping = data['mapping']
```

#### PHP
```php
// Method 1: HTTP Download
$json = file_get_contents('https://your-domain.com/files/account_translations/account_mapping.json');
$data = json_decode($json, true);
$mapping = $data['mapping'];
echo "Thai name for Cash: " . $mapping['Cash'];

// Method 2: Direct file access
$data = json_decode(
    file_get_contents('/path/to/site/public/files/account_translations/account_mapping.json'),
    true
);
$mapping = $data['mapping'];
```

## File Update Schedule

Files are automatically regenerated:
- During app installation (`bench install-app print_designer`)
- During database migration (`bench migrate`)
- When account Thai translations are updated

## File Locations

Files are stored in: `sites/[site-name]/public/files/account_translations/`

Web accessible at: `https://your-domain.com/files/account_translations/`

## Integration Tips

1. **Caching**: Files change infrequently, cache for 1-24 hours
2. **Error Handling**: Check file existence and JSON validity
3. **Encoding**: Files use UTF-8 encoding for Thai characters
4. **Version Check**: Use `generated_at` field to detect updates
5. **Fallback**: Keep local copy in case of network issues

## File Permissions

Ensure external servers have read access to the files directory:
```bash
chmod 644 /path/to/site/public/files/account_translations/*.json
```
"""


def update_files_on_account_change():
    """
    Hook to regenerate files when account translations are updated
    Can be called from DocType hooks or scheduled jobs
    """
    try:
        result = generate_account_files_for_external_access()
        if result["success"]:
            print(f"🔄 Updated account translation files: {result['files_generated']} files")
        return result
    except Exception as e:
        frappe.log_error(f"Failed to update account translation files: {str(e)}")
        return {"success": False, "error": str(e)}


def get_file_access_info():
    """Get information about generated files for debugging"""
    try:
        site_path = get_site_path()
        output_dir = os.path.join(site_path, "public", "files", "account_translations")

        if not os.path.exists(output_dir):
            return {
                "status": "not_generated",
                "message": "Translation files have not been generated yet"
            }

        files_info = []
        for filename in ["account_mapping.json", "reverse_account_mapping.json",
                        "current_accounts.json", "metadata.json", "README.md"]:
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                files_info.append({
                    "name": filename,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "url": f"/files/account_translations/{filename}"
                })

        return {
            "status": "available",
            "directory": output_dir,
            "files": files_info,
            "total_files": len(files_info)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# CLI-friendly functions for bench console access
def generate_files():
    """Simple function for bench console usage"""
    return generate_account_files_for_external_access()


def check_files():
    """Check file status from bench console"""
    info = get_file_access_info()
    print(f"📊 File Status: {info['status']}")
    if info['status'] == 'available':
        print(f"📁 Directory: {info['directory']}")
        print(f"📄 Files: {info['total_files']}")
        for file_info in info['files']:
            print(f"   • {file_info['name']} ({file_info['size']} bytes)")
    return info