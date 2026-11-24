"""Acceptance tests of the shipped services quotation template.

The package is the second template of the Phase 2 export: a Print Format
document of Print Designer for a Quotation that the missing-only installer
imports on a site that does not have it yet.

The template must not carry the identity of the site that saved it.  The
company name, the company address, the tax id, the phone number, the e-mail
address, the bank details and the contact person are resolved at print time
from the printed Quotation, from the Company of the printed Quotation, from
the Bank Account of the default bank account of that Company and from the
contact person of the printed Quotation.  The tests below hold that
behaviour:

* the package is a valid template and the installer discovers it,
* the package carries the dynamic company logo and no identity of its own,
* the address comes from the printed Quotation and not from a field of the
  Company that does not exist,
* the bank details come from the Bank Account of the default bank account of
  the Company and not from a field of the Account,
* the contact is displayed with its full name and not with the identifier of
  its link,
* a design that names no field of the printed Quotation is not deferred by
  the installer,
* the rendered page shows the identity of the printed Quotation and blanks
  where the site has no data.
"""

import json
import pathlib
import re
from typing import Any

import frappe
import yaml
from frappe.tests.utils import FrappeTestCase

from print_designer.default_templates_installer import (
    collect_referenced_fields,
    collect_required_amount_fields,
    discover_template_files,
    find_missing_dependencies,
    get_valid_fieldnames,
    insert_template,
    read_json,
    validate_template_document,
)

TEMPLATE_PATH = (
    pathlib.Path(frappe.get_app_path("print_designer"))
    / "default_templates"
    / "asean_business_suite"
    / "services_quotation.json"
)

ASSETS_PATH = TEMPLATE_PATH.with_suffix(".assets.yaml")

TEMPLATE_NAME = "services_quotation"

#: The four payloads of a Print Designer document.  The first three are the
#: pages of the design, the fourth is the whole design that the renderer
#: uses.
DESIGN_PAYLOADS = (
    "print_designer_header",
    "print_designer_body",
    "print_designer_footer",
    "print_designer_print_format",
)

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL_PATTERN = re.compile(r"https?://")


