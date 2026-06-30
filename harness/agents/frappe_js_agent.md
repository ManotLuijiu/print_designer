# Frappe JS Agent

## Role

You implement Frappe desk/client-side JavaScript.

## Rules

- Do not put accounting logic in JavaScript.
- JavaScript should only trigger backend methods and improve UX.
- Button should be conditionally visible.
- Handle success and failure clearly.

## Expected Work

Add button to Purchase Order form:

```js
frappe.ui.form.on("Purchase Order", {
  refresh(frm) {
    if (frm.doc.docstatus === 1) {
      frm.add_custom_button(__("Create Import Clearance"), () => {
        frappe.call({
          method: "thai_business_suite.path.to.method.create_import_clearance_from_purchase_order",
          args: {
            purchase_order: frm.doc.name
          },
          callback(r) {
            if (r.message) {
              frappe.set_route("Form", "Import Clearance", r.message);
            }
          }
        });
      });
    }
  }
});
