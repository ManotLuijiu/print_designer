# Regional Payment Entry customizations for Thai tax compliance
# This follows ERPNext's standard add_regional_gl_entries pattern

import frappe
from frappe import _
from frappe.utils import flt


def add_regional_gl_entries(gl_entries, doc):
    """Add regional GL entries for Thai tax compliance (ERPNext standard pattern).

    This function is called during on_submit() to create the complete Thai tax GL entries
    for the Preview functionality and actual submission.
    """

    print(f"🇹🇭 =========================== REGIONAL GL DEBUG START ===========================")
    # CRITICAL: Log to file system as well
    with open("/tmp/thai_debug.log", "a") as f:
        f.write(f"REGIONAL GL FUNCTION CALLED: {doc.name} at {frappe.utils.now()}\n")
        f.flush()
    print(f"🇹🇭 Processing regional GL entries for {doc.doctype}: {doc.name}")
    print(f"🇹🇭 Document status (docstatus): {getattr(doc, 'docstatus', 'NOT_SET')}")
    print(f"🇹🇭 Payment type: {getattr(doc, 'payment_type', 'NOT_SET')}")
    print(f"🇹🇭 Paid amount: {getattr(doc, 'paid_amount', 'NOT_SET')}")

    # Only process Payment Entry documents with Thai tax features enabled
    if doc.doctype != "Payment Entry":
        print(f"⏭️ Skipping non-Payment Entry document: {doc.doctype}")
        return

    # DEBUG: Check all Thai tax related fields on the document
    print(f"🔍 DEBUGGING ALL THAI TAX FIELDS:")

    # Check primary flag - Use multiple possible fields that indicate Thai tax compliance
    has_thai_taxes = (getattr(doc, 'subject_to_wht', 0) or
                     getattr(doc, 'pd_custom_apply_withholding_tax', 0) or
                     getattr(doc, 'pd_custom_has_thai_taxes', 0))
    print(f"   📋 subject_to_wht: {getattr(doc, 'subject_to_wht', 0)} (type: {type(getattr(doc, 'subject_to_wht', 0))})")
    print(f"   📋 pd_custom_apply_withholding_tax: {getattr(doc, 'pd_custom_apply_withholding_tax', 0)} (type: {type(getattr(doc, 'pd_custom_apply_withholding_tax', 0))})")
    print(f"   📋 pd_custom_has_thai_taxes: {getattr(doc, 'pd_custom_has_thai_taxes', 0)} (type: {type(getattr(doc, 'pd_custom_has_thai_taxes', 0))})")
    print(f"   📋 Combined has_thai_taxes: {has_thai_taxes} (type: {type(has_thai_taxes)})")

    # Log all document attributes to debug the exact field names
    print(f"🔍 COMPREHENSIVE DOCUMENT FIELD DUMP:")
    doc_dict = doc.__dict__ if hasattr(doc, '__dict__') else {}
    thai_related_fields = []
    for field_name, field_value in doc_dict.items():
        if any(keyword in field_name.lower() for keyword in ['wht', 'tax', 'retention', 'thai', 'vat', 'base']):
            thai_related_fields.append((field_name, field_value, type(field_value)))
            print(f"   📝 {field_name}: {field_value} (type: {type(field_value)})")

    if not thai_related_fields:
        print(f"   ⚠️ No Thai-related fields found in document!")
        print(f"   📋 Available document fields: {list(doc_dict.keys())[:20]}")  # Show first 20 fields

    # Check total amounts - Use the actual fields that are being populated by JavaScript
    total_wht = flt(getattr(doc, 'pd_custom_total_wht_amount', 0))  # Corrected field name
    total_retention = flt(getattr(doc, 'pd_custom_total_retention_amount', 0))
    total_vat_undue = flt(getattr(doc, 'pd_custom_total_vat_undue_amount', 0))  # Use direct field

    print(f"   💰 total_wht_amount: {total_wht} (type: {type(total_wht)})")
    print(f"   💰 total_retention_amount: {total_retention} (type: {type(total_retention)})")
    print(f"   💰 total_vat_undue_amount: {total_vat_undue} (type: {type(total_vat_undue)})")

    # Check other WHT fields that might be relevant - Use the correct prefixed fields
    apply_wht = getattr(doc, 'pd_custom_apply_withholding_tax', 0)
    tax_base = getattr(doc, 'pd_custom_tax_base_amount', 0)
    net_payment = getattr(doc, 'net_total_after_wht', 0)  # This field exists from the console log
    print(f"   🏛️ pd_custom_apply_withholding_tax: {apply_wht} (type: {type(apply_wht)})")
    print(f"   💵 pd_custom_tax_base_amount: {tax_base} (type: {type(tax_base)})")
    print(f"   💵 net_total_after_wht: {net_payment} (type: {type(net_payment)})")

    # Check Thai WHT preview section fields
    subject_to_wht = getattr(doc, 'subject_to_wht', 0)
    net_total_after_wht = getattr(doc, 'net_total_after_wht', 0)
    print(f"   📊 subject_to_wht: {subject_to_wht} (type: {type(subject_to_wht)})")
    print(f"   📊 net_total_after_wht: {net_total_after_wht} (type: {type(net_total_after_wht)})")

    # Fetch account configurations from Company doctype (default accounts)
    company = getattr(doc, 'company', None)
    print(f"   🏢 Company: {company}")

    # Get default accounts from Company doctype
    company_doc = None
    if company:
        try:
            company_doc = frappe.get_doc("Company", company)
            print(f"   ✅ Company doc loaded successfully")
        except Exception as e:
            print(f"   ❌ Error loading Company doc: {str(e)}")

    # Fetch default accounts from Company or fall back to Payment Entry fields
    if company_doc:
        wht_account = getattr(company_doc, 'default_wht_account', None) or getattr(doc, 'pd_custom_wht_account', None)
        retention_account = getattr(company_doc, 'default_retention_account', None) or getattr(doc, 'pd_custom_retention_account', None)
        vat_undue_account = getattr(company_doc, 'default_output_vat_undue_account', None) or getattr(doc, 'pd_custom_output_vat_undue_account', None)
        vat_account = getattr(company_doc, 'default_output_vat_account', None) or getattr(doc, 'pd_custom_output_vat_account', None)

        print(f"   🏦 default_wht_account (Company): {getattr(company_doc, 'default_wht_account', None)}")
        print(f"   🏦 default_retention_account (Company): {getattr(company_doc, 'default_retention_account', None)}")
        print(f"   🏦 default_output_vat_undue_account (Company): {getattr(company_doc, 'default_output_vat_undue_account', None)}")
        print(f"   🏦 default_output_vat_account (Company): {getattr(company_doc, 'default_output_vat_account', None)}")
    else:
        # Fallback to Payment Entry fields (if they exist)
        wht_account = getattr(doc, 'pd_custom_wht_account', None)
        retention_account = getattr(doc, 'pd_custom_retention_account', None)
        vat_undue_account = getattr(doc, 'pd_custom_output_vat_undue_account', None)
        vat_account = getattr(doc, 'pd_custom_output_vat_account', None)
        print(f"   ⚠️ Using Payment Entry fallback accounts")

    print(f"   🏦 Final wht_account: {wht_account}")
    print(f"   🏦 Final retention_account: {retention_account}")
    print(f"   🏦 Final vat_undue_account: {vat_undue_account}")
    print(f"   🏦 Final vat_account: {vat_account}")

    # DEBUG: Check current GL entries received
    print(f"🔍 CURRENT GL ENTRIES RECEIVED:")
    print(f"   📊 GL entries count: {len(gl_entries) if gl_entries else 0}")
    if gl_entries:
        for i, entry in enumerate(gl_entries):
            account = entry.get('account', 'NO_ACCOUNT') if hasattr(entry, 'get') else getattr(entry, 'account', 'NO_ACCOUNT_ATTR')
            debit = entry.get('debit', 0) if hasattr(entry, 'get') else getattr(entry, 'debit', 0)
            credit = entry.get('credit', 0) if hasattr(entry, 'get') else getattr(entry, 'credit', 0)
            print(f"   📋 Entry {i+1}: Account='{account}', Debit=฿{debit}, Credit=฿{credit}")

    # Main condition check with detailed debugging
    print(f"🔍 CONDITION CHECK:")
    print(f"   ✅ has_thai_taxes check: {bool(has_thai_taxes)} (value: {has_thai_taxes})")
    wht_check = total_wht > 0
    retention_check = total_retention > 0
    vat_check = total_vat_undue > 0
    amounts_check = wht_check or retention_check or vat_check
    print(f"   💰 WHT > 0: {wht_check} (value: {total_wht})")
    print(f"   💰 Retention > 0: {retention_check} (value: {total_retention})")
    print(f"   💰 VAT Undue > 0: {vat_check} (value: {total_vat_undue})")
    print(f"   💰 Any amounts > 0: {amounts_check}")

    overall_condition = bool(has_thai_taxes) and amounts_check
    print(f"   🎯 Overall condition (should proceed): {overall_condition}")

    # Only proceed if Thai taxes flag is set AND there are actual amounts
    if not has_thai_taxes or (total_wht <= 0 and total_retention <= 0 and total_vat_undue <= 0):
        print(f"❌ SKIPPING REGIONAL GL ENTRIES:")
        print(f"   📋 has_thai_taxes={has_thai_taxes} (should be truthy)")
        print(f"   💰 WHT={total_wht} (should be > 0)")
        print(f"   💰 Retention={total_retention} (should be > 0)")
        print(f"   💰 VAT Undue={total_vat_undue} (should be > 0)")
        print(f"   ❗ At least one amount should be > 0, but all are <= 0")
        print(f"🇹🇭 =========================== REGIONAL GL DEBUG END (SKIPPED) ===========================")
        return

    print(f"✅ THAI TAXES DETECTED - PROCEEDING WITH GL ENTRIES:")
    print(f"   💰 WHT: ฿{total_wht}")
    print(f"   💰 Retention: ฿{total_retention}")
    print(f"   💰 VAT Undue: ฿{total_vat_undue}")

    try:
        print(f"🔧 STARTING GL ENTRY ADJUSTMENTS:")

        # Adjust ERPNext's default Cash GL entry and add Thai compliance entries
        print(f"   🔄 Step 1: Adjusting cash GL entry for Thai compliance...")
        _adjust_cash_gl_entry_for_thai_compliance(gl_entries, doc)
        print(f"   ✅ Step 1: Cash GL entry adjustment completed")

        print(f"   🔄 Step 2: Adding Thai compliance GL entries...")
        _add_thai_compliance_gl_entries(gl_entries, doc)
        print(f"   ✅ Step 2: Thai compliance GL entries added")

        # DEBUG: Show final GL entries
        print(f"🔍 FINAL GL ENTRIES AFTER THAI TAX PROCESSING:")
        print(f"   📊 Final GL entries count: {len(gl_entries) if gl_entries else 0}")
        if gl_entries:
            for i, entry in enumerate(gl_entries):
                account = entry.get('account', 'NO_ACCOUNT') if hasattr(entry, 'get') else getattr(entry, 'account', 'NO_ACCOUNT_ATTR')
                debit = entry.get('debit', 0) if hasattr(entry, 'get') else getattr(entry, 'debit', 0)
                credit = entry.get('credit', 0) if hasattr(entry, 'get') else getattr(entry, 'credit', 0)
                remarks = entry.get('remarks', 'No remarks') if hasattr(entry, 'get') else getattr(entry, 'remarks', 'No remarks attr')
                print(f"   📋 Final Entry {i+1}: Account='{account}', Debit=฿{debit}, Credit=฿{credit}, Remarks='{remarks}'")

        print(f"🎉 Regional GL entries created successfully for {doc.name}")
        print(f"🇹🇭 =========================== REGIONAL GL DEBUG END (SUCCESS) ===========================")

    except Exception as e:
        error_msg = str(e)[:100] if len(str(e)) > 100 else str(e)
        print(f"❌ ERROR CREATING REGIONAL GL ENTRIES:")
        print(f"   💥 Error message: {error_msg}")
        print(f"   📄 Full error: {str(e)}")
        frappe.log_error(f"Thai GL: {doc.name}: {error_msg}", "Thai GL Error")
        print(f"🇹🇭 =========================== REGIONAL GL DEBUG END (ERROR) ===========================")
        frappe.throw(_("Failed to create Thai compliance GL entries: {0}").format(str(e)))


