/**
 * Thai WHT Income Type List View
 * Column order: ID → Doc Title (TH) → Income Category (TH) → Form Type (TH) → Tax Rate (%) → Income Description (TH)
 *
 * Uses JS flex for both header AND data rows (CSS alone doesn't work for header
 * because onload fires before header DOM is ready).
 *
 * Placed in DocType's own directory — loads automatically, no hook needed.
 */

frappe.listview_settings["Thai WHT Income Type"] = {
  onload: function (listview) {
    var cols = listview.columns;

    // Remove unwanted columns from array BEFORE rendering
    // Keep only: ID, Doc Title TH, Income Category TH, Form Type TH, Tax Rate, Income Desc TH
    var keep_fields = ["name", "doc_title_th", "income_category_th", "form_type_th", "tax_rate", "income_description_th"];
    var remove_idxs = [];
    for (var i = 0; i < cols.length; i++) {
      var fn = cols[i].df && cols[i].df.fieldname;
      if (!keep_fields.includes(fn) && cols[i].type !== "Tag" && cols[i].type !== "Status") {
        remove_idxs.push(i);
      }
    }
    // Remove from end to preserve indices
    for (var j = remove_idxs.length - 1; j >= 0; j--) {
      cols.splice(remove_idxs[j], 1);
    }

    // Move ID (name) to first position as frozen Subject
    var subject_idx = -1;
    var name_idx = -1;
    for (var i = 0; i < cols.length; i++) {
      if (cols[i].type === "Subject") subject_idx = i;
      if (cols[i].df && cols[i].df.fieldname === "name") name_idx = i;
    }

    if (subject_idx > -1 && name_idx > -1 && subject_idx !== name_idx) {
      cols[subject_idx].type = "Field";
      cols[name_idx].type = "Subject";
      var name_col = cols.splice(name_idx, 1)[0];
      cols.splice(subject_idx, 0, name_col);
    }

    listview.render_header(true);

    // Flex map: 6 columns [1]=ID [2]=Doc Title TH [3]=Income Category TH [4]=Form Type TH [5]=Tax Rate [6]=Income Desc TH
    // Total = 3.0 + 2.0 + 1.5 + 1.0 + 0.7 + 1.8 = 10.0
    var flex_map = {
      name: 3.0,
      doc_title_th: 2.0,
      income_category_th: 1.5,
      form_type_th: 1.0,
      tax_rate: 0.7,
      income_description_th: 1.8,
    };

    // Apply header flex AFTER render_header — must use !important to override Frappe's .list-row-col { flex: 1 !important }
    setTimeout(function () {
      var $header_cells = listview.$result
        .closest(".frappe-list")
        .find(".list-header-subject > .list-row-col");
      cols.forEach(function (col, idx) {
        var flex = flex_map[col.df && col.df.fieldname];
        if (flex !== undefined) {
          $header_cells.eq(idx).css("flex", flex + " !important");
        }
      });
    }, 100);

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
  },
};
