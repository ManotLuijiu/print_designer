"""
Command to fix Thailand Address Template to include county with Thai labels.

Usage:
    bench --site [site] execute print_designer.commands.fix_thai_address_template

This command updates the Thailand Address Template to display:
- If country == "Thailand":
  - ตำบล (Sub-district) from city field
  - อำเภอ (District) from county field
  - จังหวัด (Province) from state field
  - รหัสไปรษณีย์ (Postal code) from pincode field
- If country != "Thailand": Show default format (no Thai labels)

Example Thai output:
    142/191 หมู่ 7
    ตำบล: กะทู้
    อำเภอ: กะทู้
    จังหวัด: ภูเก็ต
    รหัสไปรษณีย์: 83120
    Thailand

Example Overseas output:
    123 Main Street
    Suite 100
    California
    90210
    United States
"""

import frappe


def execute():
    """Update Thailand Address Template to include Thai labels with country condition."""
    
    site = frappe.local.site
    print(f"📍 Fixing Thailand Address Template for site: {site}")
    
    # Check if Thailand template exists
    if not frappe.db.exists("Address Template", "Thailand"):
        print("❌ Thailand Address Template not found.")
        print("   Creating new template...")
        create_thailand_template()
    else:
        update_thailand_template()
    
    print("\n✅ Thailand Address Template fix completed!")
    
    # Show example
    show_example()


def create_thailand_template():
    """Create new Thailand Address Template."""
    doc = frappe.get_doc({
        "doctype": "Address Template",
        "name": "Thailand",
        "country": "Thailand",
        "template": get_thai_address_template(),
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print("   Created new Thailand Address Template")


def update_thailand_template():
    """Update existing Thailand Address Template."""
    doc = frappe.get_doc("Address Template", "Thailand")
    doc.template = get_thai_address_template()
    doc.save()
    frappe.db.commit()
    print("   Updated existing Thailand Address Template")


def get_thai_address_template() -> str:
    """Get the Thai address template with country condition."""
    return """{{ address_line1 }}<br>
{% if address_line2 %}{{ address_line2 }}<br>{% endif -%}
{% if country == "Thailand" %}
{% if city %}ตำบล: {{ city }}<br>{% endif -%}
{% if county %}อำเภอ: {{ county }}<br>{% endif -%}
{% if state %}จังหวัด: {{ state }}<br>{% endif -%}
{% if pincode %}รหัสไปรษณีย์: {{ pincode }}<br>{% endif -%}
{% else %}
{% if city %}{{ city }}<br>{% endif -%}
{% if county %}{{ county }}<br>{% endif -%}
{% if state %}{{ state }}<br>{% endif -%}
{% if pincode %}{{ pincode }}<br>{% endif -%}
{% endif %}
{{ country }}<br>
<br>
{% if phone %}{{ _("Phone") }}: {{ phone }}<br>{% endif -%}
{% if fax %}{{ _("Fax") }}: {{ fax }}<br>{% endif -%}
{% if email_id %}{{ _("Email") }}: {{ email_id }}<br>{% endif -%}"""


def show_example():
    """Show example of how addresses will display."""
    print("\n📝 Example Thai address:")
    print("-" * 40)
    print("""142/191 หมู่ 7
ตำบล: กะทู้
อำเภอ: กะทู้
จังหวัด: ภูเก็ต
รหัสไปรษณีย์: 83120
Thailand""")
    print("-" * 40)
    print("\n📝 Example Overseas address (no Thai labels):")
    print("-" * 40)
    print("""123 Main Street
Suite 100
California
90210
United States""")
    print("-" * 40)


if __name__ == "__main__":
    execute()