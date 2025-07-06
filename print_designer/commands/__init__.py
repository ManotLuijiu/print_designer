import click


@click.command("setup-chrome", help="setup chrome (server-side) for pdf generation")
def setup_chorme():
	from print_designer.install import setup_chromium

	setup_chromium()


@click.command("fix-pdf-generator", help="set Chrome PDF generator for all Print Designer formats")
@click.pass_context
def fix_pdf_generator(ctx):
	import frappe
	
	site = ctx.obj.get("sites", [None])[0] if ctx.obj and "sites" in ctx.obj else None
	if not site:
		click.echo("Please specify a site using --site option")
		return
	
	frappe.init(site=site)
	frappe.connect()
	
	try:
		# Get all Print Designer formats
		print_designer_formats = frappe.get_all(
			"Print Format",
			filters={"print_designer": 1},
			fields=["name", "pdf_generator"]
		)
		
		if not print_designer_formats:
			click.echo("No Print Designer formats found.")
			return
		
		updated_count = 0
		for format_doc in print_designer_formats:
			try:
				current_generator = format_doc.get("pdf_generator", "")
				
				if current_generator != "chrome":
					# Update the format to use Chrome PDF generator
					frappe.db.set_value(
						"Print Format",
						format_doc.name,
						"pdf_generator",
						"chrome"
					)
					updated_count += 1
					click.echo(f"✅ Updated '{format_doc.name}' to use Chrome PDF generator")
				else:
					click.echo(f"⏭️  '{format_doc.name}' already uses Chrome PDF generator")
					
			except Exception as e:
				click.echo(f"❌ Failed to update format '{format_doc.name}': {str(e)}")
		
		if updated_count > 0:
			frappe.db.commit()
			click.echo(f"\n🎉 Successfully updated {updated_count} Print Designer formats!")
			click.echo("Copy functionality should now work for all Print Designer formats.")
		else:
			click.echo("\n✅ All Print Designer formats already use Chrome PDF generator.")
			
	except Exception as e:
		click.echo(f"❌ Error: {str(e)}")
		frappe.db.rollback()
	finally:
		frappe.destroy()


commands = [setup_chorme, fix_pdf_generator]
