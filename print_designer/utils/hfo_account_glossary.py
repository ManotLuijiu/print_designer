"""
HFO (Health Financial Officer) Account Glossary - Thai Ministry of Public Health

Chart of accounts data extracted from https://hfo.moph.go.th/ChartOfAccount.aspx
This contains the official Thai Ministry of Public Health account codes and names
for healthcare financial management systems.

Account Code Format: XXXXXXXXXX.XXX (usually 10-13 digits with period)
- 1xxx: Assets (สินทรัพย์)
- 2xxx: Liabilities (หนี้สิน)
- 3xxx: Equity (ส่วนของเจ้าของ/ทุน)
- 4xxx: Income/Revenue (รายได้)
- 5xxx: Expenses (ค่าใช้จ่าย)
"""

# Thai Ministry of Public Health Chart of Accounts
HFO_ACCOUNT_GLOSSARY = {
    # === ASSETS (สินทรัพย์) - 1xxx ===

    # Cash and Cash Equivalents
    "1101010101.101": "เงินสด",
    "1101010000.000": "เงินสด",
    "1101020501.101": "เงินฝากธนาคาร - กระแสรายวัน",
    "1102010101.101": "เงินฝากธนาคาร - หน่วยงานรัฐ",
    "1102010000.000": "เงินฝากธนาคาร",
    "1102050101.201": "เงินฝากธนาคาร - ประจำ",

    # Receivables
    "1102010101.101": "ลูกหนี้เงินงวด",
    "1102010000.000": "ลูกหนี้เงินงวด",
    "1102050101.201": "ลูกหนี้ UC - OP ณ CUP",
    "1103010101.101": "ลูกหนี้การค้า - หน่วยงานรัฐ",
    "1103010000.000": "ลูกหนี้การค้า",
    "1103020111.101": "เงินทดรองราชการ",
    "1103020000.000": "เงินทดรองราชการ",

    # Inventory and Supplies
    "1105010101.101": "วัสดุคงคลัง",
    "1105000000.100": "วัสดุคงคลัง",
    "1105010199.101": "วัสดุสำนักงาน",
    "1105020101.101": "วัสดุการแพทย์",
    "1105030101.101": "วัสดุยา",

    # Fixed Assets
    "1201010101.101": "ที่ดิน",
    "1201020101.101": "อาคารและสิ่งปลูกสร้าง",
    "1201030101.101": "ครุภัณฑ์การแพทย์",
    "1201040101.101": "ครุภัณฑ์สำนักงาน",
    "1201050101.101": "ยานพาหนะ",

    # === LIABILITIES (หนี้สิน) - 2xxx ===

    # Accounts Payable
    "2101010101.102": "เจ้าหนี้การค้า - หน่วยงานรัฐ",
    "2101010000.000": "เจ้าหนี้การค้า",
    "2101020101.101": "เจ้าหนี้อื่น",

    # Accrued Expenses
    "2102010101.101": "ค่าใช้จ่ายค้างจ่าย",
    "2102020101.101": "เงินเดือนค้างจ่าย",
    "2102030101.101": "ดอกเบิ้ยค้างจ่าย",

    # Deposits and Advances
    "2102040101.101": "เงินรับฝากอื่น",
    "2102050101.101": "เงินมัดจำรับ",

    # === EQUITY (ส่วนของเจ้าของ/ทุน) - 3xxx ===

    "3101010101.101": "รายได้สูง/(ต่ำ) กว่าค่าใช้จ่าย",
    "3101000000.000": "รายได้สูง/(ต่ำ) กว่าค่าใช้จ่าย",
    "3101020101.101": "กำไร(ขาดทุน)สุทธิ",
    "3102010101.101": "ทุนสำรอง",

    # === INCOME/REVENUE (รายได้) - 4xxx ===

    # Service Revenue
    "4201010101.101": "รายได้จากการให้บริการ",
    "4201020199.101": "รายได้จากการให้บริการ - อื่นๆ",
    "4202010199.101": "รายได้จากการให้บริการ",

    # Other Income
    "4201020106.101": "รายได้จากการรับบริจาค",
    "4201020000.000": "รายได้จากการรับบริจาค",
    "4203010101.101": "รายได้ดอกเบิ้ย",
    "4204010101.101": "รายได้อื่น",

    # Government Subsidies
    "4301010101.101": "รายได้จากเงินงบประมาณ",
    "4301020101.101": "รายได้จากเงินอุดหนุน",

    # === EXPENSES (ค่าใช้จ่าย) - 5xxx ===

    # Personnel Expenses
    "5101010101.101": "เงินเดือน (ปกติ)",
    "5101010000.000": "เงินเดือนและค่าจ้าง",
    "5102010199.101": "ค่าจ้างประจำ - ในงบ (เงินงบประมาณ)",
    "5102020101.101": "ค่าจ้างชั่วคราว",
    "5103010101.101": "ค่าล่วงเวลา",
    "5103020101.101": "เงินโบนัส",

    # Operating Expenses
    "5104010104.101": "ค่าวัสดุ",
    "5104020101.101": "ค่าวัสดุการแพทย์",
    "5104030101.101": "ค่ายา",
    "5104040101.101": "ค่าเครื่องแต่งกาย",
    "5104050101.101": "ค่าเชื้อเพลิงและหล่อลื่น",

    # Utilities and Services
    "5105010101.101": "ค่าไฟฟ้า",
    "5105020101.101": "ค่าน้ำประปา",
    "5105030101.101": "ค่าโทรศัพท์",
    "5105040101.101": "ค่าไปรษณียากร",

    # Depreciation and Amortization
    "5105010101.101": "ค่าเสื่อม - ครุภัณฑ์สำนักงาน",
    "5106010101.101": "ค่าเสื่อมราคา - อาคาร",
    "5106020101.101": "ค่าเสื่อมราคา - ครุภัณฑ์",
    "5106030101.101": "ค่าเสื่อมราคา - ยานพาหนะ",

    # Maintenance and Repairs
    "5107010101.101": "ค่าซ่อมแซมและบำรุงรักษา",
    "5107020101.101": "ค่าซ่อมแซมอาคาร",
    "5107030101.101": "ค่าซ่อมแซมครุภัณฑ์",

    # Training and Development
    "5108010101.101": "ค่าฝึกอบรม",
    "5108020101.101": "ค่าสัมมนา",
    "5108030101.101": "ค่าเดินทาง",

    # Other Expenses
    "5109010101.101": "ค่าใช้จ่ายอื่น",
    "5109020101.101": "ค่าเสียหาย",
    "5109030101.101": "ค่าปรับ",
}

