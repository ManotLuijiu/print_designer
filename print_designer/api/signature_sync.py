import frappe
from frappe import _


@frappe.whitelist()
def sync_company_signatures(company_name=None):
	"""
	Sync signatures from Signature Basic Information to Company DocType fields
	
	Args:
		company_name (str): Specific company to sync, or None for all companies
		
	Returns:
		dict: Sync results
	"""
	try:
		companies_to_sync = []
		
		if company_name:
			if frappe.db.exists("Company", company_name):
				companies_to_sync = [company_name]
			else:
				return {"error": f"Company '{company_name}' not found"}
		else:
			# Get all companies
			companies_to_sync = [c.name for c in frappe.get_all("Company", fields=["name"])]
		
		sync_results = []
		
		for company in companies_to_sync:
			result = _sync_single_company(company)
			sync_results.append(result)
		
		return {
			"success": True,
			"synced_companies": len(sync_results),
			"results": sync_results
		}
		
	except Exception as e:
		frappe.log_error(f"Error syncing company signatures: {str(e)}")
		return {"error": str(e)}


def _sync_single_company(company_name):
	"""
	Sync signatures for a single company
	"""
	try:
		# Get CEO signature from signature_basic_information
		ceo_signature = frappe.db.get_value(
			"Signature Basic Information",
			{
				"company": company_name,
				"signature_title": ["like", "%CEO%"],
				"is_active": 1
			},
			"signature_image"
		)
		
		# If no CEO signature, try to find default signature for company
		if not ceo_signature:
			ceo_signature = frappe.db.get_value(
				"Signature Basic Information",
				{
					"company": company_name,
					"is_default": 1,
					"is_active": 1
				},
				"signature_image"
			)
		
		# Get authorized signatures
		authorized_sigs = frappe.get_all(
			"Signature Basic Information",
			filters={
				"company": company_name,
				"signature_category": "Signature",
				"is_active": 1
			},
			fields=["signature_image", "signature_title"],
			limit=2,
			order_by="is_default desc, creation asc"
		)
		
		# Update Company DocType
		update_data = {}
		
		if ceo_signature:
			update_data["ceo_signature"] = ceo_signature
		
		if authorized_sigs:
			if len(authorized_sigs) >= 1:
				update_data["authorized_signature_1"] = authorized_sigs[0].signature_image
			if len(authorized_sigs) >= 2:
				update_data["authorized_signature_2"] = authorized_sigs[1].signature_image
		
		if update_data:
			frappe.db.set_value("Company", company_name, update_data)
			frappe.db.commit()
		
		return {
			"company": company_name,
			"updated_fields": list(update_data.keys()),
			"ceo_signature": ceo_signature,
			"authorized_signatures": len(authorized_sigs)
		}
		
	except Exception as e:
		return {
			"company": company_name,
			"error": str(e)
		}


@frappe.whitelist()
def get_company_signatures_from_registry(company_name):
	"""
	Get signatures directly from Signature Basic Information registry
	
	Args:
		company_name (str): Company name
		
	Returns:
		dict: Available signatures for the company
	"""
	try:
		if not company_name:
			return {"error": "Company name is required"}
		
		# Get all signatures for the company
		signatures = frappe.get_all(
			"Signature Basic Information",
			filters={
				"company": company_name,
				"is_active": 1
			},
			fields=[
				"name",
				"signature_name", 
				"signature_title",
				"signature_image",
				"signature_category",
				"signature_type",
				"is_default",
				"user"
			],
			order_by="is_default desc, signature_title"
		)
		
		# Categorize signatures
		result = {
			"company": company_name,
			"signatures": signatures,
			"ceo_signatures": [s for s in signatures if "CEO" in (s.signature_title or "").upper()],
			"default_signature": next((s for s in signatures if s.is_default), None),
			"company_stamps": [s for s in signatures if s.signature_category == "Company Stamp"],
			"total_signatures": len(signatures)
		}
		
		return result
		
	except Exception as e:
		frappe.log_error(f"Error fetching company signatures from registry: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def create_signature_for_company(company_name, signature_name, signature_title="CEO", signature_image=None):
	"""
	Create a new signature record for a company
	
	Args:
		company_name (str): Company name
		signature_name (str): Human readable signature name
		signature_title (str): Job title (default: CEO)
		signature_image (str): Image file path
		
	Returns:
		dict: Created signature record
	"""
	try:
		if not company_name or not signature_name:
			return {"error": "Company name and signature name are required"}
		
		# Check if company exists
		if not frappe.db.exists("Company", company_name):
			return {"error": f"Company '{company_name}' not found"}
		
		# Create signature record
		signature_doc = frappe.get_doc({
			"doctype": "Signature Basic Information",
			"signature_name": signature_name,
			"signature_title": signature_title,
			"company": company_name,
			"signature_category": "Signature",
			"signature_type": "Uploaded Image",
			"signature_image": signature_image,
			"is_active": 1,
			"is_default": 1 if signature_title.upper() == "CEO" else 0,
			"signature_field_name": f"{signature_title.lower().replace(' ', '_')}_signature"
		})
		
		signature_doc.insert()
		frappe.db.commit()
		
		# Auto-sync to company fields
		sync_result = _sync_single_company(company_name)
		
		return {
			"success": True,
			"signature_record": signature_doc.name,
			"sync_result": sync_result
		}
		
	except Exception as e:
		frappe.log_error(f"Error creating signature for company: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def sync_signature_to_target_field(signature_record_name):
	"""
	Sync a specific signature record to its target field
	
	Args:
		signature_record_name (str): Name of the signature record
		
	Returns:
		dict: Sync result
	"""
	try:
		# Get signature record
		signature_doc = frappe.get_doc("Signature Basic Information", signature_record_name)
		
		if not signature_doc.signature_target_field or not signature_doc.target_doctype:
			return {"error": "Signature record missing target field mapping"}
		
		# Parse target field mapping
		from print_designer.api.signature_field_options import parse_signature_field_mapping
		
		parsed = parse_signature_field_mapping(signature_doc.signature_target_field)
		if parsed.get("error"):
			return {"error": f"Invalid target field mapping: {parsed['error']}"}
		
		target_doctype = parsed["doctype"]
		target_fieldname = parsed["fieldname"]
		
		# Update the target record
		if target_doctype == "Company" and signature_doc.company:
			frappe.db.set_value(target_doctype, signature_doc.company, target_fieldname, signature_doc.signature_image)
		elif signature_doc.user:
			# For User-related signatures
			frappe.db.set_value(target_doctype, signature_doc.user, target_fieldname, signature_doc.signature_image)
		else:
			return {"error": f"Cannot determine target record for {target_doctype}"}
		
		frappe.db.commit()
		
		return {
			"success": True,
			"signature_record": signature_record_name,
			"target_doctype": target_doctype,
			"target_field": target_fieldname,
			"updated_value": signature_doc.signature_image
		}
		
	except Exception as e:
		frappe.log_error(f"Error syncing signature to target field: {str(e)}")
		return {"error": str(e)}


@frappe.whitelist()
def auto_sync_on_signature_save(doc, method):
	"""
	Hook function to auto-sync when signature records are saved
	Called from hooks.py
	"""
	if doc.doctype == "Signature Basic Information":
		try:
			# New enhanced sync for specific target fields
			if hasattr(doc, 'auto_populate_field') and doc.auto_populate_field and doc.signature_target_field:
				sync_signature_to_target_field(doc.name)
			
			# Legacy sync for company-wide signatures
			if doc.company:
				_sync_single_company(doc.company)
		except Exception as e:
			frappe.log_error(f"Auto-sync failed for signature {doc.name}: {str(e)}")