class TestTheServicesQuotationPackage(FrappeTestCase):
    """The package of the services quotation and the installer that imports it."""

    def setUp(self):
        self.data = json.loads(TEMPLATE_PATH.read_text())

    # ------------------------------------------------------------------
    # the package
    # ------------------------------------------------------------------

    def test_the_package_is_a_valid_template(self):
        candidate, error = validate_template_document(self.data, "services_quotation.json")

        self.assertIsNone(error)
        self.assertIsNotNone(candidate)
        self.assertEqual((candidate or {}).get("name"), TEMPLATE_NAME)
        self.assertEqual((candidate or {}).get("doc_type"), "Quotation")

    def test_the_installer_discovers_the_package(self):
        discovered = [relative for relative, _ in discover_template_files("print_designer")]

        self.assertIn("asean_business_suite/services_quotation.json", discovered)

    def test_the_package_carries_the_four_designer_payloads(self):
        """Every payload of the design must be present and readable.

        A missing payload is not an empty page: the renderer reads the
        payloads and a payload that cannot be read is an error.
        """
        for key in DESIGN_PAYLOADS:
            self.assertIn(key, self.data, f"the package carries no {key}")
            self.assertTrue(self.data[key], f"the {key} of the package is empty")

            payload = json.loads(self.data[key])
            self.assertIsInstance(payload, (list, dict), key)

    def test_the_package_carries_the_settings_of_the_design(self):
        settings = json.loads(self.data["print_designer_settings"])

        self.assertIsInstance(settings, dict)
        self.assertEqual(settings.get("currentDoc"), None)

    # ------------------------------------------------------------------
    # the identity of the template
    # ------------------------------------------------------------------

    def test_the_package_carries_no_identity_of_its_own(self):
        """The template must not ship the identity of the site that saved it.

        The checks are patterns, not the values of a client: the package
        must carry no e-mail address, no file of a site and no address of
        the internet.
        """
        serialized = json.dumps(self.data, ensure_ascii=False)

        self.assertEqual(EMAIL_PATTERN.findall(serialized), [])
        self.assertNotIn("/files/", serialized)
        self.assertEqual(URL_PATTERN.findall(serialized), [])

    def test_the_package_resolves_its_identity_at_print_time(self):
        """Every identity of the page must be a lookup at print time.

        The identity of the page is the name of the company, its address,
        its tax id, its phone number, its e-mail address, the name of the
        bank account, the bank, the branch, the number of the bank account
        and the contact person.  Each of them is read from the site while
        the page is printed.
        """
        expressions = _the_dynamic_expressions(self.data)

        for expression in expressions:
            self.assertTrue(
                "frappe.db.get_value" in expression or "doc.get(" in expression,
                f"the identity is not resolved at print time: {expression!r}",
            )

    def test_the_package_uses_the_dynamic_company_logo(self):
        """The logo of the page is the logo of the company of the Quotation."""
        images = []
        for key in ("print_designer_header", "print_designer_body", "print_designer_footer"):
            images.extend(_find_images(json.loads(self.data[key])))

        self.assertTrue(images)

        for image in images:
            binding = image.get("image") or {}
            self.assertTrue(image.get("isDynamic"))
            self.assertEqual(binding.get("doctype"), "Company")
            self.assertEqual(binding.get("fieldname"), "company_logo")
            self.assertEqual(binding.get("parentField"), "company")

            # No file of the site that saved the format travels with it.
            for key in ("value", "name", "file_name", "file_url", "modified"):
                self.assertFalse(binding.get(key), key)

    # ------------------------------------------------------------------
    # the address
    # ------------------------------------------------------------------

    def test_the_package_reads_no_address_field_that_does_not_exist(self):
        """The address of the page must not come from a field of the Company.

        The Company of this ERPNext carries an ``address_html`` field in its
        metadata, but the column does not exist in the table of the site.
        A lookup of that field is an error of the database, so the package
        must not name it.
        """
        self.assertFalse(frappe.db.has_column("Company", "address_html"))

        for key in DESIGN_PAYLOADS:
            payload = self.data[key]
            self.assertNotIn("address_html", payload, key)

    def test_the_address_comes_from_the_printed_quotation(self):
        """The address of the page is the address of the printed Quotation.

        ERPNext fills ``company_address_display`` while it validates the
        Quotation, and the display of an address carries the tags of a
        line break.  The page shows the address as text.
        """
        expressions = _the_dynamic_expressions(self.data)

        addresses = [
            expression for expression in expressions if "company_address_display" in expression
        ]

        self.assertEqual(len(addresses), 1, addresses)
        self.assertIn("doc.get(", addresses[0])
        self.assertIn("striptags", addresses[0])

    # ------------------------------------------------------------------
    # the bank details
    # ------------------------------------------------------------------

    def test_the_bank_details_come_from_the_bank_account_of_the_company(self):
        """The bank details come from the Bank Account of the Company.

        The default bank account of a Company is a link to an Account, not
        to a Bank Account.  The bridge to the Bank Account is the field
        ``account`` of the Bank Account, so the lookup of the bank details
        filters on the account of the Company.
        """
        expressions = _the_dynamic_expressions(self.data)

        lookups = [expression for expression in expressions if '"Bank Account"' in expression]
        self.assertTrue(lookups, "the package reads no bank details")

        for lookup in lookups:
            self.assertIn(
                'frappe.db.get_value("Company", doc.company, "default_bank_account")', lookup
            )
            self.assertIn('{"account": the_account}', lookup)

    def test_the_bank_details_are_not_read_from_the_account(self):
        """An Account carries no bank, so the package must not read one.

        The bank name, the branch and the number of the bank account are
        fields of the Bank Account, never of the Account that it is
        linked to.
        """
        expressions = _the_dynamic_expressions(self.data)

        for expression in expressions:
            self.assertNotIn('frappe.db.get_value("Account"', expression)

    # ------------------------------------------------------------------
    # the contact
    # ------------------------------------------------------------------

    def test_the_contact_is_displayed_with_its_full_name(self):
        """The contact of the page is displayed with its full name.

        The name of a Contact is the identifier of its link, and it carries
        the name of the company of the contact.  The full name of the
        contact is the name that a reader of the page expects.
        """
        expressions = _the_dynamic_expressions(self.data)

        contacts = [expression for expression in expressions if '"Contact"' in expression]
        self.assertEqual(len(contacts), 1, contacts)

        contact = contacts[0]
        self.assertIn('doc.get("company_contact_person")', contact)
        self.assertIn("full_name", contact)
        self.assertIn("name", contact)

        # The full name is the value of the page, the name of the link is
        # only the fallback for a contact that has no full name.
        self.assertLess(contact.index("full_name"), contact.index('get("name")'))

    # ------------------------------------------------------------------
    # the installer
    # ------------------------------------------------------------------

    def test_the_opaque_identifiers_are_no_fields_of_the_quotation(self):
        """The design names nodes that the database does not know.

        A static text of the design carries an identifier of its own.  It
        is not a field of the printed Quotation, and the installer must
        not treat it as one.
        """
        valid = get_valid_fieldnames("Quotation")
        self.assertIsNotNone(valid)
        assert valid is not None

        opaque = _the_opaque_identifiers(self.data, valid)

        self.assertTrue(opaque, "the design names no node of its own")

        for identifier in opaque:
            self.assertNotIn(identifier, valid)

    def test_the_package_is_not_deferred_by_the_installer(self):
        """The installer must not defer the package for a missing field.

        The names of the static texts of the design are not fields of the
        Quotation, and a design that names no field of the Quotation has
        no dependency that could be missing.
        """
        referenced = collect_referenced_fields(self.data)
        required = collect_required_amount_fields(self.data)

        missing = find_missing_dependencies("Quotation", referenced, required)

        self.assertEqual(missing, [])

    # ------------------------------------------------------------------
    # the manifest
    # ------------------------------------------------------------------

    def test_the_manifest_ships_no_static_asset(self):
        manifest = yaml.safe_load(ASSETS_PATH.read_text())

        self.assertEqual(manifest["kind"], "print_designer_template_assets")
        self.assertEqual(manifest["template_file"], "services_quotation.json")
        self.assertEqual(manifest["template_name"], TEMPLATE_NAME)

        self.assertEqual(manifest["assets"], [])
        self.assertEqual(manifest["missing_assets"], [])

        logos = [
            image
            for image in manifest["dynamic_images"]
            if image["doctype"] == "Company" and image["fieldname"] == "company_logo"
        ]
        self.assertEqual(len(logos), 1)

    def test_the_manifest_describes_a_site_neutral_template(self):
        """The manifest tells the reader what the template resolves.

        The identity of the page is read while the page is printed, so the
        manifest says so.
        """
        manifest = yaml.safe_load(ASSETS_PATH.read_text())
        changes = " ".join(manifest.get("portability_changes") or []).lower()

        self.assertIn("print time", changes)
        self.assertIn("company", changes)


