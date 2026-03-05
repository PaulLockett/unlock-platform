"use client";

import type { Panel, ChartConfig, PanelQueryConfig } from "@/types/platform";

interface DataTabProps {
  panel: Panel;
  onChartConfigChange: (config: Partial<ChartConfig>) => void;
  onQueryConfigChange: (config: Partial<PanelQueryConfig>) => void;
}

export default function DataTab({
  panel,
  onChartConfigChange,
  onQueryConfigChange,
}: DataTabProps) {
  return (
    <div className="space-y-6">
      {/* Metric Query */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 bg-coral" />
          <span className="text-[10px] font-mono tracking-widest text-white/60 uppercase">
            Metric Query
          </span>
        </div>

        {/* Select Metric */}
        <div className="space-y-3">
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase">
            Select Metric
          </label>
          <input
            type="text"
            value={panel.chart_config.y_axis ?? ""}
            onChange={(e) => onChartConfigChange({ y_axis: e.target.value })}
            placeholder="e.g. revenue.total_quarterly_inflow"
            className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
          />
        </div>
      </div>

      {/* Aggregation */}
      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Aggregation
        </label>
        <select
          value={panel.chart_config.aggregation ?? "sum"}
          onChange={(e) => onChartConfigChange({ aggregation: e.target.value })}
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
        >
          <option value="sum">Sum</option>
          <option value="avg">Average</option>
          <option value="count">Count</option>
        </select>
      </div>

      {/* X-Axis / Interval */}
      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          X-Axis / Interval
        </label>
        <input
          type="text"
          value={panel.chart_config.x_axis ?? ""}
          onChange={(e) => onChartConfigChange({ x_axis: e.target.value })}
          placeholder="e.g. published_at"
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
        />
      </div>

      {/* Filter By */}
      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Filter: Channel Key
        </label>
        <input
          type="text"
          value={panel.query_config.channel_key ?? ""}
          onChange={(e) =>
            onQueryConfigChange({
              channel_key: e.target.value || null,
            })
          }
          placeholder="e.g. twitter"
          className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
        />
      </div>

      {/* Date Range */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
            Since
          </label>
          <input
            type="date"
            value={panel.query_config.since ?? ""}
            onChange={(e) =>
              onQueryConfigChange({ since: e.target.value || null })
            }
            className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          />
        </div>
        <div>
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
            Until
          </label>
          <input
            type="date"
            value={panel.query_config.until ?? ""}
            onChange={(e) =>
              onQueryConfigChange({ until: e.target.value || null })
            }
            className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          />
        </div>
      </div>
    </div>
  );
}
