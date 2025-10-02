# WHT Mixed Items Testing Verification

## Testing Status

### Implementation Complete ✅
- ✅ Enhanced `get_base_amount_for_wht()` - Detects separated service items
- ✅ Added `has_separated_service_items()` - Service item detection logic
- ✅ Added `get_service_amount_for_wht()` - Service-only amount calculation
- ✅ Maintenance/repair detection with Thai keywords
- ✅ Thai Revenue Department ruling กค 0702/9274 compliance

### Pending Testing Tasks

#### Test Case 3: Mixed Items (Service + Stock) 🔄 PRIORITY
**Scenario**: Laptop ฿50,000 + IT Consulting ฿10,000 = ฿60,000

**Expected Result**:
- WHT Base: ฿10,000 (service only)
- WHT Amount: ฿300 (3% of ฿10,000)
- Net Payment: ฿59,700

**Previous Bug Behavior**:
- WHT Base: ฿60,000 (entire invoice) ❌
- WHT Amount: ฿1,800 (3% of ฿60,000) ❌

**Test Steps**:
1. Create Purchase Invoice with:
   - Item 1: "Laptop Computer" (is_stock_item = 1) - ฿50,000
   - Item 2: "IT Consulting Service" (is_stock_item = 0) - ฿10,000
   - Grand Total: ฿60,000
2. Enable "Apply Thai WHT Compliance" checkbox
3. Set "WHT Rate" = 3%
4. Save and verify calculated values
5. Check `custom_withholding_tax_amount` = ฿300
6. Check `outstanding_amount` = ฿59,700

#### Test Case 4: Asset + Installation 🔄 PRIORITY
**Scenario**: Machinery ฿100,000 + Installation ฿10,000 = ฿110,000

**Expected Result**:
- WHT Base: ฿10,000 (installation only)
- WHT Amount: ฿300 (3% of ฿10,000)
- Net Payment: ฿109,700

**Test Steps**:
1. Create Purchase Invoice with:
   - Item 1: "Industrial Machinery" (is_fixed_asset = 1, is_stock_item = 1) - ฿100,000
   - Item 2: "Installation Service" (is_stock_item = 0) - ฿10,000
   - Grand Total: ฿110,000
2. Enable "Apply Thai WHT Compliance"
3. Set "WHT Rate" = 3%
4. Verify WHT Amount = ฿300

## Quick Testing Guide

### Prerequisites
```bash
# Ensure bench is running
cd /Users/manotlj/frappe-bench
bench start

# Clear cache to load new code
bench clear-cache
bench restart
```

### Creating Test Items

#### Service Items (is_stock_item = 0)
Navigate to: `http://localhost:8000/app/item/new`

**Item 1**: IT Consulting Service
- Item Code: SRVC-CONSULT
- Item Name: IT Consulting Service
- Item Group: Services
- Is Stock Item: ❌ (Unchecked)
- Default UOM: Hour
- Standard Rate: 10000

**Item 2**: Installation Service
- Item Code: SRVC-INSTALL
- Item Name: Installation Service
- Item Group: Services
- Is Stock Item: ❌ (Unchecked)
- Standard Rate: 10000

#### Stock Items (is_stock_item = 1)
**Item 3**: Laptop Computer
- Item Code: PROD-LAPTOP
- Item Name: Laptop Computer
- Item Group: Products
- Is Stock Item: ✅ (Checked)
- Standard Rate: 50000

#### Asset Items (is_fixed_asset = 1, is_stock_item = 1)
**Item 4**: Industrial Machinery
- Item Code: ASSET-MACHINE
- Item Name: Industrial Machinery
- Item Group: Asset
- Is Stock Item: ✅ (Checked)
- Is Fixed Asset: ✅ (Checked)
- Standard Rate: 100000

### Creating Test Purchase Invoices

Navigate to: `http://localhost:8000/app/purchase-invoice/new`

#### Test Invoice 1: Mixed Service + Stock
1. **Basic Info**:
   - Supplier: Select or create test supplier
   - Posting Date: Today
   - Company: Select your company

2. **Items Table**:
   - Row 1: PROD-LAPTOP - Qty: 1 - Rate: 50000 - Amount: 50000
   - Row 2: SRVC-CONSULT - Qty: 1 - Rate: 10000 - Amount: 10000
   - Grand Total: ฿60,000

3. **Thai WHT Section**:
   - ✅ Apply Thai WHT Compliance
   - WHT Rate: 3%
   - Supplier Tax ID: (enter test tax ID)

4. **Save and Verify**:
   - Click Save
   - Check "WHT Amount" field: Should show ฿300
   - Check "Outstanding Amount": Should show ฿59,700

#### Test Invoice 2: Asset + Installation
1. **Items Table**:
   - Row 1: ASSET-MACHINE - Qty: 1 - Rate: 100000 - Amount: 100000
   - Row 2: SRVC-INSTALL - Qty: 1 - Rate: 10000 - Amount: 10000
   - Grand Total: ฿110,000

2. **Thai WHT Section**:
   - ✅ Apply Thai WHT Compliance
   - WHT Rate: 3%

3. **Save and Verify**:
   - WHT Amount: ฿300 ✅
   - Outstanding Amount: ฿109,700 ✅

## Verification Checklist

### Code Verification ✅ COMPLETED
- [x] `get_base_amount_for_wht()` checks for separated service items
- [x] `has_separated_service_items()` detects service items (is_stock_item = 0)
- [x] `get_service_amount_for_wht()` calculates service-only amounts
- [x] Maintenance detection with Thai keywords implemented
- [x] Thai Revenue Department ruling compliance documented

