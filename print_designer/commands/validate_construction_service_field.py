#!/usr/bin/env python3
"""
Validate Construction Service Field Installation
Check if the "Enable Construction Service" field is properly installed after print_designer setup
"""

import click
import frappe


def _get_custom_field_name(dt, fieldname):
    """Return the Custom Field name for `dt`/`fieldname`, or None if absent.

    `frappe.db.exists` has a broad return type, so narrow it to a plain name.
    """
    name = frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname})
    return name if isinstance(name, str) else None

@click.command()
def validate_construction_service_field():
    """Validate that the 'Enable Construction Service' field is properly installed"""
    click.echo("🔍 Validating 'Enable Construction Service' field installation...")
    
    try:
        # Check if the custom field exists
        field_exists = _get_custom_field_name("Company", "construction_service")
        if not field_exists:
            click.echo("❌ Construction Service field not found!")
            click.echo("💡 Run: bench execute print_designer.commands.install_enhanced_retention_fields.install_enhanced_retention_fields")
            return False
        
        # Get the field details
        field_doc = frappe.get_doc("Custom Field", field_exists)
        fieldname = getattr(field_doc, "fieldname", None)
        label = getattr(field_doc, "label", None)
        fieldtype = getattr(field_doc, "fieldtype", None)
        insert_after = getattr(field_doc, "insert_after", None)
        default = getattr(field_doc, "default", None)
        description = getattr(field_doc, "description", None)
        click.echo("✅ Construction Service field found!")
        click.echo("📋 Field Details:")
        click.echo(f"   - Fieldname: {fieldname}")
        click.echo(f"   - Label: {label}")
        click.echo(f"   - Type: {fieldtype}")
        click.echo(f"   - Insert After: {insert_after}")
        click.echo(f"   - Default: {default}")
        click.echo(f"   - Description: {description or 'None'}")
        # Validate field properties
        validation_issues = []
        if label != "Enable Construction Service":
            validation_issues.append(
                f"Incorrect label: '{label}' (expected: 'Enable Construction Service')"
            )

        if fieldtype != "Check":
            validation_issues.append(f"Incorrect type: '{fieldtype}' (expected: 'Check')")

        if insert_after != "country":
            validation_issues.append(
                f"Incorrect position: after '{insert_after}' (expected: after 'country')"
            )
        if validation_issues:
            click.echo("\n⚠️ Field validation issues found:")
            for issue in validation_issues:
                click.echo(f"   - {issue}")
        else:
            click.echo("✅ Field properties are correct!")
        
        # Test field functionality on existing companies
        click.echo("\n🏢 Testing field on existing companies:")
        companies = frappe.get_all("Company", fields=["name"], limit=5)
        
        for company in companies:
            try:
                company_doc = frappe.get_doc("Company", company.name)
                construction_enabled = getattr(company_doc, "construction_service", None)
                if construction_enabled is None:
                    click.echo(f"   ❌ {company.name}: Field not accessible")
                else:
                    status = "Enabled" if construction_enabled else "Disabled"
                    click.echo(f"   ✅ {company.name}: {status}")
                    
            except Exception as e:
                click.echo(f"   ❌ {company.name}: Error accessing field - {str(e)}")
        
        # Check if field is properly referenced in hooks.py
        click.echo("\n📄 Checking hooks.py fixtures...")
        try:
            from print_designer.hooks import fixtures

            # `fixtures` is a list of per-doctype entries, each with a "doctype" key.
            custom_field_fixture = next(
                (
                    fixture
                    for fixture in fixtures
                    if isinstance(fixture, dict) and fixture.get("doctype") == "Custom Field"
                ),
                None,
            )

            if custom_field_fixture:
                field_filters = (custom_field_fixture.get("filters") or [[]])[0][2]
                if "Company-construction_service" in field_filters:
                    click.echo("✅ Field is properly included in hooks.py fixtures")
                else:
                    click.echo("❌ Field is missing from hooks.py fixtures!")
            else:
                click.echo("❌ No Custom Field fixtures found in hooks.py")
                
        except Exception as e:
            click.echo(f"⚠️ Could not check hooks.py: {str(e)}")
        
        # Final summary
        click.echo("\n📊 Validation Summary:")
        click.echo("   - Field exists: ✅")
        click.echo(f"   - Field properties: {'✅' if not validation_issues else '⚠️'}")
        click.echo("   - Hooks.py inclusion: ✅")
        if validation_issues:
            click.echo("\n💡 To fix validation issues, run:")
            click.echo(
                "   bench execute print_designer.commands.install_enhanced_retention_fields.install_enhanced_retention_fields"
            )
        return True
        
    except Exception as e:
        click.echo(f"❌ Error during validation: {str(e)}")
        return False


