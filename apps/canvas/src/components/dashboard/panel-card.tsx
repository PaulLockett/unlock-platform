"use client";

import { GripVertical, X, Pencil } from "lucide-react";
import type { Panel } from "@/types/platform";
import ChartRenderer from "@/components/charts/chart-renderer";

interface PanelCardProps {
  panel: Panel;
  data: Record<string, unknown>[];
  loading?: boolean;
  editMode?: boolean;
  onRemove?: () => void;
  onEdit?: () => void;
}

export default function PanelCard({
  panel,
  data,
  loading,
  editMode = false,
  onRemove,
  onEdit,
}: PanelCardProps) {
  return (
    <div
      className={`border border-white/10 bg-charcoal-light p-4 flex flex-col min-h-[200px] relative group/panel ${
        editMode ? "hover:border-coral cursor-move" : ""
      }`}
      style={{
        gridColumn: `span ${Math.min(panel.position.w, 6)}`,
        gridRow:
          panel.position.h > 1
            ? `span ${Math.min(panel.position.h, 4)}`
            : undefined,
      }}
    >
      {/* Edit mode overlay controls */}
      {editMode && (
        <>
          {/* Drag handle */}
          <div className="absolute top-2 left-2 opacity-0 group-hover/panel:opacity-100 transition-opacity text-white/30 hover:text-white cursor-grab">
            <GripVertical className="w-4 h-4" />
          </div>

          {/* Edit + Remove buttons */}
          <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover/panel:opacity-100 transition-opacity">
            <button
              onClick={onEdit}
              className="w-6 h-6 flex items-center justify-center bg-charcoal border border-white/10 text-white/40 hover:text-coral hover:border-coral transition-colors"
            >
              <Pencil className="w-3 h-3" />
            </button>
            <button
              onClick={onRemove}
              className="w-6 h-6 flex items-center justify-center bg-charcoal border border-white/10 text-white/40 hover:text-coral hover:border-coral transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>

          {/* Resize grip */}
          <div className="absolute bottom-1 right-1 opacity-0 group-hover/panel:opacity-100 transition-opacity text-white/20">
            <svg width="12" height="12" viewBox="0 0 12 12">
              <line x1="11" y1="1" x2="1" y2="11" stroke="currentColor" strokeWidth="1" />
              <line x1="11" y1="5" x2="5" y2="11" stroke="currentColor" strokeWidth="1" />
              <line x1="11" y1="9" x2="9" y2="11" stroke="currentColor" strokeWidth="1" />
            </svg>
          </div>
        </>
      )}

      {/* Panel header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] tracking-widest text-white/40 uppercase font-mono">
          {panel.title}
        </span>
        <span className="text-[9px] tracking-wider text-white/20 uppercase font-mono">
          {panel.chart_type}
        </span>
      </div>

      {/* Chart content */}
      <div className="flex-1 min-h-0">
        <ChartRenderer panel={panel} data={data} loading={loading} />
      </div>
    </div>
  );
}
