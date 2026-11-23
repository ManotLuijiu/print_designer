import unittest

import frappe

from print_designer.custom import wht_canonical_mapping as mapping

SERVICE_CODE = "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ"
CONTRACT_CODE = "40(7) ค่าจ้างทำของ"
SALARY_CODE = "40(1) เงินเดือน ค่าจ้าง"
RENT_CODE = "40(5) ค่าเช่า"

COMPANY_SERVICE_LINE = "5. ค่าจ้างทำของ ค่าบริการ ฯลฯ 3 เตรส - Service"
INDIVIDUAL_SERVICE_LINE = "40 (8) ค่าจ้างทำของ(อื่นๆ) (3%)"


class TestWhCanonicalMapping(unittest.TestCase):
    """The line, the form and the classification of a certificate agree."""

    def _resolve(self, income_type, entity_type):
        return mapping.resolve_income_type(income_type, entity_type)

    def test_service_of_a_company_uses_the_line_of_a_company(self):
        resolved = self._resolve(SERVICE_CODE, "Company")

        self.assertEqual(resolved["income_type"], COMPANY_SERVICE_LINE)
        self.assertEqual(resolved["item_income_type"], "40(8) ค่าบริการ/ค่าวิชาชีพอิสระ")
        self.assertEqual(resolved["classification"], mapping.CLASSIFICATION_COMPANY)
        self.assertEqual(resolved["pnd_form"], "PND53 Form")

    def test_service_of_an_individual_uses_the_line_of_an_individual(self):
        resolved = self._resolve(SERVICE_CODE, "Individual")

        self.assertEqual(resolved["income_type"], INDIVIDUAL_SERVICE_LINE)
        self.assertEqual(resolved["classification"], mapping.CLASSIFICATION_NON_STAFF)
        self.assertEqual(resolved["pnd_form"], "PND3 Form")

    def test_contract_work_of_a_company_uses_the_line_of_a_company(self):
        resolved = self._resolve(CONTRACT_CODE, "Company")

        self.assertEqual(resolved["income_type"], COMPANY_SERVICE_LINE)
        self.assertEqual(resolved["classification"], mapping.CLASSIFICATION_COMPANY)
        self.assertEqual(resolved["pnd_form"], "PND53 Form")

    def test_salary_of_an_individual_is_reported_on_the_form_of_a_staff(self):
        resolved = self._resolve(SALARY_CODE, "Individual")

        self.assertEqual(resolved["classification"], mapping.CLASSIFICATION_STAFF)
        self.assertEqual(resolved["pnd_form"], "PND1 Form")

    def test_rent_follows_the_kind_of_the_payee(self):
        company = self._resolve(RENT_CODE, "Company")
        individual = self._resolve(RENT_CODE, "Individual")

        self.assertEqual(company["pnd_form"], "PND53 Form")
        self.assertEqual(company["classification"], mapping.CLASSIFICATION_COMPANY)
        self.assertEqual(individual["pnd_form"], "PND3 Form")
        self.assertEqual(individual["classification"], mapping.CLASSIFICATION_NON_STAFF)

    def test_the_classification_always_names_the_form_of_the_tax(self):
        codes = sorted(mapping.LEGACY_INCOME_TYPES)
        for code in codes:
            for entity_type in ("Company", "Government", "Individual", None):
                resolved = self._resolve(code, entity_type)
                classification = resolved["classification"]
                pnd_form = resolved["pnd_form"]

                self.assertTrue(classification, msg=f"{code} / {entity_type}")
                self.assertTrue(pnd_form, msg=f"{code} / {entity_type}")

                if pnd_form == "PND1 Form":
                    self.assertEqual(classification, mapping.CLASSIFICATION_STAFF, msg=code)
                elif pnd_form == "PND3 Form":
                    self.assertEqual(classification, mapping.CLASSIFICATION_NON_STAFF, msg=code)
                elif pnd_form == "PND53 Form":
                    self.assertEqual(classification, mapping.CLASSIFICATION_COMPANY, msg=code)

    def _options(self, doctype):
        field = frappe.get_meta(doctype).get_field("income_type")
        if not field:
            raise AssertionError(f"{doctype} has no income_type field")
        return {option.strip() for option in field.options.split("\n") if option.strip()}

    def test_every_mapped_line_exists_in_the_metadata_of_the_certificate(self):
        parent_options = self._options(mapping.CERTIFICATE_INCOME_TYPE)
        item_options = self._options(mapping.CERTIFICATE_ITEM_INCOME_TYPE)

        for parent, child in mapping.LEGACY_INCOME_TYPES.values():
            self.assertIn(parent, parent_options, msg=parent)
            self.assertIn(child, item_options, msg=child)

        for parent, child in mapping.LEGACY_COMPANY_INCOME_TYPES.values():
            self.assertIn(parent, parent_options, msg=parent)
            self.assertIn(child, item_options, msg=child)

    def test_an_unknown_income_type_resolves_to_nothing(self):
        resolved = self._resolve("_Test No Such Income Type", "Company")

        self.assertEqual(resolved["income_type"], "")
        self.assertEqual(resolved["item_income_type"], "")
        self.assertEqual(resolved["pnd_form"], None)
