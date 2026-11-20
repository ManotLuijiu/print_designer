"""Missing-only installer for the Print Designer default templates.

Print Designer ships Print Format templates under
``print_designer/default_templates/``.  The folders below that root are
**categories**, not Frappe apps: ``erpnext/``, ``print_designer/`` and
``asean_business_suite/`` are plain folders.  No folder name implies that an
app with that name has to be installed on the site - the only real
dependencies of a template are the target DocType and the document fields its
saved design refers to.

This module installs every template that is **missing** on the site.  It
never updates or replaces a format that already exists, so a format a user
customised (including its thumbnail) stays byte-for-byte unchanged.

Entry points
------------
``install_missing_default_formats()``
        Missing-only installer.  Used as ``after_install`` hook, as an
        administrative backfill and as a read-only dry run.
``after_app_install(app_name)``
        Retry hook.  Runs after another app was installed and retries only the
        templates whose target DocType belongs to that app.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import frappe

from print_designer.utils.number_to_words_fields import LEGACY_AMOUNT_FIELDS

TEMPLATES_FOLDER = "default_templates"
PREVIEW_SUFFIX = "-preview.json"
FIXTURE_RELATIVE_PATH = ("fixtures", "print_format.json")

# Blobs of the saved design that may refer to document fields.
DESIGN_BLOBS = (
    "print_designer_body",
    "print_designer_header",
    "print_designer_footer",
    "print_designer_after_table",
    "print_designer_print_format",
    "print_designer_settings",
)

STATUS_IMPORTED = "imported"
STATUS_EXISTING = "existing"
STATUS_DEFERRED = "deferred"
STATUS_INVALID = "invalid"
STATUS_FAILED = "failed"

# "field", "parentField", "fieldname", "source_field" and "target_field" are
# the keys the designer uses to point at a document field.
FIELD_REFERENCE_PATTERN = re.compile(
    r'"(?:field|parentField|fieldname|source_field|target_field)"\s*:\s*"([^"]*)"'
)
# Keys the designer uses to point at a document field.
REFERENCE_KEYS = frozenset({"field", "parentField", "fieldname", "source_field", "target_field"})
# Custom fields of Print Designer and of the Thai business suite.
CUSTOM_FIELD_PREFIX = "pd_custom_"


def get_templates_root(app: str = "print_designer") -> Path:
    """Absolute path of the default templates folder of ``app``."""
    return Path(frappe.get_app_path(app)) / TEMPLATES_FOLDER


def discover_template_files(app: str = "print_designer") -> list[tuple[str, Path]]:
    """Return ``[(relative_path, absolute_path)]`` of every candidate template.

    The relative path is used for a stable, sorted discovery order so the
    result never depends on the filesystem iteration order.  Preview metadata
    (``*-preview.json``) is not a Print Format and is skipped.
    """
    root = get_templates_root(app)
    if not root.exists():
        return []

    files = []
    for path in root.rglob("*.json"):
        if path.name.endswith(PREVIEW_SUFFIX):
            continue
        files.append((path.relative_to(root).as_posix(), path))

    return sorted(files, key=lambda item: item[0])


def read_json(path: Path):
    """Read a JSON file and raise a readable error for a broken file."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as error:
        raise OSError(f"could not read '{path}': {error}") from error
    except ValueError as error:
        raise ValueError(f"'{path}' is not valid JSON: {error}") from error


def validate_template_document(data, relative_path: str) -> tuple[dict | None, str | None]:
    """Validate a parsed template file.

    Returns ``(candidate, error)``.  ``candidate`` is ``None`` when the file
    cannot be used as a Print Format template.
    """
    if not isinstance(data, dict):
        return (
            None,
            f"unsupported_payload: expected a Print Format document, got {type(data).__name__}",
        )

    doctype = data.get("doctype")
    if doctype != "Print Format":
        return None, f"unsupported_payload: doctype '{doctype}' is not 'Print Format'"

    name = str(data.get("name") or "").strip()
    if not name:
        return None, "missing_name: the Print Format has no name"

    doc_type = str(data.get("doc_type") or "").strip()
    if not doc_type:
        return None, "missing_doc_type: the Print Format has no doc_type"

    return {"name": name, "doc_type": doc_type, "data": data, "file": relative_path}, None


