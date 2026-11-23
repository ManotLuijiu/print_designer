# WHT Mixed Items Testing Guide

## Thai Revenue Department Ruling กค 0702/9274

**Date**: 10 November 2552 (2009)
**Subject**: Withholding Tax on Sales with Installation Service

## Test Scenarios Based on Thai Tax Law

### Test Case 1: Combined Invoice (Single Line Item) ❌ NO WHT
**Scenario**: Goods + service sold as single package, not separated

```
Purchase Invoice #1:
- "Conveyor System with Installation" - ฿110,000
  (is_stock_item = 1 or combined item)

Expected Result:
- WHT Amount: ฿0
- Reason: Combined item = treated as goods sale per ruling case 1
```

### Test Case 2: Separate Line Items - Service Only ✅ WHT 3%
**Scenario**: Pure service purchase

```
Purchase Invoice #2:
- Consulting Service - ฿10,000 (is_stock_item = 0)

Expected Result:
- WHT Base: ฿10,000
- WHT Amount: ฿300 (3% of ฿10,000)
- Net Payment: ฿9,700
```

### Test Case 3: Mixed Items - Service + Stock ✅ WHT 3% on Service Only
**Scenario**: Separated goods + service per ruling case 2

```
Purchase Invoice #3:
- Laptop Computer - ฿50,000 (is_stock_item = 1)
- IT Consulting - ฿10,000 (is_stock_item = 0)
Total: ฿60,000

Expected Result:
- WHT Base: ฿10,000 (service only)
- WHT Amount: ฿300 (3% of ฿10,000)
- Net Payment: ฿59,700

Previous Bug:
- WHT Base: ฿60,000 (entire invoice) ❌ WRONG
- WHT Amount: ฿1,800 (3% of ฿60,000) ❌ WRONG
```

### Test Case 4: Asset + Installation ✅ WHT 3% on Installation Only
**Scenario**: Machine purchase with separate installation service

```
Purchase Invoice #4:
- Machinery (Asset) - ฿100,000 (is_fixed_asset = 1, is_stock_item = 1)
- Installation Service - ฿10,000 (is_stock_item = 0)
Total: ฿110,000

Expected Result:
- WHT Base: ฿10,000 (installation only)
- WHT Amount: ฿300 (3% of ฿10,000)
- Net Payment: ฿109,700
```

### Test Case 5: Parts + Maintenance ✅ WHT 3% on TOTAL
**Scenario**: Repair service with parts per ruling case 4

```
Purchase Invoice #5:
- Spare Parts - ฿5,000 (is_stock_item = 1)
- Repair Service - ฿3,000 (is_stock_item = 0, item_group contains "repair")
Total: ฿8,000

Expected Result:
- WHT Base: ฿8,000 (TOTAL - special maintenance rule)
- WHT Amount: ฿240 (3% of ฿8,000)
- Net Payment: ฿7,760

Reason: Thai tax law case 4 - maintenance/repair WHT on total
```

### Test Case 6: Multiple Services + Stock ✅ WHT 3% on All Services
**Scenario**: Multiple service items with stock items

```
Purchase Invoice #6:
- Office Supplies - ฿20,000 (is_stock_item = 1)
- IT Consulting - ฿10,000 (is_stock_item = 0)
- Training Service - ฿5,000 (is_stock_item = 0)
- Equipment - ฿15,000 (is_stock_item = 1)
Total: ฿50,000

Expected Result:
- WHT Base: ฿15,000 (IT + Training services)
- WHT Amount: ฿450 (3% of ฿15,000)
- Net Payment: ฿49,550
```

## Implementation Details

### Code Changes in `withholding_tax.py`

#### 1. Enhanced `get_base_amount_for_wht()`
- Now checks for separated service items
- Calculates WHT only on service amounts in mixed purchases

#### 2. New Function: `has_separated_service_items()`
- Detects if purchase has service items as separate lines
- Returns True if ANY service item exists

#### 3. New Function: `get_service_amount_for_wht()`
- Calculates sum of service item amounts only
- Excludes stock items and assets
- **Special Rule**: Maintenance/repair → WHT on total (parts + labor)

