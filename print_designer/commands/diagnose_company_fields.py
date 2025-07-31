"""
Diagnostic tool for Company DocType field visibility issues
"""

import frappe


@frappe.whitelist()
def diagnose_company_fields():
    """Test Company form fields and provide diagnostic information"""

    print("🔍 Company DocType Field Diagnostics")
    print("=" * 60)

    # Get Company meta
    meta = frappe.get_meta("Company")

    print(f"Company DocType found with {len(meta.fields)} total fields")

    # Filter for signature/stamp related fields
    signature_related = []
    for field in meta.fields:
        field_name = field.fieldname.lower()
        field_label = (field.label or "").lower()

        if any(
            keyword in field_name or keyword in field_label
            for keyword in ["signature", "stamp", "seal", "construction"]
        ):
            signature_related.append(
                {
                    "fieldname": field.fieldname,
                    "label": field.label,
                    "fieldtype": field.fieldtype,
                    "insert_after": getattr(field, "insert_after", None),
                    "hidden": getattr(field, "hidden", 0),
                    "depends_on": getattr(field, "depends_on", None),
                    "idx": getattr(field, "idx", 0),
                }
            )

    if signature_related:
        print(
            f"\n✅ Found {len(signature_related)} signature/stamp/construction related fields:"
        )
        print("-" * 60)
        for field in sorted(signature_related, key=lambda x: x["idx"]):
            hidden_status = "HIDDEN" if field["hidden"] else "VISIBLE"
            depends_info = (
                f" (depends_on: {field['depends_on']})" if field["depends_on"] else ""
            )
            print(f"  {field['fieldname']}")
            print(f"    Label: {field['label']}")
            print(f"    Type: {field['fieldtype']}")
            print(f"    Status: {hidden_status}")
            print(f"    Insert After: {field['insert_after']}")
            print(f"    Index: {field['idx']}{depends_info}")
            print()
    else:
        print("❌ No signature/stamp/construction related fields found in Company meta")

    # Check if we can get a Company record and test field access
    companies = frappe.get_all("Company", limit=1)
    if companies:
        print(f"\n📄 Testing field access on Company: {companies[0].name}")
        print("-" * 60)

        company_doc = frappe.get_doc("Company", companies[0].name)

        # Test signature fields
        test_fields = [
            "authorized_signature_1",
            "authorized_signature_2",
            "ceo_signature",
            "company_stamp_1",
            "company_stamp_2",
            "official_seal",
        ]

        for field_name in test_fields:
            try:
                if hasattr(company_doc, field_name):
                    value = getattr(company_doc, field_name)
                    print(f"  ✅ {field_name}: Accessible (value: {value or 'None'})")
                else:
                    print(f"  ❌ {field_name}: Not accessible via doc")

                # Also check if field exists in meta
                field_meta = meta.get_field(field_name)
                if field_meta:
                    print(
                        f"      Meta: Found in DocType definition (idx: {field_meta.idx})"
                    )
                else:
                    print(f"      Meta: Not found in DocType definition")

            except Exception as e:
                print(f"  ❌ {field_name}: Error - {str(e)}")
            print()

    # Check Custom Field status
    print("\n🔧 Custom Field Status Check:")
    print("-" * 60)

    custom_fields = frappe.get_all(
        "Custom Field",
        filters={"dt": "Company"},
        fields=["fieldname", "label", "fieldtype", "hidden", "insert_after"],
    )

    signature_custom_fields = [
        cf
        for cf in custom_fields
        if any(
            keyword in cf.fieldname.lower()
            for keyword in ["signature", "stamp", "seal", "construction"]
        )
    ]

    if signature_custom_fields:
        for cf in signature_custom_fields:
            hidden_status = "HIDDEN" if cf.hidden else "VISIBLE"
            print(f"  Custom Field: {cf.fieldname} ({cf.label})")
            print(f"    Type: {cf.fieldtype}, Status: {hidden_status}")
            print(f"    Insert After: {cf.insert_after}")
            print()
    else:
        print("  No signature/stamp custom fields found")

    # Check the "Stamps & Signatures" tab specifically
    print("\n📑 Tab Structure Analysis:")
    print("-" * 60)

    tab_field = meta.get_field("stamps_signatures_tab")
    if tab_field:
        print(f"  ✅ 'Stamps & Signatures' tab found at index {tab_field.idx}")
        print(f"      Insert After: {tab_field.insert_after}")
        print(f"      Hidden: {getattr(tab_field, 'hidden', 0)}")

        # Find fields that come after this tab
        tab_idx = tab_field.idx
        fields_after_tab = [
            f for f in meta.fields if f.idx > tab_idx and f.idx <= tab_idx + 20
        ]

        print(f"  Fields immediately after tab (next 20 positions):")
        for field in fields_after_tab:
            print(
                f"    {field.idx}: {field.fieldname} ({field.label}) - {field.fieldtype}"
            )

    else:
        print("  ❌ 'Stamps & Signatures' tab not found")

    # Check if there are any permission issues
    print("\n🔐 Permission Check:")
    print("-" * 60)

    try:
        # Try to access Company form
        if frappe.has_permission("Company", "read"):
            print("  ✅ User has read permission for Company DocType")
        else:
            print("  ❌ User lacks read permission for Company DocType")

        if frappe.has_permission("Company", "write"):
            print("  ✅ User has write permission for Company DocType")
        else:
            print("  ⚠️  User lacks write permission for Company DocType")

    except Exception as e:
        print(f"  ❌ Error checking permissions: {str(e)}")

    # Check for "Enable Construction Service" specifically
    print("\n🏗️  Construction Service Field Analysis:")
    print("-" * 60)

    construction_fields = []
    for field in meta.fields:
        if (
            "construction" in field.fieldname.lower()
            or "construction" in (field.label or "").lower()
        ):
            construction_fields.append(field)

    if construction_fields:
        print(f"  ✅ Found {len(construction_fields)} construction-related fields:")
        for field in construction_fields:
            print(f"    {field.fieldname} ({field.label}) - {field.fieldtype}")
    else:
        print("  ❌ No 'Enable Construction Service' or similar fields found")
        print("  💡 This field may need to be added as a custom field or")
        print("     may be part of a different ERPNext module/domain")

    print("\n" + "=" * 60)
    print("🎯 CONCLUSIONS:")
    print("-" * 60)

    if signature_related:
        print(
            f"✅ Signature/Stamp system appears to be installed ({len(signature_related)} fields found)"
        )
        if tab_field:
            print("✅ 'Stamps & Signatures' tab is present in the form")
        else:
            print(
                "❌ 'Stamps & Signatures' tab is missing - this may cause visibility issues"
            )
    else:
        print(
            "❌ Signature/Stamp system appears to be missing or not properly installed"
        )

    if not construction_fields:
        print("⚠️  'Enable Construction Service' field is not present")
        print("   This may be a domain-specific field or requires manual addition")

    print("\n💡 RECOMMENDATIONS:")
    print("-" * 60)
    if not tab_field:
        print(
            "1. Clear DocType cache: bench --site [site] clear-cache --doctype Company"
        )
        print(
            "2. Run signature fields fix: bench execute print_designer.commands.fix_signature_fields.fix_current_site"
        )

    if not construction_fields:
        print(
            "3. Consider adding 'Enable Construction Service' as a custom field if needed"
        )
        print(
            "4. Check if this is part of an ERPNext domain or industry-specific module"
        )

    print("5. Refresh the browser and check the Company form again")

    print("\nDiagnostic complete!")

    return {
        "signature_fields_found": len(signature_related),
        "custom_fields_found": len(signature_custom_fields),
        "tab_found": tab_field is not None,
        "construction_fields_found": len(construction_fields),
        "total_company_fields": len(meta.fields),
    }
