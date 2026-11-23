"""Tests for the Print Designer owned form 50 ทวิ view model."""

from datetime import date

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer import hooks
from print_designer.custom import form_50_tawi


class TestForm50TawiMapping(FrappeTestCase):
	def test_statutory_row_of_income_type(self):
		cases = {
			"40(1) เงินเดือน ค่าจ้าง": "1",
			"40(2) ค่านายหน้า ค่าคอมมิชชั่น": "2",
			"40(3) ค่าลิขสิทธิ์": "3",
			"40(4)ก ดอกเบี้ย": "4a",
			"40(4)ข เงินปันผล": "4b",
			"40(5) ค่าเช่า": "5",
			"40(8) ค่าบริการ/ค่าวิชีพอิสระ": "5",
			"40(7) ค่าจ้างทำของ": "5",
			"5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service": "5",
			"8. ค่าโฆษณา - Advertising": "5",
			"9. ค่าเช่า - Rent": "5",
			"12. อื่นๆ - Others": "6",
			"": "6",
			None: "6",
		}
		for income_type, expected in cases.items():
			self.assertEqual(
				form_50_tawi.map_income_type_to_row(income_type),
				expected,
				msg=f"income type {income_type!r}",
			)

	def test_tax_id_cleanup_keeps_leading_zeros(self):
		self.assertEqual(form_50_tawi.clean_tax_id("0-9999-99999-99-1"), "0999999999991")
		self.assertEqual(form_50_tawi.clean_tax_id(" 3801100198897 "), "3801100198897")
		self.assertEqual(form_50_tawi.clean_tax_id(None), "")

	def test_incomplete_tax_id_stays_blank_for_the_boxes(self):
		self.assertEqual(form_50_tawi.tax_id_for_boxes("0-9999-99999-99-1"), "0999999999991")
		self.assertEqual(form_50_tawi.tax_id_for_boxes("3801100198"), "")
		self.assertEqual(form_50_tawi.tax_id_for_boxes(None), "")

	def test_branch_text(self):
		self.assertEqual(form_50_tawi.format_branch_text("00000"), "(สำนักงานใหญ่)")
		self.assertEqual(form_50_tawi.format_branch_text("00001"), "(สาขาที่ 1)")
		self.assertEqual(form_50_tawi.format_branch_text(""), "")

	def test_payment_date_is_buddhist_era(self):
		self.assertEqual(form_50_tawi.format_payment_date(date(2026, 6, 3)), "03/06/2569")
		self.assertEqual(form_50_tawi.format_payment_date(None), "")

	def test_only_the_exact_dgs_format_is_classified_as_dgs(self):
		self.assertTrue(form_50_tawi.is_dgs_form_50_tawi("DGS Form 50 Tawi"))
		self.assertFalse(form_50_tawi.is_dgs_form_50_tawi("50Tawi Form"))
		self.assertFalse(form_50_tawi.is_dgs_form_50_tawi("DGS Form 50 Tawi "))
		self.assertFalse(form_50_tawi.is_dgs_form_50_tawi(None))
		self.assertEqual(
			form_50_tawi.get_form_50_tawi_wrapper_class("DGS Form 50 Tawi"),
			form_50_tawi.FORM_50_TAWI_WRAPPER_CLASS,
		)
		self.assertEqual(form_50_tawi.get_form_50_tawi_wrapper_class("50Tawi Form"), "")

	def test_helper_is_registered_as_jinja_method(self):
		methods = hooks.jinja["methods"]
		self.assertIn("print_designer.custom.form_50_tawi.get_form_50_tawi_data", methods)
		self.assertIn("print_designer.custom.form_50_tawi.get_form_50_tawi_wrapper_class", methods)

	def test_certificate_fields_used_by_the_helper_exist(self):
		parent_fields = {df.fieldname for df in frappe.get_meta("Withholding Tax Certificate").fields}
		for field in (
			"certificate_number",
			"certificate_date",
			"payment_date",
			"tax_year",
			"tax_month",
			"supplier",
			"supplier_name",
			"supplier_tax_id",
			"supplier_address",
			"supplier_branch_code",
			"company",
			"company_branch",
			"income_type",
			"income_description",
			"wht_rate",
			"wht_condition",
			"tax_base_amount",
			"wht_amount",
			"supplier_type_classification",
			"pnd_form_type",
			"income_items",
		):
			self.assertIn(field, parent_fields, msg=field)

		item_fields = {df.fieldname for df in frappe.get_meta("Withholding Tax Item").fields}
		for field in (
			"income_type",
			"income_type_description",
			"payment_date",
			"gross_amount",
			"tax_amount",
		):
			self.assertIn(field, item_fields, msg=field)


