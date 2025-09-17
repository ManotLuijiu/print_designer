# Account Thai Translation Usage Guide

## 🚀 Complete Implementation: File-based + Database Access

Your Account Thai translation system now provides **both approaches**:
1. **File-based access** (automatic) - Generated during install/migrate
2. **Database population** (manual) - Apply translations to Account records

## 📋 Step-by-Step Usage

### Step 1: Apply Translations to Database (First Time)

```bash
# Navigate to bench
cd /Users/manotlj/frappe-bench

# Start console
bench --site moo.localhost console

# Apply Thai translations to Account.account_name_th field
from print_designer.commands.apply_account_thai_translations import apply_account_thai_translations
apply_account_thai_translations()
```

### Step 2: Access Files for External Servers (Automatic)

Files are **automatically generated** during:
- App installation (`bench install-app print_designer`)
- Database migration (`bench migrate`)

**Generated Files Location**:
```
sites/moo.localhost/public/files/account_translations/
├── account_mapping.json          # English → Thai mapping
├── reverse_account_mapping.json  # Thai → English mapping
├── current_accounts.json         # Database synchronized data
├── metadata.json                 # File information
└── README.md                     # Usage documentation
```

## 🌐 External Server Access Methods

### Method 1: Direct HTTP Download (Recommended)
```bash
# Download mapping file
curl "http://moo.localhost:8000/files/account_translations/account_mapping.json"

# Download with wget
wget "http://moo.localhost:8000/files/account_translations/account_mapping.json"
```

### Method 2: File System Access (Same Server)
```bash
# Direct file reading (if on same server)
cat "/Users/manotlj/frappe-bench/sites/moo.localhost/public/files/account_translations/account_mapping.json"
```

## 💻 Programming Examples

### JavaScript/Node.js
```javascript
const https = require('https');
const fs = require('fs');

// Method 1: HTTP Download
function loadAccountMapping() {
  const url = 'http://moo.localhost:8000/files/account_translations/account_mapping.json';

  https.get(url, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      const mapping = JSON.parse(data).mapping;
      console.log('Thai translation for Cash:', mapping['Cash']); // เงินสด
      console.log('Total translations:', Object.keys(mapping).length);
    });
  });
}

// Method 2: Direct file access (same server)
function loadAccountMappingLocal() {
  const filePath = '/Users/manotlj/frappe-bench/sites/moo.localhost/public/files/account_translations/account_mapping.json';
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  return data.mapping;
}

// Usage
loadAccountMapping();
```

### Python
```python
import json
import requests

# Method 1: HTTP Download
def load_account_mapping():
    url = 'http://moo.localhost:8000/files/account_translations/account_mapping.json'
    response = requests.get(url)
    data = response.json()
    return data['mapping']

# Method 2: Direct file access
def load_account_mapping_local():
    file_path = '/Users/manotlj/frappe-bench/sites/moo.localhost/public/files/account_translations/account_mapping.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['mapping']

# Usage examples
mapping = load_account_mapping()
print(f"Thai name for Cash: {mapping['Cash']}")  # เงินสด
print(f"Total translations: {len(mapping)}")     # 88

# Reverse lookup (Thai → English)
reverse_url = 'http://moo.localhost:8000/files/account_translations/reverse_account_mapping.json'
reverse_data = requests.get(reverse_url).json()
reverse_mapping = reverse_data['mapping']
print(f"English name for เงินสด: {reverse_mapping['เงินสด']}")  # Cash
```

### PHP
```php
<?php
// Method 1: HTTP Download
function loadAccountMapping() {
    $url = 'http://moo.localhost:8000/files/account_translations/account_mapping.json';
    $json = file_get_contents($url);
    $data = json_decode($json, true);
    return $data['mapping'];
}

// Method 2: Direct file access
function loadAccountMappingLocal() {
    $filePath = '/Users/manotlj/frappe-bench/sites/moo.localhost/public/files/account_translations/account_mapping.json';
    $json = file_get_contents($filePath);
    $data = json_decode($json, true);
    return $data['mapping'];
}

// Usage
$mapping = loadAccountMapping();
echo "Thai name for Cash: " . $mapping['Cash'] . "\n";  // เงินสด
echo "Total translations: " . count($mapping) . "\n";   // 88

// Build dropdown options
$options = [];
foreach ($mapping as $english => $thai) {
    $options[] = [
        'value' => $english,
        'label' => "$english ($thai)"
    ];
}
?>
```

## 🔧 File Management Commands

### Check File Status
```bash
# In bench console
from print_designer.utils.account_file_api import check_files
check_files()
```

### Regenerate Files Manually
```bash
# In bench console
from print_designer.utils.account_file_api import generate_files
generate_files()
```

