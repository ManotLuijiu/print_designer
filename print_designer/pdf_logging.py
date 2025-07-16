"""
PDF Generation Logging Module for Print Designer

This module provides server-side logging functionality for PDF generation events.
"""

import json
import os
import frappe
from print_designer.logger import get_logger


@frappe.whitelist(allow_guest=False)
def log_pdf_generation_issue(event_type, message, details=None, log_level="ERROR"):
    """
    Log PDF generation issues from client-side to server-side log files.
    
    Args:
        event_type: Type of event (e.g., "PDF_GENERATION_ERROR", "PDF_FREEZE", "PDF_RETRY")
        message: Human-readable message describing the issue
        details: Additional details like URL, generator, format, etc.
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        logger = get_logger("print_designer_pdf")
        
        # Parse details if it's a string
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                pass
        
        # Prepare log entry
        log_entry = {
            "event_type": event_type,
            "message": message,
            "user": frappe.session.user,
            "timestamp": frappe.utils.now(),
            "details": details or {}
        }
        
        # Add session context
        if hasattr(frappe.local, 'request'):
            log_entry["request_info"] = {
                "url": frappe.local.request.url,
                "method": frappe.local.request.method,
                "user_agent": frappe.local.request.headers.get("User-Agent", ""),
                "remote_addr": frappe.local.request.remote_addr
            }
        
        # Log based on level
        log_message = f"[{event_type}] {message} | Details: {json.dumps(log_entry, indent=2)}"
        
        if log_level.upper() == "DEBUG":
            logger.debug(log_message)
        elif log_level.upper() == "INFO":
            logger.info(log_message)
        elif log_level.upper() == "WARNING":
            logger.warning(log_message)
        elif log_level.upper() == "CRITICAL":
            logger.critical(log_message)
        else:
            logger.error(log_message)
        
        return {"success": True, "message": "Logged successfully"}
    
    except Exception as e:
        frappe.log_error(f"PDF Logging Error: {str(e)}", "PDF Logger")
        return {"success": False, "message": f"Logging failed: {str(e)}"}


@frappe.whitelist(allow_guest=False)
def get_pdf_generation_logs(limit=50, log_level=None):
    """
    Retrieve recent PDF generation logs for debugging.
    
    Args:
        limit: Number of log entries to retrieve
        log_level: Filter by log level (optional)
    """
    try:
        log_dir = os.path.join(frappe.utils.get_bench_path(), "logs", "print_designer")
        log_file = os.path.join(log_dir, "print_designer.log")
        
        if not os.path.exists(log_file):
            return {"success": False, "message": "No log file found"}
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Get the last 'limit' lines
        recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        # Filter by log level if specified
        if log_level:
            filtered_lines = []
            for line in recent_lines:
                if f"- {log_level.upper()} -" in line:
                    filtered_lines.append(line)
            recent_lines = filtered_lines
        
        return {
            "success": True, 
            "logs": recent_lines,
            "total_lines": len(lines),
            "returned_lines": len(recent_lines)
        }
    
    except Exception as e:
        frappe.log_error(f"PDF Log Retrieval Error: {str(e)}", "PDF Logger")
        return {"success": False, "message": f"Error reading log file: {str(e)}"}


@frappe.whitelist(allow_guest=False)
def clear_pdf_generation_logs():
    """
    Clear PDF generation logs (for debugging purposes).
    """
    try:
        log_dir = os.path.join(frappe.utils.get_bench_path(), "logs", "print_designer")
        log_file = os.path.join(log_dir, "print_designer.log")
        
        if os.path.exists(log_file):
            try:
                open(log_file, 'w').close()
                return {"success": True, "message": "Logs cleared successfully"}
            except Exception as e:
                return {"success": False, "message": f"Error clearing logs: {str(e)}"}
        
        return {"success": False, "message": "No log file found"}
    
    except Exception as e:
        frappe.log_error(f"PDF Log Clear Error: {str(e)}", "PDF Logger")
        return {"success": False, "message": f"Error clearing logs: {str(e)}"}


# Simple test function to verify the module is working
@frappe.whitelist(allow_guest=False)
def test_pdf_logging():
    """Test function to verify PDF logging is working"""
    try:
        # Test basic logging
        result = log_pdf_generation_issue(
            "TEST_EVENT",
            "Test message from pdf_logging module",
            {"test": True, "module": "pdf_logging.py"},
            "INFO"
        )
        
        return {
            "success": True,
            "message": "PDF logging test successful",
            "log_result": result
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"PDF logging test failed: {str(e)}"
        }