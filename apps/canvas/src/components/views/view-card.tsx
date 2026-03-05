"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { ViewDefinition, LayoutConfig } from "@/types/platform";

interface ViewCardProps {
  view: ViewDefinition;
  index: number;
}

export default function ViewCard({ view, index }: ViewCardProps) {
  const layout = view.layout_config as LayoutConfig | null;
  const panelCount = layout?.panels?.length ?? 0;
  const shareToken = view.share_token ?? view.id;
  const number = String(index + 1).padStart(2, "0");

  return (
    <Link href={`/v/${shareToken}`}>
      <article className="group relative border-r border-b border-white/10 bg-charcoal hover:bg-[#161616] transition-all duration-500 flex flex-col min-h-[420px]">
        {/* Panel count badge */}
        <div className="absolute top-0 right-0 p-6 opacity-50 group-hover:opacity-100 transition-opacity z-10">
          <div className="border border-white/20 rounded-full px-3 py-1 text-[10px] uppercase tracking-wider text-sage group-hover:border-sage group-hover:bg-sage/10 transition-colors font-mono">
            {panelCount} Panel{panelCount !== 1 ? "s" : ""}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-8 md:p-12 flex flex-col justify-center relative overflow-hidden">
          {/* Background number */}
          <div className="absolute -left-4 top-20 text-[10rem] font-display text-white/[0.02] leading-none pointer-events-none select-none">
            {number}
          </div>

          <h3 className="text-5xl md:text-6xl font-display uppercase leading-[0.85] text-offwhite group-hover:text-coral transition-colors duration-300 relative z-10">
            {view.name}
          </h3>
          {view.description && (
            <p className="font-serif italic text-white/60 mt-6 text-lg group-hover:text-white/80 transition-colors relative z-10 max-w-sm">
              {view.description}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="px-8 md:px-12 py-6 border-t border-white/5 flex items-center justify-between mt-auto bg-black/20">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full border border-sage p-0.5">
              <div className="w-full h-full rounded-full bg-charcoal-light flex items-center justify-center text-xs font-mono text-sage">
                {(view.created_by ?? "?").charAt(0).toUpperCase()}
              </div>
            </div>
            <div>
              <div className="text-sm font-bold text-offwhite font-mono">
                {view.created_by ?? "Unknown"}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-coral font-mono">
                {view.visibility === "public" ? "Public" : "Restricted"}
              </div>
            </div>
          </div>
          <div className="opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-[-10px] group-hover:translate-x-0 duration-300 bg-sage rounded-full p-2">
            <ArrowRight className="w-4 h-4 text-charcoal" />
          </div>
        </div>
      </article>
    </Link>
  );
}
