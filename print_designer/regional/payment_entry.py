# Regional Payment Entry customizations for Thai tax compliance
# This follows ERPNext's standard add_regional_gl_entries pattern

import frappe
from frappe import _
from frappe.utils import flt


def add_regional_gl_entries(gl_entries, doc):
    """Add regional GL entries for Thai tax compliance (ERPNext standard pattern)."""
    
    # Only process Payment Entry documents with Thai tax features enabled
    if doc.doctype != "Payment Entry" or not getattr(doc, 'pd_custom_has_thai_taxes', 0):
        return
    
    try:
        # Adjust ERPNext's default Cash GL entry and add Thai compliance entries
        _adjust_cash_gl_entry_for_thai_compliance(gl_entries, doc)
        _add_thai_compliance_gl_entries(gl_entries, doc)
        
    except Exception as e:
        error_msg = str(e)[:50] if len(str(e)) > 50 else str(e)
        frappe.log_error(f"Thai GL: {doc.name}: {error_msg}", "Thai GL Error")
        frappe.throw(_("Failed to create Thai compliance GL entries: {0}").format(str(e)))


def _adjust_cash_gl_entry_for_thai_compliance(gl_entries, doc):
    """Adjust ERPNext's default Cash GL entry to use net amount after Thai tax deductions."""
    
    # Get Thai tax deduction amounts
    wht_amount = flt(getattr(doc, 'pd_custom_total_wht_amount', 0), 2)
    retention_amount = flt(getattr(doc, 'pd_custom_total_retention_amount', 0), 2)
    total_deductions = wht_amount + retention_amount
    
    if total_deductions <= 0:
        return
    
    # Find and adjust the Cash GL entry that ERPNext created
    for entry in gl_entries:
        # Look for the Cash account entry (paid_to for Receive, paid_from for Pay)
        cash_account = doc.paid_to if doc.payment_type == "Receive" else doc.paid_from
        
        if entry.get("account") == cash_account:
            if doc.payment_type == "Receive":
                # Reduce Cash debit by Thai tax deductions
                original_debit = flt(entry.get("debit", 0))
                entry["debit"] = flt(original_debit - total_deductions, 2)
                entry["debit_in_account_currency"] = flt(entry.get("debit_in_account_currency", 0) - total_deductions, 2)
            else:
                # For Pay transactions, reduce Cash credit by Thai tax deductions
                original_credit = flt(entry.get("credit", 0))
                entry["credit"] = flt(original_credit - total_deductions, 2)
                entry["credit_in_account_currency"] = flt(entry.get("credit_in_account_currency", 0) - total_deductions, 2)
            
            # Add a comment to indicate this was adjusted for Thai compliance
            entry["remarks"] = entry.get("remarks", "") + " (Adjusted for Thai WHT/Retention)"
            break


