"""
Account Translation API

Integrates with translation_tools to provide Account Name translation functionality.
Follows the same patterns as translation_tools/api/glossary.py for consistency.
"""

import json
import frappe
from frappe import _
from frappe.utils import cint, now_datetime

# Import logging from translation_tools if available
try:
    from translation_tools.api.common import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@frappe.whitelist()
def sync_account_glossary_from_file():
    """Load account glossary from file and update the Translation Glossary Term database"""
    logger.info("Start sync account glossary process")

    try:
        # Import the account glossary from file
        from print_designer.utils.account_glossary import ACCOUNT_GLOSSARY, ACCOUNT_GLOSSARY_METADATA

        # Get existing terms from database
        existing_terms = frappe.get_all(
            "Translation Glossary Term",
            filters={"category": "Account Names"},
            fields=["name", "source_term"],
            as_list=False
        )

        logger.debug(f"Existing account terms: {len(existing_terms)}")

        # Convert to a dictionary for easier lookup
        existing_terms_dict = {term.source_term: term.name for term in existing_terms}

        # Statistics for report
        stats = {"added": 0, "exists": 0, "errors": 0}

        # Process each term in the account glossary file
        for source_term, thai_translation in ACCOUNT_GLOSSARY.items():
            try:
                # Skip if term already exists
                if source_term in existing_terms_dict:
                    stats["exists"] += 1
                    continue

                # Add new account term
                doc = frappe.new_doc("Translation Glossary Term")
                doc.source_term = source_term
                doc.thai_translation = thai_translation
                doc.category = ACCOUNT_GLOSSARY_METADATA["category"]
                doc.module = ACCOUNT_GLOSSARY_METADATA["module"]
                doc.context = ACCOUNT_GLOSSARY_METADATA["context"]
                doc.is_approved = 1  # Auto-approve account translations
                doc.insert()
                stats["added"] += 1

            except Exception as e:
                logger.error(f"Error adding account term {source_term}: {str(e)}")
                stats["errors"] += 1

        frappe.db.commit()

        # Log the stats
        logger.info(
            f"Account glossary sync complete: {stats['added']} terms added, "
            f"{stats['exists']} already exist, {stats['errors']} errors"
        )

        return {
            "success": True,
            "message": f"Account glossary sync complete: {stats['added']} terms added, {stats['exists']} already exist, {stats['errors']} errors",
            "stats": stats
        }

    except ImportError:
        logger.error("Could not import ACCOUNT_GLOSSARY from account_glossary.py file")
        return {
            "success": False,
            "message": "Could not import account glossary file"
        }
    except Exception as e:
        logger.error(f"Error syncing account glossary: {str(e)}")
        return {
            "success": False,
            "message": f"Error syncing account glossary: {str(e)}"
        }


@frappe.whitelist()
def get_account_glossary_terms():
    """Get all account glossary terms"""
    logger.info("Start get_account_glossary_terms")
    return frappe.get_all(
        "Translation Glossary Term",
        filters={"category": "Account Names"},
        fields=[
            "name",
            "source_term",
            "thai_translation",
            "context",
            "category",
            "module",
            "is_approved",
        ],
        order_by="source_term",
    )


def get_account_glossary_dict():
    """Get account glossary terms as a dictionary for translation lookup"""
    try:
        terms = get_account_glossary_terms()
        return {
            term.source_term: term.thai_translation
            for term in terms if term.is_approved
        }
    except Exception as e:
        logger.warning(f"Failed to fetch account glossary terms: {e}")
        return {}


