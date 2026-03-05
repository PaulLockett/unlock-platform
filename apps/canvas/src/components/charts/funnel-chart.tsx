"use client";

import type { Panel } from "@/types/platform";

interface FunnelChartPanelProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

const COLORS = ["#ea6d58", "#dbe4d0", "#f5f5f1", "rgba(234,109,88,0.6)", "rgba(219,228,208,0.6)"];

export default function FunnelChartPanel({ panel, data }: FunnelChartPanelProps) {
  const labelKey = panel.chart_config.label_field ?? panel.chart_config.x_axis ?? "name";
  const valueKey = panel.chart_config.value_field ?? panel.chart_config.y_axis ?? "value";

  const maxValue = Math.max(...data.map((d) => Number(d[valueKey] ?? 0)), 1);

  return (
    <div className="w-full h-full flex flex-col justify-center gap-3 px-4">
      {data.map((item, i) => {
        const value = Number(item[valueKey] ?? 0);
        const widthPct = (value / maxValue) * 100;
        const label = String(item[labelKey] ?? `Stage ${i + 1}`);

        return (
          <div key={i} className="flex items-center gap-3">
            <div className="w-24 text-right text-[10px] font-mono text-white/40 uppercase tracking-widest shrink-0">
              {label}
            </div>
            <div className="flex-1 h-8 bg-white/5 relative">
              <div
                className="h-full transition-all duration-500"
                style={{
                  width: `${widthPct}%`,
                  backgroundColor: COLORS[i % COLORS.length],
                }}
              />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-white/60">
                {value.toLocaleString()}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
