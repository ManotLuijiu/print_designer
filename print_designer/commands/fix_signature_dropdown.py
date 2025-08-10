#!/usr/bin/env python3
"""
Command to fix signature dropdown issue across all sites
This addresses the missing client script that populates dropdown options
"""

import frappe
from frappe.commands import pass_context, click


def get_context(context):
    "Patch function to get context"
    return context


@click.command("fix-signature-dropdown")
@click.option('--site', help='Specific site to fix (optional, defaults to all sites)')
@pass_context
def fix_signature_dropdown(context, site=None):
    """
    Fix the empty Target Signature Field dropdown issue
    
    This command:
    1. Installs the missing client script for Signature Basic Information
    2. Clears cache to refresh the interface
    3. Verifies the fix works properly
    
    Usage:
    bench fix-signature-dropdown                    # Fix all sites
    bench --site [site-name] fix-signature-dropdown  # Fix specific site
    """
    if site:
        sites_to_fix = [site]
    else:
        sites_to_fix = frappe.utils.get_sites()
    
    print(f"\n🔧 Fixing signature dropdown for {len(sites_to_fix)} site(s)...")
    
    results = {}
    
    for site_name in sites_to_fix:
        try:
            print(f"\n📍 Processing site: {site_name}")
            
            # Initialize frappe for this site
            frappe.init(site=site_name)
            frappe.connect()
            
            # Run the fix
            from print_designer.api.install_client_script import fix_signature_dropdown
            result = fix_signature_dropdown()
            
            if result.get("success"):
                print(f"   ✅ Fixed successfully")
                for step in result.get("steps", []):
                    step_name = step.get("step", "Unknown")
                    step_result = step.get("result", {})
                    if step_result.get("success"):
                        print(f"   ├─ {step_name}: ✅")
                    else:
                        print(f"   ├─ {step_name}: ❌ {step_result.get('error', 'Failed')}")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
            results[site_name] = result
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Error: {error_msg}")
            results[site_name] = {"error": error_msg, "success": False}
        
        finally:
            frappe.destroy()
    
    # Summary
    successful_sites = [site for site, result in results.items() if result.get("success")]
    failed_sites = [site for site, result in results.items() if not result.get("success")]
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Successful: {len(successful_sites)} sites")
    if successful_sites:
        for site in successful_sites:
            print(f"      - {site}")
    
    print(f"   ❌ Failed: {len(failed_sites)} sites")
    if failed_sites:
        for site in failed_sites:
            error = results[site].get("error", "Unknown error")
            print(f"      - {site}: {error}")
    
    print(f"\n{'='*50}")
    if failed_sites:
        print("⚠️  Some sites failed. Check the errors above.")
        print("💡 You can re-run this command to retry failed sites.")
    else:
        print("🎉 All sites fixed successfully!")
        print("🔄 Users should refresh their browser to see the dropdown options.")
    
    return results


# Alternative function for bench execute
def fix_all_sites():
    """
    Function that can be called via bench execute
    
    Usage:
    bench --all-sites execute print_designer.commands.fix_signature_dropdown.fix_current_site
    """
    try:
        from print_designer.api.install_client_script import fix_signature_dropdown
        result = fix_signature_dropdown()
        
        site_name = frappe.local.site
        if result.get("success"):
            print(f"✅ {site_name}: Fixed successfully")
        else:
            print(f"❌ {site_name}: {result.get('error', 'Failed')}")
        
        return result
        
    except Exception as e:
        print(f"❌ {frappe.local.site}: Error - {str(e)}")
        return {"error": str(e), "success": False}


def fix_current_site():
    """
    Fix the current site (for use with bench execute)
    """
    return fix_all_sites()


if __name__ == "__main__":
    fix_signature_dropdown()