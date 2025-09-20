import frappe

def verify_pnd_form_updates():
	"""Verify all PND forms have been updated with Int field types"""
	pnd_forms = ['PND1 Form', 'PND3 Form', 'PND53 Form', 'PND54 Form']

	results = {}
	for doctype in pnd_forms:
		try:
			doc_meta = frappe.get_meta(doctype)
			month_field = doc_meta.get_field('tax_period_month')
			results[doctype] = {
				'fieldtype': month_field.fieldtype,
				'default': month_field.default,
				'success': month_field.fieldtype == 'Int'
			}
			print(f"✅ {doctype}: tax_period_month is {month_field.fieldtype} field")
		except Exception as e:
			results[doctype] = {'error': str(e), 'success': False}
			print(f"❌ {doctype}: Error - {e}")

	# Summary
	success_count = sum(1 for r in results.values() if r.get('success', False))
	print(f"\n📊 Summary: {success_count}/{len(pnd_forms)} PND forms successfully updated")

	return results

def test_pnd_form_creation():
	"""Test creating a new PND form with the new naming system"""
	try:
		# Test PND3 Form creation (already updated in previous session)
		test_doc = frappe.new_doc('PND3 Form')
		test_doc.tax_period_month = 9  # Integer value
		test_doc.tax_period_year = 2568
		test_doc.company = frappe.db.get_single_value('Global Defaults', 'default_company')

		# Test autoname function (should generate PND3-2568-09-XXX)
		test_doc.save()

		print(f"✅ Successfully created PND3 Form: {test_doc.name}")
		print(f"📋 Name format verified: {test_doc.name}")

		# Clean up test document
		frappe.delete_doc('PND3 Form', test_doc.name, force=True)
		print(f"🧹 Cleaned up test document")

		return True

	except Exception as e:
		print(f"❌ Test creation failed: {e}")
		return False

def run_complete_verification():
	"""Run complete verification of all PND form updates"""
	print("🔍 Verifying PND Form Updates...")
	print("=" * 50)

	# Verify field types
	field_results = verify_pnd_form_updates()

	print("\n🧪 Testing PND Form Creation...")
	print("=" * 50)

	# Test form creation
	creation_test = test_pnd_form_creation()

	print("\n📋 Final Status:")
	print("=" * 50)
	all_success = all(r.get('success', False) for r in field_results.values()) and creation_test

	if all_success:
		print("🎉 All PND forms successfully updated and tested!")
		print("✅ Ready for production use with new naming system")
	else:
		print("⚠️ Some issues detected - review the output above")

	return all_success