# Copyright (c) 2025, Frappe Technologies Pvt Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CompanyRetentionSettings(Document):
    def validate(self):
        """Validate retention settings"""
        self.validate_retention_rates()
        self.validate_retention_account()
        self.sync_with_company_field()

    def validate_retention_rates(self):
        """Validate retention rate constraints"""
        if self.construction_service_enabled:
            if not self.default_retention_rate:
                frappe.throw(_("Default Retention Rate is required when Construction Service is enabled"))
            
            if self.default_retention_rate < 0:
                frappe.throw(_("Default Retention Rate cannot be negative"))
            
            if self.maximum_retention_rate and self.default_retention_rate > self.maximum_retention_rate:
                frappe.throw(_("Default Retention Rate cannot exceed Maximum Retention Rate"))
            
            if self.maximum_retention_rate and self.maximum_retention_rate > 100:
                frappe.throw(_("Maximum Retention Rate cannot exceed 100%"))

    def validate_retention_account(self):
        """Validate retention account belongs to company"""
        if self.construction_service_enabled and self.retention_account:
            account = frappe.get_cached_doc("Account", self.retention_account)
            if account.company != self.company:
                frappe.throw(_("Retention Account must belong to Company {0}").format(self.company))
            
            # Check if it's a liability account
            if not account.account_type in ["Payable", "Current Liability"]:
                frappe.msgprint(_("Warning: Retention Account should typically be a Liability account"), 
                              alert=True, indicator="orange")

    def sync_with_company_field(self):
        """Sync the construction_service field with Company doctype"""
        if self.construction_service_enabled:
            # Update Company's construction_service field
            company_doc = frappe.get_cached_doc("Company", self.company)
            if not getattr(company_doc, 'construction_service', False):
                frappe.db.set_value("Company", self.company, "construction_service", 1, update_modified=False)
                frappe.msgprint(_("Enabled Construction Service for Company {0}").format(self.company), 
                              alert=True, indicator="green")

    def on_update(self):
        """Clear cache when settings are updated and sync back to Company"""
        frappe.cache().delete_key(f"retention_settings_{self.company}")
        self.sync_to_company()

    @staticmethod
    def get_retention_settings(company):
        """Get retention settings for a company (with caching)"""
        if not company:
            return None
            
        cache_key = f"retention_settings_{company}"
        cached_settings = frappe.cache().get_value(cache_key)
        
        if cached_settings is not None:
            return cached_settings
        
        try:
            settings = frappe.get_cached_doc("Company Retention Settings", company)
            settings_dict = {
                "construction_service_enabled": settings.construction_service_enabled,
                "default_retention_rate": settings.default_retention_rate or 5.0,
                "retention_account": settings.retention_account,
                "auto_calculate_retention": settings.auto_calculate_retention,
                "minimum_invoice_amount": settings.minimum_invoice_amount or 0.0,
                "maximum_retention_rate": settings.maximum_retention_rate or 10.0
            }
            
            # Cache for 1 hour
            frappe.cache().set_value(cache_key, settings_dict, expires_in_sec=3600)
            return settings_dict
            
        except frappe.DoesNotExistError:
            # Return default settings if not found
            default_settings = {
                "construction_service_enabled": False,
                "default_retention_rate": 5.0,
                "retention_account": None,
                "auto_calculate_retention": True,
                "minimum_invoice_amount": 0.0,
                "maximum_retention_rate": 10.0
            }
            
            # Cache default settings for 30 minutes
            frappe.cache().set_value(cache_key, default_settings, expires_in_sec=1800)
            return default_settings

    @staticmethod
    def create_default_settings(company):
        """Create default retention settings for a company"""
        if frappe.db.exists("Company Retention Settings", company):
            return frappe.get_doc("Company Retention Settings", company)
        
        # Check if company has construction_service enabled
        company_doc = frappe.get_cached_doc("Company", company)
        construction_enabled = getattr(company_doc, 'construction_service', False)
        
        settings = frappe.get_doc({
            "doctype": "Company Retention Settings",
            "company": company,
            "construction_service_enabled": construction_enabled,
            "default_retention_rate": 5.0,
            "auto_calculate_retention": 1,
            "maximum_retention_rate": 10.0
        })
        settings.insert()
        
        return settings

    def sync_to_company(self):
        """Sync retention settings back to Company DocType"""
        try:
            # Skip if sync flag is set to prevent infinite loops
            if hasattr(self, 'flags') and getattr(self.flags, 'skip_company_sync', False):
                return
                
            # Get Company record
            company_doc = frappe.get_cached_doc("Company", self.company)
            
            # Map Company Retention Settings fields back to Company fields
            field_mapping = {
                'construction_service_enabled': 'construction_service',
                'default_retention_rate': 'default_retention_rate',
                'retention_account': 'default_retention_account'
            }
            
            # Track if any changes were made
            changes_made = False
            
            for settings_field, company_field in field_mapping.items():
                settings_value = getattr(self, settings_field, None)
                current_company_value = getattr(company_doc, company_field, None)
                
                # Only update if values are different
                if settings_value != current_company_value:
                    frappe.db.set_value("Company", self.company, company_field, settings_value, update_modified=False)
                    changes_made = True
            
            if changes_made:
                frappe.db.commit()
                
        except Exception as e:
            frappe.log_error(
                f"Error syncing Company Retention Settings to Company {self.company}: {str(e)}",
                "Company Retention Reverse Sync Error"
            )
            # Don't fail the save if reverse sync fails
            pass

    def before_save(self):
        """Set defaults before saving"""
        if self.construction_service_enabled:
            if not self.default_retention_rate:
                self.default_retention_rate = 5.0
            if not self.maximum_retention_rate:
                self.maximum_retention_rate = 10.0
            if self.auto_calculate_retention is None:
                self.auto_calculate_retention = 1


