"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { Panel } from "@/types/platform";

interface AreaChartPanelProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

export default function AreaChartPanel({ panel, data }: AreaChartPanelProps) {
  const xKey = panel.chart_config.x_axis ?? "name";
  const yKey = panel.chart_config.y_axis ?? "value";

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ea6d58" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#ea6d58" stopOpacity={0} />
          </linearGradient>
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
        <Area
          type="monotone"
          dataKey={yKey}
          stroke="#ea6d58"
          fill="url(#areaGrad)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
