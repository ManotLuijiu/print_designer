#!/usr/bin/env python3
"""
Fix Dynamic Images "Image not Linked" issues and install signature fields
Run this script to diagnose and fix Dynamic Images problems
"""

import frappe
from frappe import _
import sys

def diagnose_dynamic_images():
    """Comprehensive diagnosis of Dynamic Images issues"""
    print("🔍 DIAGNOSING DYNAMIC IMAGES ISSUES")
    print("=" * 50)
    
    results = {
        "signature_fields_installed": 0,
        "signature_fields_missing": 0,
        "companies_with_signatures": 0,
        "total_image_fields": 0,
        "issues_found": []
    }
    
    # Check 1: Signature field installation
    print("\n1. CHECKING SIGNATURE FIELD INSTALLATION")
    try:
        from print_designer.api.signature_field_installer import check_signature_fields_status
        status = check_signature_fields_status()
        
        if status.get("success"):
            summary = status["results"]
            for doctype, info in summary.items():
                if info["status"] == "installed":
                    results["signature_fields_installed"] += len(info["fields"])
                    print(f"   ✅ {doctype}: {len(info['fields'])} fields installed")
                elif info["status"] == "partial":
                    installed_count = sum(1 for f in info["fields"] if f["installed"])
                    missing_count = len(info["fields"]) - installed_count
                    results["signature_fields_installed"] += installed_count
                    results["signature_fields_missing"] += missing_count
                    print(f"   ⚠️  {doctype}: {installed_count}/{len(info['fields'])} fields installed")
                else:
                    results["signature_fields_missing"] += len(info["fields"])
                    print(f"   ❌ {doctype}: 0/{len(info['fields'])} fields installed")
                    results["issues_found"].append(f"Signature fields not installed for {doctype}")
        else:
            print(f"   ❌ Error checking signature fields: {status.get('error')}")
            results["issues_found"].append("Failed to check signature field status")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        results["issues_found"].append(f"Signature field check failed: {str(e)}")
    
    # Check 2: Dynamic Images API
    print("\n2. CHECKING DYNAMIC IMAGES API")
    try:
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        image_fields = get_image_docfields()
        results["total_image_fields"] = len(image_fields)
        print(f"   ✅ Found {len(image_fields)} total image fields")
        
        signature_fields = [f for f in image_fields if 'signature' in f.get('fieldname', '').lower()]
        print(f"   ✅ Found {len(signature_fields)} signature-related fields")
        
        if len(signature_fields) == 0:
            results["issues_found"].append("No signature fields found in image fields API")
    except Exception as e:
        print(f"   ❌ Error getting image fields: {str(e)}")
        results["issues_found"].append(f"Image fields API failed: {str(e)}")
    
    # Check 3: Sample signature data
    print("\n3. CHECKING SAMPLE SIGNATURE DATA")
    try:
        companies = frappe.get_all("Company", limit=3)
        for company in companies:
            doc = frappe.get_doc("Company", company.name)
            signature_count = 0
            signature_fields = ["ceo_signature", "authorized_signature_1", "authorized_signature_2"]
            
            for field in signature_fields:
                if hasattr(doc, field) and getattr(doc, field):
                    signature_count += 1
            
            if signature_count > 0:
                results["companies_with_signatures"] += 1
                print(f"   ✅ {company.name}: {signature_count}/3 signatures uploaded")
            else:
                print(f"   ⚠️  {company.name}: No signatures uploaded")
    except Exception as e:
        print(f"   ❌ Error checking company signatures: {str(e)}")
    
    # Check 4: Signature enhancements
    print("\n4. CHECKING SIGNATURE ENHANCEMENTS")
    try:
        # Check if Signature Basic Information has enhanced fields
        enhanced_fields = frappe.db.get_all("Custom Field", {
            "dt": "Signature Basic Information",
            "fieldname": ["in", ["target_doctype", "target_signature_field", "auto_populate_target_field"]]
        }, ["fieldname"])
        
        if len(enhanced_fields) >= 3:
            print("   ✅ Signature Basic Information enhanced fields installed")
        else:
            print("   ⚠️  Signature Basic Information enhanced fields missing")
            results["issues_found"].append("Target Signature Field enhancement not installed")
    except Exception as e:
        print(f"   ❌ Error checking signature enhancements: {str(e)}")
    
    return results

