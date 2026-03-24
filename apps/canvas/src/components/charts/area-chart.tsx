"use client";

import { useId } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import type { Panel } from "@/types/platform";

interface AreaChartPanelProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

const COLORS = [
  "#ea6d58",
  "#dbe4d0",
  "#f5f5f1",
  "rgba(234,109,88,0.6)",
  "#8884d8",
  "#82ca9d",
];

export default function AreaChartPanel({ panel, data }: AreaChartPanelProps) {
  const baseId = useId();
  const xKey = panel.chart_config.x_axis ?? "name";
  const yKey = panel.chart_config.y_axis ?? "value";
  const groupBy = panel.chart_config.group_by;
  const stacked = panel.chart_config.stacked ?? false;

  const groups = groupBy
    ? [...new Set(data.map((d) => String(d[groupBy] ?? "")))]
    : [yKey];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
        <defs>
          {groups.map((_, i) => (
            <linearGradient key={i} id={`${baseId}-grad-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.3} />
              <stop offset="95%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey={xKey}
          tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10, fontFamily: "Space Mono" }}
          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10, fontFamily: "Space Mono" }}
          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1a1a1a",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 0,
            fontFamily: "Space Mono",
            fontSize: 11,
            color: "#f5f5f1",
          }}
        />
        {groups.length > 1 && <Legend wrapperStyle={{ fontFamily: "Space Mono", fontSize: 10 }} />}
        {groups.map((g, i) => (
          <Area
            key={g}
            type="monotone"
            dataKey={groupBy ? g : yKey}
            stroke={COLORS[i % COLORS.length]}
            fill={`url(#${baseId}-grad-${i})`}
            strokeWidth={2}
            stackId={stacked ? "stack" : undefined}
          />
        ))}
        {panel.chart_config.warning_threshold != null && (
          <ReferenceLine
            y={panel.chart_config.warning_threshold}
            stroke="#f59e0b"
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
        )}
        {panel.chart_config.critical_threshold != null && (
          <ReferenceLine
            y={panel.chart_config.critical_threshold}
            stroke="#ef4444"
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}