class TestTheServicesQuotationRendering(FrappeTestCase):
    """The page of the services quotation, printed on a site with data."""

    def setUp(self):
        self.company = _a_company()
        self.account = _a_bank_account_of(self.company)
        self.bank = _a_bank()
        self.bank_account = _a_bank_account(self.account, self.bank)
        self.contact = _a_contact(self.company)
        self.address = _an_address(self.company)
        self.customer = _a_customer()
        self.item, self.item_created = _a_service_item(self.company)
        self.quotation: str | None = None

        self._the_company_before = {
            field: frappe.db.get_value("Company", self.company, field)
            for field in ("default_bank_account", "tax_id", "phone_no", "email")
        }

        _set_company_fields(
            self.company,
            {
                "default_bank_account": self.account,
                "tax_id": "PD-QT-TAX-1",
                "phone_no": "PD-QT-0002",
                "email": "pd-qt@example.test",
            },
        )

        self.format_installed_here = _install_the_template()

    def tearDown(self):
        _set_company_fields(self.company, self._the_company_before)

        if self.format_installed_here:
            frappe.delete_doc("Print Format", TEMPLATE_NAME, ignore_permissions=True, force=True)

        for doctype, name in (
            ("Quotation", getattr(self, "quotation", None)),
            ("Contact", getattr(self, "contact", None)),
            ("Address", getattr(self, "address", None)),
            ("Bank Account", getattr(self, "bank_account", None)),
            ("Bank", getattr(self, "bank", None)),
            ("Item", getattr(self, "item_created", None)),
        ):
            if name and frappe.db.exists(doctype, name):
                frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)

    # ------------------------------------------------------------------
    # the rendering
    # ------------------------------------------------------------------

    def test_the_page_shows_the_identity_of_the_printed_quotation(self):
        """The page shows the company of the printed Quotation.

        The name, the tax id, the phone number and the e-mail address of
        the page are read from the Company while the page is printed.
        """
        html = self._render()

        self.assertIn(self.company, html)
        self.assertIn("PD-QT-TAX-1", html)
        self.assertIn("PD-QT-0002", html)
        self.assertIn("pd-qt@example.test", html)

    def test_the_page_shows_the_address_of_the_printed_quotation(self):
        """The page shows the address of the printed Quotation as text."""
        quotation = self._quotation()
        html = self._render(quotation)

        self.assertIn("PD-QT Road 1", html)
        self.assertIn("Bangkok", html)

        # The display of an address carries the tags of a line break, the
        # page shows the address as text.
        self.assertNotIn("PD-QT Road 1<br>", html)

    def test_the_page_shows_the_bank_details_of_the_company(self):
        """The page shows the bank details of the default bank account."""
        html = self._render()

        self.assertIn("PD-QT Holder", html)
        self.assertIn("PD-QT-Bank", html)
        self.assertIn("PD-QT-BRANCH", html)
        self.assertIn("PD-QT-0001", html)

    def test_the_page_shows_the_full_name_of_the_contact(self):
        """The page shows the full name of the contact, not its link name."""
        quotation = self._quotation()
        html = self._render(quotation)

        self.assertIn("PD-QT Person", html)
        self.assertNotIn(self.contact, html)

    def test_the_page_shows_no_none(self):
        """The page must not show the text of a missing value.

        A lookup that finds nothing must leave the page blank.  A page
        that shows the word ``None`` shows a defect of the template.
        """
        html = self._render()

        self.assertNotIn("None", html)

    def test_the_page_shows_blanks_where_the_site_has_no_data(self):
        """A site without bank details and without a contact prints blanks."""
        frappe.db.set_value("Company", self.company, "default_bank_account", "")

        quotation = self._quotation()
        quotation.set("company_contact_person", None)
        quotation.set("company_address", None)
        quotation.set("company_address_display", None)

        html = self._render(quotation)

        self.assertNotIn("None", html)
        self.assertNotIn("PD-QT Holder", html)
        self.assertNotIn("PD-QT-0001", html)
        self.assertNotIn("PD-QT-BRANCH", html)

        # The page is still a page.
        self.assertGreater(len(html), 5000)

    # ------------------------------------------------------------------
    # the fixtures
    # ------------------------------------------------------------------

    def _quotation(self):
        """A Quotation that carries the fields the page reads."""
        if self.quotation:
            return frappe.get_doc("Quotation", self.quotation)

        quotation = frappe.get_doc(
            {
                "doctype": "Quotation",
                "company": self.company,
                "quotation_to": "Customer",
                "party_name": self.customer,
                "currency": frappe.db.get_value("Company", self.company, "default_currency"),
                "transaction_date": "2026-01-15",
                "valid_till": "2026-02-15",
                "company_address": self.address,
                "company_contact_person": self.contact,
                "items": [{"item_code": self.item, "qty": 1, "rate": 1000}],
            }
        )
        quotation.insert(ignore_permissions=True)
        self.quotation = str(quotation.name)

        return quotation

    def _render(self, quotation=None):
        """Print the page of the services quotation on this site."""
        if quotation is None:
            quotation = self._quotation()

        print_format = frappe.get_doc("Print Format", TEMPLATE_NAME)

        return _render(print_format, quotation)


