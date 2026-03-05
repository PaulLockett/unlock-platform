"use client";

import { Plus } from "lucide-react";

interface CreateViewCardProps {
  onClick: () => void;
}

export default function CreateViewCard({ onClick }: CreateViewCardProps) {
  return (
    <article
      onClick={onClick}
      className="group relative border-r border-b border-white/10 bg-white/[0.02] hover:bg-white/5 transition-all duration-500 flex flex-col justify-center items-center min-h-[420px] cursor-pointer"
    >
      <div className="w-24 h-24 rounded-full border border-dashed border-white/20 flex items-center justify-center group-hover:border-coral group-hover:scale-110 transition-all duration-300 bg-charcoal relative">
        <div className="absolute inset-0 bg-coral/20 rounded-full scale-0 group-hover:scale-100 transition-transform duration-300" />
        <Plus className="w-8 h-8 text-white/40 group-hover:text-coral relative z-10" />
      </div>
      <div className="mt-6 font-mono text-sm tracking-widest text-white/40 group-hover:text-coral uppercase transition-colors">
        Create New View
      </div>
      <p className="mt-2 text-white/20 text-xs font-serif italic text-center max-w-[200px]">
        Add a custom dashboard based on your current metrics
      </p>
    </article>
  );
}
