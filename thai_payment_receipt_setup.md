# Thai Tax Invoice for Payment Entry - Setup Guide

This guide explains how to use the Thai Tax Invoice format for Payment Entry that shows items from referenced Sales Invoices, meeting Thai tax law requirements.

## ✅ Installation Complete

The Thai Tax Invoice format has been installed successfully! 

## 🎯 Features

### ✅ **Thai Tax Compliance**
- Shows items from referenced Sales Invoices
- Dual language (Thai/English) labels
- Tax calculation details
- Proper signature areas

### ✅ **Automatic Item Extraction**
- Pulls items from all referenced Sales Invoices
- Shows item codes, descriptions, quantities, rates, and amounts
- Displays invoice references
- Calculates totals

### ✅ **Professional Layout**
- Company header with tax invoice designation
- Document information section
- Detailed items table
- Payment summary
- Signature sections for compliance

## 📋 How to Use

### Step 1: Create Payment Entry with Invoice References
1. Go to **Accounts > Payment Entry**
2. Create a new Payment Entry
3. In the **References** section, add the Sales Invoices you're receiving payment for
4. Save and Submit the Payment Entry

### Step 2: Print Thai Tax Invoice
1. Open the Payment Entry
2. Click **Print**
3. Select **"Payment Entry Thai Tax Invoice"** from the format dropdown
4. The print will show:
   - All items from referenced Sales Invoices
   - Tax details and totals
   - Thai and English labels
   - Proper tax invoice format

## 🛠️ Customization

### Modify the Format
1. Go to **Settings > Print Format**
2. Find **"Payment Entry Thai Tax Invoice"**
3. Click **Edit**
4. Use Print Designer to customize:
   - Colors and fonts
   - Logo placement
   - Additional fields
   - Layout adjustments

### Add Company Logo
1. Go to **Settings > Company**
2. Upload your company logo
3. The format will automatically include it

## 🔧 Technical Details

### What the Format Does
```python
# The format automatically:
# 1. Loops through all references in Payment Entry
# 2. For each Sales Invoice reference:
#    - Fetches the full invoice document
#    - Extracts all items with details
#    - Collects tax information
# 3. Displays everything in a professional format
```

### Jinja Template Logic
The format uses advanced Jinja templating to:
- Extract items from referenced invoices
- Calculate running totals
- Format currency properly
- Handle multiple invoice references
- Display tax information

## 🇹🇭 Thai Tax Law Compliance

### What's Included
- **ใบกำกับภาษี (Tax Invoice)**: Proper header designation
- **รายการสินค้า (Items List)**: Complete item details
- **การอ้างอิง (References)**: Links to original invoices
- **ลายเซ็น (Signatures)**: Required signature areas
- **วันที่ (Dates)**: Proper date formatting

### Tax Invoice Requirements Met
✅ Company name and address  
✅ Document number and date  
✅ Customer information  
✅ Detailed item list  
✅ Tax calculations  
✅ Total amounts  
✅ Signature areas  

## 📊 Example Workflow

### Scenario: Restaurant Receipt
1. **Sales Invoice**: Customer orders food items
   - Item 1: Tom Yum Soup - 150 THB
   - Item 2: Pad Thai - 120 THB
   - Tax: 21.60 THB (8%)
   - Total: 291.60 THB

2. **Payment Entry**: Customer pays
   - References: Sales Invoice above
   - Payment Method: Cash
   - Amount: 291.60 THB

3. **Thai Tax Invoice Print**: Shows
   - Complete food items list
   - Tax breakdown
   - Payment details
   - Thai/English labels
   - Compliance format

## 🆘 Troubleshooting

### Format Not Showing Items?
- Ensure Payment Entry has references to Sales Invoices
- Check that Sales Invoices contain items
- Verify the invoices are submitted

### Missing Thai Fonts?
- Install Sarabun font on your system
- Use Print Designer to set font preferences

### Need Different Layout?
- Use Print Designer to customize the format
- Modify colors, spacing, and fields as needed

## 🔄 Updates

### Reinstall Format
If you need to reinstall or update the format:
```bash
bench --site [site-name] install-thai-payment-format
```

This will update the existing format with any improvements.

---

**📞 Support**: This format was created using Print Designer's advanced Jinja templating capabilities to meet Thai tax compliance requirements while maintaining ERPNext's standard workflow.