import frappe
from frappe.utils import flt

def check_payment_entry_gl(payment_entry_name="ACC-PAY-2025-00008"):
    """Debug GL entries for a specific Payment Entry"""

    # Get GL entries
    gl_entries = frappe.get_all(
        'GL Entry',
        filters={
            'voucher_type': 'Payment Entry',
            'voucher_no': payment_entry_name,
            'is_cancelled': 0
        },
        fields=['account', 'debit', 'credit', 'remarks', 'posting_date'],
        order_by='idx'
    )

    print(f'\n=== GL Entries for Payment Entry {payment_entry_name} ===')
    print(f'Total entries: {len(gl_entries)}\n')

    total_debit = 0
    total_credit = 0

    for idx, entry in enumerate(gl_entries, 1):
        debit = flt(entry.debit, 2)
        credit = flt(entry.credit, 2)
        total_debit += debit
        total_credit += credit

        print(f'{idx}. Account: {entry.account}')
        print(f'   Debit: ฿{debit:,.2f} | Credit: ฿{credit:,.2f}')
        print(f'   Remarks: {entry.remarks or "No remarks"}')
        print()

    print(f'\n=== TOTALS ===')
    print(f'Total Debit:  ฿{total_debit:,.2f}')
    print(f'Total Credit: ฿{total_credit:,.2f}')
    print(f'Difference:   ฿{abs(total_debit - total_credit):,.2f}')
    print(f'Balanced: {"✅ Yes" if total_debit == total_credit else "❌ No"}')

    # Get Payment Entry details
    try:
        pe = frappe.get_doc('Payment Entry', payment_entry_name)
        print(f'\n=== Payment Entry Details ===')
        print(f'Payment Type: {pe.payment_type}')
        print(f'Party: {pe.party}')
        print(f'Paid Amount: {pe.paid_amount}')
        print(f'Total Allocated: {pe.total_allocated_amount}')

        # Check Thai tax fields
        print(f'\n=== Thai Tax Configuration ===')
        print(f'pd_custom_has_thai_taxes: {getattr(pe, "pd_custom_has_thai_taxes", "Not found")}')
        print(f'pd_custom_total_wht_amount: {getattr(pe, "pd_custom_total_wht_amount", "Not found")}')
        print(f'pd_custom_total_retention_amount: {getattr(pe, "pd_custom_total_retention_amount", "Not found")}')
        print(f'pd_custom_total_vat_undue_amount: {getattr(pe, "pd_custom_total_vat_undue_amount", "Not found")}')

        # Check Thai tax accounts
        print(f'\n=== Thai Tax Accounts ===')
        print(f'pd_custom_wht_account: {getattr(pe, "pd_custom_wht_account", "Not found")}')
        print(f'pd_custom_retention_account: {getattr(pe, "pd_custom_retention_account", "Not found")}')
        print(f'pd_custom_output_vat_account: {getattr(pe, "pd_custom_output_vat_account", "Not found")}')
        print(f'pd_custom_output_vat_undue_account: {getattr(pe, "pd_custom_output_vat_undue_account", "Not found")}')

        # Check references
        if hasattr(pe, 'references') and pe.references:
            print(f'\n=== Payment Entry References ===')
            for ref in pe.references:
                if ref.reference_doctype == 'Sales Invoice':
                    print(f'\nInvoice: {ref.reference_name}')
                    print(f'  Allocated: ฿{ref.allocated_amount:,.2f}')
                    print(f'  WHT Amount: ฿{getattr(ref, "pd_custom_wht_amount", 0):,.2f}')
                    print(f'  Retention: ฿{getattr(ref, "pd_custom_retention_amount", 0):,.2f}')
                    print(f'  VAT Undue: ฿{getattr(ref, "pd_custom_vat_undue_amount", 0):,.2f}')
                    print(f'  Net Payable: ฿{getattr(ref, "pd_custom_net_payable_amount", 0):,.2f}')

    except Exception as e:
        print(f'\n❌ Error getting Payment Entry details: {str(e)}')

    return {
        'balanced': total_debit == total_credit,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'difference': abs(total_debit - total_credit)
    }