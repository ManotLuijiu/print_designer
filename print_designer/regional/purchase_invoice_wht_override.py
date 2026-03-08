"""
Thai WHT Calculation Override for Purchase Invoice
Prevents ERPNext standard Tax Withholding Category interference
and provides precise Thai-compliant WHT calculations
"""

import frappe
from frappe.utils import flt, cint
from frappe import _


@frappe.whitelist()
def override_purchase_invoice_wht_calculation(doc, method=None):
    """
    Override ERPNext's standard WHT calculation for Thai compliance.
    Auto-populate values from Purchase Order and bill fields.
    Called via hooks to intercept and replace standard ERPNext WHT logic.

    Args:
        doc: Purchase Invoice document
        method: Hook method name
    """

    # STEP 1: Auto-populate fields from Purchase Order and bill fields
    auto_populate_from_purchase_order(doc)

    # STEP 2: Only process WHT calculation if Thai WHT system is enabled
    if not getattr(doc, "pd_custom_apply_thai_wht_compliance", 0) or not getattr(doc, "pd_custom_subject_to_wht", 0):
        return

    # STEP 3: Prevent ERPNext's standard Tax Withholding Category calculation
    disable_standard_wht_calculation(doc)

    # STEP 4: Apply Thai-specific WHT calculation
    calculate_thai_compliant_wht(doc)

    frappe.logger().info(f"Thai WHT Override applied to Purchase Invoice {doc.name}")

    # Handle cash purchase (is_paid) workflow - populate compliance section
    if getattr(doc, "is_paid", 0):
        _populate_compliance_section_fields(doc)


@frappe.whitelist()
def populate_compliance_section_from_preview(doc=None, docname=None):
    """
    Populate pd_custom_tax_compliance_section fields from pd_custom_wht_preview_section
    Only when is_paid (cash purchase) is enabled
    """

    # Handle both document object and document name
    if isinstance(doc, str):
        # If doc is a JSON string, parse it
        import json

        doc = frappe._dict(json.loads(doc))
    elif docname:
        # If docname is provided, get the document
        doc = frappe.get_doc("Purchase Invoice", docname)

    if not doc:
        frappe.throw(_("Document not found"))

    _populate_compliance_section_fields(doc)

    return {"message": "Compliance section populated successfully"}


def _populate_compliance_section_fields(doc):
    """
    Populate pd_custom_tax_compliance_section fields from pd_custom_wht_preview_section
    Only when is_paid (cash purchase) is enabled
    """

    print(
        f"💰 DEBUG: Purchase Invoice is cash purchase - populating compliance section from preview"
    )

    # Only populate if Thai WHT compliance is enabled and subject to WHT
    if not getattr(doc, "pd_custom_apply_thai_wht_compliance", 0) or not getattr(doc, "pd_custom_subject_to_wht", 0):
        print(f"⏭️ DEBUG: Skipping compliance section - WHT not enabled")
        return

    # Map preview fields to compliance fields
    field_mapping = {
        # From preview section → To compliance section
        "pd_custom_wht_income_type": "pd_custom_income_type",
        "pd_custom_withholding_tax_pct": "pd_custom_withholding_tax_rate",
        "pd_custom_withholding_tax_amount": "pd_custom_withholding_tax_amount",
        "pd_custom_wht_description": "pd_custom_wht_description",
        "pd_custom_wht_note": "pd_custom_wht_note",
        # Tax invoice fields
        "pd_custom_tax_invoice_company_name": "pd_custom_tax_invoice_company_name",
        "pd_custom_tax_invoice_address": "pd_custom_tax_invoice_address",
        "pd_custom_tax_invoice_tax_id": "pd_custom_tax_invoice_tax_id",
        # Additional compliance fields
        "supplier": "pd_custom_supplier_name",
        "supplier_name": "pd_custom_supplier_display_name",
    }

    populated_count = 0
    for preview_field, compliance_field in field_mapping.items():
        preview_value = getattr(doc, preview_field, None)
        current_compliance_value = getattr(doc, compliance_field, None)

        # Only populate if preview has value and compliance field is empty
        if preview_value and not current_compliance_value:
            setattr(doc, compliance_field, preview_value)
            populated_count += 1
            print(f"✅ DEBUG: Populated {compliance_field} = {preview_value}")

    print(f"📊 DEBUG: Populated {populated_count} compliance fields from preview section")

    # Log the action
    frappe.logger().info(
        f"Populated {populated_count} pd_custom_tax_compliance_section fields from preview for cash purchase PI {doc.name}"
    )


def auto_populate_from_purchase_order(doc):
    """
    Auto-populate Thai WHT and tax compliance fields from Purchase Order
    Also auto-populate tax invoice fields from bill_no, bill_date, net_total
    """

    print(f"🔥 DEBUG: Starting auto-population for Purchase Invoice {doc.name}")
    print(f"📋 DEBUG: Document has {len(getattr(doc, 'items', []))} items")

    # Auto-populate tax invoice fields from Purchase Invoice's own fields
    _populate_tax_invoice_from_bill_fields(doc)

    # Find and populate from linked Purchase Orders
    _populate_from_linked_purchase_orders(doc)

    print(f"✅ DEBUG: Auto-population completed for Purchase Invoice {doc.name}")


