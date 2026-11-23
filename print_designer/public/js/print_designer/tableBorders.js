const sides = ["Top", "Right", "Bottom", "Left"];

const isVisiblePattern = (pattern) =>
  pattern && !["none", "hidden"].includes(pattern);

const borderProperties = {
  borderColor: sides.map((side) => `border${side}Color`),
  borderStyle: sides.map((side) => `border${side}Style`),
};

function existingBorderProperties(style, property) {
  return [property, ...borderProperties[property]].filter(
    (key) =>
      style?.[key] != null &&
      (property === "borderColor" || isVisiblePattern(style[key])),
  );
}

export function getLinkedColumnHeaderStyle(column) {
  if (!column.applyStyleToHeader) return;
  const style = { ...column.style, ...column.linkedHeaderBorderStyle };
  if (style.backgroundColor === "") delete style.backgroundColor;
  return style;
}

export function setTableBorderValue(table, style, property, value) {
  style[property] = value;
  if (table.selectedColumn) {
    const column = table.selectedColumn;
    if (column.applyStyleToHeader) {
      for (const headerStyle of [
        column.linkedHeaderBorderStyle,
        column.headerBorderStyle,
      ]) {
        for (const key of existingBorderProperties(headerStyle, property)) {
          headerStyle[key] = value;
        }
      }
    }
    return;
  }
  if (!["main", "header"].includes(table.styleEditMode)) return;

  for (const key of existingBorderProperties(style, property)) {
    style[key] = value;
  }
  if (table.styleEditMode === "main") {
    for (const key of existingBorderProperties(table.altStyle, property)) {
      table.altStyle[key] = value;
    }
  }

  for (const column of table.columns) {
    const sharedStyle = column.applyStyleToHeader ? column.style : null;
    if (table.styleEditMode === "header") {
      const linkedStyle = getLinkedColumnHeaderStyle(column);
      const keys = new Set([
        ...existingBorderProperties(linkedStyle, property),
        ...existingBorderProperties(column.headerBorderStyle, property),
      ]);
      for (const key of keys) {
        column.headerBorderStyle ??= {};
        const edge = column.headerBorderStyle[key] ?? linkedStyle?.[key];
        if (property === "borderColor" || isVisiblePattern(edge)) {
          column.headerBorderStyle[key] = value;
        }
      }
      continue;
    }

    for (const key of existingBorderProperties(column.style, property)) {
      if (sharedStyle) {
        column.linkedHeaderBorderStyle ??= {};
        column.linkedHeaderBorderStyle[key] ??= sharedStyle[key];
      }
      column.style[key] = value;
    }
  }
}

function getTableBorderStyles(table, fallbackStyle) {
  if (table.selectedColumn) {
    return [
      { ...fallbackStyle, ...table.style, ...table.selectedColumn.style },
    ];
  }
  if (table.styleEditMode === "header") {
    return table.columns.map((column) => ({
      ...fallbackStyle,
      ...table.headerStyle,
      ...getLinkedColumnHeaderStyle(column),
      ...column.headerBorderStyle,
    }));
  }
  if (table.styleEditMode === "main") {
    return table.columns.flatMap((column) => [
      { ...fallbackStyle, ...table.style, ...column.style },
      { ...fallbackStyle, ...table.style, ...table.altStyle, ...column.style },
    ]);
  }
  return [
    {
      ...fallbackStyle,
      ...table[table.styleEditMode === "alt" ? "altStyle" : "labelStyle"],
    },
  ];
}

export function getTableBorderPattern(table, fallbackStyle) {
  if (table.borderPreset === "no-grid") return;
  const styles = getTableBorderStyles(table, fallbackStyle);
  const patterns = new Set(
    styles.flatMap((style) =>
      sides
        .map((side) =>
          table.borderPreset
            ? isVisiblePattern(style.borderStyle)
              ? style.borderStyle
              : "solid"
            : style[`border${side}Style`] || style.borderStyle,
        )
        .filter(isVisiblePattern),
    ),
  );
  return patterns.size === 1 ? [...patterns][0] : undefined;
}

export function getTableBorderColor(table, fallbackStyle) {
  const styles = getTableBorderStyles(table, fallbackStyle);
  const colors = new Set(
    styles.flatMap((style) =>
      sides
        .map((side) => style[`border${side}Color`] ?? style.borderColor)
        .filter(Boolean)
        .map((color) => color.toUpperCase()),
    ),
  );
  return colors.size === 1 ? [...colors][0] : "";
}

export function getTableCellStyles(
  preset,
  {
    index,
    columnCount,
    isHeader = false,
    isLastRow = false,
    isPadding = false,
  },
  ...styles
) {
  if (!preset) return styles;
  const pattern = styles.reduce(
    (value, style) =>
      isVisiblePattern(style?.borderStyle) ? style.borderStyle : value,
    "solid",
  );
  const outline = preset === "outline" || preset === "full-grid";
  const rowLines = preset === "horizontal" || preset === "full-grid";
  const edges = {
    borderTopStyle: isHeader && (outline || rowLines) ? pattern : "none",
    borderRightStyle: outline && index === columnCount - 1 ? pattern : "none",
    borderBottomStyle:
      (isLastRow && (outline || rowLines)) || (rowLines && !isPadding)
        ? pattern
        : "none",
    borderLeftStyle:
      (outline && index === 0) || preset === "full-grid" ? pattern : "none",
  };
  const cellStyle = Object.assign({}, ...styles);
  // Vue keeps the first position of a repeated key when merging styles.
  // Reinsert the preset edges after all saved border shorthands.
  for (const edge of Object.keys(edges)) {
    delete cellStyle[edge];
  }
  return Object.assign(cellStyle, edges);
}
