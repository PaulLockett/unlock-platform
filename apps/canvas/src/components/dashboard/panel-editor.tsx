"use client";

import { useState, useEffect, useRef, useCallback } from "react";
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
} from "lucide-react";
import type { Panel, ChartType, ChartConfig, PanelQueryConfig } from "@/types/platform";
import ChartRenderer from "@/components/charts/chart-renderer";

interface PanelEditorProps {
  panel: Panel;
  panelData: Record<string, unknown>[];
  shareToken: string;
  schemaFields: string[];
  onApply: (updatedPanel: Panel) => void;
  onCancel: () => void;
}

type TabId = "data" | "display" | "axes" | "thresholds";

const TABS: { id: TabId; label: string }[] = [
  { id: "display", label: "Display" },
  { id: "axes", label: "Axes" },
  { id: "data", label: "Data" },
  { id: "thresholds", label: "Thresholds" },
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

const AGGREGATIONS = ["sum", "count", "avg"];

function FieldSelect({
  value,
  onChange,
  label,
  placeholder,
  schemaFields,
}: {
  value: string;
  onChange: (v: string) => void;
  label: string;
  placeholder: string;
  schemaFields: string[];
}) {
  return (
    <div>
      <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
        {label}
      </label>
      {schemaFields.length > 0 ? (
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors appearance-none"
        >
          <option value="">— Select field —</option>
          {schemaFields.map((f) => (
            <option key={f} value={f}>
              {f}
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

export default function PanelEditor({
  panel,
  panelData,
  shareToken,
  schemaFields,
  onApply,
  onCancel,
}: PanelEditorProps) {
  const [activeTab, setActiveTab] = useState<TabId>("display");

  // Display config
  const [title, setTitle] = useState(panel.title);
  const [chartType, setChartType] = useState<ChartType>(panel.chart_type);
  const [width, setWidth] = useState(panel.position.w);

  // Axes config
  const [xAxis, setXAxis] = useState(panel.chart_config.x_axis ?? "");
  const [yAxis, setYAxis] = useState(
    panel.chart_config.y_axis ?? panel.chart_config.value_field ?? "",
  );
  const [groupBy, setGroupBy] = useState(panel.chart_config.group_by ?? "");

  // Data config
  const [aggregation, setAggregation] = useState(
    panel.chart_config.aggregation ?? "sum",
  );
  const [channelKey, setChannelKey] = useState(
    panel.query_config.channel_key ?? "",
  );
  const [since, setSince] = useState(panel.query_config.since ?? "");
  const [until, setUntil] = useState(panel.query_config.until ?? "");

  // Thresholds
  const [warningValue, setWarningValue] = useState("");
  const [criticalValue, setCriticalValue] = useState("");

  // Live preview data
  const [previewData, setPreviewData] = useState<Record<string, unknown>[]>(panelData);
  const [previewLoading, setPreviewLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  // Build a live Panel from current editor state
  const buildPreviewPanel = useCallback((): Panel => {
    const isMetricOrPie = chartType === "metric" || chartType === "pie";
    const chartConfig: ChartConfig = isMetricOrPie
      ? { value_field: yAxis || undefined, label: title, aggregation }
      : {
          x_axis: xAxis || undefined,
          y_axis: yAxis || undefined,
          group_by: groupBy || undefined,
        };

    if (chartType === "table") {
      chartConfig.columns = [xAxis, yAxis].filter(Boolean);
    }

    return {
      id: panel.id,
      title,
      chart_type: chartType,
      position: { ...panel.position, w: Math.min(width, 6) },
      chart_config: chartConfig,
      query_config: {
        channel_key: channelKey || null,
        since: since || null,
        until: until || null,
      },
    };
  }, [title, chartType, width, xAxis, yAxis, groupBy, aggregation, channelKey, since, until, panel.id, panel.position]);

  // Live data fetch with debounce
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setPreviewLoading(true);
      try {
        const queryConfig: PanelQueryConfig = {
          channel_key: channelKey || null,
          since: since || null,
          until: until || null,
        };
        const res = await fetch("/api/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            share_token: shareToken,
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
  }, [shareToken, channelKey, since, until]);

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
                </>
              )}

              {activeTab === "axes" && (
                <>
                  {chartType === "metric" || chartType === "pie" ? (
                    <FieldSelect
                      value={yAxis}
                      onChange={setYAxis}
                      label="Value Field"
                      placeholder="reach"
                      schemaFields={schemaFields}
                    />
                  ) : (
                    <>
                      <FieldSelect
                        value={xAxis}
                        onChange={setXAxis}
                        label="X-Axis Field"
                        placeholder="date"
                        schemaFields={schemaFields}
                      />
                      <FieldSelect
                        value={yAxis}
                        onChange={setYAxis}
                        label="Y-Axis Field"
                        placeholder="reach"
                        schemaFields={schemaFields}
                      />
                      <FieldSelect
                        value={groupBy}
                        onChange={setGroupBy}
                        label="Group By (optional)"
                        placeholder=""
                        schemaFields={schemaFields}
                      />
                    </>
                  )}
                </>
              )}

              {activeTab === "data" && (
                <>
                  {/* Aggregation */}
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Aggregation
                    </label>
                    <div className="flex gap-2">
                      {AGGREGATIONS.map((agg) => (
                        <button
                          key={agg}
                          onClick={() => setAggregation(agg)}
                          className={`flex-1 py-2 text-[10px] tracking-widest uppercase font-mono border transition-colors ${
                            aggregation === agg
                              ? "border-coral bg-coral/10 text-coral"
                              : "border-white/10 text-white/30 hover:text-white/60 hover:border-white/20"
                          }`}
                        >
                          {agg}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Filter fields */}
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
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                        Since
                      </label>
                      <input
                        type="date"
                        value={since}
                        onChange={(e) => setSince(e.target.value)}
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
                        onChange={(e) => setUntil(e.target.value)}
                        className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
                      />
                    </div>
                  </div>
                </>
              )}

              {activeTab === "thresholds" && (
                <>
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Warning Threshold
                    </label>
                    <input
                      type="number"
                      value={warningValue}
                      onChange={(e) => setWarningValue(e.target.value)}
                      placeholder="e.g. 1000"
                      className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                      Critical Threshold
                    </label>
                    <input
                      type="number"
                      value={criticalValue}
                      onChange={(e) => setCriticalValue(e.target.value)}
                      placeholder="e.g. 500"
                      className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
                    />
                  </div>
                  <p className="text-white/20 text-[10px] font-mono tracking-wider">
                    Thresholds are saved with the panel config. Visual rendering on charts is coming in a future phase.
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Right: Live preview */}
          <div className="w-7/12 flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10 shrink-0">
              <div className="text-[10px] tracking-widest text-coral uppercase font-mono">
                Live Preview
              </div>
              <div className="text-xl font-display text-sage uppercase mt-1">
                {title || "Untitled Panel"}
              </div>
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
