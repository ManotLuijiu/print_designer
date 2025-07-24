"""
Delivery QR Code Jinja Macros for Print Designer
Provides Jinja macro functions for delivery approval QR codes in print formats
"""

import frappe
from jinja2 import Template

def get_delivery_approval_qr_macro():
    """Get the delivery_approval_qr macro for use in Jinja templates"""
    macro_template = """
    {% macro delivery_approval_qr(delivery_note) -%}
        {% if delivery_note.customer_approval_status == 'Pending' %}
            <div class="approval-section">
                <h3>Customer Approval Required</h3>
                <div class="qr-code-container">
                    {% if delivery_note.approval_qr_code %}
                        <img src="data:image/png;base64,{{ delivery_note.approval_qr_code }}" 
                             alt="Scan to approve delivery" 
                             style="width: 150px; height: 150px;">
                    {% endif %}
                    <p>Scan QR code to approve goods received</p>
                </div>
            </div>
        {% elif delivery_note.customer_approval_status == 'Approved' %}
            <div class="approval-section approved">
                <h3>✓ Approved by Customer</h3>
                <p>Approved by: {{ delivery_note.customer_approved_by }}</p>
                <p>Date: {{ delivery_note.customer_approved_on }}</p>
                {% if delivery_note.customer_signature %}
                    <div class="signature">
                        <p>Digital Signature:</p>
                        <img src="{{ delivery_note.customer_signature }}" 
                             alt="Customer Signature" 
                             style="max-width: 200px; height: auto;">
                    </div>
                {% endif %}
            </div>
        {% endif %}
    {%- endmacro %}
    """
    return Template(macro_template)

def render_delivery_approval_qr(delivery_note_name):
    """
    Render delivery approval QR section for a delivery note
    Usage in Jinja: {{ render_delivery_approval_qr(doc.name) }}
    """
    try:
        delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
        
        # Use new field names with legacy fallback
        status = delivery_note.get("customer_approval_status") or delivery_note.get("custom_goods_received_status") or "Pending"
        qr_code = delivery_note.get("approval_qr_code") or delivery_note.get("custom_approval_qr_code")
        approved_by = delivery_note.get("customer_approved_by") or delivery_note.get("custom_approved_by")
        approved_on = delivery_note.get("customer_approved_on") or delivery_note.get("custom_customer_approval_date")
        signature = delivery_note.get("customer_signature") or delivery_note.get("custom_customer_signature")
        
        if status == 'Pending':
            html = '<div class="approval-section">'
            html += '<h3>Customer Approval Required</h3>'
            html += '<div class="qr-code-container">'
            if qr_code:
                html += f'<img src="data:image/png;base64,{qr_code}" alt="Scan to approve delivery" style="width: 150px; height: 150px;">'
            html += '<p>Scan QR code to approve goods received</p>'
            html += '</div></div>'
            return html
            
        elif status == 'Approved':
            html = '<div class="approval-section approved">'
            html += '<h3>✓ Approved by Customer</h3>'
            if approved_by:
                html += f'<p>Approved by: {approved_by}</p>'
            if approved_on:
                html += f'<p>Date: {approved_on}</p>'
            if signature:
                html += '<div class="signature">'
                html += '<p>Digital Signature:</p>'
                html += f'<img src="{signature}" alt="Customer Signature" style="max-width: 200px; height: auto;">'
                html += '</div>'
            html += '</div>'
            return html
            
        return ""
        
    except Exception as e:
        frappe.log_error(f"Error rendering delivery approval QR: {str(e)}")
        return ""

