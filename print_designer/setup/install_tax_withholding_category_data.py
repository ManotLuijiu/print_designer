"""
Seed Tax Withholding Category records from Thai WHT Income Type data.

This script:
1. Reads existing Thai WHT Income Type records
2. Groups by (income_category, rate, recipient_type) to create distinct TWCs
3. Auto-detects current fiscal year from Fiscal Year doctype for rate row dates
4. Creates Tax Withholding Category records with:
   - category_name (e.g., "WHT 3% Services - Individual (PND3)")
   - tax_deduction_basis = "Gross Total" (Thai WHT calculated before VAT)
   - Rate row: fiscal year dates, rate, single_threshold=1000
   - pd_custom_apply_wht_to_contract_installments = 1
5. Updates Thai WHT Income Type records to link to their corresponding TWC

Usage:
    bench execute print_designer.setup.install_tax_withholding_category_data.seed_tax_withholding_categories
"""

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


# Single threshold for Thai WHT (per Revenue Department regulation)
THAI_WHT_SINGLE_THRESHOLD = 1000.0


def get_current_fiscal_year():
    """
    Get current fiscal year dates from Fiscal Year doctype.
    Returns (from_date, to_date) tuple.
    """
    from frappe.utils import nowdate, getdate

    try:
        # Use Frappe's standard fiscal year utility
        fy = frappe.get_fiscal_year(nowdate(), as_dict=True)
        return (fy.year_start_date, fy.year_end_date)
    except Exception:
        pass

    # Fallback: try to get any active fiscal year
    fiscal_year = frappe.db.get_value(
        "Fiscal Year",
        {"disabled": 0},
        ["year_start_date", "year_end_date"],
        as_dict=True,
        order_by="year_start_date desc"
    )

    if fiscal_year:
        return (fiscal_year.year_start_date, fiscal_year.year_end_date)

    # Last resort: use calendar year
    year = getdate(nowdate()).year
    return (f"{year}-01-01", f"{year}-12-31")



def get_existing_thai_wht_income_types():
    """Get all existing Thai WHT Income Type records."""
    if not frappe.db.exists("DocType", "Thai WHT Income Type"):
        return []

    return frappe.get_all(
        "Thai WHT Income Type",
        fields=["name", "form_type", "recipient_type", "income_category", "income_category_th", "tax_rate"]
    )


def build_twc_name(income_category, rate, recipient_type, form_type):
    """Build a descriptive TWC name."""
    name_map = {
        "Rental Income": "Rental",
        "Rental Income (Ship Lease)": "Rental Ship Lease",
        "Professional Services": "Professional Services",
        "Services Income": "Services",
        "Prize & Awards": "Prizes Awards",
        "Entertainment Income": "Entertainment",
        "Advertising Income": "Advertising",
        "Service Fees": "Service Fees",
        "Transport Fees": "Transport",
        "Sales Promotion Income": "Sales Promotion",
        "Commission & Royalties": "Commission Royalties",
        "Interest Income": "Interest",
        "Bond Interest": "Bond Interest",
        "Dividend Income": "Dividend",
        "Ship Rental": "Ship Rental",
        "Contracting Services": "Contracting",
        "Foreign Contractor Fees": "Foreign Contractor",
        "Insurance Premiums": "Insurance Premiums",
        "Agricultural Trading Income": "Agricultural",
    }

    short_name = name_map.get(income_category, income_category)
    recipient_suffix = "Individual" if recipient_type == "Individual" else "Corporate"

    return f"WHT {rate:.0f}% {short_name} - {recipient_suffix} ({form_type})"