# Metadata about the HFO account glossary
HFO_ACCOUNT_GLOSSARY_METADATA = {
    "source": "Thai Ministry of Public Health (MOPH)",
    "source_url": "https://hfo.moph.go.th/ChartOfAccount.aspx",
    "description": "Official Chart of Accounts for Health Financial Officer (HFO) system",
    "purpose": "Healthcare financial management and reporting in Thailand",
    "account_types": {
        "1xxx": "Assets (สินทรัพย์)",
        "2xxx": "Liabilities (หนี้สิน)",
        "3xxx": "Equity (ส่วนของเจ้าของ/ทุน)",
        "4xxx": "Income/Revenue (รายได้)",
        "5xxx": "Expenses (ค่าใช้จ่าย)"
    },
    "total_accounts": len(HFO_ACCOUNT_GLOSSARY),
    "language": "Thai",
    "organization": "Ministry of Public Health, Thailand",
    "last_updated": "2024",
    "usage": "Healthcare institutions under Thai Ministry of Public Health",
    "integration_notes": "Can be used for ERPNext healthcare modules or custom health management systems"
}

# Helper functions for HFO account management
def get_account_type(account_code):
    """Get account type based on account code prefix"""
    if account_code.startswith('1'):
        return "Assets"
    elif account_code.startswith('2'):
        return "Liabilities"
    elif account_code.startswith('3'):
        return "Equity"
    elif account_code.startswith('4'):
        return "Income"
    elif account_code.startswith('5'):
        return "Expenses"
    else:
        return "Unknown"

def get_accounts_by_type(account_type):
    """Get all accounts of a specific type"""
    type_mapping = {
        "Assets": "1",
        "Liabilities": "2",
        "Equity": "3",
        "Income": "4",
        "Expenses": "5"
    }

    prefix = type_mapping.get(account_type)
    if not prefix:
        return {}

    return {code: name for code, name in HFO_ACCOUNT_GLOSSARY.items()
            if code.startswith(prefix)}

def search_accounts(search_term):
    """Search accounts by Thai name or code"""
    search_term = search_term.lower()
    results = {}

    for code, name in HFO_ACCOUNT_GLOSSARY.items():
        if search_term in name.lower() or search_term in code.lower():
            results[code] = name

    return results

# Export for use in other modules
__all__ = [
    'HFO_ACCOUNT_GLOSSARY',
    'HFO_ACCOUNT_GLOSSARY_METADATA',
    'get_account_type',
    'get_accounts_by_type',
    'search_accounts'
]