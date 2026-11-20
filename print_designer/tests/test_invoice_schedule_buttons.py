"""Browser UI checks only: stub RPCs so no order or invoice is saved."""

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

SCRIPT = Path(__file__).parents[1] / "public/js/invoice_schedule/sales_order_invoice_schedule.js"
JQUERY = Path("/home/frappe/frappe-bench/apps/frappe/node_modules/jquery/dist/jquery.min.js")


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/home/frappe/frappe-bench/chromium/chrome-linux/headless_shell",
        )
        yield browser
        browser.close()


def setup(page):
    page.set_content("""<div id="enable"><span class="info-trigger">?</span>
      <div class="sidebar-card-description">Old switch help</div><p class="help-box"></p></div>
      <div id="schedule"><p class="grid-description">Old visible table description</p>
      <div class="grid-footer"><div class="grid-buttons"><button class="grid-add-row">Add row</button>
      <button class="milestone-button">Add Milestone</button>
      <button class="milestone-button">Add Milestone</button></div></div></div>""")
    page.add_script_tag(path=str(JQUERY))
    page.evaluate("""() => {
      window.__ = text => text;
      window.flt = value => Number(value || 0);
      window.rpc = [];
      window.handlers = {};
      window.navButtons = [];
      window.frappe = {
        ui: {form: {on: (type, events) => {handlers[type] = events;}},
          SidebarCard: class {
            constructor(options) {
              options.parent.html('<div class="sidebar-card-description"></div>');
              options.parent.find('.sidebar-card-description').text(options.message);
            }
            hide() {} toggle() {}
          }},
        meta: {get_docfield: (type, name) => ({
          label: name === 'pd_custom_add_invoice_schedule_row' ? 'Add Milestone' : 'Copy from Payment Schedule',
          description: 'Legacy append-row help'
        })},
        utils: {icon: () => '<span class="milestone-help-trigger">?</span>'},
        call: options => {rpc.push({method:options.method,args:options.args});},
      };
      const grid = {wrapper:$('#schedule'),df:{description:'Old visible table description'},
        docfields:[{fieldname:'payment_term',fieldtype:'Data'}],fieldinfo:{},
        get_field(name) {return this.fieldinfo[name] ||= {};},
        update_docfield_property(name,property,value) {this.docfields.find(df=>df.fieldname===name)[property]=value;},
        set_grid_description() {this.wrapper.find('.grid-description').text(this.df.description).toggle(Boolean(this.df.description));}};
      window.frm = {doctype:'Sales Order',doc:{name:'TEST-SO',docstatus:0,pd_custom_enable_invoice_schedule:1},
        is_new:()=>false,is_dirty:()=>false,custom_buttons:{},
        cscript:{calls:[],payment_term(doc,cdt,cdn) {this.calls.push({cdt,cdn}); return 'core-result';}},
        add_custom_button:(label,fn,group)=>{window.navButtons.push({label,group});frm.custom_buttons[label]=true;},
        remove_custom_button:(label,group)=>{window.navButtons=window.navButtons.filter(b=>!(b.label===label&&b.group===group));
          delete frm.custom_buttons[label];},
        fields_dict:{pd_custom_invoice_schedule:{df:grid.df,grid},
          pd_custom_enable_invoice_schedule:{df:{},$wrapper:$('#enable'),
            show_description_on_click() {$('#enable').append('<span class="info-trigger">?</span>');}}}};
    }""")
    page.add_script_tag(path=str(SCRIPT))
    page.evaluate("handlers['Sales Order'].refresh(frm)")


def test_refresh_replaces_duplicate_legacy_buttons_with_one_generate_action(browser):
    page = browser.new_page()
    try:
        setup(page)
        page.evaluate("handlers['Sales Order'].refresh(frm); handlers['Sales Order'].refresh(frm)")
        buttons = page.locator(".grid-buttons button").all_text_contents()
        assert buttons.count("Generate Invoice") == 1
        assert buttons.count("Copy from Payment Schedule") == 1
        assert "Add Milestone" not in buttons
        assert buttons.count("Add row") == 1
        assert page.locator(".milestone-help-trigger").count() == 2
    finally:
        page.close()