@frappe.whitelist()
def push_account_glossary_to_github():
    """
    Push account glossary terms from database to GitHub repository as JSON file
    Creates account_names_glossary.json in the same repository as main glossary
    """
    import requests
    import base64
    import tempfile
    import os

    try:
        logger.info("Starting push account glossary to GitHub")

        # Import GitHub settings function from translation_tools
        try:
            from translation_tools.api.settings import get_github_token
        except ImportError:
            return {
                "github_pushed": False,
                "message": "translation_tools not available for GitHub integration"
            }

        # Use the same repository as main glossary
        github_repo = "https://github.com/ManotLuijiu/erpnext-thai-translation.git"

        # Get GitHub settings
        try:
            settings = frappe.get_single("Translation Tools Settings")
            if not settings.github_enable:
                return {
                    "github_pushed": False,
                    "message": "GitHub integration is disabled"
                }
        except:
            return {
                "github_pushed": False,
                "message": "Translation Tools Settings not found"
            }

        github_token = get_github_token()
        if not github_token:
            return {
                "github_pushed": False,
                "message": "GitHub token not configured"
            }

        # Parse repository URL
        repo_path = github_repo.replace("https://github.com/", "").replace(".git", "")
        owner, repo = repo_path.split("/")
        file_path = "glossary/account_names_glossary.json"

        # Get account glossary terms from database
        terms = frappe.get_all(
            "Translation Glossary Term",
            filters={"category": "Account Names"},
            fields=["source_term", "thai_translation", "context", "category", "module", "is_approved"],
            order_by="source_term"
        )

        logger.info(f"Found {len(terms)} account terms in database")

        # Create JSON structure
        glossary_data = {
            "version": "1.0",
            "language": "th",
            "category": "Account Names",
            "terms_count": len(terms),
            "last_updated": now_datetime().isoformat(),
            "description": "Thai translations for ERPNext Chart of Accounts",
            "terms": {}
        }

        # Add all account terms to JSON
        for term in terms:
            glossary_data["terms"][term.source_term] = {
                "translation": term.thai_translation,
                "context": term.context or "",
                "category": term.category or "Account Names",
                "module": term.module or "",
                "is_approved": term.is_approved
            }

        # Create temporary file with JSON content
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "account_names_glossary.json")

        try:
            # Write JSON to temp file
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(glossary_data, f, ensure_ascii=False, indent=2)

            # Read the file content for GitHub upload
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # GitHub API headers
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }

            # Get current file SHA if it exists
            get_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            get_response = requests.get(get_url, headers=headers)

            commit_data = {
                "message": f"Update account names glossary - {len(terms)} terms",
                "content": base64.b64encode(file_content.encode('utf-8')).decode('utf-8'),
                "branch": "main"
            }

            if get_response.status_code == 200:
                # File exists, need to update it
                current_file = get_response.json()
                commit_data["sha"] = current_file["sha"]
                logger.info(f"Updating existing file {file_path}")
            else:
                # File doesn't exist, create new one
                logger.info(f"Creating new file {file_path}")

            # Push to GitHub
            put_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            response = requests.put(put_url, headers=headers, json=commit_data)

            if response.status_code in [200, 201]:
                logger.info(f"Successfully pushed account glossary to GitHub: {len(terms)} terms")
                return {
                    "github_pushed": True,
                    "message": f"Successfully pushed {len(terms)} account terms to GitHub",
                    "terms_count": len(terms),
                    "file_path": file_path,
                    "commit_url": response.json().get("commit", {}).get("html_url", "")
                }
            else:
                error_msg = f"Failed to push to GitHub: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "github_pushed": False,
                    "message": error_msg
                }

        finally:
            # Clean up temp files
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)

    except Exception as e:
        error_msg = f"Error pushing account glossary to GitHub: {str(e)}"
        logger.error(error_msg)
        return {
            "github_pushed": False,
            "message": error_msg
        }


@frappe.whitelist()
def auto_translate_company_accounts(company):
    """Auto-translate all accounts for a specific company using GitHub glossary"""
    try:
        # First try to get translations from database
        account_translations = get_account_glossary_dict()

        # If no local translations, try to fetch from GitHub
        if not account_translations:
            github_translations = fetch_account_glossary_from_github()
            if github_translations:
                account_translations = github_translations

        if not account_translations:
            return {
                "success": False,
                "message": "No account translations available. Please sync glossary first."
            }

        # Get accounts for this company
        accounts = frappe.get_all("Account",
            filters={"company": company},
            fields=["name", "account_name", "account_name_th"]
        )

        accounts_updated = 0

        # Update accounts with Thai translations
        for account in accounts:
            thai_translation = account_translations.get(account.account_name)
            if thai_translation and not account.account_name_th:
                frappe.db.set_value("Account", account.name, {
                    "account_name_th": thai_translation,
                    "auto_translate_thai": 1
                })
                accounts_updated += 1

        frappe.db.commit()

        return {
            "success": True,
            "message": f"Successfully updated Thai names for {accounts_updated} accounts",
            "accounts_updated": accounts_updated,
            "total_accounts": len(accounts)
        }

    except Exception as e:
        error_msg = f"Error auto-translating accounts: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg
        }


def fetch_account_glossary_from_github():
    """Fetch account glossary from GitHub JSON file"""
    import requests

    try:
        # Fetch from GitHub raw content
        url = "https://raw.githubusercontent.com/ManotLuijiu/erpnext-thai-translation/main/glossary/account_names_glossary.json"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            # Extract translations from JSON structure
            return {
                term: details["translation"]
                for term, details in data.get("terms", {}).items()
                if details.get("is_approved", False)
            }
        else:
            logger.warning(f"Failed to fetch account glossary from GitHub: {response.status_code}")
            return {}

    except Exception as e:
        logger.warning(f"Error fetching account glossary from GitHub: {str(e)}")
        return {}


@frappe.whitelist()
def get_account_translation_stats(company=None):
    """Get statistics about account translation coverage"""
    try:
        filters = {}
        if company:
            filters["company"] = company

        # Get total accounts
        total_accounts = frappe.db.count("Account", filters)

        # Get accounts with Thai translations
        filters["account_name_th"] = ["!=", ""]
        translated_accounts = frappe.db.count("Account", filters)

        # Get auto-translated accounts
        filters["auto_translate_thai"] = 1
        auto_translated = frappe.db.count("Account", filters)

        coverage_percentage = (translated_accounts / total_accounts * 100) if total_accounts > 0 else 0

        return {
            "success": True,
            "total_accounts": total_accounts,
            "translated_accounts": translated_accounts,
            "auto_translated": auto_translated,
            "coverage_percentage": round(coverage_percentage, 2),
            "untranslated_accounts": total_accounts - translated_accounts
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting translation stats: {str(e)}"
        }