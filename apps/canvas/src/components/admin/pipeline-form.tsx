"use client";

import { useState, useCallback } from "react";
import { Plus, X, Loader2 } from "lucide-react";

interface TransformRule {
  type: string;
  field: string;
  expression: string;
}

interface PipelineFormProps {
  onCreated: () => void;
  onCancel: () => void;
}

export default function PipelineForm({ onCreated, onCancel }: PipelineFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [scheduleCron, setScheduleCron] = useState("");
  const [rules, setRules] = useState<TransformRule[]>([
    { type: "map", field: "", expression: "" },
  ]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleAddRule = useCallback(() => {
    setRules((prev) => [...prev, { type: "map", field: "", expression: "" }]);
  }, []);

  const handleRemoveRule = useCallback((index: number) => {
    setRules((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleRuleChange = useCallback(
    (index: number, key: keyof TransformRule, value: string) => {
      setRules((prev) =>
        prev.map((r, i) => (i === index ? { ...r, [key]: value } : r)),
      );
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!name.trim()) return;

      setSaving(true);
      setError("");
      try {
        const validRules = rules.filter((r) => r.field.trim());
        const res = await fetch("/api/configure", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            config_type: "pipeline",
            name: name.trim(),
            description: description || undefined,
            source_type: sourceType || undefined,
            schedule_cron: scheduleCron || undefined,
            transform_rules: validRules.map((r) => ({
              type: r.type,
              field: r.field,
              expression: r.expression,
            })),
          }),
        });
        const data = await res.json();
        if (data.success) {
          onCreated();
        } else {
          setError(data.message || "Failed to create pipeline");
        }
      } catch {
        setError("Network error");
      } finally {
        setSaving(false);
      }
    },
    [name, description, sourceType, scheduleCron, rules, onCreated],
  );

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs tracking-[0.3em] text-coral uppercase">
          Create Pipeline
        </h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-white/30 hover:text-white transition-colors tracking-widest uppercase"
        >
          Cancel
        </button>
      </div>

      <div className="space-y-2">
        <label className="text-[10px] text-white/30 uppercase tracking-widest">
          Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Twitter Engagement Pipeline"
          className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          required
        />
      </div>

      <div className="space-y-2">
        <label className="text-[10px] text-white/30 uppercase tracking-widest">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors resize-none"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-[10px] text-white/30 uppercase tracking-widest">
            Source Type
          </label>
          <input
            type="text"
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            placeholder="e.g. twitter, unipile"
            className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          />
        </div>
        <div className="space-y-2">
          <label className="text-[10px] text-white/30 uppercase tracking-widest">
            Schedule (Cron)
          </label>
          <input
            type="text"
            value={scheduleCron}
            onChange={(e) => setScheduleCron(e.target.value)}
            placeholder="e.g. 0 */6 * * *"
            className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          />
        </div>
      </div>

      {/* Rule builder */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <label className="text-[10px] text-white/30 uppercase tracking-widest">
            Transform Rules
          </label>
          <button
            type="button"
            onClick={handleAddRule}
            className="flex items-center gap-1 text-[10px] text-coral tracking-widest uppercase hover:text-coral/80 transition-colors"
          >
            <Plus className="w-3 h-3" />
            Add Rule
          </button>
        </div>

        <div className="space-y-3">
          {rules.map((rule, i) => (
            <div key={i} className="flex items-center gap-3">
              <select
                value={rule.type}
                onChange={(e) => handleRuleChange(i, "type", e.target.value)}
                className="w-24 bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
              >
                <option value="map">Map</option>
                <option value="filter">Filter</option>
                <option value="rename">Rename</option>
                <option value="cast">Cast</option>
                <option value="derive">Derive</option>
              </select>
              <input
                type="text"
                value={rule.field}
                onChange={(e) => handleRuleChange(i, "field", e.target.value)}
                placeholder="Field"
                className="flex-1 bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
              />
              <input
                type="text"
                value={rule.expression}
                onChange={(e) =>
                  handleRuleChange(i, "expression", e.target.value)
                }
                placeholder="Expression"
                className="flex-1 bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
              />
              <button
                type="button"
                onClick={() => handleRemoveRule(i)}
                className="text-white/20 hover:text-coral transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="text-xs text-coral tracking-widest">{error}</div>
      )}

      <div className="flex items-center justify-end gap-4 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-white/30 hover:text-white transition-colors tracking-widest uppercase"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving || !name.trim()}
          className="flex items-center gap-2 px-6 py-2 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors disabled:opacity-50"
        >
          {saving && <Loader2 className="w-3 h-3 animate-spin" />}
          Create
        </button>
      </div>
    </form>
  );
}
