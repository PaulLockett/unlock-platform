"use client";

import { useState } from "react";
import { X, Clock, Loader2 } from "lucide-react";

interface ScheduleModalProps {
  sourceName: string;
  sourceType: string;
  resourceType: string;
  channelKey?: string;
  onClose: () => void;
  onScheduled: () => void;
}

const CRON_PRESETS = [
  { label: "Every hour", cron: "0 * * * *" },
  { label: "Every 6 hours", cron: "0 */6 * * *" },
  { label: "Daily at midnight", cron: "0 0 * * *" },
  { label: "Daily at 9am", cron: "0 9 * * *" },
  { label: "Every Monday at 9am", cron: "0 9 * * MON" },
  { label: "Custom", cron: "" },
];

export default function ScheduleModal({
  sourceName,
  sourceType,
  resourceType,
  channelKey,
  onClose,
  onScheduled,
}: ScheduleModalProps) {
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [customCron, setCustomCron] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const cronExpression =
    CRON_PRESETS[selectedPreset].cron || customCron;

  const handleSubmit = async () => {
    if (!cronExpression.trim()) {
      setError("Enter a cron expression");
      return;
    }

    setSaving(true);
    setError("");
    try {
      const res = await fetch("/api/admin/schedules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_name: sourceName,
          cron_expression: cronExpression,
          source_type: sourceType,
          resource_type: resourceType,
          channel_key: channelKey ?? null,
        }),
      });
      const data = await res.json();
      if (data.success) {
        onScheduled();
      } else {
        setError(data.message || "Failed to create schedule");
      }
    } catch {
      setError("Failed to create schedule");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-100 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-charcoal/80 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative w-full max-w-md mx-4 bg-charcoal-light border border-white/10">
        <div className="absolute -top-px -left-px w-8 h-8 border-t-2 border-l-2 border-coral" />
        <div className="absolute -top-px -right-px w-8 h-8 border-t-2 border-r-2 border-coral" />

        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div>
            <div className="text-[10px] tracking-widest text-coral uppercase font-mono">
              Schedule Ingest
            </div>
            <div className="text-lg font-display text-sage uppercase mt-1">
              {sourceName}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-3">
              Frequency
            </label>
            <div className="grid grid-cols-2 gap-2">
              {CRON_PRESETS.map((preset, i) => (
                <button
                  key={preset.label}
                  onClick={() => setSelectedPreset(i)}
                  className={`flex items-center gap-2 px-3 py-2.5 border text-xs font-mono transition-colors ${
                    selectedPreset === i
                      ? "border-coral bg-coral/10 text-coral"
                      : "border-white/10 text-white/40 hover:text-white/60 hover:border-white/20"
                  }`}
                >
                  <Clock className="w-3 h-3" />
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom cron input */}
          {CRON_PRESETS[selectedPreset].label === "Custom" && (
            <div>
              <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
                Cron Expression
              </label>
              <input
                type="text"
                value={customCron}
                onChange={(e) => setCustomCron(e.target.value)}
                placeholder="0 */2 * * *"
                className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
              />
              <p className="mt-2 text-[9px] font-mono text-white/20 tracking-wider">
                Format: minute hour day-of-month month day-of-week
              </p>
            </div>
          )}

          {/* Preview */}
          {cronExpression && (
            <div className="px-3 py-2 bg-white/[0.02] border border-white/5 text-[10px] font-mono text-white/30 tracking-wider">
              Cron: <span className="text-coral">{cronExpression}</span>
              <span className="text-white/20 ml-2">
                (America/Chicago)
              </span>
            </div>
          )}

          {error && (
            <p className="text-coral text-xs font-mono">{error}</p>
          )}
        </div>

        <div className="flex items-center justify-end gap-4 p-6 pt-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving || !cronExpression}
            className="flex items-center gap-2 px-4 py-2 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors disabled:opacity-50"
          >
            {saving ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Clock className="w-3 h-3" />
            )}
            Create Schedule
          </button>
        </div>
      </div>
    </div>
  );
}
