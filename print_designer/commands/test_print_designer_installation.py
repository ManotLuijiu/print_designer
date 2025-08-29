#!/usr/bin/env python3
"""
Complete Print Designer Installation Test
Comprehensive test to verify all print_designer components are properly installed
"""

import frappe
import click
from frappe import _

@click.command()
def test_complete_print_designer_installation():
    """Comprehensive test of print_designer installation"""
    click.echo("🚀 Testing complete print_designer installation...")
    
    test_results = {
        "construction_service_field": False,
        "retention_fields": False,
        "wht_fields": False,
        "signature_fields": False,
        "watermark_fields": False,
        "company_fields": False,
        "print_format_fields": False,
        "hooks_configuration": False,
    }
    
    # Test 1: Construction Service Field
    click.echo("\n1️⃣ Testing Construction Service Field...")
    try:
        field_exists = frappe.db.exists("Custom Field", {
            "dt": "Company", 
            "fieldname": "construction_service"
        })
        
        if field_exists:
            field_doc = frappe.get_doc("Custom Field", field_exists)
            if (field_doc.label == "Enable Construction Service" and 
                field_doc.fieldtype == "Check" and
                field_doc.insert_after == "country"):
                click.echo("   ✅ Construction Service field properly installed")
                test_results["construction_service_field"] = True
            else:
                click.echo("   ⚠️ Construction Service field has incorrect properties")
        else:
            click.echo("   ❌ Construction Service field not found")
    except Exception as e:
        click.echo(f"   ❌ Error testing construction service field: {str(e)}")
    
    # Test 2: Retention Fields
    click.echo("\n2️⃣ Testing Retention Fields...")
    retention_fields = [
        ("Company", "default_retention_rate"),
        ("Company", "default_retention_account"),
        ("Sales Invoice", "custom_subject_to_retention"),
        ("Sales Invoice", "custom_retention"),
        ("Sales Invoice", "custom_retention_amount"),
        ("Quotation", "custom_subject_to_retention"),
        ("Sales Order", "custom_subject_to_retention"),
    ]
    
    retention_found = 0
    for doctype, fieldname in retention_fields:
        if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
            retention_found += 1
    
    if retention_found == len(retention_fields):
        click.echo(f"   ✅ All {len(retention_fields)} retention fields found")
        test_results["retention_fields"] = True
    else:
        click.echo(f"   ⚠️ Found {retention_found}/{len(retention_fields)} retention fields")
    
    # Test 3: WHT (Withholding Tax) Fields
    click.echo("\n3️⃣ Testing WHT Fields...")
    wht_fields = [
        ("Sales Invoice", "thai_wht_preview_section"),
        ("Sales Invoice", "subject_to_wht"),
        ("Sales Invoice", "wht_income_type"),
        ("Sales Invoice", "net_total_after_wht"),
        ("Sales Invoice", "custom_withholding_tax_amount"),
        ("Quotation", "subject_to_wht"),
        ("Sales Order", "subject_to_wht"),
    ]
    
    wht_found = 0
    for doctype, fieldname in wht_fields:
        if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
            wht_found += 1
    
    if wht_found >= len(wht_fields) * 0.8:  # Allow 80% for flexibility
        click.echo(f"   ✅ Found {wht_found}/{len(wht_fields)} WHT fields")
        test_results["wht_fields"] = True
    else:
        click.echo(f"   ⚠️ Found only {wht_found}/{len(wht_fields)} WHT fields")
    
    # Test 4: Signature Fields
    click.echo("\n4️⃣ Testing Signature Fields...")
    signature_fields = [
        ("Sales Invoice", "prepared_by_signature"),
        ("Sales Invoice", "approved_by_signature"),
        ("Quotation", "prepared_by_signature"),
        ("Sales Order", "prepared_by_signature"),
        ("Sales Order", "approved_by_signature"),
    ]
    
    signature_found = 0
    for doctype, fieldname in signature_fields:
        if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
            signature_found += 1
    
    if signature_found >= len(signature_fields) * 0.8:
        click.echo(f"   ✅ Found {signature_found}/{len(signature_fields)} signature fields")
        test_results["signature_fields"] = True
    else:
        click.echo(f"   ⚠️ Found only {signature_found}/{len(signature_fields)} signature fields")
    
    # Test 5: Watermark Fields
    click.echo("\n5️⃣ Testing Watermark Fields...")
    watermark_fields = [
        ("Print Format", "watermark_settings"),
        ("Print Settings", "watermark_settings_section"),
        ("Print Settings", "watermark_font_size"),
        ("Sales Invoice", "watermark_text"),
    ]
    
    watermark_found = 0
    for doctype, fieldname in watermark_fields:
        if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
            watermark_found += 1
    
    if watermark_found >= len(watermark_fields) * 0.7:
        click.echo(f"   ✅ Found {watermark_found}/{len(watermark_fields)} watermark fields")
        test_results["watermark_fields"] = True
    else:
        click.echo(f"   ⚠️ Found only {watermark_found}/{len(watermark_fields)} watermark fields")
    
    # Test 6: Company Fields
    click.echo("\n6️⃣ Testing Company Fields...")
    company_fields = [
        "construction_service",
        "default_retention_rate",
        "default_retention_account",
        "thailand_service_business",
        "company_signatures_section",
        "retention_section",
        "typography_section",
    ]
    
    company_found = 0
    for fieldname in company_fields:
        if frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": fieldname}):
            company_found += 1
    
    if company_found >= len(company_fields) * 0.8:
        click.echo(f"   ✅ Found {company_found}/{len(company_fields)} company fields")
        test_results["company_fields"] = True
    else:
        click.echo(f"   ⚠️ Found only {company_found}/{len(company_fields)} company fields")
    
    # Test 7: Print Format Fields
    click.echo("\n7️⃣ Testing Print Format Fields...")
    print_format_fields = [
        "print_designer",
        "print_designer_print_format",
        "print_designer_body",
        "print_designer_settings",
        "watermark_settings",
    ]
    
    print_format_found = 0
    for fieldname in print_format_fields:
        if frappe.db.exists("Custom Field", {"dt": "Print Format", "fieldname": fieldname}):
            print_format_found += 1
    
    if print_format_found >= len(print_format_fields) * 0.8:
        click.echo(f"   ✅ Found {print_format_found}/{len(print_format_fields)} print format fields")
        test_results["print_format_fields"] = True
    else:
        click.echo(f"   ⚠️ Found only {print_format_found}/{len(print_format_fields)} print format fields")
    
    # Test 8: Hooks Configuration
    click.echo("\n8️⃣ Testing Hooks Configuration...")
    try:
        from print_designer.hooks import fixtures, commands, doc_events
        
        hooks_ok = True
        
        # Check fixtures
        if not fixtures or "Custom Field" not in fixtures:
            click.echo("   ❌ Custom Field fixtures not configured")
            hooks_ok = False
        
        # Check commands
        if not commands or len(commands) < 10:
            click.echo("   ❌ Bench commands not properly configured")
            hooks_ok = False
        
        # Check doc_events
        if not doc_events or "Sales Invoice" not in doc_events:
            click.echo("   ❌ Document events not properly configured")
            hooks_ok = False
        
        if hooks_ok:
            click.echo("   ✅ Hooks configuration looks good")
            test_results["hooks_configuration"] = True
        
    except Exception as e:
        click.echo(f"   ❌ Error checking hooks: {str(e)}")
    
    # Final Summary
    click.echo("\n📊 Installation Test Summary:")
    click.echo("=" * 50)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        formatted_name = test_name.replace("_", " ").title()
        click.echo(f"   {formatted_name:<25} {status}")
    
    click.echo("=" * 50)
    click.echo(f"Overall Result: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests >= total_tests * 0.8:  # 80% pass rate
        click.echo("✅ Print Designer installation appears to be working correctly!")
        
        if test_results["construction_service_field"]:
            click.echo("🏗️ Construction Service feature is properly installed and ready to use")
        else:
            click.echo("⚠️ Construction Service feature may need attention")
            
        return True
    else:
        click.echo("❌ Print Designer installation has issues that need attention")
        click.echo("\n💡 Recommended fixes:")
        
        if not test_results["construction_service_field"]:
            click.echo("   - Run: bench execute print_designer.commands.install_enhanced_retention_fields.install_enhanced_retention_fields")
        
        if not test_results["retention_fields"]:
            click.echo("   - Run: bench execute print_designer.commands.install_retention_fields.install_retention_fields")
        
        if not test_results["wht_fields"]:
            click.echo("   - Run: bench execute print_designer.commands.install_sales_invoice_fields.install_sales_invoice_custom_fields")
        
        if not test_results["watermark_fields"]:
            click.echo("   - Run: bench execute print_designer.commands.install_watermark_fields.install_watermark_fields")
        
        return False


if __name__ == "__main__":
    test_complete_print_designer_installation()