import click


@click.command("setup-chrome", help="setup chrome (server-side) for pdf generation")
def setup_chorme():
	from print_designer.install import setup_chromium

	setup_chromium()


@click.command("install-watermark-fields", help="Install or update watermark fields for Print Designer")
def install_watermark_fields():
	"""Install watermark fields for all supported DocTypes"""
	import frappe
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from print_designer.custom_fields import CUSTOM_FIELDS
	
	try:
		click.echo("Installing Print Designer watermark fields...")
		
		# Get current site from currentsite.txt or prompt
		try:
			with open('/home/frappe/frappe-bench/sites/currentsite.txt', 'r') as f:
				site = f.read().strip()
		except:
			site = "erpnext-dev-server.bunchee.online"  # fallback
		
		click.echo(f"Using site: {site}")
		frappe.init(site=site)
		frappe.connect()
		
		# Create/update custom fields
		create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)
		frappe.db.commit()
		
		click.echo(f"✓ Print Designer watermark fields installed successfully for site: {site}")
		
		# List installed DocTypes
		doctypes_with_watermark = [dt for dt in CUSTOM_FIELDS.keys() if dt != "Print Format"]
		click.echo(f"✓ Watermark fields added to DocTypes: {', '.join(doctypes_with_watermark)}")
		
	except Exception as e:
		click.echo(f"✗ Error installing watermark fields: {str(e)}")
		raise e
	finally:
		frappe.destroy()


@click.command("check-watermark-fields", help="Check status of watermark fields installation")
def check_watermark_fields():
	"""Check if watermark fields are properly installed"""
	import frappe
	
	try:
		# Get current site from currentsite.txt or prompt
		try:
			with open('/home/frappe/frappe-bench/sites/currentsite.txt', 'r') as f:
				site = f.read().strip()
		except:
			site = "erpnext-dev-server.bunchee.online"  # fallback
		
		click.echo(f"Using site: {site}")
		frappe.init(site=site)
		frappe.connect()
		
		click.echo(f"Checking watermark fields for site: {site}")
		
		# Check each DocType for watermark_text field
		test_doctypes = ["Stock Entry", "Sales Invoice", "Purchase Invoice", "Delivery Note", "Purchase Receipt"]
		
		for doctype in test_doctypes:
			try:
				meta = frappe.get_meta(doctype)
				watermark_field = meta.get_field("watermark_text")
				
				if watermark_field:
					click.echo(f"✓ {doctype}: watermark_text field exists")
				else:
					click.echo(f"✗ {doctype}: watermark_text field MISSING")
			except Exception as e:
				click.echo(f"✗ {doctype}: Error checking field - {str(e)}")
		
		# Check database columns
		click.echo("\nChecking database columns:")
		for doctype in test_doctypes:
			try:
				table_name = f"tab{doctype}"
				result = frappe.db.sql(f"SHOW COLUMNS FROM `{table_name}` LIKE 'watermark_text'", as_dict=True)
				if result:
					click.echo(f"✓ {doctype}: Database column exists")
				else:
					click.echo(f"✗ {doctype}: Database column MISSING")
			except Exception as e:
				click.echo(f"✗ {doctype}: Error checking database - {str(e)}")
				
	except Exception as e:
		click.echo(f"✗ Error checking watermark fields: {str(e)}")
		raise e
	finally:
		frappe.destroy()


commands = [setup_chorme, install_watermark_fields, check_watermark_fields]
