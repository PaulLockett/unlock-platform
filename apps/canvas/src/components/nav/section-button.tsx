"use client";

interface SectionButtonProps {
  label: string;
  active?: boolean;
  onClick?: () => void;
}

export default function SectionButton({
  label,
  active = false,
  onClick,
}: SectionButtonProps) {
  return (
    <button className="relative group" onClick={onClick}>
      <div
        className={`transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors font-mono ${
          active ? "text-coral" : "text-white/40"
        }`}
      >
        {label}
      </div>
    </button>
  );
}