def _populate_tax_invoice_from_bill_fields(doc):
    """
    Auto-populate tax invoice fields from Purchase Invoice's bill_no, bill_date, net_total
    Logic: If user doesn't enter value, fetch from existing fields
    """

    print(f"🏷️ DEBUG: Checking tax invoice fields for Purchase Invoice {doc.name}")

    # Only populate tax invoice fields for cash purchases (is_paid = 1)
    if not getattr(doc, "is_paid", 0):
        print(
            f"❌ DEBUG: Not a cash purchase (is_paid = 0), skipping tax invoice fields auto-population"
        )
        return

    print(f"💰 DEBUG: Cash purchase detected (is_paid = 1), proceeding with tax invoice fields")

    # Tax Invoice Number ← bill_no
    if not getattr(doc, "pd_custom_tax_invoice_number", None) and getattr(doc, "bill_no", None):
        doc.pd_custom_tax_invoice_number = doc.bill_no
        print(f"📝 DEBUG: Auto-populated tax invoice number: {doc.bill_no}")
        frappe.logger().info(f"Auto-populated tax invoice number from bill_no: {doc.bill_no}")
    else:
        print(f"📝 DEBUG: Tax invoice number already set or bill_no missing")

    # Tax Invoice Date ← bill_date
    if not getattr(doc, "pd_custom_tax_invoice_date", None) and getattr(doc, "bill_date", None):
        doc.pd_custom_tax_invoice_date = doc.bill_date
        print(f"📅 DEBUG: Auto-populated tax invoice date: {doc.bill_date}")
        frappe.logger().info(f"Auto-populated tax invoice date from bill_date: {doc.bill_date}")
    else:
        print(f"📅 DEBUG: Tax invoice date already set or bill_date missing")

    # Tax Base Amount ← net_total
    if not getattr(doc, "pd_custom_tax_base_amount", None) and getattr(doc, "net_total", None):
        doc.pd_custom_tax_base_amount = doc.net_total
        print(f"💰 DEBUG: Auto-populated tax base amount: {doc.net_total}")
        frappe.logger().info(f"Auto-populated tax base amount from net_total: {doc.net_total}")
    else:
        print(f"💰 DEBUG: Tax base amount already set or net_total missing")


def _populate_from_linked_purchase_orders(doc):
    """
    Auto-populate Thai WHT fields from linked Purchase Orders
    """

    print(
        f"🔗 DEBUG: Looking for linked Purchase Orders in {len(doc.items) if doc.items else 0} items"
    )

    if not doc.items:
        print(f"❌ DEBUG: No items found in Purchase Invoice")
        return

    # Find linked Purchase Orders from Purchase Invoice items
    purchase_orders = []
    for item in doc.items:
        if item.purchase_order:
            purchase_orders.append(item.purchase_order)
            print(f"🔗 DEBUG: Found linked PO: {item.purchase_order} for item {item.item_code}")

    # Remove duplicates
    purchase_orders = list(set(purchase_orders))

    # If no direct Purchase Order links, check via Purchase Receipts
    if not purchase_orders:
        print(f"🔍 DEBUG: No direct Purchase Order links found, checking via Purchase Receipts")
        purchase_orders = _find_purchase_orders_via_receipts(doc)

    if not purchase_orders:
        print(f"❌ DEBUG: No linked Purchase Orders found through any workflow")
        frappe.logger().info("No linked Purchase Orders found for auto-population")
        return

    print(f"📋 DEBUG: Found {len(purchase_orders)} unique Purchase Orders: {purchase_orders}")

    # Get the primary Purchase Order (use first one if multiple)
    primary_po_name = purchase_orders[0]

    try:
        po_doc = frappe.get_doc("Purchase Order", primary_po_name)
        print(f"📄 DEBUG: Retrieved Purchase Order {primary_po_name}")

        # Only populate if Purchase Order has Thai WHT compliance enabled
        if not getattr(po_doc, "pd_custom_apply_thai_wht_compliance", 0):
            print(
                f"❌ DEBUG: Purchase Order {primary_po_name} does not have Thai WHT compliance enabled"
            )
            frappe.logger().info(
                f"Purchase Order {primary_po_name} does not have Thai WHT compliance enabled"
            )
            return

        # Auto-populate exact matching fields (20 fields)
        _populate_matching_fields(doc, po_doc)

        # Auto-populate WHT certificate fields
        _populate_wht_certificate_fields(doc, po_doc)

        print(
            f"✅ DEBUG: Successfully auto-populated Purchase Invoice from Purchase Order {primary_po_name}"
        )
        frappe.logger().info(
            f"Auto-populated Purchase Invoice from Purchase Order {primary_po_name}"
        )

    except Exception as e:
        print(f"❌ DEBUG: Error auto-populating from Purchase Order {primary_po_name}: {str(e)}")
        frappe.logger().error(
            f"Error auto-populating from Purchase Order {primary_po_name}: {str(e)}"
        )


def _find_purchase_orders_via_receipts(doc):
    """
    Find Purchase Orders by tracing through Purchase Receipts
    Handles workflow: Purchase Order → Purchase Receipt → Purchase Invoice
    """

    print(f"🔍 DEBUG: Tracing Purchase Orders via Purchase Receipts for PI {doc.name}")

    purchase_orders = []

    # Find Purchase Receipts linked to this Purchase Invoice
    for item in getattr(doc, "items", []):
        if hasattr(item, "purchase_receipt") and item.purchase_receipt:
            pr_name = item.purchase_receipt
            print(f"🧾 DEBUG: Found Purchase Receipt {pr_name} for item {item.item_code}")

            try:
                # Get Purchase Receipt document
                pr_doc = frappe.get_doc("Purchase Receipt", pr_name)

                # Find Purchase Orders linked to this Purchase Receipt
                for pr_item in getattr(pr_doc, "items", []):
                    if hasattr(pr_item, "purchase_order") and pr_item.purchase_order:
                        purchase_orders.append(pr_item.purchase_order)
                        print(f"🔗 DEBUG: Traced PO {pr_item.purchase_order} via PR {pr_name}")

            except Exception as e:
                print(f"⚠️ DEBUG: Error getting Purchase Receipt {pr_name}: {str(e)}")
                continue

    # Remove duplicates and return
    unique_pos = list(set(purchase_orders))
    print(
        f"📋 DEBUG: Found {len(unique_pos)} unique Purchase Orders via Purchase Receipts: {unique_pos}"
    )

    return unique_pos


