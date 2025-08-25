"""
Thai WHT Preview System Installation Commands
============================================

Command-line utilities for installing and managing the Thai Withholding Tax
preview system for sales documents.
"""

import click
import frappe
from frappe.commands import pass_context


@click.command("install-thai-wht-preview")
@pass_context
def install_thai_wht_preview(context):
    """
    Install Thai WHT preview system
    
    Usage:
        bench --site [site-name] install-thai-wht-preview
    """
    import frappe
    from print_designer.custom.thai_wht_custom_fields import install_complete_wht_system
    from print_designer.custom.thai_wht_preview import get_thai_wht_rates
    
    frappe.init(site=context.sites[0])
    frappe.connect()
    
    try:
        print("🚀 Installing Thai WHT Preview System...")
        print("="*60)
        
        # Install complete WHT system (customer + sales document fields)
        install_complete_wht_system()
        
        print("\n✅ Thai WHT Preview System Installation Complete!")
        print("\n📋 System Features:")
        print("- Customer WHT configuration fields")
        print("- WHT preview fields on Quotation, Sales Order, Sales Invoice")
        print("- Automatic WHT calculations")
        print("- Thai language support")
        
        print("\n🎯 Available WHT Rates:")
        wht_rates = get_thai_wht_rates()
        for income_type, config in wht_rates.items():
            print(f"  • {config['description']}: {config['rate']}%")
        
        print("\n📖 Next Steps:")
        print("1. Configure customer WHT settings in Customer forms")
        print("2. Test WHT preview on sales documents")
        print("3. Customize print formats to show WHT information")
        print("4. Run: bench --site [site-name] check-thai-wht-preview")
        
    except Exception as e:
        print(f"❌ Error installing Thai WHT preview system: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


@click.command("check-thai-wht-preview")
@pass_context
def check_thai_wht_preview(context):
    """
    Check Thai WHT preview system installation
    
    Usage:
        bench --site [site-name] check-thai-wht-preview
    """
    import frappe
    from print_designer.custom.thai_wht_custom_fields import check_complete_wht_system
    
    frappe.init(site=context.sites[0])
    frappe.connect()
    
    try:
        print("🔍 Checking Thai WHT Preview System...")
        print("="*60)
        
        check_complete_wht_system()
        
        print("\n📊 System Check Complete!")
        
    except Exception as e:
        print(f"❌ Error checking Thai WHT preview system: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


@click.command("remove-thai-wht-preview")
@pass_context
def remove_thai_wht_preview(context):
    """
    Remove Thai WHT preview system (for testing/cleanup)
    
    Usage:
        bench --site [site-name] remove-thai-wht-preview
    """
    import frappe
    from print_designer.custom.thai_wht_custom_fields import remove_wht_preview_fields
    
    frappe.init(site=context.sites[0])
    frappe.connect()
    
    try:
        print("🗑️  Removing Thai WHT Preview System...")
        print("="*60)
        
        # Confirm removal
        confirm = input("Are you sure you want to remove all WHT preview fields? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Removal cancelled.")
            return
        
        remove_wht_preview_fields()
        
        print("\n✅ Thai WHT Preview System removed successfully!")
        
    except Exception as e:
        print(f"❌ Error removing Thai WHT preview system: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


@click.command("test-thai-wht-preview")
@pass_context
def test_thai_wht_preview(context):
    """
    Test Thai WHT preview calculations
    
    Usage:
        bench --site [site-name] test-thai-wht-preview
    """
    import frappe
    from print_designer.custom.thai_wht_preview import preview_wht_calculation
    
    frappe.init(site=context.sites[0])
    frappe.connect()
    
    try:
        print("🧪 Testing Thai WHT Preview Calculations...")
        print("="*60)
        
        # Test with sample data
        test_cases = [
            {"customer": None, "grand_total": 100000, "income_type": "professional_services"},
            {"customer": None, "grand_total": 50000, "income_type": "construction"},
            {"customer": None, "grand_total": 25000, "income_type": "service_fees"},
        ]
        
        # Get first customer for testing
        customers = frappe.get_all("Customer", limit=1)
        if not customers:
            print("⚠️  No customers found. Please create a customer first.")
            return
        
        test_customer = customers[0].name
        print(f"📋 Using test customer: {test_customer}")
        
        for i, test_case in enumerate(test_cases, 1):
            test_case["customer"] = test_customer
            print(f"\n🧪 Test Case {i}:")
            print(f"  Customer: {test_case['customer']}")
            print(f"  Amount: ฿{test_case['grand_total']:,.2f}")
            print(f"  Income Type: {test_case['income_type']}")
            
            result = preview_wht_calculation(**test_case)
            
            if result.get('success'):
                print(f"  ✅ WHT Rate: {result.get('estimated_wht_rate', 0)}%")
                print(f"  ✅ WHT Amount: ฿{result.get('estimated_wht_amount', 0):,.2f}")
                print(f"  ✅ Net Payment: ฿{result.get('net_total_after_wht', 0):,.2f}")
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
        
        print("\n✅ Thai WHT Preview Testing Complete!")
        
    except Exception as e:
        print(f"❌ Error testing Thai WHT preview: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


@click.command("refresh-wht-preview")
@click.option("--customer", help="Refresh for specific customer")
@click.option("--company", help="Refresh for specific company")
@pass_context
def refresh_wht_preview(context, customer=None, company=None):
    """
    Refresh WHT preview for existing documents
    
    Usage:
        bench --site [site-name] refresh-wht-preview
        bench --site [site-name] refresh-wht-preview --customer "Customer Name"
    """
    import frappe
    from print_designer.custom.thai_wht_events import bulk_refresh_wht_preview
    
    frappe.init(site=context.sites[0])
    frappe.connect()
    
    try:
        print("🔄 Refreshing WHT Preview for Existing Documents...")
        print("="*60)
        
        if customer:
            print(f"📋 Filter: Customer = {customer}")
        if company:
            print(f"📋 Filter: Company = {company}")
        
        updated_count = bulk_refresh_wht_preview(customer=customer, company=company)
        
        print(f"\n✅ Refreshed WHT preview for {updated_count} documents!")
        
    except Exception as e:
        print(f"❌ Error refreshing WHT preview: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


# Register commands with Click
commands = [
    install_thai_wht_preview,
    check_thai_wht_preview,
    remove_thai_wht_preview,
    test_thai_wht_preview,
    refresh_wht_preview,
]