"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { ArrowLeft, Share2, MessageCircle, Pencil, Loader2 } from "lucide-react";
import SideNav from "@/components/nav/side-nav";
import PanelGrid from "@/components/dashboard/panel-grid";
import EditToolbar from "@/components/dashboard/edit-toolbar";
import PanelEditor from "@/components/dashboard/panel-editor";
import ShareDialog from "@/components/views/share-dialog";
import ChatPanel from "@/components/chat/chat-panel";
import type {
  ViewDefinition,
  SchemaDefinition,
  ViewPermission,
  Panel,
  LayoutConfig,
  ChartType,
} from "@/types/platform";

interface ViewDashboardProps {
  shareToken: string;
  initialEditMode?: boolean;
}

export default function ViewDashboard({
  shareToken,
  initialEditMode = false,
}: ViewDashboardProps) {
  const [view, setView] = useState<ViewDefinition | null>(null);
  const [_schema, setSchema] = useState<SchemaDefinition | null>(null);
  const [permissions, setPermissions] = useState<ViewPermission[]>([]);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editMode, setEditMode] = useState(initialEditMode);
  const [saving, setSaving] = useState(false);
  const [panelData, setPanelData] = useState<
    Record<string, Record<string, unknown>[]>
  >({});
  const [loadingPanels, setLoadingPanels] = useState<Set<string>>(new Set());

  // Edit mode: working copy of panels
  const [editPanels, setEditPanels] = useState<Panel[]>([]);
  const [dirty, setDirty] = useState(false);

  // Panel editor state
  const [editingPanelId, setEditingPanelId] = useState<string | null>(null);

  // Track original panels for discard
  const originalPanelsRef = useRef<Panel[]>([]);

  // Fetch view configuration
  const fetchView = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/views/${shareToken}`);
      const data = await res.json();

      if (!data.success) {
        setError(data.message || "Failed to load view");
        return;
      }

      setView(data.view);
      setSchema(data.schema_def);
      setPermissions(data.permissions ?? []);
    } catch {
      setError("Failed to load view");
    } finally {
      setLoading(false);
    }
  }, [shareToken]);

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

  useEffect(() => {
    fetchView();
  }, [fetchView]);

  // When view loads, fetch panel data
  useEffect(() => {
    if (!view) return;
    const layout = view.layout_config as LayoutConfig;
    const panels = layout?.panels ?? [];
    if (panels.length > 0) {
      fetchPanelData(panels);
    }
  }, [view, fetchPanelData]);

  // Enter edit mode: snapshot panels
  useEffect(() => {
    if (editMode && view) {
      const layout = view.layout_config as LayoutConfig;
      const panels = layout?.panels ?? [];
      setEditPanels([...panels]);
      originalPanelsRef.current = [...panels];
      setDirty(false);
    }
  }, [editMode, view]);

  const displayPanels = editMode
    ? editPanels
    : ((view?.layout_config as LayoutConfig)?.panels ?? []);

  // Find a "key metric" panel for the hero section
  const metricPanel = displayPanels.find((p) => p.chart_type === "metric");
  const metricValue = metricPanel ? panelData[metricPanel.id]?.[0] : null;

  // Edit operations
  const handleAddPanel = useCallback(() => {
    const newPanel: Panel = {
      id: `panel-${crypto.randomUUID()}`,
      title: "New Panel",
      chart_type: "bar" as ChartType,
      position: { x: 0, y: 0, w: 3, h: 2 },
      chart_config: { x_axis: "name", y_axis: "value" },
      query_config: {},
    };
    setEditPanels((prev) => [...prev, newPanel]);
    setDirty(true);
  }, []);

  const handleRemovePanel = useCallback((panelId: string) => {
    setEditPanels((prev) => prev.filter((p) => p.id !== panelId));
    setDirty(true);
  }, []);

  const handleEditPanel = useCallback((panelId: string) => {
    setEditingPanelId(panelId);
  }, []);

  const handleApplyPanelEdit = useCallback((updated: Panel) => {
    setEditPanels((prev) =>
      prev.map((p) => (p.id === updated.id ? updated : p)),
    );
    setEditingPanelId(null);
    setDirty(true);
  }, []);

  const handleDiscard = useCallback(() => {
    setEditPanels([...originalPanelsRef.current]);
    setDirty(false);
    setEditMode(false);
  }, []);

  const handleSave = useCallback(async () => {
    if (!view) return;
    setSaving(true);
    try {
      const res = await fetch(`/api/views/${shareToken}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          layout_config: {
            grid_columns: 6,
            panels: editPanels,
          },
        }),
      });
      const data = await res.json();
      if (data.success) {
        // Refresh view from server
        await fetchView();
        setEditMode(false);
        setDirty(false);
      }
    } catch {
      // silent fail — user sees unsaved state
    } finally {
      setSaving(false);
    }
  }, [view, shareToken, editPanels, fetchView]);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-charcoal">
        <div className="w-8 h-8 border-2 border-coral/30 border-t-coral rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !view) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-charcoal gap-4">
        <div className="text-white/40 text-sm font-mono tracking-widest uppercase">
          {error || "View not found"}
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
            {editMode && (
              <span className="px-2 py-0.5 bg-coral/10 text-coral text-[9px] tracking-widest">
                EDITING
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            {editMode ? (
              <>
                <button
                  onClick={handleDiscard}
                  className="text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
                >
                  Discard
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || !dirty}
                  className="flex items-center gap-2 px-4 py-1.5 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors disabled:opacity-50"
                >
                  {saving && <Loader2 className="w-3 h-3 animate-spin" />}
                  Save Layout
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setShareDialogOpen(true)}
                  className="flex items-center gap-2 text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
                >
                  <Share2 className="w-3 h-3" />
                  Share
                </button>
                <button
                  onClick={() => setChatOpen(!chatOpen)}
                  className="flex items-center gap-2 text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
                >
                  <MessageCircle className="w-3 h-3" />
                  Comments
                </button>
                <button
                  onClick={() => setEditMode(true)}
                  className="flex items-center gap-2 text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
                >
                  <Pencil className="w-3 h-3" />
                  Edit
                </button>
              </>
            )}
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
            editMode={editMode}
            onRemovePanel={handleRemovePanel}
            onEditPanel={handleEditPanel}
            onAddPanel={handleAddPanel}
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

          {/* Edit mode footer */}
          {editMode && (
            <div className="sticky bottom-0 bg-charcoal-light border-t border-white/10 px-8 py-4 flex items-center justify-between z-30">
              <button
                onClick={handleDiscard}
                className="text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
              >
                EXIT EDIT MODE
              </button>
              <span className="text-[10px] font-mono tracking-widest text-coral/60 uppercase">
                {dirty ? "SESSION: UNSAVED CHANGES" : "SESSION: NO CHANGES"}
              </span>
            </div>
          )}
        </div>

        {/* Floating toolbar (edit mode only) */}
        {editMode && (
          <EditToolbar
            panelCount={editPanels.length}
            onAddChart={handleAddPanel}
          />
        )}
      </main>

      {/* Share dialog */}
      <ShareDialog
        open={shareDialogOpen}
        onClose={() => setShareDialogOpen(false)}
        shareToken={shareToken}
        viewId={view.id}
        permissions={permissions}
        visibility={view.visibility ?? "public"}
        createdBy={view.created_by ?? ""}
      />

      {/* Chat panel */}
      <ChatPanel
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        viewName={view.name}
        currentUserEmail=""
      />

      {/* Panel editor overlay */}
      {editingPanelId && (() => {
        const editingPanel = editPanels.find((p) => p.id === editingPanelId);
        if (!editingPanel) return null;
        return (
          <PanelEditor
            panel={editingPanel}
            panelData={panelData[editingPanelId] ?? []}
            shareToken={shareToken}
            schemaFields={[]}
            onApply={handleApplyPanelEdit}
            onCancel={() => setEditingPanelId(null)}
          />
        );
      })()}
    </div>
  );
}
