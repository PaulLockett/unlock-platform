"use client";

import { useState, useEffect, useMemo } from "react";
import {
  X,
  ArrowRight,
  BarChart3,
  LineChart,
  PieChart,
  AreaChart,
  Filter,
  Table,
  Hash,
  Database,
  Loader2,
} from "lucide-react";
import type { Panel, ChartType } from "@/types/platform";
import { detectFieldTypes } from "@/lib/transform-data";

interface AddPanelModalProps {
  open: boolean;
  onClose: () => void;
  onAdd: (panel: Panel) => void;
  existingPanel?: Panel;
  existingPanels?: Panel[];
  schemaFields?: string[];
  shareToken: string;
  availableSources?: { key: string; record_count: number; sample_fields: string[] }[];
}

const CHART_TYPES: { type: ChartType; label: string; icon: React.ReactNode }[] =
  [
    { type: "bar", label: "Bar", icon: <BarChart3 className="w-5 h-5" /> },
    { type: "line", label: "Line", icon: <LineChart className="w-5 h-5" /> },
    { type: "pie", label: "Pie", icon: <PieChart className="w-5 h-5" /> },
    { type: "area", label: "Area", icon: <AreaChart className="w-5 h-5" /> },
    { type: "funnel", label: "Funnel", icon: <Filter className="w-5 h-5" /> },
    { type: "table", label: "Table", icon: <Table className="w-5 h-5" /> },
    { type: "metric", label: "Metric", icon: <Hash className="w-5 h-5" /> },
  ];

const WIDTH_OPTIONS = [
  { label: "Small", w: 2 },
  { label: "Medium", w: 3 },
  { label: "Large", w: 6 },
];