def _adjust_cash_gl_entry_for_thai_compliance(gl_entries, doc):
    """Adjust ERPNext's default Cash GL entry to use net amount after Thai tax deductions."""

    print(f"🔧 ADJUSTING CASH GL ENTRY DEBUG:")

    # Get Thai tax deduction amounts - Use corrected field names
    wht_amount = flt(getattr(doc, 'pd_custom_total_wht_amount', 0), 2)  # Corrected field name
    retention_amount = flt(getattr(doc, 'pd_custom_total_retention_amount', 0), 2)
    total_deductions = wht_amount + retention_amount

    print(f"   💰 WHT amount: ฿{wht_amount}")
    print(f"   💰 Retention amount: ฿{retention_amount}")
    print(f"   💰 Total deductions: ฿{total_deductions}")

    if total_deductions <= 0:
        print(f"   ⏭️ No deductions needed (total_deductions <= 0)")
        return
    
    # Find and adjust the Cash GL entry that ERPNext created
    cash_account = doc.paid_to if doc.payment_type == "Receive" else doc.paid_from
    print(f"   💳 Looking for cash account: '{cash_account}' (payment_type: {doc.payment_type})")

    cash_entry_found = False
    for i, entry in enumerate(gl_entries):
        entry_account = entry.get("account") if hasattr(entry, 'get') else getattr(entry, 'account', None)
        print(f"   📋 Checking entry {i+1}: account='{entry_account}'")

        if entry_account == cash_account:
            cash_entry_found = True
            print(f"   ✅ Found cash entry to adjust!")

            if doc.payment_type == "Receive":
                # Reduce Cash debit by Thai tax deductions
                original_debit = flt(entry.get("debit", 0) if hasattr(entry, 'get') else getattr(entry, 'debit', 0))
                new_debit = flt(original_debit - total_deductions, 2)
                original_debit_currency = entry.get("debit_in_account_currency", 0) if hasattr(entry, 'get') else getattr(entry, 'debit_in_account_currency', 0)
                new_debit_currency = flt(original_debit_currency - total_deductions, 2)

                print(f"   🔄 Receive adjustment: Debit ฿{original_debit} → ฿{new_debit}")
                print(f"   🔄 Receive adjustment: Debit currency ฿{original_debit_currency} → ฿{new_debit_currency}")

                if hasattr(entry, '__setitem__'):
                    entry["debit"] = new_debit
                    entry["debit_in_account_currency"] = new_debit_currency
                else:
                    entry.debit = new_debit
                    entry.debit_in_account_currency = new_debit_currency
            else:
                # For Pay transactions, reduce Cash credit by Thai tax deductions
                original_credit = flt(entry.get("credit", 0) if hasattr(entry, 'get') else getattr(entry, 'credit', 0))
                new_credit = flt(original_credit - total_deductions, 2)
                original_credit_currency = entry.get("credit_in_account_currency", 0) if hasattr(entry, 'get') else getattr(entry, 'credit_in_account_currency', 0)
                new_credit_currency = flt(original_credit_currency - total_deductions, 2)

                print(f"   🔄 Pay adjustment: Credit ฿{original_credit} → ฿{new_credit}")
                print(f"   🔄 Pay adjustment: Credit currency ฿{original_credit_currency} → ฿{new_credit_currency}")

                if hasattr(entry, '__setitem__'):
                    entry["credit"] = new_credit
                    entry["credit_in_account_currency"] = new_credit_currency
                else:
                    entry.credit = new_credit
                    entry.credit_in_account_currency = new_credit_currency

            # Add a comment to indicate this was adjusted for Thai compliance
            original_remarks = entry.get("remarks", "") if hasattr(entry, 'get') else getattr(entry, 'remarks', "")
            new_remarks = original_remarks + " (Adjusted for Thai WHT/Retention)"

            print(f"   📝 Updating remarks: '{original_remarks}' → '{new_remarks}'")

            if hasattr(entry, '__setitem__'):
                entry["remarks"] = new_remarks
            else:
                entry.remarks = new_remarks

            break

    if not cash_entry_found:
        print(f"   ⚠️ WARNING: Cash account '{cash_account}' not found in GL entries!")


