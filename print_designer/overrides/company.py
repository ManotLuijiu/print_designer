# Company DocType Override
# Synchronizes retention data from Company form to Company Retention Settings

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.setup.doctype.company.company import Company


class CustomCompany(Company):
    def after_insert(self):
        """Import Chart of Accounts after company creation"""
        super().after_insert()

        # Import Chart of Accounts if specified
        if self.chart_of_accounts:
            try:
                self.create_default_accounts()
            except Exception as e:
                frappe.log_error(
                    f"Error importing Chart of Accounts for {self.name}: {str(e)}",
                    "Chart of Accounts Import Error"
                )

    def on_update(self):
        """Override to handle tax setup errors and sync retention settings"""
        try:
            super().on_update()
        except IndexError as e:
            # Handle ERPNext tax setup error when Chart of Accounts not yet imported
            # This happens during initial company creation with custom CoA
            if "list index out of range" in str(e):
                # Silently skip - will be created after Chart of Accounts import
                pass
            else:
                raise

        # Only sync retention settings for existing documents with retention data
        # Skip for new companies to avoid creation errors
        if not self.is_new() and self.has_retention_data():
            self.sync_retention_settings()

    def create_default_accounts(self):
        """
        Create Chart of Accounts from selected template

        Phase 1 (Current): Basic auto-import only
        - Import CoA from JSON template
        - Skip default account assignment (Phase 2)
        - Skip tax template creation (Phase 3)

        See CHART_OF_ACCOUNTS_AUTOMATION.md for full roadmap
        """
        from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts

        # Import the chart
        frappe.local.flags.ignore_root_company_validation = True
        create_charts(
            self.name,
            self.chart_of_accounts,
            self.country
        )

        # TODO Phase 2: Auto-assign default accounts
        # TODO Phase 3: Auto-create tax templates
        # TODO Phase 4: Industry-specific configuration
        # TODO Phase 5: Validation and compliance checks

    def has_retention_data(self):
        """Check if company has any retention-related data"""
        return any([
            getattr(self, 'construction_service', False),
            getattr(self, 'default_retention_rate', 0) > 0,
            getattr(self, 'default_retention_account', None)
        ])
    
    def sync_retention_settings(self):
        """Synchronize retention data to Company Retention Settings DocType"""
        try:
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

            # Save if changes were made (silently without user messages)
            if changes_made:
                settings.flags.skip_company_sync = True
                if settings.name:
                    settings.save()
                else:
                    settings.insert()
                frappe.db.commit()

        except Exception as e:
            # Silently log error - don't fail Company save
            frappe.log_error(
                f"Error syncing Company retention settings for {self.name}: {str(e)}",
                "Company Retention Sync"
            )
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