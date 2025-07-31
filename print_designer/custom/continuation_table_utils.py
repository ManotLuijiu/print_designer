"""
Utilities for continuation table functionality
"""

import frappe
from frappe.utils import flt
from typing import Dict, List, Any, Union


def calculate_table_running_totals(table_data: List[Dict], total_columns: List[str]) -> Dict[str, float]:
    """Calculate running totals for specified columns in table data"""
    running_totals = {}
    
    if not table_data or not total_columns:
        return running_totals
    
    # Initialize totals
    for column in total_columns:
        running_totals[column] = 0.0
    
    # Calculate totals
    for row in table_data:
        for column in total_columns:
            if column in row:
                running_totals[column] += flt(row.get(column, 0))
    
    return running_totals


def get_table_page_total(page_data: List[Dict], column_fieldname: str) -> float:
    """Calculate total for a specific column in a page of data"""
    total = 0.0
    
    if not page_data:
        return total
    
    for row in page_data:
        if column_fieldname in row:
            total += flt(row.get(column_fieldname, 0))
    
    return total


def get_continuation_table_config(element: Dict) -> Dict:
    """Get continuation table configuration with defaults"""
    continuation_config = element.get("continuationConfig", {})
    
    # Set default values
    defaults = {
        "enabled": False,
        "mode": "before",  # "before" (original multiple tables) or "after" (single continuation table) - using "before" as default per user request
        "rowsPerPage": 10,
        "minRowsDisplay": 10,  # Minimum rows to display (fill with empty rows if needed)
        "useFixedHeight": True,  # Use fixed height instead of dynamic
        "showEmptyRows": True,  # Show empty rows to fill minimum
        "showRunningTotals": True,
        "showBalanceForward": True,
        "continuationHeader": "Continued from previous page",
        "continuationFooter": "Continued on next page",
        "totalColumns": [],
        "pageNumbering": True,
        "showPageTotals": True
    }
    
    # Merge with provided config
    for key, default_value in defaults.items():
        if key not in continuation_config:
            continuation_config[key] = default_value
    
    return continuation_config


def split_table_data_by_pages(table_data: List[Dict], rows_per_page: int) -> List[List[Dict]]:
    """Split table data into pages based on rows per page"""
    if not table_data:
        return []
    
    pages = []
    total_rows = len(table_data)
    
    for i in range(0, total_rows, rows_per_page):
        page_data = table_data[i:i + rows_per_page]
        pages.append(page_data)
    
    return pages


def format_continuation_value(value: Any, column_config: Dict = None) -> str:
    """Format value for display in continuation table"""
    if column_config is None:
        column_config = {}
    
    if value is None:
        return ""
    
    # Handle numeric values
    if isinstance(value, (int, float)):
        decimal_places = column_config.get("decimal_places", 2)
        if decimal_places == 0:
            return "{:,.0f}".format(value)
        else:
            return "{:,.{}f}".format(value, decimal_places)
    
    # Handle dates
    if hasattr(value, 'strftime'):
        date_format = column_config.get("date_format", "%d-%m-%Y")
        return value.strftime(date_format)
    
    # Handle other types
    return str(value)


def validate_continuation_config(continuation_config: Dict) -> Dict:
    """Validate and sanitize continuation configuration"""
    errors = []
    
    # Validate required fields
    if continuation_config.get("enabled") and not continuation_config.get("rowsPerPage"):
        errors.append("Rows per page is required when continuation is enabled")
    
    # Validate numeric values
    rows_per_page = continuation_config.get("rowsPerPage", 10)
    if not isinstance(rows_per_page, int) or rows_per_page < 1:
        errors.append("Rows per page must be a positive integer")
        continuation_config["rowsPerPage"] = 10
    
    # Validate total columns
    total_columns = continuation_config.get("totalColumns", [])
    if not isinstance(total_columns, list):
        errors.append("Total columns must be a list")
        continuation_config["totalColumns"] = []
    
    # Validate strings
    for field in ["continuationHeader", "continuationFooter"]:
        if field in continuation_config and not isinstance(continuation_config[field], str):
            continuation_config[field] = str(continuation_config[field])
    
    return {
        "config": continuation_config,
        "errors": errors
    }


