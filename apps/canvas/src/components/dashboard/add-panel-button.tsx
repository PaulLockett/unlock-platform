"use client";

interface AddPanelButtonProps {
  onClick: () => void;
}

export default function AddPanelButton({ onClick }: AddPanelButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center justify-center border border-dashed border-white/20 bg-white/[0.02] text-white/30 hover:border-white/40 hover:text-white/50 hover:bg-white/[0.04] transition-colors cursor-pointer min-h-[200px]"
      style={{ gridColumn: "span 2" }}
    >
      <div className="flex flex-col items-center gap-2">
        <span className="text-2xl">+</span>
        <span className="text-xs font-mono tracking-wider uppercase">
          Add Panel
        </span>
      </div>
    </button>
  );
}