def render_delivery_qr_compact(delivery_note_name):
    """
    Render compact delivery QR section for a delivery note
    Usage in Jinja: {{ render_delivery_qr_compact(doc.name) }}
    """
    try:
        delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
        
        status = delivery_note.get("customer_approval_status") or delivery_note.get("custom_goods_received_status") or "Pending"
        qr_code = delivery_note.get("approval_qr_code") or delivery_note.get("custom_approval_qr_code")
        approved_by = delivery_note.get("customer_approved_by") or delivery_note.get("custom_approved_by")
        approved_on = delivery_note.get("customer_approved_on") or delivery_note.get("custom_customer_approval_date")
        rejection_reason = delivery_note.get("custom_rejection_reason")
        
        if status == 'Pending' and qr_code:
            return f'''
            <div style="text-align: center; margin: 10px 0;">
                <img src="data:image/png;base64,{qr_code}" alt="Scan to approve" style="width: 100px; height: 100px;">
                <p style="margin: 5px 0; font-size: 12px;">Scan to approve delivery</p>
            </div>
            '''
        elif status == 'Approved':
            return f'''
            <div style="text-align: center; margin: 10px 0; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px;">
                <p style="margin: 0; color: #155724; font-weight: bold;">✓ Approved by {approved_by or 'Customer'}</p>
                <p style="margin: 0; font-size: 12px; color: #155724;">{approved_on or ''}</p>
            </div>
            '''
        elif status == 'Rejected':
            rejection_text = f'<p style="margin: 0; font-size: 12px; color: #721c24;">{rejection_reason}</p>' if rejection_reason else ''
            return f'''
            <div style="text-align: center; margin: 10px 0; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px;">
                <p style="margin: 0; color: #721c24; font-weight: bold;">✗ Rejected</p>
                {rejection_text}
            </div>
            '''
        return ""
        
    except Exception as e:
        frappe.log_error(f"Error rendering compact delivery QR: {str(e)}")
        return ""

def render_delivery_status_badge(delivery_note_name):
    """
    Render status badge for delivery note
    Usage in Jinja: {{ render_delivery_status_badge(doc.name) }}
    """
    try:
        delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
        status = delivery_note.get("customer_approval_status") or delivery_note.get("custom_goods_received_status") or "Pending"
        
        if status == 'Approved':
            return '<span style="background-color: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">✓ APPROVED</span>'
        elif status == 'Rejected':
            return '<span style="background-color: #dc3545; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">✗ REJECTED</span>'
        else:
            return '<span style="background-color: #ffc107; color: black; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">⏳ PENDING</span>'
            
    except Exception as e:
        frappe.log_error(f"Error rendering delivery status badge: {str(e)}")
        return '<span style="background-color: #6c757d; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">UNKNOWN</span>'

def render_delivery_approval_summary(delivery_note_name):
    """
    Render complete delivery approval summary
    Usage in Jinja: {{ render_delivery_approval_summary(doc.name) }}
    """
    try:
        delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
        
        status = delivery_note.get("customer_approval_status") or delivery_note.get("custom_goods_received_status") or "Pending"
        qr_code = delivery_note.get("approval_qr_code") or delivery_note.get("custom_approval_qr_code")
        approved_by = delivery_note.get("customer_approved_by") or delivery_note.get("custom_approved_by")
        approved_on = delivery_note.get("customer_approved_on") or delivery_note.get("custom_customer_approval_date")
        signature = delivery_note.get("customer_signature") or delivery_note.get("custom_customer_signature")
        rejection_reason = delivery_note.get("custom_rejection_reason")
        
        # Format approved date
        formatted_date = ""
        if approved_on:
            try:
                if hasattr(approved_on, 'strftime'):
                    formatted_date = approved_on.strftime('%d/%m/%Y %H:%M')
                else:
                    formatted_date = str(approved_on)
            except:
                formatted_date = str(approved_on)
        
        html = '''
        <div class="delivery-approval-summary" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; background-color: #f9f9f9;">
            <h4 style="margin: 0 0 10px 0; font-size: 16px;">Delivery Approval Status</h4>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div><strong>Status:</strong> ''' + render_delivery_status_badge(delivery_note_name) + '''</div>'''
        
        if status == 'Pending' and qr_code:
            html += f'''
                <div style="text-align: right;">
                    <img src="data:image/png;base64,{qr_code}" alt="Scan to approve" style="width: 80px; height: 80px;">
                </div>'''
        
        html += '</div>'
        
        if status == 'Approved':
            signature_html = ""
            if signature:
                signature_html = f'''
                    <div style="margin-top: 10px;">
                        <strong>Digital Signature:</strong><br>
                        <img src="{signature}" alt="Customer Signature" style="max-width: 150px; height: auto; border: 1px solid #ddd; padding: 5px; background: white;">
                    </div>'''
            
            html += f'''
            <div style="background-color: #d4edda; padding: 10px; border-radius: 4px; border-left: 4px solid #28a745;">
                <div><strong>Approved by:</strong> {approved_by or 'Unknown'}</div>
                <div><strong>Approved on:</strong> {formatted_date}</div>
                {signature_html}
            </div>'''
            
        elif status == 'Rejected':
            reason_html = f'<div><strong>Reason:</strong> {rejection_reason}</div>' if rejection_reason else ''
            html += f'''
            <div style="background-color: #f8d7da; padding: 10px; border-radius: 4px; border-left: 4px solid #dc3545;">
                <div><strong>Delivery rejected</strong></div>
                {reason_html}
            </div>'''
            
        else:
            html += '''
            <div style="background-color: #fff3cd; padding: 10px; border-radius: 4px; border-left: 4px solid #ffc107;">
                <div><strong>Awaiting customer approval</strong></div>
                <div style="font-size: 12px; color: #856404; margin-top: 5px;">
                    Customer can scan the QR code to approve or reject this delivery
                </div>
            </div>'''
        
        html += '</div>'
        return html
        
    except Exception as e:
        frappe.log_error(f"Error rendering delivery approval summary: {str(e)}")
        return f'<div class="error">Error loading delivery approval summary: {str(e)}</div>'