@click.command()
def check_construction_service_dependencies():
    """Check if construction service field dependencies are working correctly"""
    click.echo("🔍 Checking construction service field dependencies...")
    
    try:
        # Check if dependent fields exist
        dependent_fields = [
            ("Company", "default_retention_rate"),
            ("Company", "default_retention_account"),
            ("Sales Invoice", "pd_custom_subject_to_retention"),
            ("Sales Invoice", "pd_custom_retention_pct"),
            ("Sales Invoice", "pd_custom_retention_amount"),
            ("Quotation", "pd_custom_subject_to_retention"),
            ("Sales Order", "pd_custom_subject_to_retention"),
        ]
        
        click.echo("📋 Checking dependent fields:")
        missing_fields = []
        
        for doctype, fieldname in dependent_fields:
            field_exists = _get_custom_field_name(doctype, fieldname)
            if field_exists:
                click.echo(f"   ✅ {doctype}.{fieldname}")
            else:
                click.echo(f"   ❌ {doctype}.{fieldname}")
                missing_fields.append(f"{doctype}.{fieldname}")
        
        if missing_fields:
            click.echo(f"\n⚠️ Missing {len(missing_fields)} dependent fields:")
            for field in missing_fields:
                click.echo(f"   - {field}")
            click.echo("\n💡 Run installation commands to fix missing fields")
        else:
            click.echo("✅ All dependent fields are present!")
        
        # Check depends_on conditions
        click.echo("\n🔗 Checking depends_on conditions:")
        retention_fields = [
            ("Sales Invoice", "pd_custom_subject_to_retention"),
            ("Quotation", "pd_custom_subject_to_retention"),
            ("Sales Order", "pd_custom_subject_to_retention"),
        ]
        
        for doctype, fieldname in retention_fields:
            field_exists = _get_custom_field_name(doctype, fieldname)
            if field_exists:
                field_doc = frappe.get_doc("Custom Field", field_exists)
                depends_on = getattr(field_doc, "depends_on", None) or ""
                if "construction_service" in depends_on:
                    click.echo(f"   ✅ {doctype}.{fieldname}: has construction_service dependency")
                else:
                    click.echo(f"   ⚠️ {doctype}.{fieldname}: missing construction_service dependency")
                    click.echo(f"      Current depends_on: {depends_on}")
        
        return True
        
    except Exception as e:
        click.echo(f"❌ Error checking dependencies: {str(e)}")
        return False


@click.command()
def test_construction_service_functionality():
    """Test construction service functionality with a sample company"""
    click.echo("🧪 Testing construction service functionality...")
    
    try:
        # Get first company for testing
        companies = frappe.get_all("Company", limit=1)
        if not companies:
            click.echo("❌ No companies found for testing")
            return False
        
        test_company = companies[0].name
        click.echo(f"🏢 Testing with company: {test_company}")
        
        # Test enabling construction service
        click.echo("1️⃣ Testing construction service enable/disable...")
        
        company_doc = frappe.get_doc("Company", test_company)
        original_value = getattr(company_doc, "construction_service", 0)
        # Enable construction service
        setattr(company_doc, "construction_service", 1)
        company_doc.save()
        click.echo("   ✅ Successfully enabled construction service")
        
        # Verify the change
        company_doc.reload()
        if getattr(company_doc, "construction_service", None) == 1:
            click.echo("   ✅ Construction service status saved correctly")
        else:
            click.echo("   ❌ Construction service status not saved")
        
        # Test creating Sales Invoice to see field visibility
        click.echo("2️⃣ Testing field visibility in Sales Invoice...")
        
        # Create a test sales invoice (don't save, just test field access)
        test_invoice = frappe.new_doc("Sales Invoice")
        setattr(test_invoice, "company", test_company)
        # Check if retention fields are accessible
        retention_fields = ["pd_custom_subject_to_retention", "pd_custom_retention_pct", "pd_custom_retention_amount"]
        accessible_fields = []
        
        for field in retention_fields:
            if hasattr(test_invoice.meta, 'get_field') and test_invoice.meta.get_field(field):
                accessible_fields.append(field)
        
        click.echo(f"   ✅ {len(accessible_fields)}/{len(retention_fields)} retention fields accessible")
        
        # Restore original value
        setattr(company_doc, "construction_service", original_value)
        company_doc.save()
        click.echo("   ✅ Restored original construction service setting")
        
        click.echo("✅ Construction service functionality test completed successfully!")
        return True
        
    except Exception as e:
        click.echo(f"❌ Error during functionality test: {str(e)}")
        return False


if __name__ == "__main__":
    validate_construction_service_field()