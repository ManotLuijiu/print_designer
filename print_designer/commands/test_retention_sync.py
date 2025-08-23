# Test Company Retention Sync System

import frappe
from frappe import _


def test_retention_sync():
    """Test the Company to Company Retention Settings synchronization"""
    try:
        print("🧪 Testing Company Retention Sync System...")
        
        # Get the test company
        company_name = "Moo Coding"
        company = frappe.get_doc("Company", company_name)
        print(f"📊 Testing Company: {company.name}")
        
        # Check current retention fields in Company
        construction_service = getattr(company, 'construction_service', False)
        retention_rate = getattr(company, 'default_retention_rate', 0)
        retention_account = getattr(company, 'default_retention_account', None)
        
        print(f"📋 Current Company fields:")
        print(f"   construction_service: {construction_service}")
        print(f"   default_retention_rate: {retention_rate}")
        print(f"   default_retention_account: {retention_account}")
        
        # Check if Company Retention Settings exists
        settings_exists = frappe.db.exists("Company Retention Settings", company_name)
        print(f"📄 Company Retention Settings exists: {settings_exists}")
        
        if settings_exists:
            settings = frappe.get_doc("Company Retention Settings", company_name)
            print(f"📝 Company Retention Settings fields:")
            print(f"   construction_service_enabled: {settings.construction_service_enabled}")
            print(f"   default_retention_rate: {settings.default_retention_rate}")
            print(f"   retention_account: {settings.retention_account}")
            print(f"   auto_calculate_retention: {settings.auto_calculate_retention}")
            print(f"   maximum_retention_rate: {settings.maximum_retention_rate}")
        
        # Test 1: Update Company and see if it syncs to Settings
        print(f"\n🔄 Test 1: Company → Company Retention Settings sync")
        
        # Set test values
        company.construction_service = 1
        company.default_retention_rate = 8.0
        company.save()
        
        print(f"✅ Updated Company with construction_service=1, rate=8.0")
        
        # Check if it synced
        if frappe.db.exists("Company Retention Settings", company_name):
            updated_settings = frappe.get_doc("Company Retention Settings", company_name)
            print(f"📊 Sync result:")
            print(f"   Settings construction_service_enabled: {updated_settings.construction_service_enabled}")
            print(f"   Settings default_retention_rate: {updated_settings.default_retention_rate}")
            
            if updated_settings.construction_service_enabled == 1 and updated_settings.default_retention_rate == 8.0:
                print(f"✅ Company → Settings sync working!")
            else:
                print(f"❌ Company → Settings sync failed!")
        else:
            print(f"❌ Company Retention Settings not created during sync")
        
        # Test 2: Update Settings and see if it syncs back to Company
        print(f"\n🔄 Test 2: Company Retention Settings → Company sync")
        if frappe.db.exists("Company Retention Settings", company_name):
            settings = frappe.get_doc("Company Retention Settings", company_name)
            settings.default_retention_rate = 6.5
            settings.save()
            
            print(f"✅ Updated Settings with rate=6.5")
            
            # Reload company and check
            company.reload()
            updated_rate = getattr(company, 'default_retention_rate', 0)
            print(f"📊 Company default_retention_rate after settings update: {updated_rate}")
            
            if updated_rate == 6.5:
                print(f"✅ Settings → Company sync working!")
            else:
                print(f"❌ Settings → Company sync failed!")
        
        print(f"\n🎉 Sync system test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()


def check_retention_sync():
    """Check the current state of Company Retention sync without making changes"""
    try:
        print("🔍 Checking Company Retention Sync Status...")
        
        company_name = "Moo Coding"
        
        # Check Company fields
        if frappe.db.exists("Company", company_name):
            company = frappe.get_doc("Company", company_name)
            print(f"📊 Company '{company_name}':")
            print(f"   construction_service: {getattr(company, 'construction_service', 'Field not found')}")
            print(f"   default_retention_rate: {getattr(company, 'default_retention_rate', 'Field not found')}")
            print(f"   default_retention_account: {getattr(company, 'default_retention_account', 'Field not found')}")
        else:
            print(f"❌ Company '{company_name}' not found")
            return
        
        # Check Company Retention Settings
        if frappe.db.exists("Company Retention Settings", company_name):
            settings = frappe.get_doc("Company Retention Settings", company_name)
            print(f"📝 Company Retention Settings for '{company_name}':")
            print(f"   construction_service_enabled: {settings.construction_service_enabled}")
            print(f"   default_retention_rate: {settings.default_retention_rate}")
            print(f"   retention_account: {settings.retention_account}")
            print(f"   auto_calculate_retention: {settings.auto_calculate_retention}")
            print(f"   maximum_retention_rate: {settings.maximum_retention_rate}")
            print(f"   minimum_invoice_amount: {settings.minimum_invoice_amount}")
        else:
            print(f"📄 No Company Retention Settings found for '{company_name}'")
        
        # Check if our override is working
        try:
            from print_designer.overrides.company import CustomCompany
            print(f"✅ CustomCompany override class imported successfully")
        except ImportError as e:
            print(f"❌ CustomCompany override import failed: {e}")
        
        print(f"✅ Check completed!")
        
    except Exception as e:
        print(f"❌ Error during check: {str(e)}")
        import traceback
        traceback.print_exc()