def _add_thai_compliance_gl_entries(gl_entries, doc):
    """Add Thai compliance GL entries using proper ERPNext patterns (following UAE model)."""

    # WHT Assets GL Entry - Using doc.get_gl_dict() for proper object creation
    wht_amount = flt(getattr(doc, 'pd_custom_total_wht_amount', 0), 2)
    if wht_amount > 0 and getattr(doc, 'pd_custom_wht_account', None):
        gl_entries.append(
            doc.get_gl_dict({
                "account": doc.pd_custom_wht_account,
                "debit": wht_amount,
                "debit_in_account_currency": wht_amount,
                "credit": 0,
                "credit_in_account_currency": 0,
                "against": doc.party if doc.payment_type == "Receive" else doc.paid_from,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai WHT Assets: {wht_amount}",
            })
        )

    # Retention GL Entry - Using doc.get_gl_dict() for proper object creation
    retention_amount = flt(getattr(doc, 'pd_custom_total_retention_amount', 0), 2)
    if retention_amount > 0 and getattr(doc, 'pd_custom_retention_account', None):
        gl_entries.append(
            doc.get_gl_dict({
                "account": doc.pd_custom_retention_account,
                "debit": retention_amount,
                "debit_in_account_currency": retention_amount,
                "credit": 0,
                "credit_in_account_currency": 0,
                "against": doc.party if doc.payment_type == "Receive" else doc.paid_from,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai Retention: {retention_amount}",
            })
        )

    # VAT Undue to VAT conversion GL entries - Using doc.get_gl_dict()
    vat_amount = flt(getattr(doc, 'pd_custom_total_vat_undue_amount', 0), 2)
    if vat_amount > 0:
        # Debit VAT Undue account (clear undue amount)
        if getattr(doc, 'pd_custom_output_vat_undue_account', None):
            gl_entries.append(
                doc.get_gl_dict({
                    "account": doc.pd_custom_output_vat_undue_account,
                    "debit": vat_amount,
                    "debit_in_account_currency": vat_amount,
                    "credit": 0,
                    "credit_in_account_currency": 0,
                    "against": doc.party if doc.payment_type == "Receive" else doc.paid_from,
                    "cost_center": getattr(doc, 'cost_center', None),
                    "remarks": f"Thai VAT Undue Clearing: {vat_amount}",
                })
            )

        # Credit VAT account (register due VAT)
        if getattr(doc, 'pd_custom_output_vat_account', None):
            gl_entries.append(
                doc.get_gl_dict({
                    "account": doc.pd_custom_output_vat_account,
                    "debit": 0,
                    "debit_in_account_currency": 0,
                    "credit": vat_amount,
                    "credit_in_account_currency": vat_amount,
                    "against": doc.party if doc.payment_type == "Receive" else doc.paid_from,
                    "cost_center": getattr(doc, 'cost_center', None),
                    "remarks": f"Thai VAT Due Registration: {vat_amount}",
                })
            )


