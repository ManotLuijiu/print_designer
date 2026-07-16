import frappe
from frappe.utils import money_in_words


@frappe.whitelist()
def calculate_net_total_words(amount, currency="THB"):
    """Convert amount to words using Frappe's money_in_words"""
    if amount:
        return money_in_words(amount, currency)
    return ""
