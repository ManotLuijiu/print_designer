#!/usr/bin/env python3

import frappe

def test_wht_service_system():
    """Test the complete Thailand WHT service system"""
    
    print("🧪 Testing Thailand WHT Service System...")
    print("=" * 50)
    
    # 1. Check if all required fields exist
    print("\n1. Checking Required Fields:")
    print("-" * 30)
    
    # Company fields
    company_fields = ['thailand_service_business', 'default_wht_account']
    for field in company_fields:
        exists = frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": field})
        status = "✅" if exists else "❌"
        print(f"{status} Company.{field}: {'Found' if exists else 'Missing'}")
    
    # Item field
    item_field_exists = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "is_service_item"})
    status = "✅" if item_field_exists else "❌"
    print(f"{status} Item.is_service_item: {'Found' if item_field_exists else 'Missing'}")
    
    # Sales Invoice fields
    si_fields = ['subject_to_wht', 'estimated_wht_amount', 'wht_certificate_required']
    for field in si_fields:
        exists = frappe.db.exists("Custom Field", {"dt": "Sales Invoice", "fieldname": field})
        status = "✅" if exists else "❌"
        print(f"{status} Sales Invoice.{field}: {'Found' if exists else 'Missing'}")
    
    # Payment Entry fields
    pe_fields = ['apply_wht', 'wht_rate', 'wht_amount', 'wht_account', 'net_payment_amount']
    for field in pe_fields:
        exists = frappe.db.exists("Custom Field", {"dt": "Payment Entry", "fieldname": field})
        status = "✅" if exists else "❌"
        print(f"{status} Payment Entry.{field}: {'Found' if exists else 'Missing'}")
    
    # 2. Check company settings
    print("\n2. Checking Company Settings:")
    print("-" * 30)
    
    companies = frappe.get_all("Company", fields=["name", "thailand_service_business"])
    if companies:
        for company in companies:
            status = "✅ Enabled" if company.thailand_service_business else "❌ Disabled"
            print(f"{company.name}: {status}")
    else:
        print("❌ No companies found!")
    
    # 3. Test WHT calculation function
    print("\n3. Testing WHT Calculation:")
    print("-" * 30)
    
    try:
        from print_designer.accounting.thailand_wht_integration import calculate_estimated_wht
        
        test_cases = [
            (100000, 3.0, 3000.0),  # 100K at 3% = 3K
            (50000, 3.0, 1500.0),   # 50K at 3% = 1.5K
            (0, 3.0, 0.0),          # 0 at 3% = 0
        ]
        
        for base_amount, rate, expected in test_cases:
            result = calculate_estimated_wht(base_amount, rate)
            status = "✅" if abs(result - expected) < 0.01 else "❌"
            print(f"{status} {base_amount:,} at {rate}% = {result:,.2f} (expected {expected:,.2f})")
            
    except Exception as e:
        print(f"❌ Error testing WHT calculation: {str(e)}")
    
    # 4. Check if Items exist for testing
    print("\n4. Checking Sample Items:")
    print("-" * 30)
    
    items = frappe.get_all("Item", fields=["name", "is_service_item"], limit=5)
    if items:
        for item in items:
            service_status = "Service" if item.get('is_service_item') else "Product"
            print(f"📦 {item.name}: {service_status}")
    else:
        print("❌ No items found!")
    
    print("\n" + "=" * 50)
    print("🎉 Thailand WHT Service System Test Complete!")
    print("\nTo test the full system:")
    print("1. Mark an Item as 'Is Service' in Item master")
    print("2. Create a Sales Invoice with that service item")
    print("3. Check if 'Subject to Withholding Tax' auto-enables")
    print("4. Verify WHT amount calculates correctly")

if __name__ == "__main__":
    test_wht_service_system()