### View File Information
```bash
# In bench console
from print_designer.utils.account_file_api import get_file_access_info
info = get_file_access_info()
print(info)
```

## 📊 File Formats Available

### 1. account_mapping.json (Simple Mapping)
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

### 2. current_accounts.json (Database Synchronized)
```json
{
  "version": "1.0",
  "generated_at": "2025-01-17T12:30:45",
  "source": "database",
  "total_accounts": 88,
  "accounts": [
    {
      "id": "ACC-001",
      "english_name": "Cash",
      "thai_name": "เงินสด",
      "account_type": "Asset",
      "company": "My Company"
    }
  ],
  "simple_mapping": {
    "Cash": "เงินสด"
  }
}
```

## 🎯 Common Integration Scenarios

### 1. Form Dropdown/Select Options
```javascript
// Load account options for HTML select
async function loadAccountOptions() {
  const response = await fetch('http://moo.localhost:8000/files/account_translations/account_mapping.json');
  const data = await response.json();

  const select = document.getElementById('accountSelect');
  Object.entries(data.mapping).forEach(([english, thai]) => {
    const option = document.createElement('option');
    option.value = english;
    option.textContent = `${english} (${thai})`;
    select.appendChild(option);
  });
}
```

### 2. Data Table Display
```python
# Display accounts in a table with both languages
import pandas as pd
import requests

def create_account_table():
    url = 'http://moo.localhost:8000/files/account_translations/current_accounts.json'
    response = requests.get(url)
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data['accounts'])
    df = df[['english_name', 'thai_name', 'account_type', 'company']]
    df.columns = ['English Name', 'Thai Name', 'Type', 'Company']

    return df

# Usage
table = create_account_table()
print(table.head())
```

### 3. Search/Autocomplete
```javascript
// Implement search with both English and Thai
async function searchAccounts(query) {
  // Load both mappings
  const [normal, reverse] = await Promise.all([
    fetch('http://moo.localhost:8000/files/account_translations/account_mapping.json').then(r => r.json()),
    fetch('http://moo.localhost:8000/files/account_translations/reverse_account_mapping.json').then(r => r.json())
  ]);

  const results = [];
  const queryLower = query.toLowerCase();

  // Search English names
  Object.entries(normal.mapping).forEach(([english, thai]) => {
    if (english.toLowerCase().includes(queryLower)) {
      results.push({ english, thai, match: 'english' });
    }
  });

  // Search Thai names
  Object.entries(reverse.mapping).forEach(([thai, english]) => {
    if (thai.includes(query)) {
      results.push({ english, thai, match: 'thai' });
    }
  });

  return results;
}
```

### 4. Report Generation
```python
# Generate bilingual report
def generate_bilingual_report():
    import requests

    url = 'http://moo.localhost:8000/files/account_translations/current_accounts.json'
    data = requests.get(url).json()

    # Create report
    report = []
    for account in data['accounts']:
        report.append({
            'Account ID': account['id'],
            'English Name': account['english_name'],
            'ชื่อภาษาไทย': account['thai_name'],
            'Type': account['account_type'],
            'Company': account['company']
        })

    return report
```

## 🔄 Automatic Updates

Files are automatically regenerated when:
1. **App Installation**: `bench install-app print_designer`
2. **Database Migration**: `bench migrate`
3. **Manual Trigger**: Using the provided commands

## 🛠️ Troubleshooting

### Issue 1: Files Not Found
```bash
# Check if files were generated
from print_designer.utils.account_file_api import check_files
check_files()

# If not found, generate manually
from print_designer.utils.account_file_api import generate_files
generate_files()
```

### Issue 2: Empty Mapping
```bash
# First apply translations to database
from print_designer.commands.apply_account_thai_translations import apply_account_thai_translations
apply_account_thai_translations()

# Then regenerate files
from print_designer.utils.account_file_api import generate_files
generate_files()
```

### Issue 3: File Permissions
```bash
# Fix file permissions (if needed)
chmod 644 /Users/manotlj/frappe-bench/sites/moo.localhost/public/files/account_translations/*.json
```

## 📈 Performance Tips

1. **Cache Files**: Files change infrequently, cache for 1-24 hours
2. **Prefer HTTP**: Faster than API calls, no authentication needed
3. **Use Simple Mapping**: For basic key-value lookups
4. **Monitor File Size**: Current files are ~20KB, suitable for frequent loading
5. **Batch Operations**: Load once, use multiple times in your application

## 🎯 Integration Benefits

- **Zero Authentication**: Files accessible without API keys
- **High Performance**: Direct file access, no database queries
- **Always Fresh**: Auto-updated during migrations
- **Multiple Formats**: Choose format that fits your needs
- **Cross-Platform**: Works with any programming language
- **Offline Capable**: Download and cache locally

Your Account Thai translations are now available to all external servers through simple file access! 🚀