# ----------------------------------------------------------------------
# the helpers of the package
# ----------------------------------------------------------------------


def _the_dynamic_expressions(data) -> list[str]:
    """The Jinja of the design that the renderer prints.

    A static text of the design carries the value that the page shows.  A
    value that is not static is read from the printed document itself.
    The static values that carry Jinja are the expressions of the page, the
    other static values are the labels of the page.  The same expression
    occurs in several payloads of the design, so every expression is
    returned once.
    """
    expressions: list[str] = []

    for key in DESIGN_PAYLOADS:
        payload = json.loads(data[key])
        for entry in _find_dynamic_entries(payload):
            value = entry.get("value")
            if not entry.get("is_static") or not isinstance(value, str):
                continue
            if "{{" not in value and "{%" not in value:
                continue
            if value not in expressions:
                expressions.append(value)

    return expressions


def _find_dynamic_entries(node) -> list[dict]:
    """The dynamic content entries of a design payload."""
    found = []
    if isinstance(node, dict):
        if node.get("type") == "text":
            found.extend(node.get("dynamicContent") or [])
        for value in node.values():
            found.extend(_find_dynamic_entries(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_dynamic_entries(item))
    return found


def _find_images(node) -> list[dict]:
    """The image elements of a design payload."""
    found = []
    if isinstance(node, dict):
        if node.get("type") == "image":
            found.append(node)
        for value in node.values():
            found.extend(_find_images(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_find_images(item))
    return found


def _the_opaque_identifiers(data, valid: set[str]) -> set[str]:
    """The names of the static texts that the database does not know."""
    identifiers = set()

    for key in DESIGN_PAYLOADS:
        payload = json.loads(data[key])
        for entry in _find_dynamic_entries(payload):
            fieldname = entry.get("fieldname")
            if not fieldname or not entry.get("is_static"):
                continue
            if fieldname in valid:
                continue
            identifiers.add(fieldname)

    return identifiers


# ----------------------------------------------------------------------
# the helpers of the site
# ----------------------------------------------------------------------


def _set_company_fields(company: str, values: dict[str, Any]) -> None:
    """Write the fields of a company one by one.

    ``frappe.db.set_value`` accepts a mapping at runtime, but the checked
    signature of the method names a single field.
    """
    for fieldname, value in values.items():
        frappe.db.set_value("Company", company, fieldname, value)


def _a_company() -> str:
    """The company of the page.

    The test uses the company of the ERPNext test records when the site
    has it, so that the accounts of the test belong to a company with a
    chart of accounts.
    """
    if frappe.db.exists("Company", "_Test Company"):
        return "_Test Company"

    companies = frappe.get_all("Company", pluck="name", limit=1)
    if not companies:
        raise AssertionError("the site has no company to print a quotation for")

    return companies[0]


def _a_bank_account_of(company: str) -> str:
    """An Account of the company that may carry a bank account.

    The bank account of a Bank Account must be a leaf of the type
    ``Bank`` of the company, and no other Bank Account may use it.
    """
    accounts = frappe.get_all(
        "Account",
        filters={"company": company, "account_type": "Bank", "is_group": 0},
        pluck="name",
    )

    used = set(
        frappe.get_all("Bank Account", filters={"account": ["in", accounts]}, pluck="account")
    )

    for account in accounts:
        if account not in used:
            return account

    raise AssertionError(f"the company {company} has no account that may carry a bank account")


def _a_bank() -> str:
    """A bank of the test."""
    name = "PD-QT-Bank"
    if frappe.db.exists("Bank", name):
        frappe.delete_doc("Bank", name, ignore_permissions=True, force=True)

    bank = frappe.get_doc(
        {
            "doctype": "Bank",
            "bank_name": name,
            "swift_number": "PDQTBANK",
        }
    )
    bank.insert(ignore_permissions=True)

    return str(bank.name)


def _a_bank_account(account: str, bank: str) -> str:
    """A bank account of the account of the company."""
    bank_account = frappe.get_doc(
        {
            "doctype": "Bank Account",
            "account": account,
            "company": frappe.get_value("Account", account, "company"),
            "account_name": "PD-QT Holder",
            "bank": bank,
            "branch_code": "PD-QT-BRANCH",
            "bank_account_no": "PD-QT-0001",
            "is_company_account": 1,
        }
    )
    bank_account.insert(ignore_permissions=True)

    return str(bank_account.name)


def _a_contact(company: str) -> str:
    """A contact of the company."""
    contact = frappe.get_doc(
        {
            "doctype": "Contact",
            "first_name": "PD-QT",
            "last_name": "Person",
            "links": [{"link_doctype": "Company", "link_name": company}],
        }
    )
    contact.insert(ignore_permissions=True)

    return str(contact.name)


def _an_address(company: str) -> str:
    """An address of the company."""
    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": "PD-QT Address",
            "address_type": "Billing",
            "address_line1": "PD-QT Road 1",
            "city": "Bangkok",
            "country": "Thailand",
            "links": [{"link_doctype": "Company", "link_name": company}],
        }
    )
    address.insert(ignore_permissions=True)

    return str(address.name)


