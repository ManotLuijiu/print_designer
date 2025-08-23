# Company DocType Override
# Synchronizes retention data from Company form to Company Retention Settings

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.setup.doctype.company.company import Company


class CustomCompany(Company):
    def validate(self):
        """Override to add retention data synchronization"""
        super().validate()
        self.sync_retention_settings()
    
    def on_update(self):
        """Override to sync retention settings after update"""
        super().on_update()
        self.sync_retention_settings()
    
    def sync_retention_settings(self):
        """Synchronize retention data to Company Retention Settings DocType"""
        try:
            # Import here to avoid circular imports
            from print_designer.print_designer.doctype.company_retention_settings.company_retention_settings import CompanyRetentionSettings
            
            # Check if any retention fields are set
            has_retention_data = any([
                getattr(self, 'construction_service', False),
                getattr(self, 'default_retention_rate', 0),
                getattr(self, 'default_retention_account', None)
            ])
            
            if not has_retention_data:
                # No retention data in Company, nothing to sync
                return
            
            # Get or create Company Retention Settings record
            if frappe.db.exists("Company Retention Settings", self.name):
                settings = frappe.get_doc("Company Retention Settings", self.name)
            else:
                settings = frappe.new_doc("Company Retention Settings")
                settings.company = self.name
            
            # Map Company fields to Company Retention Settings fields
            field_mapping = {
                'construction_service': 'construction_service_enabled',
                'default_retention_rate': 'default_retention_rate', 
                'default_retention_account': 'retention_account'
            }
            
            # Track if any changes were made
            changes_made = False
            
            for company_field, settings_field in field_mapping.items():
                company_value = getattr(self, company_field, None)
                current_settings_value = getattr(settings, settings_field, None)
                
                # Only update if values are different
                if company_value != current_settings_value:
                    setattr(settings, settings_field, company_value)
                    changes_made = True
            
            # Set defaults for advanced settings if this is a new record
            if not settings.name:
                settings.auto_calculate_retention = 1
                settings.maximum_retention_rate = 10.0
                settings.minimum_invoice_amount = 0.0
                changes_made = True
            
            # Save if changes were made
            if changes_made:
                # Disable sync flag to prevent infinite loops
                settings.flags.skip_company_sync = True
                
                if settings.name:
                    settings.save()
                    frappe.db.commit()
                    frappe.msgprint(
                        _("Updated Company Retention Settings for {0}").format(self.name),
                        alert=True, indicator="green"
                    )
                else:
                    settings.insert()
                    frappe.db.commit()
                    frappe.msgprint(
                        _("Created Company Retention Settings for {0}").format(self.name),
                        alert=True, indicator="green"
                    )
                
        except Exception as e:
            frappe.log_error(
                f"Error syncing Company retention settings for {self.name}: {str(e)}",
                "Company Retention Sync Error"
            )
            # Don't fail the Company save if retention sync fails
            pass


def sync_company_retention_settings(doc, method=None):
    """
    Document event handler for Company validation.
    This is called via hooks.py for the Company DocType.
    """
    try:
        if hasattr(doc, 'sync_retention_settings'):
            doc.sync_retention_settings()
    except Exception as e:
        frappe.log_error(
            f"Error in Company retention sync hook for {doc.name}: {str(e)}",
            "Company Retention Hook Error"
        )