"""
Apply Account Thai Translations - Direct Field Update

Simple utility to populate account_name_th field with translations from account_glossary.py
This is a direct approach for static Account data that doesn't change frequently.
"""

import frappe
from frappe import _


def execute():
    """Main entry point for bench command"""
    apply_account_thai_translations()


def apply_account_thai_translations(company=None, force_update=False):
    """Apply Thai translations to Account.account_name_th field"""

    print("🔄 Applying Account Thai Translations...")

    try:
        # Import translations from our glossary
        from print_designer.utils.account_glossary import ACCOUNT_GLOSSARY

        # Build filters
        filters = {}
        if company:
            filters["company"] = company

        # Get all accounts
        accounts = frappe.get_all("Account",
            filters=filters,
            fields=["name", "account_name", "account_name_th", "company"]
        )

        print(f"📊 Found {len(accounts)} accounts to process")
        if company:
            print(f"🏢 Company filter: {company}")

        # Statistics
        stats = {
            "processed": 0,
            "updated": 0,
            "already_translated": 0,
            "no_translation_found": 0,
            "errors": 0
        }

        # Process each account
        for account in accounts:
            stats["processed"] += 1

            try:
                # Check if translation exists
                thai_translation = ACCOUNT_GLOSSARY.get(account.account_name)

                if not thai_translation:
                    stats["no_translation_found"] += 1
                    continue

                # Check if already translated (unless force update)
                if account.account_name_th and not force_update:
                    stats["already_translated"] += 1
                    continue

                # Update the field
                frappe.db.set_value("Account", account.name, {
                    "account_name_th": thai_translation,
                    "auto_translate_thai": 1
                })

                print(f"✅ TRANSLATED: {account.account_name} → {thai_translation}")
                stats["updated"] += 1

            except Exception as e:
                print(f"❌ Error processing {account.account_name}: {str(e)}")
                stats["errors"] += 1

        # Commit changes
        frappe.db.commit()
        print(f"💾 Database changes committed successfully")

        # Print detailed summary
        print("\n" + "="*70)
        print("📈 ACCOUNT THAI TRANSLATION SUMMARY")
        print("="*70)
        print(f"📊 Total accounts processed: {stats['processed']}")
        print(f"✅ Successfully translated: {stats['updated']} accounts")
        print(f"⏭️  Already had translations: {stats['already_translated']}")
        print(f"⚠️  No translation available: {stats['no_translation_found']}")
        print(f"❌ Processing errors: {stats['errors']}")
        print("-" * 70)

        # Calculate rates
        success_rate = (stats['updated'] / stats['processed'] * 100) if stats['processed'] > 0 else 0
        coverage_rate = ((stats['updated'] + stats['already_translated']) / stats['processed'] * 100) if stats['processed'] > 0 else 0

        print(f"📈 New translations rate: {success_rate:.1f}%")
        print(f"🎯 Total coverage rate: {coverage_rate:.1f}%")

        # Show actual count of newly translated accounts
        if stats['updated'] > 0:
            print(f"🎉 NEW TRANSLATIONS: {stats['updated']} account names now have Thai translations!")
        else:
            print("✨ All accounts already had Thai translations - no new updates needed")

        print("="*70)

        return {
            "success": True,
            "message": f"Successfully updated {stats['updated']} accounts",
            "stats": stats
        }

    except ImportError:
        error_msg = "Could not import ACCOUNT_GLOSSARY from account_glossary.py"
        print(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}

    except Exception as e:
        error_msg = f"Error applying account translations: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg)
        return {"success": False, "message": error_msg}


def get_translation_stats(company=None):
    """Get current translation coverage statistics"""

    try:
        print("📊 Checking Account Translation Coverage...")

        # Build filters
        filters = {}
        if company:
            filters["company"] = company

        # Get total accounts
        total_accounts = frappe.db.count("Account", filters)

        # Get translated accounts
        translated_filters = filters.copy()
        translated_filters["account_name_th"] = ["!=", ""]
        translated_accounts = frappe.db.count("Account", translated_filters)

        # Get auto-translated accounts
        auto_translated_filters = filters.copy()
        auto_translated_filters["auto_translate_thai"] = 1
        auto_translated = frappe.db.count("Account", auto_translated_filters)

        # Calculate coverage
        coverage_percentage = (translated_accounts / total_accounts * 100) if total_accounts > 0 else 0

        # Print results
        print(f"🏢 Company: {company or 'All Companies'}")
        print(f"📊 Total accounts: {total_accounts}")
        print(f"✅ Translated accounts: {translated_accounts}")
        print(f"🤖 Auto-translated accounts: {auto_translated}")
        print(f"📈 Coverage: {coverage_percentage:.1f}%")
        print(f"⏳ Remaining: {total_accounts - translated_accounts}")

        return {
            "success": True,
            "total_accounts": total_accounts,
            "translated_accounts": translated_accounts,
            "auto_translated": auto_translated,
            "coverage_percentage": round(coverage_percentage, 2),
            "remaining": total_accounts - translated_accounts
        }

    except Exception as e:
        error_msg = f"Error getting translation stats: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}


@frappe.whitelist()
def apply_translations_for_company(company, force_update=False):
    """API method to apply translations for specific company"""
    return apply_account_thai_translations(company=company, force_update=force_update)


@frappe.whitelist()
def get_coverage_stats(company=None):
    """API method to get translation coverage statistics"""
    return get_translation_stats(company=company)


def check_glossary_coverage():
    """Check if our glossary covers all accounts in database"""

    try:
        from print_designer.utils.account_glossary import ACCOUNT_GLOSSARY

        print("🔍 Checking Glossary Coverage...")

        # Get unique account names from database
        account_names = frappe.db.sql("""
            SELECT DISTINCT account_name
            FROM `tabAccount`
            ORDER BY account_name
        """, as_list=True)

        account_names = [name[0] for name in account_names]

        print(f"📊 Database has {len(account_names)} unique account names")
        print(f"📚 Glossary has {len(ACCOUNT_GLOSSARY)} translations")

        # Check coverage
        missing_translations = []
        for account_name in account_names:
            if account_name not in ACCOUNT_GLOSSARY:
                missing_translations.append(account_name)

        coverage_percentage = ((len(account_names) - len(missing_translations)) / len(account_names) * 100) if account_names else 0

        print(f"📈 Glossary Coverage: {coverage_percentage:.1f}%")

        if missing_translations:
            print(f"\n⚠️  Missing translations ({len(missing_translations)}):")
            for account in missing_translations:
                print(f"   - {account}")
        else:
            print("🎉 Perfect coverage! All accounts have translations.")

        return {
            "success": True,
            "total_accounts": len(account_names),
            "glossary_size": len(ACCOUNT_GLOSSARY),
            "coverage_percentage": round(coverage_percentage, 2),
            "missing_translations": missing_translations
        }

    except Exception as e:
        error_msg = f"Error checking glossary coverage: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}