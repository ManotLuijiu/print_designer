# Detailed List of 23 Sales Invoice Custom Fields

  Here are all 23 custom fields in the install_sales_invoice_fields.py file, organized by category:

  🏷️ Document Control & Watermarks

  1. watermark_text (Select)

  - Label: Document Watermark
  - Position: After is_return
  - Options: None, Original, Copy, Draft, Cancelled, Paid, Duplicate
  - Purpose: Watermark text to display on printed document
  - Features: Allow on submit, print hide, translatable

  💰 Thai Withholding Tax (WHT) System

  2. subject_to_wht (Check)

  - Label: Subject to Withholding Tax
  - Position: After taxes_and_charges
  - Purpose: Marks invoice as subject to withholding tax
  - Dependency: Visible when company is set

  3. thai_wht_preview_section (Section Break)

  - Label: Thai Ecosystem Preview (ภาษีหัก ณ ที่จ่าย/เงินประกันผลงาน)
  - Position: After named_place
  - Features: Collapsible, depends on subject_to_wht, read-only

  4. wht_amounts_column_break (Column Break)

  - Position: After thai_wht_preview_section
  - Purpose: Layout formatting for WHT section

  5. vat_treatment (Select)

  - Label: VAT Treatment
  - Position: After wht_amounts_column_break
  - Options: Standard VAT (7%), Exempt from VAT, Zero-rated for Export (0%)
  - Features: In list view, standard filter, translatable

  6. wht_income_type (Select)

  - Label: WHT Income Type
  - Position: After subject_to_wht
  - Options: professional_services, rental, service_fees, construction, advertising, other_services
  - Dependency: Shows when subject_to_wht is checked
  - Features: Read-only, no copy

  7. wht_description (Data)

  - Label: WHT Description
  - Position: After wht_income_type
  - Purpose: Thai description of WHT income type
  - Dependency: Shows when subject_to_wht is checked
  - Features: Read-only, no copy

  8. wht_certificate_required (Check)

  - Label: WHT Certificate Required
  - Position: After wht_description
  - Purpose: Customer will provide withholding tax certificate
  - Dependency: Shows when subject_to_wht is checked
  - Default: Checked (1)

  9. net_total_after_wht (Currency)

  - Label: Net Total (After WHT)
  - Position: After wht_certificate_required
  - Purpose: Net total after adding VAT (7%) and deducting WHT
  - Dependency: Shows when subject_to_wht is checked
  - Features: Read-only, company currency

  10. net_total_after_wht_in_words (Small Text)

  - Label: Net Total (After WHT) in Words
  - Position: After net_total_after_wht
  - Purpose: Net total amount in Thai words
  - Dependency: Shows when WHT is enabled AND amount exists
  - Features: Read-only

  11. wht_note (Small Text)

  - Label: WHT Note
  - Position: After net_total_after_wht_in_words
  - Purpose: Important note about WHT deduction timing
  - Default: Bilingual note (Thai/English)
  - Features: Read-only, no copy, translatable

  12. wht_preview_column_break (Column Break)

  - Position: After wht_note
  - Purpose: Layout formatting

  🏗️ Construction Retention System

  13. custom_subject_to_retention (Check)

  - Label: Subject to Retention
  - Position: After wht_preview_column_break
  - Purpose: Invoice for construction subject to retention deduction

  14. custom_net_total_after_wht_retention (Currency)

  - Label: Net Total (After WHT & Retention)
  - Position: After custom_subject_to_retention
  - Purpose: Net total after adding VAT and deducting WHT & retention
  - Dependency: Shows when retention is enabled

  15. custom_net_total_after_wht_and_retention_in_words (Data)

  - Label: Net Total (After WHT and Retention) in Words
  - Position: After custom_net_total_after_wht_retention
  - Purpose: Amount in Thai words (after WHT & retention)
  - Features: Translatable

  16. custom_retention_note (Small Text)

  - Label: Retention Note
  - Position: After custom_net_total_after_wht_and_retention_in_words
  - Purpose: Important note about retention deduction timing
  - Default: Bilingual note (Thai/English)
  - Features: Translatable

  17. custom_retention (Percent)

  - Label: Retention (%)
  - Position: After base_in_words
  - Purpose: Retention percentage to be withheld from payment
  - Dependency: Shows when retention is enabled

  18. custom_retention_amount (Currency)

  - Label: Retention Amount
  - Position: After custom_retention
  - Purpose: Calculated retention amount
  - Dependency: Shows when retention is enabled

  📊 Tax Calculations

  19. custom_withholding_tax (Percent)

  - Label: Withholding Tax (%)
  - Position: After custom_retention_amount
  - Purpose: Withholding tax percentage
  - Dependency: Shows when subject_to_wht is enabled

  20. custom_withholding_tax_amount (Currency)

  - Label: Withholding Tax Amount
  - Position: After custom_withholding_tax
  - Purpose: Calculated withholding tax amount
  - Dependency: Shows when subject_to_wht is enabled

  21. custom_payment_amount (Currency)

  - Label: Payment Amount
  - Position: After custom_withholding_tax_amount
  - Purpose: Final payment amount after all deductions
  - Dependency: Shows when retention OR WHT is enabled

  ✍️ Digital Signatures

  22. prepared_by_signature (Attach Image)

  - Label: Prepared By Signature
  - Position: After sales_team
  - Purpose: Signature of person who prepared the invoice

  23. approved_by_signature (Attach Image)

  - Label: Approved By Signature
  - Position: After prepared_by_signature
  - Purpose: Signature of person who approved the invoice

  ---
  Summary by Functionality:

  - Document Control: 1 field (watermarks)
  - Thai WHT System: 11 fields (tax calculations, notes, preview)
  - Construction Retention: 5 fields (retention calculations, notes)
  - Tax Calculations: 3 fields (percentages, amounts, final payment)
  - Digital Signatures: 2 fields (prepared by, approved by)
  - Layout Elements: 1 field (column breaks, section breaks integrated above)

  Total: 23 fields perfectly synchronized between install file and clean fixtures (excluding
  digisoft_erp fields).