def seed_tax_withholding_categories():
    """
    Main function to seed Tax Withholding Category records and link to Thai WHT Income Type.
    """
    print("Starting Tax Withholding Category seeding...")

    # Get fiscal year dates
    from_date, to_date = get_current_fiscal_year()
    print(f"Using fiscal year: {from_date} to {to_date}")

    # Get existing Thai WHT Income Type records
    thai_wht_records = get_existing_thai_wht_income_types()
    if not thai_wht_records:
        print("No Thai WHT Income Type records found. Nothing to link.")
        return

    print(f"Found {len(thai_wht_records)} Thai WHT Income Type records")

    # Build mapping: (income_category, rate, recipient_type, form_type) -> Thai WHT Income Type names
    twc_key_to_wht_names = {}
    for rec in thai_wht_records:
        key = (rec.income_category, rec.tax_rate, rec.recipient_type, rec.form_type)
        if key not in twc_key_to_wht_names:
            twc_key_to_wht_names[key] = []
        twc_key_to_wht_names[key].append(rec.name)

    print(f"Grouped into {len(twc_key_to_wht_names)} unique TWC categories")

    # Get company WHT accounts for the mandatory accounts child table
    company_wht_accounts = _get_company_wht_accounts()
    if not company_wht_accounts:
        print("⚠ No companies with default_wht_account configured. Cannot create TWC records (accounts is mandatory).")
        print("  Please set 'Default WHT Account' on Company first, then re-run migration.")
        return

    print(f"Found {len(company_wht_accounts)} companies with WHT accounts configured")

    # Create TWCs and track link mappings
    twc_name_by_key = {}
    twc_key_to_first_wht = {}  # key -> first WHT record for bilingual name
    twc_created = 0
    twc_updated = 0

    for key, wht_names in twc_key_to_wht_names.items():
        income_category, rate, recipient_type, form_type = key
        twc_name = build_twc_name(income_category, rate, recipient_type, form_type)

        # Track first WHT record for bilingual name population
        first_wht_name = wht_names[0]
        first_wht = next((r for r in thai_wht_records if r.name == first_wht_name), None)
        twc_key_to_first_wht[key] = first_wht

        # Check if TWC already exists
        if frappe.db.exists("Tax Withholding Category", twc_name):
            twc = frappe.get_doc("Tax Withholding Category", twc_name)
            twc_updated += 1
            print(f"  Updating existing TWC: {twc_name}")
        else:
            twc = frappe.new_doc("Tax Withholding Category")
            twc.name = twc_name
            twc.flags.ignore_autoname = True
            twc_created += 1
            print(f"  Creating new TWC: {twc_name}")

        twc_name_by_key[key] = twc_name

        # Update/add rate row
        _update_rate_row(twc, from_date, to_date, rate)

        # Set contract installment flag
        twc.pd_custom_apply_wht_to_contract_installments = 1

        # Set tax deduction basis — Thai WHT is calculated on gross amount (before VAT)
        twc.tax_deduction_basis = "Gross Total"

        # Populate mandatory accounts child table (preserve existing, add missing companies)
        _ensure_accounts_rows(twc, company_wht_accounts)

        # Populate combined label: Thai name + rate + PND form type
        if first_wht:
            thai_form = "ภงด." + form_type[3:]  # PND3 → ภงด.3 | PND53 → ภงด.53
            category_name_th = first_wht.get("income_category_th") or income_category
            twc.category_name = f"{category_name_th} {rate:g}% ({thai_form})"
            twc.category_name_en = first_wht.get("income_category") or income_category

        twc.save(ignore_permissions=True)

    frappe.db.commit()
    print(f"TWC seeding complete: {twc_created} created, {twc_updated} updated")

    # Now update Thai WHT Income Type records to link to TWCs
    links_updated = 0
    for rec in thai_wht_records:
        key = (rec.income_category, rec.tax_rate, rec.recipient_type, rec.form_type)
        twc_name = twc_name_by_key.get(key)
        if twc_name:
            current_link = frappe.db.get_value("Thai WHT Income Type", rec.name, "tax_withholding_category")
            if current_link != twc_name:
                frappe.db.set_value(
                    "Thai WHT Income Type",
                    rec.name,
                    "tax_withholding_category",
                    twc_name
                )
                links_updated += 1

    frappe.db.commit()
    print(f"Linked {links_updated} Thai WHT Income Type records to TWCs")

    return {
        "twc_created": twc_created,
        "twc_updated": twc_updated,
        "twc_total": twc_created + twc_updated,
        "links_updated": links_updated,
        "fiscal_year": f"{from_date} to {to_date}",
    }


def _get_company_wht_accounts():
    """
    Get all companies that have a default_wht_account configured.
    Returns list of dicts with asset account and liability account.
    """
    companies = frappe.get_all(
        "Company",
        filters={"default_wht_account": ["is", "set"]},
        fields=["name", "default_wht_account", "default_wht_debt_account"]
    )
    return [
        {
            "company": c.name,
            "account": c.default_wht_account,
            "liability_account": c.default_wht_debt_account,
        }
        for c in companies
    ]


def _ensure_accounts_rows(twc, company_wht_accounts):
    """
    Ensure the TWC has account rows for all companies with WHT accounts.
    Preserves existing rows (user may have customized the account), adds missing companies.
    Populates both asset account (from default_wht_account) and liability account
    (from default_wht_debt_account) on each row.
    """
    company_account_map = {entry["company"]: entry for entry in company_wht_accounts}

    for row in twc.get("accounts") or []:
        entry = company_account_map.get(row.company)
        if entry and entry.get("liability_account"):
            row.pd_custom_wht_liability_account = entry["liability_account"]

    existing_companies = {row.company for row in twc.get("accounts") or []}
    for entry in company_wht_accounts:
        if entry["company"] not in existing_companies:
            row = twc.append("accounts", {
                "company": entry["company"],
                "account": entry["account"],
            })
            # Populate liability account from Company.default_wht_debt_account
            if entry.get("liability_account"):
                row.pd_custom_wht_liability_account = entry["liability_account"]


