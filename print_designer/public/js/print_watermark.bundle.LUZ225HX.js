(() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropSymbols = Object.getOwnPropertySymbols;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __propIsEnum = Object.prototype.propertyIsEnumerable;
  var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
  var __spreadValues = (a, b) => {
    for (var prop in b || (b = {}))
      if (__hasOwnProp.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    if (__getOwnPropSymbols)
      for (var prop of __getOwnPropSymbols(b)) {
        if (__propIsEnum.call(b, prop))
          __defNormalProp(a, prop, b[prop]);
      }
    return a;
  };

  // ../print_designer/print_designer/public/js/print_watermark.bundle.js
  frappe.provide("print_designer.watermark");
  print_designer.watermark = {
    current_config: null,
    watermark_element: null,
    templates: [],
    init: function(print_format_name) {
      this.print_format_name = print_format_name;
      this.load_watermark_config();
      this.load_available_templates();
      this.setup_sidebar_controls();
      this.inject_sidebar_tooltips();
    },
    inject_sidebar_tooltips: function() {
      const tooltip_map = {
        "Watermark per Page": __("None=off | Original on First Page=first page only | Copy on All Pages=every page | Original,Copy on Sequence=alternating per page")
      };
      const try_inject = () => {
        const sidebar = $(".print-format-sidebar");
        if (!sidebar.length)
          return;
        sidebar.find("label").each(function() {
          const label = $(this);
          const text = label.clone().find(".watermark-help").remove().end().text().trim();
          if (tooltip_map[text] && !label.find(".watermark-help").length) {
            const $tip = $(
              `<span class="watermark-help"
                            style="cursor:help; color:var(--text-muted); font-weight:bold;
                                   border-bottom:1px dotted currentColor; margin-left:4px;
                                   font-size:0.85em; display:inline-block;">?</span>`
            );
            label.append($tip);
            $tip.tooltip({
              title: tooltip_map[text],
              placement: "right",
              trigger: "hover",
              container: "body"
            });
          }
        });
      };
      setTimeout(try_inject, 800);
      setTimeout(try_inject, 2500);
    },
    load_watermark_config: function() {
      frappe.call({
        method: "print_designer.api.watermark.get_watermark_config_for_print_format",
        args: {
          print_format: this.print_format_name
        },
        callback: (r) => {
          if (r.message && r.message.enabled) {
            this.current_config = r.message;
            this.apply_watermark();
          } else {
            this.remove_watermark();
          }
        },
        error: (r) => {
          console.error("Failed to load watermark config:", r);
          frappe.msgprint({
            title: __("Watermark Error"),
            message: __("Failed to load watermark configuration"),
            indicator: "red"
          });
        }
      });
    },
    load_available_templates: function() {
      frappe.call({
        method: "print_designer.api.watermark.get_available_watermark_templates",
        callback: (r) => {
          if (r.message) {
            this.templates = r.message;
            this.update_template_selector();
          }
        }
      });
    },
    setup_sidebar_controls: function() {
      const sidebar = $(".print-format-sidebar");
      if (!sidebar.length)
        return;
      const watermark_section = $(`
            <div class="watermark-controls">
                <h6>${__("Watermark Settings")}</h6>
                <div class="form-group">
                    <label>${__("Template")}</label>
                    <select class="form-control watermark-template-select">
                        <option value="">${__("No Watermark")}</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>${__("Mode")}</label>
                    <select class="form-control watermark-mode-select">
                        <option value="None">${__("None")}</option>
                        <option value="Original on First Page">${__("Original on First Page")}</option>
                        <option value="Copy on All Pages">${__("Copy on All Pages")}</option>
                        <option value="Original,Copy on Sequence">${__("Original,Copy on Sequence")}</option>
                    </select>
                </div>
                <div class="watermark-advanced-settings" style="display: none;">
                    <div class="form-group">
                        <label>${__("Position")}</label>
                        <select class="form-control watermark-position-select">
                            <option value="Top Left">${__("Top Left")}</option>
                            <option value="Top Center">${__("Top Center")}</option>
                            <option value="Top Right">${__("Top Right")}</option>
                            <option value="Middle Left">${__("Middle Left")}</option>
                            <option value="Middle Center">${__("Middle Center")}</option>
                            <option value="Middle Right">${__("Middle Right")}</option>
                            <option value="Bottom Left">${__("Bottom Left")}</option>
                            <option value="Bottom Center">${__("Bottom Center")}</option>
                            <option value="Bottom Right">${__("Bottom Right")}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${__("Margin (mm)")}</label>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px 8px;">
                            <div><small class="text-muted">${__("Top")}</small>
                                <input type="number" class="form-control watermark-margin-top" min="0" max="100" value="0"></div>
                            <div><small class="text-muted">${__("Right")}</small>
                                <input type="number" class="form-control watermark-margin-right" min="0" max="100" value="0"></div>
                            <div><small class="text-muted">${__("Bottom")}</small>
                                <input type="number" class="form-control watermark-margin-bottom" min="0" max="100" value="0"></div>
                            <div><small class="text-muted">${__("Left")}</small>
                                <input type="number" class="form-control watermark-margin-left" min="0" max="100" value="0"></div>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>${__("Font Size")}</label>
                        <input type="number" class="form-control watermark-font-size" min="8" max="72" value="24">
                    </div>
                    <div class="form-group">
                        <label>${__("Color")}</label>
                        <input type="color" class="form-control watermark-color" value="#999999">
                    </div>
                    <div class="form-group">
                        <label>${__("Opacity")}</label>
                        <input type="range" class="form-control watermark-opacity" min="0" max="1" step="0.1" value="0.6">
                        <small class="text-muted opacity-value">0.6</small>
                    </div>
                    <div class="form-group">
                        <label>${__("Custom Text")}</label>
                        <input type="text" class="form-control watermark-custom-text" placeholder="${__("Optional custom text")}">
                    </div>
                </div>
                <div class="btn-group w-100">
                    <button class="btn btn-sm btn-secondary toggle-advanced">${__("Advanced")}</button>
                    <button class="btn btn-sm btn-primary save-watermark-config">${__("Save")}</button>
                </div>
            </div>
        `);
      sidebar.append(watermark_section);
      this.bind_sidebar_events();
      this.populate_current_config();
    },
    bind_sidebar_events: function() {
      $(".watermark-template-select").on("change", (e) => {
        const template_name = $(e.target).val();
        if (template_name) {
          this.load_template_config(template_name);
        } else {
          this.current_config = { enabled: false };
          this.remove_watermark();
        }
      });
      $(".watermark-mode-select").on("change", (e) => {
        if (this.current_config) {
          this.current_config.watermark_mode = $(e.target).val();
          this.apply_watermark();
        }
      });
      $(".toggle-advanced").on("click", () => {
        $(".watermark-advanced-settings").toggle();
      });
      $(".watermark-position-select, .watermark-margin-top, .watermark-margin-right, .watermark-margin-bottom, .watermark-margin-left, .watermark-font-size, .watermark-color, .watermark-custom-text").on("change input", () => {
        this.update_config_from_controls();
        this.apply_watermark();
      });
      $(".watermark-opacity").on("input", (e) => {
        const value = $(e.target).val();
        $(".opacity-value").text(value);
        this.update_config_from_controls();
        this.apply_watermark();
      });
      $(".save-watermark-config").on("click", () => {
        this.save_configuration();
      });
    },
    update_template_selector: function() {
      const selector = $(".watermark-template-select");
      selector.empty().append('<option value="">' + __("No Watermark") + "</option>");
      this.templates.forEach((template) => {
        selector.append(`<option value="${template.name}">${template.name}</option>`);
      });
    },
    load_template_config: function(template_name) {
      frappe.call({
        method: "print_designer.api.watermark.get_watermark_template_config",
        args: {
          template_name
        },
        callback: (r) => {
          if (r.message) {
            this.current_config = __spreadValues({
              enabled: true,
              source: "template",
              template_name
            }, r.message);
            this.populate_current_config();
            this.apply_watermark();
          }
        },
        error: (r) => {
          frappe.msgprint({
            title: __("Template Error"),
            message: __("Failed to load template configuration"),
            indicator: "red"
          });
        }
      });
    },
    populate_current_config: function() {
      var _a, _b, _c, _d;
      if (!this.current_config || !this.current_config.enabled)
        return;
      $(".watermark-template-select").val(this.current_config.template_name || "");
      $(".watermark-mode-select").val(this.current_config.watermark_mode || "None");
      $(".watermark-position-select").val(this.current_config.position || "Top Right");
      $(".watermark-margin-top").val((_a = this.current_config.margin_top) != null ? _a : 0);
      $(".watermark-margin-right").val((_b = this.current_config.margin_right) != null ? _b : 0);
      $(".watermark-margin-bottom").val((_c = this.current_config.margin_bottom) != null ? _c : 0);
      $(".watermark-margin-left").val((_d = this.current_config.margin_left) != null ? _d : 0);
      $(".watermark-font-size").val(this.current_config.font_size || 24);
      $(".watermark-color").val(this.current_config.color || "#999999");
      $(".watermark-opacity").val(this.current_config.opacity || 0.6);
      $(".watermark-custom-text").val(this.current_config.custom_text || "");
      $(".opacity-value").text(this.current_config.opacity || 0.6);
    },
    update_config_from_controls: function() {
      if (!this.current_config) {
        this.current_config = { enabled: true };
      }
      this.current_config.watermark_mode = $(".watermark-mode-select").val();
      this.current_config.position = $(".watermark-position-select").val();
      this.current_config.margin_top = parseInt($(".watermark-margin-top").val()) || 0;
      this.current_config.margin_right = parseInt($(".watermark-margin-right").val()) || 0;
      this.current_config.margin_bottom = parseInt($(".watermark-margin-bottom").val()) || 0;
      this.current_config.margin_left = parseInt($(".watermark-margin-left").val()) || 0;
      this.current_config.font_size = parseInt($(".watermark-font-size").val()) || 24;
      this.current_config.color = $(".watermark-color").val();
      this.current_config.opacity = parseFloat($(".watermark-opacity").val()) || 0.6;
      this.current_config.custom_text = $(".watermark-custom-text").val();
    },
    apply_watermark: function() {
      if (!this.current_config || !this.current_config.enabled || this.current_config.watermark_mode === "None") {
        this.remove_watermark();
        return;
      }
      this.remove_watermark();
      const print_area = $(".print-format-container, .print-preview-wrapper").first();
      if (!print_area.length)
        return;
      const pd_custom_watermark_text = this.get_watermark_text();
      const position_style = this.get_position_style();
      if (pd_custom_watermark_text === "sequence") {
        this.watermark_element = $(`
                <div class="watermark-sequence-preview" style="
                    position: absolute;
                    pointer-events: none;
                    z-index: 1000;
                    font-family: ${this.current_config.font_family || "Sarabun"};
                    font-size: ${this.current_config.font_size || 24}px;
                    color: ${this.current_config.color || "#999999"};
                    opacity: ${this.current_config.opacity || 0.6};
                    font-weight: bold;
                    text-transform: uppercase;
                    ${position_style}
                ">
                    <div class="sequence-original">${__("ORIGINAL")}</div>
                    <div class="sequence-copy" style="margin-top: 10px; font-size: 0.8em; font-style: italic;">(${__("COPY")} on pages 2+)</div>
                </div>
            `);
      } else {
        this.watermark_element = $(`
                <div class="watermark-overlay" style="
                    position: absolute;
                    pointer-events: none;
                    z-index: 1000;
                    font-family: ${this.current_config.font_family || "Sarabun"};
                    font-size: ${this.current_config.font_size || 24}px;
                    color: ${this.current_config.color || "#999999"};
                    opacity: ${this.current_config.opacity || 0.6};
                    font-weight: bold;
                    text-transform: uppercase;
                    ${position_style}
                ">${pd_custom_watermark_text}</div>
            `);
      }
      print_area.css("position", "relative").append(this.watermark_element);
      this.apply_watermark_mode();
    },
    get_watermark_text: function() {
      if (this.current_config.custom_text) {
        return this.current_config.custom_text;
      }
      const mode = this.current_config.watermark_mode;
      if (mode === "Original on First Page") {
        return __("ORIGINAL");
      } else if (mode === "Copy on All Pages") {
        return __("COPY");
      } else if (mode === "Original,Copy on Sequence") {
        return "sequence";
      }
      return __("WATERMARK");
    },
    get_position_style: function() {
      const position = this.current_config.position || "Top Right";
      const to_px = (mm) => Math.round((parseInt(mm) || 0) * 3.7795) + "px";
      const mt = to_px(this.current_config.margin_top);
      const mr = to_px(this.current_config.margin_right);
      const mb = to_px(this.current_config.margin_bottom);
      const ml = to_px(this.current_config.margin_left);
      const positions = {
        "Top Left": `top: ${mt}; left: ${ml};`,
        "Top Center": `top: ${mt}; left: 50%; transform: translateX(-50%);`,
        "Top Right": `top: ${mt}; right: ${mr};`,
        "Middle Left": `top: 50%; left: ${ml}; transform: translateY(-50%);`,
        "Middle Center": "top: 50%; left: 50%; transform: translate(-50%, -50%);",
        "Middle Right": `top: 50%; right: ${mr}; transform: translateY(-50%);`,
        "Bottom Left": `bottom: ${mb}; left: ${ml};`,
        "Bottom Center": `bottom: ${mb}; left: 50%; transform: translateX(-50%);`,
        "Bottom Right": `bottom: ${mb}; right: ${mr};`
      };
      return positions[position] || positions["Top Right"];
    },
    apply_watermark_mode: function() {
      const mode = this.current_config.watermark_mode;
      if (mode === "Copy on All Pages") {
        const pages = $(".print-format-page");
        if (pages.length > 1) {
          pages.each((index, page) => {
            if (index > 0) {
              const cloned_watermark = this.watermark_element.clone();
              $(page).css("position", "relative").append(cloned_watermark);
            }
          });
        }
      }
    },
    remove_watermark: function() {
      $(".watermark-overlay, .watermark-sequence-preview").remove();
      this.watermark_element = null;
    },
    save_configuration: function() {
      if (!this.current_config)
        return;
      this.update_config_from_controls();
      const config_data = {
        watermark_template: $(".watermark-template-select").val() || null,
        override_settings: $(".watermark-template-select").val() ? 0 : 1,
        watermark_mode: this.current_config.watermark_mode,
        font_size: this.current_config.font_size,
        position: this.current_config.position,
        font_family: this.current_config.font_family,
        color: this.current_config.color,
        opacity: this.current_config.opacity,
        custom_text: this.current_config.custom_text
      };
      frappe.call({
        method: "print_designer.api.watermark.save_print_format_watermark_config",
        args: {
          print_format: this.print_format_name,
          config: config_data
        },
        callback: (r) => {
          if (r.message && r.message.success) {
            frappe.show_alert({
              message: r.message.message,
              indicator: "green"
            });
          } else {
            frappe.msgprint({
              title: __("Save Error"),
              message: r.message.error || __("Failed to save configuration"),
              indicator: "red"
            });
          }
        },
        error: (r) => {
          frappe.msgprint({
            title: __("Save Error"),
            message: __("Failed to save watermark configuration"),
            indicator: "red"
          });
        }
      });
    },
    create_template: function(template_data) {
      return frappe.call({
        method: "print_designer.api.watermark.create_watermark_template",
        args: {
          template_data
        },
        callback: (r) => {
          if (r.message && r.message.success) {
            this.load_available_templates();
            frappe.show_alert({
              message: r.message.message,
              indicator: "green"
            });
            return r.message.template_name;
          } else {
            frappe.msgprint({
              title: __("Template Creation Error"),
              message: r.message.error || __("Failed to create template"),
              indicator: "red"
            });
          }
        }
      });
    },
    show_template_dialog: function() {
      const dialog = new frappe.ui.Dialog({
        title: __("Create Watermark Template"),
        fields: [
          {
            fieldtype: "Data",
            fieldname: "template_name",
            label: __("Template Name"),
            reqd: 1
          },
          {
            fieldtype: "Select",
            fieldname: "watermark_mode",
            label: __("Watermark Mode"),
            options: "None\nOriginal on First Page\nCopy on All Pages\nOriginal,Copy on Sequence",
            default: "Copy on All Pages",
            reqd: 1
          },
          {
            fieldtype: "Section Break"
          },
          {
            fieldtype: "Int",
            fieldname: "font_size",
            label: __("Font Size (px)"),
            default: 24
          },
          {
            fieldtype: "Select",
            fieldname: "position",
            label: __("Position"),
            options: "Top Left\nTop Center\nTop Right\nMiddle Left\nMiddle Center\nMiddle Right\nBottom Left\nBottom Center\nBottom Right",
            default: "Top Right"
          },
          {
            fieldtype: "Select",
            fieldname: "font_family",
            label: __("Font Family"),
            options: "Arial\nHelvetica\nTimes New Roman\nCourier New\nVerdana\nGeorgia\nTahoma\nCalibri\nSarabun",
            default: "Sarabun"
          },
          {
            fieldtype: "Color",
            fieldname: "color",
            label: __("Text Color"),
            default: "#999999"
          },
          {
            fieldtype: "Float",
            fieldname: "opacity",
            label: __("Opacity"),
            default: 0.6,
            precision: 2
          },
          {
            fieldtype: "Data",
            fieldname: "custom_text",
            label: __("Custom Text"),
            description: __("Override default text (Original/Copy) with custom text")
          },
          {
            fieldtype: "Text",
            fieldname: "description",
            label: __("Description")
          }
        ],
        primary_action_label: __("Create Template"),
        primary_action: (values) => {
          this.create_template(values).then(() => {
            dialog.hide();
          });
        }
      });
      dialog.show();
    }
  };
  $(document).ready(() => {
    if (window.cur_frm && cur_frm.doctype === "Print Format") {
      frappe.after_ajax(() => {
        if (cur_frm.doc.name) {
          print_designer.watermark.init(cur_frm.doc.name);
        }
      });
    }
    const maybe_inject_tooltips = () => {
      const route = frappe.get_route ? frappe.get_route() : [];
      if (route && route[0] === "print") {
        print_designer.watermark.inject_sidebar_tooltips();
      }
    };
    setTimeout(maybe_inject_tooltips, 1e3);
    if (frappe.router) {
      frappe.router.on("change", () => setTimeout(maybe_inject_tooltips, 1e3));
    }
  });
  (function() {
    const _original_print_doc = frappe.ui.form.Form.prototype.print_doc;
    frappe.ui.form.Form.prototype.print_doc = function() {
      if (this.is_dirty()) {
        frappe.toast({
          message: __(
            "This document has unsaved changes which might not appear in the output. <br> Consider saving the document before printing."
          ),
          indicator: "yellow"
        });
      }
      const print_format = this.get_print_format();
      frappe.xcall("print_designer.overrides.print_button.get_print_config", {
        print_format
      }).then((config) => {
        if (config.raw_printing && config.tbs_agent_available) {
          this._submit_raw_print_via_tbs(print_format, config);
        } else if (config.pdf_generator === "chrome") {
          const params = new URLSearchParams({
            doctype: this.doctype,
            name: this.doc.name,
            format: print_format,
            no_letterhead: this.get_letterhead ? 0 : 1,
            _lang: frappe.boot.lang || "en"
          });
          const pdf_url = `/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`;
          window.open(pdf_url, "_blank");
        } else {
          _original_print_doc.call(this);
        }
      }).catch(() => {
        _original_print_doc.call(this);
      });
    };
    frappe.ui.form.Form.prototype._submit_raw_print_via_tbs = function(print_format, config) {
      frappe.show_alert({
        message: __("Sending to printer..."),
        indicator: "blue"
      });
      frappe.xcall("print_designer.overrides.print_button.submit_raw_print", {
        doc: this.doctype,
        name: this.doc.name,
        print_format,
        agent: config.default_agent,
        printer: config.default_printer
      }).then((result) => {
        if (result && result.success) {
          frappe.show_alert({
            message: __("Print job submitted successfully"),
            indicator: "green"
          });
        }
      }).catch((err) => {
        frappe.msgprint({
          title: __("Print Error"),
          message: err.message || __("Failed to submit print job"),
          indicator: "red"
        });
      });
    };
    frappe.ui.form.Form.prototype.get_print_format = function() {
      const user_settings = frappe.get_user_settings(this.doctype);
      if (user_settings && user_settings.print_format) {
        return user_settings.print_format;
      }
      const meta = frappe.get_meta(this.doctype);
      if (meta && meta.default_print_format) {
        return meta.default_print_format;
      }
      return "Standard";
    };
    const _patch_print_view = function() {
      if (!frappe.ui.form.PrintView)
        return;
      const _original_printit = frappe.ui.form.PrintView.prototype.printit;
      frappe.ui.form.PrintView.prototype.printit = function() {
        const me = this;
        if (!me.is_raw_printing()) {
          return _original_printit.call(me);
        }
        const print_format_name = me.selected_format();
        frappe.xcall("print_designer.overrides.print_button.get_print_config", {
          print_format: print_format_name
        }).then((config) => {
          if (config.tbs_agent_available) {
            me._tbs_raw_print(print_format_name, config);
          } else {
            _original_printit.call(me);
          }
        }).catch(() => {
          _original_printit.call(me);
        });
      };
      frappe.ui.form.PrintView.prototype._tbs_raw_print = function(print_format, config) {
        frappe.show_alert({
          message: __("Sending to printer via TBS agent..."),
          indicator: "blue"
        });
        frappe.xcall("print_designer.overrides.print_button.submit_raw_print", {
          doc: this.frm.doctype || this.frm.doc.doctype,
          name: this.frm.docname || this.frm.doc.name,
          print_format,
          agent: config.default_agent,
          printer: config.default_printer
        }).then((result) => {
          if (result && result.success) {
            frappe.show_alert({
              message: __("Print job submitted successfully"),
              indicator: "green"
            });
          }
        }).catch((err) => {
          frappe.msgprint({
            title: __("Print Error"),
            message: err.message || __("Failed to submit print job to TBS agent"),
            indicator: "red"
          });
        });
      };
    };
    if (frappe.ui.form.PrintView) {
      _patch_print_view();
    } else {
      $(document).on("page-change", function() {
        if (frappe.ui.form.PrintView && !frappe.ui.form.PrintView.prototype._tbs_raw_print) {
          _patch_print_view();
        }
      });
    }
  })();
})();
//# sourceMappingURL=print_watermark.bundle.LUZ225HX.js.map
