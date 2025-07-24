#!/usr/bin/env python3
"""
Utility script to check which sites have print_designer installed.

Usage:
    python check_sites_with_print_designer.py
"""

import sys
import os
import glob

def check_sites_with_print_designer():
    """Check which sites have print_designer installed"""
    
    # Add the frappe-bench path to sys.path so we can import frappe
    bench_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    sys.path.insert(0, bench_path)
    
    try:
        import frappe
        
        # Get all site directories
        sites_path = os.path.join(bench_path, 'sites')
        site_dirs = [d for d in os.listdir(sites_path) 
                    if os.path.isdir(os.path.join(sites_path, d)) 
                    and not d.startswith('.') 
                    and d not in ['assets', 'apps.json', 'apps.txt', 'common_site_config.json', 'excluded_apps.txt']]
        
        sites_with_print_designer = []
        sites_without_print_designer = []
        
        for site_name in site_dirs:
            try:
                frappe.init(site_name)
                frappe.connect()
                
                installed_apps = frappe.get_installed_apps()
                if 'print_designer' in installed_apps:
                    sites_with_print_designer.append(site_name)
                else:
                    sites_without_print_designer.append(site_name)
                    
                frappe.destroy()
                
            except Exception as e:
                print(f"⚠️  Could not check site '{site_name}': {str(e)}")
                continue
        
        print("📋 Site Analysis Results:")
        print("=" * 50)
        
        if sites_with_print_designer:
            print(f"✅ Sites WITH print_designer ({len(sites_with_print_designer)}):")
            for site in sorted(sites_with_print_designer):
                print(f"   • {site}")
            print()
        
        if sites_without_print_designer:
            print(f"❌ Sites WITHOUT print_designer ({len(sites_without_print_designer)}):")
            for site in sorted(sites_without_print_designer):
                print(f"   • {site}")
            print()
        
        print("💡 To install watermark fields on sites with print_designer:")
        for site in sorted(sites_with_print_designer):
            print(f"   bench --site {site} install-watermark-fields")
        
        return sites_with_print_designer, sites_without_print_designer
        
    except Exception as e:
        print(f"❌ Error checking sites: {str(e)}")
        return [], []

def main():
    print("Checking all sites for print_designer installation...")
    print()
    check_sites_with_print_designer()

if __name__ == "__main__":
    main()