def _populate_matching_fields(pi_doc, po_doc):
    """
    Populate the 20 exact matching fields from Purchase Order to Purchase Invoice
    Only populate if Purchase Invoice field is empty
    """

    print(f"🔄 DEBUG: Starting field mapping from PO {po_doc.name} to PI {pi_doc.name}")

    # Exact matching fields to populate
    matching_fields = [
        "pd_custom_apply_thai_wht_compliance",
        "thailand_service_business",  # Required for pd_custom_subject_to_wht field visibility
        "pd_custom_vat_treatment",
        "pd_custom_subject_to_wht",
        "pd_custom_wht_income_type",
        "pd_custom_wht_description",
        "pd_custom_wht_note",
        "pd_custom_subject_to_retention",
        "pd_custom_retention_note",
        "pd_custom_retention_pct",
        "pd_custom_withholding_tax_pct",  # WHT rate
    ]

    # Only populate if Purchase Invoice field is empty
    populated_count = 0
    for field in matching_fields:
        po_value = getattr(po_doc, field, None)
        pi_value = getattr(pi_doc, field, None)

        if po_value and not pi_value:
            setattr(pi_doc, field, po_value)
            populated_count += 1
            print(f"✅ DEBUG: Populated {field}: {po_value}")
            frappe.logger().info(f"Populated {field}: {po_value}")
        else:
            print(f"⏭️ DEBUG: Skipped {field} (PO: {po_value}, PI: {pi_value})")

    print(f"📊 DEBUG: Populated {populated_count}/{len(matching_fields)} matching fields")


def _populate_wht_certificate_fields(pi_doc, po_doc):
    """
    Populate WHT Certificate fields (right column of pd_custom_tax_compliance_section)
    ONLY for cash purchases (is_paid = 1)
    """

    print(f"🏆 DEBUG: Checking WHT certificate fields for PI {pi_doc.name}")

    # Only populate WHT certificate fields for cash purchases
    if not getattr(pi_doc, "is_paid", 0):
        print(f"❌ DEBUG: Not a cash purchase (is_paid = 0), skipping WHT certificate fields")
        return

    # Enable WHT certificate application if WHT is applicable AND it's a cash purchase
    if (
        getattr(po_doc, "pd_custom_subject_to_wht", 0)
        and getattr(po_doc, "pd_custom_withholding_tax_pct", 0)
        and not getattr(pi_doc, "pd_custom_apply_withholding_tax", 0)
    ):

        pi_doc.pd_custom_apply_withholding_tax = 1
        print(f"🏆 DEBUG: Auto-enabled WHT certificate application for cash purchase")
        frappe.logger().info("Auto-enabled WHT certificate application for cash purchase")

        # WHT Certificate Date - use posting date if not set
        if not getattr(pi_doc, "pd_custom_wht_certificate_date", None):
            pi_doc.pd_custom_wht_certificate_date = pi_doc.posting_date
            print(f"🏆 DEBUG: Set WHT certificate date to {pi_doc.posting_date}")

        # WHT Rate - from Purchase Order if not set
        if not getattr(pi_doc, "pd_custom_withholding_tax_rate", None):
            pi_doc.pd_custom_withholding_tax_rate = getattr(po_doc, "pd_custom_withholding_tax_pct", 0)
            print(f"🏆 DEBUG: Set WHT rate to {pi_doc.pd_custom_withholding_tax_rate}%")

        # Auto-generate WHT certificate number if needed
        _auto_generate_wht_certificate_number(pi_doc)
    else:
        print(f"❌ DEBUG: WHT certificate conditions not met for cash purchase")


def _auto_generate_wht_certificate_number(pi_doc):
    """
    Auto-generate WHT certificate number if not provided by user
    """

    if not getattr(pi_doc, "pd_custom_wht_certificate_no", None):
        try:
            # Generate certificate number: Company-WHT-Year-Sequence
            company_abbr = frappe.db.get_value("Company", pi_doc.company, "abbr") or "COMP"
            year = frappe.utils.nowdate()[:4]

            # Get next sequence number
            sequence = _get_next_wht_certificate_sequence(pi_doc.company, year)

            # Format: COMP-WHT-2024-001
            cert_number = f"{company_abbr}-WHT-{year}-{sequence:03d}"
            pi_doc.pd_custom_wht_certificate_no = cert_number

            frappe.logger().info(f"Auto-generated WHT Certificate No: {cert_number}")

        except Exception as e:
            frappe.logger().error(f"Error generating WHT certificate number: {str(e)}")
            # Fallback to simple format
            pi_doc.pd_custom_wht_certificate_no = f"WHT-{pi_doc.name}"


def _get_next_wht_certificate_sequence(company, year):
    """
    Get next sequence number for WHT certificate within company and year
    """

    try:
        # Query existing certificates for this company and year
        pattern = f"%-WHT-{year}-%"

        existing_certs = frappe.db.sql(
            """
            SELECT pd_custom_wht_certificate_no
            FROM `tabPurchase Invoice`
            WHERE company = %s
            AND pd_custom_wht_certificate_no LIKE %s
            AND docstatus != 2
            ORDER BY creation DESC
            LIMIT 1
        """,
            (company, pattern),
        )

        if existing_certs and existing_certs[0][0]:
            # Extract sequence number from last certificate
            last_cert = existing_certs[0][0]
            try:
                # Split by '-' and get last part
                parts = last_cert.split("-")
                if len(parts) >= 4:
                    sequence_part = parts[-1]
                    last_sequence = int(sequence_part)
                    return last_sequence + 1
            except (ValueError, IndexError):
                pass

        # If no existing certificates found or parsing failed, start with 1
        return 1

    except Exception as e:
        frappe.logger().error(f"Error getting WHT certificate sequence: {str(e)}")
        return 1


