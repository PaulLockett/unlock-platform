"use client";

import { Search } from "lucide-react";
import { format } from "date-fns";

interface HeaderBarProps {
  role?: string;
  children?: React.ReactNode;
}

export default function HeaderBar({ role = "User", children }: HeaderBarProps) {
  const today = format(new Date(), "MMMM d, yyyy");

  return (
    <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40 shrink-0">
      <div className="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50 font-mono">
        <span className="text-coral">{role}</span>
        <span>/</span>
        <span>{today}</span>
      </div>

      <div className="flex items-center gap-6">
        {children}
        <div className="relative hidden md:block group">
          <input
            type="text"
            placeholder="SEARCH VIEWS..."
            className="bg-transparent border-b border-white/20 py-1 pr-8 text-sm focus:outline-none focus:border-sage placeholder-white/20 w-48 font-mono transition-colors"
          />
          <Search className="w-4 h-4 text-white/40 absolute right-0 top-1 group-hover:text-sage transition-colors" />
        </div>
      </div>
    </header>
  );
}
