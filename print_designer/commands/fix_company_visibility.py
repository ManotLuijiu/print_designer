"""
Fix Company DocType field visibility issues
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


@frappe.whitelist()
def fix_company_field_visibility():
    """
    Fix Company DocType field visibility issues
    This addresses problems where signature/stamp fields exist but are not visible
    """

    print("🔧 Fixing Company DocType Field Visibility Issues")
    print("=" * 60)

    try:
        # Step 1: Clear all relevant caches
        print("1️⃣ Clearing caches...")
        frappe.clear_cache(doctype="Company")
        frappe.clear_cache()
        print("   ✅ Caches cleared")

        # Step 2: Force Company DocType reload
        print("\n2️⃣ Reloading Company DocType...")
        frappe.reload_doctype("Company")
        print("   ✅ Company DocType reloaded")

        # Step 3: Verify signature fields are properly ordered
        print("\n3️⃣ Checking field ordering...")
        meta = frappe.get_meta("Company")

        signature_fields = []
        for field in meta.fields:
            if any(
                keyword in field.fieldname.lower()
                for keyword in ["signature", "stamp", "seal"]
            ):
                signature_fields.append(
                    {
                        "fieldname": field.fieldname,
                        "label": field.label,
                        "idx": field.idx,
                        "insert_after": getattr(field, "insert_after", None),
                    }
                )

        if signature_fields:
            print(f"   ✅ Found {len(signature_fields)} signature-related fields")
            for field in sorted(signature_fields, key=lambda x: x["idx"]):
                print(
                    f"      {field['idx']}: {field['fieldname']} (after: {field['insert_after']})"
                )
        else:
            print("   ❌ No signature fields found in meta")
            return {"success": False, "error": "No signature fields found"}

        # Step 4: Add "Enable Construction Service" field if requested
        print("\n4️⃣ Adding 'Enable Construction Service' field...")

        # Check if it already exists
        existing_field = frappe.db.get_value(
            "Custom Field",
            {"dt": "Company", "fieldname": "enable_construction_service"},
            "name",
        )

        if not existing_field:
            construction_field = {
                "Company": [
                    {
                        "fieldname": "enable_construction_service",
                        "label": "Enable Construction Service",
                        "fieldtype": "Check",
                        "default": "0",
                        "insert_after": "is_group",
                        "description": "Enable construction service features for this company",
                    }
                ]
            }

            create_custom_fields(construction_field, ignore_validate=True)
            print("   ✅ 'Enable Construction Service' field added")
        else:
            print("   ℹ️  'Enable Construction Service' field already exists")

        # Step 5: Force database sync for Company
        print("\n5️⃣ Synchronizing database...")
        frappe.db.updatedb("Company")
        print("   ✅ Database synchronized")

        # Step 6: Verify fields are accessible
        print("\n6️⃣ Verifying field accessibility...")

        companies = frappe.get_all("Company", limit=1)
        if companies:
            company_doc = frappe.get_doc("Company", companies[0].name)

            test_fields = [
                "authorized_signature_1",
                "company_stamp_1",
                "enable_construction_service",
            ]
            accessibility_results = {}

            for field_name in test_fields:
                try:
                    if hasattr(company_doc, field_name):
                        value = getattr(company_doc, field_name)
                        accessibility_results[field_name] = "accessible"
                        print(f"   ✅ {field_name}: Accessible")
                    else:
                        accessibility_results[field_name] = "not_accessible"
                        print(f"   ❌ {field_name}: Not accessible")
                except Exception as e:
                    accessibility_results[field_name] = f"error: {str(e)}"
                    print(f"   ❌ {field_name}: Error - {str(e)}")

        # Step 7: Commit changes
        print("\n7️⃣ Committing changes...")
        frappe.db.commit()
        print("   ✅ Changes committed")

        # Step 8: Final cache clear
        print("\n8️⃣ Final cache clear...")
        frappe.clear_cache()
        print("   ✅ Final cache cleared")

        print("\n" + "=" * 60)
        print("🎉 Company field visibility fix completed!")
        print("\n💡 Next steps:")
        print("1. Refresh your browser completely (Ctrl+F5 or Cmd+Shift+R)")
        print("2. Navigate to Company form")
        print("3. Look for 'Stamps & Signatures' tab")
        print("4. Check for 'Enable Construction Service' field in the main details")

        return {
            "success": True,
            "signature_fields_found": len(signature_fields),
            "construction_field_added": not bool(existing_field),
            "accessibility_results": accessibility_results if companies else {},
        }

    except Exception as e:
        print(f"\n❌ Error fixing Company field visibility: {str(e)}")
        import traceback

        traceback.print_exc()

        return {"success": False, "error": str(e)}


@frappe.whitelist()
def check_company_field_issues():
    """
    Quick check for common Company field visibility issues
    """
    print("🔍 Quick Company Field Issues Check")
    print("=" * 50)

    issues_found = []
    suggestions = []

    try:
        # Check 1: Meta loading
        meta = frappe.get_meta("Company")
        if not meta:
            issues_found.append("Cannot load Company DocType meta")
            suggestions.append("Run: bench --site [site] migrate")

        # Check 2: Signature fields in meta
        signature_fields = [
            f for f in meta.fields if "signature" in f.fieldname.lower()
        ]
        if not signature_fields:
            issues_found.append("No signature fields found in Company meta")
            suggestions.append(
                "Run: bench execute print_designer.commands.fix_signature_fields.fix_current_site"
            )
        else:
            print(f"✅ Found {len(signature_fields)} signature fields in meta")

        # Check 3: Custom fields in database
        custom_fields = frappe.get_all(
            "Custom Field",
            filters={"dt": "Company", "fieldname": ["like", "%signature%"]},
            fields=["fieldname", "hidden"],
        )

        hidden_fields = [cf for cf in custom_fields if cf.hidden]
        if hidden_fields:
            issues_found.append(f"{len(hidden_fields)} signature fields are hidden")
            suggestions.append("Check field visibility settings in Customize Form")

        # Check 4: Construction service field
        construction_field = frappe.db.get_value(
            "Custom Field",
            {"dt": "Company", "fieldname": "enable_construction_service"},
            "name",
        )
        if not construction_field:
            issues_found.append("'Enable Construction Service' field is missing")
            suggestions.append(
                "Run: bench execute print_designer.commands.fix_company_visibility.fix_company_field_visibility"
            )
        else:
            print("✅ 'Enable Construction Service' field exists")

        # Check 5: Tab break field
        tab_field = meta.get_field("stamps_signatures_tab")
        if not tab_field:
            issues_found.append("'Stamps & Signatures' tab is missing from meta")
            suggestions.append(
                "Clear cache and reload: bench --site [site] clear-cache"
            )
        else:
            print("✅ 'Stamps & Signatures' tab found in meta")

        print(f"\n📊 Summary:")
        print(f"   Issues found: {len(issues_found)}")
        print(f"   Suggestions: {len(suggestions)}")

        if issues_found:
            print(f"\n❌ Issues Found:")
            for i, issue in enumerate(issues_found, 1):
                print(f"   {i}. {issue}")

            print(f"\n💡 Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
        else:
            print(f"\n✅ No obvious issues found!")
            print(f"   Try refreshing your browser and checking the Company form")

        return {
            "success": True,
            "issues_found": issues_found,
            "suggestions": suggestions,
            "signature_fields_count": len(signature_fields),
            "hidden_fields_count": len(hidden_fields)
            if "hidden_fields" in locals()
            else 0,
        }

    except Exception as e:
        print(f"❌ Error checking Company field issues: {str(e)}")
        return {"success": False, "error": str(e)}
