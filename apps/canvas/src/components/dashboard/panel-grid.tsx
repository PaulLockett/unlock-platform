"use client";

import type { Panel } from "@/types/platform";
import PanelCard from "./panel-card";
import AddPanelButton from "./add-panel-button";

interface PanelGridProps {
  panels: Panel[];
  panelData: Record<string, Record<string, unknown>[]>;
  loadingPanels: Set<string>;
  editMode?: boolean;
  onRemovePanel?: (panelId: string) => void;
  onEditPanel?: (panelId: string) => void;
  onAddPanel?: () => void;
}

export default function PanelGrid({
  panels,
  panelData,
  loadingPanels,
  editMode = false,
  onRemovePanel,
  onEditPanel,
  onAddPanel,
}: PanelGridProps) {
  if (!panels.length && !editMode) {
    return (
      <div className="flex items-center justify-center py-32 text-white/20 text-sm font-mono tracking-widest">
        NO PANELS — ENTER EDIT MODE TO ADD CHARTS
      </div>
    );
  }

  return (
    <div
      className="grid gap-0 border-t border-white/10"
      style={{ gridTemplateColumns: "repeat(6, 1fr)" }}
    >
      {panels.map((panel) => (
        <PanelCard
          key={panel.id}
          panel={panel}
          data={panelData[panel.id] ?? []}
          loading={loadingPanels.has(panel.id)}
          editMode={editMode}
          onRemove={() => onRemovePanel?.(panel.id)}
          onEdit={() => onEditPanel?.(panel.id)}
        />
      ))}
      {editMode && onAddPanel && <AddPanelButton onClick={onAddPanel} />}
    </div>
  );
}
