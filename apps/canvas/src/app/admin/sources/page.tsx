"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Plus,
  RefreshCw,
  Globe,
  Upload,
  Webhook,
  Database,
  HardDrive,
  Mail,
  Loader2,
} from "lucide-react";
import SideNav from "@/components/nav/side-nav";
import SourceForm from "@/components/admin/source-form";
import FileUpload from "@/components/admin/file-upload";

type Protocol =
  | "rest_api"
  | "file_upload"
  | "webhook"
  | "s3"
  | "database"
  | "smtp";

interface DataSource {
  id: string;
  name: string;
  protocol: Protocol;
  service?: string;
  status: string;
  channel_key?: string;
  resource_type: string;
  created_at: string;
}

const PROTOCOL_OPTIONS: {
  key: Protocol;
  label: string;
  icon: React.ReactNode;
  available: boolean;
}[] = [
  { key: "rest_api", label: "REST API", icon: <Globe className="w-5 h-5" />, available: true },
  { key: "file_upload", label: "File Upload", icon: <Upload className="w-5 h-5" />, available: true },
  { key: "webhook", label: "Webhook", icon: <Webhook className="w-5 h-5" />, available: false },
  { key: "s3", label: "S3 / Cloud", icon: <HardDrive className="w-5 h-5" />, available: false },
  { key: "database", label: "Database", icon: <Database className="w-5 h-5" />, available: false },
  { key: "smtp", label: "SMTP / Email", icon: <Mail className="w-5 h-5" />, available: true },
];

export default function AdminSourcesPage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [selectedProtocol, setSelectedProtocol] = useState<Protocol | null>(null);
  const [ingesting, setIngesting] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/admin/sources");
      const data = await res.json();
      if (data.success) setSources(data.sources);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const handleTriggerIngest = useCallback(
    async (source: DataSource) => {
      setIngesting(source.id);
      try {
        await fetch("/api/admin/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            source_name: source.name,
            source_type: source.protocol === "rest_api" ? (source.service ?? "generic") : source.protocol,
            resource_type: source.resource_type,
            channel_key: source.channel_key ?? null,
          }),
        });
        await fetchSources();
      } catch {
        // silent
      } finally {
        setIngesting(null);
      }
    },
    [fetchSources],
  );

  const handleSourceCreated = useCallback(() => {
    setShowAdd(false);
    setSelectedProtocol(null);
    fetchSources();
  }, [fetchSources]);

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal">
      <SideNav />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40 shrink-0">
          <div className="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50">
            <span className="text-white/30">Admin</span>
            <span>/</span>
            <span className="text-coral">Data Sources</span>
          </div>
          <button
            onClick={() => {
              setShowAdd(true);
              setSelectedProtocol(null);
            }}
            className="flex items-center gap-2 px-4 py-1.5 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors"
          >
            <Plus className="w-3 h-3" />
            Add Source
          </button>
        </header>

        <div className="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth">
          {/* Protocol selector (step 1 of add flow) */}
          {showAdd && !selectedProtocol && (
            <section className="px-8 md:px-12 py-12 border-b border-white/10">
              <h2 className="text-xs tracking-[0.3em] text-coral uppercase mb-8">
                Select Protocol
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {PROTOCOL_OPTIONS.map((proto) => (
                  <button
                    key={proto.key}
                    disabled={!proto.available}
                    onClick={() => setSelectedProtocol(proto.key)}
                    className={`p-6 border flex flex-col items-center gap-3 transition-all ${
                      proto.available
                        ? "border-white/10 hover:border-coral text-white/60 hover:text-coral cursor-pointer"
                        : "border-white/5 text-white/20 cursor-not-allowed"
                    }`}
                  >
                    {proto.icon}
                    <span className="text-[10px] tracking-widest uppercase">
                      {proto.label}
                    </span>
                    {!proto.available && (
                      <span className="text-[8px] tracking-widest text-white/20 uppercase">
                        Coming Soon
                      </span>
                    )}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setShowAdd(false)}
                className="mt-6 text-xs text-white/30 hover:text-white transition-colors tracking-widest uppercase"
              >
                Cancel
              </button>
            </section>
          )}

          {/* Source form (step 2) */}
          {showAdd && selectedProtocol && selectedProtocol !== "file_upload" && (
            <section className="px-8 md:px-12 py-12 border-b border-white/10">
              <SourceForm
                protocol={selectedProtocol}
                onCreated={handleSourceCreated}
                onCancel={() => {
                  setSelectedProtocol(null);
                }}
              />
            </section>
          )}

          {/* File upload form */}
          {showAdd && selectedProtocol === "file_upload" && (
            <section className="px-8 md:px-12 py-12 border-b border-white/10">
              <FileUpload
                onUploaded={handleSourceCreated}
                onCancel={() => setSelectedProtocol(null)}
              />
            </section>
          )}

          {/* Source list */}
          <section className="px-8 md:px-12 py-12">
            <h2 className="text-xs tracking-[0.3em] text-white/40 uppercase mb-8">
              Registered Sources ({sources.length})
            </h2>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-6 h-6 text-coral animate-spin" />
              </div>
            ) : sources.length === 0 ? (
              <div className="text-center py-20 text-white/20 text-xs tracking-widest">
                NO DATA SOURCES REGISTERED
              </div>
            ) : (
              <div className="space-y-2">
                {/* Table header */}
                <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-4 px-4 py-2 text-[10px] tracking-widest text-white/30 uppercase border-b border-white/5">
                  <span>Name</span>
                  <span>Protocol</span>
                  <span>Service</span>
                  <span>Status</span>
                  <span>Channel</span>
                  <span>Actions</span>
                </div>

                {sources.map((source) => (
                  <div
                    key={source.id}
                    className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-4 px-4 py-3 border-b border-white/5 hover:bg-white/[0.02] transition-colors items-center"
                  >
                    <span className="text-sm text-offwhite font-mono truncate">
                      {source.name}
                    </span>
                    <span className="text-xs text-white/40">
                      {source.protocol.replace("_", " ").toUpperCase()}
                    </span>
                    <span className="text-xs text-white/40">
                      {source.service ?? "—"}
                    </span>
                    <span>
                      <span
                        className={`inline-flex items-center gap-1.5 text-[10px] tracking-widest uppercase ${
                          source.status === "active"
                            ? "text-sage"
                            : "text-white/30"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            source.status === "active"
                              ? "bg-sage"
                              : "bg-white/20"
                          }`}
                        />
                        {source.status}
                      </span>
                    </span>
                    <span className="text-xs text-white/40">
                      {source.channel_key ?? "—"}
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleTriggerIngest(source)}
                        disabled={ingesting === source.id}
                        className="flex items-center gap-1 text-[10px] tracking-widest text-coral hover:text-coral/80 transition-colors uppercase disabled:opacity-50"
                      >
                        {ingesting === source.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <RefreshCw className="w-3 h-3" />
                        )}
                        Ingest
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Footer */}
          <footer className="p-12 border-t border-white/10 text-white/20 text-xs flex flex-col md:flex-row justify-between items-center gap-4 font-mono">
            <div className="tracking-widest">
              &copy; {new Date().getFullYear()} UNLOCK ALABAMA DATA PLATFORM
            </div>
            <div className="flex items-center gap-2 text-coral tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-coral animate-pulse" />
              SYSTEM OPERATIONAL
            </div>
          </footer>
        </div>
      </main>
    </div>
  );
}
