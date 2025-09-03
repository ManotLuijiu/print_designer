"""
Export and Import functionality for Print Designer formats
"""

import json
import frappe
from frappe import _
from datetime import datetime


def safe_get_attr(obj, attr_name, default=None):
    """Safe attribute getter that handles missing attributes gracefully"""
    try:
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name, default)
        else:
            return default
    except (AttributeError, TypeError):
        return default


@frappe.whitelist()
def export_print_format(print_format_name):
    """
    Export a Print Designer format as JSON for backup purposes.
    
    Args:
        print_format_name: Name of the print format to export
        
    Returns:
        JSON string containing all print designer data
    """
    if not frappe.has_permission("Print Format", "read", print_format_name):
        frappe.throw(_("You don't have permission to export this Print Format"))
    
    print_format = frappe.get_doc("Print Format", print_format_name)
    
    # Check if it's a Print Designer format
    if not print_format.print_designer:
        frappe.throw(_("This is not a Print Designer format"))
    
    # Prepare export data with safe attribute access for PDPrintFormat compatibility
    export_data = {
        "export_date": datetime.now().isoformat(),
        "frappe_version": frappe.__version__,
        "print_designer_version": "1.7.8",  # You can get this from app version
        "print_format": {
            "name": print_format.name,
            "doc_type": print_format.doc_type,
            "module": safe_get_attr(print_format, "module", None),
            "standard": safe_get_attr(print_format, "standard", 0),
            "custom": safe_get_attr(print_format, "custom", 0),
            "disabled": safe_get_attr(print_format, "disabled", 0),
            "print_format_type": safe_get_attr(print_format, "print_format_type", "Standard"),
            "raw_printing": safe_get_attr(print_format, "raw_printing", 0),
            "raw_commands": safe_get_attr(print_format, "raw_commands", None),
            "margin_top": safe_get_attr(print_format, "margin_top", None),
            "margin_right": safe_get_attr(print_format, "margin_right", None),
            "margin_bottom": safe_get_attr(print_format, "margin_bottom", None),
            "margin_left": safe_get_attr(print_format, "margin_left", None),
            "default_print_language": safe_get_attr(print_format, "default_print_language", None),
            "font": safe_get_attr(print_format, "font", None),
            "font_size": safe_get_attr(print_format, "font_size", None),
            "page_number": safe_get_attr(print_format, "page_number", None),
            "align_labels_right": safe_get_attr(print_format, "align_labels_right", 0),
            "show_section_headings": safe_get_attr(print_format, "show_section_headings", 0),
            "line_breaks": safe_get_attr(print_format, "line_breaks", 0),
            "absolute_value": safe_get_attr(print_format, "absolute_value", 0),
            # Print Designer specific fields
            "print_designer": safe_get_attr(print_format, "print_designer", 0),
            "print_designer_header": safe_get_attr(print_format, "print_designer_header", None),
            "print_designer_body": safe_get_attr(print_format, "print_designer_body", None),
            "print_designer_footer": safe_get_attr(print_format, "print_designer_footer", None),
            "print_designer_after_table": safe_get_attr(print_format, "print_designer_after_table", None),
            "print_designer_settings": safe_get_attr(print_format, "print_designer_settings", None),
            "print_designer_print_format": safe_get_attr(print_format, "print_designer_print_format", None),
            "css": safe_get_attr(print_format, "css", None),
            "custom_css": safe_get_attr(print_format, "custom_css", None),
        }
    }
    
    # Add metadata
    export_data["metadata"] = {
        "exported_by": frappe.session.user,
        "original_name": print_format.name,
        "description": f"Export of Print Designer format: {print_format.name}"
    }
    
    return export_data