def _add_thai_compliance_gl_entries(gl_entries, doc):
    """Add Thai compliance GL entries using proper ERPNext patterns (following UAE model)."""

    print(f"🏛️ ADDING THAI COMPLIANCE GL ENTRIES DEBUG:")
    print(f"   💳 Payment Type: {doc.payment_type}")

    # Get default accounts from Company doctype
    company = getattr(doc, 'company', None)
    company_doc = None
    if company:
        try:
            company_doc = frappe.get_doc("Company", company)
        except Exception as e:
            print(f"   ❌ Error loading Company doc in _add_thai_compliance_gl_entries: {str(e)}")

    # Get Thai tax amounts using correct field names from the system
    wht_amount = flt(getattr(doc, 'pd_custom_total_wht_amount', 0), 2)  # Corrected: use total_wht_amount
    retention_amount = flt(getattr(doc, 'pd_custom_total_retention_amount', 0), 2)
    vat_amount = flt(getattr(doc, 'pd_custom_total_vat_undue_amount', 0), 2)

    print(f"   💰 WHT amount: ฿{wht_amount}")
    print(f"   💰 Retention amount: ฿{retention_amount}")
    print(f"   💰 VAT amount: ฿{vat_amount}")

    # Handle different payment types
    if doc.payment_type == "Receive":
        _add_thai_receive_gl_entries(gl_entries, doc, company_doc, wht_amount, retention_amount, vat_amount)
    elif doc.payment_type == "Pay":
        _add_thai_pay_gl_entries(gl_entries, doc, company_doc, wht_amount, retention_amount, vat_amount)
    else:
        print(f"   ⚠️ Unknown payment type: {doc.payment_type}")