def render_delivery_qr_with_instructions(delivery_note_name):
    """
    Render QR code with detailed instructions
    Usage in Jinja: {{ render_delivery_qr_with_instructions(doc.name) }}
    """
    try:
        delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
        
        status = delivery_note.get("customer_approval_status") or delivery_note.get("custom_goods_received_status") or "Pending"
        qr_code = delivery_note.get("approval_qr_code") or delivery_note.get("custom_approval_qr_code")
        
        if status == 'Pending' and qr_code:
            return f'''
            <div style="text-align: center; padding: 20px; border: 2px dashed #007bff; margin: 15px 0; border-radius: 10px; background-color: #f8f9fa;">
                <h3 style="color: #007bff; margin: 0 0 15px 0;">Customer Approval Required</h3>
                <div style="display: inline-block; margin: 0 20px;">
                    <img src="data:image/png;base64,{qr_code}" alt="Scan to approve delivery" style="width: 150px; height: 150px; border: 2px solid #007bff; border-radius: 10px;">
                </div>
                <div style="margin-top: 15px;">
                    <p style="margin: 5px 0; font-size: 14px; font-weight: bold; color: #495057;">📱 Scan QR code with your mobile device</p>
                    <p style="margin: 5px 0; font-size: 12px; color: #6c757d;">You will be redirected to approve or reject this delivery</p>
                    <p style="margin: 5px 0; font-size: 12px; color: #6c757d;">Digital signature collection available</p>
                </div>
            </div>
            '''
        return ""
        
    except Exception as e:
        frappe.log_error(f"Error rendering delivery QR with instructions: {str(e)}")
        return ""

# Legacy compatibility function
def render_legacy_delivery_qr(delivery_note_name):
    """
    Render legacy QR code for backward compatibility
    Usage in Jinja: {{ render_legacy_delivery_qr(doc.name) }}
    """
    try:
        delivery_note = frappe.get_doc("Delivery Note", delivery_note_name)
        
        status = delivery_note.get("custom_goods_received_status") or "Pending"
        qr_code = delivery_note.get("custom_approval_qr_code")
        approved_by = delivery_note.get("custom_approved_by")
        
        if status == 'Pending' and qr_code:
            return f'''
            <div style="text-align: center; margin: 10px 0;">
                <img src="data:image/png;base64,{qr_code}" alt="Scan to approve" style="width: 120px; height: 120px;">
                <p style="margin: 5px 0; font-size: 12px;">Scan to approve delivery</p>
            </div>
            '''
        elif status == 'Approved':
            approved_text = f'<p style="margin: 0; font-size: 12px;">by {approved_by}</p>' if approved_by else ''
            return f'''
            <div style="text-align: center; margin: 10px 0; color: green;">
                <p style="margin: 0; font-weight: bold;">✓ Approved</p>
                {approved_text}
            </div>
            '''
        return ""
        
    except Exception as e:
        frappe.log_error(f"Error rendering legacy delivery QR: {str(e)}")
        return ""