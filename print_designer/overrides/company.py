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

        # Check for CSV-based CoA import first (print_designer custom fields)
        if self.get('pd_use_csv_coa') and self.get('pd_coa_csv_file'):
            try:
                self.import_coa_from_csv()
                return  # Skip standard CoA import if CSV import successful
            except Exception as e:
                frappe.log_error(
                    f"Error importing Chart of Accounts from CSV for {self.name}: {str(e)}",
                    "CSV CoA Import Error"
                )
                # Fall through to standard import if CSV import fails

        # Import Chart of Accounts from standard template if specified
        if self.chart_of_accounts:
            try:
                self.create_default_accounts()
            except Exception as e:
                frappe.log_error(
                    f"Error importing Chart of Accounts for {self.name}: {str(e)}",
                    "Chart of Accounts Import Error"
                )

    def on_update(self):
        """Override to handle tax setup errors"""
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

        # NOTE: Company Retention Settings sync DISABLED
        # Retention settings are read directly from Company fields (construction_service,
        # default_retention_rate, default_retention_account) in SO/SI calculations.
        # Company Retention Settings DocType is redundant and causes deletion issues.
        # See: sales_order_calculations.py:64-82, sales_invoice_calculations.py:58-83

    def on_trash(self):
        """Delete linked Company Retention Settings before Company deletion"""
        # Clean up any existing Company Retention Settings to prevent LinkExistsError
        if frappe.db.exists("Company Retention Settings", self.name):
            frappe.delete_doc("Company Retention Settings", self.name, force=True, ignore_permissions=True)
            frappe.db.commit()

    def import_coa_from_csv(self):
        """
        Import Chart of Accounts from CSV file.

        Attempts to use thai_business_suite CoA mapper if available,
        falls back to basic import if not available.

        Raises:
            Exception: If import fails
        """
        import tempfile
        import os
        import json

        # Get CSV file content
        from frappe.utils.file_manager import get_file
        csv_content = get_file(self.pd_coa_csv_file)[1]

        # Decode if bytes
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode('utf-8')

        # Write CSV to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_csv:
            tmp_csv.write(csv_content)
            tmp_csv_path = tmp_csv.name

        # Write JSON to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_json:
            tmp_json_path = tmp_json.name

        try:
            # Try to use thai_business_suite CoA mapper (advanced)
            thai_business_suite_available = False
            try:
                from thai_business_suite.coa_mapper.chart_of_accounts_mapper import ChartOfAccountsMapper
                thai_business_suite_available = True
                frappe.msgprint(
                    _("Using advanced CSV mapper from thai_business_suite"),
                    indicator='blue',
                    alert=True
                )
            except ImportError:
                frappe.msgprint(
                    _("thai_business_suite not available - Using basic CSV import"),
                    indicator='orange',
                    alert=True
                )

            if thai_business_suite_available:
                # Advanced import with thai_business_suite
                mapping_template = self.get('pd_coa_mapping_template')

                if mapping_template:
                    # Use specified template
                    template = frappe.get_doc('TBS CoA Mapping Template', mapping_template)
                    config = template.get_mapping_config()
                else:
                    # Use default Standard Thai CoA template
                    from thai_business_suite.coa_mapper.chart_of_accounts_mapper import get_coa_mapping_config
                    try:
                        config = get_coa_mapping_config('standard_thai_coa')
                    except ValueError:
                        # Fallback to inpac_pharma_format if standard not found
                        config = get_coa_mapping_config('inpac_pharma_format')

                # Override chart name to match company
                config['coa_config']['chart_name'] = f"{self.name} Chart of Accounts"

                # Create mapper and convert
                mapper = ChartOfAccountsMapper(mapping_config=config)
                result = mapper.csv_to_json_template(
                    source_csv=tmp_csv_path,
                    output_json=tmp_json_path,
                    validate=True
                )

                # Import the generated JSON
                self._import_coa_json(tmp_json_path)

                # Update status
                self.db_set('pd_coa_import_status', f"✅ Imported {result['statistics']['total_accounts']} accounts", update_modified=False)

                frappe.msgprint(
                    _("Chart of Accounts imported successfully from CSV: {0} accounts").format(
                        result['statistics']['total_accounts']
                    ),
                    indicator='green',
                    alert=True
                )

            else:
                # Basic CSV import (fallback without thai_business_suite)
                # This requires CSV to be in exact ERPNext JSON-compatible format
                frappe.throw(
                    _("""
                        <strong>thai_business_suite not installed</strong><br><br>
                        CSV-based Chart of Accounts import requires the thai_business_suite app for advanced mapping.<br><br>
                        <strong>Options:</strong><br>
                        1. Install thai_business_suite: <code>bench get-app thai_business_suite</code><br>
                        2. Use standard ERPNext Chart of Accounts templates instead<br>
                        3. Manually import accounts after company creation
                    """),
                    title=_("Advanced CSV Import Not Available")
                )

        finally:
            # Clean up temporary files
            if os.path.exists(tmp_csv_path):
                os.remove(tmp_csv_path)
            if os.path.exists(tmp_json_path):
                os.remove(tmp_json_path)

    def _import_coa_json(self, json_path):
        """
        Import Chart of Accounts from JSON file.

        Args:
            json_path: Path to Chart of Accounts JSON file
        """
        import json

        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            coa_data = json.load(f)

        # Use ERPNext's chart import function
        from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts

        # Create a temporary chart template
        chart_name = coa_data.get('name', f"{self.name} Chart of Accounts")

        # ERPNext expects chart template in specific location
        # We'll use the import_chart function which handles JSON data
        from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import import_chart

        frappe.local.flags.ignore_root_company_validation = True

        # Import the chart
        import_chart(
            self.name,
            chart_data=coa_data,
            from_coa_importer=True
        )

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