### Functional Testing 🔄 PENDING
- [ ] Test Case 1: Combined item - No WHT
- [ ] Test Case 2: Pure service - WHT 3%
- [ ] Test Case 3: Mixed items - WHT on service only ⚠️ **CRITICAL**
- [ ] Test Case 4: Asset + installation - WHT on install only ⚠️ **CRITICAL**
- [ ] Test Case 5: Maintenance - WHT on total
- [ ] Test Case 6: Multiple services - WHT on all services

### Integration Testing 🔄 PENDING
- [ ] WHT certificate generation with correct base amount
- [ ] Accounting entries reflect service-only WHT
- [ ] Payment Entry WHT calculation unchanged (backward compatibility)
- [ ] WHT certificate PDF shows correct amounts
- [ ] Journal Entry creates proper GL entries

### Edge Cases Testing 🔄 PENDING
- [ ] Mixed invoice with 3+ service items
- [ ] Invoice with only stock items (no WHT)
- [ ] Invoice with only service items (full WHT)
- [ ] Maintenance item with Thai keywords detection
- [ ] Asset without installation (no WHT)
- [ ] Empty invoice validation

## Expected Behavior Summary

| Scenario | Items | WHT Base | WHT Amount | Status |
|----------|-------|----------|------------|--------|
| Combined | 1 (goods+service) | ฿0 | ฿0 | Pending |
| Pure Service | 1 service | Full amount | 3% | Pending |
| **Mixed** | Service + Stock | **Service only** | **3%** | **Priority Test** |
| **Asset + Install** | Asset + Service | **Service only** | **3%** | **Priority Test** |
| Maintenance | Parts + Repair | TOTAL | 3% | Pending |
| Multiple Services | Multiple services + stock | Sum services | 3% | Pending |

## Debug Information

### How to Check Calculated Values

1. **Enable Developer Mode**:
   ```bash
   bench --site [site-name] set-config developer_mode 1
   bench restart
   ```

2. **Check Console Output**:
   - Open browser DevTools (F12)
   - Go to Console tab
   - Create/save Purchase Invoice
   - Look for WHT calculation logs

3. **Database Verification**:
   ```bash
   bench --site [site-name] mariadb
   ```
   ```sql
   -- Check Purchase Invoice WHT calculation
   SELECT
       name,
       grand_total,
       custom_withholding_tax_amount,
       outstanding_amount
   FROM `tabPurchase Invoice`
   WHERE custom_is_withholding_tax = 1
   ORDER BY creation DESC
   LIMIT 5;
   ```

4. **Python Console Testing**:
   ```bash
   bench --site [site-name] console
   ```
   ```python
   from print_designer.custom.withholding_tax import get_service_amount_for_wht, has_separated_service_items
   import frappe

   # Get latest Purchase Invoice
   pi = frappe.get_last_doc("Purchase Invoice")

   # Test functions
   has_service = has_separated_service_items(pi)
   service_amount = get_service_amount_for_wht(pi)

   print(f"Has separated service items: {has_service}")
   print(f"Service amount for WHT: {service_amount}")
   print(f"Grand total: {pi.grand_total}")
   ```

## Success Criteria

### Critical Success Indicators ✅
1. **Mixed Invoice Test (Service + Stock)**:
   - ✅ Code detects service items via `is_stock_item = 0`
   - 🔄 WHT calculated on service amount only (฿10,000 not ฿60,000)
   - 🔄 WHT Amount = ฿300 (not ฿1,800)

2. **Asset + Installation Test**:
   - ✅ Code excludes assets from WHT base
   - 🔄 WHT calculated on installation only (฿10,000 not ฿110,000)
   - 🔄 WHT Amount = ฿300

3. **Backward Compatibility**:
   - 🔄 Pure service invoices still calculate correctly
   - 🔄 Payment Entry WHT unchanged
   - 🔄 Existing certificates remain valid

## Next Steps

### Immediate Actions Required
1. **Setup Test Environment**:
   - Create test items (SRVC-CONSULT, PROD-LAPTOP, ASSET-MACHINE, SRVC-INSTALL)
   - Create test supplier with Tax ID
   - Enable Thai WHT compliance in company settings

2. **Execute Priority Tests**:
   - Test Case 3: Mixed service + stock invoice
   - Test Case 4: Asset + installation invoice
   - Verify WHT calculations match expected values

3. **Document Test Results**:
   - Screenshot of successful test invoices
   - Record actual vs expected WHT amounts
   - Note any discrepancies or bugs

4. **Production Readiness**:
   - If tests pass: Deploy to staging environment
   - If tests fail: Debug and fix issues
   - User acceptance testing with real scenarios

## Rollback Plan (If Tests Fail)

```bash
cd /Users/manotlj/frappe-bench/apps/print_designer
git log --oneline -5
git revert <commit-hash-of-wht-fix>
bench clear-cache
bench restart
```

## Contact for Issues

If testing reveals issues, check:
1. `/Users/manotlj/frappe-bench/logs/web.error.log` - Python errors
2. Browser Console - JavaScript errors
3. `WHT_MIXED_ITEMS_TEST.md` - Test scenarios reference
4. `WHT_FIX_SUMMARY.md` - Implementation details

---

**Test Status**: Implementation Complete ✅ | Testing Pending 🔄
**Priority**: HIGH - Critical bug fix for Thai tax compliance
**Estimated Testing Time**: 1-2 hours for comprehensive testing
