# Copyright (c) 2026, AWS Solution Ltd. and contributors
# For license information, please see license.txt


import os
import json
import click
import frappe
from frappe.commands import pass_context


@click.command("install-thai-payment-format")
@pass_context
def install_thai_payment_format(context):
    """Install Thai Tax Invoice format for Payment Entry"""
    
    site = context.sites[0] if context.sites else None
    if not site:
        click.echo("Please specify a site using --site option")
        return
    
    frappe.init(site=site)
    frappe.connect()
    
    try:
        # Check if format already exists
        existing_format = frappe.db.exists("Print Format", "Payment Entry Thai Tax Invoice")
        
        if existing_format:
            click.echo("♻️  Thai Payment format already exists. Updating...")
            print_format = frappe.get_doc("Print Format", existing_format)
        else:
            click.echo("🆕 Creating new Thai Payment format...")
            print_format = frappe.new_doc("Print Format")
            print_format.name = "Payment Entry Thai Tax Invoice"
        
        # Set basic properties
        print_format.update({
            "doc_type": "Payment Entry",
            "module": "Print Designer",
            "print_designer": 1,
            "disabled": 0,
            "standard": "No",
            "print_format_type": "Jinja",
            "font": "Sarabun",
            "font_size": 14,
            "margin_top": 15,
            "margin_bottom": 15,
            "margin_left": 10,
            "margin_right": 10,
            "page_size": "A4",
            "default_print_language": "th",
            "css": """
.print-format {
    font-family: 'Sarabun', sans-serif;
    font-size: 14px;
    line-height: 1.4;
}

.thai-tax-invoice table {
    font-size: 12px;
}

@media print {
    .print-format {
        font-size: 12px;
    }
}
""",
            "html": """
{%- set invoice_items = [] -%}
{%- set invoice_totals = {} -%}

{# Collect items from referenced invoices #}
{%- for reference in doc.references -%}
  {%- if reference.reference_doctype == "Sales Invoice" -%}
    {%- set invoice = frappe.get_doc("Sales Invoice", reference.reference_name) -%}
    {%- for item in invoice.items -%}
      {%- set _ = invoice_items.append({
        'item_code': item.item_code,
        'item_name': item.item_name,
        'description': item.description,
        'qty': item.qty,
        'uom': item.uom,
        'rate': item.rate,
        'amount': item.amount,
        'invoice_no': invoice.name
      }) -%}
    {%- endfor -%}
    {%- set _ = invoice_totals.update({
      invoice.name: {
        'net_total': invoice.net_total,
        'grand_total': invoice.grand_total,
        'total_taxes_and_charges': invoice.total_taxes_and_charges or 0
      }
    }) -%}
  {%- endif -%}
{%- endfor -%}

<div class="thai-tax-invoice" style="font-family: 'Sarabun', Arial, sans-serif; max-width: 800px; margin: 0 auto;">
  <!-- Header -->
  <div style="text-align: center; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 15px;">
    <h1 style="margin: 0; font-size: 24px;">{{ doc.company }}</h1>
    <div style="font-size: 18px; margin: 10px 0;">
      <strong>ใบกำกับภาษี / Tax Invoice</strong><br>
      <strong>ใบเสร็จรับเงิน / Receipt</strong>
    </div>
  </div>

  <!-- Document Info -->
  <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
    <div style="width: 48%;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 4px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">เลขที่ / No.</td>
          <td style="padding: 4px; border: 1px solid #ddd;">{{ doc.name }}</td>
        </tr>
        <tr>
          <td style="padding: 4px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">วันที่ / Date</td>
          <td style="padding: 4px; border: 1px solid #ddd;">{{ doc.posting_date.strftime('%d/%m/%Y') if doc.posting_date else '' }}</td>
        </tr>
        <tr>
          <td style="padding: 4px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">ลูกค้า / Customer</td>
          <td style="padding: 4px; border: 1px solid #ddd;">{{ doc.party_name or doc.party }}</td>
        </tr>
      </table>
    </div>
    <div style="width: 48%;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 4px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">ประเภท / Type</td>
          <td style="padding: 4px; border: 1px solid #ddd;">{{ doc.payment_type }}</td>
        </tr>
        <tr>
          <td style="padding: 4px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">วิธีชำระ / Method</td>
          <td style="padding: 4px; border: 1px solid #ddd;">{{ doc.mode_of_payment or '-' }}</td>
        </tr>
        <tr>
          <td style="padding: 4px; border: 1px solid #ddd; background: #f8f9fa; font-weight: bold;">จำนวนเงิน / Amount</td>
          <td style="padding: 4px; border: 1px solid #ddd;">{{ '{:,.2f}'.format(doc.paid_amount) }} {{ doc.paid_to_account_currency or doc.company_currency }}</td>
        </tr>
      </table>
    </div>
  </div>

  <!-- Items Section -->
  {% if invoice_items %}
  <div style="margin-bottom: 20px;">
    <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">รายการสินค้า / Items</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #000;">
      <thead>
        <tr style="background-color: #f5f5f5;">
          <th style="border: 1px solid #000; padding: 8px;">รหัสสินค้า<br>Item Code</th>
          <th style="border: 1px solid #000; padding: 8px;">รายละเอียด<br>Description</th>
          <th style="border: 1px solid #000; padding: 8px;">จำนวน<br>Qty</th>
          <th style="border: 1px solid #000; padding: 8px;">ราคา<br>Rate</th>
          <th style="border: 1px solid #000; padding: 8px;">จำนวนเงิน<br>Amount</th>
          <th style="border: 1px solid #000; padding: 8px;">ใบแจ้งหนี้<br>Invoice</th>
        </tr>
      </thead>
      <tbody>
        {% for item in invoice_items %}
        <tr>
          <td style="border: 1px solid #000; padding: 6px;">{{ item.item_code }}</td>
          <td style="border: 1px solid #000; padding: 6px;">{{ item.description or item.item_name }}</td>
          <td style="border: 1px solid #000; padding: 6px; text-align: center;">{{ item.qty }}</td>
          <td style="border: 1px solid #000; padding: 6px; text-align: right;">{{ '{:,.2f}'.format(item.rate) }}</td>
          <td style="border: 1px solid #000; padding: 6px; text-align: right;">{{ '{:,.2f}'.format(item.amount) }}</td>
          <td style="border: 1px solid #000; padding: 6px; text-align: center;">{{ item.invoice_no }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <!-- Referenced Documents -->
  {% if doc.references %}
  <div style="margin-bottom: 20px;">
    <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">เอกสารอ้างอิง / Referenced Documents</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #000;">
      <thead>
        <tr style="background-color: #f5f5f5;">
          <th style="border: 1px solid #000; padding: 8px;">ประเภท<br>Type</th>
          <th style="border: 1px solid #000; padding: 8px;">เลขที่<br>Number</th>
          <th style="border: 1px solid #000; padding: 8px;">จำนวนเงิน<br>Amount</th>
        </tr>
      </thead>
      <tbody>
        {% for reference in doc.references %}
        <tr>
          <td style="border: 1px solid #000; padding: 6px;">{{ reference.reference_doctype }}</td>
          <td style="border: 1px solid #000; padding: 6px;">{{ reference.reference_name }}</td>
          <td style="border: 1px solid #000; padding: 6px; text-align: right;">{{ '{:,.2f}'.format(reference.allocated_amount) }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <!-- Payment Summary -->
  <div style="display: flex; justify-content: flex-end; margin: 20px 0;">
    <table style="width: 300px; border-collapse: collapse;">
      <tr>
        <td style="padding: 6px; border: 1px solid #000; background: #f8f9fa; text-align: right; font-weight: bold;">จำนวนเงินที่ชำระ<br>Payment Amount</td>
        <td style="padding: 6px; border: 1px solid #000; text-align: right; font-weight: bold;">{{ '{:,.2f}'.format(doc.paid_amount) }} {{ doc.paid_to_account_currency or doc.company_currency }}</td>
      </tr>
    </table>
  </div>

  <!-- Signatures -->
  <div style="display: flex; justify-content: space-between; margin-top: 40px; gap: 20px;">
    <div style="flex: 1; text-align: center; border: 1px solid #ccc; padding: 20px; min-height: 60px;">
      <div style="border-top: 1px solid #000; margin-top: 40px; padding-top: 5px;">
        ผู้รับเงิน<br>Received by
      </div>
    </div>
    <div style="flex: 1; text-align: center; border: 1px solid #ccc; padding: 20px; min-height: 60px;">
      <div style="border-top: 1px solid #000; margin-top: 40px; padding-top: 5px;">
        ผู้อนุมัติ<br>Approved by
      </div>
    </div>
    <div style="flex: 1; text-align: center; border: 1px solid #ccc; padding: 20px; min-height: 60px;">
      <div style="border-top: 1px solid #000; margin-top: 40px; padding-top: 5px;">
        ลูกค้า<br>Customer
      </div>
    </div>
  </div>
</div>
"""
        })
        
        # Save the print format
        if existing_format:
            print_format.save()
            click.echo("✅ Thai Payment format updated successfully!")
        else:
            print_format.insert()
            click.echo("✅ Thai Payment format created successfully!")
        
        frappe.db.commit()
        
        # Instructions
        click.echo("\n📋 Next steps:")
        click.echo("1. Go to Payment Entry > Print > Select 'Payment Entry Thai Tax Invoice'")
        click.echo("2. The format will show items from referenced Sales Invoices")
        click.echo("3. Customize the format in Print Designer if needed")
        click.echo("\n🇹🇭 Format includes:")
        click.echo("   • Thai and English labels")
        click.echo("   • Items from referenced invoices")
        click.echo("   • Tax compliance structure")
        click.echo("   • Signature areas")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        frappe.db.rollback()
        frappe.log_error(f"Error installing Thai payment format: {str(e)}")
    finally:
        frappe.destroy()


commands = [install_thai_payment_format]