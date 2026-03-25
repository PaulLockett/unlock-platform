"use client";

import { Plus } from "lucide-react";

interface EditToolbarProps {
  panelCount: number;
  onAddChart: () => void;
}

export default function EditToolbar({
  panelCount,
  onAddChart,
}: EditToolbarProps) {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 px-6 py-3 bg-charcoal-light border border-white/10 shadow-2xl">
      <button
        onClick={onAddChart}
        className="flex items-center gap-2 px-4 py-1.5 bg-coral text-charcoal text-[10px] tracking-widest uppercase font-mono hover:bg-coral/90 transition-colors"
      >
        <Plus className="w-3.5 h-3.5" />
        Add Chart
      </button>
      <span className="text-[10px] tracking-widest text-white/30 uppercase font-mono">
        {panelCount} {panelCount === 1 ? "Panel" : "Panels"}
      </span>
    </div>
  );
}