# TODO: Income Type Options Reconciliation
# ===========================================
# Currently pd_custom_wht_income_type and pd_custom_income_type have different options
#
# pd_custom_wht_income_type options:
# - professional_services, rental, service_fees, construction, advertising, other_services
#
# pd_custom_income_type options (Thai Revenue Department):
# - 1. เงินเดือน ค่าจ้าง ฯลฯ 40(1)
# - 2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)
# - 3. ค่าแห่งลิขสิทธิ์ ฯลฯ 40(3)
# - 4. ดอกเบี้ย ฯลฯ 40(4)ก
# - 5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส
# - 6. ค่าบริการ/ค่าสินค้าภาครัฐ
#
# Reference: https://www.rd.go.th/5937.html#mata40
#
# TODO mapping (to be implemented later):
# def _map_wht_income_type_to_revenue_department_classification(pd_custom_wht_income_type):
#     """
#     Map pd_custom_wht_income_type to pd_custom_income_type based on Thai Tax law
#     Reference: https://www.rd.go.th/5937.html#mata40
#     """
#
#     mapping = {
#         'professional_services': '2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)',
#         'rental': '4. ดอกเบี้ย ฯลฯ 40(4)ก',  # May need refinement
#         'service_fees': '5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส',
#         'construction': '5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส',
#         'advertising': '2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ 40(2)',
#         'other_services': '6. ค่าบริการ/ค่าสินค้าภาครัฐ'
#     }
#
#     return mapping.get(pd_custom_wht_income_type)
#
# This mapping needs review with actual Thai Tax law requirements
# ===========================================


def disable_standard_wht_calculation(doc):
    """
    Prevent ERPNext's automatic Tax Withholding Category calculation
    by removing any auto-generated tax withholding entries
    """

    if not hasattr(doc, "taxes") or not doc.taxes:
        return

    # Remove any tax entries that were auto-generated by ERPNext's WHT system
    taxes_to_remove = []
    for idx, tax in enumerate(doc.taxes):
        if tax.account_head and "withholding" in tax.account_head.lower():
            taxes_to_remove.append(idx)

    # Remove in reverse order to maintain indices
    for idx in reversed(taxes_to_remove):
        doc.taxes.pop(idx)

    frappe.logger().info(f"Removed {len(taxes_to_remove)} ERPNext WHT tax entries")


def calculate_thai_compliant_wht(doc):
    """
    Calculate WHT using Thai compliance rules:
    - Use net_total (before VAT) as calculation base
    - Apply precise percentage calculation without rounding quirks
    - Support Thai retention system integration
    """

    print(f"🧮 DEBUG: calculate_thai_compliant_wht called for PI {doc.name}")

    # Get WHT rate from custom field
    wht_rate = flt(getattr(doc, "pd_custom_withholding_tax_pct", 0))
    print(f"🧮 DEBUG: WHT rate: {wht_rate}%")

    if wht_rate <= 0:
        print(f"⏭️ DEBUG: WHT rate is 0 or negative, skipping calculation")
        return

    # Calculate WHT base amount (SERVICE ITEMS ONLY - Thai tax law)
    wht_base_amount = get_wht_calculation_base(doc)

    # Calculate RETENTION base amount (WHOLE INVOICE - contract guarantee)
    # Priority: base_total (Company Currency) → total (Transaction Currency)
    retention_base_amount = flt(getattr(doc, "base_total", 0)) or flt(getattr(doc, "total", 0))

    # DEBUGGING: Show result AFTER calculation
    print(f"\n{'='*80}")
    print(f"📊 WHT Base (service items only): {wht_base_amount}")
    print(f"📊 Retention Base (whole invoice): {retention_base_amount}")
    print(f"   - base_total: {flt(getattr(doc, 'base_total', 0))}")
    print(f"   - total: {flt(getattr(doc, 'total', 0))}")
    print(f"{'='*80}\n")

    # Precise WHT calculation: wht_base × rate ÷ 100 (SERVICE ITEMS ONLY)
    wht_amount = flt(wht_base_amount * wht_rate / 100, 2)  # Round to 2 decimal places
    print(f"🧮 DEBUG: Calculated WHT amount: {wht_base_amount} × {wht_rate}% = {wht_amount}")

    # Update custom WHT fields
    doc.pd_custom_withholding_tax_amount = wht_amount
    print(f"🧮 DEBUG: Set pd_custom_withholding_tax_amount = {wht_amount}")

    # CONDITIONAL: Set pd_custom_subject_to_wht flag only when WHT amount is calculated and > 0
    if wht_amount > 0:
        doc.pd_custom_subject_to_wht = 1
        print(f"✅ DEBUG: Set pd_custom_subject_to_wht = 1 (WHT Amount: {wht_amount})")
        frappe.logger().info(
            f"Set pd_custom_subject_to_wht = 1 for PI {doc.name} (WHT Amount: {wht_amount})"
        )
    else:
        doc.pd_custom_subject_to_wht = 0
        print(f"❌ DEBUG: Set pd_custom_subject_to_wht = 0 (No WHT amount)")
        frappe.logger().info(f"Set pd_custom_subject_to_wht = 0 for PI {doc.name} (No WHT amount)")

    # Calculate retention amount if retention is enabled
    print("\n" + "=" * 80)
    print("🔍 RETENTION CALCULATION DEBUG START - Purchase Invoice")
    print("=" * 80)

    pd_custom_subject_to_retention = getattr(doc, "pd_custom_subject_to_retention", 0)
    has_custom_retention = hasattr(doc, "pd_custom_retention_pct")
    print(f"1. pd_custom_subject_to_retention: {pd_custom_subject_to_retention}")
    print(f"2. has pd_custom_retention_pct attr: {has_custom_retention}")

    if pd_custom_subject_to_retention and has_custom_retention:
        retention_percentage = flt(getattr(doc, "pd_custom_retention_pct", 0))
        print(f"3. retention_percentage: {retention_percentage}%")
        print(f"4. retention_base_amount (WHOLE INVOICE): {retention_base_amount}")

        # Browser debug message
        frappe.msgprint(
            f"🔍 CALC DEBUG (PI): retention_base = {retention_base_amount}, retention % = {retention_percentage}%",
            indicator="orange",
            title="Retention Calculation - PI",
        )

        if retention_percentage > 0:
            # FIXED: Retention is calculated on WHOLE INVOICE, not just services
            # Thai business practice: Retention guarantees entire project (materials + labor)
            # Example: 100,000 THB invoice × 5% = 5,000 THB retention
            calculated_retention = flt(retention_base_amount * retention_percentage / 100, 2)
            doc.pd_custom_retention_amount = calculated_retention
            print(
                f"5. ✅ Calculated retention_amount: {retention_base_amount} × {retention_percentage}% = {calculated_retention}"
            )

            # Browser debug message
            frappe.msgprint(
                f"✅ Calculated retention_amount = {calculated_retention} THB (on whole invoice)",
                indicator="green",
                title="Retention Calculation Success - PI",
            )

    print("=" * 80 + "\n")

    # Calculate final payment amount (after WHT and retention)
    retention_amount = flt(getattr(doc, "pd_custom_retention_amount", 0))
    final_payment = flt(doc.grand_total) - wht_amount - retention_amount
    doc.pd_custom_payment_amount = final_payment
    print(
        f"🧮 DEBUG: Final payment: {doc.grand_total} - {wht_amount} - {retention_amount} = {final_payment}"
    )

    # Update preview fields for user display
    update_thai_wht_preview_fields(doc, wht_base_amount, wht_amount, final_payment)
    print(f"🧮 DEBUG: Updated preview fields")

    frappe.logger().info(
        f"Thai WHT Calculation: {wht_base_amount} × {wht_rate}% = {wht_amount} "
        f"(Final Payment: {final_payment})"
    )


