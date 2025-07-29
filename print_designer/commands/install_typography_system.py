"""
Install Typography System Command

Installs the Global Defaults typography integration system for Print Designer.
This command ensures that font selection through Global Defaults is properly
configured and all necessary fields and functionality are available.
"""

import frappe
from frappe.commands import pass_context, click


@click.command('install-typography-system')
@pass_context
def install_typography_system(context):
	"""Install Print Designer typography system integration with Global Defaults."""
	
	# Switch to the correct site context
	for site in context.sites:
		frappe.init(site=site)
		frappe.connect()
		
		try:
			print(f"\n🎨 Installing Typography System for site: {site}")
			
			# Install custom fields to Global Defaults
			print("📝 Installing typography fields to Global Defaults...")
			_install_typography_fields()
			
			# Setup default typography settings
			print("⚙️  Setting up default typography configuration...")
			_setup_default_typography()
			
			# Install client script
			print("📜 Installing client script enhancements...")
			_verify_client_script_integration()
			
			# Create initial typography override CSS
			print("🎨 Creating typography override CSS file...")
			_create_initial_typography_css()
			
			# Verify installation
			print("✅ Verifying typography system installation...")
			_verify_installation()
			
			print(f"🎉 Typography system successfully installed for {site}!")
			print("\n📖 Usage Instructions:")
			print("   1. Go to Setup > Global Defaults")
			print("   2. Scroll to the 'Typography Settings' section")
			print("   3. Select your preferred Primary Font Family")
			print("   4. Enable Thai Font Support if needed")
			print("   5. Click 'Apply Typography' to apply changes system-wide")
			print("   6. Refresh the page to see the new font in action")
			
		except Exception as e:
			print(f"❌ Error installing typography system for {site}: {str(e)}")
			frappe.log_error(f"Typography system installation error: {str(e)}")
			
		finally:
			frappe.destroy()


def _install_typography_fields():
	"""Install typography custom fields to Global Defaults."""
	from print_designer.install import ensure_custom_fields
	
	# Ensure custom fields are installed (includes Global Defaults fields)
	ensure_custom_fields()
	
	print("   ✓ Typography fields added to Global Defaults")


def _setup_default_typography():
	"""Setup default typography settings."""
	from print_designer.api.global_typography import setup_default_typography
	
	setup_default_typography()
	
	print("   ✓ Default typography settings configured")


def _verify_client_script_integration():
	"""Verify that the client script is properly integrated."""
	import os
	from frappe import get_app_path
	
	client_script_path = os.path.join(
		get_app_path("print_designer"),
		"print_designer",
		"client_scripts",
		"global_defaults.js"
	)
	
	if os.path.exists(client_script_path):
		print("   ✓ Client script integration verified")
	else:
		print("   ⚠️  Client script not found - may need manual installation")


def _create_initial_typography_css():
	"""Create the initial typography override CSS file."""
	from print_designer.api.global_typography import reset_typography_to_default
	
	result = reset_typography_to_default()
	
	if result.get("success"):
		print("   ✓ Typography override CSS created")
	else:
		print(f"   ⚠️  Failed to create CSS: {result.get('error', 'Unknown error')}")


def _verify_installation():
	"""Verify that all components are properly installed."""
	checks = []
	
	# Check if Global Defaults has typography fields
	try:
		global_defaults = frappe.get_single("Global Defaults")
		if hasattr(global_defaults, 'primary_font_family'):
			checks.append("✓ Typography fields installed")
		else:
			checks.append("❌ Typography fields missing")
	except Exception as e:
		checks.append(f"❌ Global Defaults access error: {str(e)}")
	
	# Check if client script is linked
	from print_designer.print_designer.hooks import doctype_js
	if "Global Defaults" in doctype_js:
		checks.append("✓ Client script integration configured")
	else:
		checks.append("❌ Client script integration missing")
	
	# Check if API endpoints are available
	try:
		from print_designer.api import global_typography
		checks.append("✓ Typography API endpoints available")
	except ImportError:
		checks.append("❌ Typography API endpoints missing")
	
	# Print verification results
	for check in checks:
		print(f"   {check}")
	
	# Overall status
	failed_checks = [check for check in checks if check.startswith("❌")]
	if not failed_checks:
		print("   🎯 All components verified successfully!")
	else:
		print(f"   ⚠️  {len(failed_checks)} issues found - check above for details")


# CLI command registration
commands = [install_typography_system]