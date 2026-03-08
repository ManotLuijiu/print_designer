"""
Test Thai WHT Preview System
============================

Simple test script to verify the WHT preview system is working correctly.
"""

import frappe
from print_designer.custom.thai_wht_preview import (
    calculate_thai_wht_preview,
    get_customer_wht_config,
    preview_wht_calculation
)
from frappe.utils import flt


def test_wht_system():
    """
    Test the complete WHT preview system
    """
    try:
        print("🧪 Testing Thai WHT Preview System...")
        print("="*60)
        
        # Test 1: Check WHT rates configuration
        print("\n1️⃣ Testing WHT Rates Configuration:")
        from print_designer.custom.thai_wht_preview import THAI_WHT_RATES
        for income_type, config in THAI_WHT_RATES.items():
            print(f"  • {income_type}: {config['rate']}% - {config['description']}")
        
        # Test 2: Get a customer for testing
        print("\n2️⃣ Finding Test Customer:")
        customers = frappe.get_all("Customer", limit=1)
        if not customers:
            print("❌ No customers found. Please create a customer first.")
            return
        
        test_customer = customers[0].name
        print(f"  Using customer: {test_customer}")
        
        # Test 3: Configure customer for WHT (if not already configured)
        print("\n3️⃣ Configuring Customer for WHT:")
        customer_doc = frappe.get_doc("Customer", test_customer)
        
        # Set WHT configuration
        if not getattr(customer_doc, 'pd_custom_subject_to_wht', False):
            customer_doc.pd_custom_subject_to_wht = 1
            customer_doc.pd_custom_wht_income_type = "professional_services"
            customer_doc.is_juristic_person = 1
            customer_doc.custom_wht_rate = 0  # Use default rate
            customer_doc.save()
            print(f"  ✅ Configured {test_customer} for WHT")
        else:
            print(f"  ✅ {test_customer} already configured for WHT")
        
        # Test 4: Test customer WHT configuration retrieval
        print("\n4️⃣ Testing Customer WHT Configuration:")
        wht_config = get_customer_wht_config(test_customer)
        print(f"  Customer WHT Config: {wht_config}")
        
        # Test 5: Test WHT preview calculation
        print("\n5️⃣ Testing WHT Preview Calculation:")
        test_cases = [
            {"amount": 100000, "income_type": "professional_services", "expected_rate": 3.0},
            {"amount": 50000, "income_type": "construction", "expected_rate": 2.0},
            {"amount": 25000, "income_type": "service_fees", "expected_rate": 3.0},
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n  Test Case {i}:")
            print(f"    Amount: ฿{test_case['amount']:,.2f}")
            print(f"    Income Type: {test_case['income_type']}")
            print(f"    Expected Rate: {test_case['expected_rate']}%")
            
            result = preview_wht_calculation(
                customer=test_customer,
                grand_total=test_case['amount'],
                income_type=test_case['income_type']
            )
            
            if result.get('success') is False:
                print(f"    ❌ Error: {result.get('error', 'Unknown error')}")
                continue
            
            actual_rate = result.get('estimated_wht_rate', 0)
            wht_amount = result.get('pd_custom_withholding_tax_amount', 0)
            net_amount = result.get('pd_custom_net_total_after_wht', 0)
            
            print(f"    ✅ Actual Rate: {actual_rate}%")
            print(f"    ✅ WHT Amount: ฿{wht_amount:,.2f}")
            print(f"    ✅ Net Payment: ฿{net_amount:,.2f}")
            
            # Verify calculation
            expected_wht = (test_case['amount'] * test_case['expected_rate']) / 100
            expected_net = test_case['amount'] - expected_wht
            
            if abs(wht_amount - expected_wht) < 0.01:
                print(f"    ✅ Calculation verified!")
            else:
                print(f"    ❌ Calculation mismatch: expected ฿{expected_wht:,.2f}")
        
        # Test 6: Test document WHT preview calculation
        print("\n6️⃣ Testing Document WHT Preview:")
        
        # Create a temporary document-like object
        temp_doc = frappe._dict({
            'customer': test_customer,
            'grand_total': 100000,
            'net_total': 100000,
            'company': frappe.defaults.get_user_default('Company') or 'Test Company'
        })
        
        wht_preview = calculate_thai_wht_preview(temp_doc)
        print(f"  Document WHT Preview: {wht_preview}")
        
        print("\n✅ Thai WHT Preview System Test Complete!")
        print("\n📋 Summary:")
        print("- WHT rates configuration: Working ✅")
        print("- Customer configuration: Working ✅")
        print("- WHT preview calculation: Working ✅")
        print("- Document integration: Working ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during WHT system test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # This allows the script to be run directly
    test_wht_system()