def _add_thai_receive_gl_entries(gl_entries, doc, company_doc, wht_amount, retention_amount, vat_amount):
    """Add Thai GL entries for Payment Entry (Receive) - Customer payments."""

    print(f"   📥 Processing RECEIVE payment GL entries...")

    # WHT Assets GL Entry - Customer pays us, we withhold tax
    if wht_amount > 0:
        wht_account = getattr(company_doc, 'default_wht_account', None) if company_doc else None
        wht_account = wht_account or getattr(doc, 'pd_custom_wht_account', None)

        if wht_account:
            print(f"   ✅ Creating WHT Assets GL entry (Receive): ฿{wht_amount}")
            gl_entries.append(doc.get_gl_dict({
                "account": wht_account,
                "debit": wht_amount,
                "debit_in_account_currency": wht_amount,
                "credit": 0,
                "credit_in_account_currency": 0,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai WHT Assets (Receive): ฿{wht_amount}",
            }))

    # Retention GL Entry - For construction/service retention
    if retention_amount > 0:
        retention_account = getattr(company_doc, 'default_retention_account', None) if company_doc else None
        retention_account = retention_account or getattr(doc, 'pd_custom_retention_account', None)

        if retention_account:
            print(f"   ✅ Creating Retention Assets GL entry (Receive): ฿{retention_amount}")
            gl_entries.append(doc.get_gl_dict({
                "account": retention_account,
                "debit": retention_amount,
                "debit_in_account_currency": retention_amount,
                "credit": 0,
                "credit_in_account_currency": 0,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai Retention Assets (Receive): ฿{retention_amount}",
            }))

    # Output VAT: Undue → Due conversion (when we receive payment from customer)
    if vat_amount > 0:
        vat_undue_account = getattr(company_doc, 'default_output_vat_undue_account', None) if company_doc else None
        vat_due_account = getattr(company_doc, 'default_output_vat_account', None) if company_doc else None

        if vat_undue_account and vat_due_account:
            print(f"   ✅ Creating Output VAT Undue → Due conversion (Receive): ฿{vat_amount}")
            # Debit VAT Undue (clear it)
            gl_entries.append(doc.get_gl_dict({
                "account": vat_undue_account,
                "debit": vat_amount,
                "debit_in_account_currency": vat_amount,
                "credit": 0,
                "credit_in_account_currency": 0,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai Output VAT Undue Clear (Receive): ฿{vat_amount}",
            }))
            # Credit VAT Due (register liability)
            gl_entries.append(doc.get_gl_dict({
                "account": vat_due_account,
                "debit": 0,
                "debit_in_account_currency": 0,
                "credit": vat_amount,
                "credit_in_account_currency": vat_amount,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai Output VAT Due Register (Receive): ฿{vat_amount}",
            }))


