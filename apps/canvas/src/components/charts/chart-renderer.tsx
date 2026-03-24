"use client";

import { useMemo } from "react";
import type { Panel } from "@/types/platform";
import { transformData } from "@/lib/transform-data";
import type { AggregationType, SortDirection } from "@/lib/transform-data";
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
  // Apply client-side transformations (aggregation, sort, limit)
  const transformedData = useMemo(() => {
    const config = panel.chart_config;
    const agg = config.aggregation as AggregationType | undefined;
    const groupField = config.x_axis ?? config.group_by;
    const valueField = config.y_axis ?? config.value_field;

    // Only aggregate for non-metric/non-table types when aggregation is set
    // and we have both a group field and a value field
    const shouldAggregate =
      agg &&
      groupField &&
      valueField &&
      panel.chart_type !== "metric" && // MetricCard does its own aggregation
      panel.chart_type !== "table"; // Tables show raw data

    return transformData(data, {
      groupBy: shouldAggregate ? groupField : undefined,
      valueField: shouldAggregate ? valueField : undefined,
      aggregation: shouldAggregate ? agg : undefined,
      sortField: config.sort_by ?? undefined,
      sortDirection: (config.sort_direction as SortDirection) ?? "asc",
    });
  }, [data, panel.chart_config, panel.chart_type]);

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-coral/30 border-t-coral rounded-full animate-spin" />
      </div>
    );
  }

  if (!transformedData.length && panel.chart_type !== "metric") {
    return (
      <div className="w-full h-full flex items-center justify-center text-white/20 text-xs font-mono tracking-widest">
        NO DATA
      </div>
    );
  }

  switch (panel.chart_type) {
    case "bar":
      return <BarChartPanel panel={panel} data={transformedData} />;
    case "line":
      return <LineChartPanel panel={panel} data={transformedData} />;
    case "pie":
      return <PieChartPanel panel={panel} data={transformedData} />;
    case "area":
      return <AreaChartPanel panel={panel} data={transformedData} />;
    case "funnel":
      return <FunnelChartPanel panel={panel} data={transformedData} />;
    case "table":
      return <DataTable panel={panel} data={transformedData} />;
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
