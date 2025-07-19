import frappe
from frappe import _
import json
from datetime import datetime


@frappe.whitelist()
def log_pdf_generation_issue(event_type, message, details, log_level="INFO"):
    """Log PDF generation issues to server"""
    try:
        # Create a log entry in Error Log or custom doctype
        frappe.log_error(
            title=f"PDF Generation: {event_type}",
            message=f"{message}\n\nDetails: {details}",
            reference_doctype="Print Format",
        )

        return {"success": True, "message": "Logged successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_pdf_generation_logs(limit=50, log_level=None):
    """Get recent PDF generation logs"""
    try:
        filters = {"error": ["like", "%PDF Generation%"]}
        if log_level:
            filters["error"] = ["like", f"%{log_level}%"]

        logs = frappe.get_list(
            "Error Log",
            filters=filters,
            fields=["creation", "error", "reference_doctype"],
            order_by="creation desc",
            limit=limit,
        )

        formatted_logs = []
        for log in logs:
            formatted_logs.append(f"[{log.creation}] {log.error}")

        return {"success": True, "logs": formatted_logs}
    except Exception as e:
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def clear_pdf_generation_logs():
    """Clear PDF generation logs"""
    try:
        # Delete logs older than 7 days with PDF Generation in the title
        frappe.db.sql("""
            DELETE FROM `tabError Log`
            WHERE error LIKE '%PDF Generation%'
            AND creation < DATE_SUB(NOW(), INTERVAL 7 DAY)
        """)

        frappe.db.commit()
        return {"success": True, "message": "Logs cleared successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