def _a_customer() -> str:
    """A customer of the site.

    The test reuses a customer of the site: a customer that the test
    creates needs an identifier that the localisation of the site may
    require.
    """
    customers = frappe.get_all("Customer", filters={"disabled": 0}, pluck="name", limit=1)
    if not customers:
        raise AssertionError("the site has no customer to print a quotation for")

    return customers[0]


def _a_service_item(company: str) -> tuple[str, str | None]:
    """An item that the quotation offers.

    :returns: The name of the item and the name of the item when the
            test created it.
    """
    items = frappe.get_all(
        "Item",
        filters={"is_stock_item": 0, "is_sales_item": 1, "disabled": 0},
        pluck="name",
        limit=1,
    )
    if items:
        return str(items[0]), None

    item = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": "PD-QT Service Item",
            "item_name": "PD-QT Service Item",
            "item_group": "All Item Groups",
            "is_stock_item": 0,
            "is_sales_item": 1,
            "company": company,
        }
    )
    item.insert(ignore_permissions=True)

    # The caller removes the item of the test.
    return str(item.name), str(item.name)


def _install_the_template() -> bool:
    """Install the package of the services quotation on this site.

    :returns: True when the test installed the package, False when the
            site already had it.
    """
    if frappe.db.exists("Print Format", TEMPLATE_NAME):
        return False

    data = read_json(TEMPLATE_PATH)
    candidate, error = validate_template_document(data, "services_quotation.json")
    if error or candidate is None:
        raise AssertionError(f"the package is not a valid template: {error}")

    insert_template(candidate)

    return True


def _render(print_format, doc) -> str:
    """Render a Print Designer format the way the print view renders it."""
    from frappe.utils.jinja import get_jenv

    jenv = get_jenv()
    template = frappe.call(
        frappe.get_hooks("get_print_format_template")[-1],
        jenv=jenv,
        print_format=print_format,
    )

    return frappe.get_attr(frappe.get_hooks("pdf_body_html")[-1])(
        jenv=jenv,
        template=template,
        print_format=print_format,
        args={"doc": doc, "doc_data": json.dumps(doc.as_dict(), default=str)},
    )
