# WHT User Guide - Mixed Items (Thai Tax Compliance)

## Quick Reference: When Does WHT Apply?

### ✅ YES - WHT 3% Required
1. **Separate Service Items**: Service as separate line in invoice
2. **Asset + Installation**: Installation service separated from asset
3. **Maintenance/Repair**: Parts + labor (WHT on total amount)
4. **Multiple Services**: Each service as separate line

### ❌ NO - WHT Not Required
1. **Combined Item**: "Machine with Installation" as single item
2. **Pure Goods**: Only stock items, no services
3. **Services < ฿1,000**: Below minimum threshold

## Common Scenarios

### Scenario 1: IT Consulting + Equipment Purchase ✅
**How to Create Invoice**:
```
Line 1: IT Consulting Service - ฿10,000 (Service Item)
Line 2: Laptop Computer - ฿50,000 (Stock Item)
Total: ฿60,000

Enable: "Apply Thai WHT Compliance" ✓
Set Rate: 3%
```

**Result**:
- WHT Base: ฿10,000 (consulting only)
- WHT Amount: ฿300
- Net Payment: ฿59,700

**Why**: Service separated from goods → WHT on service only

---

### Scenario 2: Machine Installation ✅
**How to Create Invoice**:
```
Line 1: Industrial Machine - ฿100,000 (Asset Item)
Line 2: Installation Service - ฿10,000 (Service Item)
Total: ฿110,000

Enable: "Apply Thai WHT Compliance" ✓
Set Rate: 3%
```

**Result**:
- WHT Base: ฿10,000 (installation only)
- WHT Amount: ฿300
- Net Payment: ฿109,700

**Why**: Installation fee separated → WHT on installation only

---

### Scenario 3: Equipment Repair ✅
**How to Create Invoice**:
```
Line 1: Spare Parts - ฿5,000 (Stock Item)
Line 2: Repair Service - ฿3,000 (Service Item with "repair" in description)
Total: ฿8,000

Enable: "Apply Thai WHT Compliance" ✓
Set Rate: 3%
```

**Result**:
- WHT Base: ฿8,000 (TOTAL amount)
- WHT Amount: ฿240
- Net Payment: ฿7,760

**Why**: Maintenance/repair special rule → WHT on total (parts + labor)

---

### Scenario 4: Combined Package ❌
**How to Create Invoice**:
```
Line 1: "Conveyor System with Installation" - ฿110,000 (Single Combined Item)
Total: ฿110,000

Enable: "Apply Thai WHT Compliance" ✓
Set Rate: 3%
```

**Result**:
- WHT Base: ฿0
- WHT Amount: ฿0
- Net Payment: ฿110,000

**Why**: Combined item = treated as goods sale (no WHT per Thai tax law)

**Fix**: Separate into two lines if you need WHT:
- Line 1: Conveyor System - ฿100,000
- Line 2: Installation - ฿10,000

---

## Step-by-Step: Creating WHT Invoice

### Step 1: Create Purchase Invoice
1. Go to **Buying → Purchase Invoice → New**
2. Select Supplier
3. Add items line by line

### Step 2: Configure Items Correctly
**For Services** (WHT applies):
- Item Type: **Service** (is_stock_item = No)
- Examples: Consulting, Installation, Training, Repair

