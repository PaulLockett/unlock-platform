"use client";

import type { Panel, ChartConfig } from "@/types/platform";

interface AxesTabProps {
  panel: Panel;
  onChartConfigChange: (config: Partial<ChartConfig>) => void;
}

export default function AxesTab({ panel, onChartConfigChange }: AxesTabProps) {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          X-Axis Field
        </label>
        <input
          type="text"
          value={panel.chart_config.x_axis ?? ""}
          onChange={(e) => onChartConfigChange({ x_axis: e.target.value })}
          placeholder="e.g. date, category, name"
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
        />
      </div>

      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Y-Axis Field
        </label>
        <input
          type="text"
          value={panel.chart_config.y_axis ?? ""}
          onChange={(e) => onChartConfigChange({ y_axis: e.target.value })}
          placeholder="e.g. value, count, amount"
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
        />
      </div>

      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Group By
        </label>
        <input
          type="text"
          value={panel.chart_config.group_by ?? ""}
          onChange={(e) =>
            onChartConfigChange({ group_by: e.target.value || undefined })
          }
          placeholder="e.g. channel_key, source"
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
        />
      </div>

      {/* Value/Label fields for pie and funnel */}
      {(panel.chart_type === "pie" || panel.chart_type === "funnel") && (
        <>
          <div>
            <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
              Value Field
            </label>
            <input
              type="text"
              value={panel.chart_config.value_field ?? ""}
              onChange={(e) =>
                onChartConfigChange({ value_field: e.target.value })
              }
              placeholder="e.g. count, amount"
              className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
            />
          </div>
          <div>
            <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
              Label Field
            </label>
            <input
              type="text"
              value={panel.chart_config.label_field ?? ""}
              onChange={(e) =>
                onChartConfigChange({ label_field: e.target.value })
              }
              placeholder="e.g. name, stage"
              className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
            />
          </div>
        </>
      )}

      {/* Metric-specific */}
      {panel.chart_type === "metric" && (
        <div>
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
            Display Label
          </label>
          <input
            type="text"
            value={panel.chart_config.label ?? ""}
            onChange={(e) => onChartConfigChange({ label: e.target.value })}
            placeholder="e.g. Total Revenue"
            className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
          />
        </div>
      )}
    </div>
  );
}
