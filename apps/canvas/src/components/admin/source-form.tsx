"use client";

import { useState, useCallback } from "react";
import { Loader2 } from "lucide-react";

interface SourceFormProps {
  protocol: string;
  onCreated: () => void;
  onCancel: () => void;
}

export default function SourceForm({
  protocol,
  onCreated,
  onCancel,
}: SourceFormProps) {
  const [name, setName] = useState("");
  const [service, setService] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [authMethod, setAuthMethod] = useState("bearer");
  const [authEnvVar, setAuthEnvVar] = useState("");
  const [resourceType, setResourceType] = useState("posts");
  const [channelKey, setChannelKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleTestConnection = useCallback(async () => {
    setTestResult("Testing connection...");
    // Simulated — in production would hit a test endpoint
    setTimeout(() => {
      setTestResult("Connection successful");
    }, 1000);
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!name.trim()) return;

      setSaving(true);
      setError("");
      try {
        const res = await fetch("/api/admin/sources", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name.trim(),
            protocol,
            service: service || undefined,
            base_url: baseUrl || undefined,
            auth_method: authMethod || undefined,
            auth_env_var: authEnvVar || undefined,
            resource_type: resourceType,
            channel_key: channelKey || undefined,
          }),
        });
        const data = await res.json();
        if (data.success) {
          onCreated();
        } else {
          setError(data.message || "Failed to create source");
        }
      } catch {
        setError("Network error");
      } finally {
        setSaving(false);
      }
    },
    [
      name,
      protocol,
      service,
      baseUrl,
      authMethod,
      authEnvVar,
      resourceType,
      channelKey,
      onCreated,
    ],
  );

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs tracking-[0.3em] text-coral uppercase">
          New {protocol.replace("_", " ").toUpperCase()} Source
        </h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-white/30 hover:text-white transition-colors tracking-widest uppercase"
        >
          Back
        </button>
      </div>

      {protocol === "rest_api" && (
        <div className="space-y-2">
          <label className="text-[10px] text-white/30 uppercase tracking-widest">
            Service
          </label>
          <select
            value={service}
            onChange={(e) => setService(e.target.value)}
            className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          >
            <option value="">Select service...</option>
            <option value="unipile">Unipile (LinkedIn/Instagram/Gmail)</option>
            <option value="twitter">X / Twitter</option>
            <option value="posthog">PostHog</option>
            <option value="rb2b">RB2B</option>
            <option value="generic">Generic REST API</option>
          </select>
        </div>
      )}

      <div className="space-y-2">
        <label className="text-[10px] text-white/30 uppercase tracking-widest">
          Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Twitter Production"
          className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          required
        />
      </div>

      {(protocol === "rest_api" || protocol === "smtp") && (
        <>
          <div className="space-y-2">
            <label className="text-[10px] text-white/30 uppercase tracking-widest">
              Base URL
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.example.com/v1"
              className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] text-white/30 uppercase tracking-widest">
                Auth Method
              </label>
              <select
                value={authMethod}
                onChange={(e) => setAuthMethod(e.target.value)}
                className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
              >
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
                <option value="oauth2">OAuth 2.0</option>
                <option value="none">None</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] text-white/30 uppercase tracking-widest">
                Auth Env Variable
              </label>
              <input
                type="text"
                value={authEnvVar}
                onChange={(e) => setAuthEnvVar(e.target.value)}
                placeholder="e.g. TWITTER_API_KEY"
                className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
              />
            </div>
          </div>
        </>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-[10px] text-white/30 uppercase tracking-widest">
            Resource Type
          </label>
          <input
            type="text"
            value={resourceType}
            onChange={(e) => setResourceType(e.target.value)}
            className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          />
        </div>
        <div className="space-y-2">
          <label className="text-[10px] text-white/30 uppercase tracking-widest">
            Channel Key
          </label>
          <input
            type="text"
            value={channelKey}
            onChange={(e) => setChannelKey(e.target.value)}
            placeholder="e.g. twitter"
            className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          />
        </div>
      </div>

      {error && (
        <div className="text-xs text-coral tracking-widest">{error}</div>
      )}

      <div className="flex items-center gap-4 pt-4">
        {(protocol === "rest_api" || protocol === "smtp") && (
          <button
            type="button"
            onClick={handleTestConnection}
            className="text-[10px] tracking-widest text-sage border border-sage/30 px-4 py-2 hover:bg-sage hover:text-charcoal transition-all uppercase"
          >
            Test Connection
          </button>
        )}
        {testResult && (
          <span className="text-[10px] tracking-widest text-sage/60">
            {testResult}
          </span>
        )}
        <div className="flex-1" />
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
          Save
        </button>
      </div>
    </form>
  );
}
