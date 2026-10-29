"""Assign a WHT income type to the Items of the ``Services`` Item Group.

A Sales Order / Quotation / Sales Invoice that carries an item of the
``Services`` Item Group is subject to Thai withholding tax (see
``print_designer.custom.service_item_wht``).  The category that is withheld is
taken from ``Item.pd_custom_wht_income_type`` (see
``print_designer.custom.item_wht_config``), so every service item needs that
master data.  An item without it produces a document whose withholding tax
flag is switched on but whose income type, rate and amount stay empty.

This command fills that gap for the items that have no income type yet.

Rules
-----
* An existing income type is **never** overwritten, so a deliberate choice
  (or a value maintained by another application) is always kept.
* The target category is validated before anything is written.  When no
  category is given on the command line, it is derived from the items of the
  group that already carry one, so nothing site specific is hardcoded.  When
  those items disagree the command stops and asks for an explicit category.
* The command is a **dry run by default**.  ``--apply`` is required to write.
* Only the ``Item`` master is touched.  No document, ledger or account is
  affected.

The dry run prints the plan and writes nothing.
"""

import click
import frappe
from frappe.commands import get_site, pass_context

from print_designer.custom.item_wht_config import ITEM_INCOME_TYPE_FIELD
from print_designer.custom.service_item_wht import SERVICE_ITEM_GROUP

#: The doctype that stores the withholding tax categories.
CATEGORY_DOCTYPE = "Tax Withholding Category"


def get_service_items(item_group=SERVICE_ITEM_GROUP):
    """Return the Items of ``item_group`` with their WHT income type.

    The income type field is only selected when it is installed on the site,
    because selecting a missing column raises a database error.
    """
    fields = ["name", "item_code", "item_name", "item_group"]
    if is_item_income_type_installed():
        fields.append(ITEM_INCOME_TYPE_FIELD)

    return frappe.get_all(
        "Item",
        filters={"item_group": item_group},
        fields=fields,
        limit=0,
    )


def is_item_income_type_installed():
    """Return True when the Item carries the WHT income type field."""
    try:
        return bool(frappe.get_meta("Item").has_field(ITEM_INCOME_TYPE_FIELD))
    except Exception:
        return False


def build_plan(items, income_type_field=ITEM_INCOME_TYPE_FIELD):
    """Return the items that have no income type yet.

    :param items: iterable of mappings holding the income type field.
    """
    plan = []
    for item in items:
        value = item.get(income_type_field)
        if not (value or "").strip():
            plan.append(item)
    return plan


def resolve_income_type(items, requested=None, income_type_field=ITEM_INCOME_TYPE_FIELD):
    """Return the category to assign.

    :param requested: the category given by the caller, if any.
    :param items: the items of the group, used to derive the category when the
            caller did not request one.

    An explicit request always wins.  Otherwise the category that the items of
    the group already use is taken, but only when all of them agree.
    """
    if requested:
        return requested

    used = {
        (item.get(income_type_field) or "").strip()
        for item in items
        if (item.get(income_type_field) or "").strip()
    }
    if len(used) == 1:
        return used.pop()
    if not used:
        raise ValueError(
            "No WHT income type is configured for the items of this group. "
            "Pass the target category explicitly."
        )
    raise ValueError(
        "The items of this group use different WHT income types "
        f"({', '.join(sorted(used))}). Pass the target category explicitly."
    )


def set_service_item_wht_income_type(
    income_type=None,
    item_group=SERVICE_ITEM_GROUP,
    apply=False,
):
    """Assign the WHT income type to the service items that have none.

    :param income_type: the ``Tax Withholding Category`` to assign.  Derived
            from the group when omitted.
    :param item_group: the item group whose items are processed.
    :param apply: when False (the default) nothing is written.
    """
    if not is_item_income_type_installed():
        raise ValueError(f"The Item field {ITEM_INCOME_TYPE_FIELD} is not installed on this site.")

    items = get_service_items(item_group)
    if not items:
        click.echo(f"No items found in the item group '{item_group}'.")
        return {"updated": [], "planned": [], "income_type": income_type}

    target = resolve_income_type(items, requested=income_type)

    if not frappe.db.exists(CATEGORY_DOCTYPE, target):
        raise ValueError(f"The withholding tax category '{target}' does not exist on this site.")

    plan = build_plan(items)

    click.echo(f"Item group        : {item_group}")
    click.echo(f"Income type       : {target}")
    click.echo(f"Items in group    : {len(items)}")
    click.echo(f"Already configured: {len(items) - len(plan)}")
    click.echo(f"Missing income type: {len(plan)}")

    if not plan:
        click.echo("Nothing to do.")
        return {"updated": [], "planned": [], "income_type": target}

    click.echo("")
    for item in plan:
        click.echo(
            f"  - {item.item_code} | {item.item_name} | group: {item.item_group} "
            f"| income type: (empty) -> {target}"
        )

    if not apply:
        click.echo("")
        click.echo("Dry run: nothing was written. Re-run with --apply to write the changes.")
        return {"updated": [], "planned": plan, "income_type": target}

    updated = []
    for item in plan:
        frappe.db.set_value("Item", item.name, ITEM_INCOME_TYPE_FIELD, target)
        updated.append(item.name)

    frappe.db.commit()

    click.echo("")
    click.echo(f"Updated {len(updated)} item(s): {', '.join(updated)}")
    return {"updated": updated, "planned": plan, "income_type": target}


@click.command("set-service-item-wht-income-type")
@click.option("--site", help="Site name")
@click.option(
    "--income-type",
    help=(
        "The Tax Withholding Category to assign. Derived from the items of the group when omitted."
    ),
)
@click.option(
    "--item-group",
    default=SERVICE_ITEM_GROUP,
    show_default=True,
    help="The item group whose items receive the income type.",
)
@click.option("--apply", is_flag=True, help="Write the changes (default: dry run).")
@pass_context
def set_service_item_wht_income_type_cmd(
    context, site=None, income_type=None, item_group=None, apply=False
):
    """Assign a WHT income type to the service items that have none."""
    site = site or get_site(context)

    try:
        with frappe.init_site(site):
            frappe.connect()
            set_service_item_wht_income_type(
                income_type=income_type,
                item_group=item_group or SERVICE_ITEM_GROUP,
                apply=apply,
            )
    except ValueError as error:
        raise click.ClickException(str(error)) from error