@frappe.whitelist()
def get_company_retention_info(company):
    """API endpoint to get retention information for a company"""
    if not company:
        frappe.throw(_("Company is required"))
    
    settings = CompanyRetentionSettings.get_retention_settings(company)
    return settings


@frappe.whitelist()
def calculate_retention_amount(company, base_net_total, custom_retention_rate=None):
    """Calculate retention amount for a given company and invoice amount"""
    if not company or not base_net_total:
        return 0
    
    try:
        settings = CompanyRetentionSettings.get_retention_settings(company)
        
        # If construction service is not enabled, return 0
        if not settings.get('construction_service_enabled'):
            return 0
        
        # Check minimum invoice amount threshold
        min_amount = settings.get('minimum_invoice_amount', 0)
        if base_net_total < min_amount:
            return 0
        
        # Use provided rate or default rate
        retention_rate = custom_retention_rate or settings.get('default_retention_rate', 5.0)
        
        # Validate against maximum rate
        max_rate = settings.get('maximum_retention_rate', 10.0)
        if retention_rate > max_rate:
            retention_rate = max_rate
        
        # Calculate retention amount
        retention_amount = (base_net_total * retention_rate) / 100
        return retention_amount
        
    except Exception as e:
        frappe.log_error(f"Error calculating retention for company {company}: {str(e)}")
        return 0


@frappe.whitelist()
def setup_retention_for_all_companies():
    """Setup retention settings for all companies that don't have them"""
    companies = frappe.get_all("Company", fields=["name"])
    created_count = 0
    
    for company in companies:
        if not frappe.db.exists("Company Retention Settings", company.name):
            try:
                CompanyRetentionSettings.create_default_settings(company.name)
                created_count += 1
            except Exception as e:
                frappe.log_error(f"Failed to create retention settings for {company.name}: {str(e)}")
    
    frappe.msgprint(_("Created retention settings for {0} companies").format(created_count))
    return created_count


# Document Event Handlers for Sales Invoice
def sales_invoice_validate(doc, method):
    """Calculate retention fields automatically on Sales Invoice validation"""
    if not doc.company:
        return
    
    try:
        settings = CompanyRetentionSettings.get_retention_settings(doc.company)
        
        # If construction service is not enabled, clear retention fields
        if not settings.get('construction_service_enabled'):
            doc.custom_retention = 0
            doc.custom_retention_amount = 0
            return
        
        # Auto-calculate if enabled and no manual retention rate set
        if settings.get('auto_calculate_retention') and not doc.custom_retention:
            doc.custom_retention = settings.get('default_retention_rate', 5.0)
        
        # Calculate retention amount if retention rate is set
        if doc.custom_retention and doc.base_net_total:
            doc.custom_retention_amount = calculate_retention_amount(
                doc.company, 
                doc.base_net_total, 
                doc.custom_retention
            )
        else:
            doc.custom_retention_amount = 0
            
    except Exception as e:
        frappe.log_error(f"Error in sales_invoice_validate for {doc.name}: {str(e)}")


def sales_invoice_before_save(doc, method):
    """Ensure retention calculations are correct before saving"""
    sales_invoice_validate(doc, method)
