import frappe
from frappe import _


@frappe.whitelist()
def install_complete_system():
    """
    API endpoint to install complete Thai WHT and QR Delivery system
    Can be called from Frappe UI or external systems
    """
    if not frappe.has_permission("Print Format", "create"):
        frappe.throw(_("Insufficient permissions to install system components"))
    
    try:
        from print_designer.setup.install import setup_thai_withholding_tax_and_qr_delivery
        
        result = setup_thai_withholding_tax_and_qr_delivery()
        
        if result["success"]:
            frappe.msgprint(
                _("System installation completed successfully!<br><br>Features installed:<br>{}").format(
                    "<br>".join([f"• {feature}" for feature in result["features"]])
                ),
                title=_("Installation Complete"),
                indicator="green"
            )
        
        return result
        
    except Exception as e:
        frappe.log_error(f"API installation error: {str(e)}")
        frappe.throw(_("Installation failed: {}").format(str(e)))


@frappe.whitelist()
def get_system_status():
    """
    API endpoint to check system installation status
    Returns detailed status of all components
    """
    try:
        from print_designer.setup.install import get_installation_status
        
        status = get_installation_status()
        
        # Calculate overall health
        dn_fields = status['custom_fields']['delivery_note']
        pe_fields = status['custom_fields']['payment_entry']
        api_status = status['api_endpoints']
        
        total_components = (
            dn_fields['total'] + pe_fields['total'] + 
            2 +  # print formats
            1 +  # web page
            api_status['total']  # api endpoints
        )
        installed_components = (
            dn_fields['installed'] + pe_fields['installed'] +
            (1 if status['print_formats']['thai_wht'] else 0) +
            (1 if status['print_formats']['qr_delivery'] else 0) +
            (1 if status['web_pages']['delivery_approval'] else 0) +
            api_status['available']
        )
        
        health_percentage = (installed_components / total_components) * 100
        
        return {
            "status": status,
            "health": {
                "percentage": round(health_percentage, 1),
                "installed": installed_components,
                "total": total_components,
                "status": "complete" if health_percentage == 100 else "partial" if health_percentage >= 80 else "incomplete"
            }
        }
        
    except Exception as e:
        frappe.log_error(f"API status check error: {str(e)}")
        frappe.throw(_("Status check failed: {}").format(str(e)))


@frappe.whitelist()
def get_usage_instructions():
    """
    API endpoint to get detailed usage instructions for both systems
    """
    return {
        "thai_wht": {
            "title": "Thai Form 50 ทวิ (Withholding Tax Certificate)",
            "description": "Generate government-compliant withholding tax certificates for supplier payments",
            "steps": [
                "Create a Payment Entry for supplier payment",
                "Enable 'Apply Thai Withholding Tax' checkbox in the Thai Withholding Tax section",
                "Set the appropriate withholding tax rate (3% for services, 1% for rental, 5% for royalty)",
                "Enter the supplier's 13-digit Thai Tax ID",
                "Save and submit the Payment Entry",
                "Print using 'Payment Entry Form 50 ทวิ - Thai Withholding Tax Certificate' format"
            ],
            "features": [
                "Automatic tax calculation based on payment amount",
                "Auto-generated certificate numbers",
                "Thai language support with proper formatting",
                "Government-compliant Form 50 ทวิ layout",
                "Audit trail for tax compliance"
            ],
            "tax_rates": {
                "services": "3%",
                "rental": "1%", 
                "royalty": "5%",
                "professional_fees": "3%",
                "advertising": "2%"
            }
        },
        "qr_delivery": {
            "title": "QR Code Delivery Approval System",
            "description": "Enable customers to approve delivery receipt via QR code scanning",
            "steps": [
                "Create a Delivery Note with customer and item details",
                "Submit the Delivery Note (QR code generated automatically)",
                "Print using 'Delivery Note with QR Approval' format",
                "Customer scans QR code from printed delivery note",
                "Customer reviews delivery details on mobile-friendly web interface",
                "Customer approves delivery and optionally adds digital signature",
                "Status automatically updated in ERPNext with timestamp and signature"
            ],
            "features": [
                "Automatic QR code generation on Delivery Note submission",
                "Professional Bootstrap 5 web interface",
                "Mobile-responsive design for easy scanning",
                "Digital signature collection using SignaturePad.js",
                "Real-time status updates and audit trail",
                "Delivery rejection with reason tracking",
                "FontAwesome icons and professional styling"
            ],
            "web_interface": {
                "url_pattern": "/delivery-approval/{delivery_note_id}",
                "features": [
                    "Responsive card-based layout",
                    "Interactive signature capture",
                    "Detailed item display with totals",
                    "Status tracking with visual indicators",
                    "Error handling and user feedback"
                ]
            }
        },
        "api_endpoints": {
            "qr_delivery": [
                {
                    "endpoint": "generate_delivery_approval_qr",
                    "description": "Generate QR code for delivery approval",
                    "parameters": ["delivery_note_name"]
                },
                {
                    "endpoint": "approve_delivery_goods", 
                    "description": "Approve delivery with optional signature",
                    "parameters": ["delivery_note_name", "customer_signature"]
                },
                {
                    "endpoint": "reject_delivery_goods",
                    "description": "Reject delivery with reason",
                    "parameters": ["delivery_note_name", "rejection_reason"]
                },
                {
                    "endpoint": "get_delivery_status",
                    "description": "Get current delivery approval status",
                    "parameters": ["delivery_note_name"]
                }
            ]
        }
    }


@frappe.whitelist()
def repair_installation():
    """
    API endpoint to repair/fix installation issues
    Attempts to fix common installation problems
    """
    if not frappe.has_permission("Print Format", "create"):
        frappe.throw(_("Insufficient permissions to repair installation"))
    
    try:
        from print_designer.setup.install import get_installation_status, add_custom_fields, create_print_formats
        
        repair_log = []
        
        # Check and repair custom fields
        status = get_installation_status()
        
        # Repair Delivery Note fields
        dn_missing = status['custom_fields']['delivery_note']['missing']
        if dn_missing:
            repair_log.append(f"Attempting to repair {len(dn_missing)} missing Delivery Note fields")
            add_custom_fields()
            repair_log.append("✅ Delivery Note fields repair completed")
        
        # Repair Payment Entry fields  
        pe_missing = status['custom_fields']['payment_entry']['missing']
        if pe_missing:
            repair_log.append(f"Attempting to repair {len(pe_missing)} missing Payment Entry fields")
            add_custom_fields()
            repair_log.append("✅ Payment Entry fields repair completed")
        
        # Repair print formats
        if not status['print_formats']['thai_wht'] or not status['print_formats']['qr_delivery']:
            repair_log.append("Attempting to repair missing print formats")
            create_print_formats()
            repair_log.append("✅ Print formats repair completed")
        
        # Repair web page
        if not status['web_pages']['delivery_approval']:
            repair_log.append("Attempting to repair delivery approval web page")
            try:
                from print_designer.custom.delivery_note_qr import create_delivery_approval_page
                create_delivery_approval_page()
                repair_log.append("✅ Web page repair completed")
            except:
                repair_log.append("⚠️ Web page repair failed - file may already exist")
        
        frappe.db.commit()
        
        if not repair_log:
            repair_log.append("No repairs needed - system is healthy")
        
        return {
            "success": True,
            "message": "Repair process completed",
            "repair_log": repair_log
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"API repair error: {str(e)}")
        return {
            "success": False,
            "message": f"Repair failed: {str(e)}"
        }