**For Goods** (WHT doesn't apply):
- Item Type: **Stock** or **Asset**
- Examples: Equipment, Supplies, Machinery

### Step 3: Enable WHT
1. Check: **"Apply Thai WHT Compliance"** ✓
2. Set: **"WHT Rate"** = 3% (or appropriate rate)
3. System auto-calculates WHT on service items only

### Step 4: Verify Calculation
Check these fields:
- **Tax Base Amount**: Should show service amount only (not total)
- **WHT Amount**: 3% of service amount
- **Outstanding Amount**: Total - WHT

### Step 5: Submit and Create Certificate
- Click **Submit**
- WHT Certificate auto-generated
- Payment Entry will deduct WHT automatically

---

## Thai Tax Law Quick Guide

### Legal Basis
**Thai Revenue Department Ruling กค 0702/9274** (10 November 2552)

### Four Rules:

#### Rule 1: Combined Item → No WHT
- Goods + service sold as **single package**
- One line item, no separation
- Treated as **goods sale** (ไม่หัก ณ ที่จ่าย)

#### Rule 2: Separate Items → WHT on Service
- Goods and service as **different lines**
- OR separate invoices
- WHT **3%** on service amount only

#### Rule 3: Pure Goods → No WHT
- Only stock items
- No services involved
- No WHT required

#### Rule 4: Maintenance → WHT on Total
- Repair/maintenance service
- Includes parts + labor
- WHT **3%** on **combined amount** (parts + labor)
- Keywords: "repair", "maintenance", "ซ่อม", "บำรุง"

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Not Separating Services
**Wrong**:
```
Line 1: "Machine with Installation" - ฿110,000
```
**Result**: No WHT (combined item)

**Correct**:
```
Line 1: Machine - ฿100,000
Line 2: Installation - ฿10,000
```
**Result**: WHT ฿300 on installation

---

### ❌ Mistake 2: Wrong Item Type
**Wrong**:
```
Line 1: "Consulting" (Stock Item) - ฿10,000
```
**Result**: No WHT (system sees it as goods)

**Correct**:
```
Line 1: "Consulting" (Service Item) - ฿10,000
```
**Result**: WHT ฿300

**How to Fix**: Edit Item Master → Set "Is Stock Item" = No

---

### ❌ Mistake 3: Forgetting WHT Enable
**Wrong**:
```
"Apply Thai WHT Compliance" = unchecked
```
**Result**: No WHT calculated

**Correct**:
```
"Apply Thai WHT Compliance" = checked ✓
"WHT Rate" = 3%
```

---

## Checklist: Before Submitting Invoice

- [ ] Services are separate line items (not combined with goods)
- [ ] Service items marked as "Service" type (is_stock_item = No)
- [ ] "Apply Thai WHT Compliance" checkbox enabled ✓
- [ ] WHT Rate set correctly (usually 3%)
- [ ] Review calculated WHT amount (should be on services only)
- [ ] Verify outstanding amount (total - WHT)
- [ ] Supplier has Tax ID entered

---

## Troubleshooting

### Problem: WHT Calculated on Entire Invoice
**Cause**: Old system bug (now fixed)
**Solution**:
- System now auto-detects service items
- WHT calculated on services only
- If still wrong, check item types

### Problem: No WHT Calculated
**Check**:
1. Is "Apply Thai WHT Compliance" enabled? ✓
2. Is WHT Rate set? (3%)
3. Are there service items? (is_stock_item = No)
4. Is invoice amount ≥ ฿1,000?

### Problem: WHT on Maintenance Wrong
**If repair/maintenance**:
- Should calculate on total (parts + labor)
- Check if item description has "repair" keyword
- System detects: repair, maintenance, ซ่อม, บำรุง, รักษา

### Problem: Can't Find WHT Certificate
**Location**:
- Auto-created on Purchase Invoice submit
- Go to: **Accounting → Withholding Tax Certificate**
- Or click link in Purchase Invoice

---

## Examples by Industry

### IT Services
```
Consulting - ฿15,000 (Service) → WHT ฿450
Software License - ฿20,000 (Goods) → No WHT
Training - ฿5,000 (Service) → WHT ฿150
Total WHT: ฿600 (on ฿20,000 services)
```

### Construction
```
Materials - ฿50,000 (Stock) → No WHT
Installation - ฿10,000 (Service) → WHT ฿300
Total WHT: ฿300 (on ฿10,000 installation)
```

### Manufacturing
```
Machine - ฿200,000 (Asset) → No WHT
Installation - ฿15,000 (Service) → WHT ฿450
Training - ฿5,000 (Service) → WHT ฿150
Total WHT: ฿600 (on ฿20,000 services)
```

### Maintenance
```
Spare Parts - ฿8,000 (Stock) → Part of WHT base
Repair Labor - ฿4,000 (Service) → Part of WHT base
Total WHT: ฿360 (3% of ฿12,000 total - special rule)
```

---

## FAQs

**Q1: Can I combine goods and services in one line?**
A: Yes, but no WHT will apply (treated as goods sale). Separate them if you need WHT.

**Q2: What if supplier complains about WHT amount?**
A: Show them the invoice breakdown. WHT applies only to service amounts per Thai tax law.

**Q3: Do I need separate invoices for goods and services?**
A: No, separate LINE ITEMS in same invoice is sufficient.

**Q4: What WHT rate should I use?**
A:
- General services: 3%
- Professional services: 5%
- Advertising: 2%
- Transportation: 1%
- Rental: 5%

**Q5: When do I need to pay WHT to Revenue Department?**
A: Within 7 days of month-end. File PND forms by deadline.

**Q6: Can I skip WHT for small amounts?**
A: Minimum threshold is ฿1,000 per transaction, but always check current regulations.

---

## Contact Support

**Technical Issues**: [Your IT Support Email]
**Tax Questions**: [Your Accounting Team]
**System Training**: [Your Training Coordinator]

**Thai Revenue Department Hotline**: 1161
**Reference Document**: กค 0702/9274 (10 Nov 2552)

---

## System Updates

**Latest Update**: Mixed Items WHT Fix
**What Changed**: System now correctly calculates WHT on service items only in mixed purchases
**Action Required**: None - automatic for all new invoices
**Old Invoices**: Unchanged, only new invoices use corrected calculation
