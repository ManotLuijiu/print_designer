import { parseFloatAndUnit } from "../utils";
/**
 *
 * @param {{inputString: String, defaultInputUnit: 'px'|'mm'|'cm'|'in',  convertionUnit: 'px'|'mm'|'cm'|'in'}} `px is considered by default for defaultInputUnit and convertionUnit`
 * @example
 * useChangeValueUnit("210 mm", "in") : {
 *  value: 8.26771653553125,
 *  unit: in,
 *  error: false
 * }
 * @returns {{value: Number, unit: String, error: Boolean}} converted value based on unit parameters
 */
export function useChangeValueUnit({
  inputString,
  defaultInputUnit = "px",
  convertionUnit = "px",
}) {
  // Handle undefined/null input
  if (inputString == null || inputString === "") {
    return {
      value: 0,
      unit: convertionUnit,
      error: true,
    };
  }

  const parsedInput = parseFloatAndUnit(inputString, defaultInputUnit);

  // Handle parse errors
  if (!parsedInput || parsedInput.value == null || isNaN(parsedInput.value)) {
    return {
      value: 0,
      unit: convertionUnit,
      error: true,
    };
  }

  const UnitValues = Object.freeze({
    px: 1,
    mm: 3.7795275591,
    cm: 37.795275591,
    in: 96,
  });
  const converstionFactor = Object.freeze({
    from_px: {
      to_px: 1,
      to_mm: UnitValues.px / UnitValues.mm,
      to_cm: UnitValues.px / UnitValues.cm,
      to_in: UnitValues.px / UnitValues.in,
    },
    from_mm: {
      to_mm: 1,
      to_px: UnitValues.mm / UnitValues.px,
      to_cm: UnitValues.mm / UnitValues.cm,
      to_in: UnitValues.mm / UnitValues.in,
    },
    from_cm: {
      to_cm: 1,
      to_px: UnitValues.cm / UnitValues.px,
      to_mm: UnitValues.cm / UnitValues.mm,
      to_in: UnitValues.cm / UnitValues.in,
    },
    from_in: {
      to_in: 1,
      to_px: UnitValues.in / UnitValues.px,
      to_mm: UnitValues.in / UnitValues.mm,
      to_cm: UnitValues.in / UnitValues.cm,
    },
  });

  const fromUnit = `from_${parsedInput.unit}`;
  const toUnit = `to_${convertionUnit}`;

  // Check if the conversion paths exist
  if (
    !converstionFactor[fromUnit] ||
    converstionFactor[fromUnit][toUnit] == null
  ) {
    return {
      value: parsedInput.value,
      unit: convertionUnit,
      error: false,
    };
  }

  return {
    value: parsedInput.value * converstionFactor[fromUnit][toUnit],
    unit: convertionUnit,
    error: false,
  };
}
