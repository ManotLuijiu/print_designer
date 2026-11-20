"""Regression tests for the missing-only default template installer."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from print_designer.default_templates_installer import (
    collect_referenced_fields,
    collect_required_amount_fields,
    discover_template_files,
    find_missing_dependencies,
    get_templates_root,
    install_missing_default_formats,
    validate_template_document,
)

APP_ROOT = Path(__file__).resolve().parents[2]
SERVICES_QUOTATION = (
    APP_ROOT
    / "print_designer"
    / "default_templates"
    / "asean_business_suite"
    / "services_quotation.json"
)


def make_template(name="PD Test Template", doc_type="Quotation", **extra):
    doc = {
        "doctype": "Print Format",
        "name": name,
        "doc_type": doc_type,
        "module": "Selling",
        "standard": "No",
        "print_designer": 1,
        "print_designer_template_app": "print_designer",
        "print_designer_body": json.dumps({"data": []}),
        "print_designer_header": json.dumps({"data": []}),
        "print_designer_footer": json.dumps({"data": []}),
        "print_designer_settings": json.dumps({"schema_version": "1.3.0"}),
    }
    doc.update(extra)
    return doc


def collect_image_bindings(data):
    """Every dynamic image binding of a saved design."""
    bindings = []

    def walk(node):
        if isinstance(node, dict):
            image = node.get("image")
            if isinstance(image, dict) and image.get("fieldname"):
                bindings.append(image)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for key in (
        "print_designer_body",
        "print_designer_header",
        "print_designer_footer",
        "print_designer_print_format",
    ):
        blob = data.get(key)
        if not blob:
            continue
        payload = json.loads(blob) if isinstance(blob, str) else blob
        walk(payload)

    return bindings


class TestTemplateDiscovery(unittest.TestCase):
    def test_discovery_is_sorted_by_relative_path(self):
        files = discover_template_files()
        relative_paths = [relative for relative, _path in files]

        self.assertEqual(relative_paths, sorted(relative_paths))
        self.assertIn("asean_business_suite/services_quotation.json", relative_paths)

    def test_preview_files_are_not_templates(self):
        relative_paths = [relative for relative, _path in discover_template_files()]

        for relative_path in relative_paths:
            self.assertFalse(relative_path.endswith("-preview.json"))

    def test_templates_root_is_inside_the_app(self):
        root = get_templates_root()

        self.assertTrue(root.is_dir())
        self.assertEqual(root.name, "default_templates")
        self.assertTrue(str(root).startswith(str(APP_ROOT)))


class TestTemplateValidation(unittest.TestCase):
    def test_preview_file_payload_is_rejected(self):
        candidate, error = validate_template_document({"doctype": "File", "name": "x"}, "a.json")

        self.assertIsNone(candidate)
        self.assertIsNotNone(error)
        self.assertIn("unsupported_payload", str(error))

    def test_missing_name_is_rejected(self):
        candidate, error = validate_template_document({"doctype": "Print Format"}, "a.json")

        self.assertIsNone(candidate)
        self.assertIsNotNone(error)
        self.assertIn("missing_name", str(error))

    def test_missing_doc_type_is_rejected(self):
        candidate, error = validate_template_document(
            {"doctype": "Print Format", "name": "x"}, "a.json"
        )

        self.assertIsNone(candidate)
        self.assertIsNotNone(error)
        self.assertIn("missing_doc_type", str(error))

    def test_valid_template_is_accepted(self):
        candidate, error = validate_template_document(make_template(), "a.json")

        self.assertIsNone(error)
        assert candidate is not None
        self.assertEqual(candidate["name"], "PD Test Template")
        self.assertEqual(candidate["doc_type"], "Quotation")


class TestDependencyDetection(unittest.TestCase):
    def test_missing_fields_are_reported(self):
        missing = find_missing_dependencies("Quotation", {"pd_custom_definitely_missing"})

        self.assertIn("pd_custom_definitely_missing", missing)

    def test_existing_fields_are_not_reported(self):
        missing = find_missing_dependencies("Quotation", {"company", "grand_total"})

        self.assertEqual(missing, [])

    def test_legacy_amount_binding_is_resolved(self):
        """A design that still names the pre-rename field must not be deferred."""
        meta_fields = {
            "pd_custom_net_total_after_wht",
            "pd_custom_net_total_after_wht_words",
        }
        with patch(
            "print_designer.default_templates_installer.get_valid_fieldnames",
            return_value=meta_fields,
        ):
            missing = find_missing_dependencies(
                "Quotation",
                set(),
                {"net_total_after_wht", "net_total_after_wht_in_words"},
            )

        self.assertEqual(missing, [])

    def test_random_element_ids_are_ignored(self):
        missing = find_missing_dependencies("Quotation", {"AeRQikuuqk", "kTvevPFIwP"})

        self.assertEqual(missing, [])


class TestServicesQuotationTemplate(unittest.TestCase):
    """The shipped template must stay portable and free of source site assets."""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SERVICES_QUOTATION.read_text())

    def test_template_is_a_print_format_document(self):
        self.assertEqual(self.data["doctype"], "Print Format")
        self.assertEqual(self.data["name"], "services_quotation")
        self.assertEqual(self.data["doc_type"], "Quotation")
        self.assertEqual(self.data["print_designer_template_app"], "print_designer")

    def test_template_has_no_source_site_asset(self):
        raw = SERVICES_QUOTATION.read_text()

        self.assertNotIn("/files/", raw)
        self.assertNotIn("/private/files/", raw)
        self.assertEqual(self.data.get("print_designer_preview_img", ""), "")

    def test_template_uses_the_dynamic_company_logo(self):
        bindings = collect_image_bindings(self.data)

        self.assertEqual(len(bindings), 10)
        for binding in bindings:
            self.assertEqual(binding["doctype"], "Company")
            self.assertEqual(binding["fieldname"], "company_logo")
            self.assertEqual(binding["parentField"], "company")

    def test_image_field_of_the_linked_doctype_is_not_a_document_field(self):
        referenced = collect_referenced_fields(self.data)

        self.assertNotIn("company_logo", referenced)
        self.assertIn("company", referenced)

    def test_template_saved_current_document_is_empty(self):
        settings = json.loads(self.data["print_designer_settings"])

        self.assertIsNone(settings.get("currentDoc"))

    def test_template_number_to_words_pair_uses_legacy_binding(self):
        settings = json.loads(self.data["print_designer_settings"])
        pairs = settings.get("numberToWordsFieldPairs")

        self.assertEqual(
            pairs,
            [
                {
                    "source_field": "net_total_after_wht",
                    "target_field": "net_total_after_wht_in_words",
                    "currency_field": "currency",
                }
            ],
        )

    def test_referenced_fields_are_resolved_on_a_quotation_site(self):
        if not frappe.db.exists("DocType", "Quotation"):
            self.skipTest("Quotation is not installed on this site")

        missing = find_missing_dependencies(
            "Quotation",
            collect_referenced_fields(self.data),
            collect_required_amount_fields(self.data),
        )

        self.assertEqual(missing, [])


class TestMissingOnlyInstallation(FrappeTestCase):
    """The installer may only add formats, never touch an existing one."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.created = []
        self.addCleanup(self.temp_dir.cleanup)
        self.addCleanup(self._cleanup_formats)

    def _cleanup_formats(self):
        for name in self.created:
            if frappe.db.exists("Print Format", name):
                frappe.delete_doc("Print Format", name, force=True, ignore_permissions=True)

    def _write_template(self, relative_path, doc):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, indent=1))
        self.created.append(doc["name"])

    def _install(self, **kwargs):
        with patch(
            "print_designer.default_templates_installer.get_templates_root",
            return_value=self.root,
        ):
            return install_missing_default_formats(**kwargs)

    def test_missing_template_is_imported(self):
        self._write_template("category/format.json", make_template(name="PD Import One"))

        results = self._install()

        self.assertEqual([entry["name"] for entry in results["imported"]], ["PD Import One"])
        self.assertTrue(frappe.db.exists("Print Format", "PD Import One"))

    def test_installed_template_keeps_its_design(self):
        self._write_template("category/format.json", make_template(name="PD Import Two"))

        self._install()

        values = frappe.db.get_value(
            "Print Format",
            "PD Import Two",
            ["doc_type", "print_designer", "standard", "print_designer_template_app"],
        )
        assert values is not None
        self.assertEqual(tuple(values), ("Quotation", 1, "No", "print_designer"))

    def test_rerun_reports_existing_and_changes_nothing(self):
        self._write_template("category/format.json", make_template(name="PD Import Three"))

        self._install()
        frappe.db.set_value("Print Format", "PD Import Three", "disabled", 1)

        results = self._install()

        self.assertEqual(results["imported"], [])
        self.assertEqual([entry["name"] for entry in results["existing"]], ["PD Import Three"])
        self.assertEqual(frappe.db.get_value("Print Format", "PD Import Three", "disabled"), 1)

    def test_existing_format_is_never_overwritten(self):
        self._write_template("category/format.json", make_template(name="PD Import Four"))
        self._install()

        frappe.db.set_value("Print Format", "PD Import Four", "disabled", 1)
        frappe.db.set_value(
            "Print Format",
            "PD Import Four",
            "print_designer_preview_img",
            "/files/custom-preview.png",
        )

        before = frappe.db.get_value(
            "Print Format", "PD Import Four", ["modified", "disabled", "print_designer_preview_img"]
        )

        self._install()

        after = frappe.db.get_value(
            "Print Format", "PD Import Four", ["modified", "disabled", "print_designer_preview_img"]
        )

        self.assertEqual(before, after)

    def test_dry_run_inserts_nothing(self):
        self._write_template("category/format.json", make_template(name="PD Import Five"))

        results = self._install(dry_run=True)

        self.assertEqual(results["imported"], [])
        self.assertEqual([entry["name"] for entry in results["pending"]], ["PD Import Five"])
        self.assertFalse(frappe.db.exists("Print Format", "PD Import Five"))

    def test_missing_doctype_is_deferred(self):
        self._write_template(
            "category/format.json",
            make_template(name="PD Deferred DocType", doc_type="No Such DocType"),
        )

        results = self._install()

        self.assertEqual(results["imported"], [])
        deferred = [
            entry for entry in results["deferred"] if entry["name"] == "PD Deferred DocType"
        ]
        self.assertEqual(len(deferred), 1)
        self.assertIn("missing_doctype", deferred[0]["reason"])
        self.assertFalse(frappe.db.exists("Print Format", "PD Deferred DocType"))

    def test_missing_custom_field_is_deferred(self):
        template = make_template(name="PD Deferred Field")
        template["print_designer_body"] = json.dumps(
            {"data": [{"columns": [[{"field": "pd_custom_field_that_is_missing"}]]}]}
        )
        self._write_template("category/format.json", template)

        results = self._install()

        deferred = [entry for entry in results["deferred"] if entry["name"] == "PD Deferred Field"]
        self.assertEqual(len(deferred), 1)
        self.assertIn("missing_fields", deferred[0]["reason"])
        self.assertIn("pd_custom_field_that_is_missing", deferred[0]["missing_fields"])

    def test_duplicate_names_are_reported(self):
        self._write_template("a-first.json", make_template(name="PD Duplicate"))
        self._write_template("b-second.json", make_template(name="PD Duplicate"))

        results = self._install()

        self.assertEqual(len(results["conflicts"]), 1)
        self.assertEqual(results["conflicts"][0]["winner"], "a-first.json")
        self.assertEqual(len(results["invalid"]), 1)
        self.assertIn("duplicate_name", results["invalid"][0]["reason"])
        self.assertEqual(len(results["imported"]), 1)

    def test_broken_json_is_reported_as_invalid(self):
        path = self.root / "broken.json"
        path.write_text("{not json")

        results = self._install()

        self.assertEqual(len(results["invalid"]), 1)
        self.assertIn("invalid_json", results["invalid"][0]["reason"])

    def test_template_is_not_made_a_default(self):
        self._write_template("category/format.json", make_template(name="PD No Default"))

        self._install()

        self.assertFalse(
            frappe.db.get_value("DocType", "Quotation", "default_print_format") == "PD No Default"
        )


