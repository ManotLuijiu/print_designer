import { watch, markRaw } from "vue";
import { useMainStore } from "./store/MainStore";
import { useElementStore } from "./store/ElementStore";
import { makeFeild } from "./frappeControl";
import { storeToRefs } from "pinia";
import {
  parseFloatAndUnit,
  handleAlignIconClick,
  handleBorderIconClick,
  getConditonalObject,
  getParentPage,
} from "./utils";

// P3: Border Visual Editor Component - use markRaw to avoid reactivity warning
import BorderVisualEditor from "./components/custom/BorderVisualEditor.vue";
const BorderVisualEditorRaw = markRaw(BorderVisualEditor);
// P4: Drag Paint Controls Component
import DragPaintControls from "./components/custom/DragPaintControls.vue";
const DragPaintControlsRaw = markRaw(DragPaintControls);
export const createPropertiesPanel = () => {
  const MainStore = useMainStore();
  const ElementStore = useElementStore(); // Used in some closures

  // Step 1: Watch for selection changes and log target object
  watch(
    () => MainStore.currentElements,
    (newVal) => {
      const keys = Object.keys(newVal);
      const values = Object.values(newVal);
      const firstElement = values[0];
      console.log(
        `[Selection] Changed: count=${keys.length} | firstType=${firstElement?.type} | styleEditMode=${firstElement?.styleEditMode} | selectedColumn=${firstElement?.selectedColumn?.label ?? "none"}`,
        { keys, firstElement },
      );
    },
    { deep: true },
  );

  const iconControl = ({
    name,
    size,
    padding,
    margin,
    onClick,
    isActive,
    onlyIcon = false,
    parentBorderTop = false,
    parentBorderBottom = false,
    condtional = null,
    useLetterBox = false,
    letter = "",
    ...args
  }) => {
    const iconProps = {
      onlyIcon,
      name,
      size,
      padding,
      margin,
      onClick,
      isActive,
      useLetterBox,
      letter,
    };
    const result = { icon: iconProps };
    if (onlyIcon) {
      result["name"] = name;
      result["condtional"] = condtional;
      result["parentBorderTop"] = parentBorderTop;
      result["parentBorderBottom"] = parentBorderBottom;
      if (Object.keys(args).length !== 0 && args.constructor === Object) {
        Object.entries({ ...args })?.forEach((arg) => {
          result[arg[0]] = arg[1];
        });
      }
    }
    return result;
  };
  const AlignIcons = (name) => {
    return iconControl({
      name,
      size: 20,
      padding: 3,
      margin: 4,
      onClick: () => handleAlignIconClick(name),
      onlyIcon: true,
    });
  };
  const textAlignIcons = (name) => {
    const mapper = {
      textAlignLeft: "left",
      textAlignRight: "right",
      textAlignCenter: "center",
      textAlignJustify: "justify",
    };
    return iconControl({
      name,
      size: 20,
      padding: 3,
      margin: 5,
      onClick: () =>
        (getConditonalObject({
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          isStyle: true,
        })["textAlign"] = mapper[name]),
      isActive: () =>
        getConditonalObject({
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          isStyle: true,
          property: "textAlign",
        }) == mapper[name],
      onlyIcon: true,
      parentBorderTop: true,
      parentBorderBottom: true,
    });
  };
  const borderWidthIcons = (name, { ...args }) => {
    // Letter mapping for simple box icons
    const letterMap = {
      borderAll: "All",
      borderLeftStyle: "L",
      borderRightStyle: "R",
      borderTopStyle: "T",
      borderBottomStyle: "B",
    };
    return iconControl({
      name,
      color: "var(--text-muted)",
      size: 18,
      padding: 2,
      margin: 8,
      useLetterBox: true,
      letter: letterMap[name] || name,
      condtional: () => {
        return parseFloatAndUnit(
          getConditonalObject({
            reactiveObject: () => MainStore.getCurrentElementsValues[0],
            isStyle: true,
            property: "borderWidth",
          }),
        ).value;
      },
      onClick: () => {
        const selectedElement = MainStore.getCurrentElementsValues[0];
        const hasSelectedColumn = !!selectedElement?.selectedColumn;
        const styleEditMode = selectedElement?.styleEditMode;

        // For L/R in header mode (no column selected), target specific column's style
        if (
          styleEditMode === "header" &&
          !hasSelectedColumn &&
          selectedElement?.columns?.length
        ) {
          let targetColumnStyle;

          if (name === "borderLeftStyle") {
            // L: target first column's style
            targetColumnStyle = selectedElement.columns[0].style;
          } else if (name === "borderRightStyle") {
            // R: target last column's style
            targetColumnStyle =
              selectedElement.columns[selectedElement.columns.length - 1].style;
          }

          if (targetColumnStyle) {
            if (targetColumnStyle[name] === "hidden") {
              targetColumnStyle[name] = "solid";
            } else {
              targetColumnStyle[name] = "hidden";
            }
          }
          return;
        }

        // Default behavior: use getConditonalObject
        let targetStyle = getConditonalObject({
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          isStyle: true,
        });
        handleBorderIconClick(targetStyle, name);
      },
      isActive: () => {
        const selectedElement = MainStore.getCurrentElementsValues[0];
        const hasSelectedColumn = !!selectedElement?.selectedColumn;
        const styleEditMode = selectedElement?.styleEditMode;

        // Helper: border is ACTIVE if NOT hidden (undefined = visible like Excel grid)
        const isBorderActive = (styleObj) => {
          if (!styleObj) return true;
          return styleObj[name] !== "hidden";
        };

        // For L/R in header mode (no column selected), check specific column's style
        if (
          styleEditMode === "header" &&
          !hasSelectedColumn &&
          selectedElement?.columns?.length
        ) {
          let checkStyle;

          if (name === "borderLeftStyle") {
            // L: check first column's style
            checkStyle = selectedElement.columns[0].style;
          } else if (name === "borderRightStyle") {
            // R: check last column's style
            checkStyle =
              selectedElement.columns[selectedElement.columns.length - 1].style;
          }

          if (checkStyle) {
            return isBorderActive(checkStyle);
          }
          return true; // Default to active if no column style
        }

        // Default: check the conditional object
        let checkStyle = getConditonalObject({
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          isStyle: true,
        });

        if (name === "borderAll") {
          return [
            "borderTopStyle",
            "borderBottomStyle",
            "borderLeftStyle",
            "borderRightStyle",
          ].every((side) => {
            const value = checkStyle?.[side];
            return !!value && value !== "hidden";
          });
        } else {
          return isBorderActive(checkStyle);
        }
      },
      onlyIcon: true,
      parentBorderTop: true,
      parentBorderBottom: true,
      ...args,
    });
  };

  // Border Presets (P2)
  const borderPresets = [
    { name: "No Grid", borders: { L: false, R: false, T: false, B: false } },
    { name: "Full Grid", borders: { L: true, R: true, T: true, B: true } },
    {
      name: "Outline Only",
      borders: {
        L: true,
        R: true,
        T: true,
        B: true,
        innerV: false,
        innerH: false,
      },
    },
    {
      name: "Horizontal",
      borders: { L: false, R: false, T: true, B: true, innerH: true },
    },
  ];

  const applyBorderPreset = (preset) => {
    const selectedElement = MainStore.getCurrentElementsValues[0];
    if (!selectedElement) return;

    const getStyleObj = () =>
      getConditonalObject({
        reactiveObject: () => selectedElement,
        isStyle: true,
      });

    // Apply outer borders
    const style = getStyleObj();
    if (style) {
      style.borderLeftStyle = preset.borders.L ? "solid" : "hidden";
      style.borderRightStyle = preset.borders.R ? "solid" : "hidden";
      style.borderTopStyle = preset.borders.T ? "solid" : "hidden";
      style.borderBottomStyle = preset.borders.B ? "solid" : "hidden";
    }

    // Apply to all columns if table
    if (selectedElement.columns) {
      selectedElement.columns.forEach((col) => {
        if (!col.style) col.style = {};
        col.style.borderLeftStyle = preset.borders.L ? "solid" : "hidden";
        col.style.borderRightStyle = preset.borders.R ? "solid" : "hidden";
      });
    }
  };

  // P3: Visual Border Editor - using Vue component
  const createBorderGrid = () => {
    return {
      label: __("Border Grid"),
      name: "borderGrid",
      labelDirection: "row",
      isLabelled: false,
      condtional: () => {
        const element = MainStore.getCurrentElementsValues[0];
        return element?.type === "table";
      },
      component: BorderVisualEditorRaw,
    };
  };

  // P4: Drag Paint Controls - using Vue component
  const createDragPaintControls = () => {
    return {
      label: __("Drag Paint"),
      name: "dragPaint",
      labelDirection: "row",
      isLabelled: false,
      condtional: () => {
        const element = MainStore.getCurrentElementsValues[0];
        return element?.type === "table";
      },
      component: DragPaintControlsRaw,
    };
  };

  // Copy/Paste Border Style (P5)
  let copiedBorderStyle = null;
  const copyBorderStyle = () => {
    const selectedElement = MainStore.getCurrentElementsValues[0];
    if (!selectedElement) return;
    const style = getConditonalObject({
      reactiveObject: () => selectedElement,
      isStyle: true,
    });
    if (style) {
      copiedBorderStyle = { ...style };
      frappe.show_alert(__("Border style copied"));
    }
  };
  const pasteBorderStyle = () => {
    if (!copiedBorderStyle) return;
    const selectedElement = MainStore.getCurrentElementsValues[0];
    if (!selectedElement) return;
    const style = getConditonalObject({
      reactiveObject: () => selectedElement,
      isStyle: true,
    });
    if (style) {
      Object.assign(style, {
        borderLeftStyle: copiedBorderStyle.borderLeftStyle,
        borderRightStyle: copiedBorderStyle.borderRightStyle,
        borderTopStyle: copiedBorderStyle.borderTopStyle,
        borderBottomStyle: copiedBorderStyle.borderBottomStyle,
        borderLeftWidth: copiedBorderStyle.borderLeftWidth,
        borderRightWidth: copiedBorderStyle.borderRightWidth,
        borderTopWidth: copiedBorderStyle.borderTopWidth,
        borderBottomWidth: copiedBorderStyle.borderBottomWidth,
        borderLeftColor: copiedBorderStyle.borderLeftColor,
        borderRightColor: copiedBorderStyle.borderRightColor,
        borderTopColor: copiedBorderStyle.borderTopColor,
        borderBottomColor: copiedBorderStyle.borderBottomColor,
      });
      frappe.show_alert(__("Border style pasted"));
    }
  };

  // Border Style Icons: Solid, Dotted, Dashed
  const borderStyleIcons = (name, { ...args }) => {
    const mapper = {
      borderStyleSolid: "solid",
      borderStyleDotted: "dotted",
      borderStyleDashed: "dashed",
    };
    return iconControl({
      name,
      color: "var(--text-muted)",
      size: 24,
      padding: 2,
      margin: 4,
      condtional: () => {
        return parseFloatAndUnit(
          getConditonalObject({
            reactiveObject: () => MainStore.getCurrentElementsValues[0],
            isStyle: true,
            property: "borderWidth",
          }),
        ).value;
      },
      onClick: () => {
        const element = getConditonalObject({
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          isStyle: true,
        });
        if (element) {
          element["borderStyle"] = mapper[name];
        }
      },
      isActive: () => {
        const element = getConditonalObject({
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          isStyle: true,
        });
        // Default to solid if not set
        const currentStyle = element
          ? element["borderStyle"] || "solid"
          : "solid";
        return currentStyle === mapper[name];
      },
      onlyIcon: true,
      parentBorderTop: true,
      parentBorderBottom: true,
      ...args,
    });
  };

  const inputControl = ({
    label,
    name,
    propertyName,
    inputUnit,
    labelDirection,
    reactiveObject,
    condtional = null,
    ...args
  }) => {
    const result = {
      label,
      name,
      propertyName,
      condtional,
      labelDirection,
      isLabelled: true,
      inputUnit,
      reactiveObject,
      saveWithUom: false,
    };
    if (Object.keys(args).length !== 0 && args.constructor === Object) {
      Object.entries({ ...args })?.forEach((arg) => {
        result[arg[0]] = arg[1];
      });
    }
    return result;
  };
  const pageInput = (label, name, propertyName, { ...args }) => {
    return inputControl({
      label,
      name,
      propertyName,
      inputUnit: () => MainStore.page.UOM,
      labelDirection: "column",
      reactiveObject: () => MainStore.page,
      ...args,
    });
  };
  const paddingInput = (label, name, propertyName) => {
    return inputControl({
      label,
      name,
      propertyName,
      inputUnit: "px",
      labelDirection: "column",
      reactiveObject: () => MainStore.getCurrentElementsValues[0],
      isStyle: true,
      isFontStyle: true,
      saveWithUom: true,
    });
  };
  const transformInput = (label, name, propertyName) => {
    return inputControl({
      label,
      name,
      propertyName,
      inputUnit: () => MainStore.page.UOM,
      labelDirection: "row",
      reactiveObject: () => MainStore.getCurrentElementsValues[0],
    });
  };
  const inputWithIcon = ({
    label,
    name,
    size,
    padding,
    margin,
    inputUnit,
    reactiveObject,
    propertyName,
    labelDirection = "row",
    condtional = null,
    isStyle = false,
    saveWithUom = false,
    ...args
  }) => {
    const result = inputControl({
      label,
      name,
      propertyName,
      inputUnit,
      isLabelled: false,
      condtional,
      reactiveObject,
      labelDirection,
      saveWithUom,
      isStyle,
      ...args,
    });
    result["icon"] = iconControl({
      name,
      size,
      padding,
      margin,
    }).icon;
    return result;
  };
  const styleInputwithIcon = (
    name,
    size,
    {
      padding = 0,
      margin = 0,
      saveWithUom = false,
      isRaw = false,
      condtional = null,
      ...args
    },
  ) =>
    inputWithIcon({
      name,
      propertyName: name,
      size,
      padding,
      margin,
      inputUnit: "px",
      reactiveObject: () => MainStore.getCurrentElementsValues[0],
      isStyle: true,
      isRaw,
      saveWithUom,
      condtional,
      ...args,
    });
  const colorStyleFrappeControl = (
    label,
    name,
    propertyName,
    isFontStyle = false,
    isStyle = true,
  ) => {
    return {
      label,
      name,
      labelDirection: "column",
      isLabelled: true,
      frappeControl: (ref, name) => {
        let styleClass = "table";
        if (MainStore.activeControl == "text") {
          if (MainStore.textControlType == "dynamic") {
            styleClass = "dynamicText";
          } else {
            styleClass = "staticText";
          }
        }
        makeFeild({
          name,
          ref,
          fieldtype: "Color",
          requiredData: [
            MainStore.getCurrentElementsValues[0] ||
              MainStore.globalStyles[styleClass],
          ],
          reactiveObject: () => {
            return (
              MainStore.getCurrentElementsValues[0] ||
              MainStore.globalStyles[styleClass]
            );
          },
          propertyName,
          isStyle,
          isFontStyle,
        });
      },
    };
  };
  MainStore.propertiesPanel.push({
    sectionCondtional: () => !!MainStore.getCurrentElementsId.length,
    fields: [
      [
        AlignIcons("alignLeft"),
        AlignIcons("alignHorizontalCenter"),
        AlignIcons("alignRight"),
        AlignIcons("alignTop"),
        AlignIcons("alignVerticalCenter"),
        AlignIcons("alignBottom"),
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Page Settings",
    sectionCondtional: () =>
      !MainStore.getCurrentElementsId.length &&
      MainStore.activeControl === "mouse-pointer",
    fields: [
      {
        label: () => `Select ${MainStore.rawMeta?.name || "Document"}`,
        isLabelled: true,
        name: "documentName",
        condtional: () => !!MainStore.currentDoc,
        frappeControl: (ref, name) => {
          const { doctype, currentDoc } = storeToRefs(MainStore);
          makeFeild({
            name: name,
            ref: ref,
            fieldtype: "Link",
            requiredData: [doctype, currentDoc],
            options: MainStore.doctype,
            reactiveObject: MainStore,
            propertyName: "currentDoc",
          });
        },
      },
      {
        label: "Page Size",
        name: "pageSize",
        isLabelled: true,
        condtional: null,
        frappeControl: (ref, name) => {
          const MainStore = useMainStore();
          const { pageSizes } = storeToRefs(MainStore);
          makeFeild({
            name: name,
            ref: ref,
            fieldtype: "Autocomplete",
            requiredData: pageSizes,
            options: Object.keys(pageSizes.value),
            reactiveObject: MainStore,
            propertyName: "currentPageSize",
            onChangeCallback: (value = null) => {
              if (value && value != "CUSTOM") {
                MainStore.currentPageSize = value;
                MainStore.page.width = MainStore.convertToPX(
                  MainStore.pageSizes[value][0],
                  "mm",
                );
                MainStore.page.height = MainStore.convertToPX(
                  MainStore.pageSizes[value][1],
                  "mm",
                );
              } else {
                MainStore.frappeControls[name].set_value(
                  MainStore.currentPageSize,
                );
              }
            },
          });
        },
      },
      {
        label: "Page UOM",
        name: "pageUom",
        isLabelled: true,
        condtional: null,
        frappeControl: (ref, name) => {
          const MainStore = useMainStore();
          const { page } = storeToRefs(MainStore);
          makeFeild({
            name,
            ref,
            fieldtype: "Autocomplete",
            requiredData: () => page.value.UOM,
            options: () => [
              { label: "Pixels (px)", value: "px" },
              { label: "Milimeter (mm)", value: "mm" },
              { label: "Centimeter (cm)", value: "cm" },
              { label: "Inch (in)", value: "in" },
            ],
            reactiveObject: page,
            propertyName: "UOM",
          });
        },
      },
      [
        pageInput("Height", "page_height", "height", {
          parentBorderTop: true,
          condtional: () => MainStore.mode == "editing",
        }),
        pageInput("Width", "page_width", "width", {
          condtional: () => MainStore.mode == "editing",
        }),
      ],
      [
        {
          label: "Number to Words Fields",
          name: "numberToWordsFields",
          isLabelled: true,
          flex: "auto",
          condtional: null,
          button: {
            label: "Configure Fields",
            size: "sm",
            style: "secondary",
            margin: 15,
            onClick: (event) => {
              const numericTypes = ["Currency", "Float", "Int", "Percent"];
              const textTypes = ["Data", "Small Text", "Text", "Long Text"];
              const numericFields = MainStore.metaFields
                .filter((field) => numericTypes.includes(field.fieldtype))
                .map((field) => field.fieldname);
              const textFields = MainStore.metaFields
                .filter((field) => textTypes.includes(field.fieldtype))
                .map((field) => field.fieldname);
              const currencyFields = MainStore.metaFields
                .filter(
                  (field) =>
                    field.fieldtype === "Link" && field.options === "Currency",
                )
                .map((field) => field.fieldname);
              const dialog = new frappe.ui.Dialog({
                title: __("Number to Words Fields"),
                fields: [
                  {
                    fieldname: "pairs",
                    fieldtype: "Table",
                    label: __("Field Pairs"),
                    in_place_edit: true,
                    data: JSON.parse(
                      JSON.stringify(MainStore.numberToWordsFieldPairs),
                    ),
                    fields: [
                      {
                        fieldname: "source_field",
                        fieldtype: "Autocomplete",
                        label: __("Number Field"),
                        options: numericFields,
                        in_list_view: 1,
                        reqd: 1,
                      },
                      {
                        fieldname: "target_field",
                        fieldtype: "Autocomplete",
                        label: __("Words Field"),
                        options: textFields,
                        in_list_view: 1,
                        reqd: 1,
                      },
                      {
                        fieldname: "currency_field",
                        fieldtype: "Autocomplete",
                        label: __("Currency Field"),
                        options: currencyFields,
                        in_list_view: 1,
                      },
                    ],
                  },
                ],
                primary_action_label: __("Apply"),
                primary_action(values) {
                  MainStore.numberToWordsFieldPairs = (values.pairs || []).map(
                    ({ source_field, target_field, currency_field }) => ({
                      source_field,
                      target_field,
                      ...(currency_field ? { currency_field } : {}),
                    }),
                  );
                  dialog.hide();
                },
              });
              dialog.show();
              event.target.blur();
            },
          },
        },
      ],
      [
        {
          label: "Delete Page",
          name: "deletePage",
          isLabelled: true,
          flex: "auto",
          condtional: () => MainStore.activePage,
          reactiveObject: () => MainStore.activePage,
          button: {
            label: "Delete Page",
            size: "sm",
            style: "secondary",
            margin: 15,
            onClick: (e) => {
              if (MainStore.activePage?.childrens.length) {
                let message = __("Are you sure you want to delete the page?");
                frappe.confirm(message, () => {
                  ElementStore.Elements.splice(
                    ElementStore.Elements.indexOf(MainStore.activePage),
                    1,
                  );
                  frappe.show_alert(
                    {
                      message: `Page Deleted Successfully`,
                      indicator: "green",
                    },
                    5,
                  );
                });
              } else {
                ElementStore.Elements.splice(
                  ElementStore.Elements.indexOf(MainStore.activePage),
                  1,
                );
                frappe.show_alert(
                  {
                    message: `Page Deleted Successfully`,
                    indicator: "green",
                  },
                  5,
                );
              }
              e.target.blur();
            },
          },
        },
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Page Margins",
    sectionCondtional: () =>
      !MainStore.getCurrentElementsId.length &&
      MainStore.activeControl === "mouse-pointer",
    fields: [
      [
        pageInput("Top", "page_top", "marginTop"),
        pageInput("Bottom", "page_bottom", "marginBottom"),
      ],
      [
        pageInput("Left", "page_left", "marginLeft"),
        pageInput("Right", "page_right", "marginRight"),
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Header / Footer",
    sectionCondtional: () =>
      !MainStore.getCurrentElementsId.length &&
      MainStore.activeControl === "mouse-pointer",
    fields: [
      [
        pageInput("Header", "page_header", "headerHeight"),
        pageInput("Footer", "page_footer", "footerHeight"),
      ],
    ],
  });

  MainStore.propertiesPanel.push({
    title: "Select Pages",
    sectionCondtional: () =>
      MainStore.mode != "editing" &&
      MainStore.activePage &&
      !MainStore.getCurrentElementsId.length &&
      MainStore.activeControl === "mouse-pointer",
    fields: [
      [
        {
          label: "First",
          name: "firstPage",
          isLabelled: true,
          condtional: () => MainStore.activePage,
          reactiveObject: () => MainStore.activePage,
          button: {
            label: "First",
            size: "sm",
            style: () =>
              MainStore.activePage.firstPage ? "primary" : "secondary",
            margin: 15,
            onClick: (e) => {
              MainStore.activePage.firstPage = !MainStore.activePage.firstPage;
              if (MainStore.activePage.firstPage) {
                ElementStore.Elements.forEach((element) => {
                  if (element == MainStore.activePage) return;
                  element.firstPage = false;
                });
              }
              e.target.blur();
            },
          },
        },
        {
          label: "Odd",
          name: "oddPages",
          isLabelled: true,
          condtional: () => MainStore.activePage,
          reactiveObject: () => MainStore.activePage,
          button: {
            label: "Odd",
            style: () =>
              MainStore.activePage.oddPage ? "primary" : "secondary",
            margin: 15,
            size: "sm",
            onClick: (e) => {
              MainStore.activePage.oddPage = !MainStore.activePage.oddPage;
              if (MainStore.activePage.oddPage) {
                ElementStore.Elements.forEach((element) => {
                  if (element == MainStore.activePage) return;
                  element.oddPage = false;
                });
              }
              e.target.blur();
            },
          },
        },
        {
          label: "Even",
          name: "evenPages",
          isLabelled: true,
          condtional: () => MainStore.activePage,
          reactiveObject: () => MainStore.activePage,
          button: {
            label: "Even",
            style: () =>
              MainStore.activePage.evenPage ? "primary" : "secondary",
            margin: 15,
            size: "sm",
            onClick: (e) => {
              MainStore.activePage.evenPage = !MainStore.activePage.evenPage;
              if (MainStore.activePage.evenPage) {
                ElementStore.Elements.forEach((element) => {
                  if (element == MainStore.activePage) return;
                  element.evenPage = false;
                });
              }
              e.target.blur();
            },
          },
        },
        {
          label: "Last",
          name: "lastPages",
          isLabelled: true,
          condtional: () => MainStore.activePage,
          reactiveObject: () => MainStore.activePage,
          button: {
            label: "Last",
            style: () =>
              MainStore.activePage.lastPage ? "primary" : "secondary",
            margin: 15,
            size: "sm",
            onClick: (e) => {
              MainStore.activePage.lastPage = !MainStore.activePage.lastPage;
              if (MainStore.activePage.lastPage) {
                ElementStore.Elements.forEach((element) => {
                  if (element == MainStore.activePage) return;
                  element.lastPage = false;
                });
              }
              e.target.blur();
            },
          },
        },
      ],
    ],
  });

  MainStore.propertiesPanel.push({
    title: "Transform",
    sectionCondtional: () => MainStore.getCurrentElementsId.length === 1,
    fields: [
      [
        transformInput("X", "transformStartX", "startX"),
        transformInput("Y", "transformStartY", "startY"),
      ],
      [
        transformInput("H", "transformHeight", "height"),
        transformInput("W", "transformWidth", "width"),
      ],
      [
        {
          label: "Height",
          name: "heightType",
          isLabelled: true,
          labelDirection: "column",
          condtional: () => {
            const currentEl = MainStore.getCurrentElementsValues[0];
            if (
              ElementStore.isElementOverlapping(
                currentEl,
                getParentPage(currentEl).childrens,
              )
            ) {
              return false;
            }
            if (
              currentEl?.type === "table" ||
              (currentEl.type === "text" &&
                (currentEl.isDynamic || currentEl.parseJinja))
            ) {
              return true;
            }
            return false;
          },
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name,
              ref,
              fieldtype: "Select",
              requiredData: [MainStore.getCurrentElementsValues[0]],
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "heightType",
              isStyle: false,
              options: () => [
                { label: "Auto", value: "auto" },
                { label: "Auto ( min-height)", value: "auto-min-height" },
                { label: "Fixed", value: "fixed" },
              ],
            });
          },
          flex: 1,
        },
        {
          label: "Z Index",
          name: "zIndex",
          isLabelled: true,
          labelDirection: "column",
          condtional: () => MainStore.getCurrentElementsValues[0],
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name,
              ref,
              fieldtype: "Int",
              requiredData: [MainStore.getCurrentElementsValues[0]],
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "zIndex",
              isStyle: true,
              formatValue: (object, property, _isStyle) => {
                if (!object) return;
                return parseInt(object[property]) || 0;
              },
            });
          },
          flex: 1,
        },
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Table Settings",
    sectionCondtional: () =>
      (MainStore.getCurrentElementsId.length === 1 &&
        MainStore.getCurrentElementsValues[0]?.type == "table") ||
      MainStore.activeControl == "table",
    fields: [
      [
        {
          label: "Current Table",
          name: "table",
          isLabelled: true,
          labelDirection: "column",
          flex: 3,
          condtional: () =>
            MainStore.getCurrentElementsValues[0]?.type == "table",
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name,
              ref,
              fieldtype: "Autocomplete",
              requiredData: [MainStore.getTableMetaFields.length],
              options: () => {
                let tablefields = [];
                MainStore.getTableMetaFields.map((field) =>
                  tablefields.push({
                    label: field.label || field.fieldname,
                    value: field.fieldname,
                  }),
                );
                return tablefields;
              },
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "table",
              isStyle: false,
              onChangeCallback: (value = null) => {
                const currentEL = MainStore.getCurrentElementsValues[0];
                const idx = {
                  fieldname: "idx",
                  fieldtype: "Int",
                  label: "No.",
                  options: undefined,
                  tableName: currentEL["table"],
                };
                if (value && currentEL) {
                  currentEL["table"] = MainStore.metaFields.find(
                    (field) => field.fieldname == value,
                  );
                  currentEL["table"].default_layout =
                    frappe.get_user_settings(MainStore.doctype, "GridView")[
                      currentEL["table"].options
                    ] || {};
                  if (Object.keys(currentEL["table"].default_layout).length) {
                    df = { idx };
                    Object.values(currentEL["table"].default_layout).forEach(
                      (value) => {
                        key = value.fieldname;
                        df[key] = currentEL["table"].childfields.find(
                          (df) => df.fieldname == key,
                        );
                      },
                    );
                    currentEL["table"].default_layout = df;
                  } else {
                    currentEL["table"].childfields.map((df) => {
                      currentEL["table"].default_layout["idx"] = idx;
                      if (
                        df.fieldname &&
                        df.in_list_view &&
                        !df.is_virtual &&
                        frappe.model.is_value_type(df) &&
                        df.fieldtype !== "Read Only" &&
                        !frappe.model.layout_fields.includes(df.fieldtype)
                      ) {
                        currentEL["table"].default_layout[df.fieldname] = df;
                      }
                    });
                  }
                  // fill columns with default fields if table is empty
                  if (
                    currentEL.columns &&
                    !currentEL.columns.some((c) => c.dynamicContent) &&
                    currentEL["table"].default_layout
                  ) {
                    dlKeys = Object.keys(currentEL["table"].default_layout);
                    currentEL.columns
                      .slice(0, dlKeys.length)
                      .forEach((col, index) => {
                        col.dynamicContent = [
                          currentEL["table"].default_layout[dlKeys[index]],
                        ];
                        col.dynamicContent.forEach((dc) => {
                          dc.tableName = currentEL["table"].fieldname;
                        });
                        // NOTE: col.label is intentionally NOT reset here.
                        // The user types the column header (e.g. Thai "ลำดับที่")
                        // directly into the properties panel; this previously
                        // overwrote it with the saved Grid View preference
                        // ("sequence" for idx), which silently destroyed the
                        // user's override.
                      });
                  }

                  MainStore.frappeControls[name].$input.blur();
                }
              },
              formatValue: (object, property, _isStyle) => {
                if (!object) return;
                return object[property]?.fieldname || "";
              },
            });
          },
        },
        {
          label: "Rows",
          name: "no_of_rows",
          isLabelled: true,
          labelDirection: "column",
          condtional: () => MainStore.getCurrentElementsValues[0]?.table,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name,
              ref,
              fieldtype: "Int",
              requiredData: [MainStore.getCurrentElementsValues[0]],
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "PreviewRowNo",
              isStyle: false,
              onChangeCallback: (value = null) => {
                if (
                  value &&
                  !Number.isInteger(
                    MainStore.frappeControls["no_of_rows"].value,
                  )
                ) {
                  MainStore.frappeControls["no_of_rows"].set_value(
                    MainStore.frappeControls["no_of_rows"].last_value,
                  );
                }
              },
            });
          },
          flex: 1,
        },
        {
          label: "Min Rows",
          name: "min_rows",
          isLabelled: true,
          labelDirection: "column",
          condtional: () => MainStore.getCurrentElementsValues[0]?.table,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name,
              ref,
              fieldtype: "Int",
              requiredData: [MainStore.getCurrentElementsValues[0]],
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "minRows",
              isStyle: false,
              defaultValue: 0,
              onChangeCallback: (value = null) => {
                // Clamp to non-negative integer; 0 = no padding.
                if (value == null || value === "" || Number.isNaN(value)) {
                  MainStore.getCurrentElementsValues[0].minRows = 0;
                  return;
                }
                const n = Math.max(0, Math.floor(Number(value)));
                MainStore.getCurrentElementsValues[0].minRows = n;
                MainStore.getCurrentElementsValues[0].PreviewRowNo = n;
              },
            });
          },
          flex: 1,
        },
      ],
      [
        {
          label: "Primary Table",
          name: "isPrimaryTable",
          isLabelled: true,
          labelDirection: "column",
          condtional: () => MainStore.getCurrentElementsValues[0]?.table,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            const ElementStore = useElementStore();
            makeFeild({
              name,
              ref,
              fieldtype: "Select",
              requiredData: [MainStore.getCurrentElementsValues[0]],
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "isPrimaryTable",
              isStyle: false,
              options: () => [
                { label: "Yes", value: "Yes" },
                { label: "No", value: "No" },
              ],
              formatValue: (object, property, _isStyle) => {
                if (!object) return;
                return object[property] ? "Yes" : "No";
              },
              onChangeCallback: (value = null) => {
                if (value && MainStore.getCurrentElementsValues[0]) {
                  ElementStore.setPrimaryTable(
                    MainStore.getCurrentElementsValues[0],
                    value === "Yes",
                  );
                  MainStore.frappeControls[name].$input.blur();
                }
              },
            });
          },
          flex: 1,
        },
        {
          label: "Style Mode :",
          isLabelled: true,
          name: "tableStyleEditMode",
          labelDirection: "column",
          condtional: () =>
            [
              MainStore.getCurrentElementsValues[0]?.type,
              MainStore.activeControl,
            ].indexOf("table") != -1,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name: name,
              ref: ref,
              fieldtype: "Select",
              requiredData: [MainStore],
              options: () => {
                return [
                  { label: "Table Header", value: "header" },
                  { label: "All Rows", value: "main" },
                  { label: "Alternate Rows", value: "alt" },
                  { label: "Field Labels", value: "label" },
                ];
              },
              reactiveObject: () => {
                return (
                  MainStore.getCurrentElementsValues[0] ||
                  MainStore.globalStyles["table"]
                );
              },
              onChangeCallback: (_value) => {
                if (
                  MainStore.getCurrentElementsValues[0]?.selectedDynamicText
                ) {
                  if (
                    MainStore.getCurrentElementsValues[0].styleEditMode ==
                    "label"
                  ) {
                    MainStore.getCurrentElementsValues[0].selectedDynamicText.labelStyleEditing = true;
                  } else {
                    MainStore.getCurrentElementsValues[0].selectedDynamicText.labelStyleEditing = false;
                    if (
                      MainStore.getCurrentElementsValues[0].styleEditMode ==
                      "header"
                    ) {
                      MainStore.getCurrentElementsValues[0].selectedDynamicText =
                        null;
                    }
                  }
                }
                if (
                  MainStore.getCurrentElementsValues[0]?.selectedColumn &&
                  value != "main"
                ) {
                  MainStore.getCurrentElementsValues[0].selectedColumn = null;
                }
              },
              propertyName: "styleEditMode",
            });
          },
        },
      ],
      [
        {
          label: "Apply Style to Header",
          name: "applyStyleToHeader",
          isLabelled: true,
          labelDirection: "column",
          condtional: () =>
            MainStore.getCurrentElementsValues[0]?.type == "table" &&
            MainStore.getCurrentElementsValues[0].selectedColumn,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            // ElementStore available for future use
            // const ElementStore = useElementStore();
            makeFeild({
              name,
              ref,
              fieldtype: "Select",
              requiredData: [MainStore.getCurrentElementsValues[0]],
              reactiveObject: () =>
                MainStore.getCurrentElementsValues[0].selectedColumn,
              propertyName: "applyStyleToHeader",
              isStyle: false,
              options: () => [
                { label: "Yes", value: "Yes" },
                { label: "No", value: "No" },
              ],
              formatValue: (object, property, _isStyle) => {
                if (!object) return;
                return object[property] ? "Yes" : "No";
              },
              onChangeCallback: (value = null) => {
                if (
                  value &&
                  MainStore.getCurrentElementsValues[0].selectedColumn
                ) {
                  MainStore.getCurrentElementsValues[0].selectedColumn.applyStyleToHeader =
                    value === "Yes";
                  MainStore.frappeControls[name].$input.blur();
                }
              },
            });
          },
          flex: 1,
        },
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Rectangle Settings",
    sectionCondtional: () =>
      MainStore.getCurrentElementsId.length === 1 &&
      MainStore.getCurrentElementsValues[0]?.type == "rectangle",
    fields: [
      [
        colorStyleFrappeControl(
          "Background",
          "rectangleBackgroundColor",
          "backgroundColor",
        ),
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Enable Jinja Parsing",
    sectionCondtional: () =>
      MainStore.getCurrentElementsId.length === 1 &&
      MainStore.getCurrentElementsValues[0].type === "text" &&
      !MainStore.getCurrentElementsValues[0].isDynamic,
    fields: [
      [
        {
          label: "Render Jinja",
          name: "parseJinja",
          labelDirection: "column",
          condtional: () =>
            MainStore.getCurrentElementsId.length === 1 &&
            MainStore.getCurrentElementsValues[0].type === "text" &&
            !MainStore.getCurrentElementsValues[0].isDynamic,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name: name,
              ref: ref,
              fieldtype: "Select",
              requiredData: [MainStore.getCurrentElementsValues[0]],
              options: () => [
                { label: "Yes", value: "Yes" },
                { label: "No", value: "No" },
              ],
              formatValue: (object, property, _isStyle) => {
                if (!object) return;
                return object[property] ? "Yes" : "No";
              },
              onChangeCallback: (value = null) => {
                if (value && MainStore.getCurrentElementsValues[0]) {
                  MainStore.getCurrentElementsValues[0]["parseJinja"] =
                    value === "Yes";
                  MainStore.frappeControls[name].$input.blur();
                }
              },
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "parseJinja",
            });
          },
        },
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Text Tool",
    sectionCondtional: () => MainStore.activeControl === "text",
    fields: [
      [
        {
          label: "Text Control :",
          name: "textControlType",
          labelDirection: "column",
          condtional: () => MainStore.activeControl === "text",
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name: name,
              ref: ref,
              fieldtype: "Select",
              requiredData: [MainStore],
              options: () => [
                { label: "Dynamic Text", value: "dynamic" },
                { label: "Static Text", value: "static" },
              ],
              reactiveObject: MainStore,
              propertyName: "textControlType",
            });
          },
        },
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Font Settings",
    sectionCondtional: () =>
      (MainStore.getCurrentElementsId.length === 1 &&
        ["text", "table"].indexOf(
          MainStore.getCurrentElementsValues[0]?.type,
        ) != -1) ||
      (["table", "text"].indexOf(MainStore.activeControl) != -1 &&
        MainStore.getCurrentElementsId.length === 0),
    fields: [
      [
        {
          label: "Choose Element :",
          name: "textStyleEditMode",
          labelDirection: "column",
          condtional: () =>
            [
              MainStore.getCurrentElementsValues[0]?.type,
              MainStore.activeControl,
            ].indexOf("table") == -1,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name: name,
              ref: ref,
              fieldtype: "Select",
              requiredData: [MainStore],
              options: () => {
                if (
                  ("text" == MainStore.getCurrentElementsValues[0]?.type &&
                    MainStore.getCurrentElementsValues[0]?.isDynamic) ||
                  ("text" == MainStore.activeControl &&
                    MainStore.textControlType == "dynamic")
                )
                  return [
                    { label: "Label Element", value: "label" },
                    { label: "Main Element", value: "main" },
                  ];
                return [{ label: "Main Element", value: "main" }];
              },
              reactiveObject: () => {
                let styleClass = "staticText";
                if (MainStore.textControlType == "dynamic") {
                  styleClass = "dynamicText";
                }
                return (
                  MainStore.getCurrentElementsValues[0] ||
                  MainStore.globalStyles[styleClass]
                );
              },
              onChangeCallback: (_value) => {
                if (
                  MainStore.getCurrentElementsValues[0]?.selectedDynamicText
                ) {
                  if (
                    MainStore.getCurrentElementsValues[0].styleEditMode ==
                    "label"
                  ) {
                    MainStore.getCurrentElementsValues[0].selectedDynamicText.labelStyleEditing = true;
                  } else {
                    MainStore.getCurrentElementsValues[0].selectedDynamicText.labelStyleEditing = false;
                  }
                }
              },
              propertyName: "styleEditMode",
            });
          },
        },
      ],
      [
        {
          label: "Label Style :",
          name: "labelDisplayOptions",
          labelDirection: "column",
          condtional: () => {
            let styleClass = "table";
            if (MainStore.activeControl == "text") {
              if (MainStore.textControlType == "dynamic") {
                styleClass = "dynamicText";
              } else {
                styleClass = "staticText";
              }
            }
            let curObj =
              MainStore.getCurrentElementsValues[0] ||
              MainStore.globalStyles[styleClass];
            if (
              curObj.type == "table" ||
              (curObj.type == "text" && curObj.isDynamic)
            ) {
              return true;
            }
            return false;
          },
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name: name,
              ref: ref,
              fieldtype: "Select",
              requiredData: [MainStore],
              options: () => {
                return [
                  { label: "Inline", value: "standard" },
                  { label: "Row", value: "flexDynamicText" },
                  { label: "Column", value: "flexDirectionColumn" },
                ];
              },
              reactiveObject: () => {
                let styleClass = "table";
                if (MainStore.activeControl == "text") {
                  if (MainStore.textControlType == "dynamic") {
                    styleClass = "dynamicText";
                  } else {
                    styleClass = "staticText";
                  }
                }
                return (
                  MainStore.getCurrentElementsValues[0] ||
                  MainStore.globalStyles[styleClass]
                );
              },
              onChangeCallback: (_value) => {
                let object = MainStore.getCurrentElementsValues[0];
                if (!object) return;
                if (object.labelDisplayStyle == "standard") {
                  object.classes = object.classes.filter(
                    (cls) =>
                      ["flexDynamicText", "flexDirectionColumn"].indexOf(cls) ==
                      -1,
                  );
                } else if (object.labelDisplayStyle == "flexDynamicText") {
                  if (object.classes.indexOf("flexDynamicText") == -1) {
                    object.classes.push("flexDynamicText");
                  }
                  object.classes = object.classes.filter(
                    (cls) => cls != "flexDirectionColumn",
                  );
                } else if (object.labelDisplayStyle == "flexDirectionColumn") {
                  if (object.classes.indexOf("flexDynamicText") == -1) {
                    object.classes.push("flexDynamicText");
                  }
                  if (object.classes.indexOf("flexDirectionColumn") == -1) {
                    object.classes.push("flexDirectionColumn");
                  }
                }
              },
              propertyName: "labelDisplayStyle",
            });
          },
        },
      ],
      [
        {
          label: "Font",
          name: "googleFonts",
          isLabelled: true,
          labelDirection: "column",
          condtional: null,
          parentBorderBottom: true,
          parentBorderTop: true,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            makeFeild({
              name: name,
              ref: ref,
              fieldtype: "Autocomplete",
              requiredData: [MainStore.getGoogleFonts],
              options: () => MainStore.getGoogleFonts,
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "fontFamily",
              isStyle: true,
              isFontStyle: true,
              onChangeCallback: (value = null) => {
                MainStore.currentFonts.indexOf(value) == -1 &&
                  MainStore.currentFonts.push(value);
                if (!MainStore.frappeControls["fontWeight"]) return;
                MainStore.frappeControls["fontWeight"].df.options =
                  MainStore.getGoogleFontWeights(
                    MainStore.getStyleObject(true),
                  );
                MainStore.frappeControls["fontWeight"].refresh();
                if (
                  MainStore.frappeControls["fontWeight"].df.options.indexOf(
                    MainStore.frappeControls["fontWeight"].value,
                  ) == -1
                ) {
                  MainStore.frappeControls["fontWeight"].set_value(400);
                  MainStore.frappeControls["fontWeight"].refresh();
                }
              },
            });
          },
        },
        {
          label: "Weight",
          name: "fontWeight",
          isLabelled: true,
          labelDirection: "column",
          condtional: null,
          frappeControl: (ref, name) => {
            const MainStore = useMainStore();
            let styleClass = "table";
            if (MainStore.activeControl == "text") {
              if (MainStore.textControlType == "dynamic") {
                styleClass = "dynamicText";
              } else {
                styleClass = "staticText";
              }
            }
            makeFeild({
              name: name,
              ref: ref,
              fieldtype: "Select",
              requiredData: [
                MainStore.getCurrentElementsValues[0] ||
                  MainStore.globalStyles[styleClass],
              ],
              options: () => {
                return MainStore.getGoogleFontWeights(
                  MainStore.getStyleObject(true),
                );
              },
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              propertyName: "fontWeight",
              isStyle: true,
              isFontStyle: true,
            });
          },
        },
      ],
      [
        styleInputwithIcon("fontSize", 23, {
          padding: 5,
          saveWithUom: true,
          isFontStyle: true,
        }),
        styleInputwithIcon("lineHeight", 23, {
          padding: 5,
          isRaw: true,
          isFontStyle: true,
        }),
      ],
      [
        iconControl({
          name: "fontItalic",
          size: 28,
          padding: 8,
          margin: 0,
          parentBorderTop: true,
          parentBorderBottom: true,
          condtional: () => {
            if (
              !MainStore.frappeControls["googleFonts"] ||
              !MainStore.frappeControls["fontWeight"]
            )
              return false;
            let isItalicAvaiable =
              MainStore.fonts[
                MainStore.getCurrentStyle("fontFamily")
              ]?.[1].indexOf(
                parseInt(MainStore.getCurrentStyle("fontWeight")),
              ) != -1;
            if (
              !isItalicAvaiable &&
              MainStore.getCurrentStyle("fontStyle") == "italic"
            ) {
              MainStore.getStyleObject(true)["fontStyle"] = "normal";
            }
            return isItalicAvaiable;
          },
          onClick: () => {
            MainStore.getStyleObject(true)["fontStyle"] =
              MainStore.getCurrentStyle("fontStyle") == "italic"
                ? "normal"
                : "italic";
          },
          isActive: () => MainStore.getCurrentStyle("fontStyle") == "italic",
          onlyIcon: true,
          flex: "auto",
        }),
        iconControl({
          name: "fontUnderLine",
          size: 21,
          padding: 4,
          margin: 3.5,
          parentBorderTop: true,
          parentBorderBottom: true,
          isActive: () => {
            let field = {
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              isStyle: true,
              isFontStyle: true,
            };
            return (
              getConditonalObject(field)?.["textDecoration"] == "underline"
            );
          },
          onClick: () => {
            let field = {
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              isStyle: true,
              isFontStyle: true,
            };
            getConditonalObject(field)["textDecoration"] =
              getConditonalObject(field)?.["textDecoration"] == "underline"
                ? "none"
                : "underline";
          },
          onlyIcon: true,
          flex: "auto",
        }),
        styleInputwithIcon("letterSpacing", 31, {
          padding: 7,
          saveWithUom: true,
          isFontStyle: true,
          flex: 10,
        }),
      ],
      [
        textAlignIcons("textAlignLeft"),
        textAlignIcons("textAlignCenter"),
        textAlignIcons("textAlignRight"),
        textAlignIcons("textAlignJustify"),
      ],
      [
        colorStyleFrappeControl("Text", "textColor", "color", true),
        colorStyleFrappeControl(
          "Background",
          "textBackgroundColor",
          "backgroundColor",
          true,
        ),
      ],
    ],
  });
  // P6: Per-border color inputs
  const perBorderColor = (side, label) => {
    const propMap = {
      L: "borderLeftColor",
      R: "borderRightColor",
      T: "borderTopColor",
      B: "borderBottomColor",
    };
    const propertyName = propMap[side];
    return {
      label: label,
      name: propertyName,
      labelDirection: "column",
      isLabelled: true,
      condtional: () => {
        const style = getConditonalObject({
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          isStyle: true,
        });
        return (
          style?.borderLeftStyle !== "hidden" ||
          style?.borderRightStyle !== "hidden"
        );
      },
      frappeControl: (ref, name) => {
        makeFeild({
          name: name,
          ref: ref,
          fieldtype: "Color",
          requiredData: [MainStore.getCurrentElementsValues[0]],
          reactiveObject: () => MainStore.getCurrentElementsValues[0],
          propertyName: propertyName,
          isStyle: true,
        });
      },
    };
  };

  MainStore.propertiesPanel.push({
    title: "Border",
    sectionCondtional: () => MainStore.getCurrentElementsId.length === 1,
    fields: [
      // P2: Border Presets
      [
        {
          label: __("Presets"),
          name: "borderPresets",
          labelDirection: "row",
          isLabelled: false,
          condtional: () => true,
          frappeControl: (ref, _name) => {
            const container = document.createElement("div");
            container.className = "flex gap-1 flex-wrap";
            borderPresets.forEach((preset) => {
              const btn = document.createElement("button");
              btn.className = "btn btn-xs btn-default";
              btn.textContent = preset.name;
              btn.onclick = () => applyBorderPreset(preset);
              container.appendChild(btn);
            });
            ref?.appendChild(container);
          },
        },
      ],
      // Copy/Paste Borders (P5)
      [
        {
          label: __("Copy"),
          name: "copyBorder",
          labelDirection: "column",
          isLabelled: true,
          condtional: () => true,
          frappeControl: (ref, _name) => {
            const btn = document.createElement("button");
            btn.className = "btn btn-xs btn-default";
            btn.textContent = __("Copy");
            btn.onclick = copyBorderStyle;
            ref?.appendChild(btn);
          },
        },
        {
          label: __("Paste"),
          name: "pasteBorder",
          labelDirection: "column",
          isLabelled: true,
          condtional: () => copiedBorderStyle !== null,
          frappeControl: (ref, _name) => {
            const btn = document.createElement("button");
            btn.className = "btn btn-xs btn-default";
            btn.textContent = __("Paste");
            btn.onclick = pasteBorderStyle;
            ref?.appendChild(btn);
          },
        },
      ],
      // Main border controls
      [
        styleInputwithIcon("borderWidth", 24, {
          padding: 6,
          margin: 4,
          saveWithUom: true,
        }),
        styleInputwithIcon("borderRadius", 24, {
          padding: 7,
          margin: 4,
          saveWithUom: true,
        }),
      ],
      [
        borderStyleIcons("borderStyleSolid"),
        borderStyleIcons("borderStyleDotted"),
        borderStyleIcons("borderStyleDashed"),
      ],
      [
        borderWidthIcons("borderAll"),
        borderWidthIcons("borderLeftStyle"),
        borderWidthIcons("borderRightStyle"),
        borderWidthIcons("borderTopStyle"),
        borderWidthIcons("borderBottomStyle"),
      ],
      // P6: Per-border colors
      [perBorderColor("L", __("Left")), perBorderColor("R", __("Right"))],
      [perBorderColor("T", __("Top")), perBorderColor("B", __("Bottom"))],
      // P3: Visual Border Editor (3x3 grid in dialog)
      [createBorderGrid()],
      // P4: Drag Paint Controls
      [createDragPaintControls()],
      // Legacy combined border color
      {
        label: "Border Color",
        name: "borderColor",
        labelDirection: "column",
        isLabelled: true,
        condtional: () => {
          return parseFloatAndUnit(
            getConditonalObject({
              reactiveObject: () => MainStore.getCurrentElementsValues[0],
              isStyle: true,
              property: "borderWidth",
            }),
          ).value;
        },
        frappeControl: (ref, name) => {
          makeFeild({
            name: name,
            ref: ref,
            fieldtype: "Color",
            requiredData: [MainStore.getCurrentElementsValues[0]],
            reactiveObject: () => MainStore.getCurrentElementsValues[0],
            propertyName: "borderColor",
            isStyle: true,
          });
        },
      },
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Padding",
    sectionCondtional: () =>
      MainStore.getCurrentElementsId.length === 1 &&
      ["text", "image", "table"].indexOf(
        MainStore.getCurrentElementsValues[0].type,
      ) !== -1,
    fields: [
      [
        paddingInput("Top", "paddingTop", "paddingTop"),
        paddingInput("Bottom", "paddingBottom", "paddingBottom"),
      ],
      [
        paddingInput("Left", "paddingLeft", "paddingLeft"),
        paddingInput("Right", "paddingRight", "paddingRight"),
      ],
    ],
  });
  MainStore.propertiesPanel.push({
    title: "Barcode Settings",
    sectionCondtional: () =>
      (!MainStore.getCurrentElementsId.length &&
        MainStore.activeControl === "barcode") ||
      (MainStore.getCurrentElementsId.length === 1 &&
        MainStore.getCurrentElementsValues[0].type === "barcode"),
    fields: [
      {
        label: "Barcode Format",
        name: "barcodeFormat",
        isLabelled: true,
        condtional: null,
        frappeControl: (ref, name) => {
          const MainStore = useMainStore();
          const { barcodeFormats } = storeToRefs(MainStore);
          makeFeild({
            name: name,
            ref: ref,
            fieldtype: "Autocomplete",
            requiredData: [
              barcodeFormats,
              MainStore.getCurrentElementsValues[0] ||
                MainStore.globalStyles["barcode"],
            ],
            options: () => barcodeFormats.value,
            reactiveObject: () => {
              return (
                MainStore.getCurrentElementsValues[0] ||
                MainStore.globalStyles["barcode"]
              );
            },
            propertyName: "barcodeFormat",
          });
        },
      },
      [
        colorStyleFrappeControl(
          "Color",
          "barcodeColor",
          "barcodeColor",
          false,
          false,
        ),
        colorStyleFrappeControl(
          "Background",
          "barcodeBackgroundColor",
          "barcodeBackgroundColor",
          false,
          false,
        ),
      ],
    ],
  });
};
