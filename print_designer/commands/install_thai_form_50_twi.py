import os
import json
import click
import frappe
from frappe.commands import pass_context


@click.command("install-thai-form-50-twi")
@pass_context
def install_thai_form_50_twi(context):
    """Install Thai Form 50 ทวิ (Withholding Tax Certificate) formats"""

    site = context.sites[0] if context.sites else None
    if not site:
        click.echo("Please specify a site using --site option")
        return

    frappe.init(site=site)
    frappe.connect()

    try:
        # Create formats for different document types
        formats_to_create = [
            {
                "name": "Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate",
                "doc_type": "Payment Entry",
                "description": "หนังสือรับรองการหักภาษี ณ ที่จ่าย สำหรับ Payment Entry (Thai Withholding Tax Certificate for Payment Entry)",
                "template_file": "payment_entry_form_50_twi.json",
            },
            {
                "name": "Purchase Invoice Form 50 ทวิ",
                "doc_type": "Purchase Invoice", 
                "description": "หนังสือรับรองการหักภาษี ณ ที่จ่าย สำหรับ Purchase Invoice",
                "template_file": "thai_form_50_twi.html",
            },
            {
                "name": "Journal Entry Form 50 ทวิ",
                "doc_type": "Journal Entry",
                "description": "หนังสือรับรองการหักภาษี ณ ที่จ่าย สำหรับ Journal Entry",
                "template_file": "thai_form_50_twi.html",
            },
        ]

        created_count = 0
        updated_count = 0

        for format_config in formats_to_create:
            existing_format = frappe.db.exists("Print Format", format_config["name"])

            if existing_format:
                click.echo(f"♻️  Updating existing format: {format_config['name']}")
                print_format = frappe.get_doc("Print Format", existing_format)
                updated_count += 1
            else:
                click.echo(f"🆕 Creating new format: {format_config['name']}")
                print_format = frappe.new_doc("Print Format")
                print_format.name = format_config["name"]
                created_count += 1

            # Handle different template types
            if format_config["template_file"].endswith(".json"):
                # Load Print Designer JSON format
                template_path = f"/home/frappe/frappe-bench/apps/print_designer/print_designer/default_templates/erpnext/{format_config['template_file']}"
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        template_data = json.loads(f.read())
                    
                    # Update the print format with JSON data
                    print_format.update({
                        "doc_type": format_config["doc_type"],
                        "module": "Print Designer",
                        "print_designer": 1,
                        "disabled": 0,
                        "standard": "No",
                        "font": template_data.get("font", "Sarabun"),
                        "font_size": template_data.get("font_size", 12),
                        "margin_top": template_data.get("margin_top", 15),
                        "margin_bottom": template_data.get("margin_bottom", 15),
                        "margin_left": template_data.get("margin_left", 15),
                        "margin_right": template_data.get("margin_right", 15),
                        "page_size": template_data.get("page_size", "A4"),
                        "default_print_language": template_data.get("default_print_language", "th"),
                        "print_designer_settings": json.dumps(template_data.get("print_designer_settings", {})),
                        "print_designer_header": json.dumps(template_data.get("print_designer_header", [])),
                        "print_designer_body": json.dumps(template_data.get("print_designer_body", [])),
                        "print_designer_footer": json.dumps(template_data.get("print_designer_footer", [])),
                        "css": template_data.get("css", ""),
                        "description": format_config["description"],
                    })
                    click.echo(f"   📋 Loaded Print Designer JSON template")
                    
                except Exception as e:
                    click.echo(f"❌ Error reading JSON template: {str(e)}")
                    continue
                    
            else:
                # Load HTML Jinja template (legacy)
                template_path = f"/home/frappe/frappe-bench/apps/print_designer/print_designer/print_designer/page/print_designer/jinja/{format_config['template_file']}"
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        template_html = f.read()
                    
                    # Set format properties for HTML template
                    print_format.update({
                        "doc_type": format_config["doc_type"],
                        "module": "Print Designer",
                        "print_designer": 1,
                        "disabled": 0,
                        "standard": "No",
                        "print_format_type": "Jinja",
                        "font": "Sarabun",
                        "font_size": 12,
                        "margin_top": 15,
                        "margin_bottom": 15,
                        "margin_left": 15,
                        "margin_right": 15,
                        "page_size": "A4",
                        "default_print_language": "th",
                        "html": template_html,
                        "css": """
/* Thai Form 50 ทวิ Styles */
.form-50-twi {
    font-family: 'Sarabun', Arial, sans-serif;
    font-size: 12px;
    line-height: 1.2;
}

.form-50-twi .tax-table {
    font-size: 11px;
}

.form-50-twi .checkbox {
    font-family: Arial, sans-serif;
}

@media print {
    .form-50-twi {
        font-size: 11px;
    }

    .form-50-twi .signature-box {
        min-height: 60px;
    }
}
""",
                        "description": format_config["description"],
                    })
                    click.echo(f"   📋 Loaded HTML Jinja template")
                    
                except Exception as e:
                    click.echo(f"❌ Error reading HTML template: {str(e)}")
                    continue

            # Save the format
            if existing_format:
                print_format.save()
            else:
                print_format.insert()

        frappe.db.commit()

        # Success message
        if created_count > 0 or updated_count > 0:
            click.echo(f"\n✅ Success!")
            if created_count > 0:
                click.echo(f"   📋 Created {created_count} new Form 50 ทวิ formats")
            if updated_count > 0:
                click.echo(f"   🔄 Updated {updated_count} existing formats")

        # Instructions
        click.echo(f"\n📋 Available Form 50 ทวิ formats:")
        for format_config in formats_to_create:
            click.echo(
                f"   • {format_config['name']} - for {format_config['doc_type']}"
            )

        click.echo(f"\n🇹🇭 Form 50 ทวิ Features:")
        click.echo(f"   ✅ Official Thai withholding tax certificate format")
        click.echo(f"   ✅ Automatic tax calculations")
        click.echo(f"   ✅ Payer and payee information")
        click.echo(f"   ✅ Tax rate and amount details")
        click.echo(f"   ✅ Signature areas for compliance")
        click.echo(f"   ✅ Thai and English labels")

        click.echo(f"\n📖 Usage:")
        click.echo(f"   1. Open Payment Entry, Purchase Invoice, or Journal Entry")
        click.echo(f"   2. Click Print and select the appropriate Form 50 ทวิ format")
        click.echo(f"   3. The form will auto-populate with document data")
        click.echo(f"   4. Review and print for tax compliance")

        click.echo(f"\n⚠️  Important Notes:")
        click.echo(f"   • Verify tax rates are correct for your transactions")
        click.echo(f"   • Ensure tax ID numbers are properly configured")
        click.echo(f"   • Review amounts before submitting to tax authorities")
        click.echo(f"   • Keep copies for your records")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        frappe.db.rollback()
        frappe.log_error(f"Error installing Thai Form 50 ทวิ: {str(e)}")
    finally:
        frappe.destroy()


commands = [install_thai_form_50_twi]