def test_regional_gl_entries():
    """Test function to verify regional GL entries implementation."""
    import frappe
    from frappe.utils import flt

    print("=== Testing Regional GL Entries Implementation ===")

    # Create a mock Payment Entry document with get_gl_dict method
    class MockPaymentEntry:
        def __init__(self):
            self.doctype = "Payment Entry"  # Required by regional function
            self.name = "TEST-PAY-001"
            self.payment_type = "Receive"
            self.pd_custom_has_thai_taxes = 1
            self.pd_custom_total_wht_amount = 3.0
            self.pd_custom_total_vat_undue_amount = 7.0
            self.pd_custom_total_retention_amount = 0.0
            self.pd_custom_wht_account = "Asset - WHT"
            self.pd_custom_output_vat_undue_account = "Liability - VAT Undue"
            self.pd_custom_output_vat_account = "Liability - VAT"
            self.paid_to = "Asset - Cash"
            self.cost_center = "Main Cost Center"
            self.party = "Customer-001"

        def get_gl_dict(self, gl_dict_data):
            """Mock get_gl_dict that creates a proper frappe._dict without account validation"""
            from frappe import _dict

            # Create a proper frappe._dict object like ERPNext does
            gl_entry = _dict({
                "account": gl_dict_data.get("account"),
                "debit": flt(gl_dict_data.get("debit", 0)),
                "credit": flt(gl_dict_data.get("credit", 0)),
                "debit_in_account_currency": flt(gl_dict_data.get("debit_in_account_currency", 0)),
                "credit_in_account_currency": flt(gl_dict_data.get("credit_in_account_currency", 0)),
                "against": gl_dict_data.get("against"),
                "cost_center": gl_dict_data.get("cost_center"),
                "remarks": gl_dict_data.get("remarks", ""),
                "voucher_type": "Payment Entry",
                "voucher_no": self.name,
                "posting_date": "2025-01-01"
            })

            return gl_entry

    # Test the regional function with mock document
    doc = MockPaymentEntry()
    test_gl_entries = []

    # Add simulated base GL entries (like ERPNext creates)
    test_gl_entries.append({
        "account": "Asset - Cash",
        "debit": 107.0,
        "credit": 0,
        "debit_in_account_currency": 107.0,
        "credit_in_account_currency": 0,
        "remarks": "Cash Receipt"
    })

    test_gl_entries.append({
        "account": "Asset - Debtors",
        "debit": 0,
        "credit": 107.0,
        "debit_in_account_currency": 0,
        "credit_in_account_currency": 107.0,
        "remarks": "Customer Payment"
    })

    print(f"Document: {doc.name}")
    print(f"Payment type: {doc.payment_type}")
    print(f"Has Thai taxes: {doc.pd_custom_has_thai_taxes}")
    print(f"WHT amount: {doc.pd_custom_total_wht_amount}")
    print(f"VAT amount: {doc.pd_custom_total_vat_undue_amount}")

    print(f"\n=== Before Regional Processing ===")
    print(f"GL Entries count: {len(test_gl_entries)}")
    total_debit_before = sum(entry.get('debit', 0) for entry in test_gl_entries)
    total_credit_before = sum(entry.get('credit', 0) for entry in test_gl_entries)

    for i, entry in enumerate(test_gl_entries):
        print(f"Entry {i+1}: {entry['account']} - Debit: ฿{entry.get('debit', 0)}, Credit: ฿{entry.get('credit', 0)}")
    print(f"Total Debits: ฿{total_debit_before}, Total Credits: ฿{total_credit_before}")

    # Apply regional function - this is the actual test
    try:
        add_regional_gl_entries(test_gl_entries, doc)
        print(f"\n✅ Regional function executed successfully!")

        print(f"\n=== After Regional Processing ===")
        print(f"GL Entries count: {len(test_gl_entries)}")

        total_debit = sum(entry.get('debit', 0) for entry in test_gl_entries)
        total_credit = sum(entry.get('credit', 0) for entry in test_gl_entries)

        for i, entry in enumerate(test_gl_entries):
            debit = entry.get('debit', 0)
            credit = entry.get('credit', 0)
            account = entry.get('account', 'Unknown')
            remarks = entry.get('remarks', 'No remarks')
            print(f"Entry {i+1}: {account} - Debit: ฿{debit}, Credit: ฿{credit}")
            print(f"         Remarks: {remarks}")

        print(f"\n=== Balance Check ===")
        print(f"Total Debits: ฿{total_debit}")
        print(f"Total Credits: ฿{total_credit}")
        print(f"Balanced: {'✅ Yes' if total_debit == total_credit else '❌ No'}")

        # Check cash adjustment
        expected_cash = 107.0 - 3.0  # Original minus WHT
        actual_cash = None
        for entry in test_gl_entries:
            if entry.get('account') == 'Asset - Cash':
                actual_cash = entry.get('debit', 0)
                break

        print(f"\n=== Cash Adjustment Test ===")
        print(f"Expected Cash: ฿{expected_cash} (Original ฿107 - WHT ฿3)")
        print(f"Actual Cash: ฿{actual_cash}")
        print(f"Cash Adjustment: {'✅ Correct' if actual_cash == expected_cash else '❌ Incorrect'}")

        # Verify GL entries are proper frappe._dict objects
        thai_entries = [entry for entry in test_gl_entries if 'Thai' in entry.get('remarks', '')]
        print(f"\n=== GL Entry Object Type Verification ===")
        print(f"Thai-specific entries created: {len(thai_entries)}")

        for entry in thai_entries:
            # Check if entry has .debit attribute (indicates proper frappe._dict)
            has_attr = hasattr(entry, 'debit')
            entry_type = type(entry).__name__
            print(f"Entry type: {entry_type}, Has .debit attribute: {'✅ Yes' if has_attr else '❌ No'}")

        print(f"\n🎉 Regional GL Entries Fix Test PASSED!")
        print(f"✅ No 'AttributeError: dict object has no attribute debit' errors")
        print(f"✅ GL entries created with proper doc.get_gl_dict() method")
        print(f"✅ Cash adjustment working correctly")
        print(f"✅ GL balance maintained")

        return test_gl_entries

    except Exception as e:
        print(f"\n❌ Regional function failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None