export default function AddPanelModal({
  open,
  onClose,
  onAdd,
  existingPanel,
  existingPanels = [],
  schemaFields = [],
  shareToken,
  availableSources = [],
}: AddPanelModalProps) {
  const isEditing = !!existingPanel;

  const [title, setTitle] = useState(existingPanel?.title ?? "");
  const [chartType, setChartType] = useState<ChartType>(
    existingPanel?.chart_type ?? "bar",
  );
  const [xAxis, setXAxis] = useState(
    existingPanel?.chart_config.x_axis ?? "",
  );
  const [yAxis, setYAxis] = useState(
    existingPanel?.chart_config.y_axis ??
      existingPanel?.chart_config.value_field ??
      "",
  );
  const [width, setWidth] = useState(existingPanel?.position.w ?? 3);
  const [sourceKey, setSourceKey] = useState(
    existingPanel?.query_config.source_key ?? "",
  );
  const [error, setError] = useState("");

  // Fetch live data to discover fields
  const [liveData, setLiveData] = useState<Record<string, unknown>[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const doFetch = async () => {
      setLoadingData(true);
      try {
        const r = await fetch("/api/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            share_token: shareToken,
            source_key: sourceKey || null,
            limit: 20,
            offset: 0,
          }),
        });
        const data = await r.json();
        if (!cancelled && data.success && data.records) {
          setLiveData(data.records);
        }
      } catch {
        // ignore fetch errors
      } finally {
        if (!cancelled) setLoadingData(false);
      }
    };
    doFetch();
    return () => { cancelled = true; };
  }, [open, shareToken, sourceKey]);

  // Detect fields from live data
  const fieldTypes = useMemo(() => detectFieldTypes(liveData), [liveData]);
  const dataFields = useMemo(() => {
    if (liveData.length > 0) return Object.keys(liveData[0]);
    return [];
  }, [liveData]);

  // Merge schema fields + data fields, deduplicated
  const allFields = useMemo(() => {
    const merged = new Set([...schemaFields, ...dataFields]);
    return [...merged].sort();
  }, [schemaFields, dataFields]);

  const numericFields = useMemo(() => {
    return allFields.filter((f) => fieldTypes.get(f) === "number");
  }, [allFields, fieldTypes]);

  const handleSubmit = () => {
    if (!title.trim()) {
      setError("Panel title is required");
      return;
    }

    // Compute position: stack below existing panels
    const nextY = existingPanels.reduce(
      (max, p) => Math.max(max, p.position.y + (p.position.h || 1)),
      0,
    );

    const isMetricOrPie = chartType === "metric" || chartType === "pie";

    const panel: Panel = {
      id: existingPanel?.id ?? crypto.randomUUID(),
      title: title.trim(),
      chart_type: chartType,
      position: existingPanel?.position ?? {
        x: 0,
        y: nextY,
        w: Math.min(width, 6),
        h: 1,
      },
      chart_config: {
        ...(isMetricOrPie
          ? { value_field: yAxis || undefined, label: title.trim() }
          : {
              x_axis: xAxis || undefined,
              y_axis: yAxis || undefined,
            }),
        ...(chartType === "metric"
          ? { aggregation: "sum" }
          : {}),
        ...(chartType === "table"
          ? {
              columns: [xAxis, yAxis].filter(Boolean),
            }
          : {}),
      },
      query_config: {
        source_key: sourceKey || null,
      },
    };

    // When editing, preserve the existing position
    if (existingPanel) {
      panel.position = { ...existingPanel.position, w: Math.min(width, 6) };
    }

    onAdd(panel);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-charcoal/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg mx-4 bg-charcoal-light border border-white/10">
        {/* Corner accents */}
        <div className="absolute -top-px -left-px w-8 h-8 border-t-2 border-l-2 border-coral" />
        <div className="absolute -top-px -right-px w-8 h-8 border-t-2 border-r-2 border-coral" />
        <div className="absolute -bottom-px -left-px w-8 h-8 border-b-2 border-l-2 border-coral" />
        <div className="absolute -bottom-px -right-px w-8 h-8 border-b-2 border-r-2 border-coral" />

        {/* Header */}
        <div className="flex items-center justify-between p-8 pb-0">
          <div>
            <div className="text-[10px] tracking-widest text-coral uppercase font-mono">
              {isEditing ? "Edit Panel" : "New Panel"}
            </div>
            <h2 className="text-3xl font-display uppercase text-sage mt-1">
              {isEditing ? "Configure" : "Add Chart"}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="p-8 space-y-6">
          {/* Data Source */}
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
              <div className="flex items-center gap-2 px-4 py-3 bg-charcoal border border-white/10 text-sm font-mono text-white/40">
                <Database className="w-4 h-4" />
                {loadingData ? "Loading data..." : "Auto-detect"}
              </div>
            )}
          </div>

          {/* Field status indicator */}
          {loadingData ? (
            <div className="flex items-center gap-2 text-[9px] font-mono text-white/25 tracking-wider">
              <Loader2 className="w-3 h-3 animate-spin" />
              Loading fields from data source...
            </div>
          ) : allFields.length > 0 ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-white/[0.02] border border-white/5 text-[9px] font-mono text-white/30 tracking-wider">
              <Database className="w-3 h-3" />
              {allFields.length} fields available
              {numericFields.length > 0 && (
                <span className="text-coral">
                  ({numericFields.length} numeric)
                </span>
              )}
            </div>
          ) : null}

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
              autoFocus
            />
          </div>

          {/* Chart Type */}
          <div>
            <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
              Chart Type
            </label>
            <div className="grid grid-cols-4 gap-2">
              {CHART_TYPES.map(({ type, label, icon }) => (
                <button
                  key={type}
                  onClick={() => setChartType(type)}
                  className={`flex flex-col items-center gap-1.5 p-3 border transition-colors ${
                    chartType === type
                      ? "border-coral bg-coral/10 text-coral"
                      : "border-white/10 text-white/30 hover:text-white/60 hover:border-white/20"
                  }`}
                >
                  {icon}
                  <span className="text-[9px] tracking-widest uppercase font-mono">
                    {label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Axis fields — always dropdowns when fields are available */}
          {chartType !== "metric" && chartType !== "pie" ? (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                  X-Axis Field
                </label>
                <select
                  value={xAxis}
                  onChange={(e) => setXAxis(e.target.value)}
                  className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors appearance-none"
                >
                  <option value="">— Select field —</option>
                  {allFields.map((f) => (
                    <option key={f} value={f}>
                      {f}{fieldTypes.has(f) ? ` (${fieldTypes.get(f)})` : ""}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                  Y-Axis Field
                </label>
                <select
                  value={yAxis}
                  onChange={(e) => setYAxis(e.target.value)}
                  className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors appearance-none"
                >
                  <option value="">— Select field —</option>
                  {(numericFields.length > 0 ? numericFields : allFields).map((f) => (
                    <option key={f} value={f}>
                      {f}{fieldTypes.has(f) ? ` (${fieldTypes.get(f)})` : ""}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                Value Field
              </label>
              <select
                value={yAxis}
                onChange={(e) => setYAxis(e.target.value)}
                className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite focus:outline-none focus:border-coral transition-colors appearance-none"
              >
                <option value="">— Select field —</option>
                {(numericFields.length > 0 ? numericFields : allFields).map((f) => (
                  <option key={f} value={f}>
                    {f}{fieldTypes.has(f) ? ` (${fieldTypes.get(f)})` : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Width selector */}
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

          {error && (
            <p className="text-coral text-xs font-mono">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-4 p-8 pt-0">
          <button
            onClick={onClose}
            className="px-6 py-2 text-sm font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="flex items-center gap-2 px-6 py-2 bg-coral text-charcoal text-sm font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors"
          >
            {isEditing ? "Apply" : "Add Panel"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
