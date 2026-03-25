"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import type { Panel } from "@/types/platform";

interface LineChartPanelProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

export default function LineChartPanel({ panel, data }: LineChartPanelProps) {
  const xKey = panel.chart_config.x_axis ?? "name";
  const yKey = panel.chart_config.y_axis ?? "value";
  const groupBy = panel.chart_config.group_by;

  const groups = groupBy
    ? [...new Set(data.map((d) => String(d[groupBy] ?? "")))]
    : [yKey];

  const COLORS = [
    "#ea6d58",
    "#dbe4d0",
    "#f5f5f1",
    "rgba(234,109,88,0.6)",
    "#8884d8",
    "#82ca9d",
    "#ffc658",
    "#ff7c43",
  ];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
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
          <Line
            key={g}
            type="monotone"
            dataKey={groupBy ? g : yKey}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: COLORS[i % COLORS.length] }}
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
      </LineChart>
    </ResponsiveContainer>
  );
}
