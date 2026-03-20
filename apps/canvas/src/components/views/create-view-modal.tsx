"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { X, ArrowRight, Loader2 } from "lucide-react";

interface CreateViewModalProps {
  open: boolean;
  onClose: () => void;
}

export default function CreateViewModal({ open, onClose }: CreateViewModalProps) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCreate = useCallback(async () => {
    if (!name.trim()) {
      setError("View name is required");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/configure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config_type: "view",
          name: name.trim(),
          description: description.trim() || null,
          schema_id: "", // empty — panels added in edit mode
          layout_config: { grid_columns: 6, panels: [] },
          visibility: "public",
        }),
      });

      const result = await res.json();
      if (!result.success) {
        setError(result.message || "Failed to create view");
        return;
      }

      // Redirect to edit mode
      router.push(`/v/${result.share_token}?edit=true`);
      onClose();
    } catch {
      setError("Failed to create view");
    } finally {
      setLoading(false);
    }
  }, [name, description, router, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-charcoal/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg mx-4 bg-charcoal-light border border-white/10">
        {/* Corner accents */}
        <div className="absolute -top-px -left-px w-8 h-8 border-t-2 border-l-2 border-coral" />
        <div className="absolute -top-px -right-px w-8 h-8 border-t-2 border-r-2 border-coral" />
        <div className="absolute -bottom-px -left-px w-8 h-8 border-b-2 border-l-2 border-coral" />
        <div className="absolute -bottom-px -right-px w-8 h-8 border-b-2 border-r-2 border-coral" />

        {/* Header */}
        <div className="flex items-center justify-between p-8 pb-0">
          <div>
            <div className="text-[10px] tracking-widest text-coral uppercase font-mono">
              New Dashboard
            </div>
            <h2 className="text-3xl font-display uppercase text-sage mt-1">
              Create View
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="p-8 space-y-6">
          <div>
            <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
              View Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Q4 Revenue Metrics"
              className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-[10px] tracking-widest text-white/40 uppercase font-mono mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Comprehensive tracking of donor pipeline and grant allocation."
              rows={3}
              className="w-full bg-charcoal border border-white/10 px-4 py-3 text-sm font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors resize-none"
            />
          </div>

          {error && (
            <p className="text-coral text-xs font-mono">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-4 p-8 pt-0">
          <button
            onClick={onClose}
            className="px-6 py-2 text-sm font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2 bg-coral text-charcoal text-sm font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                Create View
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
