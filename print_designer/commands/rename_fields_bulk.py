#!/usr/bin/env python3
"""
Bulk field rename script for print_designer custom fields.
Replaces old unprefixed field names with pd_custom_* prefixed names.

Phase B: Install scripts (Quotation, PI, PO, PE)
Phase C: Business logic Python files
Phase D: JS files
Phase E: Cross-app references

Run via: python3 apps/print_designer/print_designer/commands/rename_fields_bulk.py
"""

import os
import re

# ============================================================
# RENAME MAPPING: old_name → new_name
# ============================================================

# Common fields shared across multiple DocTypes
COMMON_RENAMES = {
    "watermark_text": "pd_custom_watermark_text",
    "prepared_by_signature": "pd_custom_prepared_by_signature",
    "approved_by_signature": "pd_custom_approved_by_signature",
    "thai_wht_preview_section": "pd_custom_wht_preview_section",
    "wht_amounts_column_break": "pd_custom_wht_amounts_cb",
    "vat_treatment": "pd_custom_vat_treatment",
    "subject_to_wht": "pd_custom_subject_to_wht",
    "wht_income_type": "pd_custom_wht_income_type",
    "wht_description": "pd_custom_wht_description",
    "net_total_after_wht": "pd_custom_net_total_after_wht",
    "net_total_after_wht_in_words": "pd_custom_net_total_after_wht_words",
    "wht_certificate_required": "pd_custom_wht_certificate_required",
    "wht_note": "pd_custom_wht_note",
    "wht_preview_column_break": "pd_custom_wht_preview_cb",
    "custom_subject_to_retention": "pd_custom_subject_to_retention",
    "custom_retention": "pd_custom_retention_pct",
    "custom_retention_amount": "pd_custom_retention_amount",
    "custom_net_total_after_wht_retention": "pd_custom_net_after_wht_retention",
    "custom_net_total_after_wht_retention_in_words": "pd_custom_net_after_wht_retention_words",
    "custom_retention_note": "pd_custom_retention_note",
    "custom_withholding_tax": "pd_custom_withholding_tax_pct",
    "custom_withholding_tax_amount": "pd_custom_withholding_tax_amount",
    "custom_payment_amount": "pd_custom_payment_amount",
}

# PI/PO-specific fields
PI_PO_RENAMES = {
    "apply_thai_wht_compliance": "pd_custom_apply_thai_wht_compliance",
    "thai_tax_compliance_section": "pd_custom_tax_compliance_section",
    "bill_cash": "pd_custom_bill_cash",
}

# SO-specific deposit fields
SO_DEPOSIT_RENAMES = {
    "section_break_o8q38": "pd_custom_deposit_section",
    "has_deposit": "pd_custom_has_deposit",
    "deposit_invoice": "pd_custom_deposit_invoice",
    "column_break_euapx": "pd_custom_deposit_cb",
    "percent_deposit": "pd_custom_percent_deposit",
    "deposit_deduction_method": "pd_custom_deposit_deduction_method",
}

# SI-specific QR fields
SI_QR_RENAMES = {
    "custom_invoice_qr_section": "pd_custom_qr_section",
    "custom_show_qr_on_print": "pd_custom_show_qr_on_print",
    "custom_invoice_qr_code": "pd_custom_qr_code",
    "custom_invoice_qr_image": "pd_custom_qr_image",
    "custom_invoice_qr_url": "pd_custom_qr_url",
    "custom_invoice_qr_column_break": "pd_custom_qr_cb",
    "custom_invoice_qr_generated_on": "pd_custom_qr_generated_on",
    "custom_invoice_qr_data_version": "pd_custom_qr_data_version",
}

# ============================================================
# FILES TO PROCESS
# ============================================================

BENCH_ROOT = "/home/frappe/frappe-bench/apps"

# Skip these directories/files
SKIP_PATTERNS = [
    "/patches/",
    "/.git/",
    "/node_modules/",
    "/__pycache__/",
    "/rename_fields_bulk.py",  # Don't modify this script itself
    # Already updated in Phase A:
    "/commands/install_sales_invoice_fields.py",
    "/commands/install_sales_order_fields.py",
]


