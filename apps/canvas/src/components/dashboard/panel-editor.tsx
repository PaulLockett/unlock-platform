"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import {
  X,
  Check,
  BarChart3,
  LineChart,
  PieChart,
  AreaChart,
  Filter,
  Table,
  Hash,
  ArrowUpDown,
  Layers,
  Database,
} from "lucide-react";
import type { Panel, ChartType, ChartConfig, PanelQueryConfig } from "@/types/platform";
import ChartRenderer from "@/components/charts/chart-renderer";
import { detectFieldTypes } from "@/lib/transform-data";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PanelEditorProps {
  panel: Panel;
  panelData: Record<string, unknown>[];
  shareToken: string;
  schemaFields: string[];
  availableSources?: { key: string; record_count: number; sample_fields: string[] }[];
  onApply: (updatedPanel: Panel) => void;
  onCancel: () => void;
}

type TabId = "data" | "display" | "axes" | "transform";


// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TABS: { id: TabId; label: string }[] = [
  { id: "display", label: "Display" },
  { id: "axes", label: "Axes" },
  { id: "data", label: "Data" },
  { id: "transform", label: "Transform" },
];

const CHART_TYPES: { type: ChartType; label: string; icon: React.ReactNode }[] = [
  { type: "bar", label: "Bar", icon: <BarChart3 className="w-4 h-4" /> },
  { type: "line", label: "Line", icon: <LineChart className="w-4 h-4" /> },
  { type: "pie", label: "Pie", icon: <PieChart className="w-4 h-4" /> },
  { type: "area", label: "Area", icon: <AreaChart className="w-4 h-4" /> },
  { type: "funnel", label: "Funnel", icon: <Filter className="w-4 h-4" /> },
  { type: "table", label: "Table", icon: <Table className="w-4 h-4" /> },
  { type: "metric", label: "Metric", icon: <Hash className="w-4 h-4" /> },
];

const WIDTH_OPTIONS = [
  { label: "Small", w: 2 },
  { label: "Medium", w: 3 },
  { label: "Large", w: 6 },
];

const HEIGHT_OPTIONS = [
  { label: "Short", h: 1 },
  { label: "Medium", h: 2 },
  { label: "Tall", h: 3 },
];

const AGGREGATIONS = ["sum", "count", "avg", "min", "max"];