def get_wht_calculation_base(doc):
    """
    Get the correct base amount for WHT calculation.
    Thai WHT should be calculated ONLY on service items, not assets/goods.
    WHT applies to: Item.pd_custom_is_service_item = 1
    """

    # Calculate WHT base from SERVICE ITEMS ONLY
    # WHT does not apply to assets/goods, only to services
    service_items_total = 0.0

    if hasattr(doc, "items") and doc.items:
        for item in doc.items:
            # Check if item is a service item by querying Item master
            item_code = getattr(item, "item_code", None)
            if item_code:
                try:
                    item_doc = frappe.get_cached_doc("Item", item_code)
                    is_service = getattr(item_doc, "pd_custom_is_service_item", 0)

                    if is_service:
                        # Sum only service item amounts
                        service_items_total += flt(item.amount)
                except Exception:
                    # If item not found or error, skip this item
                    pass

    return flt(service_items_total)


def update_thai_wht_preview_fields(doc, base_amount, wht_amount, final_payment):
    """
    Update Thai WHT preview section fields for better user experience
    """

    # Update net total after WHT field: grand_total - wht_amount
    # This represents: base_amount + VAT - WHT
    doc.pd_custom_net_total_after_wht = flt(doc.grand_total) - wht_amount

    # Update in words fields if they exist
    if hasattr(doc, "pd_custom_net_total_after_wht_words"):
        from frappe.utils import money_in_words

        doc.pd_custom_net_total_after_wht_words = money_in_words(doc.pd_custom_net_total_after_wht, doc.currency)

    # Update combined WHT and retention amounts
    if hasattr(doc, "pd_custom_net_after_wht_retention"):
        doc.pd_custom_net_after_wht_retention = final_payment

        if hasattr(doc, "pd_custom_net_after_wht_retention_words"):
            doc.pd_custom_net_after_wht_retention_words = money_in_words(
                final_payment, doc.currency
            )