def get_fixture_print_format_names(app: str = "print_designer") -> set[str]:
    """Names of the Print Formats that ``fixtures/print_format.json`` manages."""
    path = Path(frappe.get_app_path(app)).joinpath(*FIXTURE_RELATIVE_PATH)
    if not path.exists():
        return set()

    try:
        rows = read_json(path)
    except Exception:
        return set()

    names = set()
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and row.get("doctype") == "Print Format" and row.get("name"):
                names.add(row["name"])
    return names


def collect_referenced_fields(data: dict) -> set[str]:
    """Document fields the saved design of a template refers to.

    A dynamic image binding points at a field of another doctype
    (``Company.company_logo``); only its ``parentField`` belongs to the
    document that renders the template.
    """
    references: set[str] = set()

    for key in DESIGN_BLOBS:
        blob = data.get(key)
        if not blob:
            continue

        payload = blob
        if isinstance(blob, str):
            try:
                payload = json.loads(blob)
            except ValueError:
                # Not a JSON payload - fall back to a plain text scan.
                references |= _scan_text_references(blob)
                continue

        _walk_references(payload, references)

    return references


def _scan_text_references(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in FIELD_REFERENCE_PATTERN.finditer(text)
        if match.group(1).strip()
    }


def _walk_references(node, references: set[str], skip_fieldname: bool = False) -> None:
    """Collect the field references of a parsed design payload."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in REFERENCE_KEYS and isinstance(value, str) and value.strip():
                if not (skip_fieldname and key == "fieldname"):
                    references.add(value.strip())
            if key == "image" and isinstance(value, dict):
                # The image binding points at a field of the linked doctype.
                _walk_references(value, references, skip_fieldname=True)
            else:
                _walk_references(value, references)
    elif isinstance(node, list):
        for item in node:
            _walk_references(item, references)


def collect_required_amount_fields(data: dict) -> set[str]:
    """Source and target fields of the configured amount-in-words pairs."""
    required: set[str] = set()

    for key in DESIGN_BLOBS:
        blob = data.get(key)
        if not blob:
            continue

        payload = blob
        if isinstance(blob, str):
            try:
                payload = json.loads(blob)
            except ValueError:
                continue

        if not isinstance(payload, dict):
            continue

        pairs = payload.get("numberToWordsFieldPairs")
        if not isinstance(pairs, list):
            continue

        for pair in pairs:
            if not isinstance(pair, dict):
                continue
            for field_key in ("source_field", "target_field"):
                value = pair.get(field_key)
                if isinstance(value, str) and value.strip():
                    required.add(value.strip())

    return required


def get_valid_fieldnames(doc_type: str, depth: int = 2) -> set[str] | None:
    """All fieldnames of ``doc_type`` and of its child tables.

    Returns ``None`` when the DocType does not exist on this site.
    """
    try:
        meta = frappe.get_meta(doc_type)
    except Exception:
        return None

    names: set[str] = set()
    for df in meta.fields:
        if df.fieldname:
            names.add(df.fieldname)
        if df.fieldtype == "Table" and depth > 0 and df.options:
            child_names = get_valid_fieldnames(df.options, depth=depth - 1)
            if child_names:
                names |= child_names

    return names


def find_missing_dependencies(
    doc_type: str,
    referenced: set[str],
    required: set[str] | None = None,
) -> list[str]:
    """Fields of the saved design that do not exist on the target DocType.

    Only the custom fields of the design and the fields of its configured
    amount-in-words pairs are required.  A standard field that an ERPNext
    version does not ship is not a reason to defer a template - the column
    simply stays empty.

    Legacy amount bindings are resolved through
    ``print_designer.utils.number_to_words_fields.LEGACY_AMOUNT_FIELDS``: a
    design that still names ``net_total_after_wht`` is accepted when the
    replacement ``pd_custom_net_total_after_wht`` exists.  Obsolete fields are
    never recreated.
    """
    valid = get_valid_fieldnames(doc_type)
    if valid is None:
        return []

    candidates = set(required or set())
    candidates |= {name for name in referenced if name.startswith(CUSTOM_FIELD_PREFIX)}

    missing = []
    for name in sorted(candidates):
        if name in valid:
            continue
        alias = LEGACY_AMOUNT_FIELDS.get(name)
        if alias and alias in valid:
            continue
        missing.append(name)

    return missing


def get_supported_pdf_generators() -> set[str]:
    """PDF generators the Print Format doctype offers on this site."""
    try:
        meta = frappe.get_meta("Print Format")
    except Exception:
        return set()

    df = meta.get_field("pdf_generator")
    if not df or not df.options:
        return set()

    return {line.strip() for line in df.options.split("\n") if line.strip()}


def get_doc_type_app(doc_type: str) -> str | None:
    """App that owns ``doc_type`` (``None`` when the DocType is unknown)."""
    try:
        return frappe.get_doctype_app(doc_type)
    except Exception:
        return None


def make_entry(
    status: str,
    file: str,
    name: str | None = None,
    doc_type: str | None = None,
    reason: str | None = None,
    **extra,
) -> dict:
    entry = {
        "status": status,
        "file": file,
        "name": name,
        "doc_type": doc_type,
        "reason": reason,
    }
    entry.update(extra)
    return entry


def new_results(dry_run: bool = False) -> dict:
    return {
        "dry_run": bool(dry_run),
        "scanned": 0,
        "imported": [],
        "existing": [],
        "deferred": [],
        "invalid": [],
        "failed": [],
        "pending": [],
        "conflicts": [],
    }


def summarize(results: dict) -> dict:
    return {
        "scanned": results["scanned"],
        "imported": len(results["imported"]),
        "existing": len(results["existing"]),
        "deferred": len(results["deferred"]),
        "invalid": len(results["invalid"]),
        "failed": len(results["failed"]),
        "pending": len(results["pending"]),
        "conflicts": len(results["conflicts"]),
    }


def insert_template(candidate: dict) -> None:
    """Insert a template that is known to be missing.

    The insert runs with ``in_import`` so that the Print Format validation
    side effects (exporting a file into the app folder, refusing to touch a
    standard format) do not fire.  The caller owns the transaction.
    """
    data = dict(candidate["data"])

    previous_in_import = frappe.flags.in_import
    frappe.flags.in_import = True
    try:
        doc = frappe.get_doc(data)
        doc.flags.ignore_validate = True
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory = True
        doc.insert()
    finally:
        frappe.flags.in_import = previous_in_import


def install_missing_default_formats(
    dry_run: bool = False,
    app: str = "print_designer",
    only_app: str | None = None,
) -> dict:
    """Install every default template that is missing on this site.

    :param dry_run: when True nothing is inserted, no file is copied and no
            setting is changed.  The candidates are listed in ``pending``.
    :param app: the app that ships the templates.
    :param only_app: restrict the run to the templates whose target DocType
            belongs to this app (used by the ``after_app_install`` retry hook).

    :returns: a structured result with the buckets ``imported``, ``existing``,
            ``deferred``, ``invalid``, ``failed``, ``pending`` and ``conflicts``.
    """
    results = new_results(dry_run=dry_run)
    fixture_names = get_fixture_print_format_names(app)

    candidates: list[dict] = []
    for relative_path, path in discover_template_files(app):
        results["scanned"] += 1

        try:
            data = read_json(path)
        except Exception as error:
            results["invalid"].append(
                make_entry(STATUS_INVALID, relative_path, reason=f"invalid_json: {error}")
            )
            continue

        candidate, error = validate_template_document(data, relative_path)
        if error or candidate is None:
            results["invalid"].append(make_entry(STATUS_INVALID, relative_path, reason=error))
            continue

        candidates.append(candidate)

    # Deterministic winner for duplicated names: the first file in sorted
    # relative path order.  Every other file with that name is invalid.
    by_name: dict[str, list[dict]] = {}
    for candidate in candidates:
        by_name.setdefault(candidate["name"], []).append(candidate)

    winners: list[dict] = []
    for name in sorted(by_name):
        group = by_name[name]
        winner = group[0]
        if len(group) > 1:
            results["conflicts"].append(
                {
                    "name": name,
                    "winner": winner["file"],
                    "files": [item["file"] for item in group],
                }
            )
            for loser in group[1:]:
                results["invalid"].append(
                    make_entry(
                        STATUS_INVALID,
                        loser["file"],
                        name=name,
                        doc_type=loser["doc_type"],
                        reason=f"duplicate_name: '{name}' is already defined in '{winner['file']}'",
                    )
                )
        winners.append(winner)

    supported_generators = get_supported_pdf_generators()

    for candidate in winners:
        name = candidate["name"]
        doc_type = candidate["doc_type"]
        relative_path = candidate["file"]

        if only_app and get_doc_type_app(doc_type) != only_app:
            continue

        if frappe.db.exists("Print Format", name):
            results["existing"].append(
                make_entry(
                    STATUS_EXISTING,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason="already_installed",
                )
            )
            continue

        if name in fixture_names:
            results["invalid"].append(
                make_entry(
                    STATUS_INVALID,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason="fixture_conflict: the name is managed by fixtures/print_format.json",
                )
            )
            continue

        if not frappe.db.exists("DocType", doc_type):
            results["deferred"].append(
                make_entry(
                    STATUS_DEFERRED,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason=f"missing_doctype: '{doc_type}' is not installed on this site",
                )
            )
            continue

        generator = candidate["data"].get("pdf_generator")
        if generator and supported_generators and generator not in supported_generators:
            results["deferred"].append(
                make_entry(
                    STATUS_DEFERRED,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason=f"renderer_unsupported: '{generator}' is not offered by this site",
                )
            )
            continue

        missing_fields = find_missing_dependencies(
            doc_type,
            collect_referenced_fields(candidate["data"]),
            collect_required_amount_fields(candidate["data"]),
        )
        if missing_fields:
            results["deferred"].append(
                make_entry(
                    STATUS_DEFERRED,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason="missing_fields: the design refers to fields that do not exist yet",
                    missing_fields=missing_fields,
                )
            )
            continue

        if dry_run:
            results["pending"].append(
                make_entry(
                    STATUS_IMPORTED,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason="dry_run: nothing was inserted",
                )
            )
            continue

        savepoint = f"pd_default_template_{frappe.scrub(name)}"
        try:
            frappe.db.savepoint(savepoint)
            insert_template(candidate)
            frappe.db.release_savepoint(savepoint)
        except frappe.exceptions.DuplicateEntryError:
            frappe.db.rollback(save_point=savepoint)
            results["existing"].append(
                make_entry(
                    STATUS_EXISTING,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason="already_installed",
                )
            )
        except Exception as error:
            frappe.db.rollback(save_point=savepoint)
            results["failed"].append(
                make_entry(
                    STATUS_FAILED,
                    relative_path,
                    name=name,
                    doc_type=doc_type,
                    reason=f"{type(error).__name__}: {error}",
                )
            )
        else:
            results["imported"].append(
                make_entry(
                    STATUS_IMPORTED, relative_path, name=name, doc_type=doc_type, reason="installed"
                )
            )

    results["summary"] = summarize(results)
    return results


def after_app_install(app_name: str) -> None:
    """Retry the templates that were deferred by a missing dependency.

    Frappe calls this hook with the name of the app that was just installed.
    Only the templates whose target DocType belongs to that app are retried,
    so installing an unrelated app never touches the other templates.
    """
    try:
        results = install_missing_default_formats(only_app=app_name)
    except Exception:
        frappe.log_error(title="Print Designer default template retry failed")
        return

    summary = results.get("summary", {})
    if summary.get("imported") or summary.get("failed"):
        frappe.logger().info(
            "Print Designer default templates after installing {0}: {1}".format(app_name, summary)
        )
