# External API Integration Guide

## Account Thai Translations API for External Servers

This guide explains how external servers can access Account Name (TH) data from your Frappe/ERPNext system through REST API endpoints.

## 🚀 Quick Start

### Base URL
```
https://your-domain.com/api/method/print_designer.api.account_api
```

### API Endpoints Overview

| Endpoint | Description | Guest Access |
|----------|-------------|------------- |
| `get_accounts_with_thai_names` | Get all accounts with Thai translations | ✅ Yes |
| `get_account_thai_mapping` | Get account name mapping | ✅ Yes |
| `search_accounts_thai` | Search accounts by name | ✅ Yes |
| `get_account_by_name` | Get specific account details | ✅ Yes |
| `sync_accounts_to_external_system` | Push data to external system | ❌ Auth Required |

## 📖 Detailed API Documentation

### 1. Get All Accounts with Thai Names

**Endpoint**: `GET /api/method/print_designer.api.account_api.get_accounts_with_thai_names`

**Parameters**:
- `company` (optional): Filter by company name
- `format` (optional): Response format (`json`, `csv`, `dict`) - default: `json`
- `include_balance` (optional): Include account balances - default: `false`

**Example Requests**:
```bash
# Get all accounts with Thai names (JSON format)
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_accounts_with_thai_names"

# Get accounts for specific company with balances
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_accounts_with_thai_names?company=MyCompany&include_balance=true"

# Get data in CSV format
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_accounts_with_thai_names?format=csv"
```

**Example Response** (JSON format):
```json
{
  "success": true,
  "data": [
    {
      "name": "ACC-001",
      "account_name": "Cash",
      "account_name_th": "เงินสด",
      "account_type": "Asset",
      "account_number": "1001",
      "company": "My Company",
      "is_group": 0,
      "parent_account": "Current Assets"
    },
    {
      "name": "ACC-002",
      "account_name": "Bank Account",
      "account_name_th": "บัญชีธนาคาร",
      "account_type": "Asset",
      "account_number": "1002",
      "company": "My Company",
      "is_group": 0,
      "parent_account": "Current Assets"
    }
  ],
  "count": 88,
  "company": "All Companies",
  "timestamp": "2025-01-17 12:30:45",
  "include_balance": false
}
```

### 2. Get Account Name Mapping

**Endpoint**: `GET /api/method/print_designer.api.account_api.get_account_thai_mapping`

**Parameters**:
- `simple` (optional): Return simple key-value mapping - default: `true`

**Example Request**:
```bash
# Simple mapping
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_account_thai_mapping"

# Detailed mapping
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_account_thai_mapping?simple=false"
```

**Example Response** (Simple):
```json
{
  "success": true,
  "mapping": {
    "Cash": "เงินสด",
    "Bank Account": "บัญชีธนาคาร",
    "Accounts Receivable": "ลูกหนี้การค้า",
    "Sales": "ขาย"
  },
  "count": 88
}
```

### 3. Search Accounts

**Endpoint**: `GET /api/method/print_designer.api.account_api.search_accounts_thai`

**Parameters**:
- `query` (required): Search term (English or Thai)
- `limit` (optional): Maximum results - default: `20`

**Example Request**:
```bash
# Search in English
curl "https://your-domain.com/api/method/print_designer.api.account_api.search_accounts_thai?query=cash"

# Search in Thai
curl "https://your-domain.com/api/method/print_designer.api.account_api.search_accounts_thai?query=เงินสด"
```

### 4. Get Specific Account

**Endpoint**: `GET /api/method/print_designer.api.account_api.get_account_by_name`

**Parameters**:
- `account_name` (required): Account name to lookup
- `with_thai` (optional): Include Thai translation - default: `true`

**Example Request**:
```bash
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_account_by_name?account_name=Cash"
```

## 🔧 Integration Examples

### JavaScript/Node.js
```javascript
const axios = require('axios');

class AccountAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async getAllAccounts(company = null, includeBalance = false) {
        const params = {
            format: 'json',
            include_balance: includeBalance
        };
        if (company) params.company = company;

        const response = await axios.get(
            `${this.baseUrl}/api/method/print_designer.api.account_api.get_accounts_with_thai_names`,
            { params }
        );
        return response.data;
    }

    async getAccountMapping() {
        const response = await axios.get(
            `${this.baseUrl}/api/method/print_designer.api.account_api.get_account_thai_mapping`
        );
        return response.data.mapping;
    }

    async searchAccounts(query, limit = 20) {
        const response = await axios.get(
            `${this.baseUrl}/api/method/print_designer.api.account_api.search_accounts_thai`,
            { params: { query, limit } }
        );
        return response.data.results;
    }
}

// Usage
const accountAPI = new AccountAPI('https://your-domain.com');

// Get all accounts
accountAPI.getAllAccounts().then(data => {
    console.log(`Found ${data.count} accounts with Thai translations`);
    data.data.forEach(account => {
        console.log(`${account.account_name} → ${account.account_name_th}`);
    });
});

// Get mapping for dropdown/select options
accountAPI.getAccountMapping().then(mapping => {
    Object.entries(mapping).forEach(([english, thai]) => {
        console.log(`${english}: ${thai}`);
    });
});
```

### Python
```python
import requests

class AccountAPI:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_all_accounts(self, company=None, include_balance=False):
        params = {
            'format': 'json',
            'include_balance': str(include_balance).lower()
        }
        if company:
            params['company'] = company

        response = requests.get(
            f"{self.base_url}/api/method/print_designer.api.account_api.get_accounts_with_thai_names",
            params=params
        )
        return response.json()

    def get_account_mapping(self, simple=True):
        params = {'simple': str(simple).lower()}
        response = requests.get(
            f"{self.base_url}/api/method/print_designer.api.account_api.get_account_thai_mapping",
            params=params
        )
        return response.json()

    def search_accounts(self, query, limit=20):
        params = {'query': query, 'limit': limit}
        response = requests.get(
            f"{self.base_url}/api/method/print_designer.api.account_api.search_accounts_thai",
            params=params
        )
        return response.json()

# Usage
api = AccountAPI('https://your-domain.com')

# Get all accounts
accounts_data = api.get_all_accounts(company="My Company", include_balance=True)
print(f"Found {accounts_data['count']} accounts")

# Get simple mapping
mapping_data = api.get_account_mapping()
for english_name, thai_name in mapping_data['mapping'].items():
    print(f"{english_name} → {thai_name}")

# Search for accounts
results = api.search_accounts("เงิน")  # Search for accounts containing "เงิน"
for account in results['results']:
    print(f"{account['account_name']} ({account['account_name_th']})")
```

### PHP
```php
<?php
class AccountAPI {
    private $baseUrl;

    public function __construct($baseUrl) {
        $this->baseUrl = $baseUrl;
    }

    public function getAllAccounts($company = null, $includeBalance = false) {
        $params = [
            'format' => 'json',
            'include_balance' => $includeBalance ? 'true' : 'false'
        ];
        if ($company) {
            $params['company'] = $company;
        }

        $url = $this->baseUrl . '/api/method/print_designer.api.account_api.get_accounts_with_thai_names?' . http_build_query($params);
        $response = file_get_contents($url);
        return json_decode($response, true);
    }

    public function getAccountMapping($simple = true) {
        $params = ['simple' => $simple ? 'true' : 'false'];
        $url = $this->baseUrl . '/api/method/print_designer.api.account_api.get_account_thai_mapping?' . http_build_query($params);
        $response = file_get_contents($url);
        return json_decode($response, true);
    }
}

// Usage
$api = new AccountAPI('https://your-domain.com');

// Get accounts
$accountsData = $api->getAllAccounts();
echo "Found " . $accountsData['count'] . " accounts\n";

// Get mapping
$mappingData = $api->getAccountMapping();
foreach ($mappingData['mapping'] as $english => $thai) {
    echo "$english → $thai\n";
}
?>
```

