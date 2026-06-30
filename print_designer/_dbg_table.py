import json

import frappe

pf = frappe.get_doc("Print Format", "Receipt")
pd = json.loads(pf.print_designer_print_format or "{}")


def find(o):
    if isinstance(o, dict):
        if o.get("type") == "table":
            with open("/tmp/dbg.log", "w") as f:
                f.write("table id={}\n".format(o.get("id")))
                f.write(
                    "style: {}\n".format(json.dumps(o.get("style"), indent=2, default=str)[:800])
                )
                f.write(
                    "headerStyle: {}\n".format(
                        json.dumps(o.get("headerStyle"), indent=2, default=str)[:600]
                    )
                )
                f.write(
                    "altStyle: {}\n".format(
                        json.dumps(o.get("altStyle"), indent=2, default=str)[:400]
                    )
                )
        for v in o.values():
            find(v)
    elif isinstance(o, list):
        for v in o:
            find(v)


find(pd)