class TestForm50TawiViewModel(FrappeTestCase):
	def _certificate(self, **overrides):
		values = {
			"certificate_number": "WHTC-6906-00005",
			"certificate_date": date(2026, 6, 3),
			"payment_date": date(2026, 6, 3),
			"tax_year": "2569",
			"tax_month": "06 - มิถุนายน (June)",
			"supplier": "TEST-SUP-0001",
			"supplier_name": "บริษัท ทดสอบ จำกัด",
			"supplier_tax_id": "0-9999-99999-99-1",
			"supplier_address": "99/1 ถนนทดสอบ",
			"supplier_branch_code": "00000",
			"company": "",
			"company_branch": "00000",
			"income_type": "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service",
			"income_description": "ค่าสิขภาพและบริการ",
			"wht_rate": 3.0,
			"wht_condition": "1. หัก ณ ที่จ่าย (Withhold at Source)",
			"tax_base_amount": 100.0,
			"wht_amount": 3.0,
			"net_payment_amount": 103.0,
			"supplier_type_classification": "Company/Juristic Person (PND.53)",
			"pnd_form_type": "PND53 Form",
			"income_items": [],
		}
		values.update(overrides)
		return frappe._dict(values)

	def test_parent_only_certificate_builds_one_row(self):
		data = form_50_tawi.build_form_50_tawi_data(self._certificate())

		self.assertTrue(data["has_income_items"] is False)
		self.assertTrue(data["rows"]["5"]["filled"])
		self.assertEqual(data["rows"]["5"]["amount"], 100.0)
		self.assertEqual(data["rows"]["5"]["tax"], 3.0)
		self.assertEqual(data["rows"]["5"]["amount_text"], "100.00")
		self.assertEqual(data["rows"]["5"]["date"], "03/06/2569")
		for key in ("1", "2", "3", "4a", "4b", "6"):
			self.assertFalse(data["rows"][key]["filled"], msg=key)

		self.assertEqual(data["total_amount"], 100.0)
		self.assertEqual(data["total_tax"], 3.0)
		self.assertEqual(data["total_amount_text"], "100.00")
		self.assertEqual(data["total_tax_text"], "3.00")
		self.assertIn("บาท", data["total_tax_words"])

		self.assertEqual(data["signature_day"], "03")
		self.assertEqual(data["signature_month"], "มิถุนายน")
		self.assertEqual(data["signature_year"], "2569")
		self.assertEqual(data["certificate_date"], "03/06/2569")

		self.assertEqual(data["pnd_checkbox"], "7")
		self.assertEqual(data["wht_condition_checkbox"], "1")

		self.assertEqual(data["supplier_tax_id"], "0999999999991")
		self.assertEqual(data["supplier_branch_text"], "(สำนักงานใหญ่)")
		self.assertEqual(data["company_branch_text"], "(สำนักงานใหญ่)")

	def test_child_items_are_mapped_to_statutory_rows(self):
		items = [
			frappe._dict(
				{
					"income_type": "40(1) เงินเดือน ค่าจ้าง",
					"gross_amount": 1000.0,
					"tax_rate": 3.0,
					"tax_amount": 30.0,
					"net_amount": 970.0,
					"payment_date": date(2026, 6, 3),
				}
			),
			frappe._dict(
				{
					"income_type": "40(5) ค่าเช่า",
					"gross_amount": 200.0,
					"tax_rate": 5.0,
					"tax_amount": 10.0,
					"net_amount": 190.0,
					"payment_date": date(2026, 6, 3),
				}
			),
			frappe._dict(
				{
					"income_type": "40(8) ค่าบริการ/ค่าวิชีพอิสระ",
					"gross_amount": 300.0,
					"tax_rate": 3.0,
					"tax_amount": 9.0,
					"net_amount": 291.0,
					"payment_date": date(2026, 6, 3),
				}
			),
		]
		data = form_50_tawi.build_form_50_tawi_data(
			self._certificate(
				income_items=items,
				tax_base_amount=1500.0,
				wht_amount=49.0,
			)
		)

		self.assertTrue(data["has_income_items"])
		self.assertEqual(data["rows"]["1"]["amount"], 1000.0)
		self.assertEqual(data["rows"]["1"]["tax"], 30.0)
		self.assertEqual(data["rows"]["1"]["date"], "03/06/2569")
		self.assertEqual(data["rows"]["5"]["amount"], 500.0)
		self.assertEqual(data["rows"]["5"]["tax"], 19.0)

		self.assertEqual(data["sum_amount"], 1500.0)
		self.assertEqual(data["sum_tax"], 49.0)
		self.assertTrue(data["totals_match"])

	def test_totals_mismatch_is_reported(self):
		data = form_50_tawi.build_form_50_tawi_data(
			self._certificate(
				income_items=[
					frappe._dict(
						{
							"income_type": "40(5) ค่าเช่า",
							"gross_amount": 200.0,
							"tax_amount": 10.0,
							"payment_date": date(2026, 6, 3),
						}
					)
				],
				tax_base_amount=999.0,
				wht_amount=3.0,
			)
		)
		self.assertFalse(data["totals_match"])
		self.assertEqual(data["sum_amount"], 200.0)

	def test_pnd_checkbox_falls_back_to_the_classification(self):
		data = form_50_tawi.build_form_50_tawi_data(
			self._certificate(pnd_form_type="", supplier_type_classification="Individual - Non-staff (PND.3)")
		)
		self.assertEqual(data["pnd_checkbox"], "4")

		data = form_50_tawi.build_form_50_tawi_data(
			self._certificate(pnd_form_type="PND1 Form")
		)
		self.assertEqual(data["pnd_checkbox"], "1")

	def test_optional_fields_stay_empty(self):
		data = form_50_tawi.build_form_50_tawi_data(
			self._certificate(
				certificate_date=None,
				payment_date=None,
				income_type="",
				income_description="",
				supplier_tax_id="",
				supplier_address="",
				tax_base_amount=0.0,
				wht_amount=0.0,
			)
		)
		self.assertEqual(data["certificate_date"], "")
		self.assertEqual(data["signature_day"], "")
		self.assertEqual(data["signature_month"], "")
		self.assertEqual(data["signature_year"], "")
		self.assertEqual(data["supplier_tax_id"], "")
		self.assertFalse(data["rows"]["6"]["filled"])
		self.assertEqual(data["total_amount"], 0.0)
