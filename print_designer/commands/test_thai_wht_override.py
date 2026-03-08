"""
Test Thai WHT Override System
Validates that the override correctly calculates 10,000 x 3% = 300 (not 306)
"""

import frappe
from frappe.utils import flt
from frappe import _

def execute():
    """Test the Thai WHT override system with sample data"""

    print("🧪 Testing Thai WHT Override System")
    print("=" * 50)

    # Test data
    test_data = {
        "net_total": 10000.0,
        "wht_rate": 3.0,
        "expected_wht": 300.0
    }

    # Test the calculation function
    from print_designer.regional.purchase_order_wht_override import get_wht_calculation_base, calculate_thai_compliant_wht

    # Create a mock Purchase Order document
    mock_doc = frappe._dict({
        "name": "TEST-PO-001",
        "pd_custom_apply_thai_wht_compliance": 1,
        "pd_custom_subject_to_wht": 1,
        "net_total": test_data["net_total"],
        "base_net_total": test_data["net_total"],
        "total": test_data["net_total"],
        "grand_total": test_data["net_total"] * 1.07,  # With 7% VAT
        "pd_custom_withholding_tax_pct": test_data["wht_rate"],
        "currency": "THB",
        "items": [
            frappe._dict({"amount": 5000}),
            frappe._dict({"amount": 5000})
        ]
    })

    print(f"📊 Test Data:")
    print(f"   Net Total: ฿{test_data['net_total']:,.2f}")
    print(f"   WHT Rate: {test_data['wht_rate']}%")
    print(f"   Expected WHT: ฿{test_data['expected_wht']:,.2f}")
    print()

    # Test base amount calculation
    base_amount = get_wht_calculation_base(mock_doc)
    print(f"✅ Base Amount Calculation: ฿{base_amount:,.2f}")

    # Test Thai WHT calculation
    calculate_thai_compliant_wht(mock_doc)
    calculated_wht = flt(mock_doc.pd_custom_withholding_tax_amount)

    print(f"✅ Thai WHT Calculation: ฿{calculated_wht:,.2f}")
    print(f"✅ Final Payment Amount: ฿{flt(mock_doc.pd_custom_payment_amount):,.2f}")
    print()

    # Validation
    if calculated_wht == test_data["expected_wht"]:
        print("🎉 SUCCESS: Thai WHT Override works correctly!")
        print(f"   ✅ {test_data['net_total']:,.0f} × {test_data['wht_rate']}% = ฿{calculated_wht:,.2f}")
    else:
        print("❌ FAILED: Calculation mismatch!")
        print(f"   Expected: ฿{test_data['expected_wht']:,.2f}")
        print(f"   Got: ฿{calculated_wht:,.2f}")
        print(f"   Difference: ฿{abs(calculated_wht - test_data['expected_wht']):,.2f}")

    print()
    print("🔧 Testing Additional Scenarios:")

    # Test different amounts
    test_scenarios = [
        {"amount": 5000, "rate": 3, "expected": 150},
        {"amount": 20000, "rate": 5, "expected": 1000},
        {"amount": 15000, "rate": 1, "expected": 150},
        {"amount": 12345.67, "rate": 3, "expected": 370.37}
    ]

    for scenario in test_scenarios:
        mock_doc.net_total = scenario["amount"]
        mock_doc.pd_custom_withholding_tax_pct = scenario["rate"]

        calculate_thai_compliant_wht(mock_doc)
        result = flt(mock_doc.pd_custom_withholding_tax_amount)

        status = "✅" if result == scenario["expected"] else "❌"
        print(f"   {status} ฿{scenario['amount']:,.2f} × {scenario['rate']}% = ฿{result:,.2f} (expected: ฿{scenario['expected']:,.2f})")

    print()
    return True

@frappe.whitelist()
def test_purchase_order_wht_override():
    """API endpoint to test WHT override on a real Purchase Order"""

    # Find a test Purchase Order or create instructions
    purchase_orders = frappe.get_list(
        "Purchase Order",
        filters={"pd_custom_apply_thai_wht_compliance": 1, "docstatus": 0},
        limit=1
    )

    if not purchase_orders:
        return {
            "status": "no_test_data",
            "message": "No Purchase Orders with pd_custom_apply_thai_wht_compliance enabled found. Please create a test Purchase Order with Thai WHT enabled.",
            "instructions": [
                "1. Create a new Purchase Order",
                "2. Enable 'Apply Thai Withholding Tax Compliance' (pd_custom_apply_thai_wht_compliance)",
                "3. Add items with total amount = 10,000",
                "4. Set custom WHT rate to 3%",
                "5. Run this test again"
            ]
        }

    # Test with the found Purchase Order
    from print_designer.regional.purchase_order_wht_override import get_thai_wht_calculation_debug_info

    po_name = purchase_orders[0].name
    debug_info = get_thai_wht_calculation_debug_info(po_name)

    return {
        "status": "success",
        "purchase_order": po_name,
        "debug_info": debug_info
    }

if __name__ == "__main__":
    execute()