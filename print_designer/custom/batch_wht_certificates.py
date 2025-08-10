import frappe
from frappe import _


@frappe.whitelist()
def generate_batch_wht_certificates(filters):
    """Generate WHT certificates for multiple payments"""

    # Get payment entries with WHT
    payments = frappe.get_list(
        "Payment Entry",
        filters={"apply_thai_withholding_tax": 1, "docstatus": 1, **filters},
        fields=["name", "party", "paid_amount", "posting_date"],
    )

    certificates = []
    for payment in payments:
        # Generate certificate for each payment
        doc = frappe.get_doc("Payment Entry", payment.name)
        pdf = frappe.get_print(
            "Payment Entry",
            payment.name,
            "Thai Form 50ทวิ - Official Certificate",
            as_pdf=True,
        )

        certificates.append(
            {
                "payment": payment.name,
                "party": payment.party,
                "amount": payment.paid_amount,
                "pdf": pdf,
            }
        )

    return certificates


@frappe.whitelist()
def create_wht_summary_report(from_date, to_date):
    """Create summary report of all WHT for a period"""

    sql = """
        SELECT 
            pe.name,
            pe.party,
            pe.posting_date,
            pe.income_type_selection,
            pe.custom_total_amount_paid,
            pe.custom_total_tax_withheld,
            pe.custom_party_tax_id
        FROM `tabPayment Entry` pe
        WHERE pe.apply_thai_withholding_tax = 1
        AND pe.docstatus = 1  
        AND pe.posting_date BETWEEN %s AND %s
        ORDER BY pe.posting_date
    """

    data = frappe.db.sql(sql, (from_date, to_date), as_dict=1)

    # Calculate totals
    total_paid = sum(d.custom_total_amount_paid or 0 for d in data)
    total_tax = sum(d.custom_total_tax_withheld or 0 for d in data)

    return {
        "data": data,
        "total_paid": total_paid,
        "total_tax": total_tax,
        "count": len(data),
    }
