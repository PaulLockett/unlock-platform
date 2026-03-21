"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import SideNav from "@/components/nav/side-nav";
import PanelGrid from "@/components/dashboard/panel-grid";
import { useView } from "@/hooks/use-view";
import type {
  Panel,
  LayoutConfig,
} from "@/types/platform";

interface ViewDashboardProps {
  shareToken: string;
  initialEditMode?: boolean;
}

export default function ViewDashboard({
  shareToken,
}: ViewDashboardProps) {
  const { view, isLoading, isError, errorMessage } = useView(shareToken);
  const [panelData, setPanelData] = useState<
    Record<string, Record<string, unknown>[]>
  >({});
  const [loadingPanels, setLoadingPanels] = useState<Set<string>>(new Set());

  // Fetch data for each panel in parallel
  const fetchPanelData = useCallback(
    async (panels: Panel[]) => {
      const newLoadingPanels = new Set(panels.map((p) => p.id));
      setLoadingPanels(newLoadingPanels);

      const results: Record<string, Record<string, unknown>[]> = {};

      await Promise.all(
        panels.map(async (panel) => {
          try {
            const res = await fetch("/api/query", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                share_token: shareToken,
                channel_key: panel.query_config.channel_key ?? null,
                engagement_type: panel.query_config.engagement_type ?? null,
                since: panel.query_config.since ?? null,
                until: panel.query_config.until ?? null,
                limit: 1000,
                offset: 0,
              }),
            });
            const data = await res.json();
            results[panel.id] = data.success ? data.records : [];
          } catch {
            results[panel.id] = [];
          } finally {
            setLoadingPanels((prev) => {
              const next = new Set(prev);
              next.delete(panel.id);
              return next;
            });
          }
        }),
      );

      setPanelData(results);
    },
    [shareToken],
  );

  // When view loads, fetch panel data
  useEffect(() => {
    if (!view) return;
    const layout = view.layout_config as LayoutConfig;
    const panels = layout?.panels ?? [];
    if (panels.length > 0) {
      fetchPanelData(panels);
    }
  }, [view, fetchPanelData]);

  const displayPanels = (view?.layout_config as LayoutConfig)?.panels ?? [];

  // Find a "key metric" panel for the hero section
  const metricPanel = displayPanels.find((p) => p.chart_type === "metric");
  const metricValue = metricPanel ? panelData[metricPanel.id]?.[0] : null;

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-charcoal">
        <div className="w-8 h-8 border-2 border-coral/30 border-t-coral rounded-full animate-spin" />
      </div>
    );
  }

  if (isError || !view) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-charcoal gap-4">
        <div className="text-white/40 text-sm font-mono tracking-widest uppercase">
          {errorMessage || "View not found"}
        </div>
        <Link
          href="/"
          className="text-coral text-xs font-mono tracking-widest hover:underline"
        >
          BACK TO VIEWS
        </Link>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal">
      <SideNav />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Header */}
        <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40 shrink-0">
          <div className="flex items-center gap-4 text-xs tracking-widest uppercase font-mono">
            <Link
              href="/"
              className="text-white/40 hover:text-white transition-colors flex items-center gap-2"
            >
              <ArrowLeft className="w-3 h-3" />
              Back to Views
            </Link>
            <span className="text-white/20">/</span>
            <span className="text-offwhite">{view.name}</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth">
          {/* Hero section */}
          <section className="min-h-[25vh] flex flex-col justify-end px-8 md:px-12 pb-8 border-b border-white/10 relative overflow-hidden">
            <div className="absolute top-0 right-20 w-[1px] h-full bg-white/5" />
            <div className="flex items-end justify-between relative z-10">
              <div>
                <h1 className="text-[clamp(3rem,8vw,8rem)] leading-[0.85] font-display text-sage uppercase tracking-tight">
                  {view.name}
                </h1>
                {view.description && (
                  <p className="font-serif italic text-white/60 mt-4 text-lg max-w-lg">
                    {view.description}
                  </p>
                )}
              </div>
              {metricPanel && metricValue && (
                <div className="hidden lg:block text-right">
                  <div className="text-5xl font-display text-coral leading-none">
                    {String(
                      metricValue[
                        metricPanel.chart_config.value_field ?? "value"
                      ] ?? "—",
                    )}
                  </div>
                  <div className="text-[10px] tracking-widest text-white/40 mt-1 uppercase font-mono">
                    {metricPanel.chart_config.label ?? metricPanel.title}
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Panel grid */}
          <PanelGrid
            panels={displayPanels}
            panelData={panelData}
            loadingPanels={loadingPanels}
            editMode={false}
            onRemovePanel={() => {}}
            onEditPanel={() => {}}
            onAddPanel={() => {}}
          />

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
    </div>
  );
}