def fix_dynamic_images():
    """Fix Dynamic Images issues"""
    print("\n🔧 FIXING DYNAMIC IMAGES ISSUES")
    print("=" * 50)
    
    fixes_applied = []
    
    # Fix 1: Install signature fields
    print("\n1. INSTALLING SIGNATURE FIELDS")
    try:
        from print_designer.api.signature_field_installer import install_signature_fields
        result = install_signature_fields()
        
        if result.get("success"):
            print(f"   ✅ Installed signature fields for {len(result['doctypes'])} DocTypes")
            fixes_applied.append("Signature fields installed")
        else:
            print(f"   ❌ Failed to install signature fields: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Error installing signature fields: {str(e)}")
    
    # Fix 2: Install signature enhancements
    print("\n2. INSTALLING SIGNATURE ENHANCEMENTS")
    try:
        from print_designer.api.safe_install import safe_install_signature_enhancements
        result = safe_install_signature_enhancements()
        
        if result.get("success"):
            print("   ✅ Signature enhancements installed successfully")
            fixes_applied.append("Signature enhancements installed")
        else:
            print(f"   ❌ Failed to install signature enhancements: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Error installing signature enhancements: {str(e)}")
    
    # Fix 3: Clear cache and refresh
    print("\n3. CLEARING CACHE AND REFRESHING")
    try:
        frappe.clear_cache()
        print("   ✅ Cache cleared")
        fixes_applied.append("Cache cleared")
    except Exception as e:
        print(f"   ❌ Error clearing cache: {str(e)}")
    
    # Fix 4: Refresh dynamic images
    print("\n4. REFRESHING DYNAMIC IMAGES")
    try:
        from print_designer.api.refresh_dynamic_images import refresh_dynamic_images
        result = refresh_dynamic_images()
        
        if result.get("success"):
            print(f"   ✅ {result['message']}")
            print(f"   📊 Total image fields: {result['total_image_fields']}")
            print(f"   🖋️  Signature fields: {result['signature_fields_available']}")
            fixes_applied.append("Dynamic images refreshed")
        else:
            print(f"   ❌ Failed to refresh dynamic images: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Error refreshing dynamic images: {str(e)}")
    
    return fixes_applied

def main():
    """Main execution function"""
    print("🎨 PRINT DESIGNER - DYNAMIC IMAGES FIX")
    print("=" * 50)
    print("This script will diagnose and fix Dynamic Images issues")
    print("including 'Image not Linked' problems and missing signature fields")
    
    # Diagnose issues
    results = diagnose_dynamic_images()
    
    print("\n📋 DIAGNOSIS SUMMARY")
    print("=" * 30)
    print(f"✅ Signature fields installed: {results['signature_fields_installed']}")
    print(f"❌ Signature fields missing: {results['signature_fields_missing']}")
    print(f"🏢 Companies with signatures: {results['companies_with_signatures']}")
    print(f"🖼️  Total image fields: {results['total_image_fields']}")
    
    if results['issues_found']:
        print(f"\n⚠️  ISSUES FOUND ({len(results['issues_found'])}):")
        for issue in results['issues_found']:
            print(f"   • {issue}")
    
    # Apply fixes
    fixes = fix_dynamic_images()
    
    print("\n✅ FIXES APPLIED")
    print("=" * 20)
    if fixes:
        for fix in fixes:
            print(f"   ✅ {fix}")
    else:
        print("   ⚠️  No fixes could be applied")
    
    print("\n🎯 NEXT STEPS")
    print("=" * 15)
    print("1. Hard refresh your browser (Ctrl+F5)")
    print("2. Go to Company DocType and upload signature images")
    print("3. Check Print Designer > Dynamic Images again")
    print("4. For Target Signature Field:")
    print("   → Go to 'Signature Basic Information' DocType")
    print("   → Create new signature record")
    print("   → You'll see Target DocType and Target Signature Field dropdowns")

if __name__ == "__main__":
    main()