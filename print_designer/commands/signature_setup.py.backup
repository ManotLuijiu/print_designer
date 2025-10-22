import click
import frappe
from frappe.commands import pass_context, get_site


@click.command("setup-signatures")
@click.option("--site", help="Site name")
@click.option("--force", is_flag=True, help="Force reinstall even if already installed")
@pass_context
def setup_signatures(context, site=None, force=False):
	"""Set up signature enhancements for Print Designer"""
	
	if not site:
		site = get_site(context)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			if force:
				click.echo("Force reinstalling signature enhancements...")
				from print_designer.api.safe_install import force_reinstall
				result = force_reinstall()
			else:
				click.echo("Installing signature enhancements...")
				from print_designer.api.safe_install import safe_install_signature_enhancements
				result = safe_install_signature_enhancements()
			
			if result.get("success"):
				click.echo(click.style("✓ Signature enhancements installed successfully!", fg="green"))
				
				for step in result.get("steps", []):
					status = "✓" if step["success"] else "✗"
					color = "green" if step["success"] else "red"
					click.echo(f"  {click.style(status, fg=color)} {step['title']}: {step['message']}")
			else:
				click.echo(click.style(f"✗ Installation failed: {result.get('error', 'Unknown error')}", fg="red"))
				
		except Exception as e:
			click.echo(click.style(f"✗ Error: {str(e)}", fg="red"))
			raise
		finally:
			frappe.destroy()


@click.command("check-signature-status")
@click.option("--site", help="Site name")
@pass_context
def check_signature_status(context, site=None):
	"""Check signature enhancement installation status"""
	
	if not site:
		site = get_site(context)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			from print_designer.api.safe_install import check_installation_status
			status = check_installation_status()
			
			if status.get("error"):
				click.echo(click.style(f"✗ Error checking status: {status['error']}", fg="red"))
				return
			
			overall_status = "✓ READY" if status["overall_installed"] else "✗ NEEDS SETUP"
			color = "green" if status["overall_installed"] else "yellow"
			click.echo(click.style(f"Overall Status: {overall_status}", fg=color))
			click.echo()
			
			for check in status["checks"]:
				status_mark = "✓" if check["installed"] else "✗"
				color = "green" if check["installed"] else "red"
				click.echo(f"  {click.style(status_mark, fg=color)} {check['component']}")
				
				if isinstance(check["details"], list) and check["details"]:
					for detail in check["details"]:
						if isinstance(detail, dict) and "fieldname" in detail:
							click.echo(f"    - {detail['fieldname']} ({detail['label']})")
				elif isinstance(check["details"], dict):
					for key, value in check["details"].items():
						click.echo(f"    - {key}: {value}")
			
			if not status["overall_installed"]:
				click.echo()
				click.echo(click.style("To install, run:", fg="yellow"))
				click.echo(f"  bench --site {site} setup-signatures")
				
		except Exception as e:
			click.echo(click.style(f"✗ Error: {str(e)}", fg="red"))
			raise
		finally:
			frappe.destroy()


commands = [
	setup_signatures,
	check_signature_status
]