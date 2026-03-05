"use client";

import type { Panel } from "@/types/platform";

interface ThresholdsTabProps {
  panel: Panel;
}

export default function ThresholdsTab({ panel }: ThresholdsTabProps) {
  return (
    <div className="space-y-6">
      <div className="text-[10px] font-mono tracking-widest text-white/30 uppercase">
        Thresholds for {panel.chart_type} chart
      </div>

      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Warning Threshold
        </label>
        <div className="flex items-center gap-3">
          <input
            type="number"
            placeholder="e.g. 80"
            className="flex-1 bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
          />
          <div className="w-4 h-4 bg-yellow-500/60 border border-yellow-500" />
        </div>
      </div>

      <div>
        <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase mb-2">
          Critical Threshold
        </label>
        <div className="flex items-center gap-3">
          <input
            type="number"
            placeholder="e.g. 95"
            className="flex-1 bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
          />
          <div className="w-4 h-4 bg-coral/60 border border-coral" />
        </div>
      </div>

      <p className="text-[10px] font-mono text-white/20">
        Thresholds add colored markers to charts when values exceed the defined limits.
      </p>
    </div>
  );
}
