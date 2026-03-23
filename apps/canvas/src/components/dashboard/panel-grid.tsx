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
  if (!panels.length) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <div className="text-white/20 text-sm font-mono tracking-widest">
          {editMode
            ? "NO PANELS YET — CLICK ADD CHART TO GET STARTED"
            : "NO PANELS — ENTER EDIT MODE TO ADD CHARTS"}
        </div>
        {editMode && onAddPanel && <AddPanelButton onClick={onAddPanel} />}
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
