"use client";

import { Plus } from "lucide-react";

interface AddPanelButtonProps {
  onClick: () => void;
}

export default function AddPanelButton({ onClick }: AddPanelButtonProps) {
  return (
    <button
      onClick={onClick}
      className="col-span-2 border border-dashed border-white/10 hover:border-coral min-h-[200px] flex flex-col items-center justify-center gap-2 transition-colors group"
    >
      <div className="w-10 h-10 rounded-full border border-dashed border-white/20 flex items-center justify-center group-hover:border-coral group-hover:scale-110 transition-all bg-charcoal">
        <Plus className="w-4 h-4 text-white/30 group-hover:text-coral transition-colors" />
      </div>
      <span className="text-[10px] font-mono tracking-widest text-white/20 group-hover:text-coral uppercase transition-colors">
        Add Panel
      </span>
    </button>
  );
}
