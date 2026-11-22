"""The migration of the Output VAT Undue ledger of Print Designer.

The ledger of the undue output VAT is the ``Output VAT Undue`` document.
A site that carries the rows of the old implementation of the ledger gets
the ledger of the current version with this patch.

What the patch does
-------------------

* the schema of the ledger is the schema of the JSON of the document.  The
  model synchronisation of Frappe applies it before this patch runs, so the
  patch verifies the columns of the table and reports the ones that are
  missing,
* the identity of a row of the ledger is the invoice it belongs to.  The
  document names itself after the field ``sales_invoice`` and the insert of
  the tracking sets the name of the row to the name of the invoice, so the
  primary key of the table is the uniqueness of the ledger.  The patch
  verifies the naming of the document and the primary key of the table,
* there is no unique index on the column ``sales_invoice``.  The rows of the
  old implementation carry a name of their own and a site can hold more than
  one row for an invoice - the old implementation wrote a row per submit
  without a uniqueness of its own.  A table like that cannot take a unique
  index without a rewrite of the history of the ledger, and the history is
  not rewritten here.  The patch reports the invoices that share more than
  one row and keeps the rows as they are,
* the patch creates nothing: no row of the ledger, no GL entry and no
  backfill of the history.  The rows of the old implementation carry no
  snapshot of the decision of the invoice; a backfill of the snapshot needs
  its own review.

Why there is no phase before the model synchronisation
------------------------------------------------------

A phase before the model synchronisation would only be needed when the
synchronisation itself can fail on the rows of the old implementation.
It cannot:

* the unique index of a field comes from the property ``unique`` of the
  field, and the field ``sales_invoice`` does not carry it.  The
  synchronisation creates no unique index on the column, so it cannot fail
  because of the rows that share an invoice,
* the primary key of the table is the name of the row.  The rows of the old
  implementation carry a name of their own and the history is not rewritten,
  so the synchronisation cannot fail because of them either.

The invoices that share more than one row are settled where they matter,
not in the schema: the writer of the ledger finds the row of the invoice
before it writes one, and the reader takes the oldest row of the invoice as
the row of the ledger.
"""

from typing import Any, cast

import frappe

#: The ledger of the undue output VAT.
LEDGER = "Output VAT Undue"

#: The table of the ledger.
TABLE = "tabOutput VAT Undue"

#: The field that carries the invoice a row of the ledger belongs to.
IDENTITY_FIELD = "sales_invoice"

#: The fields of the snapshot of the decision of the invoice.
SNAPSHOT_FIELDS = (
    "company",
    "treatment_reason",
    "registration_kind",
    "service_base_amount",
    "invoice_vat_amount",
    "recognized_vat_amount",
    "remaining_vat_amount",
)


def execute():
    """Bring the ledger of the site to the ledger of the current version.

    The patch runs after the model synchronisation of Frappe, so the schema
    of the ledger is already the schema of the JSON of the document.
    """
    if not frappe.db.table_exists(LEDGER):
        return

    missing = _missing_columns()
    shared = _shared_invoices()
    identity = _identity_is_ready()

    if missing:
        print(
            f"Print Designer: the ledger {LEDGER} misses the columns {', '.join(missing)}. "
            "The model synchronisation did not apply the schema of the document."
        )

    if not identity:
        print(
            f"Print Designer: the ledger {LEDGER} does not carry the identity of the "
            f"invoice yet. The document has to name itself after the field {IDENTITY_FIELD} "
            "and the table has to keep its primary key."
        )

    if shared:
        print(
            f"Print Designer: {len(shared)} invoice(s) of the ledger {LEDGER} carry more "
            "than one row. The rows of the old implementation are kept as they are; the "
            "ledger takes the oldest row of an invoice as the row of the invoice."
        )
        for invoice, count in shared:
            print(f"Print Designer: the invoice {invoice} carries {count} rows of the ledger.")

    _keep_the_migration_safe(shared)

    rows_without_snapshot = _rows_without_snapshot()
    if rows_without_snapshot:
        print(
            f"Print Designer: {rows_without_snapshot} row(s) of the ledger {LEDGER} carry no "
            "snapshot of the decision of the invoice. They are the rows of the old "
            "implementation; a backfill of the snapshot needs its own review."
        )


def _missing_columns():
    """The columns of the snapshot that the table of the ledger does not have."""
    columns = _columns()
    return [field for field in SNAPSHOT_FIELDS if field not in columns]


