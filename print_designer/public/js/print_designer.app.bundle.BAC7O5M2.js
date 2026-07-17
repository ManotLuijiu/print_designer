(() => {
  // ../print_designer/print_designer/public/js/thailand_wht/thailand_wht_sales_invoice.js
  console.log("\u{1F527} Sales Invoice Client Script Loading - Enhanced Debug Mode for BUN-6...");
  var originalDoc = {};
  var trackingChanges = false;
  function trackFieldChanges(frm, context) {
    const changes = {};
    const currentFields = JSON.stringify(frm.doc);
    const originalFields = JSON.stringify(originalDoc);
    if (currentFields !== originalFields && Object.keys(originalDoc).length > 0) {
      for (let field in frm.doc) {
        if (frm.doc[field] !== originalDoc[field]) {
          changes[field] = {
            old: originalDoc[field],
            new: frm.doc[field]
          };
        }
      }
      console.log(`\u{1F50D} ${context} - Field changes detected:`, changes);
      console.log(`\u{1F50D} ${context} - __unsaved:`, frm.doc.__unsaved);
      console.log(`\u{1F50D} ${context} - is_dirty():`, frm.is_dirty());
      const criticalFields = ["__unsaved", "docstatus", "__islocal", "modified", "modified_by", "owner", "creation"];
      const criticalChanges = {};
      for (let field of criticalFields) {
        if (field in changes) {
          criticalChanges[field] = changes[field];
        }
      }
      if (Object.keys(criticalChanges).length > 0) {
        console.log(`\u{1F6A8} ${context} - CRITICAL field changes that affect submit logic:`, criticalChanges);
      }
      const calculatedFields = ["grand_total", "total", "net_total", "outstanding_amount", "paid_amount"];
      const calculatedChanges = {};
      for (let field of calculatedFields) {
        if (field in changes) {
          calculatedChanges[field] = changes[field];
        }
      }
      if (Object.keys(calculatedChanges).length > 0) {
        console.log(`\u{1F4B0} ${context} - Calculated field changes:`, calculatedChanges);
      }
    }
    return Object.keys(changes).length > 0;
  }
  function monitorFormDirtyState(frm) {
    if (frm.set_dirty_original)
      return;
    frm.set_dirty_original = frm.set_dirty;
    frm.set_dirty = function() {
      console.log("\u{1F6A8} set_dirty() called from:", new Error().stack.split("\n")[1]);
      console.log("\u{1F6A8} Current dirty state:", this.is_dirty());
      return frm.set_dirty_original.apply(this, arguments);
    };
  }
  frappe.ui.form.on("Sales Invoice", {
    onload: function(frm) {
      console.log("\u{1F4CB} Sales Invoice onload triggered", {
        docname: frm.doc.name,
        docstatus: frm.doc.docstatus,
        is_new: frm.is_new(),
        status: frm.doc.status
      });
      originalDoc = JSON.parse(JSON.stringify(frm.doc));
      monitorFormDirtyState(frm);
      if (frm.doc.company) {
        setTimeout(() => pd_fetch_company_thai_fields(frm), 100);
      }
    },
    refresh: function(frm) {
      console.log("\u{1F504} Sales Invoice refresh triggered", {
        docname: frm.doc.name,
        docstatus: frm.doc.docstatus,
        is_new: frm.is_new(),
        status: frm.doc.status,
        is_dirty: frm.is_dirty(),
        country: frm.doc.pd_custom_company_country,
        taxes_count: frm.doc.taxes ? frm.doc.taxes.length : 0,
        toolbar_buttons: frm.page.btn_primary ? frm.page.btn_primary.text() : "No primary button"
      });
      if (frm.page.btn_primary) {
        console.log("\u{1F518} Primary button text:", frm.page.btn_primary.text());
        console.log("\u{1F518} Primary button visible:", frm.page.btn_primary.is(":visible"));
      }
      const submitBtn = frm.page.wrapper.find('.btn-primary:contains("Submit")');
      const saveBtn = frm.page.wrapper.find('.btn-primary:contains("Save")');
      console.log("\u{1F50D} Submit button found:", submitBtn.length > 0);
      console.log("\u{1F50D} Save button found:", saveBtn.length > 0);
      if (trackingChanges) {
        trackFieldChanges(frm, "REFRESH");
      }
      if (frm.doc.company && frm.doc.thailand_service_business === void 0 && frm.doc.construction_service === void 0) {
        frm.events.company(frm);
      }
      pd_calculate_wht_amounts(frm);
      console.log("\u{1F1F9}\u{1F1ED} WHT calculated on refresh");
    },
    before_save: function(frm) {
      console.log("\u{1F4BE} Before save - storing current state");
      originalDoc = JSON.parse(JSON.stringify(frm.doc));
      trackingChanges = false;
    },
    after_save: function(frm) {
      console.log("\u{1F4BE} Sales Invoice after_save triggered", {
        docname: frm.doc.name,
        docstatus: frm.doc.docstatus,
        status: frm.doc.status,
        is_dirty: frm.is_dirty(),
        __unsaved: frm.doc.__unsaved
      });
      trackingChanges = true;
      originalDoc = JSON.parse(JSON.stringify(frm.doc));
      let checkCount = 0;
      let wasClean = !frm.is_dirty();
      const checkInterval = setInterval(() => {
        checkCount++;
        const isDirty = frm.is_dirty();
        const hasChanges = trackFieldChanges(frm, `CHECK_${checkCount}`);
        if (wasClean && isDirty) {
          console.log(`\u{1F6A8} DIRTY STATE TRANSITION DETECTED on check ${checkCount}!`);
          console.log("\u{1F6A8} Form just became dirty - investigating...");
          console.log("   - Previous state: CLEAN");
          console.log("   - Current state: DIRTY");
          console.log("   - frm.doc.__unsaved:", frm.doc.__unsaved);
          console.log("   - Button text:", frm.page.btn_primary ? frm.page.btn_primary.text() : "No button");
          console.log("\u{1F50D} Deep analysis of dirty trigger:");
          console.log("   - frm.dirty_fields:", frm.dirty_fields);
          console.log("   - Document changed fields:", hasChanges ? "YES" : "NO");
          const canSubmit = frm.doc.docstatus === 0 && !frm.doc.__islocal && !frm.doc.__unsaved && frm.perm[0].submit;
          console.log("   - Can submit conditions:", {
            docstatus_0: frm.doc.docstatus === 0,
            not_local: !frm.doc.__islocal,
            not_unsaved: !frm.doc.__unsaved,
            has_submit_perm: frm.perm[0].submit,
            final_result: canSubmit
          });
        }
        wasClean = !isDirty;
        console.log(`\u23F0 Post-save check ${checkCount}:`, {
          timestamp: new Date().toISOString(),
          docstatus: frm.doc.docstatus,
          is_dirty: isDirty,
          has_field_changes: hasChanges,
          button_text: frm.page.btn_primary ? frm.page.btn_primary.text() : "No button",
          __unsaved: frm.doc.__unsaved
        });
        if (checkCount >= 20 || isDirty && hasChanges) {
          clearInterval(checkInterval);
          console.log(`\u{1F3C1} Stopped monitoring after ${checkCount} checks`);
          trackingChanges = false;
        }
      }, 500);
    },
    on_submit: function(frm) {
      console.log("\u{1F680} Sales Invoice on_submit triggered", {
        docname: frm.doc.name,
        docstatus: frm.doc.docstatus,
        status: frm.doc.status
      });
    },
    pd_custom_wht_income_type: function(frm) {
      if (frm.doc.pd_custom_wht_income_type && frm.doc.pd_custom_subject_to_wht) {
        const lang = frappe.boot.lang || "en";
        const desc_field = lang === "th" ? "income_description_th" : "income_description";
        const category_field = lang === "th" ? "income_category_th" : "income_category";
        frappe.db.get_value(
          "Thai WHT Income Type",
          frm.doc.pd_custom_wht_income_type,
          [desc_field, category_field, "tax_rate"],
          function(r) {
            if (r) {
              const category = r[category_field] || "";
              const description = r[desc_field] || "";
              const display_text = category ? `${category} - ${description}` : description;
              frm.set_value("pd_custom_wht_description", display_text);
            }
          }
        );
      } else if (!frm.doc.pd_custom_wht_income_type) {
        frm.set_value("pd_custom_wht_description", "");
      }
    },
    company: function(frm) {
      pd_fetch_company_thai_fields(frm);
    },
    taxes_and_charges: function(frm) {
      console.log("\u{1F1F9}\u{1F1ED} Thailand WHT: taxes_and_charges event triggered");
      pd_override_thai_tax_charge_type(frm);
    }
  });
  frappe.ui.form.on("Sales Taxes and Charges", {
    charge_type: function(frm, cdt, cdn) {
      const tax_row = locals[cdt][cdn];
      console.log("\u{1F1F9}\u{1F1ED} Thailand WHT: charge_type changed to:", tax_row.charge_type);
      pd_calculate_wht_amounts(frm);
    }
  });
  function pd_fetch_company_thai_fields(frm) {
    if (!frm.doc.company)
      return;
    frappe.db.get_value("Company", frm.doc.company, [
      "thailand_service_business",
      "construction_service",
      "country"
    ]).then((r) => {
      if (r && r.message) {
        frm.doc.pd_custom_company_thailand_service_business = r.message.thailand_service_business || 0;
        frm.doc.pd_custom_company_construction_service = r.message.construction_service || 0;
        frm.doc.pd_custom_company_country = r.message.country;
        console.log("Thailand WHT: Company fields fetched", {
          thailand_service_business: frm.doc.pd_custom_company_thailand_service_business,
          construction_service: frm.doc.pd_custom_company_construction_service,
          country: frm.doc.pd_custom_company_country
        });
        frm.refresh_fields(["pd_custom_company_thailand_service_business", "pd_custom_company_construction_service", "pd_custom_company_country"]);
      }
    });
  }
  function pd_override_thai_tax_charge_type(frm) {
    console.log("\u{1F1F9}\u{1F1ED} Thailand WHT: pd_override_thai_tax_charge_type called");
    console.log("  - company:", frm.doc.company);
    console.log("  - country:", frm.doc.pd_custom_company_country);
    console.log("  - taxes count:", frm.doc.taxes ? frm.doc.taxes.length : 0);
    if (!frm.doc.company || !frm.doc.taxes || frm.doc.taxes.length === 0) {
      console.log("  - SKIP: No company or taxes");
      return;
    }
    if (frm.doc.pd_custom_company_country !== "Thailand") {
      console.log("  - SKIP: Not Thailand company");
      return;
    }
    let overridden = 0;
    frm.doc.taxes.forEach(function(tax, idx) {
      console.log(`  - Tax row ${idx}: charge_type='${tax.charge_type}', amount=${tax.tax_amount}`);
      if (tax.charge_type && !["Thai Tax Compliance", "On Previous Row Amount", "On Previous Row Total", "On Item Quantity"].includes(tax.charge_type)) {
        if (!tax.custom_original_charge_type) {
          tax.custom_original_charge_type = tax.charge_type;
        }
        tax.charge_type = "Thai Tax Compliance";
        console.log(`  - Tax row ${idx}: OVERRIDE to 'Thai Tax Compliance'`);
        overridden++;
      }
    });
    if (overridden > 0) {
      console.log("\u{1F1F9}\u{1F1ED} Thailand WHT: Set charge_type to Thai Tax Compliance for", overridden, "tax rows");
      frm.refresh_field("taxes");
    }
  }
  $(document).on("change", "[data-fieldname]", function() {
    if (trackingChanges) {
      const fieldname = $(this).data("fieldname");
      console.log("\u{1F527} Field change detected:", fieldname, "New value:", $(this).val());
    }
  });
  var originalCall = frappe.call;
  frappe.call = function(opts) {
    if (trackingChanges && opts.method) {
      console.log("\u{1F4E1} API call during tracking:", opts.method, opts.args || "");
    }
    return originalCall.apply(this, arguments);
  };
  function monitorModelEvents() {
    if (!frappe.model.set_value_original) {
      frappe.model.set_value_original = frappe.model.set_value;
      frappe.model.set_value = function(doctype, docname, fieldname, value, skip_dirty_trigger) {
        if (trackingChanges && doctype === "Sales Invoice") {
          console.log(`\u{1F527} frappe.model.set_value called:`, {
            doctype,
            docname,
            fieldname,
            value,
            skip_dirty_trigger,
            stack: new Error().stack.split("\n")[2]
          });
        }
        return frappe.model.set_value_original.apply(this, arguments);
      };
    }
    if (!frappe.model.set_unsaved_original) {
      const originalSetValue = frappe.model.set_value;
    }
  }
  monitorModelEvents();
  window.pd_fetch_company_thai_fields = pd_fetch_company_thai_fields;
  window.pd_calculate_wht_amounts = pd_calculate_wht_amounts;
  function pd_calculate_wht_amounts(frm) {
    const total = frm.doc.total || 0;
    const whtPct = frm.doc.pd_custom_withholding_tax_pct || 0;
    const whtAmount = total * whtPct / 100;
    const netTotalAfterWHT = total - whtAmount;
    frm.set_value("pd_custom_withholding_tax_amount", whtAmount, null, true);
    frm.set_value("pd_custom_net_total_after_wht", netTotalAfterWHT, null, true);
    if (netTotalAfterWHT > 0) {
      frappe.call({
        method: "print_designer.thailand_wht_sales_invoice.calculate_net_total_words",
        args: { amount: netTotalAfterWHT, currency: frm.doc.currency },
        callback: function(r) {
          if (r.message) {
            frm.set_value("pd_custom_net_total_after_wht_words", r.message, null, true);
            frm.refresh_fields(["pd_custom_net_total_after_wht_words"]);
          }
        }
      });
    } else {
      frm.set_value("pd_custom_net_total_after_wht_words", "", null, true);
      frm.refresh_fields(["pd_custom_net_total_after_wht_words"]);
    }
  }
})();
//# sourceMappingURL=print_designer.app.bundle.BAC7O5M2.js.map
