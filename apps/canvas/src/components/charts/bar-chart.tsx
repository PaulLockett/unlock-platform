"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { Panel } from "@/types/platform";

interface BarChartPanelProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

export default function BarChartPanel({ panel, data }: BarChartPanelProps) {
  const xKey = panel.chart_config.x_axis ?? "name";
  const yKey = panel.chart_config.y_axis ?? "value";
  const groupBy = panel.chart_config.group_by;

  // If group_by is set, we need multiple bars
  const groups = groupBy
    ? [...new Set(data.map((d) => String(d[groupBy] ?? "")))]
    : [yKey];

  const COLORS = ["#ea6d58", "#dbe4d0", "#f5f5f1", "rgba(234,109,88,0.6)"];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
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
          <Bar
            key={g}
            dataKey={groupBy ? g : yKey}
            fill={COLORS[i % COLORS.length]}
            radius={[2, 2, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
