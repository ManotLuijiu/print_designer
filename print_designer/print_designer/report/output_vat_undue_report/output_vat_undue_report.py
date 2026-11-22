"""Output VAT Undue balances and retained conversion history."""

from print_designer.print_designer.report.sales_vat_register import get_register_rows, make_columns

COLUMNS = (
    ("posting_date", "Posting Date", "Date", None, 105),
    ("name", "Output VAT Undue", "Link", "Output VAT Undue", 155),
    ("sales_invoice", "Sales Invoice", "Link", "Sales Invoice", 145),
    ("customer_name", "Customer", "Data", None, 170),
    ("status", "Status", "Data", None, 175),
    ("vat_treatment", "VAT Treatment", "Data", None, 135),
    ("company_currency", "Currency", "Link", "Currency", 90),
    ("service_base_amount", "Service Base", "Currency", "company_currency", 115),
    ("vat_amount", "VAT Amount", "Currency", "company_currency", 115),
    ("recognized_vat_amount", "Recognized VAT", "Currency", "company_currency", 130),
    ("remaining_vat_amount", "Remaining VAT", "Currency", "company_currency", 130),
    ("converted_date", "Converted On", "Date", None, 105),
    ("tax_invoice_number", "Tax Invoice Number", "Data", None, 145),
    ("tax_invoice_date", "Tax Invoice Date", "Date", None, 115),
)


def execute(filters=None):
    fields = [field for field, *_ in COLUMNS]
    return make_columns(COLUMNS), get_register_rows("Output VAT Undue", filters, fields)