def _rows_without_snapshot():
    """The number of the rows that carry no snapshot of the decision."""
    columns = _columns()
    if "company" not in columns:
        return 0

    rows = cast(
        "list[dict[str, Any]]",
        frappe.db.sql(
            """
			select count(*) as total
			from `tabOutput VAT Undue`
			where ifnull(`company`, '') = ''
			""",
            as_dict=True,
        ),
    )

    return rows[0].get("total", 0) if rows else 0


def _shared_invoices():
    """The invoices that carry more than one row of the ledger."""
    columns = _columns()
    if IDENTITY_FIELD not in columns:
        return []

    rows = cast(
        "list[dict[str, Any]]",
        frappe.db.sql(
            f"""
			select `{IDENTITY_FIELD}` as invoice, count(*) as total
			from `tabOutput VAT Undue`
			where ifnull(`{IDENTITY_FIELD}`, '') != ''
			group by `{IDENTITY_FIELD}`
			having count(*) > 1
			order by `{IDENTITY_FIELD}`
			""",
            as_dict=True,
        ),
    )

    return [(row.get("invoice"), row.get("total")) for row in rows]


def _identity_is_ready():
    """True when the ledger carries the identity of the invoice.

    The identity is the name of the row: the document names itself after
    the field of the invoice and the primary key of the table refuses a
    second row with that name.
    """
    autoname = frappe.db.get_value("DocType", LEDGER, "autoname")
    if autoname != f"field:{IDENTITY_FIELD}":
        return False

    return _has_primary_key()


def _keep_the_migration_safe(shared):
    """Keep a later model synchronisation from failing on the ledger.

    A site that edits the document in the desk marks the field of the
    invoice as unique - that is what Frappe does with a document that names
    itself after a field.  A table that holds more than one row for an
    invoice cannot take that unique index, and the model synchronisation
    would fail on it.  The flag goes back to zero and the rows stay as they
    are.
    """
    if not shared:
        return

    field = str(
        frappe.db.get_value(
            "DocField",
            {"parent": LEDGER, "fieldname": IDENTITY_FIELD},
            "name",
        )
        or ""
    )
    if not field:
        return

    if not frappe.db.get_value("DocField", field, "unique"):
        return

    frappe.db.set_value("DocField", field, "unique", 0)
    print(
        f"Print Designer: the field {IDENTITY_FIELD} of the ledger {LEDGER} is marked as "
        "unique no more. The rows of the old implementation share an invoice and the "
        "unique index cannot be built on them."
    )


def _columns():
    """The columns of the table of the ledger."""
    try:
        return set(frappe.db.get_table_columns(LEDGER))
    except Exception:
        return set()


def _has_primary_key():
    """True when the table of the ledger keeps its primary key on the name."""
    for index in _indexes():
        if index["unique"] and [column.lower() for column in index["columns"]] == ["name"]:
            return True

    return False


def _indexes():
    """The indexes of the table of the ledger, in a shape that is neutral."""
    if frappe.db.db_type == "postgres":
        return _postgres_indexes()

    return _mariadb_indexes()


def _mariadb_indexes():
    """The indexes of the table of the ledger of a MariaDB site."""
    rows = cast(
        "list[dict[str, Any]]",
        frappe.db.sql(f"show index from `{TABLE}`", as_dict=True),
    )

    indexes: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("Key_name") or "")
        index = indexes.setdefault(
            name,
            {"name": name, "unique": not row.get("Non_unique"), "columns": []},
        )
        index["columns"].append(row.get("Column_name"))

    return list(indexes.values())


def _postgres_indexes():
    """The indexes of the table of the ledger of a PostgreSQL site."""
    rows = cast(
        "list[dict[str, Any]]",
        frappe.db.sql(
            """
			select indexname, indexdef
			from pg_indexes
			where tablename = %s
			""",
            (TABLE,),
            as_dict=True,
        ),
    )

    indexes = []
    for row in rows:
        definition = str(row.get("indexdef") or "")
        indexes.append(
            {
                "name": row.get("indexname"),
                "unique": "UNIQUE" in definition.upper(),
                "columns": _columns_of_definition(definition),
            }
        )

    return indexes


def _columns_of_definition(definition):
    """The columns of an index definition of PostgreSQL."""
    start = definition.find("(")
    end = definition.rfind(")")
    if start == -1 or end == -1:
        return []

    columns = []
    for part in definition[start + 1 : end].split(","):
        part = part.strip()
        if not part:
            continue
        columns.append(part.split()[0].strip('"'))

    return columns