@frappe.whitelist()
def validate_thai_wht_configuration(doc, method=None):
    """
    Validate Thai WHT configuration to ensure proper setup
    Auto-fetch default WHT rate from Company if not specified
    THAI COMPLIANCE: Validate mandatory bill_no and bill_date for Thai tax compliance
    """

    print(f"🔍 DEBUG: validate_thai_wht_configuration called for PI {doc.name}")
    print(f"🔍 DEBUG: pd_custom_apply_thai_wht_compliance: {getattr(doc, 'pd_custom_apply_thai_wht_compliance', 0)}")
    print(f"🔍 DEBUG: pd_custom_subject_to_wht: {getattr(doc, 'pd_custom_subject_to_wht', 0)}")
    print(f"🔍 DEBUG: is_paid: {getattr(doc, 'is_paid', 0)}")
    print(f"🔍 DEBUG: current pd_custom_withholding_tax_pct: {getattr(doc, 'pd_custom_withholding_tax_pct', 0)}")

    # THAI COMPLIANCE: Mandatory Bill Number and Bill Date validation (unless cash purchase)
    validate_thai_mandatory_bill_fields(doc)

    if not getattr(doc, "pd_custom_apply_thai_wht_compliance", 0):
        print(f"⏭️ DEBUG: Thai WHT compliance not enabled for PI {doc.name}")
        return

    # ✅ FIX: Auto-populate WHT rate for ALL purchases with WHT, not just cash purchases
    if getattr(doc, "pd_custom_subject_to_wht", 0):
        print(f"🎯 DEBUG: Processing WHT for PI {doc.name} (pd_custom_subject_to_wht=1)")

        # Auto-populate WHT rate based on income type if not already set
        if (
            not getattr(doc, "pd_custom_withholding_tax_pct")
            or flt(getattr(doc, "pd_custom_withholding_tax_pct", 0)) == 0
        ):
            print("🔄 DEBUG: WHT rate empty, attempting auto-population")

            # Try to get default WHT rate based on income type
            wht_rate = get_default_wht_rate_by_income_type(doc)

            if wht_rate and flt(wht_rate) > 0:
                doc.pd_custom_withholding_tax_pct = flt(wht_rate)
                print(
                    f"✅ DEBUG: Auto-set WHT rate to {wht_rate}% for income type {getattr(doc, 'pd_custom_wht_income_type', None)}"
                )
                frappe.logger().info(
                    f"Auto-set WHT rate {wht_rate}% for income type {getattr(doc, 'pd_custom_wht_income_type', None)} in PI {doc.name}"
                )

                # Show user-friendly message
                frappe.msgprint(
                    _("Auto-applied {0}% WHT rate for {1} income type").format(
                        flt(wht_rate), getattr(doc, "pd_custom_wht_income_type", "selected")
                    ),
                    indicator="blue",
                )
            else:
                print("⚠️ DEBUG: No WHT rate found - user must set manually")
                # Don't throw error - let user set rate manually
                frappe.msgprint(
                    _("Please set Withholding Tax percentage manually for this transaction"),
                    indicator="yellow",
                )

    # Auto-fetch default retention rate from Company if applicable
    print("\n" + "=" * 80)
    print("🔍 RETENTION AUTO-FETCH DEBUG START - Purchase Invoice")
    print("=" * 80)

    pd_custom_subject_to_retention = getattr(doc, "pd_custom_subject_to_retention", 0)
    print(f"1. pd_custom_subject_to_retention: {pd_custom_subject_to_retention}")

    # Browser debug message
    frappe.msgprint(
        f"🔍 DEBUG Step 1: pd_custom_subject_to_retention = {pd_custom_subject_to_retention}",
        indicator="orange",
        title="Retention Debug - PI",
    )

    if pd_custom_subject_to_retention:
        print(f"2. Company: {doc.company}")

        # Check if construction_service is enabled for this Company
        construction_service_enabled = frappe.db.get_value(
            "Company", doc.company, "construction_service"
        )
        print(f"3. construction_service_enabled: {construction_service_enabled}")

        # Browser debug message
        frappe.msgprint(
            f"🔍 DEBUG Step 2: Company = {doc.company}<br>construction_service = {construction_service_enabled}",
            indicator="orange",
            title="Retention Debug - PI",
        )

        if construction_service_enabled:
            # Check current retention rate value
            current_retention = getattr(doc, "pd_custom_retention_pct", None)
            current_retention_value = flt(current_retention) if current_retention else 0
            print(
                f"4. Current pd_custom_retention_pct: {current_retention} (value: {current_retention_value})"
            )

            # PRIORITY 1: Check if retention rate came from Purchase Order
            # If PI was created from PO, retention should already be populated
            has_po_reference = False
            if hasattr(doc, "items") and doc.items:
                for item in doc.items:
                    if hasattr(item, "purchase_order") and item.purchase_order:
                        has_po_reference = True
                        print(f"5. ✅ Found PO reference: {item.purchase_order}")
                        break

            if has_po_reference and current_retention_value > 0:
                # Case 1: PI created from PO and retention rate already populated from PO
                print(
                    f"6. ✅ Retention rate already populated from Purchase Order: {current_retention_value}%"
                )
                frappe.msgprint(
                    f"✅ Using retention rate from Purchase Order: {current_retention_value}%",
                    indicator="blue",
                    title="Retention from PO - PI",
                )
            elif not current_retention or current_retention_value == 0:
                # Case 2: No PO reference OR PO has no retention → Auto-fetch from Company
                print(f"7. No retention from PO, fetching from Company default...")

                default_retention_rate = frappe.db.get_value(
                    "Company", doc.company, "default_retention_rate"
                )
                print(f"8. default_retention_rate from Company: {default_retention_rate}")

                # Browser debug message
                frappe.msgprint(
                    f"🔍 DEBUG Step 3: No PO retention, using Company default = {default_retention_rate}%",
                    indicator="orange",
                    title="Retention Debug - PI",
                )

                if default_retention_rate and flt(default_retention_rate) > 0:
                    doc.pd_custom_retention_pct = flt(default_retention_rate)
                    print(
                        f"9. ✅ Set doc.pd_custom_retention_pct to Company default: {doc.pd_custom_retention_pct}"
                    )

                    # Show success message
                    frappe.msgprint(
                        f"✅ Auto-applied Company default retention rate: {flt(default_retention_rate)}%",
                        indicator="green",
                        title="Success - PI",
                    )
            else:
                # Case 3: Retention already set manually by user
                print(f"10. ℹ️ Retention rate already set manually: {current_retention_value}%")

    print("=" * 80 + "\n")

    # Additional validation for cash purchases only
    if getattr(doc, "pd_custom_subject_to_wht", 0) and getattr(doc, "is_paid", 0):
        print(f"💰 DEBUG: Additional cash purchase validation for PI {doc.name}")

        if not getattr(doc, "pd_custom_wht_income_type"):
            frappe.throw(
                _(
                    "WHT Income Type is required when Subject to Withholding Tax is enabled for cash purchases"
                )
            )

        # MANDATORY: pd_custom_income_type for Revenue Department compliance
        if not getattr(doc, "pd_custom_income_type"):
            frappe.throw(
                _(
                    "Income Type (Revenue Department classification) is required when Subject to Withholding Tax is enabled for cash purchases"
                )
            )

    # Validate VAT treatment for TDS transactions
    # Only suggest VAT Undue if document has single item type (not mixed assets + services)
    pd_custom_vat_treatment = getattr(doc, "pd_custom_vat_treatment", "")
    if pd_custom_vat_treatment and pd_custom_vat_treatment not in ["VAT Undue (7%)", "Exempt from VAT"]:
        # Check if document has mixed item types
        has_mixed_item_types = _check_mixed_item_types(doc)

        # Only show VAT Undue suggestion for single-item-type documents
        if not has_mixed_item_types:
            frappe.msgprint(
                _(
                    "Consider using 'VAT Undue (7%)' for TDS transactions to comply with Thai tax regulations"
                ),
                indicator="yellow",
            )


