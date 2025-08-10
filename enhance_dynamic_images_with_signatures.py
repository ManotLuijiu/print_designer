#!/usr/bin/env python3
"""
Enhance Dynamic Images to Include Signature Basic Information
This creates a bridge between Signature Basic Information and Dynamic Images
"""

import frappe
from frappe import _

def enhance_get_image_docfields():
    """
    Enhance the get_image_docfields function to include Signature Basic Information signatures
    """
    
    # Read the current print_designer.py file
    file_path = "/home/frappe/frappe-bench/apps/print_designer/print_designer/print_designer/page/print_designer/print_designer.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if our enhancement is already there
    if "# Enhanced: Include Signature Basic Information" in content:
        print("✅ Enhancement already applied!")
        return
    
    # Find the get_image_docfields function and enhance it
    function_start = content.find("def get_image_docfields():")
    if function_start == -1:
        print("❌ Could not find get_image_docfields function")
        return
    
    # Find the return statement
    return_line = content.find("return all_image_fields", function_start)
    if return_line == -1:
        print("❌ Could not find return statement")
        return
    
    # Insert our enhancement before the return statement
    enhancement_code = '''
    # Enhanced: Include Signature Basic Information signatures in Dynamic Images
    try:
        # Get all signature records from Signature Basic Information
        signature_records = frappe.get_all("Signature Basic Information", 
            fields=["name", "signature_name", "signature_title", "signature_category", 
                   "signature_type", "signature_image", "signature_data", "user"],
            filters={"docstatus": ["!=", 2]}  # Exclude cancelled
        )
        
        # Add virtual signature fields to the image fields list
        for sig in signature_records:
            if sig.signature_image or sig.signature_data:
                # Create a virtual field that looks like a regular DocType field
                virtual_field = {
                    "name": f"signature_basic_{sig.name}",
                    "parent": "Signature Basic Information", 
                    "fieldname": f"signature_{sig.name.replace('-', '_').lower()}",
                    "fieldtype": "Attach Image",
                    "label": f"{sig.signature_name} ({sig.signature_category})",
                    "options": None,
                    "signature_id": sig.name,  # Store reference to original signature
                    "signature_value": sig.signature_image or sig.signature_data,
                    "signature_user": sig.user,
                    "signature_type": sig.signature_type
                }
                all_image_fields.append(virtual_field)
                
    except Exception as e:
        frappe.log_error(f"Error adding Signature Basic Information to Dynamic Images: {str(e)}")
    
    '''
    
    # Insert the enhancement
    enhanced_content = content[:return_line] + enhancement_code + content[return_line:]
    
    # Write back to file
    with open(file_path, 'w') as f:
        f.write(enhanced_content)
    
    print("✅ Enhanced get_image_docfields to include Signature Basic Information!")
    print("📝 Signatures from Signature Basic Information will now appear in Dynamic Images")

def enhance_app_image_modal():
    """
    Enhance AppImageModal.vue to handle Signature Basic Information signatures
    """
    file_path = "/home/frappe/frappe-bench/apps/print_designer/print_designer/public/js/print_designer/components/layout/AppImageModal.vue"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if enhancement is already there
    if "// Enhanced: Handle Signature Basic Information" in content:
        print("✅ AppImageModal enhancement already applied!")
        return
    
    # Find the getValue function call area (around line 234-246)
    enhancement_area = content.find("await Promise.all(imageFields.map(async (field) => {")
    if enhancement_area == -1:
        print("❌ Could not find enhancement area in AppImageModal.vue")
        return
    
    # Find the end of the Promise.all block
    end_block = content.find("MainStore.imageDocFields = imageFields;", enhancement_area)
    if end_block == -1:
        print("❌ Could not find end of Promise.all block")
        return
    
    # Insert enhancement before setting MainStore.imageDocFields
    enhancement_code = '''
			// Enhanced: Handle Signature Basic Information signatures
			imageFields.forEach(field => {
				if (field.parent === "Signature Basic Information" && field.signature_value) {
					field.value = field.signature_value;
				}
			});
			
			'''
    
    enhanced_content = content[:end_block] + enhancement_code + content[end_block:]
    
    with open(file_path, 'w') as f:
        f.write(enhanced_content)
    
    print("✅ Enhanced AppImageModal.vue to handle Signature Basic Information!")

def test_enhancement():
    """
    Test the enhancement by checking what image fields are returned
    """
    print("🧪 TESTING ENHANCED DYNAMIC IMAGES")
    print("=" * 40)
    
    try:
        from print_designer.print_designer.page.print_designer.print_designer import get_image_docfields
        
        fields = get_image_docfields()
        
        # Count different types of fields
        doctype_fields = [f for f in fields if f.get("parent") != "Signature Basic Information"]
        signature_fields = [f for f in fields if f.get("parent") == "Signature Basic Information"]
        
        print(f"📊 RESULTS:")
        print(f"   📋 DocType Image Fields: {len(doctype_fields)}")
        print(f"   🖋️  Signature Basic Information Fields: {len(signature_fields)}")
        print(f"   📦 Total Dynamic Images Available: {len(fields)}")
        
        if signature_fields:
            print(f"\n🖋️  SIGNATURE BASIC INFORMATION SIGNATURES:")
            for sig in signature_fields[:5]:  # Show first 5
                print(f"   • {sig['label']} ({sig.get('signature_type', 'Unknown')})")
        
        return {
            "success": True,
            "total_fields": len(fields),
            "doctype_fields": len(doctype_fields), 
            "signature_basic_fields": len(signature_fields)
        }
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """
    Main execution function
    """
    print("🎯 ENHANCING DYNAMIC IMAGES WITH SIGNATURE BASIC INFORMATION")
    print("=" * 65)
    
    print("\n1. Enhancing get_image_docfields() function...")
    enhance_get_image_docfields()
    
    print("\n2. Enhancing AppImageModal.vue component...")
    enhance_app_image_modal()
    
    print("\n3. Testing enhancements...")
    test_enhancement()
    
    print("\n🎉 ENHANCEMENT COMPLETE!")
    print("📝 Next steps:")
    print("   1. Restart your development server (bench start)")
    print("   2. Hard refresh your browser (Ctrl+F5)")
    print("   3. Open Print Designer and check Dynamic Images")
    print("   4. Signatures from Signature Basic Information should now appear!")

if __name__ == "__main__":
    main()