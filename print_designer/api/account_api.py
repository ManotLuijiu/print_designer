"""
Account API - External Access to Account Thai Translations

Provides REST API endpoints for external servers to access Account Name (TH) data.
Supports various formats and filtering options for integration flexibility.
"""

import frappe
from frappe import _
from frappe.utils import flt, cstr
import json

@frappe.whitelist(allow_guest=True)
def get_accounts_with_thai_names(company=None, format="json", include_balance=False):
    """
    Get all accounts with Thai translations for external server integration

    Args:
        company (str): Filter by specific company (optional)
        format (str): Response format - 'json', 'csv', 'dict' (default: json)
        include_balance (bool): Include account balances (default: False)

    Returns:
        dict: Account data with Thai translations in requested format
    """
    try:
        # Build filters
        filters = {}
        if company:
            filters["company"] = company

        # Base fields
        fields = [
            "name",
            "account_name",
            "account_name_th",
            "account_type",
            "account_number",
            "company",
            "is_group",
            "parent_account"
        ]

        # Add balance fields if requested
        if include_balance:
            fields.extend([
                "account_currency",
                "balance_must_be"
            ])

        # Get accounts with Thai translations
        accounts = frappe.get_all("Account",
            filters=filters,
            fields=fields,
            order_by="account_name"
        )

        # Filter out accounts without Thai translations
        translated_accounts = [
            account for account in accounts
            if account.get('account_name_th')
        ]

        # Add balance information if requested
        if include_balance:
            for account in translated_accounts:
                try:
                    balance = frappe.db.get_value("Account", account.name, "balance") or 0
                    account["current_balance"] = flt(balance, 2)
                except:
                    account["current_balance"] = 0.0

        # Format response based on requested format
        if format.lower() == "csv":
            return format_as_csv(translated_accounts)
        elif format.lower() == "dict":
            return format_as_dict(translated_accounts)
        else:
            # Default JSON format
            return {
                "success": True,
                "data": translated_accounts,
                "count": len(translated_accounts),
                "company": company or "All Companies",
                "timestamp": frappe.utils.now(),
                "include_balance": include_balance
            }

    except Exception as e:
        frappe.log_error(f"Error in get_accounts_with_thai_names: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve account data"
        }

@frappe.whitelist(allow_guest=True)
def get_accounts_enhanced(company=None, include_thai=True, include_balance=False, filters=None):
    """
    Enhanced account fetching following ERPNext patterns - automatically includes Thai names
    This method follows ERPNext's standard habit of including all relevant fields

    Args:
        company (str): Filter by specific company (optional)
        include_thai (bool): Include Thai account names (default: True)
        include_balance (bool): Include account balances (default: False)
        filters (dict): Additional filters for account query

    Returns:
        dict: Enhanced account data with Thai names included by default
    """
    try:
        # Build filters
        query_filters = {}
        if company:
            query_filters["company"] = company

        # Add custom filters if provided
        if filters and isinstance(filters, dict):
            query_filters.update(filters)

        # Standard ERPNext account fields + Thai enhancement
        fields = [
            "name",
            "account_name",
            "account_type",
            "account_number",
            "company",
            "is_group",
            "parent_account",
            "account_currency",
            "disabled"
        ]

        # Add Thai name field by default (ERPNext pattern enhancement)
        if include_thai:
            fields.append("account_name_th")

        # Add balance fields if requested
        if include_balance:
            fields.extend(["balance_must_be", "freeze_account"])

        # Get accounts following ERPNext query pattern
        accounts = frappe.get_all("Account",
            filters=query_filters,
            fields=fields,
            order_by="account_name"
        )

        # Enhanced data processing
        for account in accounts:
            # Add display name (English + Thai if available)
            if include_thai and account.get('account_name_th'):
                account["display_name"] = f"{account.account_name} ({account.account_name_th})"
                account["has_thai_translation"] = True
            else:
                account["display_name"] = account.account_name
                account["has_thai_translation"] = False

            # Add current balance if requested (ERPNext enhancement)
            if include_balance:
                try:
                    balance = frappe.db.get_value("Account", account.name, "balance") or 0
                    account["current_balance"] = flt(balance, 2)
                except:
                    account["current_balance"] = 0.0

        return {
            "success": True,
            "data": accounts,
            "count": len(accounts),
            "company": company or "All Companies",
            "thai_translations_included": include_thai,
            "timestamp": frappe.utils.now()
        }

    except Exception as e:
        frappe.log_error(f"Error in get_accounts_enhanced: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve enhanced account data"
        }

