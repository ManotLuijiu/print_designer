# Copyright (c) 2026, AWS Solution Ltd. and contributors
# For license information, please see license.txt


import click
import frappe
from frappe.commands import pass_context


@click.command("install-complete-system")
@pass_context
def install_complete_system(context):
    """Install complete Thai WHT and QR Delivery system for Print Designer"""
    
    site = context.sites[0] if context.sites else None
    if not site:
        click.echo("Please specify a site using --site option")
        return

    frappe.init(site=site)
    frappe.connect()

    try:
        click.echo("🚀 Installing Complete Print Designer System...")
        click.echo("   📋 Thai Withholding Tax Certificate (Form 50 ทวิ)")
        click.echo("   📦 QR Code Delivery Approval System")
        click.echo("")
        
        # Import and run the complete setup
        from print_designer.setup.install import setup_thai_withholding_tax_and_qr_delivery
        
        result = setup_thai_withholding_tax_and_qr_delivery()
        
        if result["success"]:
            click.echo("✅ Installation completed successfully!")
            click.echo("")
            click.echo("🎯 Features installed:")
            for feature in result["features"]:
                click.echo(f"   ✓ {feature}")
            
            click.echo("")
            click.echo("📖 Usage Instructions:")
            click.echo("")
            
            click.echo("🏛️  Thai Form 50 ทวิ (Withholding Tax Certificate):")
            click.echo("   1. Create Payment Entry for supplier payment")
            click.echo("   2. Enable 'Apply Thai Withholding Tax' checkbox")
            click.echo("   3. Set withholding tax rate (3% for services, 1% for rental)")
            click.echo("   4. Enter supplier's 13-digit Tax ID")
            click.echo("   5. Save and submit Payment Entry")
            click.echo("   6. Print using 'Payment Entry Form 50 ทวิ' format")
            click.echo("")
            
            click.echo("📱 QR Code Delivery Approval:")
            click.echo("   1. Create and submit Delivery Note")
            click.echo("   2. QR code automatically generated")
            click.echo("   3. Customer scans QR code from delivery note")
            click.echo("   4. Customer approves/rejects via web interface")
            click.echo("   5. Status tracked automatically")
            click.echo("   6. Use 'Delivery Note with QR Approval' print format")
            click.echo("")
            
            click.echo("🔗 API Endpoints Available:")
            click.echo("   • generate_delivery_approval_qr(delivery_note_name)")
            click.echo("   • approve_delivery_goods(delivery_note_name, signature)")
            click.echo("   • reject_delivery_goods(delivery_note_name, reason)")
            click.echo("   • get_delivery_status(delivery_note_name)")
            click.echo("")
            
            click.echo("🖥️  Web Interface:")
            click.echo("   • /delivery-approval/{delivery_note_id}")
            click.echo("   • Professional Bootstrap 5 interface")
            click.echo("   • Digital signature collection")
            click.echo("   • Mobile-responsive design")
            click.echo("")
            
            click.echo("📝 Custom Fields Added:")
            click.echo("   Delivery Note: 8 fields for QR approval workflow")
            click.echo("   Payment Entry: 7 fields for Thai withholding tax")
            click.echo("")
            
            # Check installation status
            from print_designer.setup.install import get_installation_status
            status = get_installation_status()
            
            click.echo("📊 Installation Status:")
            click.echo(f"   • Delivery Note fields: {status['custom_fields']['delivery_note']['installed']}/{status['custom_fields']['delivery_note']['total']}")
            click.echo(f"   • Payment Entry fields: {status['custom_fields']['payment_entry']['installed']}/{status['custom_fields']['payment_entry']['total']}")
            click.echo(f"   • Print formats: {'✓' if status['print_formats']['thai_wht'] and status['print_formats']['qr_delivery'] else '⚠️'}")
            click.echo(f"   • Web interface: {'✓' if status['web_pages']['delivery_approval'] else '⚠️'}")
            click.echo(f"   • API endpoints: {status['api_endpoints']['available']}/{status['api_endpoints']['total']}")
            
        else:
            click.echo(f"❌ Installation failed: {result['message']}")
            
    except Exception as e:
        click.echo(f"❌ Error during installation: {str(e)}")
        frappe.db.rollback()
        frappe.log_error(f"Error installing complete system: {str(e)}")
    finally:
        frappe.destroy()


@click.command("check-system-status")
@pass_context
def check_system_status(context):
    """Check installation status of Print Designer system components"""
    
    site = context.sites[0] if context.sites else None
    if not site:
        click.echo("Please specify a site using --site option")
        return

    frappe.init(site=site)
    frappe.connect()

    try:
        from print_designer.setup.install import get_installation_status
        
        click.echo("📊 Print Designer System Status")
        click.echo("=" * 50)
        
        status = get_installation_status()
        
        # Custom Fields Status
        click.echo("\n📝 Custom Fields:")
        dn_fields = status['custom_fields']['delivery_note']
        pe_fields = status['custom_fields']['payment_entry']
        
        click.echo(f"   Delivery Note: {dn_fields['installed']}/{dn_fields['total']} installed")
        if dn_fields['missing']:
            click.echo(f"      Missing: {', '.join(dn_fields['missing'])}")
        
        click.echo(f"   Payment Entry: {pe_fields['installed']}/{pe_fields['total']} installed")
        if pe_fields['missing']:
            click.echo(f"      Missing: {', '.join(pe_fields['missing'])}")
        
        # Print Formats Status
        click.echo("\n🖨️  Print Formats:")
        click.echo(f"   Thai WHT Certificate: {'✅ Installed' if status['print_formats']['thai_wht'] else '❌ Missing'}")
        click.echo(f"   QR Delivery Format: {'✅ Installed' if status['print_formats']['qr_delivery'] else '❌ Missing'}")
        
        # Web Interface Status
        click.echo("\n🌐 Web Interface:")
        click.echo(f"   Delivery Approval Page: {'✅ Available' if status['web_pages']['delivery_approval'] else '❌ Missing'}")
        
        # API Endpoints Status
        click.echo("\n🔗 API Endpoints:")
        api_status = status['api_endpoints']
        click.echo(f"   Available: {api_status['available']}/{api_status['total']}")
        for endpoint in api_status['endpoints']:
            click.echo(f"      ✅ {endpoint}")
        
        # Overall health
        click.echo("\n🏥 Overall Health:")
        total_components = (
            dn_fields['total'] + pe_fields['total'] + 
            2 +  # print formats
            1 +  # web page
            api_status['total']  # api endpoints
        )
        installed_components = (
            dn_fields['installed'] + pe_fields['installed'] +
            (1 if status['print_formats']['thai_wht'] else 0) +
            (1 if status['print_formats']['qr_delivery'] else 0) +
            (1 if status['web_pages']['delivery_approval'] else 0) +
            api_status['available']
        )
        
        health_percentage = (installed_components / total_components) * 100
        click.echo(f"   System Health: {health_percentage:.1f}% ({installed_components}/{total_components} components)")
        
        if health_percentage == 100:
            click.echo("   🎉 System is fully installed and ready!")
        elif health_percentage >= 80:
            click.echo("   ⚠️  System mostly installed with minor issues")
        else:
            click.echo("   🔧 System needs attention - run install-complete-system")
            
    except Exception as e:
        click.echo(f"❌ Error checking status: {str(e)}")
        frappe.log_error(f"Error checking system status: {str(e)}")
    finally:
        frappe.destroy()


commands = [install_complete_system, check_system_status]