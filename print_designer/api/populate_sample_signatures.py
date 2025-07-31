"""
API to populate sample signature images for testing and demonstration
"""

import frappe
import os
from frappe import _

@frappe.whitelist()
def populate_sample_company_signatures():
    """
    Populate sample signature images from static files to Company signature fields
    This helps resolve "Image not Linked" issues by providing default sample signatures
    """
    
    try:
        # Get the first company or create a sample one
        companies = frappe.get_all("Company", limit=1)
        if not companies:
            frappe.throw(_("No Company found. Please create a Company first."))
        
        company_name = companies[0].name
        company_doc = frappe.get_doc("Company", company_name)
        
        print(f"🏢 Populating sample signatures for Company: {company_name}")
        
        # Define signature field mappings to static images
        signature_mappings = {
            "authorized_signature_1": "Signature_01.jpg",
            "ceo_signature": "Signature_01.jpg", 
            "company_logo": "AWS Solution Ltd__page-0001.jpg"  # If company_logo field exists
        }
        
        updated_fields = []
        
        for field_name, image_filename in signature_mappings.items():
            # Check if field exists in the Company DocType
            if hasattr(company_doc, field_name):
                # Create the static image URL
                image_url = f"/assets/print_designer/images/local/{image_filename}"
                
                # Set the field value
                setattr(company_doc, field_name, image_url)
                updated_fields.append(f"{field_name} -> {image_filename}")
                print(f"  ✅ {field_name}: {image_url}")
            else:
                print(f"  ⚠️  Field '{field_name}' not found in Company DocType")
        
        # Save the company document
        if updated_fields:
            company_doc.save()
            frappe.db.commit()
            
            print(f"\n🎉 Successfully updated {len(updated_fields)} signature fields:")
            for field in updated_fields:
                print(f"    • {field}")
            
            return {
                "success": True,
                "message": f"Sample signatures populated for {company_name}",
                "updated_fields": updated_fields,
                "company": company_name
            }
        else:
            return {
                "success": False, 
                "message": "No signature fields were updated",
                "available_images": get_available_static_images()
            }
            
    except Exception as e:
        frappe.log_error(f"Error populating sample signatures: {str(e)}", "Sample Signatures")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_available_static_images():
    """Get list of available static images in the local directory"""
    try:
        static_images_path = os.path.join(
            frappe.get_app_path("print_designer"),
            "print_designer", "public", "images", "local"
        )
        
        if not os.path.exists(static_images_path):
            return []
        
        image_files = []
        for filename in os.listdir(static_images_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg')):
                image_files.append({
                    "filename": filename,
                    "url": f"/assets/print_designer/images/local/{filename}",
                    "type": filename.split('.')[-1].upper()
                })
        
        return image_files
        
    except Exception as e:
        frappe.log_error(f"Error getting static images: {str(e)}", "Static Images")
        return []


@frappe.whitelist()
def assign_static_image_to_field(doctype, docname, fieldname, static_image_filename):
    """
    Assign a static image to a specific field in a document
    
    Args:
        doctype: DocType name (e.g., "Company")
        docname: Document name 
        fieldname: Field name (e.g., "ceo_signature")
        static_image_filename: Filename from static images (e.g., "Signature_01.jpg")
    """
    try:
        # Get the document
        doc = frappe.get_doc(doctype, docname)
        
        # Check if field exists
        if not hasattr(doc, fieldname):
            return {
                "success": False,
                "error": f"Field '{fieldname}' not found in {doctype}"
            }
        
        # Create the static image URL
        image_url = f"/assets/print_designer/images/local/{static_image_filename}"
        
        # Verify the static image file exists
        static_images_path = os.path.join(
            frappe.get_app_path("print_designer"),
            "print_designer", "public", "images", "local", static_image_filename
        )
        
        if not os.path.exists(static_images_path):
            return {
                "success": False,
                "error": f"Static image '{static_image_filename}' not found"
            }
        
        # Set the field value
        setattr(doc, fieldname, image_url)
        doc.save()
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Successfully assigned {static_image_filename} to {doctype}.{fieldname}",
            "image_url": image_url
        }
        
    except Exception as e:
        frappe.log_error(f"Error assigning static image: {str(e)}", "Static Image Assignment")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def clear_signature_field(doctype, docname, fieldname):
    """Clear a signature field (set to None/empty)"""
    try:
        doc = frappe.get_doc(doctype, docname)
        
        if not hasattr(doc, fieldname):
            return {
                "success": False,
                "error": f"Field '{fieldname}' not found in {doctype}"
            }
        
        setattr(doc, fieldname, None)
        doc.save()
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Cleared {doctype}.{fieldname}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }