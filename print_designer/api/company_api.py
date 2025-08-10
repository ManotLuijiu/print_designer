import frappe
from frappe import _


@frappe.whitelist()
def get_company_signature(company_name):
	"""
	Get CEO signature for a company with fallback options
	
	Args:
		company_name (str): Name of the company
		
	Returns:
		dict: CEO signature or fallback message
	"""
	try:
		if not company_name:
			return {"error": "Company name is required"}
		
		# Get CEO signature
		ceo_signature = frappe.get_value("Company", company_name, "ceo_signature")
		
		if ceo_signature:
			return {"ceo_signature": ceo_signature, "company": company_name}
		else:
			# Check if company exists
			if frappe.db.exists("Company", company_name):
				return {
					"ceo_signature": None, 
					"company": company_name,
					"message": "CEO signature not set for this company"
				}
			else:
				return {"error": f"Company '{company_name}' not found"}
				
	except Exception as e:
		frappe.log_error(f"Error fetching CEO signature: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def set_company_signature(company_name, signature_file):
	"""
	Set CEO signature for a company
	
	Args:
		company_name (str): Name of the company
		signature_file (str): File path or URL of the signature
		
	Returns:
		dict: Success message or error
	"""
	try:
		if not company_name or not signature_file:
			return {"error": "Company name and signature file are required"}
		
		# Update the company record
		frappe.db.set_value("Company", company_name, "ceo_signature", signature_file)
		frappe.db.commit()
		
		return {
			"success": True,
			"message": f"CEO signature updated for {company_name}",
			"ceo_signature": signature_file
		}
		
	except Exception as e:
		frappe.log_error(f"Error setting CEO signature: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist() 
def get_company_assets(company_name):
	"""
	Get all company visual assets
	
	Args:
		company_name (str): Name of the company
		
	Returns:
		dict: All company assets including fallbacks
	"""
	try:
		if not company_name:
			return {"error": "Company name is required"}
		
		# Get company data
		company_data = frappe.get_value(
			"Company", 
			company_name, 
			["ceo_signature", "company_logo", "default_letter_head"],
			as_dict=True
		)
		
		if not company_data:
			return {"error": f"Company '{company_name}' not found"}
		
		# Get letterhead image
		letterhead_image = None
		if company_data.get("default_letter_head"):
			letterhead_image = frappe.get_value(
				"Letter Head", 
				company_data["default_letter_head"], 
				"image"
			)
		
		# Also try to find letterhead by company name as backup
		if not letterhead_image:
			letterhead_by_name = frappe.get_value(
				"Letter Head",
				{"letter_head_name": company_name},
				"image"
			)
			if letterhead_by_name:
				letterhead_image = letterhead_by_name
		
		return {
			"company": company_name,
			"ceo_signature": company_data.get("ceo_signature"),
			"company_logo": company_data.get("company_logo"),
			"letterhead_image": letterhead_image,
			"has_signature": bool(company_data.get("ceo_signature")),
			"has_logo": bool(company_data.get("company_logo")),
			"has_letterhead": bool(letterhead_image)
		}
		
	except Exception as e:
		frappe.log_error(f"Error fetching company assets: {str(e)}")
		return {"error": str(e)}