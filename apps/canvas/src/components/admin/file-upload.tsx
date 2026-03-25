"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, Loader2, FileText } from "lucide-react";

interface FileUploadProps {
  onUploaded: () => void;
  onCancel: () => void;
}

export default function FileUpload({ onUploaded, onCancel }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [resourceType, setResourceType] = useState("posts");
  const [channelKey, setChannelKey] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    const valid = /\.(csv|json)$/i.test(f.name);
    if (!valid) {
      setError("Only CSV and JSON files are supported");
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setError("File must be under 50MB");
      return;
    }
    setFile(f);
    setError("");
    if (!sourceName) {
      setSourceName(f.name.replace(/\.(csv|json)$/i, ""));
    }
  }, [sourceName]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!file || !sourceName.trim()) return;

      setUploading(true);
      setError("");
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("source_name", sourceName.trim());
        formData.append("resource_type", resourceType);
        if (channelKey) formData.append("channel_key", channelKey);

        const res = await fetch("/api/admin/upload", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (data.success) {
          onUploaded();
        } else {
          setError(data.message || "Upload failed");
        }
      } catch {
        setError("Network error");
      } finally {
        setUploading(false);
      }
    },
    [file, sourceName, resourceType, channelKey, onUploaded],
  );

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs tracking-[0.3em] text-coral uppercase">
          File Upload
        </h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-white/30 hover:text-white transition-colors tracking-widest uppercase"
        >
          Back
        </button>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-sm p-12 flex flex-col items-center gap-4 cursor-pointer transition-colors ${
          dragOver
            ? "border-coral bg-coral/5"
            : file
              ? "border-sage/30 bg-sage/5"
              : "border-white/10 hover:border-white/20"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
        {file ? (
          <>
            <FileText className="w-8 h-8 text-sage" />
            <div className="text-sm font-mono text-offwhite">{file.name}</div>
            <div className="text-[10px] text-white/30 tracking-widest">
              {(file.size / 1024).toFixed(1)} KB
            </div>
          </>
        ) : (
          <>
            <Upload className="w-8 h-8 text-white/20" />
            <div className="text-xs font-mono text-white/40 tracking-widest">
              DROP CSV OR JSON FILE HERE
            </div>
            <div className="text-[10px] text-white/20">Max 50MB</div>
          </>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-[10px] text-white/30 uppercase tracking-widest">
          Source Name
        </label>
        <input
          type="text"
          value={sourceName}
          onChange={(e) => setSourceName(e.target.value)}
          placeholder="e.g. Q4 Revenue Data"
          className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          required
        />
      </div>

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
            placeholder="Optional"
            className="w-full bg-charcoal-light border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
          />
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
          disabled={uploading || !file || !sourceName.trim()}
          className="flex items-center gap-2 px-6 py-2 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors disabled:opacity-50"
        >
          {uploading && <Loader2 className="w-3 h-3 animate-spin" />}
          Upload &amp; Ingest
        </button>
      </div>
    </form>
  );
}
