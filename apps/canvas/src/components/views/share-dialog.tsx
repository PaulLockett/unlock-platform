"use client";

import { useState, useCallback } from "react";
import { X, Link2, Lock, Globe, Loader2 } from "lucide-react";
import type { ViewPermission } from "@/types/platform";

interface ShareDialogProps {
  open: boolean;
  onClose: () => void;
  shareToken: string;
  viewId: string;
  permissions: ViewPermission[];
  visibility: string;
  createdBy: string;
}

export default function ShareDialog({
  open,
  onClose,
  shareToken,
  permissions,
  visibility,
  createdBy,
}: ShareDialogProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"read" | "write" | "admin">("read");
  const [inviting, setInviting] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleInvite = useCallback(async () => {
    if (!email.trim()) return;
    setInviting(true);
    try {
      await fetch("/api/share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          share_token: shareToken,
          recipient_id: email.trim(),
          recipient_type: "user",
          permission: role,
        }),
      });
      setEmail("");
    } catch {
      // silent
    } finally {
      setInviting(false);
    }
  }, [email, role, shareToken]);

  const handleCopyLink = useCallback(() => {
    const url = `${window.location.origin}/v/${shareToken}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [shareToken]);

  if (!open) return null;

  const roleLabel = (perm: string) => {
    switch (perm) {
      case "admin":
        return "Admin";
      case "write":
        return "Can edit";
      default:
        return "Can view";
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-charcoal/80 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative w-full max-w-lg mx-4 bg-charcoal-light border border-white/10">
        {/* Corner accents */}
        <div className="absolute -top-px -left-px w-8 h-8 border-t-2 border-l-2 border-coral" />
        <div className="absolute -top-px -right-px w-8 h-8 border-t-2 border-r-2 border-coral" />
        <div className="absolute -bottom-px -left-px w-8 h-8 border-b-2 border-l-2 border-coral" />
        <div className="absolute -bottom-px -right-px w-8 h-8 border-b-2 border-r-2 border-coral" />

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div>
            <div className="text-[10px] tracking-widest text-coral uppercase font-mono">
              Sharing
            </div>
            <h2 className="text-xl font-display uppercase text-sage mt-1">
              Share This View
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Add people */}
        <div className="p-6 space-y-4 border-b border-white/10">
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase">
            Add People
          </label>
          <div className="flex gap-2">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email or user ID..."
              className="flex-1 bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors"
            />
            <select
              value={role}
              onChange={(e) =>
                setRole(e.target.value as "read" | "write" | "admin")
              }
              className="bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite focus:outline-none focus:border-coral transition-colors"
            >
              <option value="read">Can view</option>
              <option value="write">Can edit</option>
              <option value="admin">Admin</option>
            </select>
            <button
              onClick={handleInvite}
              disabled={inviting || !email.trim()}
              className="px-4 py-2 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors disabled:opacity-50"
            >
              {inviting ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                "Invite"
              )}
            </button>
          </div>
        </div>

        {/* People with access */}
        <div className="p-6 space-y-3 border-b border-white/10 max-h-[200px] overflow-y-auto no-scrollbar">
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase">
            People With Access
          </label>

          {/* Owner */}
          <div className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-sage/20 flex items-center justify-center text-xs font-mono text-sage">
                {createdBy.charAt(0).toUpperCase()}
              </div>
              <div>
                <div className="text-xs font-mono text-offwhite">
                  {createdBy}
                </div>
                <div className="text-[10px] font-mono text-white/30">Owner</div>
              </div>
            </div>
            <span className="text-[10px] font-mono text-white/30 tracking-widest">
              OWNER
            </span>
          </div>

          {/* Granted permissions */}
          {permissions.map((perm) => (
            <div
              key={perm.principal_id}
              className="flex items-center justify-between py-2"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-charcoal border border-white/10 flex items-center justify-center text-xs font-mono text-white/60">
                  {perm.principal_id.charAt(0).toUpperCase()}
                </div>
                <div className="text-xs font-mono text-offwhite">
                  {perm.principal_id}
                </div>
              </div>
              <span className="text-[10px] font-mono text-white/40 tracking-widest uppercase">
                {roleLabel(perm.permission)}
              </span>
            </div>
          ))}
        </div>

        {/* General access */}
        <div className="p-6 space-y-2 border-b border-white/10">
          <label className="block text-[10px] font-mono tracking-widest text-white/40 uppercase">
            General Access
          </label>
          <div className="flex items-center gap-3">
            {visibility === "public" ? (
              <>
                <Globe className="w-4 h-4 text-sage" />
                <div>
                  <div className="text-xs font-mono text-offwhite">
                    Anyone with the link
                  </div>
                  <div className="text-[10px] font-mono text-white/30">
                    Anyone on the internet with the link can view
                  </div>
                </div>
              </>
            ) : (
              <>
                <Lock className="w-4 h-4 text-coral" />
                <div>
                  <div className="text-xs font-mono text-offwhite">
                    Restricted
                  </div>
                  <div className="text-[10px] font-mono text-white/30">
                    Only people with access can open with the link
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6">
          <button
            onClick={handleCopyLink}
            className="flex items-center gap-2 text-xs font-mono tracking-widest text-white/40 hover:text-white transition-colors uppercase"
          >
            <Link2 className="w-3 h-3" />
            {copied ? "Copied!" : "Copy Link"}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-charcoal border border-white/10 text-xs font-mono tracking-widest text-offwhite uppercase hover:border-white/20 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