## 🔒 Authentication Options

### Guest Access (Default)
Most endpoints allow guest access for easy integration. No authentication required.

### API Key Authentication (Optional)
For secured access, use Frappe's API key authentication:

```bash
curl -H "Authorization: token api_key:api_secret" \
     "https://your-domain.com/api/method/print_designer.api.account_api.get_accounts_with_thai_names"
```

### Session-based Authentication
For web applications, use session cookies after login.

## 🎯 Common Use Cases

### 1. Populate Dropdown/Select Options
```javascript
// Get account mapping for form dropdowns
const mapping = await accountAPI.getAccountMapping();
const selectOptions = Object.entries(mapping).map(([english, thai]) => ({
    value: english,
    label: `${english} (${thai})`
}));
```

### 2. Autocomplete Search
```javascript
// Implement autocomplete with Thai support
async function searchAccounts(query) {
    const results = await accountAPI.search_accounts(query);
    return results.results.map(account => ({
        id: account.name,
        text: `${account.account_name} (${account.account_name_th})`
    }));
}
```

### 3. Data Synchronization
```python
# Sync account data to external database
def sync_accounts_to_local_db():
    api = AccountAPI('https://your-domain.com')
    accounts = api.get_all_accounts(include_balance=True)

    for account in accounts['data']:
        # Update or insert into local database
        update_local_account({
            'external_id': account['name'],
            'english_name': account['account_name'],
            'thai_name': account['account_name_th'],
            'account_type': account['account_type'],
            'balance': account.get('current_balance', 0)
        })
```

### 4. Reporting Integration
```python
# Generate bilingual reports
def generate_account_report():
    accounts = api.get_all_accounts(format='json')

    report_data = []
    for account in accounts['data']:
        report_data.append({
            'Account Code': account['account_number'],
            'English Name': account['account_name'],
            'Thai Name': account['account_name_th'],
            'Type': account['account_type'],
            'Company': account['company']
        })

    return report_data
```

## 📊 Performance Considerations

- **Caching**: API responses are suitable for caching. Consider caching account mappings for 1-24 hours.
- **Pagination**: Use the `limit` parameter for search endpoints to control response size.
- **Filtering**: Use company filters to reduce data transfer when working with specific companies.
- **Format Selection**: Use CSV format for bulk data processing, JSON for application integration.

## 🐛 Error Handling

All endpoints return consistent error format:
```json
{
  "success": false,
  "error": "Error description",
  "message": "User-friendly error message"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (missing required parameters)
- `404`: Not Found
- `500`: Internal Server Error

## 🔄 Real-time Updates

For real-time synchronization, consider implementing webhooks or scheduled polling:

```python
import schedule
import time

def sync_accounts():
    # Fetch latest account data
    accounts = api.get_all_accounts()
    # Update local system
    update_local_accounts(accounts['data'])

# Schedule sync every hour
schedule.every().hour.do(sync_accounts)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 📝 Testing the API

### Quick Test
```bash
# Test basic connectivity
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_api_documentation"

# Test account retrieval
curl "https://your-domain.com/api/method/print_designer.api.account_api.get_accounts_with_thai_names?limit=5"
```

### Test with Authentication
```bash
# With API key (if required)
curl -H "Authorization: Bearer your_api_key" \
     "https://your-domain.com/api/method/print_designer.api.account_api.get_accounts_with_thai_names"
```

## 💡 Tips for External Integration

1. **Start Simple**: Begin with the mapping endpoint to understand data structure
2. **Cache Wisely**: Account data is relatively static, suitable for caching
3. **Handle Thai Text**: Ensure your system supports UTF-8 encoding for Thai characters
4. **Test Thoroughly**: Test with different company filters and search queries
5. **Monitor Usage**: Track API usage to avoid rate limits
6. **Plan for Growth**: Consider pagination for large datasets

This API provides complete external access to your Account Thai translations, enabling seamless integration with other systems while maintaining data consistency and security.