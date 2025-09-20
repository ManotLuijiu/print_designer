import click
import frappe
from frappe.utils import flt


@click.command()
@click.option('--site', default='moo.localhost', help='Site name')
@click.option('--pnd-form', default='PND53-2568-09-073', help='PND Form name to test')
def test_pnd_population(site, pnd_form):
	"""Test PND53 Form automatic WHT certificate population"""
	frappe.init(site=site)
	frappe.connect()

	try:
		# Get the PND53 form
		doc = frappe.get_doc('PND53 Form', pnd_form)

		print(f"\n=== Testing PND53 Form: {doc.name} ===")
		print(f"Tax Period: {doc.tax_period_month}/{doc.tax_period_year}")
		print(f"Initial items count: {len(doc.items)}")

		# Test the populate method
		doc.populate_wht_certificates()

		print(f"After populate_wht_certificates: {len(doc.items)} items")

		# Show details of populated items
		if doc.items:
			print("\nPopulated certificates:")
			for i, item in enumerate(doc.items, 1):
				print(f"  {i}. {item.withholding_tax_cert}: {item.company_name} - ฿{item.tax_amount}")
		else:
			print("No certificates were populated!")

		# Calculate totals
		doc.calculate_totals()

		print(f"\nSummary:")
		print(f"  Total certificates: {doc.total_certificates}")
		print(f"  Total tax amount: ฿{doc.total_tax_amount}")

		# Save the document to persist the populated items
		doc.save()
		print(f"\nDocument saved successfully with {len(doc.items)} items")

		return len(doc.items)

	except Exception as e:
		print(f"Error: {str(e)}")
		return 0
	finally:
		frappe.db.close()


if __name__ == "__main__":
	test_pnd_population()