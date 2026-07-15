/**
 * Tax Withholding Category List View
 * Column order: ID (name) → Category Name (title_field)
 *
 * Uses JS flex for both header AND data rows (CSS alone doesn't work for header
 * because onload fires before header DOM is ready).
 *
 * Extends ERPNext core DocType via doctype_list_js hook.
 */

setTimeout(function () {
  var settings = frappe.listview_settings["Tax Withholding Category"] || {};
  var original_onload = settings.onload;

  settings.onload = function (listview) {
    if (original_onload) {
      original_onload.call(this, listview);
    }

    var cols = listview.columns;

    // Move ID (name) to first position as frozen Subject
    var subject_idx = cols.findIndex(function (c) {
      return c.type === "Subject";
    });
    var name_idx = cols.findIndex(function (c) {
      return c.df && c.df.fieldname === "name" && c.type === "Field";
    });

    if (subject_idx > -1 && name_idx > -1 && subject_idx !== name_idx) {
      cols[subject_idx].type = "Field";
      cols[name_idx].type = "Subject";
      var name_col = cols.splice(name_idx, 1)[0];
      cols.splice(subject_idx, 0, name_col);
    }

    listview.render_header(true);

    // Flex map: [1]=ID [2]=Category Name
    var flex_map = {
      name: 3.0,
      category_name: 2.0,
    };

    // Apply header flex via JS (not CSS — timing issue in onload)
    var apply_header_flex = function () {
      var $header_cells = listview.$result
        .closest(".frappe-list")
        .find(".list-header-subject > .list-row-col");
      cols.forEach(function (col, idx) {
        var flex = flex_map[col.df && col.df.fieldname];
        if (flex !== undefined) {
          $header_cells.eq(idx).css("flex", flex + " !important");
        }
      });
    };

    setTimeout(apply_header_flex, 100);

    // Apply flex to data rows on each render cycle
    var apply_data_flex = function () {
      listview.$result.find(".list-row").each(function () {
        var $cells = $(this).find(".level-left > .list-row-col");
        cols.forEach(function (col, idx) {
          var flex = flex_map[col.df && col.df.fieldname];
          if (flex !== undefined) {
            $cells.eq(idx).css("flex", flex + " !important");
          }
        });
      });
    };

    var orig_render = listview.render.bind(listview);
    listview.render = function () {
      orig_render();
      setTimeout(apply_data_flex, 50);
    };

    listview.render();
  };

  frappe.listview_settings["Tax Withholding Category"] = settings;
}, 0);
