"use client";

import { useState, useEffect, useCallback } from "react";
import SideNav, { type NavSection } from "@/components/nav/side-nav";
import HeaderBar from "@/components/nav/header-bar";
import ViewCard from "@/components/views/view-card";
import CreateViewCard from "@/components/views/create-view-card";
import CreateViewModal from "@/components/views/create-view-modal";
import type { ViewDefinition } from "@/types/platform";

interface DashboardClientProps {
  userId: string;
  userEmail: string;
  userRole: string;
  isAdmin: boolean;
}

export default function DashboardClient({
  userId,
  userEmail,
  userRole,
  isAdmin,
}: DashboardClientProps) {
  const [section, setSection] = useState<NavSection>("personal");
  const [views, setViews] = useState<ViewDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  const fetchViews = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/views");
      if (res.ok) {
        const data = await res.json();
        setViews((data.items ?? []) as ViewDefinition[]);
      }
    } catch {
      // silently fail — empty grid shown
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchViews();
  }, [fetchViews]);

  // Filter views by section
  const filtered = views.filter((view) => {
    if (section === "personal") return view.created_by === userId;
    if (section === "public") return view.visibility === "public";
    // shared: views not owned by user but accessible
    return view.created_by !== userId;
  });

  const viewCount = filtered.length;

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal">
      <SideNav
        activeSection={section}
        onSectionChange={setSection}
        userEmail={userEmail}
      />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <HeaderBar role={userRole} />

        <div className="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth">
          {/* Hero section */}
          <section className="min-h-[35vh] flex flex-col justify-end px-8 md:px-12 pb-12 border-b border-white/10 relative overflow-hidden">
            {/* Decorative lines */}
            <div className="absolute top-0 right-20 w-[1px] h-full bg-white/5" />
            <div className="absolute top-20 right-0 w-full h-[1px] bg-white/5" />

            <div className="flex items-end justify-between relative z-10">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-2 h-2 bg-coral rounded-full animate-pulse" />
                  <h2 className="text-coral font-serif italic text-2xl md:text-3xl">
                    Welcome back, {isAdmin ? "Administrator" : userEmail.split("@")[0]}
                  </h2>
                </div>
                <h1 className="text-[clamp(5rem,10vw,11rem)] leading-[0.8] font-display text-sage uppercase tracking-tight">
                  My
                  <br />
                  Views
                </h1>
              </div>
              <div className="hidden lg:block text-right mb-2">
                <div className="text-7xl font-display text-white/10 leading-none">
                  {String(viewCount).padStart(2, "0")}
                </div>
                <div className="text-xs tracking-widest text-white/40 mt-1 uppercase border-t border-white/10 pt-2 font-mono">
                  Active Views
                </div>
              </div>
            </div>
          </section>

          {/* View grid */}
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-l border-white/10 auto-rows-fr">
            {loading ? (
              // Loading skeleton cards
              Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="border-r border-b border-white/10 bg-charcoal min-h-[420px] animate-pulse"
                >
                  <div className="p-12 space-y-6">
                    <div className="h-16 w-3/4 bg-white/5 rounded" />
                    <div className="h-4 w-1/2 bg-white/5 rounded" />
                  </div>
                </div>
              ))
            ) : (
              <>
                {filtered.map((view, i) => (
                  <ViewCard key={view.id} view={view} index={i} />
                ))}
                <CreateViewCard onClick={() => setCreateModalOpen(true)} />
                {/* Fill remaining grid cells for clean layout */}
                {filtered.length % 3 < 2 && (
                  <div className="hidden lg:block border-r border-b border-white/10 bg-charcoal" />
                )}
                {filtered.length % 3 === 0 && (
                  <div className="hidden lg:block border-r border-b border-white/10 bg-charcoal" />
                )}
              </>
            )}
          </section>

          {/* Footer */}
          <footer className="p-12 border-t border-white/10 text-white/20 text-xs flex flex-col md:flex-row justify-between items-center gap-4 font-mono">
            <div className="tracking-widest">
              &copy; {new Date().getFullYear()} UNLOCK ALABAMA DATA PLATFORM
            </div>
            <div className="flex gap-8 tracking-wider">
              <span className="hover:text-white cursor-pointer transition-colors">
                PRIVACY
              </span>
              <span className="hover:text-white cursor-pointer transition-colors">
                TERMS
              </span>
              <span className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-sage" />
                STATUS: OPERATIONAL
              </span>
            </div>
          </footer>
        </div>
      </main>

      <CreateViewModal
        open={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          fetchViews();
        }}
      />
    </div>
  );
}
