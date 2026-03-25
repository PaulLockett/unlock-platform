"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, Loader2 } from "lucide-react";
import SideNav from "@/components/nav/side-nav";
import SchemaForm from "@/components/admin/schema-form";

interface SchemaConfig {
  name: string;
  description?: string;
  schema_type?: string;
  version?: number;
  status?: string;
  fields?: Record<string, unknown>[];
  created_at?: string;
}

export default function AdminSchemasPage() {
  const [schemas, setSchemas] = useState<SchemaConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  const fetchSchemas = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/configs?type=schema");
      const data = await res.json();
      if (data.success) setSchemas(data.configs ?? []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchemas();
  }, [fetchSchemas]);

  const handleCreated = useCallback(() => {
    setShowCreate(false);
    fetchSchemas();
  }, [fetchSchemas]);

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal">
      <SideNav />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40 shrink-0">
          <div className="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50">
            <span className="text-white/30">Admin</span>
            <span>/</span>
            <span className="text-coral">Schemas</span>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-1.5 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors"
          >
            <Plus className="w-3 h-3" />
            Create Schema
          </button>
        </header>

        <div className="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth">
          {showCreate && (
            <section className="px-8 md:px-12 py-12 border-b border-white/10">
              <SchemaForm
                onCreated={handleCreated}
                onCancel={() => setShowCreate(false)}
              />
            </section>
          )}

          <section className="px-8 md:px-12 py-12">
            <h2 className="text-xs tracking-[0.3em] text-white/40 uppercase mb-8">
              Registered Schemas ({schemas.length})
            </h2>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-6 h-6 text-coral animate-spin" />
              </div>
            ) : schemas.length === 0 ? (
              <div className="text-center py-20 text-white/20 text-xs tracking-widest">
                NO SCHEMAS REGISTERED
              </div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-4 px-4 py-2 text-[10px] tracking-widest text-white/30 uppercase border-b border-white/5">
                  <span>Name</span>
                  <span>Type</span>
                  <span>Version</span>
                  <span>Status</span>
                  <span>Fields</span>
                  <span>Created</span>
                </div>

                {schemas.map((schema, i) => (
                  <div
                    key={i}
                    className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr] gap-4 px-4 py-3 border-b border-white/5 hover:bg-white/[0.02] transition-colors items-center"
                  >
                    <span className="text-sm text-offwhite font-mono truncate">
                      {schema.name}
                    </span>
                    <span className="text-xs text-white/40">
                      {schema.schema_type ?? "—"}
                    </span>
                    <span className="text-xs text-white/40">
                      v{schema.version ?? 1}
                    </span>
                    <span>
                      <span
                        className={`inline-flex items-center gap-1.5 text-[10px] tracking-widest uppercase ${
                          schema.status === "active"
                            ? "text-sage"
                            : "text-white/30"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            schema.status === "active"
                              ? "bg-sage"
                              : "bg-white/20"
                          }`}
                        />
                        {schema.status ?? "active"}
                      </span>
                    </span>
                    <span className="text-xs text-white/40">
                      {schema.fields?.length ?? 0}
                    </span>
                    <span className="text-xs text-white/40">
                      {schema.created_at
                        ? new Date(schema.created_at).toLocaleDateString()
                        : "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>

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
