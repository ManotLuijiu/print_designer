# Signature Fields Configuration for Print Designer
# This file defines signature image fields to be added to various DocTypes

SIGNATURE_FIELDS = {
	# User Management
	"User": [
		{
			"fieldname": "signature_image",
			"fieldtype": "Attach Image",
			"label": "Signature",
			"insert_after": "user_image",
			"description": "Upload signature image for documents and print formats"
		}
	],
	
	# HR Module
	"Employee": [
		{
			"fieldname": "signature_image",
			"fieldtype": "Attach Image",
			"label": "Signature",
			"insert_after": "image",
			"description": "Employee signature for HR documents and approvals"
		}
	],
	
	"Designation": [
		{
			"fieldname": "designation_signature",
			"fieldtype": "Attach Image",
			"label": "Designation Signature",
			"insert_after": "description",
			"description": "Default signature for this designation/role"
		},
		{
			"fieldname": "signature_authority_level",
			"fieldtype": "Select",
			"label": "Signature Authority Level",
			"options": "None\nLow\nMedium\nHigh\nExecutive",
			"default": "None",
			"insert_after": "designation_signature",
			"description": "Level of signature authority for approval workflows"
		},
		{
			"fieldname": "max_approval_amount",
			"fieldtype": "Currency",
			"label": "Maximum Approval Amount",
			"insert_after": "signature_authority_level",
			"description": "Maximum amount this designation can approve with signature"
		}
	],
	
	# CRM Module
	"Customer": [
		{
			"fieldname": "signature_image",
			"fieldtype": "Attach Image",
			"label": "Authorized Signature",
			"insert_after": "image",
			"description": "Authorized signatory signature for customer documents"
		}
	],
	
	"Lead": [
		{
			"fieldname": "signature_image",
			"fieldtype": "Attach Image",
			"label": "Signature",
			"insert_after": "image",
			"description": "Lead signature for agreements and documents"
		}
	],
	
	# Buying Module
	"Supplier": [
		{
			"fieldname": "signature_image",
			"fieldtype": "Attach Image",
			"label": "Authorized Signature",
			"insert_after": "image",
			"description": "Authorized signatory signature for supplier documents"
		}
	],
	
	# Accounting Module
	"Company": [
		{
			"fieldname": "authorized_signature_1",
			"fieldtype": "Attach Image",
			"label": "Authorized Signature 1",
			"insert_after": "company_logo",
			"description": "Primary authorized signatory for company documents"
		},
		{
			"fieldname": "authorized_signature_2",
			"fieldtype": "Attach Image",
			"label": "Authorized Signature 2",
			"insert_after": "authorized_signature_1",
			"description": "Secondary authorized signatory for company documents"
		},
		{
			"fieldname": "ceo_signature",
			"fieldtype": "Attach Image",
			"label": "CEO Signature",
			"insert_after": "authorized_signature_2",
			"description": "CEO signature for executive documents"
		}
	],
	
	# Projects Module
	"Project": [
		{
			"fieldname": "project_manager_signature",
			"fieldtype": "Attach Image",
			"label": "Project Manager Signature",
			"insert_after": "project_name",
			"description": "Project manager signature for project documents"
		}
	],
	
	# Manufacturing Module
	"Item": [
		{
			"fieldname": "quality_inspector_signature",
			"fieldtype": "Attach Image",
			"label": "Quality Inspector Signature",
			"insert_after": "image",
			"description": "Quality inspector signature for item certification"
		}
	],
	
	# Sales Module - Transaction Documents
	"Sales Invoice": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "sales_team",
			"description": "Signature of person who prepared the invoice"
		},
		{
			"fieldname": "approved_by_signature",
			"fieldtype": "Attach Image",
			"label": "Approved By Signature",
			"insert_after": "prepared_by_signature",
			"description": "Signature of person who approved the invoice"
		}
	],
	
	"Sales Order": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "sales_team",
			"description": "Signature of person who prepared the sales order"
		},
		{
			"fieldname": "approved_by_signature",
			"fieldtype": "Attach Image",
			"label": "Approved By Signature",
			"insert_after": "prepared_by_signature",
			"description": "Signature of person who approved the sales order"
		}
	],
	
	"Quotation": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "sales_team",
			"description": "Signature of person who prepared the quotation"
		}
	],
	
	# Purchase Module - Transaction Documents
	"Purchase Invoice": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "buying_price_list",
			"description": "Signature of person who prepared the purchase invoice"
		},
		{
			"fieldname": "approved_by_signature",
			"fieldtype": "Attach Image",
			"label": "Approved By Signature",
			"insert_after": "prepared_by_signature",
			"description": "Signature of person who approved the purchase invoice"
		}
	],
	
	"Purchase Order": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "buying_price_list",
			"description": "Signature of person who prepared the purchase order"
		},
		{
			"fieldname": "approved_by_signature",
			"fieldtype": "Attach Image",
			"label": "Approved By Signature",
			"insert_after": "prepared_by_signature",
			"description": "Signature of person who approved the purchase order"
		}
	],
	
	"Request for Quotation": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "buying_price_list",
			"description": "Signature of person who prepared the RFQ"
		}
	],
	
	# Stock Module
	"Delivery Note": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "shipping_address_name",
			"description": "Signature of person who prepared the delivery note"
		},
		{
			"fieldname": "delivered_by_signature",
			"fieldtype": "Attach Image",
			"label": "Delivered By Signature",
			"insert_after": "prepared_by_signature",
			"description": "Signature of delivery person"
		},
		{
			"fieldname": "received_by_signature",
			"fieldtype": "Attach Image",
			"label": "Received By Signature",
			"insert_after": "delivered_by_signature",
			"description": "Signature of person who received the delivery"
		}
	],
	
	"Purchase Receipt": [
		{
			"fieldname": "prepared_by_signature",
			"fieldtype": "Attach Image",
			"label": "Prepared By Signature",
			"insert_after": "shipping_address",
			"description": "Signature of person who prepared the purchase receipt"
		},
		{
			"fieldname": "received_by_signature",
			"fieldtype": "Attach Image",
			"label": "Received By Signature",
			"insert_after": "prepared_by_signature",
			"description": "Signature of person who received the items"
		}
	],
	
	# Asset Module
	"Asset": [
		{
			"fieldname": "custodian_signature",
			"fieldtype": "Attach Image",
			"label": "Custodian Signature",
			"insert_after": "image",
			"description": "Signature of asset custodian"
		}
	],
	
	# HR Module - Additional
	"Job Offer": [
		{
			"fieldname": "hr_signature",
			"fieldtype": "Attach Image",
			"label": "HR Signature",
			"insert_after": "offer_terms",
			"description": "HR representative signature"
		},
		{
			"fieldname": "candidate_signature",
			"fieldtype": "Attach Image",
			"label": "Candidate Signature",
			"insert_after": "hr_signature",
			"description": "Candidate acceptance signature"
		}
	],
	
	"Appraisal": [
		{
			"fieldname": "appraiser_signature",
			"fieldtype": "Attach Image",
			"label": "Appraiser Signature",
			"insert_after": "appraisal_template",
			"description": "Signature of person conducting appraisal"
		},
		{
			"fieldname": "employee_signature",
			"fieldtype": "Attach Image",
			"label": "Employee Signature",
			"insert_after": "appraiser_signature",
			"description": "Employee acknowledgment signature"
		}
	],
	
	# Quality Module
	"Quality Inspection": [
		{
			"fieldname": "inspector_signature",
			"fieldtype": "Attach Image",
			"label": "Inspector Signature",
			"insert_after": "quality_inspection_template",
			"description": "Quality inspector signature"
		},
		{
			"fieldname": "supervisor_signature",
			"fieldtype": "Attach Image",
			"label": "Supervisor Signature",
			"insert_after": "inspector_signature",
			"description": "Supervisor approval signature"
		}
	],
	
	# Maintenance Module
	"Maintenance Schedule": [
		{
			"fieldname": "technician_signature",
			"fieldtype": "Attach Image",
			"label": "Technician Signature",
			"insert_after": "maintenance_schedule_details",
			"description": "Technician signature for maintenance completion"
		}
	],
	
	# Custom DocTypes (if they exist)
	"Contract": [
		{
			"fieldname": "party_signature",
			"fieldtype": "Attach Image",
			"label": "Party Signature",
			"insert_after": "contract_terms",
			"description": "Contracting party signature"
		},
		{
			"fieldname": "witness_signature",
			"fieldtype": "Attach Image",
			"label": "Witness Signature",
			"insert_after": "party_signature",
			"description": "Witness signature"
		}
	]
}

# Function to get all signature fields for installation
def get_signature_fields():
	"""
	Returns all signature fields in the format expected by Frappe's custom fields system
	"""
	return SIGNATURE_FIELDS

# Function to get signature fields for a specific DocType
def get_signature_fields_for_doctype(doctype):
	"""
	Returns signature fields for a specific DocType
	"""
	return SIGNATURE_FIELDS.get(doctype, [])

# Function to check if a DocType has signature fields
def has_signature_fields(doctype):
	"""
	Check if a DocType has signature fields configured
	"""
	return doctype in SIGNATURE_FIELDS

# Function to get all DocTypes with signature fields
def get_doctypes_with_signatures():
	"""
	Returns list of all DocTypes that have signature fields
	"""
	return list(SIGNATURE_FIELDS.keys())