@frappe.whitelist()
def import_print_format(export_data, new_name=None, overwrite=False):
    """
    Import a Print Designer format from exported JSON data.
    
    Args:
        export_data: JSON string or dict containing exported print format data
        new_name: Optional new name for the imported format (to avoid conflicts)
        overwrite: If True, overwrite existing format with same name
        
    Returns:
        Name of the imported print format
    """
    if not frappe.has_permission("Print Format", "create"):
        frappe.throw(_("You don't have permission to import Print Formats"))
    
    # Parse JSON if string
    if isinstance(export_data, str):
        try:
            export_data = json.loads(export_data)
        except json.JSONDecodeError as e:
            frappe.throw(_("Invalid JSON data: {0}").format(str(e)))
    
    # Validate export data structure
    if "print_format" not in export_data:
        frappe.throw(_("Invalid export data: missing print_format"))
    
    format_data = export_data["print_format"]
    
    # Determine the name for the new format
    if new_name:
        format_name = new_name
    else:
        format_name = format_data.get("name")
    
    # Check if format already exists
    if frappe.db.exists("Print Format", format_name):
        if not overwrite:
            # Generate a unique name
            base_name = format_name
            counter = 1
            while frappe.db.exists("Print Format", format_name):
                format_name = f"{base_name} ({counter})"
                counter += 1
            frappe.msgprint(_("Print Format renamed to {0} to avoid conflict").format(format_name))
        else:
            # Delete existing format if overwrite is True
            if not frappe.has_permission("Print Format", "delete", format_name):
                frappe.throw(_("You don't have permission to overwrite this Print Format"))
            frappe.delete_doc("Print Format", format_name, force=True)
    
    # Create new Print Format document
    new_format = frappe.new_doc("Print Format")
    
    # Copy all fields from export data with safe assignment
    fields_to_copy = [
        "doc_type", "module", "standard", "custom", "disabled",
        "print_format_type", "raw_printing", "raw_commands",
        "margin_top", "margin_right", "margin_bottom", "margin_left",
        "default_print_language", "font", "font_size", "page_number",
        "align_labels_right", "show_section_headings", "line_breaks",
        "absolute_value", "print_designer", "print_designer_header",
        "print_designer_body", "print_designer_footer", 
        "print_designer_after_table", "print_designer_settings",
        "print_designer_print_format", "css", "custom_css"
    ]
    
    for field in fields_to_copy:
        if field in format_data and format_data[field] is not None:
            # Safe attribute setting for PDPrintFormat compatibility
            try:
                setattr(new_format, field, format_data[field])
            except AttributeError:
                # Skip fields that don't exist in PDPrintFormat class
                frappe.log_error(f"Field '{field}' not available in Print Format class, skipping", "Print Format Import Warning")
    
    # Set the name
    new_format.name = format_name
    
    # Set standard to 0 for imported formats (unless explicitly importing a standard format)
    if not frappe.conf.developer_mode:
        new_format.standard = 0
    
    # Set custom to 0 for imported formats
    new_format.custom = 0
    
    try:
        new_format.insert()
        
        # Add import metadata as a comment
        if "metadata" in export_data:
            metadata = export_data["metadata"]
            comment = f"Imported from: {metadata.get('original_name', 'Unknown')}"
            if metadata.get("exported_by"):
                comment += f" (exported by {metadata['exported_by']})"
            if export_data.get("export_date"):
                comment += f" on {export_data['export_date']}"
            
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Info",
                "reference_doctype": "Print Format",
                "reference_name": new_format.name,
                "content": comment
            }).insert(ignore_permissions=True)
        
        frappe.msgprint(_("Print Format {0} imported successfully").format(format_name), indicator="green")
        return new_format.name
        
    except Exception as e:
        frappe.log_error(f"Error importing Print Format: {str(e)}", "Print Format Import Error")
        frappe.throw(_("Error importing Print Format: {0}").format(str(e)))


@frappe.whitelist()
def duplicate_print_format(source_name, new_name):
    """
    Duplicate a Print Designer format with a new name.
    
    Args:
        source_name: Name of the print format to duplicate
        new_name: Name for the duplicated format
        
    Returns:
        Name of the duplicated print format
    """
    if not frappe.has_permission("Print Format", "create"):
        frappe.throw(_("You don't have permission to duplicate Print Formats"))
    
    if not frappe.has_permission("Print Format", "read", source_name):
        frappe.throw(_("You don't have permission to read the source Print Format"))
    
    # Export the source format
    export_data = export_print_format(source_name)
    
    # Import with new name
    return import_print_format(export_data, new_name=new_name, overwrite=False)


@frappe.whitelist()
def validate_import_data(export_data):
    """
    Validate export data before import to provide early feedback.
    
    Args:
        export_data: JSON string or dict to validate
        
    Returns:
        Dict with validation results
    """
    try:
        # Parse JSON if string
        if isinstance(export_data, str):
            export_data = json.loads(export_data)
        
        # Check required fields
        if "print_format" not in export_data:
            return {
                "valid": False,
                "message": _("Missing print_format in export data")
            }
        
        format_data = export_data["print_format"]
        
        # Check essential fields
        required_fields = ["doc_type", "print_designer"]
        missing_fields = [f for f in required_fields if f not in format_data]
        
        if missing_fields:
            return {
                "valid": False,
                "message": _("Missing required fields: {0}").format(", ".join(missing_fields))
            }
        
        # Check if doctype exists
        if not frappe.db.exists("DocType", format_data["doc_type"]):
            return {
                "valid": False,
                "message": _("DocType {0} does not exist in this system").format(format_data["doc_type"])
            }
        
        # Check if it's a Print Designer format
        if not format_data.get("print_designer"):
            return {
                "valid": False,
                "message": _("This is not a Print Designer format")
            }
        
        # All validations passed
        return {
            "valid": True,
            "message": _("Export data is valid"),
            "format_name": format_data.get("name"),
            "doc_type": format_data.get("doc_type"),
            "export_date": export_data.get("export_date"),
            "exported_by": export_data.get("metadata", {}).get("exported_by")
        }
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "message": _("Invalid JSON: {0}").format(str(e))
        }
    except Exception as e:
        return {
            "valid": False,
            "message": _("Validation error: {0}").format(str(e))
        }