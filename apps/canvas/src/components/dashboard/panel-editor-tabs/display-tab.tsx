"use client";

import type { Panel, ChartType } from "@/types/platform";

interface DisplayTabProps {
  panel: Panel;
  onTitleChange: (title: string) => void;
  onChartTypeChange: (type: ChartType) => void;
  onColorSchemeChange: (scheme: string) => void;
}

const CHART_TYPES: { value: ChartType; label: string }[] = [
  { value: "bar", label: "Bar" },
  { value: "line", label: "Line" },
  { value: "pie", label: "Pie" },
  { value: "area", label: "Area" },
  { value: "funnel", label: "Funnel" },
  { value: "table", label: "Table" },
  { value: "metric", label: "Metric" },
];

export default function DisplayTab({
  panel,
  onTitleChange,
  onChartTypeChange,
  onColorSchemeChange,
}: DisplayTabProps) {
  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Panel Title
        </label>
        <input
          type="text"
          value={panel.title}
          onChange={(e) => onTitleChange(e.target.value)}
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
        />
      </div>

      {/* Chart Type */}
      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-3">
          Chart Type
        </label>
        <div className="grid grid-cols-4 gap-2">
          {CHART_TYPES.map((ct) => (
            <button
              key={ct.value}
              onClick={() => onChartTypeChange(ct.value)}
              className={`px-2 py-2 text-[10px] font-mono tracking-widest uppercase border transition-colors ${
                panel.chart_type === ct.value
                  ? "border-coral text-coral bg-coral/10"
                  : "border-white/10 text-white/40 hover:border-white/20 hover:text-white/60"
              }`}
            >
              {ct.label}
            </button>
          ))}
        </div>
      </div>

      {/* Color Scheme */}
      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Color Scheme
        </label>
        <select
          value={panel.chart_config.color_scheme ?? "default"}
          onChange={(e) => onColorSchemeChange(e.target.value)}
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
        >
          <option value="default">Default (Coral + Sage)</option>
          <option value="warm">Warm</option>
          <option value="cool">Cool</option>
          <option value="mono">Monochrome</option>
        </select>
      </div>

      {/* Grid Size */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
            Width (columns)
          </label>
          <select
            value={panel.position.w}
            onChange={() => {
              // resize handled via panel-card grips
            }}
            className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          >
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <option key={n} value={n}>
                {n} col{n !== 1 ? "s" : ""}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
            Height (rows)
          </label>
          <select
            value={panel.position.h}
            onChange={() => {
              // resize via grips
            }}
            className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          >
            {[1, 2, 3, 4].map((n) => (
              <option key={n} value={n}>
                {n} row{n !== 1 ? "s" : ""}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