def _check_mixed_item_types(doc):
    """
    Check if document contains mixed item types (both assets and services).
    VAT point occurs immediately for mixed documents, so VAT Undue is not applicable.

    Args:
        doc: Purchase Invoice or Purchase Order document

    Returns:
        bool: True if document has mixed item types (assets + services), False otherwise
    """
    if not hasattr(doc, "items") or not doc.items:
        return False

    has_assets = False
    has_services = False

    for item in doc.items:
        # Check if item is an asset or service
        if hasattr(item, "item_code") and item.item_code:
            item_doc = frappe.get_cached_doc("Item", item.item_code)
            is_fixed_asset = getattr(item_doc, "is_fixed_asset", 0)
            is_stock_item = getattr(item_doc, "is_stock_item", 0)

            # Asset: is_fixed_asset = 1 OR is_stock_item = 1 (goods)
            # Service: is_fixed_asset = 0 AND is_stock_item = 0
            if is_fixed_asset or is_stock_item:
                has_assets = True
            else:
                has_services = True

        # Early exit if we found both types
        if has_assets and has_services:
            return True

    return False


def get_default_wht_rate_by_income_type(doc):
    """
    Get default Thai WHT rate based on income type according to Thai Revenue Department regulations

    Args:
        doc: Purchase Invoice document

    Returns:
        float: WHT percentage rate (e.g., 3.0 for 3%)
    """

    pd_custom_wht_income_type = getattr(doc, "pd_custom_wht_income_type", "")

    # Standard Thai WHT rates according to Revenue Department regulations
    wht_rate_mapping = {
        "professional_services": 3.0,  # ค่าจ้างวิชาชีพ - 3% (Section 40(2))
        "rental": 5.0,  # ค่าเช่า - 5%
        "service_fees": 3.0,  # ค่าบริการ - 3% (Section 3 Ter)
        "construction": 3.0,  # ค่าก่อสร้าง - 3% (Section 3 Ter)
        "advertising": 2.0,  # ค่าโฆษณา - 2% (Section 40(2))
        "other_services": 3.0,  # ค่าบริการอื่น ๆ - 3% (default for services)
    }

    rate = wht_rate_mapping.get(pd_custom_wht_income_type, None)

    print(f"🔍 DEBUG: get_default_wht_rate_by_income_type")
    print(f"  Income type: {pd_custom_wht_income_type}")
    print(f"  Mapped rate: {rate}%")

    if not rate:
        # Try to get from Company default_wht_rate as fallback
        try:
            company_default = frappe.db.get_value("Company", doc.company, "default_wht_rate")
            if company_default and flt(company_default) > 0:
                rate = flt(company_default)
                print(f"  Using company default: {rate}%")
        except:
            pass

    return rate


def validate_thai_mandatory_bill_fields(doc):
    """
    Thai Tax Compliance: Make bill_no and bill_date mandatory fields by default
    Required for Thai Revenue Department audit compliance and tax documentation
    Prevents ERPNext bug where blank fields disappear and become uneditable

    DEFAULT BEHAVIOR: Fields are ALWAYS mandatory (locked) regardless of is_paid
    UNLOCK MECHANISM: User can tick 'pd_custom_bill_cash' checkbox to make fields optional
    USE CASE: Street shops with บิลเงินสด that have no formal invoice numbering

    Args:
        doc: Purchase Invoice document

    Raises:
        frappe.ValidationError: If mandatory fields are missing and pd_custom_bill_cash is not enabled
    """

    # Check if user has enabled pd_custom_bill_cash (บิลเงินสด) to unlock mandatory fields
    bill_cash_enabled = getattr(doc, "pd_custom_bill_cash", 0)

    if bill_cash_enabled:
        # บิลเงินสด enabled: bill_no and bill_date are NOT mandatory (user unlocked)
        frappe.logger().info(
            f"บิลเงินสด enabled for PI {doc.name}: User unlocked mandatory bill field validation"
        )

        # Optional: Show info message for unlocked fields (only in first save)
        if hasattr(doc, "is_new") and callable(doc.is_new) and doc.is_new():
            frappe.msgprint(
                _("🔓 บิลเงินสด: Fields unlocked - Supplier invoice details are optional"),
                indicator="blue",
                alert=False,
            )
        return

    # DEFAULT: bill_no and bill_date are ALWAYS MANDATORY (locked by default)

    # Check if bill_no (Supplier Invoice No) is provided
    bill_no = getattr(doc, "bill_no", None)
    if not bill_no or not str(bill_no).strip():
        frappe.throw(
            _(
                "Supplier Invoice No (Bill No) is mandatory for Thai tax compliance. Please either:\n"
                "• Enter the supplier's invoice number, OR\n"
                "• Enable 'บิลเงินสด' checkbox if supplier has no formal invoice system"
            ),
            frappe.MandatoryError,
            title=_("Missing Supplier Invoice No"),
        )

    # Check if bill_date (Supplier Invoice Date) is provided
    bill_date = getattr(doc, "bill_date", None)
    if not bill_date:
        frappe.throw(
            _(
                "Supplier Invoice Date (Bill Date) is mandatory for Thai tax compliance. Please either:\n"
                "• Enter the supplier's invoice date, OR\n"
                "• Enable 'บิลเงินสด' checkbox if supplier has no formal invoice system"
            ),
            frappe.MandatoryError,
            title=_("Missing Supplier Invoice Date"),
        )

    # Additional validation: bill_date should not be in future
    from frappe.utils import getdate, nowdate

    if getdate(bill_date) > getdate(nowdate()):
        frappe.throw(
            _("Supplier Invoice Date cannot be in the future. Please enter a valid invoice date."),
            frappe.ValidationError,
            title=_("Invalid Invoice Date"),
        )

    # Log successful validation for audit trail
    frappe.logger().info(
        f"Thai mandatory bill fields validated successfully for PI {doc.name}: bill_no={bill_no}, bill_date={bill_date}"
    )

    # Optional: Show success message to user (only in first save)
    if doc.is_new():
        frappe.msgprint(
            _("✅ Thai tax compliance validated: Supplier invoice details recorded"),
            indicator="green",
            alert=False,
        )