def should_skip(filepath):
    """Check if file should be skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern in filepath:
            return True
    return False


def get_all_renames():
    """Get the complete rename mapping."""
    renames = {}
    renames.update(COMMON_RENAMES)
    renames.update(PI_PO_RENAMES)
    # Don't include SO_DEPOSIT_RENAMES or SI_QR_RENAMES in bulk - they're too specific
    # and already handled in Phase A install scripts
    return renames


def replace_in_file(filepath, renames, dry_run=False):
    """Replace old field names with new ones in a single file.

    Uses word-boundary-aware replacement to avoid partial matches.
    E.g., won't replace 'subject_to_wht' inside 'pd_custom_subject_to_wht'.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original = f.read()
    except (UnicodeDecodeError, PermissionError):
        return []

    content = original
    changes = []

    # Sort renames by length (longest first) to avoid partial replacements
    sorted_renames = sorted(renames.items(), key=lambda x: len(x[0]), reverse=True)

    for old_name, new_name in sorted_renames:
        if old_name not in content:
            continue

        # Skip if already renamed (e.g., pd_custom_subject_to_wht already exists)
        # Use negative lookbehind to avoid replacing inside already-prefixed names
        # Pattern: match old_name but NOT when preceded by pd_custom_ or other prefix

        # Count occurrences that are NOT already part of the new name
        # Simple approach: replace only if old_name appears without being part of new_name

        # Build a regex that matches old_name as a "word" but not inside the new_name
        # We need to handle various contexts:
        # - Python: "old_name", doc.old_name, doc.get("old_name")
        # - JS: doc.old_name, frm.doc.old_name, 'old_name'
        # - Jinja: doc.old_name
        # - Field definitions: "fieldname": "old_name", "insert_after": "old_name"

        # Use word boundary that works for field names (letters, digits, underscores)
        # Negative lookbehind for alphanumeric/underscore to avoid partial match
        pattern = r'(?<![a-zA-Z0-9_])' + re.escape(old_name) + r'(?![a-zA-Z0-9_])'

        matches = list(re.finditer(pattern, content))
        if not matches:
            continue

        # Filter out matches that are inside the new_name (already renamed)
        real_matches = []
        for m in matches:
            start = m.start()
            # Check if this match is part of the new_name
            # Look backwards for pd_custom_ prefix
            prefix_start = max(0, start - len("pd_custom_"))
            preceding = content[prefix_start:start]
            if "pd_custom_" in preceding:
                continue  # Already part of a pd_custom_ name
            real_matches.append(m)

        if not real_matches:
            continue

        # Do the replacement
        new_content = re.sub(pattern, lambda m: new_name if not _is_already_prefixed(content, m.start()) else m.group(), content)

        if new_content != content:
            count = len(real_matches)
            changes.append(f"  {old_name} → {new_name} ({count} occurrences)")
            content = new_content

    if changes and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return changes


def _is_already_prefixed(content, pos):
    """Check if the match at pos is already part of a pd_custom_ name."""
    prefix = "pd_custom_"
    prefix_start = max(0, pos - len(prefix))
    preceding = content[prefix_start:pos]
    return prefix in preceding


def process_directory(directory, renames, extensions, dry_run=False):
    """Process all matching files in a directory tree."""
    total_changes = {}

    for root, dirs, files in os.walk(directory):
        for fname in files:
            if not any(fname.endswith(ext) for ext in extensions):
                continue

            filepath = os.path.join(root, fname)

            if should_skip(filepath):
                continue

            changes = replace_in_file(filepath, renames, dry_run)
            if changes:
                # Make path relative for readability
                rel_path = filepath.replace(BENCH_ROOT + "/", "")
                total_changes[rel_path] = changes

    return total_changes


def main(dry_run=False):
    """Main execution function."""
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"  Field Rename Bulk Update ({mode})")
    print(f"{'='*60}\n")

    renames = get_all_renames()
    print(f"Total rename mappings: {len(renames)}")

    all_changes = {}

    # Phase B + C + D: print_designer app (Python + JS + HTML)
    print("\n--- Processing: print_designer ---")
    pd_dir = os.path.join(BENCH_ROOT, "print_designer")
    changes = process_directory(pd_dir, renames, [".py", ".js", ".html"], dry_run)
    all_changes.update(changes)

    # Phase E: digisoft_erp
    print("\n--- Processing: digisoft_erp ---")
    dgs_dir = os.path.join(BENCH_ROOT, "digisoft_erp")
    if os.path.exists(dgs_dir):
        changes = process_directory(dgs_dir, renames, [".py", ".js", ".html"], dry_run)
        all_changes.update(changes)

    # Phase E: inpac_pharma
    print("\n--- Processing: inpac_pharma ---")
    ip_dir = os.path.join(BENCH_ROOT, "inpac_pharma")
    if os.path.exists(ip_dir):
        changes = process_directory(ip_dir, renames, [".py", ".js", ".html"], dry_run)
        all_changes.update(changes)

    # Phase E: thai_business_suite
    print("\n--- Processing: thai_business_suite ---")
    tbs_dir = os.path.join(BENCH_ROOT, "thai_business_suite")
    if os.path.exists(tbs_dir):
        changes = process_directory(tbs_dir, renames, [".py", ".js", ".html"], dry_run)
        all_changes.update(changes)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY ({mode})")
    print(f"{'='*60}")

    if all_changes:
        total_files = len(all_changes)
        total_replacements = sum(len(v) for v in all_changes.values())
        print(f"\nFiles modified: {total_files}")
        print(f"Total replacements: {total_replacements}")
        print()

        for filepath, changes in sorted(all_changes.items()):
            print(f"📄 {filepath}")
            for change in changes:
                print(f"   {change}")
            print()
    else:
        print("\nNo changes needed - all fields already renamed!")

    return all_changes


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    main(dry_run=dry_run)
