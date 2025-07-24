import os
import json
import click
import frappe
from frappe.commands import pass_context


def install_print_format():
    """
    Install Delivery Note QR print format
    """
    format_name = "Delivery Note with QR Approval"
    
    # Check if format already exists
    existing_format = frappe.db.exists("Print Format", format_name)
    
    if existing_format:
        print_format = frappe.get_doc("Print Format", existing_format)
    else:
        print_format = frappe.new_doc("Print Format")
        print_format.name = format_name
    
    # Load the JSON template
    template_path = "/home/frappe/frappe-bench/apps/print_designer/print_designer/default_templates/erpnext/delivery_note_qr_approval.json"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.loads(f.read())
        
        # Update the print format with JSON data
        print_format.update({
            "doc_type": "Delivery Note",
            "module": "Print Designer",
            "print_designer": 1,
            "disabled": 0,
            "standard": "No",
            "font": template_data.get("font", "Arial"),
            "font_size": template_data.get("font_size", 12),
            "margin_top": template_data.get("margin_top", 20),
            "margin_bottom": template_data.get("margin_bottom", 20),
            "margin_left": template_data.get("margin_left", 20),
            "margin_right": template_data.get("margin_right", 20),
            "page_size": template_data.get("page_size", "A4"),
            "print_designer_settings": json.dumps(template_data.get("print_designer_settings", {})),
            "print_designer_header": json.dumps(template_data.get("print_designer_header", [])),
            "print_designer_body": json.dumps(template_data.get("print_designer_body", [])),
            "print_designer_footer": json.dumps(template_data.get("print_designer_footer", [])),
            "css": template_data.get("css", ""),
            "description": template_data.get("description", "Professional Delivery Note template with integrated QR code for customer approval workflow"),
        })
        
        # Save the format
        if existing_format:
            print_format.save()
        else:
            print_format.insert()
            
    except Exception as e:
        frappe.log_error(f"Error installing Delivery Note QR print format: {str(e)}")
        raise


@click.command("install-delivery-qr")
@pass_context
def install_delivery_qr(context):
    """Install Delivery Note QR Code approval system"""

    site = context.sites[0] if context.sites else None
    if not site:
        click.echo("Please specify a site using --site option")
        return

    frappe.init(site=site)
    frappe.connect()

    try:
        click.echo("🚚 Installing Delivery Note QR Code approval system...")
        
        # Import and run the custom fields installation
        from print_designer.custom.delivery_note_qr import add_custom_fields, create_delivery_approval_page
        
        # Add custom fields
        add_custom_fields()
        click.echo("   ✅ Added custom fields to Delivery Note")
        
        # Create delivery approval web page
        try:
            create_delivery_approval_page()
            click.echo("   ✅ Created delivery approval web page")
        except Exception as e:
            click.echo(f"   ⚠️  Web page creation skipped: {str(e)}")
        
        # Install print format
        install_print_format()
        click.echo("   ✅ Installed Delivery Note QR print format")
        
        # Commit changes
        frappe.db.commit()
        
        # Success message
        click.echo(f"\n✅ Delivery Note QR Code system installed successfully!")
        
        # Feature overview
        click.echo(f"\n🎯 Features installed:")
        click.echo(f"   📱 QR Code generation for delivery approval")
        click.echo(f"   ✅ Customer approval/rejection workflow")
        click.echo(f"   🖊️  Digital signature collection")
        click.echo(f"   📊 Status tracking and audit trail")
        click.echo(f"   🌐 Web-based approval interface")
        
        # Usage instructions
        click.echo(f"\n📖 How to use:")
        click.echo(f"   1. Submit a Delivery Note")
        click.echo(f"   2. QR code will be automatically generated")
        click.echo(f"   3. Customer scans QR code to approve/reject delivery")
        click.echo(f"   4. Status and signatures are tracked automatically")
        
        # API endpoints
        click.echo(f"\n🔗 Available API endpoints:")
        click.echo(f"   • generate_delivery_approval_qr(delivery_note_name)")
        click.echo(f"   • approve_delivery_goods(delivery_note_name, signature)")
        click.echo(f"   • reject_delivery_goods(delivery_note_name, reason)")
        click.echo(f"   • get_delivery_status(delivery_note_name)")
        click.echo(f"   • get_qr_code_image(delivery_note_name)")
        
        # Print format integration
        click.echo(f"\n🖨️  Print Format Integration:")
        click.echo(f"   • 'Delivery Note with QR Approval' format installed")
        click.echo(f"   • QR codes available in custom_approval_qr_code field")
        click.echo(f"   • Use get_qr_code_image() in Jinja templates")
        click.echo(f"   • Status tracking in custom_goods_received_status")
        click.echo(f"   • Professional layout with customer approval section")
        
        # Custom fields added
        click.echo(f"\n📝 Custom fields added to Delivery Note:")
        custom_fields = [
            "custom_delivery_approval_section",
            "custom_goods_received_status", 
            "custom_approval_qr_code",
            "custom_approval_url",
            "custom_customer_approval_date",
            "custom_approved_by",
            "custom_customer_signature",
            "custom_rejection_reason"
        ]
        for field in custom_fields:
            exists = frappe.db.exists("Custom Field", {"dt": "Delivery Note", "fieldname": field})
            status = "✅" if exists else "❌"
            click.echo(f"   {status} {field}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        frappe.db.rollback()
        frappe.log_error(f"Error installing Delivery Note QR system: {str(e)}")
    finally:
        frappe.destroy()


commands = [install_delivery_qr]