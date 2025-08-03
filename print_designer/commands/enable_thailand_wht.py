#!/usr/bin/env python3

import click
import frappe


def enable_thailand_wht_for_company(company_name):
    """Enable Thailand WHT for a specific company"""
    try:
        company_doc = frappe.get_doc("Company", company_name)
        company_doc.thailand_service_business = 1
        company_doc.save()
        frappe.db.commit()
        click.echo(f"✅ Thailand service business enabled for {company_name}")
        return True
    except Exception as e:
        click.echo(f"❌ Error enabling Thailand WHT for {company_name}: {str(e)}")
        return False


def enable_thailand_wht_for_all_companies():
    """Enable Thailand WHT for all companies"""
    companies = frappe.get_all("Company", fields=["name"])
    
    if not companies:
        click.echo("No companies found!")
        return
    
    click.echo(f"Found {len(companies)} companies. Enabling Thailand WHT...")
    
    success_count = 0
    for company in companies:
        if enable_thailand_wht_for_company(company.name):
            success_count += 1
    
    click.echo(f"✅ Thailand WHT enabled for {success_count}/{len(companies)} companies")


def check_thailand_wht_status():
    """Check Thailand WHT status for all companies"""
    companies = frappe.get_all("Company", fields=["name", "thailand_service_business"])
    
    if not companies:
        click.echo("No companies found!")
        return
    
    click.echo("Thailand Withholding Tax Status:")
    click.echo("-" * 50)
    
    for company in companies:
        status = "✅ Enabled" if company.thailand_service_business else "❌ Disabled"
        click.echo(f"{company.name}: {status}")


if __name__ == "__main__":
    check_thailand_wht_status()
    enable_thailand_wht_for_all_companies()