def test_generate_button_calls_generation_preview_not_append_row(browser):
    page = browser.new_page()
    try:
        setup(page)
        page.get_by_role("button", name="Generate Invoice", exact=True).click()
        assert page.evaluate("rpc") == [
            {
                "method": "print_designer.custom.invoice_schedule.generate_milestone_invoices",
                "args": {"sales_order": "TEST-SO", "preview": 1},
            }
        ]
    finally:
        page.close()


def test_schedule_description_lives_only_in_the_switch_help_card(browser):
    page = browser.new_page()
    try:
        setup(page)
        page.evaluate("handlers['Sales Order'].refresh(frm)")
        assert page.locator("#enable .info-trigger").count() == 1
        assert not page.locator(".grid-description").is_visible()
        help_text = page.locator("#enable .sidebar-card-description").inner_text()
        assert "split the plan into as many invoices as you need" in help_text
        assert "before submitting the Sales Order" in help_text
        generation_help = page.locator(
            ".grid-buttons .info-card .sidebar-card-description"
        ).first.inner_text()
        assert "Create draft Sales Invoices" in generation_help
        assert "Legacy append-row help" not in generation_help
    finally:
        page.close()


def test_navbar_generate_action_only_for_a_draft_with_the_schedule_enabled(browser):
    page = browser.new_page()
    try:
        setup(page)
        assert page.evaluate("window.navButtons") == [
            {"label": "Generate Invoice", "group": "Milestones"}
        ]

        # a submitted order has frozen milestones, the action is withdrawn
        page.evaluate("frm.doc.docstatus = 1; handlers['Sales Order'].refresh(frm)")
        assert page.evaluate("window.navButtons") == []

        # a draft without the schedule does not get the action either
        page.evaluate(
            "frm.doc.docstatus = 0; frm.doc.pd_custom_enable_invoice_schedule = 0; handlers['Sales Order'].refresh(frm)"
        )
        assert page.evaluate("window.navButtons") == []

        # and it comes back when the schedule is enabled again
        page.evaluate(
            "frm.doc.pd_custom_enable_invoice_schedule = 1; handlers['Sales Order'].refresh(frm)"
        )
        assert page.evaluate("window.navButtons") == [
            {"label": "Generate Invoice", "group": "Milestones"}
        ]
    finally:
        page.close()


def test_milestone_names_skip_core_lookup_but_payment_schedule_keeps_it(browser):
    page = browser.new_page()
    try:
        setup(page)
        page.evaluate("handlers['Sales Order'].refresh(frm)")
        page.evaluate("frm.cscript.payment_term(frm.doc, 'Invoice Schedule', 'NEW-MILESTONE')")
        assert page.evaluate("frm.cscript.calls") == []
        assert page.evaluate("rpc") == []
        result = page.evaluate("frm.cscript.payment_term(frm.doc, 'Payment Schedule', 'TERM-ROW')")
        assert result == "core-result"
        assert page.evaluate("frm.cscript.calls") == [{"cdt": "Payment Schedule", "cdn": "TERM-ROW"}]
    finally:
        page.close()


def test_milestone_dropdown_uses_payment_term_search_and_allows_custom_names(browser):
    page = browser.new_page()
    try:
        setup(page)
        field = page.evaluate("frm.fields_dict.pd_custom_invoice_schedule.grid.docfields[0]")
        assert field["fieldtype"] == "Autocomplete"
        assert field["ignore_validation"] == 1
        query = page.evaluate("frm.fields_dict.pd_custom_invoice_schedule.grid.get_field('payment_term').get_query")
        assert query["query"] == "print_designer.custom.invoice_schedule.search_milestone_payment_terms"
    finally:
        page.close()
