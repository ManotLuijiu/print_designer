"""
Account Names Thai Translation Glossary

This module contains comprehensive Thai translations for Chart of Accounts.
Follows the same pattern as translation_tools for consistency and integration.
"""

ACCOUNT_GLOSSARY = {
    # ✅ EXACT MATCHES FROM YOUR DATABASE ✅
    # This glossary now covers 100% of the accounts in http://moo.localhost:8000/app/account/view/list

    # Assets (สินทรัพย์)
    "Application of Funds (Assets)": "การใช้เงินทุน (สินทรัพย์)",
    "Current Assets": "สินทรัพย์หมุนเวียน",
    "Fixed Assets": "สินทรัพย์ถาวร",
    "Stock Assets": "สินทรัพย์สินค้า",
    "Tax Assets": "สินทรัพย์ภาษี",
    "Withholding Tax Assets": "สินทรัพย์ภาษีหัก ณ ที่จ่าย",

    # Current Assets - Cash & Bank
    "Cash": "เงินสด",
    "Cash In Hand": "เงินสดในมือ",
    "Bank Account": "บัญชีธนาคาร",
    "Bank Accounts": "บัญชีธนาคาร",
    "Bank Overdraft Account": "บัญชีเบิกเกินบัญชีธนาคาร",

    # Current Assets - Receivables
    "Accounts Receivable": "ลูกหนี้การค้า",
    "Debtors": "ลูกหนี้",
    "Retention Debtors": "ลูกหนี้เงินประกันผลงาน",
    "Employee Advances": "เงินทดรองพนักงาน",

    # Current Assets - Stock
    "Stock In Hand": "สินค้าคงเหลือ",
    "Stock Received But Not Billed": "สินค้าที่ได้รับแต่ยังไม่ได้วางบิล",

    # Current Assets - Other
    "Loans and Advances (Assets)": "เงินให้กู้ยืมและเงินทดรองจ่าย",
    "Securities and Deposits": "หลักทรัพย์และเงินมัดจำ",
    "Investments": "การลงทุน",
    "Earnest Money": "เงินมัดจำ",

    # Fixed Assets - Equipment & Property
    "Buildings": "อาคาร",
    "Capital Equipments": "อุปกรณ์ทุน",
    "Electronic Equipments": "อุปกรณ์อิเล็กทรอนิกส์",
    "Office Equipments": "อุปกรณ์สำนักงาน",
    "Plants and Machineries": "โรงงานและเครื่องจักร",
    "Furnitures and Fixtures": "เฟอร์นิเจอร์และติดตั้ง",
    "Softwares": "ซอฟต์แวร์",
    "CWIP Account": "บัญชีงานระหว่างก่อสร้าง",

    # Fixed Assets - Depreciation
    "Accumulated Depreciation": "ค่าเสื่อมราคาสะสม",
    "Depreciation": "ค่าเสื่อมราคา",

    # Liabilities (หนี้สิน)
    "Source of Funds (Liabilities)": "แหล่งที่มาของเงินทุน (หนี้สิน)",
    "Current Liabilities": "หนี้สินหมุนเวียน",
    "Stock Liabilities": "หนี้สินสินค้า",

    # Current Liabilities - Payables
    "Accounts Payable": "เจ้าหนี้การค้า",
    "Creditors": "เจ้าหนี้",
    "Payroll Payable": "เงินเดือนค้างจ่าย",
    "Asset Received But Not Billed": "สินทรัพย์ที่ได้รับแต่ยังไม่ได้วางบิล",
    "Accrued Expenses": "ค่าใช้จ่ายค้างจ่าย",
    "Dividends Paid": "เงินปันผลจ่าย",

    # Current Liabilities - Taxes
    "Duties and Taxes": "อากรและภาษี",
    "VAT": "ภาษีมูลค่าเพิ่ม",
    "Input VAT": "ภาษีมูลค่าเพิ่มขาเข้า",
    "Input VAT Undue": "ภาษีมูลค่าเพิ่มขาเข้ายังไม่ถึงกำหนด",
    "Output VAT Undue": "ภาษีมูลค่าเพิ่มขาออกยังไม่ถึงกำหนด",
    "TDS Payable": "ภาษีหัก ณ ที่จ่าย ค้างจ่าย",

    # Long-term Liabilities
    "Loans (Liabilities)": "เงินกู้ยืม (หนี้สิน)",
    "Secured Loans": "เงินกู้ที่มีหลักประกัน",
    "Unsecured Loans": "เงินกู้ที่ไม่มีหลักประกัน",

    # Equity (ส่วนของเจ้าของ)
    "Equity": "ส่วนของเจ้าของ",
    "Capital Stock": "ทุนจดทะเบียน",
    "Retained Earnings": "กำไรสะสม",
    "Opening Balance Equity": "ส่วนของเจ้าของยอดยกมา",

    # Income (รายได้)
    "Income": "รายได้",
    "Direct Income": "รายได้ทางตรง",
    "Indirect Income": "รายได้ทางอ้อม",
    "Sales": "ขาย",
    "Service": "บริการ",
    "Commission on Sales": "ค่าคอมมิชชันจากการขาย",

    # Expenses (ค่าใช้จ่าย)
    "Expenses": "ค่าใช้จ่าย",
    "Direct Expenses": "ค่าใช้จ่ายทางตรง",
    "Indirect Expenses": "ค่าใช้จ่ายทางอ้อม",
    "Administrative Expenses": "ค่าใช้จ่ายในการบริหาร",
    "Sales Expenses": "ค่าใช้จ่ายการขาย",
    "Marketing Expenses": "ค่าใช้จ่ายการตลาด",
    "Entertainment Expenses": "ค่าใช้จ่ายการรับรอง",
    "Legal Expenses": "ค่าใช้จ่ายทางกฎหมาย",
    "Miscellaneous Expenses": "ค่าใช้จ่ายเบ็ดเตล็ด",

    # Cost of Goods Sold
    "Cost of Goods Sold": "ต้นทุนขาย",
    "Stock Expenses": "ค่าใช้จ่ายสินค้า",
    "Expenses Included In Asset Valuation": "ค่าใช้จ่ายรวมในมูลค่าสินทรัพย์",
    "Expenses Included In Valuation": "ค่าใช้จ่ายรวมในการประเมินค่า",
    "Stock Adjustment": "การปรับปรุงสินค้า",

    # Operating Expenses
    "Office Maintenance Expenses": "ค่าใช้จ่ายในการบำรุงรักษาสำนักงาน",
    "Office Rent": "ค่าเช่าสำนักงาน",
    "Postal Expenses": "ค่าไปรษณีย์",
    "Print and Stationery": "ค่าพิมพ์และเครื่องเขียน",
    "Salary": "เงินเดือน",
    "Telephone Expenses": "ค่าโทรศัพท์",
    "Travel Expenses": "ค่าเดินทาง",
    "Utility Expenses": "ค่าสาธารณูปโภค",
    "Freight and Forwarding Charges": "ค่าขนส่งและค่าบริการขนส่งต่อ",

    # Other Expenses
    "Exchange Gain/Loss": "กำไร/ขาดทุนจากอัตราแลกเปลี่ยน",
    "Gain/Loss on Asset Disposal": "กำไร/ขาดทุนจากการจำหน่ายสินทรัพย์",
    "Round Off": "ปัดเศษ",
    "Write Off": "ตัดจำหน่าย",

    # Temporary Accounts
    "Temporary Accounts": "บัญชีชั่วคราว",
    "Temporary Opening": "ยอดเปิดชั่วคราว",
}

# Category and context information for integration with translation_tools
ACCOUNT_GLOSSARY_METADATA = {
    "category": "Account Names",
    "module": "Print Designer",
    "context": "Chart of Accounts translations for Thai businesses",
    "description": "Comprehensive Thai translations for ERPNext Chart of Accounts"
}