@frappe.whitelist()
def get_table_data_preview(doctype: str, docname: str, fieldname: str, rows_per_page: int = 10) -> Dict:
    """Get preview of how table data will be split across pages"""
    try:
        doc = frappe.get_doc(doctype, docname)
        table_data = doc.get(fieldname) or []
        
        if not table_data:
            return {
                "success": True,
                "total_rows": 0,
                "total_pages": 0,
                "pages": []
            }
        
        pages = split_table_data_by_pages(table_data, rows_per_page)
        
        return {
            "success": True,
            "total_rows": len(table_data),
            "total_pages": len(pages),
            "rows_per_page": rows_per_page,
            "pages": [
                {
                    "page_number": i + 1,
                    "rows": len(page),
                    "start_idx": i * rows_per_page,
                    "end_idx": min((i + 1) * rows_per_page, len(table_data))
                }
                for i, page in enumerate(pages)
            ]
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def calculate_continuation_totals(doctype: str, docname: str, fieldname: str, total_columns: List[str]) -> Dict:
    """Calculate totals for continuation table columns"""
    try:
        doc = frappe.get_doc(doctype, docname)
        table_data = doc.get(fieldname) or []
        
        if not table_data:
            return {
                "success": True,
                "totals": {},
                "total_rows": 0
            }
        
        # Convert table_data to list of dicts if needed
        if hasattr(table_data[0], 'as_dict'):
            table_data = [row.as_dict() for row in table_data]
        
        totals = calculate_table_running_totals(table_data, total_columns)
        
        return {
            "success": True,
            "totals": totals,
            "total_rows": len(table_data),
            "columns": total_columns
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_empty_rows(current_row_count: int, min_rows: int, columns: List[Dict]) -> List[Dict]:
    """Generate empty rows to fill up to minimum row count"""
    empty_rows = []
    rows_needed = max(0, min_rows - current_row_count)
    
    for i in range(rows_needed):
        empty_row = {
            "idx": current_row_count + i + 1,
            "is_empty_row": True
        }
        
        # Add empty values for each column
        for column in columns:
            if hasattr(column, 'fieldname'):
                empty_row[column.fieldname] = ""
            elif isinstance(column, dict) and 'fieldname' in column:
                empty_row[column['fieldname']] = ""
        
        empty_rows.append(empty_row)
    
    return empty_rows


def calculate_table_height(min_rows: int, row_height: int = 35, header_height: int = 40, footer_height: int = 35) -> int:
    """Calculate fixed table height based on minimum rows"""
    return header_height + (min_rows * row_height) + footer_height


def get_continuation_css() -> str:
    """Get CSS styles for continuation tables"""
    return """
    .continuation-table-page {
        margin-bottom: 20px;
    }
    
    .continuation-header {
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
        padding: 5px;
        border-bottom: 1px solid #ccc;
        background-color: #f8f9fa;
    }
    
    .continuation-footer {
        text-align: center;
        font-weight: bold;
        margin-top: 10px;
        padding: 5px;
        border-top: 1px solid #ccc;
        background-color: #f8f9fa;
    }
    
    .continuation-table .balance-forward tr {
        background-color: #f8f9fa !important;
        font-weight: bold;
    }
    
    .continuation-table .running-totals tr {
        background-color: #f0f0f0 !important;
        font-weight: bold;
        border-top: 2px solid #333 !important;
    }
    
    .continuation-table tbody tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    .continuation-table tbody tr:nth-child(odd) {
        background-color: #ffffff;
    }
    
    @media print {
        .continuation-table-page {
            page-break-inside: avoid;
        }
        
        .continuation-header,
        .continuation-footer {
            page-break-inside: avoid;
        }
    }
    """