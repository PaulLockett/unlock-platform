"use client";

import type { Panel } from "@/types/platform";

interface DataTableProps {
  panel: Panel;
  data: Record<string, unknown>[];
}

export default function DataTable({ panel, data }: DataTableProps) {
  // Use explicit columns from config, or auto-detect from data
  const columns =
    panel.chart_config.columns && panel.chart_config.columns.length > 0
      ? panel.chart_config.columns
      : data.length > 0
        ? Object.keys(data[0])
        : [];

  if (!columns.length) {
    return (
      <div className="w-full h-full flex items-center justify-center text-white/20 text-xs font-mono">
        NO COLUMNS
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-auto no-scrollbar">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-white/10">
            {columns.map((col) => (
              <th
                key={col}
                className="text-left px-3 py-2 text-[10px] tracking-widest text-white/40 uppercase font-normal"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={i}
              className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
            >
              {columns.map((col) => (
                <td key={col} className="px-3 py-2 text-white/60">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