const TIME_RANGES = [
  { label: "Last 7 days", days: 7 },
  { label: "Last 30 days", days: 30 },
  { label: "Last 90 days", days: 90 },
  { label: "Last 365 days", days: 365 },
  { label: "All time", days: 0 },
  { label: "Custom", days: -1 },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function FieldSelect({
  value,
  onChange,
  label,
  placeholder,
  fields,
  fieldTypes,
  allowNone,
}: {
  value: string;
  onChange: (v: string) => void;
  label: string;
  placeholder: string;
  fields: string[];
  fieldTypes?: Map<string, string>;
  allowNone?: boolean;
}) {
  return (
    <div>
      <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
        {label}
      </label>
      {fields.length > 0 ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors appearance-none"
        >
          <option value="">{allowNone ? "— None —" : "— Select field —"}</option>
          {fields.map((f) => (
            <option key={f} value={f}>
              {f}
              {fieldTypes?.has(f) ? ` (${fieldTypes.get(f)})` : ""}
            </option>
          ))}
        </select>
      ) : (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
        />
      )}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[9px] tracking-widest text-white/25 uppercase font-mono pt-2">
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function PanelEditor({
  panel,
  panelData,
  shareToken,
  schemaFields,
  availableSources = [],
  onApply,
  onCancel,
}: PanelEditorProps) {
  const [activeTab, setActiveTab] = useState<TabId>("display");

  // Display config
  const [title, setTitle] = useState(panel.title);
  const [chartType, setChartType] = useState<ChartType>(panel.chart_type);
  const [width, setWidth] = useState(panel.position.w);
  const [height, setHeight] = useState(panel.position.h || 1);

  // Axes config
  const [xAxis, setXAxis] = useState(panel.chart_config.x_axis ?? "");
  const [yAxis, setYAxis] = useState(
    panel.chart_config.y_axis ?? panel.chart_config.value_field ?? "",
  );
  const [groupBy, setGroupBy] = useState(panel.chart_config.group_by ?? "");

  // Data config
  const [sourceKey, setSourceKey] = useState(panel.query_config.source_key ?? "");
  const [channelKey, setChannelKey] = useState(panel.query_config.channel_key ?? "");
  const [timeRange, setTimeRange] = useState<number>(-1); // -1 = custom
  const [since, setSince] = useState(panel.query_config.since ?? "");
  const [until, setUntil] = useState(panel.query_config.until ?? "");

  // Transform config
  const [aggregation, setAggregation] = useState(panel.chart_config.aggregation ?? "sum");
  const [sortField, setSortField] = useState(panel.chart_config.sort_by ?? "");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">(
    panel.chart_config.sort_direction ?? "asc",
  );
  const [stacked, setStacked] = useState(panel.chart_config.stacked ?? false);

  // Thresholds
  const [warningValue, setWarningValue] = useState(
    panel.chart_config.warning_threshold?.toString() ?? "",
  );
  const [criticalValue, setCriticalValue] = useState(
    panel.chart_config.critical_threshold?.toString() ?? "",
  );

  // Live preview data
  const [previewData, setPreviewData] = useState<Record<string, unknown>[]>(panelData);
  const [previewLoading, setPreviewLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Detect field types from live data
  const fieldTypes = useMemo(() => detectFieldTypes(previewData), [previewData]);

  // Auto-detect available fields: merge schema fields + fields from live data
  const allFields = useMemo(() => {
    const fromData = previewData.length > 0 ? Object.keys(previewData[0]) : [];
    const merged = new Set([...schemaFields, ...fromData]);
    return [...merged].sort();
  }, [schemaFields, previewData]);

  // Numeric fields only (for y-axis, value fields)
  const numericFields = useMemo(() => {
    return allFields.filter((f) => fieldTypes.get(f) === "number");
  }, [allFields, fieldTypes]);

  // When selecting a source, update sample fields
  const selectedSource = availableSources.find((s) => s.key === sourceKey);

  // Merge sample fields from selected source into available fields
  const effectiveFields = useMemo(() => {
    const fromSource = selectedSource?.sample_fields ?? [];
    const merged = new Set([...allFields, ...fromSource]);
    return [...merged].sort();
  }, [allFields, selectedSource]);

  // Time range helper
  useEffect(() => {
    if (timeRange === -1) return; // custom — don't override
    if (timeRange === 0) {
      // all time
      setSince("");
      setUntil("");
      return;
    }
    const now = new Date();
    const start = new Date(now);
    start.setDate(start.getDate() - timeRange);
    setSince(start.toISOString().split("T")[0]);
    setUntil(now.toISOString().split("T")[0]);
  }, [timeRange]);

  // Build a live Panel from current editor state
  const buildPreviewPanel = useCallback((): Panel => {
    const isMetricOrPie = chartType === "metric" || chartType === "pie";
    const chartConfig: ChartConfig = isMetricOrPie
      ? {
          value_field: yAxis || undefined,
          label: title,
          aggregation,
        }
      : {
          x_axis: xAxis || undefined,
          y_axis: yAxis || undefined,
          group_by: groupBy || undefined,
          aggregation,
          sort_by: sortField || undefined,
          sort_direction: sortDirection,
          stacked,
        };

    if (chartType === "table") {
      chartConfig.columns = effectiveFields.length > 0
        ? [xAxis, yAxis, groupBy].filter(Boolean)
        : undefined;
      chartConfig.sort_by = sortField || undefined;
      chartConfig.sort_direction = sortDirection;
    }

    if (warningValue) chartConfig.warning_threshold = parseFloat(warningValue);
    if (criticalValue) chartConfig.critical_threshold = parseFloat(criticalValue);

    return {
      id: panel.id,
      title,
      chart_type: chartType,
      position: { ...panel.position, w: Math.min(width, 6), h: height },
      chart_config: chartConfig,
      query_config: {
        source_key: sourceKey || null,
        channel_key: channelKey || null,
        since: since || null,
        until: until || null,
      },
    };
  }, [
    title, chartType, width, height, xAxis, yAxis, groupBy, aggregation,
    sortField, sortDirection, stacked, channelKey, sourceKey, since, until,
    panel.id, panel.position, effectiveFields, warningValue, criticalValue,
  ]);

  // Live data fetch with debounce
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setPreviewLoading(true);
      try {
        const queryConfig: PanelQueryConfig = {
          source_key: sourceKey || null,
          channel_key: channelKey || null,
          since: since || null,
          until: until || null,
        };
        const res = await fetch("/api/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            share_token: shareToken,
            source_key: queryConfig.source_key,
            channel_key: queryConfig.channel_key,
            engagement_type: null,
            since: queryConfig.since,
            until: queryConfig.until,
            limit: 1000,
            offset: 0,
          }),
        });
        const data = await res.json();
        setPreviewData(data.success ? data.records : []);
      } catch {
        setPreviewData([]);
      } finally {
        setPreviewLoading(false);
      }
    }, 500);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [shareToken, sourceKey, channelKey, since, until]);

  const handleApply = () => {
    onApply(buildPreviewPanel());
  };

  const previewPanel = buildPreviewPanel();

  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center">
      {/* Scrim overlay */}
      <div
        className="absolute inset-0 bg-charcoal/70 backdrop-blur-[2px]"
        onClick={onCancel}
      />

      {/* Editor panel */}
      <div className="relative w-full max-w-6xl mx-4 bg-charcoal-light border border-white/10 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Corner accents */}
        <div className="absolute -top-px -left-px w-8 h-8 border-t-2 border-l-2 border-coral" />
        <div className="absolute -top-px -right-px w-8 h-8 border-t-2 border-r-2 border-coral" />
        <div className="absolute -bottom-px -left-px w-8 h-8 border-b-2 border-l-2 border-coral" />
        <div className="absolute -bottom-px -right-px w-8 h-8 border-b-2 border-r-2 border-coral" />

        {/* Header */}
        <div className="flex items-center justify-between px-8 py-5 border-b border-white/10 shrink-0">
          <div className="flex items-center gap-4">
            <span className="px-3 py-1 bg-coral/10 text-coral text-[9px] tracking-widest uppercase font-mono border border-coral/20">
              Editing Panel
            </span>
            <span className="text-sm font-mono text-offwhite">{title || "Untitled"}</span>
            {previewData.length > 0 && (
              <span className="text-[9px] font-mono text-white/25 tracking-wider">
                {previewData.length} rows
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onCancel}
              className="flex items-center gap-1.5 px-4 py-1.5 text-[10px] tracking-widest uppercase font-mono text-white/40 hover:text-white border border-white/10 hover:border-white/20 transition-colors"
            >
              <X className="w-3 h-3" />
              Cancel
            </button>
            <button
              onClick={handleApply}
              className="flex items-center gap-1.5 px-4 py-1.5 text-[10px] tracking-widest uppercase font-mono bg-coral text-charcoal hover:bg-coral/90 transition-colors"
            >
              <Check className="w-3 h-3" />
              Apply Changes
            </button>
          </div>
        </div>

        {/* Body: Config (left) + Preview (right) */}
        <div className="flex flex-1 min-h-0 overflow-hidden">
          {/* Left: Tabbed config */}
          <div className="w-5/12 border-r border-white/10 flex flex-col overflow-hidden">
            {/* Tab bar */}
            <div className="flex border-b border-white/10 shrink-0">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 py-3 text-[10px] tracking-widest uppercase font-mono transition-colors ${
                    activeTab === tab.id
                      ? "text-coral border-b-2 border-coral"
                      : "text-white/30 hover:text-white/60"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {/* ============================================================ */}
              {/* DISPLAY TAB                                                   */}
              {/* ============================================================ */}
              {activeTab === "display" && (
                <>
                  {/* Title */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Panel Title
                    </label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Daily Reach"
                      className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
                    />
                  </div>

                  {/* Chart type */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Chart Type
                    </label>
                    <div className="grid grid-cols-4 gap-2">
                      {CHART_TYPES.map(({ type, label, icon }) => (
                        <button
                          key={type}
                          onClick={() => setChartType(type)}
                          className={`flex flex-col items-center gap-1 p-2.5 border transition-colors ${
                            chartType === type
                              ? "border-coral bg-coral/10 text-coral"
                              : "border-white/10 text-white/30 hover:text-white/60 hover:border-white/20"
                          }`}
                        >
                          {icon}
                          <span className="text-[8px] tracking-widest uppercase font-mono">
                            {label}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Width */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Panel Width
                    </label>
                    <div className="flex gap-2">
                      {WIDTH_OPTIONS.map(({ label, w }) => (
                        <button
                          key={w}
                          onClick={() => setWidth(w)}
                          className={`flex-1 py-2 text-[10px] tracking-widest uppercase font-mono border transition-colors ${
                            width === w
                              ? "border-coral bg-coral/10 text-coral"
                              : "border-white/10 text-white/30 hover:text-white/60 hover:border-white/20"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Height */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Panel Height
                    </label>
                    <div className="flex gap-2">
                      {HEIGHT_OPTIONS.map(({ label, h }) => (
                        <button
                          key={h}
                          onClick={() => setHeight(h)}
                          className={`flex-1 py-2 text-[10px] tracking-widest uppercase font-mono border transition-colors ${
                            height === h
                              ? "border-coral bg-coral/10 text-coral"
                              : "border-white/10 text-white/30 hover:text-white/60 hover:border-white/20"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Stacked toggle (bar/area only) */}
                  {(chartType === "bar" || chartType === "area") && (
                    <div className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2 text-[10px] tracking-widest text-white/40 uppercase font-mono">
                        <Layers className="w-3.5 h-3.5" />
                        Stacked
                      </div>
                      <button
                        onClick={() => setStacked(!stacked)}
                        className={`w-10 h-5 rounded-full transition-colors relative ${
                          stacked ? "bg-coral" : "bg-white/10"
                        }`}
                      >
                        <div
                          className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-transform ${
                            stacked ? "translate-x-5" : "translate-x-0.5"
                          }`}
                        />
                      </button>
                    </div>
                  )}
                </>
              )}

              {/* ============================================================ */}
              {/* AXES TAB                                                      */}
              {/* ============================================================ */}
              {activeTab === "axes" && (
                <>
                  {effectiveFields.length > 0 && (
                    <div className="flex items-center gap-2 px-3 py-2 bg-white/[0.02] border border-white/5 text-[9px] font-mono text-white/30 tracking-wider">
                      <Database className="w-3 h-3" />
                      {effectiveFields.length} fields detected
                      {numericFields.length > 0 && (
                        <span className="text-coral">
                          ({numericFields.length} numeric)
                        </span>
                      )}
                    </div>
                  )}

                  {chartType === "metric" || chartType === "pie" ? (
                    <>
                      <FieldSelect
                        value={yAxis}
                        onChange={setYAxis}
                        label="Value Field"
                        placeholder="reach"
                        fields={numericFields.length > 0 ? numericFields : effectiveFields}
                        fieldTypes={fieldTypes}
                      />
                      {chartType === "pie" && (
                        <FieldSelect
                          value={xAxis}
                          onChange={setXAxis}
                          label="Label Field"
                          placeholder="category"
                          fields={effectiveFields}
                          fieldTypes={fieldTypes}
                        />
                      )}
                    </>
                  ) : (
                    <>
                      <FieldSelect
                        value={xAxis}
                        onChange={setXAxis}
                        label="X-Axis Field"
                        placeholder="date"
                        fields={effectiveFields}
                        fieldTypes={fieldTypes}
                      />
                      <FieldSelect
                        value={yAxis}
                        onChange={setYAxis}
                        label="Y-Axis Field"
                        placeholder="reach"
                        fields={numericFields.length > 0 ? numericFields : effectiveFields}
                        fieldTypes={fieldTypes}
                      />
                      <FieldSelect
                        value={groupBy}
                        onChange={setGroupBy}
                        label="Group By (optional)"
                        placeholder=""
                        fields={effectiveFields}
                        fieldTypes={fieldTypes}
                        allowNone
                      />
                    </>
                  )}
                </>
              )}

              {/* ============================================================ */}
              {/* DATA TAB                                                      */}
              {/* ============================================================ */}
              {activeTab === "data" && (
                <>
                  {/* Source selector */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Data Source
                    </label>
                    {availableSources.length > 0 ? (
                      <select
                        value={sourceKey}
                        onChange={(e) => setSourceKey(e.target.value)}
                        className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors appearance-none"
                      >
                        <option value="">— Auto-detect —</option>
                        {availableSources.map((s) => (
                          <option key={s.key} value={s.key}>
                            {s.key} ({s.record_count} records)
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={sourceKey}
                        onChange={(e) => setSourceKey(e.target.value)}
                        placeholder="Leave empty to auto-detect"
                        className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
                      />
                    )}
                    {selectedSource && (
                      <div className="mt-2 text-[9px] font-mono text-white/25 tracking-wider">
                        Fields: {selectedSource.sample_fields.join(", ")}
                      </div>
                    )}
                  </div>

                  {/* Time range presets */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Time Range
                    </label>
                    <div className="grid grid-cols-3 gap-1.5">
                      {TIME_RANGES.map(({ label, days }) => (
                        <button
                          key={label}
                          onClick={() => setTimeRange(days)}
                          className={`py-2 text-[9px] tracking-widest uppercase font-mono border transition-colors ${
                            timeRange === days
                              ? "border-coral bg-coral/10 text-coral"
                              : "border-white/10 text-white/30 hover:text-white/60 hover:border-white/20"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Custom date range (shown when "Custom" is selected or dates are manually set) */}
                  {(timeRange === -1 || since || until) && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                          Since
                        </label>
                        <input
                          type="date"
                          value={since}
                          onChange={(e) => {
                            setSince(e.target.value);
                            setTimeRange(-1);
                          }}
                          className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                          Until
                        </label>
                        <input
                          type="date"
                          value={until}
                          onChange={(e) => {
                            setUntil(e.target.value);
                            setTimeRange(-1);
                          }}
                          className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
                        />
                      </div>
                    </div>
                  )}

                  <SectionLabel>Filters</SectionLabel>

                  {/* Channel Key */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Channel Key
                    </label>
                    <input
                      type="text"
                      value={channelKey}
                      onChange={(e) => setChannelKey(e.target.value)}
                      placeholder="e.g. twitter, linkedin"
                      className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
                    />
                  </div>
                </>
              )}

              {/* ============================================================ */}
              {/* TRANSFORM TAB                                                 */}
              {/* ============================================================ */}
              {activeTab === "transform" && (
                <>
                  {/* Aggregation */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Aggregation
                    </label>
                    <div className="flex gap-1.5 flex-wrap">
                      {AGGREGATIONS.map((agg) => (
                        <button
                          key={agg}
                          onClick={() => setAggregation(agg)}
                          className={`px-3 py-2 text-[10px] tracking-widest uppercase font-mono border transition-colors ${
                            aggregation === agg
                              ? "border-coral bg-coral/10 text-coral"
                              : "border-white/10 text-white/30 hover:text-white/60 hover:border-white/20"
                          }`}
                        >
                          {agg}
                        </button>
                      ))}
                    </div>
                    <p className="mt-2 text-[9px] font-mono text-white/20 tracking-wider">
                      Groups by x-axis field and aggregates y-axis values
                    </p>
                  </div>

                  <SectionLabel>Sort</SectionLabel>

                  {/* Sort field */}
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <FieldSelect
                        value={sortField}
                        onChange={setSortField}
                        label="Sort By"
                        placeholder=""
                        fields={effectiveFields}
                        fieldTypes={fieldTypes}
                        allowNone
                      />
                    </div>
                    <div className="w-28 flex flex-col">
                      <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                        Direction
                      </label>
                      <button
                        onClick={() =>
                          setSortDirection(sortDirection === "asc" ? "desc" : "asc")
                        }
                        className="flex items-center justify-center gap-1.5 flex-1 border border-white/10 text-white/40 hover:text-white hover:border-white/20 transition-colors text-[10px] tracking-widest uppercase font-mono"
                      >
                        <ArrowUpDown className="w-3 h-3" />
                        {sortDirection}
                      </button>
                    </div>
                  </div>

                  <SectionLabel>Thresholds</SectionLabel>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                        Warning
                      </label>
                      <div className="relative">
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-amber-400" />
                        <input
                          type="number"
                          value={warningValue}
                          onChange={(e) => setWarningValue(e.target.value)}
                          placeholder="e.g. 1000"
                          className="w-full bg-charcoal border border-white/10 pl-8 pr-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                        Critical
                      </label>
                      <div className="relative">
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-red-500" />
                        <input
                          type="number"
                          value={criticalValue}
                          onChange={(e) => setCriticalValue(e.target.value)}
                          placeholder="e.g. 500"
                          className="w-full bg-charcoal border border-white/10 pl-8 pr-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Right: Live preview */}
          <div className="w-7/12 flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10 shrink-0 flex items-center justify-between">
              <div>
                <div className="text-[10px] tracking-widest text-coral uppercase font-mono">
                  Live Preview
                </div>
                <div className="text-xl font-display text-sage uppercase mt-1">
                  {title || "Untitled Panel"}
                </div>
              </div>
              {previewData.length > 0 && (
                <div className="text-[9px] font-mono text-white/20 tracking-wider text-right">
                  <div>{previewData.length} records</div>
                  <div>{effectiveFields.length} fields</div>
                </div>
              )}
            </div>
            <div className="flex-1 p-6 min-h-[400px]">
              <ChartRenderer
                panel={previewPanel}
                data={previewData}
                loading={previewLoading}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
