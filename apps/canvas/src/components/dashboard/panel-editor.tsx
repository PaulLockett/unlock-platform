"use client";

import { useState, useCallback } from "react";
import type { Panel, ChartConfig, ChartType, PanelQueryConfig } from "@/types/platform";
import ChartRenderer from "@/components/charts/chart-renderer";
import DataTab from "./panel-editor-tabs/data-tab";
import DisplayTab from "./panel-editor-tabs/display-tab";
import AxesTab from "./panel-editor-tabs/axes-tab";
import ThresholdsTab from "./panel-editor-tabs/thresholds-tab";

type EditorTab = "data" | "display" | "axes" | "thresholds";

interface PanelEditorProps {
  panel: Panel;
  data: Record<string, unknown>[];
  onApply: (updated: Panel) => void;
  onCancel: () => void;
}

export default function PanelEditor({
  panel: initialPanel,
  data,
  onApply,
  onCancel,
}: PanelEditorProps) {
  const [panel, setPanel] = useState<Panel>({ ...initialPanel });
  const [activeTab, setActiveTab] = useState<EditorTab>("data");

  const handleChartConfigChange = useCallback(
    (updates: Partial<ChartConfig>) => {
      setPanel((prev) => ({
        ...prev,
        chart_config: { ...prev.chart_config, ...updates },
      }));
    },
    [],
  );

  const handleQueryConfigChange = useCallback(
    (updates: Partial<PanelQueryConfig>) => {
      setPanel((prev) => ({
        ...prev,
        query_config: { ...prev.query_config, ...updates },
      }));
    },
    [],
  );

  const handleTitleChange = useCallback((title: string) => {
    setPanel((prev) => ({ ...prev, title }));
  }, []);

  const handleChartTypeChange = useCallback((chart_type: ChartType) => {
    setPanel((prev) => ({ ...prev, chart_type }));
  }, []);

  const handleColorSchemeChange = useCallback((color_scheme: string) => {
    setPanel((prev) => ({
      ...prev,
      chart_config: { ...prev.chart_config, color_scheme },
    }));
  }, []);

  const TABS: { id: EditorTab; label: string }[] = [
    { id: "data", label: "Data" },
    { id: "display", label: "Display" },
    { id: "axes", label: "Axes" },
    { id: "thresholds", label: "Thresholds" },
  ];

  return (
    <div className="fixed inset-0 z-[90]">
      {/* Scrim */}
      <div
        className="absolute inset-0"
        style={{ backgroundColor: "rgba(18,18,18,0.7)", backdropFilter: "blur(2px)" }}
        onClick={onCancel}
      />

      {/* Editor panel */}
      <div className="absolute inset-x-0 top-20 bottom-0 flex items-start justify-center px-4 pt-8">
        <div className="relative w-full max-w-6xl bg-charcoal-light border border-white/10 shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <span className="px-2 py-0.5 bg-coral/10 text-coral text-[9px] font-mono tracking-widest">
                EDITING PANEL
              </span>
              <span className="text-sm font-mono text-offwhite">
                {panel.title}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={onCancel}
                className="text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
              >
                Cancel
              </button>
              <button
                onClick={() => onApply(panel)}
                className="px-4 py-1.5 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors"
              >
                Apply Changes
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-white/10">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 text-[10px] font-mono tracking-widest uppercase transition-colors ${
                  activeTab === tab.id
                    ? "text-coral border-b-2 border-coral"
                    : "text-white/40 hover:text-white/60"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content: config + preview */}
          <div className="grid grid-cols-12 min-h-[500px]">
            {/* Config side */}
            <div className="col-span-5 p-6 border-r border-white/10 overflow-y-auto max-h-[600px] no-scrollbar">
              {activeTab === "data" && (
                <DataTab
                  panel={panel}
                  onChartConfigChange={handleChartConfigChange}
                  onQueryConfigChange={handleQueryConfigChange}
                />
              )}
              {activeTab === "display" && (
                <DisplayTab
                  panel={panel}
                  onTitleChange={handleTitleChange}
                  onChartTypeChange={handleChartTypeChange}
                  onColorSchemeChange={handleColorSchemeChange}
                />
              )}
              {activeTab === "axes" && (
                <AxesTab
                  panel={panel}
                  onChartConfigChange={handleChartConfigChange}
                />
              )}
              {activeTab === "thresholds" && <ThresholdsTab panel={panel} />}
            </div>

            {/* Live preview side */}
            <div className="col-span-7 p-6 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-mono tracking-widest text-white/40 uppercase">
                  Live Preview
                </span>
                <span className="text-sm font-display text-sage uppercase">
                  {panel.title}
                </span>
              </div>
              <div className="flex-1 min-h-[400px] bg-charcoal border border-white/5 p-4">
                <ChartRenderer panel={panel} data={data} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
