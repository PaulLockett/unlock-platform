"use client";

import type { Panel } from "@/types/platform";
import BarChartPanel from "./bar-chart";
import LineChartPanel from "./line-chart";
import PieChartPanel from "./pie-chart";
import AreaChartPanel from "./area-chart";
import FunnelChartPanel from "./funnel-chart";
import MetricCard from "./metric-card";
import DataTable from "../data/data-table";

interface ChartRendererProps {
  panel: Panel;
  data: Record<string, unknown>[];
  loading?: boolean;
}

export default function ChartRenderer({
  panel,
  data,
  loading = false,
}: ChartRendererProps) {
  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-coral/30 border-t-coral rounded-full animate-spin" />
      </div>
    );
  }

  if (!data.length && panel.chart_type !== "metric") {
    return (
      <div className="w-full h-full flex items-center justify-center text-white/20 text-xs font-mono tracking-widest">
        NO DATA
      </div>
    );
  }

  switch (panel.chart_type) {
    case "bar":
      return <BarChartPanel panel={panel} data={data} />;
    case "line":
      return <LineChartPanel panel={panel} data={data} />;
    case "pie":
      return <PieChartPanel panel={panel} data={data} />;
    case "area":
      return <AreaChartPanel panel={panel} data={data} />;
    case "funnel":
      return <FunnelChartPanel panel={panel} data={data} />;
    case "table":
      return <DataTable panel={panel} data={data} />;
    case "metric":
      return <MetricCard panel={panel} data={data} />;
    default:
      return (
        <div className="w-full h-full flex items-center justify-center text-white/20 text-xs font-mono">
          Unsupported: {panel.chart_type}
        </div>
      );
  }
}
