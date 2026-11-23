"""Output VAT entries recorded in the Thai Sales VAT ledger."""

from print_designer.print_designer.report.sales_vat_register import get_register_rows, make_columns

COLUMNS = (
    ("report_date", "VAT Date", "Date", None, 105),
    ("name", "Thai Sales VAT", "Link", "Thai Sales VAT", 145),
    ("sales_invoice", "Sales Invoice", "Link", "Sales Invoice", 145),
    ("tax_invoice_number", "Tax Invoice Number", "Data", None, 145),
    ("customer_name", "Customer", "Data", None, 170),
    ("customer_tax_id", "Customer Tax ID", "Data", None, 130),
    ("customer_branch", "Customer Branch", "Data", None, 120),
    ("base_amount", "Base Amount", "Float", None, 120),
    ("vat_amount", "VAT Amount", "Float", None, 115),
    ("is_vat_exempt", "VAT Exempt", "Check", None, 95),
    ("total_amount", "Total Amount", "Float", None, 120),
    ("payment_entry_reference", "Payment Entry", "Link", "Payment Entry", 145),
)


def execute(filters=None):
    fields = [field for field, *_ in COLUMNS if field != "report_date"]
    fields += ["posting_date", "tax_invoice_date", "vat_conversion_date"]
    return make_columns(COLUMNS), get_register_rows("Thai Sales VAT", filters, fields, due=True)
