"use client";

import type { Panel } from "@/types/platform";

interface MetricCardProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

export default function MetricCard({ panel, data }: MetricCardProps) {
  const valueField = panel.chart_config.value_field ?? panel.chart_config.y_axis ?? "value";
  const label = panel.chart_config.label ?? panel.title;

  // Compute the metric value
  let value: number;
  const agg = panel.chart_config.aggregation ?? "sum";

  if (!data.length) {
    value = 0;
  } else if (agg === "count") {
    value = data.length;
  } else if (agg === "avg") {
    const sum = data.reduce((acc, d) => acc + Number(d[valueField] ?? 0), 0);
    value = sum / data.length;
  } else {
    // sum (default)
    value = data.reduce((acc, d) => acc + Number(d[valueField] ?? 0), 0);
  }

  // Format the value
  const formatted =
    value >= 1_000_000
      ? `${(value / 1_000_000).toFixed(1)}M`
      : value >= 1_000
        ? `${(value / 1_000).toFixed(1)}K`
        : value % 1 !== 0
          ? value.toFixed(2)
          : value.toLocaleString();

  return (
    <div className="w-full h-full flex flex-col justify-center items-center gap-2 px-4">
      <div className="text-[10px] font-mono tracking-widest text-white/40 uppercase">
        {label}
      </div>
      <div className="text-5xl font-display text-coral leading-none">
        {formatted}
      </div>
    </div>
  );
}
