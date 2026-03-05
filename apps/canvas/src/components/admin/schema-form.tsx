"use client";

import { useState, useCallback } from "react";
import { Plus, X, Loader2 } from "lucide-react";

interface SchemaField {
  name: string;
  type: string;
  required: boolean;
}

interface SchemaFormProps {
  onCreated: () => void;
  onCancel: () => void;
}

export default function SchemaForm({ onCreated, onCancel }: SchemaFormProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [schemaType, setSchemaType] = useState("standard");
  const [fields, setFields] = useState<SchemaField[]>([
    { name: "", type: "string", required: false },
  ]);
  const [funnelStages, setFunnelStages] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleAddField = useCallback(() => {
    setFields((prev) => [...prev, { name: "", type: "string", required: false }]);
  }, []);

  const handleRemoveField = useCallback((index: number) => {
    setFields((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleFieldChange = useCallback(
    (index: number, key: keyof SchemaField, value: string | boolean) => {
      setFields((prev) =>
        prev.map((f, i) => (i === index ? { ...f, [key]: value } : f)),
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
        const validFields = fields.filter((f) => f.name.trim());
        const res = await fetch("/api/configure", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            config_type: "schema",
            name: name.trim(),
            description: description || undefined,
            schema_type: schemaType,
            fields: validFields.map((f) => ({
              name: f.name,
              type: f.type,
              required: f.required,
            })),
            funnel_stages:
              schemaType === "funnel" && funnelStages.length > 0
                ? funnelStages.map((s, i) => ({ name: s, order: i }))
                : undefined,
          }),
        });
        const data = await res.json();
        if (data.success) {
          onCreated();
        } else {
          setError(data.message || "Failed to create schema");
        }
      } catch {
        setError("Network error");
      } finally {
        setSaving(false);
      }
    },
    [name, description, schemaType, fields, funnelStages, onCreated],
  );

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs tracking-[0.3em] text-coral uppercase">
          Create Schema
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
          placeholder="e.g. Social Media Engagement"
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

      <div className="space-y-2">
        <label className="text-[10px] text-white/30 uppercase tracking-widest">
          Type
        </label>
        <select
          value={schemaType}
          onChange={(e) => setSchemaType(e.target.value)}
          className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
        >
          <option value="standard">Standard</option>
          <option value="funnel">Funnel</option>
          <option value="timeseries">Timeseries</option>
        </select>
      </div>

      {/* Field builder */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <label className="text-[10px] text-white/30 uppercase tracking-widest">
            Fields
          </label>
          <button
            type="button"
            onClick={handleAddField}
            className="flex items-center gap-1 text-[10px] text-coral tracking-widest uppercase hover:text-coral/80 transition-colors"
          >
            <Plus className="w-3 h-3" />
            Add Field
          </button>
        </div>

        <div className="space-y-3">
          {fields.map((field, i) => (
            <div key={i} className="flex items-center gap-3">
              <input
                type="text"
                value={field.name}
                onChange={(e) => handleFieldChange(i, "name", e.target.value)}
                placeholder="Field name"
                className="flex-1 bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
              />
              <select
                value={field.type}
                onChange={(e) => handleFieldChange(i, "type", e.target.value)}
                className="w-28 bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
              >
                <option value="string">String</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
                <option value="date">Date</option>
                <option value="json">JSON</option>
              </select>
              <label className="flex items-center gap-1.5 text-[10px] text-white/30 cursor-pointer">
                <input
                  type="checkbox"
                  checked={field.required}
                  onChange={(e) =>
                    handleFieldChange(i, "required", e.target.checked)
                  }
                  className="accent-coral"
                />
                Req
              </label>
              <button
                type="button"
                onClick={() => handleRemoveField(i)}
                className="text-white/20 hover:text-coral transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Funnel stages (conditional) */}
      {schemaType === "funnel" && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <label className="text-[10px] text-white/30 uppercase tracking-widest">
              Funnel Stages
            </label>
            <button
              type="button"
              onClick={() => setFunnelStages((prev) => [...prev, ""])}
              className="flex items-center gap-1 text-[10px] text-coral tracking-widest uppercase hover:text-coral/80 transition-colors"
            >
              <Plus className="w-3 h-3" />
              Add Stage
            </button>
          </div>
          <div className="space-y-2">
            {funnelStages.map((stage, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-[10px] text-white/20 w-6">{i + 1}.</span>
                <input
                  type="text"
                  value={stage}
                  onChange={(e) =>
                    setFunnelStages((prev) =>
                      prev.map((s, j) => (j === i ? e.target.value : s)),
                    )
                  }
                  placeholder="Stage name"
                  className="flex-1 bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
                />
                <button
                  type="button"
                  onClick={() =>
                    setFunnelStages((prev) => prev.filter((_, j) => j !== i))
                  }
                  className="text-white/20 hover:text-coral transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

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
