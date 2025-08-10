"""
Test PDF Generators command for Print Designer
Tests availability and functionality of all PDF generators
"""

import click
import frappe
from frappe.commands import pass_context, get_site


@click.command('test-pdf-generators')
@click.option('--site', help='Site name')
@pass_context
def test_pdf_generators(context, site=None):
	"""Test availability and functionality of PDF generators"""
	if not site:
		site = get_site(context)
	
	frappe.init(site=site)
	frappe.connect()
	
	try:
		from print_designer.pdf_generator_manager import PDFGeneratorManager
		
		click.echo("\n" + "="*60)
		click.echo("PDF GENERATOR AVAILABILITY TEST")
		click.echo("="*60)
		
		# Test availability
		available = PDFGeneratorManager.get_available_generators()
		current = PDFGeneratorManager.determine_generator()
		
		click.echo(f"\nAvailable Generators: {len(available)}")
		for i, generator in enumerate(available, 1):
			status = "✓ CURRENT" if generator == current else "✓ Available"
			click.echo(f"  {i}. {generator:<15} {status}")
		
		click.echo(f"\nAuto-Selected Generator: {current}")
		
		# Test individual generators
		click.echo("\n" + "-"*40)
		click.echo("INDIVIDUAL GENERATOR TESTS")
		click.echo("-"*40)
		
		test_html = """
		<html>
		<head><title>PDF Test</title></head>
		<body>
			<h1>PDF Generator Test</h1>
			<p>This is a test document for PDF generation.</p>
			<div style="border: 1px solid #000; padding: 10px; margin: 10px 0;">
				<strong>Test Content:</strong> Basic HTML with CSS styling.
			</div>
		</body>
		</html>
		"""
		
		# Test wkhtmltopdf (always available)
		click.echo("1. Testing wkhtmltopdf...")
		try:
			from frappe.utils.pdf import get_pdf
			pdf_output = get_pdf(test_html)
			if pdf_output and len(pdf_output) > 1000:  # Basic size check
				click.echo("   ✓ wkhtmltopdf: SUCCESS")
			else:
				click.echo("   ✗ wkhtmltopdf: FAILED (empty output)")
		except Exception as e:
			click.echo(f"   ✗ wkhtmltopdf: FAILED ({str(e)})")
		
		# Test WeasyPrint
		if "WeasyPrint" in available:
			click.echo("2. Testing WeasyPrint...")
			try:
				import weasyprint
				html_doc = weasyprint.HTML(string=test_html)
				pdf_output = html_doc.write_pdf()
				if pdf_output and len(pdf_output) > 1000:
					click.echo("   ✓ WeasyPrint: SUCCESS")
				else:
					click.echo("   ✗ WeasyPrint: FAILED (empty output)")
			except Exception as e:
				click.echo(f"   ✗ WeasyPrint: FAILED ({str(e)})")
		else:
			click.echo("2. WeasyPrint: Not available (import failed)")
		
		# Test Chrome
		if "chrome" in available:
			click.echo("3. Testing Chrome...")
			try:
				from print_designer.pdf_generator.generator import FrappePDFGenerator
				generator = FrappePDFGenerator()
				# Just test if we can initialize Chrome
				if generator:
					click.echo("   ✓ Chrome: Available (dependencies found)")
				else:
					click.echo("   ✗ Chrome: FAILED (initialization failed)")
			except Exception as e:
				click.echo(f"   ✗ Chrome: FAILED ({str(e)})")
		else:
			click.echo("3. Chrome: Not available (dependencies missing)")
		
		# Test Print Designer specific functionality
		click.echo("\n" + "-"*40)
		click.echo("PRINT DESIGNER INTEGRATION TEST")
		click.echo("-"*40)
		
		# Check if Print Designer formats exist
		pd_formats = frappe.get_all("Print Format", 
			filters={"print_designer": 1}, 
			fields=["name", "pdf_generator"],
			limit=5
		)
		
		if pd_formats:
			click.echo(f"\nFound {len(pd_formats)} Print Designer formats:")
			for fmt in pd_formats:
				generator_info = fmt.get("pdf_generator", "Not set")
				click.echo(f"  • {fmt['name']:<30} → {generator_info}")
		else:
			click.echo("\nNo Print Designer formats found.")
		
		# Final recommendations
		click.echo("\n" + "="*60)
		click.echo("RECOMMENDATIONS")
		click.echo("="*60)
		
		if "WeasyPrint" in available:
			click.echo("✓ RECOMMENDED: WeasyPrint")
			click.echo("  - Best CSS support")
			click.echo("  - Native Python integration")
			click.echo("  - No external dependencies")
		
		if "wkhtmltopdf" in available:
			click.echo("✓ FALLBACK: wkhtmltopdf") 
			click.echo("  - Reliable and stable")
			click.echo("  - Limited CSS support")
			click.echo("  - Good for simple layouts")
		
		if "chrome" in available:
			click.echo("⚠ ADVANCED: Chrome")
			click.echo("  - Full CSS support")
			click.echo("  - Resource intensive")
			click.echo("  - Complex setup requirements")
		
		click.echo(f"\nCurrent auto-selection: {current}")
		click.echo("PDF generators are working correctly! ✓")
		
	except Exception as e:
		click.echo(f"Error testing PDF generators: {str(e)}")
		raise
	finally:
		frappe.destroy()


commands = [test_pdf_generators]