/**
 * Client-side data transformations for chart rendering.
 *
 * Handles group-by aggregation, sorting, and field type detection
 * so that all chart types (not just metric) can aggregate data.
 */

export type AggregationType = "sum" | "count" | "avg" | "min" | "max";
export type SortDirection = "asc" | "desc";

export interface TransformOptions {
  /** Field to group rows by (becomes the x-axis category) */
  groupBy?: string;
  /** Field to aggregate (y-axis value) */
  valueField?: string;
  /** Aggregation function */
  aggregation?: AggregationType;
  /** Field to sort by */
  sortField?: string;
  /** Sort direction */
  sortDirection?: SortDirection;
  /** Max rows to return after transformation */
  limit?: number;
}

/**
 * Group rows by a field and aggregate a value field.
 *
 * Example: groupBy="campaign", valueField="reach", aggregation="sum"
 * Input:  [{campaign:"A", reach:100}, {campaign:"A", reach:200}, {campaign:"B", reach:50}]
 * Output: [{campaign:"A", reach:300}, {campaign:"B", reach:50}]
 */
function groupAndAggregate(
  data: Record<string, unknown>[],
  groupBy: string,
  valueField: string,
  aggregation: AggregationType,
): Record<string, unknown>[] {
  const groups = new Map<string, { rows: Record<string, unknown>[]; sum: number; count: number; min: number; max: number }>();

  for (const row of data) {
    const key = String(row[groupBy] ?? "");
    if (!groups.has(key)) {
      groups.set(key, { rows: [], sum: 0, count: 0, min: Infinity, max: -Infinity });
    }
    const g = groups.get(key)!;
    const val = Number(row[valueField] ?? 0);
    g.rows.push(row);
    g.sum += isNaN(val) ? 0 : val;
    g.count += 1;
    g.min = Math.min(g.min, isNaN(val) ? Infinity : val);
    g.max = Math.max(g.max, isNaN(val) ? -Infinity : val);
  }

  const result: Record<string, unknown>[] = [];
  for (const [key, g] of groups) {
    let value: number;
    switch (aggregation) {
      case "count":
        value = g.count;
        break;
      case "avg":
        value = g.count > 0 ? g.sum / g.count : 0;
        break;
      case "min":
        value = g.min === Infinity ? 0 : g.min;
        break;
      case "max":
        value = g.max === -Infinity ? 0 : g.max;
        break;
      default: // sum
        value = g.sum;
        break;
    }
    // Preserve all fields from the first row in the group, override the value field
    result.push({ ...g.rows[0], [groupBy]: key, [valueField]: value });
  }

  return result;
}

/**
 * Sort data by a field.
 */
function sortData(
  data: Record<string, unknown>[],
  sortField: string,
  direction: SortDirection,
): Record<string, unknown>[] {
  return [...data].sort((a, b) => {
    const aVal = a[sortField];
    const bVal = b[sortField];

    // Numeric comparison
    const aNum = Number(aVal);
    const bNum = Number(bVal);
    if (!isNaN(aNum) && !isNaN(bNum)) {
      return direction === "asc" ? aNum - bNum : bNum - aNum;
    }

    // String comparison
    const aStr = String(aVal ?? "");
    const bStr = String(bVal ?? "");
    return direction === "asc"
      ? aStr.localeCompare(bStr)
      : bStr.localeCompare(aStr);
  });
}

/**
 * Apply transformations to chart data.
 *
 * This is the main entry point — call from ChartRenderer before passing
 * data to individual chart components.
 */
export function transformData(
  data: Record<string, unknown>[],
  options: TransformOptions,
): Record<string, unknown>[] {
  if (!data.length) return data;

  let result = data;

  // Apply group-by aggregation
  if (options.groupBy && options.valueField && options.aggregation) {
    result = groupAndAggregate(
      result,
      options.groupBy,
      options.valueField,
      options.aggregation,
    );
  }

  // Apply sorting
  if (options.sortField) {
    result = sortData(result, options.sortField, options.sortDirection ?? "asc");
  }

  // Apply limit
  if (options.limit && options.limit > 0) {
    result = result.slice(0, options.limit);
  }

  return result;
}

/**
 * Detect field types from data sample.
 * Returns a map of field name → inferred type.
 */
export function detectFieldTypes(
  data: Record<string, unknown>[],
): Map<string, "number" | "date" | "string"> {
  const types = new Map<string, "number" | "date" | "string">();
  if (!data.length) return types;

  // Sample up to 10 rows
  const sample = data.slice(0, 10);
  const fields = Object.keys(data[0]);

  for (const field of fields) {
    const values = sample.map((r) => r[field]).filter((v) => v != null && v !== "");

    if (values.length === 0) {
      types.set(field, "string");
      continue;
    }

    // Check if numeric
    const allNumeric = values.every((v) => !isNaN(Number(v)));
    if (allNumeric) {
      types.set(field, "number");
      continue;
    }

    // Check if date-like (ISO dates, common date patterns)
    const datePattern = /^\d{4}-\d{2}-\d{2}|^\d{1,2}\/\d{1,2}\/\d{2,4}|^\w+ \d{1,2},? \d{4}/;
    const allDates = values.every((v) => datePattern.test(String(v)));
    if (allDates) {
      types.set(field, "date");
      continue;
    }

    types.set(field, "string");
  }

  return types;
}