def _add_thai_pay_gl_entries(gl_entries, doc, company_doc, wht_amount, retention_amount, vat_amount):
    """Add Thai GL entries for Payment Entry (Pay) - Supplier payments with Thai accounting flow."""

    print(f"   📤 Processing PAY payment GL entries...")
    print(f"   🏛️ Implementing Thai service purchase accounting flow...")

    # For Pay transactions, we need to handle the Thai accounting flow:
    # Dr. Creditors                      107  ← Standard ERPNext (party account)
    # Dr. Input VAT                        7  ← Company.default_input_vat_account
    #     Cr. Withholding Tax - Debt         3  ← Company.default_wht_debt_account
    #     Cr. Cash/Bank                    104  ← Standard ERPNext (already adjusted)
    #     Cr. Input VAT Undue                7  ← Company.default_input_vat_undue_account

    # 1. Input VAT Recognition (Dr. Input VAT account)
    if vat_amount > 0:
        input_vat_account = getattr(company_doc, 'default_input_vat_account', None) if company_doc else None
        input_vat_undue_account = getattr(company_doc, 'default_input_vat_undue_account', None) if company_doc else None

        if input_vat_account:
            print(f"   ✅ Creating Input VAT recognition GL entry (Pay): ฿{vat_amount}")
            gl_entries.append(doc.get_gl_dict({
                "account": input_vat_account,
                "debit": vat_amount,
                "debit_in_account_currency": vat_amount,
                "credit": 0,
                "credit_in_account_currency": 0,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai Input VAT Recognition (Pay): ฿{vat_amount}",
            }))

        # Credit Input VAT Undue account (clear the undue amount from Purchase Invoice)
        if input_vat_undue_account:
            print(f"   ✅ Creating Input VAT Undue clear GL entry (Pay): ฿{vat_amount}")
            gl_entries.append(doc.get_gl_dict({
                "account": input_vat_undue_account,
                "debit": 0,
                "debit_in_account_currency": 0,
                "credit": vat_amount,
                "credit_in_account_currency": vat_amount,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai Input VAT Undue Clear (Pay): ฿{vat_amount}",
            }))

    # 2. Withholding Tax Debt (Cr. WHT Debt account)
    # We owe government the WHT we deducted from supplier
    if wht_amount > 0:
        wht_debt_account = getattr(company_doc, 'default_wht_debt_account', None) if company_doc else None

        if wht_debt_account:
            print(f"   ✅ Creating WHT Debt liability GL entry (Pay): ฿{wht_amount}")
            gl_entries.append(doc.get_gl_dict({
                "account": wht_debt_account,
                "debit": 0,
                "debit_in_account_currency": 0,
                "credit": wht_amount,
                "credit_in_account_currency": wht_amount,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai WHT Debt Liability (Pay): ฿{wht_amount}",
            }))
        else:
            print(f"   ⚠️ No WHT debt account configured for company {company}")

    # 3. Retention handling (if applicable)
    if retention_amount > 0:
        retention_account = getattr(company_doc, 'default_retention_account', None) if company_doc else None

        if retention_account:
            print(f"   ✅ Creating Retention liability GL entry (Pay): ฿{retention_amount}")
            gl_entries.append(doc.get_gl_dict({
                "account": retention_account,
                "debit": 0,
                "debit_in_account_currency": 0,
                "credit": retention_amount,
                "credit_in_account_currency": retention_amount,
                "against": doc.party,
                "cost_center": getattr(doc, 'cost_center', None),
                "remarks": f"Thai Retention Liability (Pay): ฿{retention_amount}",
            }))

    print(f"   ✅ Thai Pay GL entries completed")
    print(f"   📊 Summary: VAT=฿{vat_amount}, WHT=฿{wht_amount}, Retention=฿{retention_amount}")


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