def _update_rate_row(twc, from_date, to_date, rate):
    """Add or update rate row in TWC."""
    from frappe.utils import getdate

    # Check if a rate row with matching dates already exists
    existing_row = None
    if twc.get("rates"):
        for i, row in enumerate(twc.rates):
            if getdate(row.from_date) == getdate(from_date) and getdate(row.to_date) == getdate(to_date):
                existing_row = i
                break

    if existing_row is not None:
        # Update existing row
        twc.rates[existing_row].tax_withholding_rate = rate
        twc.rates[existing_row].single_threshold = THAI_WHT_SINGLE_THRESHOLD
        twc.rates[existing_row].cumulative_threshold = 0
    else:
        # Add new rate row
        twc.append("rates", {
            "from_date": from_date,
            "to_date": to_date,
            "tax_withholding_rate": rate,
            "single_threshold": THAI_WHT_SINGLE_THRESHOLD,
            "cumulative_threshold": 0,
        })


def check_tax_withholding_categories():
    """Check status of seeded Tax Withholding Categories."""
    if not frappe.db.exists("DocType", "Tax Withholding Category"):
        print("Tax Withholding Category doctype not found")
        return False

    total_twc = frappe.db.count("Tax Withholding Category")

    # Count TWCs with our naming pattern
    wht_twcs = frappe.get_all(
        "Tax Withholding Category",
        filters={"name": ["like", "WHT %"]},
        fields=["name", "pd_custom_apply_wht_to_contract_installments"]
    )

    twc_with_flag = sum(1 for t in wht_twcs if t.pd_custom_apply_wht_to_contract_installments)

    # Count linked Thai WHT Income Types
    linked = frappe.get_all(
        "Thai WHT Income Type",
        filters={"tax_withholding_category": ["is", "set"]},
        pluck="name"
    )
    total_wht = frappe.db.count("Thai WHT Income Type")

    print(f"Tax Withholding Categories: {total_twc} total, {len(wht_twcs)} WHT-related, {twc_with_flag} with contract flag")
    print(f"Thai WHT Income Types: {len(linked)}/{total_wht} linked to TWC")

    return len(linked) > 0


def apply_tax_deduction_basis_descriptions():
    """
    Add Thai-localized descriptions to tax_deduction_basis select options via Property Setter.
    This helps Thai users understand the difference without needing to read ERPNext docs.
    Also sets title_field on Tax Withholding Category so category_name shows in Link fields,
    and enables show_title_field_in_link on the Payment Entry tax_withholding_category field.
    """
    # Description for "Gross Total" option
    make_property_setter(
        "Tax Withholding Category",
        "tax_deduction_basis",
        "description",
        "Thai WHT: Gross Total = tax_base × WHT_rate | Net Total = tax_base × (1 + VAT%) × WHT_rate. "
        "Use Gross Total for most Thai WHT (services, commissions). Use Net Total for dividends, interest.",
        "Text",
    )

    # Custom options description - append Thai explanation
    make_property_setter(
        "Tax Withholding Category",
        "tax_deduction_basis",
        "options",
        "\nGross Total\nNet Total",
        "Select",
    )

    # Set title_field on Tax Withholding Category so Frappe shows category_name
    # as the human-readable title in all Link fields pointing to this doctype
    make_property_setter(
        "Tax Withholding Category",
        "",
        "title_field",
        "category_name",
        "Data",
    )

    # Enable show_title_field_in_link on Payment Entry's tax_withholding_category field
    # so the Thai category_name appears beneath the TWC name after selection
    make_property_setter(
        "Payment Entry",
        "tax_withholding_category",
        "show_title_field_in_link",
        "1",
        "Check",
    )

    frappe.db.commit()
    print("✓ Updated tax_deduction_basis descriptions for Thai users")
    print("✓ Set title_field=category_name on Tax Withholding Category")
    print("✓ Enabled show_title_field_in_link on Payment Entry.tax_withholding_category")


def cleanup_tax_deduction_basis_descriptions():
    """Remove the Property Setters on uninstall."""
    for filters in [
        {"doc_type": "Tax Withholding Category", "field_name": "tax_deduction_basis", "property": "description"},
        {"doc_type": "Tax Withholding Category", "field_name": "", "property": "title_field"},
        {"doc_type": "Payment Entry", "field_name": "tax_withholding_category", "property": "show_title_field_in_link"},
    ]:
        ps = frappe.db.exists("Property Setter", filters)
        if ps:
            frappe.delete_doc("Property Setter", ps, force=True)
            print(f"  ✓ Removed Property Setter: {filters}")

    frappe.db.commit()
    print("✓ Cleaned up tax_deduction_basis descriptions")


