"""
Payment Entry Thai Tax Calculations

Handles Thai tax calculations (VAT + WHT + Retention) for Payment Entry when paying Sales Invoices.
Integrates with the construction service retention system and extends it for complete Thai tax compliance.

Thai Tax System Case Study: Project 100, VAT 7%, WHT 3%, Retention 5%
Sales Invoice: Dr. A/R 107, Cr. Income 100, Cr. Output VAT-Undue 7
Payment Entry: Dr. Cash 99, Dr. Retention 5, Dr. WHT 3, Dr. VAT-Undue 7, Cr. A/R 107, Cr. Output VAT 7

Key Functions:
1. calculate_retention_amounts - Enhanced for VAT + WHT + Retention calculations
2. create_retention_gl_entries - Enhanced for complete Thai tax GL entries
3. validate_retention_account - Enhanced for multi-tax account validation
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


def payment_entry_calculate_retention_amounts(doc, method=None):
    """Calculate Thai tax amounts (VAT + WHT + Retention) when Payment Entry references are updated."""
    
    if not doc.references:
        return
        
    # Check if any referenced invoices have Thai tax components
    total_retention = 0.0
    total_wht = 0.0
    total_vat_undue = 0.0
    has_thai_taxes = False
    thai_tax_details = []
    
    for ref in doc.references:
        thai_tax_info = _get_invoice_thai_tax_info(ref.reference_doctype, ref.reference_name)
        
        if thai_tax_info and thai_tax_info.get("has_thai_taxes"):
            has_thai_taxes = True
            
            # Get tax amounts from invoice
            retention_amount = flt(thai_tax_info.get("retention_amount", 0))
            wht_amount = flt(thai_tax_info.get("wht_amount", 0))
            vat_undue_amount = flt(thai_tax_info.get("vat_undue_amount", 0))
            
            outstanding_amount = flt(ref.outstanding_amount, 2)
            allocated_amount = flt(ref.allocated_amount, 2)
            
            # Calculate proportional amounts for allocated portion
            if outstanding_amount > 0:
                proportion = allocated_amount / outstanding_amount
                ref_retention_amount = flt(retention_amount * proportion, 2)
                ref_wht_amount = flt(wht_amount * proportion, 2)
                ref_vat_undue_amount = flt(vat_undue_amount * proportion, 2)
            else:
                ref_retention_amount = ref_wht_amount = ref_vat_undue_amount = 0.0
            
            # Update reference fields
            ref.pd_custom_has_retention = 1 if ref_retention_amount > 0 else 0
            ref.pd_custom_retention_amount = ref_retention_amount
            ref.pd_custom_retention_percentage = thai_tax_info.get("retention_percentage", 0)
            ref.pd_custom_wht_amount = ref_wht_amount
            ref.pd_custom_wht_percentage = thai_tax_info.get("wht_percentage", 0)
            ref.pd_custom_vat_undue_amount = ref_vat_undue_amount
            ref.pd_custom_net_payable_amount = flt(allocated_amount - ref_retention_amount - ref_wht_amount, 2)
            
            total_retention += ref_retention_amount
            total_wht += ref_wht_amount
            total_vat_undue += ref_vat_undue_amount
            
            thai_tax_details.append({
                "invoice": ref.reference_name,
                "retention_amount": ref_retention_amount,
                "retention_percentage": thai_tax_info.get("retention_percentage", 0),
                "wht_amount": ref_wht_amount,
                "wht_percentage": thai_tax_info.get("wht_percentage", 0),
                "vat_undue_amount": ref_vat_undue_amount
            })
        else:
            # No Thai taxes for this reference
            ref.pd_custom_has_retention = 0
            ref.pd_custom_retention_amount = 0.0
            ref.pd_custom_retention_percentage = 0.0
            ref.pd_custom_wht_amount = 0.0
            ref.pd_custom_wht_percentage = 0.0
            ref.pd_custom_vat_undue_amount = 0.0
            ref.pd_custom_net_payable_amount = flt(ref.allocated_amount, 2)
    
    # Update Payment Entry header fields
    doc.pd_custom_has_retention = 1 if total_retention > 0 else 0
    doc.pd_custom_has_thai_taxes = 1 if has_thai_taxes else 0
    doc.pd_custom_total_retention_amount = flt(total_retention, 2)
    doc.pd_custom_total_wht_amount = flt(total_wht, 2)
    doc.pd_custom_total_vat_undue_amount = flt(total_vat_undue, 2)
    
    # Calculate net payment after all Thai tax deductions
    total_deductions = total_retention + total_wht  # VAT doesn't reduce cash payment
    if doc.payment_type == "Pay":
        # For payments (to suppliers)
        doc.pd_custom_net_payment_after_retention = flt(doc.paid_amount - total_deductions, 2)
    else:
        # For receipts (from customers)  
        doc.pd_custom_net_payment_after_retention = flt(doc.received_amount - total_deductions, 2)
    
    # Set Thai tax accounts if not set
    if has_thai_taxes:
        _set_thai_tax_accounts(doc)
    
    # Generate comprehensive Thai tax note
    if thai_tax_details:
        doc.pd_custom_retention_note = _generate_thai_tax_note(thai_tax_details)


def _get_invoice_thai_tax_info(reference_doctype, reference_name):
    """Get comprehensive Thai tax information (VAT + WHT + Retention) from the referenced invoice."""
    
    if reference_doctype not in ["Sales Invoice", "Purchase Invoice"]:
        return None
    
    try:
        invoice = frappe.get_doc(reference_doctype, reference_name)
        
        # Initialize tax info structure
        tax_info = {
            "has_thai_taxes": False,
            "retention_amount": 0,
            "wht_amount": 0,
            "vat_undue_amount": 0,
            "retention_percentage": 0,
            "wht_percentage": 0
        }
        
        # Check for retention (existing system)
        if reference_doctype == "Sales Invoice":
            subject_to_retention = getattr(invoice, 'custom_subject_to_retention', 0)
            retention_amount = flt(getattr(invoice, 'custom_retention_amount', 0))
            retention_percentage = flt(getattr(invoice, 'custom_retention', 0))
            
            if subject_to_retention and retention_amount > 0:
                tax_info["has_thai_taxes"] = True
                tax_info["retention_amount"] = retention_amount
                tax_info["retention_percentage"] = retention_percentage
        
        # Check for WHT (existing system)
        subject_to_wht = getattr(invoice, 'subject_to_wht', 0)
        wht_amount = flt(getattr(invoice, 'custom_withholding_tax_amount', 0))
        
        if subject_to_wht and wht_amount > 0:
            tax_info["has_thai_taxes"] = True
            tax_info["wht_amount"] = wht_amount
            # Calculate WHT percentage from amount
            if invoice.net_total > 0:
                tax_info["wht_percentage"] = flt((wht_amount / invoice.net_total) * 100, 2)
        
        # Check for Output VAT - Undue (from Sales Taxes and Charges)
        vat_undue_amount = _get_output_vat_undue_amount(invoice)
        if vat_undue_amount > 0:
            tax_info["has_thai_taxes"] = True
            tax_info["vat_undue_amount"] = vat_undue_amount
        
        return tax_info
        
    except Exception as e:
        frappe.log_error(f"Error getting Thai tax info for {reference_name}: {str(e)}")
        return {"has_thai_taxes": False}


def _get_output_vat_undue_amount(invoice):
    """Extract Output VAT - Undue amount from Sales Taxes and Charges."""
    
    vat_undue_amount = 0.0
    
    try:
        # Look for tax charges with Output VAT - Undue account
        if hasattr(invoice, 'taxes') and invoice.taxes:
            for tax in invoice.taxes:
                account_head = getattr(tax, 'account_head', '')
                tax_amount = flt(getattr(tax, 'tax_amount', 0))
                
                # Check if this is Output VAT - Undue account
                if account_head and 'output vat' in account_head.lower() and 'undue' in account_head.lower():
                    vat_undue_amount += tax_amount
                elif account_head and 'vat' in account_head.lower() and 'undue' in account_head.lower():
                    vat_undue_amount += tax_amount
        
    except Exception as e:
        frappe.log_error(f"Error getting Output VAT Undue amount: {str(e)}")
    
    return flt(vat_undue_amount, 2)


def _get_company_retention_account(company):
    """Get the default retention account from company settings."""
    
    try:
        # Get from Company.default_retention_account (this field already exists)
        retention_account = frappe.db.get_value("Company", company, "default_retention_account")
        
        if retention_account:
            return retention_account
        
        # If not set, warn user to configure it
        frappe.msgprint(
            _("Please configure Default Retention Account in Company {0} settings").format(company),
            indicator="orange"
        )
        
        return None
        
    except Exception as e:
        frappe.log_error(f"Error getting retention account for {company}: {str(e)}")
        return None


def _set_thai_tax_accounts(doc):
    """Set default accounts for Thai tax processing."""
    
    try:
        company_doc = frappe.get_cached_doc("Company", doc.company)
        
        # Set retention account (existing system)
        if not getattr(doc, 'pd_custom_retention_account', None):
            doc.pd_custom_retention_account = getattr(company_doc, 'default_retention_account', None)
        
        # Set WHT account
        if not getattr(doc, 'pd_custom_wht_account', None):
            doc.pd_custom_wht_account = getattr(company_doc, 'default_wht_account', None)
        
        # Set VAT accounts
        if not getattr(doc, 'pd_custom_output_vat_undue_account', None):
            doc.pd_custom_output_vat_undue_account = getattr(company_doc, 'default_output_vat_undue_account', None)
        
        if not getattr(doc, 'pd_custom_output_vat_account', None):
            doc.pd_custom_output_vat_account = getattr(company_doc, 'default_output_vat_account', None)
            
    except Exception as e:
        frappe.log_error(f"Error setting Thai tax accounts: {str(e)}")


def _generate_thai_tax_note(thai_tax_details):
    """Generate comprehensive note about Thai tax calculations."""
    
    if not thai_tax_details:
        return ""
    
    note_lines = ["Thai Tax Details:"]
    
    for detail in thai_tax_details:
        invoice = detail['invoice']
        note_lines.append(f"\n• Invoice: {invoice}")
        
        if detail['retention_amount'] > 0:
            note_lines.append(f"  - Retention: {detail['retention_percentage']}% = ฿{detail['retention_amount']:,.2f}")
        
        if detail['wht_amount'] > 0:
            note_lines.append(f"  - WHT: {detail['wht_percentage']}% = ฿{detail['wht_amount']:,.2f}")
        
        if detail['vat_undue_amount'] > 0:
            note_lines.append(f"  - VAT Undue: ฿{detail['vat_undue_amount']:,.2f}")
    
    note_lines.append("\nRetention held as asset until project completion.")
    note_lines.append("WHT submitted to Revenue Department as tax credit.")
    note_lines.append("VAT Undue converted to Output VAT.")
    
    return "\n".join(note_lines)


def payment_entry_validate_retention(doc, method=None):
    """Validate Thai tax setup before submission."""
    
    if not getattr(doc, 'pd_custom_has_thai_taxes', 0):
        return
    
    # Validate required accounts are set
    required_accounts = []
    
    if getattr(doc, 'pd_custom_total_retention_amount', 0) > 0:
        if not getattr(doc, 'pd_custom_retention_account', None):
            required_accounts.append("Retention Account")
    
    if getattr(doc, 'pd_custom_total_wht_amount', 0) > 0:
        if not getattr(doc, 'pd_custom_wht_account', None):
            required_accounts.append("WHT Account")
    
    if getattr(doc, 'pd_custom_total_vat_undue_amount', 0) > 0:
        if not getattr(doc, 'pd_custom_output_vat_undue_account', None):
            required_accounts.append("Output VAT Undue Account")
        if not getattr(doc, 'pd_custom_output_vat_account', None):
            required_accounts.append("Output VAT Account")
    
    if required_accounts:
        frappe.throw(_("Required Thai tax accounts missing: {0}").format(", ".join(required_accounts)))
    
    # Validate account types and company
    _validate_thai_tax_accounts(doc)
    
    # Validate calculated amounts
    _validate_thai_tax_amounts(doc)


def _validate_thai_tax_accounts(doc):
    """Validate Thai tax account types and company."""
    
    validations = []
    
    # Retention account should be Asset/Receivable
    if getattr(doc, 'pd_custom_retention_account', None):
        validations.append({
            "account": doc.pd_custom_retention_account,
            "name": "Retention Account",
            "allowed_types": ["Asset", "Receivable"]
        })
    
    # WHT account should be Asset
    if getattr(doc, 'pd_custom_wht_account', None):
        validations.append({
            "account": doc.pd_custom_wht_account,
            "name": "WHT Account", 
            "allowed_types": ["Asset"]
        })
    
    # VAT accounts should be Liability
    if getattr(doc, 'pd_custom_output_vat_undue_account', None):
        validations.append({
            "account": doc.pd_custom_output_vat_undue_account,
            "name": "Output VAT Undue Account",
            "allowed_types": ["Liability"]
        })
    
    if getattr(doc, 'pd_custom_output_vat_account', None):
        validations.append({
            "account": doc.pd_custom_output_vat_account,
            "name": "Output VAT Account",
            "allowed_types": ["Liability"]
        })
    
    # Perform validations
    for validation in validations:
        try:
            account = frappe.get_doc("Account", validation["account"])
            
            if account.company != doc.company:
                frappe.throw(_("{0} must belong to the same company as the payment").format(validation["name"]))
            
            if account.account_type not in validation["allowed_types"]:
                frappe.throw(_("{0} must be of type: {1}").format(
                    validation["name"], 
                    " or ".join(validation["allowed_types"])
                ))
        
        except frappe.DoesNotExistError:
            frappe.throw(_("{0} does not exist: {1}").format(validation["name"], validation["account"]))


def _validate_thai_tax_amounts(doc):
    """Validate calculated Thai tax amounts."""
    
    # Validate retention amounts
    if getattr(doc, 'pd_custom_total_retention_amount', 0) > 0:
        total_calculated_retention = sum(flt(getattr(ref, 'pd_custom_retention_amount', 0), 2) 
                                        for ref in doc.references if getattr(ref, 'pd_custom_has_retention', 0))
        
        if abs(flt(doc.pd_custom_total_retention_amount, 2) - total_calculated_retention) > 0.01:
            frappe.throw(_("Total retention amount mismatch. Expected {0}, got {1}").format(
                frappe.format_value(total_calculated_retention, 'Currency'),
                frappe.format_value(doc.pd_custom_total_retention_amount, 'Currency')
            ))
    
    # Validate WHT amounts
    if getattr(doc, 'pd_custom_total_wht_amount', 0) > 0:
        total_calculated_wht = sum(flt(getattr(ref, 'pd_custom_wht_amount', 0), 2) 
                                 for ref in doc.references if getattr(ref, 'pd_custom_wht_amount', 0) > 0)
        
        if abs(flt(doc.pd_custom_total_wht_amount, 2) - total_calculated_wht) > 0.01:
            frappe.throw(_("Total WHT amount mismatch. Expected {0}, got {1}").format(
                frappe.format_value(total_calculated_wht, 'Currency'),
                frappe.format_value(doc.pd_custom_total_wht_amount, 'Currency')
            ))
    
    # Validate VAT amounts
    if getattr(doc, 'pd_custom_total_vat_undue_amount', 0) > 0:
        total_calculated_vat = sum(flt(getattr(ref, 'pd_custom_vat_undue_amount', 0), 2) 
                                 for ref in doc.references if getattr(ref, 'pd_custom_vat_undue_amount', 0) > 0)
        
        if abs(flt(doc.pd_custom_total_vat_undue_amount, 2) - total_calculated_vat) > 0.01:
            frappe.throw(_("Total VAT Undue amount mismatch. Expected {0}, got {1}").format(
                frappe.format_value(total_calculated_vat, 'Currency'),
                frappe.format_value(doc.pd_custom_total_vat_undue_amount, 'Currency')
            ))


def payment_entry_on_submit_create_retention_entries(doc, method=None):
    """Create comprehensive Thai tax GL entries on Payment Entry submission."""
    
    if not getattr(doc, 'pd_custom_has_thai_taxes', 0):
        return
    
    try:
        # Create retention GL entry (if applicable)
        if getattr(doc, 'pd_custom_total_retention_amount', 0) > 0:
            _create_retention_gl_entry(doc)
        
        # Create WHT GL entry (if applicable)
        if getattr(doc, 'pd_custom_total_wht_amount', 0) > 0:
            _create_wht_gl_entry(doc)
        
        # Create VAT processing GL entries (if applicable)
        if getattr(doc, 'pd_custom_total_vat_undue_amount', 0) > 0:
            _create_vat_gl_entries(doc)
        
        # Create comprehensive tracking record
        _create_retention_tracking_record(doc)
        
        # Show summary to user
        _show_thai_tax_summary(doc)
        
    except Exception as e:
        frappe.log_error(f"Error creating Thai tax GL entries for {doc.name}: {str(e)}")
        frappe.throw(_("Failed to create Thai tax GL entries: {0}").format(str(e)))


def _create_retention_gl_entry(doc):
    """Create GL entry for retention as asset (debit entry)."""
    
    from frappe.utils import get_link_to_form
    
    try:
        retention_amount = flt(doc.pd_custom_total_retention_amount, 2)
        
        if retention_amount <= 0:
            return
        
        # Create GL Entry for retention as asset (DEBIT side)
        # This matches: Dr. Construction Retention 5000, Cr. Accounts Receivable 100000
        gl_entry = frappe.new_doc("GL Entry")
        gl_entry.posting_date = doc.posting_date
        gl_entry.transaction_date = doc.posting_date
        gl_entry.account = doc.pd_custom_retention_account
        gl_entry.party_type = doc.party_type
        gl_entry.party = doc.party
        gl_entry.debit = retention_amount  # ✅ DEBIT - Retention is an asset we hold
        gl_entry.debit_in_account_currency = retention_amount
        gl_entry.credit = 0
        gl_entry.credit_in_account_currency = 0
        gl_entry.against = doc.paid_from if doc.payment_type == "Pay" else doc.paid_to
        gl_entry.voucher_type = doc.doctype
        gl_entry.voucher_no = doc.name
        gl_entry.remarks = f"Construction retention held for {doc.name}"
        gl_entry.is_opening = "No"
        gl_entry.company = doc.company
        gl_entry.finance_book = doc.finance_book
        
        gl_entry.insert(ignore_permissions=True)
        
        frappe.msgprint(_("Retention asset GL entry created: {0}").format(
            get_link_to_form("GL Entry", gl_entry.name)
        ))
        
    except Exception as e:
        frappe.log_error(f"Error creating retention GL entry for {doc.name}: {str(e)}")
        frappe.throw(_("Failed to create retention asset entry: {0}").format(str(e)))


def _create_wht_gl_entry(doc):
    """Create GL entry for WHT as asset (tax credit)."""
    
    from frappe.utils import get_link_to_form
    
    try:
        wht_amount = flt(doc.pd_custom_total_wht_amount, 2)
        
        if wht_amount <= 0:
            return
        
        # Create GL Entry for WHT as asset (DEBIT side)
        # Dr. WHT - Assets (tax credit we can claim from Revenue Department)
        gl_entry = frappe.new_doc("GL Entry")
        gl_entry.posting_date = doc.posting_date
        gl_entry.transaction_date = doc.posting_date
        gl_entry.account = doc.pd_custom_wht_account
        gl_entry.party_type = doc.party_type
        gl_entry.party = doc.party
        gl_entry.debit = wht_amount  # ✅ DEBIT - WHT is a tax credit asset
        gl_entry.debit_in_account_currency = wht_amount
        gl_entry.credit = 0
        gl_entry.credit_in_account_currency = 0
        gl_entry.against = doc.paid_from if doc.payment_type == "Pay" else doc.paid_to
        gl_entry.voucher_type = doc.doctype
        gl_entry.voucher_no = doc.name
        gl_entry.remarks = f"Thai WHT tax credit for {doc.name}"
        gl_entry.is_opening = "No"
        gl_entry.company = doc.company
        gl_entry.finance_book = doc.finance_book
        
        gl_entry.insert(ignore_permissions=True)
        
        frappe.msgprint(_("WHT tax credit GL entry created: {0}").format(
            get_link_to_form("GL Entry", gl_entry.name)
        ))
        
    except Exception as e:
        frappe.log_error(f"Error creating WHT GL entry for {doc.name}: {str(e)}")
        frappe.throw(_("Failed to create WHT tax credit entry: {0}").format(str(e)))


def _create_vat_gl_entries(doc):
    """Create GL entries for VAT processing (Undue → Due conversion)."""
    
    from frappe.utils import get_link_to_form
    
    try:
        vat_amount = flt(doc.pd_custom_total_vat_undue_amount, 2)
        
        if vat_amount <= 0:
            return
        
        # Entry 1: Dr. Output VAT - Undue (clear the undue amount)
        gl_entry_undue = frappe.new_doc("GL Entry")
        gl_entry_undue.posting_date = doc.posting_date
        gl_entry_undue.transaction_date = doc.posting_date
        gl_entry_undue.account = doc.pd_custom_output_vat_undue_account
        gl_entry_undue.party_type = doc.party_type
        gl_entry_undue.party = doc.party
        gl_entry_undue.debit = vat_amount  # ✅ DEBIT - Clear undue VAT
        gl_entry_undue.debit_in_account_currency = vat_amount
        gl_entry_undue.credit = 0
        gl_entry_undue.credit_in_account_currency = 0
        gl_entry_undue.against = doc.pd_custom_output_vat_account
        gl_entry_undue.voucher_type = doc.doctype
        gl_entry_undue.voucher_no = doc.name
        gl_entry_undue.remarks = f"Thai VAT Undue clearance for {doc.name}"
        gl_entry_undue.is_opening = "No"
        gl_entry_undue.company = doc.company
        gl_entry_undue.finance_book = doc.finance_book
        
        gl_entry_undue.insert(ignore_permissions=True)
        
        # Entry 2: Cr. Output VAT (register due VAT)
        gl_entry_due = frappe.new_doc("GL Entry")
        gl_entry_due.posting_date = doc.posting_date
        gl_entry_due.transaction_date = doc.posting_date
        gl_entry_due.account = doc.pd_custom_output_vat_account
        gl_entry_due.party_type = doc.party_type
        gl_entry_due.party = doc.party
        gl_entry_due.debit = 0
        gl_entry_due.debit_in_account_currency = 0
        gl_entry_due.credit = vat_amount  # ✅ CREDIT - Register due VAT
        gl_entry_due.credit_in_account_currency = vat_amount
        gl_entry_due.against = doc.pd_custom_output_vat_undue_account
        gl_entry_due.voucher_type = doc.doctype
        gl_entry_due.voucher_no = doc.name
        gl_entry_due.remarks = f"Thai VAT Due registration for {doc.name}"
        gl_entry_due.is_opening = "No"
        gl_entry_due.company = doc.company
        gl_entry_due.finance_book = doc.finance_book
        
        gl_entry_due.insert(ignore_permissions=True)
        
        frappe.msgprint(_("VAT processing GL entries created: {0} and {1}").format(
            get_link_to_form("GL Entry", gl_entry_undue.name),
            get_link_to_form("GL Entry", gl_entry_due.name)
        ))
        
    except Exception as e:
        frappe.log_error(f"Error creating VAT GL entries for {doc.name}: {str(e)}")
        frappe.throw(_("Failed to create VAT processing entries: {0}").format(str(e)))


def _show_thai_tax_summary(doc):
    """Show summary of Thai tax processing to user."""
    
    summary_lines = ["🇹🇭 Thai Tax Processing Complete:"]
    
    if getattr(doc, 'pd_custom_total_retention_amount', 0) > 0:
        summary_lines.append(f"✅ Retention: ฿{doc.pd_custom_total_retention_amount:,.2f} (held as asset)")
    
    if getattr(doc, 'pd_custom_total_wht_amount', 0) > 0:
        summary_lines.append(f"✅ WHT: ฿{doc.pd_custom_total_wht_amount:,.2f} (tax credit registered)")
    
    if getattr(doc, 'pd_custom_total_vat_undue_amount', 0) > 0:
        summary_lines.append(f"✅ VAT: ฿{doc.pd_custom_total_vat_undue_amount:,.2f} (converted Undue → Due)")
    
    net_payment = getattr(doc, 'pd_custom_net_payment_after_retention', 0)
    summary_lines.append(f"💰 Net Cash Payment: ฿{net_payment:,.2f}")
    
    frappe.msgprint(
        _("\n".join(summary_lines)),
        title=_("Thai Tax System Processing Complete"),
        indicator="green"
    )


def _create_retention_tracking_record(doc):
    """Create a record to track retention for future release."""
    
    try:
        # Create retention tracking document (if DocType exists)
        # This would be a custom DocType for tracking retention release
        
        retention_data = {
            "payment_entry": doc.name,
            "party_type": doc.party_type,
            "party": doc.party,
            "company": doc.company,
            "retention_amount": doc.pd_custom_total_retention_amount,
            "retention_date": doc.posting_date,
            "retention_account": doc.pd_custom_retention_account,
            "status": "Held",
            "remarks": doc.pd_custom_retention_note
        }
        
        # For now, just log the retention tracking info
        frappe.log_error(
            message=f"Retention tracking data: {retention_data}",
            title=f"Retention Tracking for {doc.name}"
        )
        
        # TODO: Create actual Retention Tracking DocType and insert record
        
    except Exception as e:
        frappe.log_error(f"Error creating retention tracking record for {doc.name}: {str(e)}")


def payment_entry_on_cancel_reverse_retention_entries(doc, method=None):
    """Reverse all Thai tax GL entries on Payment Entry cancellation."""
    
    if not getattr(doc, 'pd_custom_has_thai_taxes', 0):
        return
    
    try:
        # Find and cancel all Thai tax GL entries
        accounts_to_reverse = []
        
        if getattr(doc, 'pd_custom_retention_account', None):
            accounts_to_reverse.append(doc.pd_custom_retention_account)
        
        if getattr(doc, 'pd_custom_wht_account', None):
            accounts_to_reverse.append(doc.pd_custom_wht_account)
        
        if getattr(doc, 'pd_custom_output_vat_undue_account', None):
            accounts_to_reverse.append(doc.pd_custom_output_vat_undue_account)
        
        if getattr(doc, 'pd_custom_output_vat_account', None):
            accounts_to_reverse.append(doc.pd_custom_output_vat_account)
        
        # Reverse entries for each account
        total_reversed = 0
        for account in accounts_to_reverse:
            thai_tax_gl_entries = frappe.get_all("GL Entry",
                filters={
                    "voucher_type": doc.doctype,
                    "voucher_no": doc.name,
                    "account": account,
                    "is_cancelled": 0
                },
                fields=["name"]
            )
            
            for entry in thai_tax_gl_entries:
                gl_doc = frappe.get_doc("GL Entry", entry.name)
                gl_doc.is_cancelled = 1
                gl_doc.save(ignore_permissions=True)
                total_reversed += 1
        
        if total_reversed > 0:
            frappe.msgprint(_("Thai tax GL entries reversed: {0} entries").format(total_reversed))
        
    except Exception as e:
        frappe.log_error(f"Error reversing Thai tax GL entries for {doc.name}: {str(e)}")
        frappe.throw(_("Failed to reverse Thai tax entries: {0}").format(str(e)))