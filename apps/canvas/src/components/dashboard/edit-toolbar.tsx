"use client";

import { Plus, Grid3X3, History } from "lucide-react";

interface EditToolbarProps {
  onAddPanel: () => void;
}

export default function EditToolbar({ onAddPanel }: EditToolbarProps) {
  return (
    <div className="fixed bottom-8 right-8 z-50 flex gap-3">
      <button
        onClick={onAddPanel}
        className="flex items-center gap-2 px-4 py-2 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors shadow-lg"
      >
        <Plus className="w-3 h-3" />
        Add Chart
      </button>
      <button className="flex items-center gap-2 px-4 py-2 bg-charcoal-light border border-white/10 text-white/40 text-xs font-mono tracking-widest uppercase hover:text-white hover:border-white/20 transition-colors shadow-lg">
        <Grid3X3 className="w-3 h-3" />
        Grid
      </button>
      <button className="flex items-center gap-2 px-4 py-2 bg-charcoal-light border border-white/10 text-white/40 text-xs font-mono tracking-widest uppercase hover:text-white hover:border-white/20 transition-colors shadow-lg">
        <History className="w-3 h-3" />
        History
      </button>
    </div>
  );
}