@frappe.whitelist(allow_guest=True)
def get_account_thai_mapping(simple=True):
    """
    Get account name to Thai name mapping for external systems

    Args:
        simple (bool): Return simple key-value mapping (default: True)

    Returns:
        dict: Account name mapping in various formats
    """
    try:
        accounts = frappe.get_all("Account",
            fields=["account_name", "account_name_th", "company", "account_type"],
            filters={"account_name_th": ["!=", ""]},
            order_by="account_name"
        )

        if simple:
            # Simple key-value mapping
            mapping = {
                account.account_name: account.account_name_th
                for account in accounts
            }
            return {
                "success": True,
                "mapping": mapping,
                "count": len(mapping)
            }
        else:
            # Detailed mapping with metadata
            detailed_mapping = {}
            for account in accounts:
                detailed_mapping[account.account_name] = {
                    "thai_name": account.account_name_th,
                    "company": account.company,
                    "account_type": account.account_type
                }

            return {
                "success": True,
                "detailed_mapping": detailed_mapping,
                "count": len(detailed_mapping)
            }

    except Exception as e:
        frappe.log_error(f"Error in get_account_thai_mapping: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def search_accounts_thai(query, limit=20):
    """
    Search accounts by English or Thai names for external autocomplete

    Args:
        query (str): Search query (English or Thai)
        limit (int): Maximum results to return (default: 20)

    Returns:
        dict: Matching accounts with Thai translations
    """
    try:
        # Search in both English and Thai names
        accounts = frappe.db.sql("""
            SELECT
                name,
                account_name,
                account_name_th,
                account_type,
                company
            FROM `tabAccount`
            WHERE (
                account_name LIKE %(query)s
                OR account_name_th LIKE %(query)s
            )
            AND account_name_th IS NOT NULL
            AND account_name_th != ''
            ORDER BY
                CASE
                    WHEN account_name LIKE %(exact_query)s THEN 1
                    WHEN account_name_th LIKE %(exact_query)s THEN 2
                    ELSE 3
                END,
                account_name
            LIMIT %(limit)s
        """, {
            "query": f"%{query}%",
            "exact_query": f"{query}%",
            "limit": limit
        }, as_dict=True)

        return {
            "success": True,
            "results": accounts,
            "count": len(accounts),
            "query": query
        }

    except Exception as e:
        frappe.log_error(f"Error in search_accounts_thai: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_account_by_name(account_name, with_thai=True):
    """
    Get specific account details by name with Thai translation

    Args:
        account_name (str): Account name to lookup
        with_thai (bool): Include Thai translation (default: True)

    Returns:
        dict: Account details with Thai name
    """
    try:
        filters = {"account_name": account_name}
        fields = ["name", "account_name", "account_type", "company", "account_number", "is_group"]

        if with_thai:
            fields.append("account_name_th")

        account = frappe.get_value("Account", filters, fields, as_dict=True)

        if not account:
            return {
                "success": False,
                "message": f"Account '{account_name}' not found"
            }

        # Add enhanced display information
        if with_thai and account.get('account_name_th'):
            account["display_name"] = f"{account.account_name} ({account.account_name_th})"
            account["has_thai_translation"] = True
        else:
            account["display_name"] = account.account_name
            account["has_thai_translation"] = False

        return {
            "success": True,
            "account": account
        }

    except Exception as e:
        frappe.log_error(f"Error in get_account_by_name: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_account_list_for_reports(company=None, account_type=None, is_group=None):
    """
    ERPNext-style account list for reports with automatic Thai name inclusion
    Follows standard ERPNext report data fetching patterns

    Args:
        company (str): Filter by company
        account_type (str): Filter by account type (Asset, Liability, etc.)
        is_group (bool): Filter by group accounts

    Returns:
        list: Account data formatted for ERPNext reports with Thai names
    """
    try:
        # Build filters following ERPNext pattern
        filters = {"disabled": 0}

        if company:
            filters["company"] = company
        if account_type:
            filters["account_type"] = account_type
        if is_group is not None:
            filters["is_group"] = is_group

        # Standard ERPNext report fields + Thai enhancement
        fields = [
            "name",
            "account_name",
            "account_name_th",  # Always include Thai name
            "account_type",
            "parent_account",
            "company",
            "is_group",
            "account_number",
            "account_currency"
        ]

        # Get accounts ordered by account name (ERPNext standard)
        accounts = frappe.get_all("Account",
            filters=filters,
            fields=fields,
            order_by="account_name"
        )

        # Format for ERPNext report consumption
        formatted_accounts = []
        for account in accounts:
            # Create ERPNext-style account entry with Thai enhancement
            account_entry = {
                "account": account.name,
                "account_name": account.account_name,
                "account_name_th": account.get("account_name_th") or "",
                "account_type": account.account_type,
                "parent_account": account.parent_account,
                "company": account.company,
                "is_group": account.is_group,
                "account_number": account.account_number,
                "currency": account.account_currency
            }

            # Add enhanced display name for UI consumption
            if account.get("account_name_th"):
                account_entry["display_name"] = f"{account.account_name} | {account.account_name_th}"
            else:
                account_entry["display_name"] = account.account_name

            formatted_accounts.append(account_entry)

        return {
            "success": True,
            "accounts": formatted_accounts,
            "count": len(formatted_accounts),
            "filters_applied": filters
        }

    except Exception as e:
        frappe.log_error(f"Error in get_account_list_for_reports: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve account list for reports"
        }

@frappe.whitelist()
def sync_accounts_to_external_system(external_api_url, api_key=None, company=None):
    """
    Push account data with Thai translations to external system

    Args:
        external_api_url (str): External API endpoint URL
        api_key (str): API authentication key (optional)
        company (str): Filter by company (optional)

    Returns:
        dict: Sync operation result
    """
    try:
        import requests

        # Get accounts data
        accounts_data = get_accounts_with_thai_names(
            company=company,
            format="json",
            include_balance=True
        )

        if not accounts_data.get("success"):
            return accounts_data

        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Send to external system
        response = requests.post(
            external_api_url,
            json=accounts_data,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return {
                "success": True,
                "message": f"Successfully synced {accounts_data['count']} accounts",
                "external_response": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"External API returned status {response.status_code}",
                "response_text": response.text
            }

    except Exception as e:
        frappe.log_error(f"Error in sync_accounts_to_external_system: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def format_as_csv(accounts):
    """Format accounts data as CSV string"""
    import csv
    import io

    if not accounts:
        return {"success": True, "csv_data": "", "count": 0}

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=accounts[0].keys())
    writer.writeheader()
    writer.writerows(accounts)

    return {
        "success": True,
        "csv_data": output.getvalue(),
        "count": len(accounts)
    }

def format_as_dict(accounts):
    """Format accounts data as nested dictionary by company"""
    result = {}

    for account in accounts:
        company = account.get("company", "Unknown")
        if company not in result:
            result[company] = []
        result[company].append(account)

    return {
        "success": True,
        "data_by_company": result,
        "total_companies": len(result),
        "total_accounts": len(accounts)
    }

@frappe.whitelist()
def get_account_with_thai_for_erpnext(account_name=None, account_id=None):
    """
    ERPNext integration utility - Get account data with Thai name for existing ERPNext flows
    This method is designed to be called by ERPNext reports and other modules

    Args:
        account_name (str): Account name for lookup
        account_id (str): Account ID for lookup (alternative to account_name)

    Returns:
        dict: Account data formatted for ERPNext consumption with Thai enhancement
    """
    try:
        if not account_name and not account_id:
            return {
                "success": False,
                "message": "Either account_name or account_id is required"
            }

        # Build filter based on provided parameter
        if account_id:
            filters = {"name": account_id}
        else:
            filters = {"account_name": account_name}

        # Get account with Thai enhancement
        account = frappe.get_value("Account", filters, [
            "name",
            "account_name",
            "account_name_th",
            "account_type",
            "parent_account",
            "company",
            "account_number",
            "is_group",
            "account_currency"
        ], as_dict=True)

        if not account:
            return {
                "success": False,
                "message": "Account not found"
            }

        # Format for ERPNext compatibility
        result = {
            "account_id": account.name,
            "account_name": account.account_name,
            "account_name_th": account.get("account_name_th") or "",
            "account_type": account.account_type,
            "parent_account": account.parent_account,
            "company": account.company,
            "account_number": account.account_number,
            "is_group": account.is_group,
            "currency": account.account_currency,
            "has_thai_translation": bool(account.get("account_name_th"))
        }

        # Add bilingual display name
        if account.get("account_name_th"):
            result["bilingual_name"] = f"{account.account_name} | {account.account_name_th}"
        else:
            result["bilingual_name"] = account.account_name

        return {
            "success": True,
            "account": result
        }

    except Exception as e:
        frappe.log_error(f"Error in get_account_with_thai_for_erpnext: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def enhance_account_data_with_thai(account_data):
    """
    Utility function to enhance existing ERPNext account data with Thai names
    Can be used by other modules to add Thai translations to their account queries

    Args:
        account_data (list or dict): Existing account data from ERPNext queries

    Returns:
        Enhanced account data with Thai names added
    """
    try:
        # Handle single account or list of accounts
        if isinstance(account_data, dict):
            accounts_to_process = [account_data]
            return_single = True
        elif isinstance(account_data, list):
            accounts_to_process = account_data
            return_single = False
        else:
            return account_data  # Return unchanged if not dict or list

        # Get all unique account names/IDs from the data
        account_identifiers = set()
        for account in accounts_to_process:
            if account.get("account"):
                account_identifiers.add(account["account"])
            elif account.get("account_name"):
                account_identifiers.add(account["account_name"])

        if not account_identifiers:
            return account_data  # No accounts to enhance

        # Bulk fetch Thai translations
        thai_translations = {}
        for identifier in account_identifiers:
            # Try by name first, then by ID
            thai_name = frappe.db.get_value("Account",
                ["name", "account_name"],
                "account_name_th",
                filters={"name": identifier}) or \
                       frappe.db.get_value("Account",
                ["account_name"],
                "account_name_th",
                filters={"account_name": identifier})

            if thai_name:
                thai_translations[identifier] = thai_name

        # Enhance the account data
        for account in accounts_to_process:
            account_key = account.get("account") or account.get("account_name")
            if account_key and account_key in thai_translations:
                # Add Thai name
                account["account_name_th"] = thai_translations[account_key]
                account["has_thai_translation"] = True

                # Add bilingual display name
                base_name = account.get("account_name") or account.get("account")
                account["display_name_bilingual"] = f"{base_name} | {thai_translations[account_key]}"
            else:
                account["account_name_th"] = ""
                account["has_thai_translation"] = False
                account["display_name_bilingual"] = account.get("account_name") or account.get("account", "")

        return accounts_to_process[0] if return_single else accounts_to_process

    except Exception as e:
        frappe.log_error(f"Error in enhance_account_data_with_thai: {str(e)}")
        return account_data  # Return original data if enhancement fails

@frappe.whitelist(allow_guest=True)
def get_api_documentation():
    """
    Get API documentation for external developers

    Returns:
        dict: Complete API documentation with examples
    """
    return {
        "api_version": "2.0",
        "base_url": frappe.utils.get_url(),
        "endpoints": {
            "get_accounts_enhanced": {
                "url": "/api/method/print_designer.api.account_api.get_accounts_enhanced",
                "method": "GET",
                "description": "Enhanced account fetching with automatic Thai name inclusion",
                "parameters": {
                    "company": "Filter by company name (optional)",
                    "include_thai": "Include Thai account names (default: true)",
                    "include_balance": "Include account balances (default: false)",
                    "filters": "Additional filters as JSON object (optional)"
                },
                "example": "/api/method/print_designer.api.account_api.get_accounts_enhanced?company=MyCompany&include_thai=true"
            },
            "get_account_list_for_reports": {
                "url": "/api/method/print_designer.api.account_api.get_account_list_for_reports",
                "method": "GET",
                "description": "ERPNext-style account list for reports with Thai names",
                "parameters": {
                    "company": "Filter by company (optional)",
                    "account_type": "Filter by account type (optional)",
                    "is_group": "Filter by group accounts (optional)"
                },
                "example": "/api/method/print_designer.api.account_api.get_account_list_for_reports?company=MyCompany&account_type=Asset"
            },
            "get_account_with_thai_for_erpnext": {
                "url": "/api/method/print_designer.api.account_api.get_account_with_thai_for_erpnext",
                "method": "GET",
                "description": "ERPNext integration utility for single account with Thai name",
                "parameters": {
                    "account_name": "Account name for lookup (optional)",
                    "account_id": "Account ID for lookup (optional)"
                },
                "example": "/api/method/print_designer.api.account_api.get_account_with_thai_for_erpnext?account_name=Cash"
            },
            "get_accounts_with_thai_names": {
                "url": "/api/method/print_designer.api.account_api.get_accounts_with_thai_names",
                "method": "GET",
                "description": "Get all accounts with Thai translations",
                "parameters": {
                    "company": "Filter by company name (optional)",
                    "format": "Response format: json, csv, dict (default: json)",
                    "include_balance": "Include account balances (default: false)"
                },
                "example": "/api/method/print_designer.api.account_api.get_accounts_with_thai_names?company=MyCompany&format=json&include_balance=true"
            },
            "get_account_thai_mapping": {
                "url": "/api/method/print_designer.api.account_api.get_account_thai_mapping",
                "method": "GET",
                "description": "Get account name to Thai name mapping",
                "parameters": {
                    "simple": "Return simple key-value mapping (default: true)"
                },
                "example": "/api/method/print_designer.api.account_api.get_account_thai_mapping?simple=false"
            },
            "search_accounts_thai": {
                "url": "/api/method/print_designer.api.account_api.search_accounts_thai",
                "method": "GET",
                "description": "Search accounts by English or Thai names",
                "parameters": {
                    "query": "Search query (required)",
                    "limit": "Maximum results (default: 20)"
                },
                "example": "/api/method/print_designer.api.account_api.search_accounts_thai?query=เงินสด&limit=10"
            },
            "get_account_by_name": {
                "url": "/api/method/print_designer.api.account_api.get_account_by_name",
                "method": "GET",
                "description": "Get specific account by name",
                "parameters": {
                    "account_name": "Account name to lookup (required)",
                    "with_thai": "Include Thai translation (default: true)"
                },
                "example": "/api/method/print_designer.api.account_api.get_account_by_name?account_name=Cash&with_thai=true"
            }
        },
        "integration_utilities": {
            "enhance_account_data_with_thai": {
                "description": "Utility function to enhance existing ERPNext account data with Thai names",
                "usage": "Can be called from other Python modules to add Thai translations to account queries",
                "example": "from print_designer.api.account_api import enhance_account_data_with_thai\nenhanced_data = enhance_account_data_with_thai(your_account_data)"
            }
        },
        "authentication": {
            "guest_access": "Most endpoints allow guest access",
            "api_key": "Use X-Frappe-API-Key and X-Frappe-API-Secret headers for authenticated access"
        }
    }