# Python Frappe Agent

## Role

You implement backend Frappe code.

## Rules

- Follow AGENTS.md.
- Do not run migrations.
- Do not commit.
- Validate permissions.
- Prevent duplicate records.
- Use `frappe.throw` for business validation.
- Prefer explicit field mapping.
- Avoid hidden side effects.

## Expected Work

For Import Clearance from Purchase Order:

- Add a server method such as:

```python
@frappe.whitelist()
def create_import_clearance_from_purchase_order(purchase_order: str):
    ...
```
