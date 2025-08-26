# Here are all 21 Quotation custom fields after removing estimated_wht_amount:

  Complete List of 21 Quotation Custom Fields

  🏷️ Document Control & Watermarks

  1. watermark_text (Select)
    - Label: Document Watermark
    - Position: After is_return
    - Options: None, Original, Copy, Draft, Cancelled, Duplicate

  ✍️ Digital Signatures

  2. prepared_by_signature (Attach Image)
    - Label: Prepared By Signature
    - Position: After sales_team

  💰 Thai Withholding Tax (WHT) Core

  3. subject_to_wht (Check)
    - Label: Subject to Withholding Tax
    - Position: After taxes_and_charges

  🏗️ Thai WHT Preview Section

  4. thai_wht_preview_section (Section Break)
    - Label: Thai Ecosystem Preview (ภาษีหัก ณ ที่จ่าย/เงินประกันผลงาน)
    - Position: After named_place
    - Features: Collapsible
  5. wht_amounts_column_break (Column Break)
    - Position: After thai_wht_preview_section
    - ✅ Currently showing in production
  6. vat_treatment (Select)
    - Label: VAT Treatment
    - Position: After wht_amounts_column_break
    - Options: Standard VAT (7%), Exempt from VAT, Zero-rated for Export (0%)
    - ✅ Currently showing in production

  📊 WHT Calculation Fields (Missing in production - will be fixed)

  7. wht_income_type (Select) ❌ Missing
    - Label: WHT Income Type
    - Position: After subject_to_wht
    - Options: professional_services, rental, service_fees, construction, advertising, other_services
  8. wht_description (Data) ❌ Missing
    - Label: WHT Description
    - Position: After wht_income_type
    - Purpose: Thai description of WHT income type
  9. net_total_after_wht (Currency) ❌ Missing
    - Label: Net Total (After WHT)
    - Position: After wht_description ← Fixed chain
    - Purpose: Net total after adding VAT and deducting WHT
  10. net_total_after_wht_in_words (Small Text) ❌ Missing
    - Label: Net Total (After WHT) in Words
    - Position: After net_total_after_wht
    - Purpose: Amount in Thai words
  11. wht_note (Small Text) ❌ Missing
    - Label: WHT Note
    - Position: After net_total_after_wht_in_words
    - Default: Bilingual note about WHT deduction timing

  🔄 Layout Elements

  12. wht_preview_column_break (Column Break)
    - Position: After wht_note

  🏗️ Construction Retention System

  13. custom_subject_to_retention (Check)
    - Label: Subject to Retention
    - Position: After wht_preview_column_break
  14. custom_net_total_after_wht_retention (Currency)
    - Label: Net Total (After WHT & Retention)
    - Position: After custom_subject_to_retention
  15. custom_net_total_after_wht_and_retention_in_words (Data)
    - Label: Net Total (After WHT and Retention) in Words
    - Position: After custom_net_total_after_wht_retention
  16. custom_retention_note (Small Text)
    - Label: Retention Note
    - Position: After custom_net_total_after_wht_and_retention_in_words
    - Default: Bilingual retention note

  📊 Retention Calculations

  17. custom_retention (Percent)
    - Label: Retention (%)
    - Position: After base_in_words
  18. custom_retention_amount (Currency)
    - Label: Retention Amount
    - Position: After custom_retention
  19. custom_withholding_tax (Percent)
    - Label: Withholding Tax (%)
    - Position: After custom_retention_amount
  20. custom_withholding_tax_amount (Currency)
    - Label: Withholding Tax Amount
    - Position: After custom_withholding_tax
  21. custom_payment_amount (Currency)
    - Label: Payment Amount
    - Position: After custom_withholding_tax_amount
    - Purpose: Final payment amount after all deductions

  ---
  Production Issue Status:

  ✅ Currently Working (2 fields):

  - wht_amounts_column_break
  - vat_treatment

  ❌ Missing in Production (5 WHT fields):

  - wht_income_type
  - wht_description
  - net_total_after_wht ← Now properly chains after wht_description
  - net_total_after_wht_in_words
  - wht_note

  ❓ Status Unknown (14 other fields):

  - All retention fields, signatures, and other sections

  Key Fix: Removed the problematic estimated_wht_amount field that was breaking the chain. Now
  net_total_after_wht directly follows wht_description, creating a proper field sequence that should
  install correctly in production.

  Total Count: 21 fields (down from 22 after removing estimated_wht_amount)