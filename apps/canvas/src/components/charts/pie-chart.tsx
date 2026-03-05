"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { Panel } from "@/types/platform";

interface PieChartPanelProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

const COLORS = ["#ea6d58", "#dbe4d0", "#f5f5f1", "rgba(234,109,88,0.6)", "rgba(219,228,208,0.6)"];

export default function PieChartPanel({ panel, data }: PieChartPanelProps) {
  const valueKey = panel.chart_config.value_field ?? panel.chart_config.y_axis ?? "value";
  const labelKey = panel.chart_config.label_field ?? panel.chart_config.x_axis ?? "name";

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={labelKey}
          cx="50%"
          cy="50%"
          innerRadius="40%"
          outerRadius="70%"
          paddingAngle={2}
          stroke="none"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
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
        <Legend
          wrapperStyle={{ fontFamily: "Space Mono", fontSize: 10, color: "rgba(255,255,255,0.4)" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