@frappe.whitelist()
def get_thai_wht_calculation_debug_info(purchase_invoice_name):
    """
    Debug function to analyze WHT calculation differences
    Returns detailed breakdown of both ERPNext and Thai calculations
    """

    doc = frappe.get_doc("Purchase Invoice", purchase_invoice_name)

    debug_info = {
        "document": purchase_invoice_name,
        "pd_custom_apply_thai_wht_compliance": getattr(doc, "pd_custom_apply_thai_wht_compliance", 0),
        "pd_custom_subject_to_wht": getattr(doc, "pd_custom_subject_to_wht", 0),
        "wht_rate": flt(getattr(doc, "pd_custom_withholding_tax_pct", 0)),
        "amounts": {
            "net_total": flt(getattr(doc, "net_total", 0)),
            "base_net_total": flt(getattr(doc, "base_net_total", 0)),
            "total": flt(getattr(doc, "total", 0)),
            "grand_total": flt(getattr(doc, "grand_total", 0)),
        },
        "thai_calculation": {},
        "erpnext_calculation": {},
    }

    # Thai calculation
    if debug_info["wht_rate"] > 0:
        base_amount = get_wht_calculation_base(doc)
        thai_wht = flt(base_amount * debug_info["wht_rate"] / 100, 2)

        debug_info["thai_calculation"] = {
            "base_amount": base_amount,
            "calculation": f"{base_amount} × {debug_info['wht_rate']}% = {thai_wht}",
            "wht_amount": thai_wht,
        }

    # ERPNext standard calculation (if any tax withholding entries exist)
    if hasattr(doc, "taxes") and doc.taxes:
        for tax in doc.taxes:
            if tax.account_head and "withholding" in tax.account_head.lower():
                debug_info["erpnext_calculation"] = {
                    "account": tax.account_head,
                    "tax_amount": flt(tax.tax_amount),
                    "base_tax_amount": flt(tax.base_tax_amount),
                    "rate": flt(tax.rate),
                }
                break

    return debug_info


@frappe.whitelist()
def test_thai_wht_automation():
    """
    Test function to verify the complete Thai WHT automation workflow
    Creates a test Purchase Invoice to verify field automation and calculation
    """

    try:
        # Create a test Purchase Invoice with Thai WHT enabled
        test_pi = frappe.new_doc("Purchase Invoice")
        test_pi.supplier = "Test Supplier"  # Use a simple supplier name
        test_pi.currency = "THB"
        test_pi.company = frappe.defaults.get_defaults().get("company")

        # Add a test item
        test_pi.append(
            "items",
            {
                "item_code": "Test Item",
                "description": "Test Service Item",
                "qty": 1,
                "rate": 10000,
                "amount": 10000,
            },
        )

        # Calculate totals to simulate ERPNext behavior
        test_pi.net_total = 10000
        test_pi.total = 10000
        test_pi.grand_total = 10000

        # Enable Thai WHT Compliance
        test_pi.pd_custom_apply_thai_wht_compliance = 1
        test_pi.pd_custom_subject_to_wht = 1
        test_pi.pd_custom_withholding_tax_pct = 3  # 3%
        test_pi.pd_custom_wht_income_type = "professional_services"

        # Test our calculation override
        calculate_thai_compliant_wht(test_pi)

        # Collect results
        results = {
            "test_status": "success",
            "base_amount": flt(test_pi.net_total),
            "wht_rate": flt(test_pi.pd_custom_withholding_tax_pct),
            "calculated_wht": flt(getattr(test_pi, "pd_custom_withholding_tax_amount", 0)),
            "expected_wht": 300,
            "calculation_correct": flt(getattr(test_pi, "pd_custom_withholding_tax_amount", 0))
            == 300,
            "final_payment": flt(getattr(test_pi, "pd_custom_payment_amount", 0)),
            "message": (
                "✅ Thai WHT calculation working correctly!"
                if flt(getattr(test_pi, "pd_custom_withholding_tax_amount", 0)) == 300
                else "❌ Thai WHT calculation issue detected"
            ),
        }

        return results

    except Exception as e:
        return {
            "test_status": "error",
            "error_message": str(e),
            "message": f"❌ Test failed: {str(e)}",
        }