#### 4. Maintenance Detection
- Keywords: 'repair', 'maintenance', 'ซ่อม', 'บำรุง', 'รักษา'
- Checks item_group and item description
- Applies Thai tax ruling case 4

## Testing Steps

### Step 1: Create Test Items
```sql
-- Service Items (is_stock_item = 0)
INSERT INTO `tabItem` (name, item_name, is_stock_item) VALUES
  ('SRVC-CONSULT', 'IT Consulting Service', 0),
  ('SRVC-INSTALL', 'Installation Service', 0),
  ('SRVC-REPAIR', 'Repair Service', 0),
  ('SRVC-TRAIN', 'Training Service', 0);

-- Stock Items (is_stock_item = 1)
INSERT INTO `tabItem` (name, item_name, is_stock_item) VALUES
  ('PROD-LAPTOP', 'Laptop Computer', 1),
  ('PROD-PARTS', 'Spare Parts', 1),
  ('PROD-SUPPLIES', 'Office Supplies', 1);

-- Asset Items (is_fixed_asset = 1, is_stock_item = 1)
INSERT INTO `tabItem` (name, item_name, is_stock_item, is_fixed_asset) VALUES
  ('ASSET-MACHINE', 'Industrial Machinery', 1, 1);
```

### Step 2: Create Test Purchase Invoices
1. Create each test case purchase invoice
2. Enable `apply_thai_wht_compliance = 1`
3. Set `custom_withholding_tax_rate = 3.0`
4. Submit and verify WHT calculation

### Step 3: Verify Calculations
Check each invoice:
- `custom_withholding_tax_amount` matches expected
- `outstanding_amount` = grand_total - wht_amount
- WHT certificate generated correctly

## Expected Behavior Matrix

| Scenario | Items | WHT Base | WHT Amount | Notes |
|----------|-------|----------|------------|-------|
| Combined | 1 (goods+service) | ฿0 | ฿0 | No WHT - goods sale |
| Pure Service | 1 service | Full amount | 3% | Standard service WHT |
| Mixed | Service + Stock | Service only | 3% | Key fix - was using total |
| Asset + Install | Asset + Service | Service only | 3% | Installation fee only |
| Maintenance | Parts + Repair | TOTAL | 3% | Special rule - parts+labor |
| Multiple Services | Multiple services + stock | Sum services | 3% | All services combined |

## Compliance Notes

### Thai Revenue Department Requirements
1. **Separate Billing = WHT Required**: If service is separate line or invoice
2. **Combined Billing = No WHT**: If goods+service sold as single item
3. **Maintenance Exception**: Parts + repair = WHT on total amount
4. **Installation**: Only installation fee subject to WHT, not asset cost

### Documentation Reference
- Ruling: กค 0702/9274
- Date: 10 พฤศจิกายน 2552
- Law: Section 3 ter, Revenue Code + กรมสรรพากร Order ท.ป.4/2528

## Validation Checklist

- [ ] Test Case 1: Combined item - No WHT ✅
- [ ] Test Case 2: Pure service - WHT 3% ✅
- [ ] Test Case 3: Mixed items - WHT on service only ✅
- [ ] Test Case 4: Asset + installation - WHT on install only ✅
- [ ] Test Case 5: Maintenance - WHT on total ✅
- [ ] Test Case 6: Multiple services - WHT on all services ✅
- [ ] WHT certificate generated correctly
- [ ] Accounting entries correct (WHT payable + supplier deduction)
- [ ] Payment Entry WHT still works (unchanged)

## Rollback Plan

If issues found:
```bash
cd /Users/manotlj/frappe-bench/apps/print_designer
git log --oneline -5
git revert <commit-hash>
bench restart
```

## Notes for Production

1. **Backup before deploy**: `bench backup`
2. **Test on staging first**: Create test invoices
3. **Monitor first week**: Check WHT calculations closely
4. **User training**: Explain separate line item requirement
5. **Document examples**: Provide user guide with test cases