class TestDefaultTemplateApiFlags(FrappeTestCase):
    """The API reads its flag the way the client meant it.

    A whitelisted method receives its arguments from the request, so the flag
    arrives as a string.  "0" and "false" have to read as "off", otherwise the
    installer runs as a dry run while the caller asked for a real one.
    """

    def _run(self, dry_run):
        from print_designer.api import default_templates_api

        captured = {}

        def fake_install(dry_run=False):
            captured["dry_run"] = dry_run
            return {"imported": [], "pending": [], "existing": [], "invalid": []}

        with (
            patch.object(default_templates_api, "install_missing_default_formats", fake_install),
            patch.object(frappe.db, "commit") as commit,
        ):
            default_templates_api.run_default_template_installation(dry_run=dry_run)

        return captured["dry_run"], commit.called

    def test_a_string_off_is_read_as_off(self):
        for value in ("0", "false", "False", "no", "off", ""):
            dry_run, committed = self._run(value)
            self.assertFalse(dry_run, f"{value!r} should read as off")
            self.assertTrue(committed, f"{value!r} should run for real")

    def test_a_string_on_is_read_as_on(self):
        for value in ("1", "true", "True", "yes", "on"):
            dry_run, committed = self._run(value)
            self.assertTrue(dry_run, f"{value!r} should read as on")
            self.assertFalse(committed, f"{value!r} should not commit")

    def test_a_real_boolean_is_kept(self):
        self.assertTrue(self._run(True)[0])
        self.assertFalse(self._run(False)[0])

    def test_no_flag_reads_as_off(self):
        dry_run, committed = self._run(None)
        self.assertFalse(dry_run)
        self.assertTrue(committed)
