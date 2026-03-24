"use client";

import { useState } from "react";
import { ArrowUp, ArrowDown } from "lucide-react";
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

  // Local sort state (allows interactive column header sorting)
  const [sortCol, setSortCol] = useState(panel.chart_config.sort_by ?? "");
  const [sortDir, setSortDir] = useState<"asc" | "desc">(
    panel.chart_config.sort_direction ?? "asc",
  );

  if (!columns.length) {
    return (
      <div className="w-full h-full flex items-center justify-center text-white/20 text-xs font-mono">
        NO COLUMNS
      </div>
    );
  }

  // Apply local sort
  const sorted = sortCol
    ? [...data].sort((a, b) => {
        const aVal = a[sortCol];
        const bVal = b[sortCol];
        const aNum = Number(aVal);
        const bNum = Number(bVal);
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return sortDir === "asc" ? aNum - bNum : bNum - aNum;
        }
        const aStr = String(aVal ?? "");
        const bStr = String(bVal ?? "");
        return sortDir === "asc"
          ? aStr.localeCompare(bStr)
          : bStr.localeCompare(aStr);
      })
    : data;

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
  };

  return (
    <div className="w-full h-full overflow-auto no-scrollbar">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-white/10">
            {columns.map((col) => (
              <th
                key={col}
                onClick={() => handleSort(col)}
                className="text-left px-3 py-2 text-[10px] tracking-widest text-white/40 uppercase font-normal cursor-pointer hover:text-white/60 transition-colors select-none"
              >
                <span className="inline-flex items-center gap-1">
                  {col}
                  {sortCol === col && (
                    sortDir === "asc"
                      ? <ArrowUp className="w-3 h-3 text-coral" />
                      : <ArrowDown className="w-3 h-3 text-coral" />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
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
