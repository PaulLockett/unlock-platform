"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Pencil, Save, X, Loader2 } from "lucide-react";
import SideNav from "@/components/nav/side-nav";
import PanelGrid from "@/components/dashboard/panel-grid";
import EditToolbar from "@/components/dashboard/edit-toolbar";
import AddPanelModal from "@/components/dashboard/add-panel-modal";
import PanelEditor from "@/components/dashboard/panel-editor";
import { useView } from "@/hooks/use-view";
import type { Panel, LayoutConfig, SchemaDefinition } from "@/types/platform";

interface ViewDashboardProps {
  shareToken: string;
  initialEditMode?: boolean;
  userId?: string | null;
  isAdmin?: boolean;
}

export default function ViewDashboard({
  shareToken,
  initialEditMode = false,
  userId,
  isAdmin = false,
}: ViewDashboardProps) {
  const router = useRouter();
  const { view, schema, permissions, isLoading, isError, errorMessage, refresh } =
    useView(shareToken);

  // Edit mode state
  const [editMode, setEditMode] = useState(initialEditMode);
  const [editPanels, setEditPanels] = useState<Panel[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [addPanelModalOpen, setAddPanelModalOpen] = useState(false);
  const [editingPanel, setEditingPanel] = useState<Panel | undefined>();
  const [editingPanelId, setEditingPanelId] = useState<string | null>(null);

  // Panel data for rendering charts
  const [panelData, setPanelData] = useState<
    Record<string, Record<string, unknown>[]>
  >({});
  const [loadingPanels, setLoadingPanels] = useState<Set<string>>(new Set());

  // Available data sources for panel editor
  const [availableSources, setAvailableSources] = useState<
    { key: string; record_count: number; sample_fields: string[] }[]
  >([]);

  // Track panel IDs to avoid refetching when panels haven't changed
  const prevPanelIdsRef = useRef<string>("");

  // Fetch available sources when entering edit mode
  useEffect(() => {
    if (!editMode) return;
    fetch("/api/sources")
      .then((r) => r.json())
      .then((data) => {
        if (data.success) setAvailableSources(data.sources);
      })
      .catch(() => {});
  }, [editMode]);

  // Fetch data for panels in parallel
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
                source_key: panel.query_config.source_key ?? null,
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

  // When view loads (read mode), fetch panel data
  useEffect(() => {
    if (!view || editMode) return;
    const layout = view.layout_config as LayoutConfig;
    const panels = layout?.panels ?? [];
    if (panels.length > 0) {
      fetchPanelData(panels);
    }
  }, [view, editMode, fetchPanelData]);

  // Sync editPanels when entering edit mode
  useEffect(() => {
    if (editMode && view) {
      const layout = view.layout_config as LayoutConfig;
      setEditPanels(structuredClone(layout?.panels ?? []));
      setSaveError("");
    }
  }, [editMode, view]);

  // Fetch data for edit panels when their IDs change
  useEffect(() => {
    if (!editMode) return;
    const panelIds = editPanels.map((p) => p.id).join(",");
    if (panelIds === prevPanelIdsRef.current) return;
    prevPanelIdsRef.current = panelIds;
    if (editPanels.length > 0) {
      fetchPanelData(editPanels);
    }
  }, [editMode, editPanels, fetchPanelData]);

  // URL sync for edit mode
  useEffect(() => {
    const url = new URL(window.location.href);
    if (editMode) {
      url.searchParams.set("edit", "true");
    } else {
      url.searchParams.delete("edit");
    }
    window.history.replaceState({}, "", url.toString());
  }, [editMode]);

  // Permission check: can this user edit?
  const isOwner = !!(userId && view?.created_by === userId);
  const hasWriteGrant = permissions.some(
    (p) =>
      p.principal_id === userId &&
      (p.permission === "write" || p.permission === "admin"),
  );
  const canEdit = isOwner || hasWriteGrant || isAdmin;

  // Panel mutation callbacks
  const handleRemovePanel = useCallback((panelId: string) => {
    setEditPanels((prev) => prev.filter((p) => p.id !== panelId));
  }, []);

  const handleAddPanel = useCallback((panel: Panel) => {
    setEditPanels((prev) => [...prev, panel]);
  }, []);

  const handleEditPanel = useCallback(
    (panelId: string) => {
      setEditingPanelId(panelId);
    },
    [],
  );

  const handleUpdatePanel = useCallback((updatedPanel: Panel) => {
    setEditPanels((prev) =>
      prev.map((p) => (p.id === updatedPanel.id ? updatedPanel : p)),
    );
  }, []);

  // Save layout via PATCH
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setSaveError("");
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
      if (!data.success) {
        setSaveError(data.message || "Save failed");
        return;
      }

      // If the backend returned a different share_token (old workers create
      // a new view instead of updating), redirect to the new URL so the
      // saved panels are visible.
      const newToken = data.share_token;
      if (newToken && newToken !== shareToken) {
        router.push(`/v/${newToken}`);
        return;
      }

      await refresh();
      setEditMode(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setIsSaving(false);
    }
  }, [shareToken, editPanels, refresh, router]);

  // Discard changes
  const handleDiscard = useCallback(() => {
    const layout = view?.layout_config as LayoutConfig;
    setEditPanels(layout?.panels ?? []);
    setEditMode(false);
    setSaveError("");
  }, [view]);

  // Display panels: edit mode uses local state, view mode uses server state
  const serverPanels = (view?.layout_config as LayoutConfig)?.panels ?? [];
  const displayPanels = editMode ? editPanels : serverPanels;

  // Find a "key metric" panel for the hero section
  const metricPanel = displayPanels.find((p) => p.chart_type === "metric");
  const metricValue = metricPanel ? panelData[metricPanel.id]?.[0] : null;

  // Extract schema fields for editor dropdowns
  const schemaFields: string[] =
    (schema as SchemaDefinition | null)?.fields?.map((f) => f.target_field).filter(Boolean) ?? [];

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

          {/* Edit controls */}
          <div className="flex items-center gap-3">
            {editMode ? (
              <>
                <span className="px-3 py-1 bg-coral/10 text-coral text-[9px] tracking-widest uppercase font-mono border border-coral/20">
                  Editing
                </span>
                {saveError && (
                  <span className="text-coral text-[9px] font-mono max-w-[200px] truncate">
                    {saveError}
                  </span>
                )}
                <button
                  onClick={handleDiscard}
                  disabled={isSaving}
                  className="flex items-center gap-1.5 px-4 py-1.5 text-[10px] tracking-widest uppercase font-mono text-white/40 hover:text-white border border-white/10 hover:border-white/20 transition-colors disabled:opacity-50"
                >
                  <X className="w-3 h-3" />
                  Discard
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-1.5 px-4 py-1.5 text-[10px] tracking-widest uppercase font-mono bg-coral text-charcoal hover:bg-coral/90 transition-colors disabled:opacity-50"
                >
                  {isSaving ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Save className="w-3 h-3" />
                  )}
                  Save
                </button>
              </>
            ) : (
              canEdit && (
                <button
                  onClick={() => setEditMode(true)}
                  className="flex items-center gap-1.5 px-4 py-1.5 text-[10px] tracking-widest uppercase font-mono text-white/40 hover:text-coral border border-white/10 hover:border-coral/30 transition-colors"
                >
                  <Pencil className="w-3 h-3" />
                  Edit
                </button>
              )
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth">
          {/* Hero section */}
          <section className="min-h-[25vh] flex flex-col justify-end px-8 md:px-12 pb-8 border-b border-white/10 relative overflow-hidden">
            <div className="absolute top-0 right-20 w-px h-full bg-white/5" />
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
            onAddPanel={() => {
              setEditingPanel(undefined);
              setAddPanelModalOpen(true);
            }}
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

        {/* Edit mode toolbar */}
        {editMode && (
          <EditToolbar
            panelCount={editPanels.length}
            onAddChart={() => {
              setEditingPanel(undefined);
              setAddPanelModalOpen(true);
            }}
          />
        )}
      </main>

      {/* Add Panel Modal — for creating NEW panels */}
      {addPanelModalOpen && (
        <AddPanelModal
          key={editingPanel?.id ?? "new"}
          open={addPanelModalOpen}
          onClose={() => {
            setAddPanelModalOpen(false);
            setEditingPanel(undefined);
          }}
          onAdd={(panel) => {
            if (editingPanel) {
              handleUpdatePanel(panel);
            } else {
              handleAddPanel(panel);
            }
          }}
          existingPanel={editingPanel}
          existingPanels={editPanels}
          schemaFields={schemaFields}
        />
      )}

      {/* Inline Panel Editor — for editing EXISTING panels */}
      {editingPanelId && (() => {
        const editPanel = editPanels.find((p) => p.id === editingPanelId);
        if (!editPanel) return null;
        return (
          <PanelEditor
            key={editingPanelId}
            panel={editPanel}
            panelData={panelData[editingPanelId] ?? []}
            shareToken={shareToken}
            schemaFields={schemaFields}
            availableSources={availableSources}
            onApply={(updatedPanel) => {
              handleUpdatePanel(updatedPanel);
              setEditingPanelId(null);
            }}
            onCancel={() => setEditingPanelId(null)}
          />
        );
      })()}
    </div>
  );
}
