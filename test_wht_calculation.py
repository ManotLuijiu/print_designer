#!/usr/bin/env python3

import frappe
from print_designer.accounting.thailand_wht_integration import calculate_estimated_wht, get_company_wht_rate

def test_wht_calculation():
    """Test the WHT calculation function"""
    
    print("🧪 Testing WHT Calculation Function...")
    print("=" * 50)
    
    # Test 1: Direct calculation with rate
    print("\n1. Testing with specific rate:")
    result1 = calculate_estimated_wht(base_amount=100000, wht_rate=3.0)
    print(f"   100,000 at 3% = {result1} (expected: 3000.0)")
    
    # Test 2: Calculation with company parameter
    print("\n2. Testing with company parameter:")
    companies = frappe.get_all("Company", fields=["name"], limit=1)
    if companies:
        company_name = companies[0].name
        print(f"   Using company: {company_name}")
        
        # Get company's WHT rate
        company_rate = get_company_wht_rate(company_name)
        print(f"   Company WHT rate: {company_rate}%")
        
        # Calculate WHT
        result2 = calculate_estimated_wht(base_amount=100000, company=company_name)
        print(f"   100,000 with company rate = {result2}")
        
        # Manual verification
        expected = (100000 * company_rate) / 100
        print(f"   Expected: {expected}")
        
    else:
        print("   No companies found!")
    
    # Test 3: Test with zero amount
    print("\n3. Testing with zero amount:")
    result3 = calculate_estimated_wht(base_amount=0, wht_rate=3.0)
    print(f"   0 at 3% = {result3} (expected: 0)")
    
    # Test 4: Test various amounts
    print("\n4. Testing various amounts:")
    test_amounts = [50000, 150000, 250000]
    for amount in test_amounts:
        result = calculate_estimated_wht(base_amount=amount, wht_rate=3.0)
        expected = (amount * 3.0) / 100
        print(f"   {amount:,} at 3% = {result} (expected: {expected})")
    
    print("\n" + "=" * 50)
    print("🎉 WHT Calculation Test Complete!")

if __name__ == "__main__":
    test_wht_calculation()