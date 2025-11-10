#!/usr/bin/env python3
"""
Payment Entry Creation Hook

Hooks into Payment Entry creation from Sales Invoice to populate Thai tax fields
when using "Create > Payment" button from Sales Invoice.
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_payment_entry_with_thai_tax(dt, dn, **kwargs):
    """
    Enhanced get_payment_entry that populates Thai tax fields.
    This overrides the default get_payment_entry for Sales Invoices.
    """
    # Import the original function
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    
    # Filter out 'cmd' parameter that's automatically added by Frappe API calls
    filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'cmd'}
    
    # Call the original function to get the Payment Entry
    pe = get_payment_entry(dt, dn, **filtered_kwargs)
    
    # If this is a Sales Invoice, populate Thai tax fields
    if dt == "Sales Invoice" and pe.references:
        for ref in pe.references:
            if ref.reference_doctype == "Sales Invoice" and ref.reference_name == dn:
                # Fetch Thai tax data from the Sales Invoice
                thai_tax_data = _get_sales_invoice_thai_tax_data(dn)

                if thai_tax_data:
                    # Populate Thai tax fields in the reference
                    _populate_reference_thai_tax_fields(ref, thai_tax_data)

                    # Update summary fields in the Payment Entry
                    _update_payment_entry_thai_tax_summary(pe, thai_tax_data)

    # If this is a Purchase Invoice, populate Thai tax fields
    elif dt == "Purchase Invoice" and pe.references:
        for ref in pe.references:
            if ref.reference_doctype == "Purchase Invoice" and ref.reference_name == dn:
                # Fetch Thai tax data from the Purchase Invoice
                thai_tax_data = _get_purchase_invoice_thai_tax_data(dn)

                if thai_tax_data:
                    # Populate Payment Entry header fields for Purchase Invoice scenario
                    _populate_payment_entry_purchase_fields(pe, thai_tax_data)
    
    return pe


def _get_sales_invoice_thai_tax_data(invoice_name):
    """
    Fetch Thai tax data from a Sales Invoice.
    Returns dict with Thai tax information.
    """
    try:
        # Get Thai tax fields from Sales Invoice
        invoice_data = frappe.db.get_value(
            "Sales Invoice",
            invoice_name,
            [
                "custom_subject_to_retention",
                "custom_retention_amount", 
                "custom_retention",
                "subject_to_wht",
                "grand_total",
                "net_total_after_wht",
                "custom_withholding_tax",
                "custom_withholding_tax_amount",
                "taxes_and_charges",
                "vat_treatment"
            ],
            as_dict=True
        )
        
        print(f"DEBUG: Raw Sales Invoice data for {invoice_name}:")
        print(f"  - custom_withholding_tax (percentage): {invoice_data.get('custom_withholding_tax')}")
        print(f"  - custom_withholding_tax_amount (amount): {invoice_data.get('custom_withholding_tax_amount')}")
        print(f"  - grand_total: {invoice_data.get('grand_total')}")
        print(f"  - net_total_after_wht: {invoice_data.get('net_total_after_wht')}")
        print(f"  - subject_to_wht: {invoice_data.get('subject_to_wht')}")
        print(f"  - vat_treatment: {invoice_data.get('vat_treatment')}")
        print(f"  - taxes_and_charges: {invoice_data.get('taxes_and_charges')}")
        print(f"  - custom_subject_to_retention: {invoice_data.get('custom_subject_to_retention')}")
        print(f"  - custom_retention_amount: {invoice_data.get('custom_retention_amount')}")
        print(f"  - custom_retention: {invoice_data.get('custom_retention')}")

        if not invoice_data:
            print(f"ERROR: No invoice data found for {invoice_name}")
            return None
        
        # Check if custom_withholding_tax_amount exists and use it directly
        stored_wht_amount = invoice_data.get("custom_withholding_tax_amount", 0)
        
        if stored_wht_amount and stored_wht_amount > 0:
            # Use the stored amount directly
            wht_amount = stored_wht_amount
            wht_percentage = invoice_data.get("custom_withholding_tax", 0)
            print(f"DEBUG WHT Direct: Invoice {invoice_name}, Using stored WHT amount = {wht_amount}, WHT% = {wht_percentage}")
        else:
            # Fallback: Calculate from percentage
            wht_percentage = invoice_data.get("custom_withholding_tax", 0)
            net_total_after_wht = invoice_data.get("net_total_after_wht", 0)
            wht_amount = 0
            if wht_percentage > 0 and net_total_after_wht > 0:
                wht_amount = net_total_after_wht * (wht_percentage / 100)
                print(f"DEBUG WHT Calculated: Invoice {invoice_name}, WHT% = {wht_percentage}%, Net Total After WHT = {net_total_after_wht}, Calculated WHT Amount = {wht_amount}")
            else:
                print(f"DEBUG WHT Skip: Invoice {invoice_name}, WHT% = {wht_percentage}%, Net Total After WHT = {net_total_after_wht}")
        
        # Calculate VAT Undue amount from taxes_and_charges with VAT treatment context
        vat_undue_amount = _calculate_vat_undue_amount(invoice_name, invoice_data.get("taxes_and_charges", ""), invoice_data.get("vat_treatment", ""))
        
        # Convert to Payment Entry Reference field format
        thai_tax_data = {
            "has_retention": invoice_data.get("custom_subject_to_retention", 0),
            "retention_amount": invoice_data.get("custom_retention_amount", 0),
            "retention_percentage": invoice_data.get("custom_retention", 0),
            "has_wht": invoice_data.get("subject_to_wht", 0),
            "wht_amount": wht_amount,
            "wht_percentage": wht_percentage,
            "vat_undue_amount": vat_undue_amount,
            "vat_treatment": invoice_data.get("vat_treatment", "")  # Include VAT treatment info
        }

        print(f"DEBUG: Final thai_tax_data being returned for {invoice_name}:")
        print(f"  - has_retention: {thai_tax_data['has_retention']}")
        print(f"  - retention_amount: {thai_tax_data['retention_amount']}")
        print(f"  - has_wht: {thai_tax_data['has_wht']}")
        print(f"  - wht_amount: {thai_tax_data['wht_amount']}")
        print(f"  - wht_percentage: {thai_tax_data['wht_percentage']}")
        print(f"  - vat_undue_amount: {thai_tax_data['vat_undue_amount']}")

        return thai_tax_data
        
    except Exception as e:
        frappe.log_error(
            message=f"Error fetching Thai tax data for Sales Invoice {invoice_name}: {str(e)}",
            title="Payment Entry Thai Tax Data Fetch Error"
        )
        return None


def _get_purchase_invoice_thai_tax_data(invoice_name):
    """
    Fetch Thai tax data from a Purchase Invoice.
    Returns dict with Thai tax information for Payment Entry (Pay) scenario.
    """
    try:
        # Get Thai tax fields from Purchase Invoice
        invoice_data = frappe.db.get_value(
            "Purchase Invoice",
            invoice_name,
            [
                "subject_to_wht",
                "vat_treatment",
                "net_total_after_wht",
                "custom_withholding_tax",
                "custom_withholding_tax_amount",
                "apply_thai_wht_compliance",
                "wht_income_type",
                "wht_description",
                "grand_total",
                "net_total",  # Add net_total for tax base calculation
                "taxes_and_charges",
                "custom_subject_to_retention",  # Add retention checkbox
                "custom_retention",  # Add retention percentage
                "custom_retention_amount"  # Add retention amount
            ],
            as_dict=True
        )

        print(f"DEBUG: Raw Purchase Invoice data for {invoice_name}:")
        print(f"  - subject_to_wht: {invoice_data.get('subject_to_wht')}")
        print(f"  - vat_treatment: {invoice_data.get('vat_treatment')}")
        print(f"  - net_total_after_wht: {invoice_data.get('net_total_after_wht')}")
        print(f"  - custom_withholding_tax_amount: {invoice_data.get('custom_withholding_tax_amount')}")
        print(f"  - apply_thai_wht_compliance: {invoice_data.get('apply_thai_wht_compliance')}")
        print(f"  - custom_subject_to_retention: {invoice_data.get('custom_subject_to_retention')}")
        print(f"  - custom_retention: {invoice_data.get('custom_retention')}")
        print(f"  - custom_retention_amount: {invoice_data.get('custom_retention_amount')}")

        if not invoice_data:
            print(f"ERROR: No Purchase Invoice data found for {invoice_name}")
            return None

        # Convert to Payment Entry field format
        thai_tax_data = {
            "subject_to_wht": invoice_data.get("subject_to_wht", 0),
            "vat_treatment": invoice_data.get("vat_treatment", ""),
            "net_total_after_wht": invoice_data.get("net_total_after_wht", 0),
            "wht_amount": invoice_data.get("custom_withholding_tax_amount", 0),
            "wht_percentage": invoice_data.get("custom_withholding_tax", 0),
            "apply_thai_wht_compliance": invoice_data.get("apply_thai_wht_compliance", 0),
            "wht_income_type": invoice_data.get("wht_income_type", ""),
            "wht_description": invoice_data.get("wht_description", ""),
            "grand_total": invoice_data.get("grand_total", 0),
            "net_total": invoice_data.get("net_total", 0),  # Use net_total for tax base (before VAT)
            "custom_subject_to_retention": invoice_data.get("custom_subject_to_retention", 0),
            "custom_retention": invoice_data.get("custom_retention", 0),
            "custom_retention_amount": invoice_data.get("custom_retention_amount", 0)
        }

        print(f"DEBUG: Final Purchase Invoice thai_tax_data for {invoice_name}:")
        print(f"  - subject_to_wht: {thai_tax_data['subject_to_wht']}")
        print(f"  - vat_treatment: {thai_tax_data['vat_treatment']}")
        print(f"  - net_total_after_wht: {thai_tax_data['net_total_after_wht']}")
        print(f"  - wht_amount: {thai_tax_data['wht_amount']}")
        print(f"  - custom_subject_to_retention: {thai_tax_data['custom_subject_to_retention']}")
        print(f"  - custom_retention: {thai_tax_data['custom_retention']}")
        print(f"  - custom_retention_amount: {thai_tax_data['custom_retention_amount']}")

        return thai_tax_data

    except Exception as e:
        frappe.log_error(
            message=f"Error fetching Thai tax data for Purchase Invoice {invoice_name}: {str(e)}",
            title="Payment Entry Purchase Invoice Thai Tax Data Fetch Error"
        )
        return None


def _populate_payment_entry_purchase_fields(pe, thai_tax_data):
    """
    Populate Payment Entry header fields for Purchase Invoice (Pay) scenario.
    This copies Thai tax fields from Purchase Invoice to Payment Entry header.
    """
    if not thai_tax_data:
        return

    print(f"DEBUG: Populating Payment Entry header fields with Purchase Invoice data:")
    print(f"  - subject_to_wht: {thai_tax_data.get('subject_to_wht')}")
    print(f"  - vat_treatment: {thai_tax_data.get('vat_treatment')}")
    print(f"  - wht_amount: {thai_tax_data.get('wht_amount')}")
    print(f"  - wht_percentage: {thai_tax_data.get('wht_percentage')}")

    # Set the main Thai tax fields in Payment Entry (ERPNext standard fields)
    if hasattr(pe, 'subject_to_wht'):
        pe.subject_to_wht = thai_tax_data.get("subject_to_wht", 0)
        print(f"  - Set pe.subject_to_wht = {pe.subject_to_wht}")

    if hasattr(pe, 'vat_treatment'):
        pe.vat_treatment = thai_tax_data.get("vat_treatment", "")
        print(f"  - Set pe.vat_treatment = '{pe.vat_treatment}'")

    if hasattr(pe, 'net_total_after_wht'):
        pe.net_total_after_wht = thai_tax_data.get("net_total_after_wht", 0)
        print(f"  - Set pe.net_total_after_wht = {pe.net_total_after_wht}")

    # Set WHT fields (newly added custom fields)
    if hasattr(pe, 'custom_withholding_tax'):
        pe.custom_withholding_tax = thai_tax_data.get("wht_percentage", 0)
        print(f"  - Set pe.custom_withholding_tax = {pe.custom_withholding_tax}%")

    if hasattr(pe, 'custom_withholding_tax_amount'):
        pe.custom_withholding_tax_amount = thai_tax_data.get("wht_amount", 0)
        print(f"  - Set pe.custom_withholding_tax_amount = {pe.custom_withholding_tax_amount}")

    # Set income type and description from Purchase Invoice
    if hasattr(pe, 'wht_income_type') and thai_tax_data.get("wht_income_type"):
        pe.wht_income_type = thai_tax_data.get("wht_income_type", "")
        print(f"  - Set pe.wht_income_type = '{pe.wht_income_type}'")

    if hasattr(pe, 'wht_description') and thai_tax_data.get("wht_description"):
        pe.wht_description = thai_tax_data.get("wht_description", "")
        print(f"  - Set pe.wht_description = '{pe.wht_description}'")

    # Set WHT certificate required flag
    if hasattr(pe, 'wht_certificate_required'):
        pe.wht_certificate_required = 1 if thai_tax_data.get("subject_to_wht", 0) else 0
        print(f"  - Set pe.wht_certificate_required = {pe.wht_certificate_required}")

    # Set Thai compliance application flags if they exist
    if hasattr(pe, 'apply_thai_wht_compliance'):
        pe.apply_thai_wht_compliance = thai_tax_data.get("apply_thai_wht_compliance", 0)
        print(f"  - Set pe.apply_thai_wht_compliance = {pe.apply_thai_wht_compliance}")

    # Set Thai Compliance Tab fields (pd_custom_* fields)

    # Tax Base Amount (should be net_total, not grand_total)
    if hasattr(pe, 'pd_custom_tax_base_amount'):
        # Use net_total (before VAT) as tax base for WHT calculation
        pe.pd_custom_tax_base_amount = thai_tax_data.get("net_total", 0)
        print(f"  - Set pe.pd_custom_tax_base_amount = {pe.pd_custom_tax_base_amount} (net_total before VAT)")

    # WHT Certificate Number - Now only for Payment Entry (Receive) manual input
    # Note: pd_custom_wht_certificate_no is used for Payment Entry (Receive) - customer issued certificates
    # Payment Entry (Pay) uses pd_custom_wht_certificate (Link field) for our issued certificates
    # Skip auto-generation for pd_custom_wht_certificate_no field

    # Keep Buddhist Era year logic for when actual WHT Certificate is created
    # This will be used in the certificate creation process, not here
    # Format: WHTC-BBMM-##### where BB = Buddhist year (last 2 digits), MM = month
    # Example: WHTC-6809-00001 for September 2025 (2568 BE)

    # WHT Certificate Date - Use posting_date
    if hasattr(pe, 'pd_custom_wht_certificate_date'):
        pe.pd_custom_wht_certificate_date = pe.posting_date
        print(f"  - Set pe.pd_custom_wht_certificate_date = {pe.pd_custom_wht_certificate_date}")

    # WHT Rate - Copy from Purchase Invoice
    if hasattr(pe, 'pd_custom_withholding_tax_rate'):
        pe.pd_custom_withholding_tax_rate = thai_tax_data.get("wht_percentage", 0)
        print(f"  - Set pe.pd_custom_withholding_tax_rate = {pe.pd_custom_withholding_tax_rate}%")

    # WHT Amount - Already handled above via custom_withholding_tax_amount
    if hasattr(pe, 'pd_custom_withholding_tax_amount'):
        pe.pd_custom_withholding_tax_amount = thai_tax_data.get("wht_amount", 0)
        print(f"  - Set pe.pd_custom_withholding_tax_amount = {pe.pd_custom_withholding_tax_amount}")

    # Net Payment Amount - Calculate as grand_total - WHT amount
    if hasattr(pe, 'pd_custom_net_payment_amount'):
        grand_total = thai_tax_data.get("grand_total", 0)
        wht_amount = thai_tax_data.get("wht_amount", 0)
        pe.pd_custom_net_payment_amount = grand_total - wht_amount
        print(f"  - Set pe.pd_custom_net_payment_amount = {pe.pd_custom_net_payment_amount} (grand_total {grand_total} - WHT {wht_amount})")

    # Apply Withholding Tax flag
    if hasattr(pe, 'pd_custom_apply_withholding_tax'):
        pe.pd_custom_apply_withholding_tax = 1 if thai_tax_data.get("subject_to_wht", 0) else 0
        print(f"  - Set pe.pd_custom_apply_withholding_tax = {pe.pd_custom_apply_withholding_tax}")

    # Income Type for Thai Compliance Tab
    if hasattr(pe, 'pd_custom_income_type') and thai_tax_data.get("wht_income_type"):
        pe.pd_custom_income_type = thai_tax_data.get("wht_income_type", "")
        print(f"  - Set pe.pd_custom_income_type = '{pe.pd_custom_income_type}'")

    # Mark for WHT certificate creation if WHT amount exists
    if thai_tax_data.get("wht_amount", 0) > 0:
        # WHT certificate will be created based on pd_custom_apply_withholding_tax field
        print(f"  - WHT certificate will be created (WHT amount = {thai_tax_data.get('wht_amount')})")
    else:
        # No WHT certificate needed since no WHT amount
        print(f"  - No WHT certificate needed (no WHT amount)")

    # ============================================================================
    # RETENTION FIELDS DEBUG SECTION
    # ============================================================================
    print("\n" + "="*80)
    print("🔍 RETENTION CHECKBOX DEBUG - Payment Entry Population")
    print("="*80)
    
    # Get the raw value from thai_tax_data
    checkbox_value_raw = thai_tax_data.get("custom_subject_to_retention")
    retention_rate_raw = thai_tax_data.get("custom_retention")
    retention_amount_raw = thai_tax_data.get("custom_retention_amount")
    
    print(f"1. Raw values from Purchase Invoice:")
    print(f"   - custom_subject_to_retention (checkbox): {checkbox_value_raw} (type: {type(checkbox_value_raw)})")
    print(f"   - custom_retention (rate): {retention_rate_raw} (type: {type(retention_rate_raw)})")
    print(f"   - custom_retention_amount: {retention_amount_raw} (type: {type(retention_amount_raw)})")
    
    # Check if Payment Entry has the retention fields
    has_checkbox = hasattr(pe, 'custom_subject_to_retention')
    has_rate = hasattr(pe, 'custom_retention')
    has_amount = hasattr(pe, 'custom_retention_amount')
    
    print(f"\n2. Payment Entry field availability:")
    print(f"   - hasattr(pe, 'custom_subject_to_retention'): {has_checkbox}")
    print(f"   - hasattr(pe, 'custom_retention'): {has_rate}")
    print(f"   - hasattr(pe, 'custom_retention_amount'): {has_amount}")
    
    # Browser debug message for field availability
    frappe.msgprint(
        f"🔍 RETENTION DEBUG - Field Availability:<br><br>"
        f"<b>Raw Purchase Invoice Values:</b><br>"
        f"• Checkbox: {checkbox_value_raw} (type: {type(checkbox_value_raw).__name__})<br>"
        f"• Rate: {retention_rate_raw}<br>"
        f"• Amount: {retention_amount_raw}<br><br>"
        f"<b>Payment Entry Field Checks:</b><br>"
        f"• Has checkbox field: {has_checkbox}<br>"
        f"• Has rate field: {has_rate}<br>"
        f"• Has amount field: {has_amount}",
        indicator='orange',
        title="Retention Field Debug"
    )
    
    # Set retention checkbox from Purchase Invoice
    if has_checkbox:
        # Try multiple approaches to set the checkbox
        checkbox_value = int(checkbox_value_raw) if checkbox_value_raw else 0
        
        print(f"\n3. Setting checkbox field:")
        print(f"   - Converting {checkbox_value_raw} to integer: {checkbox_value}")
        print(f"   - Before setting: pe.custom_subject_to_retention = {getattr(pe, 'custom_subject_to_retention', 'NOT SET')}")
        
        # Set the value
        pe.custom_subject_to_retention = checkbox_value
        
        print(f"   - After setting: pe.custom_subject_to_retention = {pe.custom_subject_to_retention}")
        print(f"   - Verification: getattr(pe, 'custom_subject_to_retention') = {getattr(pe, 'custom_subject_to_retention', 'FAILED')}")
        
        # Browser message for checkbox setting
        frappe.msgprint(
            f"📝 CHECKBOX SETTING:<br><br>"
            f"• Raw value: {checkbox_value_raw}<br>"
            f"• Converted to: {checkbox_value}<br>"
            f"• Set pe.custom_subject_to_retention = {checkbox_value}<br>"
            f"• After setting: {getattr(pe, 'custom_subject_to_retention', 'FAILED')}",
            indicator='blue',
            title="Checkbox Setting"
        )
    else:
        print(f"\n3. ❌ CHECKBOX FIELD NOT FOUND on Payment Entry")
        frappe.msgprint(
            f"❌ ERROR: Payment Entry does not have 'custom_subject_to_retention' field!<br>"
            f"Field availability check returned: {has_checkbox}",
            indicator='red',
            title="Missing Field Error"
        )

    # Set retention rate from Purchase Invoice
    if has_rate:
        print(f"\n4. Setting retention rate field:")
        print(f"   - Before: pe.custom_retention = {getattr(pe, 'custom_retention', 'NOT SET')}")
        pe.custom_retention = thai_tax_data.get("custom_retention", 0)
        print(f"   - After: pe.custom_retention = {pe.custom_retention}%")
    else:
        print(f"\n4. ❌ RATE FIELD NOT FOUND on Payment Entry")

    # Set retention amount from Purchase Invoice
    if has_amount:
        print(f"\n5. Setting retention amount field:")
        print(f"   - Before: pe.custom_retention_amount = {getattr(pe, 'custom_retention_amount', 'NOT SET')}")
        pe.custom_retention_amount = thai_tax_data.get("custom_retention_amount", 0)
        print(f"   - After: pe.custom_retention_amount = {pe.custom_retention_amount}")
    else:
        print(f"\n5. ❌ AMOUNT FIELD NOT FOUND on Payment Entry")
    
    # Final verification
    print(f"\n6. FINAL VERIFICATION - All retention fields after setting:")
    print(f"   - custom_subject_to_retention: {getattr(pe, 'custom_subject_to_retention', 'NOT FOUND')}")
    print(f"   - custom_retention: {getattr(pe, 'custom_retention', 'NOT FOUND')}%")
    print(f"   - custom_retention_amount: {getattr(pe, 'custom_retention_amount', 'NOT FOUND')}")
    print("="*80 + "\n")
    
    # Final browser message
    frappe.msgprint(
        f"✅ FINAL RETENTION VALUES:<br><br>"
        f"<b>Payment Entry After Setting:</b><br>"
        f"• Checkbox: {getattr(pe, 'custom_subject_to_retention', 'NOT FOUND')}<br>"
        f"• Rate: {getattr(pe, 'custom_retention', 'NOT FOUND')}%<br>"
        f"• Amount: {getattr(pe, 'custom_retention_amount', 'NOT FOUND')} THB",
        indicator='green',
        title="Final Retention Values"
    )


def _calculate_vat_undue_amount(invoice_name, taxes_and_charges_template, vat_treatment=""):
    """
    Calculate VAT Undue amount from Sales Invoice taxes.
    
    In Thailand's service business, VAT occurs when payment is made.
    If taxes_and_charges template contains 'undue', 'ภาษีขายตั้งพัก', or 'ภาษีขายที่ไม่ถึงกำหนด',
    then all VAT amounts are VAT Undue amounts.
    
    Args:
        invoice_name: Sales Invoice name
        taxes_and_charges_template: Template name from taxes_and_charges field
        vat_treatment: VAT treatment status (VAT 7%, VAT 0%, VAT Exempt)
    
    Returns:
        float: Total VAT Undue amount
    """
    if not taxes_and_charges_template:
        return 0
    
    print(f"DEBUG VAT UNDUE: Processing invoice {invoice_name}")
    print(f"  - taxes_and_charges_template: '{taxes_and_charges_template}'")
    print(f"  - vat_treatment: '{vat_treatment}'")

    # Thai VAT Undue keywords
    vat_undue_keywords = ['undue', 'ภาษีขายตั้งพัก', 'ภาษีขายที่ไม่ถึงกำหนด']
    template_lower = taxes_and_charges_template.lower()

    # Check if template contains VAT Undue keywords
    is_vat_undue_template = any(keyword.lower() in template_lower for keyword in vat_undue_keywords)

    print(f"  - is_vat_undue_template: {is_vat_undue_template}")

    if not is_vat_undue_template:
        print(f"  - Template doesn't contain VAT Undue keywords, returning 0")
        return 0
    
    # Additional validation: Check VAT treatment status
    # Only process VAT Undue if VAT is applicable (not VAT Exempt or Zero-rated)
    if vat_treatment:
        vat_treatment_lower = vat_treatment.lower()
        if "exempt" in vat_treatment_lower or "zero-rated" in vat_treatment_lower:
            return 0  # No VAT Undue for VAT Exempt or Zero-rated Export invoices
    
    try:
        # Get all tax rows from the Sales Invoice
        tax_rows = frappe.db.get_all(
            "Sales Taxes and Charges",
            filters={
                "parent": invoice_name,
                "parenttype": "Sales Invoice"
            },
            fields=["account_head", "tax_amount", "description"]
        )
        
        total_vat_undue = 0
        
        # Log VAT treatment for debugging
        if vat_treatment:
            frappe.logger().debug(f"Processing VAT Undue for {invoice_name}: VAT Treatment = {vat_treatment}")
        
        for tax in tax_rows:
            # Check if this tax row is VAT (contains VAT keywords in account or description)
            account_head = tax.get("account_head", "").lower()
            description = tax.get("description", "").lower()
            
            # VAT indicators in account head or description
            vat_indicators = ['vat', 'ภาษีขาย', 'ภาพ']
            
            is_vat_row = any(indicator in account_head or indicator in description 
                           for indicator in vat_indicators)
            
            if is_vat_row and tax.get("tax_amount"):
                total_vat_undue += tax.get("tax_amount", 0)
        
        return total_vat_undue
        
    except Exception as e:
        frappe.log_error(
            message=f"Error calculating VAT Undue for {invoice_name}: {str(e)}",
            title="VAT Undue Calculation Error"
        )
        return 0


def _populate_reference_thai_tax_fields(ref, thai_tax_data):
    """
    Populate Thai tax fields in a Payment Entry Reference row.
    """
    if not thai_tax_data:
        return
    
    # Set retention fields
    ref.pd_custom_has_retention = thai_tax_data.get("has_retention", 0)
    ref.pd_custom_retention_amount = thai_tax_data.get("retention_amount", 0)
    ref.pd_custom_retention_percentage = thai_tax_data.get("retention_percentage", 0)
    
    # Set WHT fields
    ref.pd_custom_wht_amount = thai_tax_data.get("wht_amount", 0)
    ref.pd_custom_wht_percentage = thai_tax_data.get("wht_percentage", 0)
    
    # Set VAT fields
    ref.pd_custom_vat_undue_amount = thai_tax_data.get("vat_undue_amount", 0)
    
    # Calculate net payable amount (allocated amount minus deductions)
    net_payable = ref.allocated_amount or 0
    
    if ref.pd_custom_retention_amount:
        net_payable -= ref.pd_custom_retention_amount
    
    if ref.pd_custom_wht_amount:
        net_payable -= ref.pd_custom_wht_amount
    
    ref.pd_custom_net_payable_amount = net_payable


def _update_payment_entry_thai_tax_summary(pe, thai_tax_data):
    """
    Update Payment Entry summary fields based on Thai tax data.
    """
    if not thai_tax_data:
        return
    
    # Check if Payment Entry has the Thai tax summary fields
    retention_amount = thai_tax_data.get("retention_amount", 0)
    wht_amount = thai_tax_data.get("wht_amount", 0)
    vat_undue_amount = thai_tax_data.get("vat_undue_amount", 0)
    
    has_thai_taxes = bool(retention_amount or wht_amount or vat_undue_amount)
    
    # Set summary fields if they exist
    if hasattr(pe, 'pd_custom_has_thai_taxes'):
        pe.pd_custom_has_thai_taxes = 1 if has_thai_taxes else 0
    
    if hasattr(pe, 'pd_custom_has_retention'):
        pe.pd_custom_has_retention = 1 if retention_amount > 0 else 0
    
    if hasattr(pe, 'pd_custom_total_retention_amount'):
        pe.pd_custom_total_retention_amount = retention_amount
    
    if hasattr(pe, 'pd_custom_total_wht_amount'):
        pe.pd_custom_total_wht_amount = wht_amount
    
    if hasattr(pe, 'pd_custom_total_vat_undue_amount'):
        pe.pd_custom_total_vat_undue_amount = vat_undue_amount
    
    if hasattr(pe, 'pd_custom_net_payment_after_retention'):
        pe.pd_custom_net_payment_after_retention = (pe.total_allocated_amount or 0) - retention_amount
    
    # Set default accounts from Company settings if not already set
    _populate_default_thai_tax_accounts(pe)


def _populate_default_thai_tax_accounts(pe):
    """
    Populate default Thai tax accounts from Company settings if not already set.
    This ensures the Payment Entry has proper account defaults from the company.
    """
    if not pe.company:
        return
    
    try:
        # Get company default accounts
        company_data = frappe.db.get_value(
            "Company",
            pe.company,
            [
                "default_retention_account",
                "default_wht_account", 
                "default_output_vat_undue_account",
                "default_output_vat_account"
            ],
            as_dict=True
        )
        
        if not company_data:
            return
        
        # Set retention account if blank and company has default
        if hasattr(pe, 'pd_custom_retention_account') and not getattr(pe, 'pd_custom_retention_account', None):
            if company_data.get("default_retention_account"):
                pe.pd_custom_retention_account = company_data.get("default_retention_account")
        
        # Set WHT account if blank and company has default
        if hasattr(pe, 'pd_custom_wht_account') and not getattr(pe, 'pd_custom_wht_account', None):
            if company_data.get("default_wht_account"):
                pe.pd_custom_wht_account = company_data.get("default_wht_account")
        
        # Set VAT Undue account if blank and company has default
        if hasattr(pe, 'pd_custom_output_vat_undue_account') and not getattr(pe, 'pd_custom_output_vat_undue_account', None):
            if company_data.get("default_output_vat_undue_account"):
                pe.pd_custom_output_vat_undue_account = company_data.get("default_output_vat_undue_account")
        
        # Set VAT account if blank and company has default
        if hasattr(pe, 'pd_custom_output_vat_account') and not getattr(pe, 'pd_custom_output_vat_account', None):
            if company_data.get("default_output_vat_account"):
                pe.pd_custom_output_vat_account = company_data.get("default_output_vat_account")
                
    except Exception as e:
        frappe.log_error(
            message=f"Error populating default Thai tax accounts for Payment Entry: {str(e)}",
            title="Payment Entry Default Account Population Error"
        )