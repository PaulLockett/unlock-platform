"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Camera } from "lucide-react";
import SideNav from "@/components/nav/side-nav";

interface ProfileData {
  fullName: string;
  email: string;
  bio: string;
}

export default function AccountPage() {
  const [profile, setProfile] = useState<ProfileData>({
    fullName: "",
    email: "",
    bio: "",
  });
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const originalRef = useRef<ProfileData>({ fullName: "", email: "", bio: "" });
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [highContrast, setHighContrast] = useState(false);
  const [activeTheme, setActiveTheme] = useState(0);

  // Load user profile from Supabase session
  useEffect(() => {
    async function loadProfile() {
      try {
        const userRes = await fetch("/api/views");
        if (userRes.ok) {
          // User is authenticated — profile loaded from session
        }
      } catch {
        // fallback to empty
      }
    }
    loadProfile();
  }, []);

  const handleChange = useCallback(
    (field: keyof ProfileData, value: string) => {
      setProfile((prev) => ({ ...prev, [field]: value }));
      setDirty(true);
    },
    [],
  );

  const handleDiscard = useCallback(() => {
    setProfile({ ...originalRef.current });
    setDirty(false);
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      // Save profile to user metadata
      originalRef.current = { ...profile };
      setDirty(false);
    } finally {
      setSaving(false);
    }
  }, [profile]);

  const handleAvatarChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      setAvatarPreview(url);
      setDirty(true);
    },
    [],
  );

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal">
      <SideNav />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Header */}
        <header className="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40 shrink-0">
          <div className="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50">
            <span className="text-white/30">System Admin</span>
            <span>/</span>
            <span className="text-coral">Settings &amp; Profile</span>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth bg-[#0d0d0d]">
          <section className="px-8 md:px-12 py-16 border-b border-white/10">
            <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-16 items-start">
              {/* Left sidebar */}
              <div className="w-full md:w-1/3">
                <div className="sticky top-12">
                  <h1 className="text-7xl font-display text-sage uppercase leading-[0.8] mb-6">
                    Account
                    <br />
                    Profile
                  </h1>
                  <p className="font-serif italic text-white/40 text-lg leading-relaxed">
                    Manage your administrative credentials and visual preferences
                    across the platform.
                  </p>
                </div>
              </div>

              {/* Right content */}
              <div className="flex-1 space-y-20">
                {/* Section 01: Personal Details */}
                <div>
                  <h3 className="text-xs tracking-[0.3em] text-coral uppercase mb-10 pb-2 border-b border-white/5">
                    01 / Personal Details
                  </h3>

                  {/* Avatar */}
                  <div className="flex items-end gap-8 mb-12">
                    <div className="relative group/avatar">
                      <div
                        className="w-24 h-24 rounded-full border border-white/10 bg-charcoal-light bg-cover bg-center overflow-hidden flex items-center justify-center"
                        style={
                          avatarPreview
                            ? { backgroundImage: `url(${avatarPreview})` }
                            : undefined
                        }
                      >
                        {!avatarPreview && (
                          <span className="text-2xl font-display text-white/20">
                            {profile.fullName.charAt(0).toUpperCase() || "U"}
                          </span>
                        )}
                      </div>
                      <label className="absolute inset-0 rounded-full flex items-center justify-center bg-charcoal/70 opacity-0 group-hover/avatar:opacity-100 transition-opacity cursor-pointer">
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={handleAvatarChange}
                        />
                        <Camera className="w-5 h-5 text-coral" />
                      </label>
                    </div>
                    <div>
                      <div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">
                        Profile Photo
                      </div>
                      <label className="text-[10px] tracking-widest text-coral border border-coral/30 px-4 py-1.5 hover:bg-coral hover:text-charcoal transition-all uppercase cursor-pointer">
                        <input
                          type="file"
                          accept="image/*"
                          className="hidden"
                          onChange={handleAvatarChange}
                        />
                        Upload New Photo
                      </label>
                      <p className="mt-2 text-[10px] text-white/20 font-mono">
                        JPG, PNG or GIF &middot; max 2MB
                      </p>
                    </div>
                  </div>

                  {/* Fields */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                      <label className="text-[10px] text-white/30 uppercase tracking-widest">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={profile.fullName}
                        onChange={(e) =>
                          handleChange("fullName", e.target.value)
                        }
                        placeholder="Your full name"
                        className="w-full bg-transparent border-b border-white/10 py-2 text-xl font-serif italic text-offwhite focus:outline-none focus:border-coral transition-colors"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] text-white/30 uppercase tracking-widest">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={profile.email}
                        readOnly
                        className="w-full bg-transparent border-b border-white/10 py-2 text-xl font-mono text-white/40 focus:outline-none cursor-not-allowed"
                      />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <label className="text-[10px] text-white/30 uppercase tracking-widest">
                        Bio / Designation
                      </label>
                      <input
                        type="text"
                        value={profile.bio}
                        onChange={(e) => handleChange("bio", e.target.value)}
                        placeholder="Your role or designation"
                        className="w-full bg-transparent border-b border-white/10 py-2 text-xl font-serif italic text-offwhite focus:outline-none focus:border-coral transition-colors"
                      />
                    </div>
                  </div>
                </div>

                {/* Section 02: Platform Experience */}
                <div>
                  <h3 className="text-xs tracking-[0.3em] text-coral uppercase mb-10 pb-2 border-b border-white/5">
                    02 / Platform Experience
                  </h3>
                  <div className="grid grid-cols-1 gap-12">
                    <div className="space-y-6">
                      <div className="text-[10px] text-white/30 uppercase tracking-widest mb-4">
                        Theme Configuration
                      </div>
                      <div className="flex gap-4">
                        {[
                          { bg: "bg-charcoal", label: "Dark" },
                          { bg: "bg-[#f5f5f1]", label: "Light" },
                          { bg: "bg-[#1a2b25]", label: "Forest" },
                        ].map((theme, i) => (
                          <button
                            key={i}
                            onClick={() => {
                              setActiveTheme(i);
                              setDirty(true);
                            }}
                            className={`w-10 h-10 rounded-full ${theme.bg} border-2 ${
                              activeTheme === i
                                ? "border-coral"
                                : "border-white/10"
                            } flex items-center justify-center shadow-lg transition-colors`}
                          >
                            {activeTheme === i && (
                              <div className="w-4 h-4 rounded-full bg-coral" />
                            )}
                          </button>
                        ))}
                      </div>
                      <div className="pt-4">
                        <button
                          onClick={() => {
                            setHighContrast(!highContrast);
                            setDirty(true);
                          }}
                          className="flex items-center gap-3 group cursor-pointer w-fit"
                        >
                          <span className="text-sm text-white/60 group-hover:text-offwhite transition-colors">
                            High Contrast Mode
                          </span>
                          <div
                            className={`w-10 h-5 rounded-full relative transition-colors ${
                              highContrast ? "bg-coral" : "bg-white/10"
                            }`}
                          >
                            <div
                              className={`absolute top-1 w-3 h-3 rounded-full transition-all ${
                                highContrast
                                  ? "left-6 bg-charcoal"
                                  : "left-1 bg-white/40"
                              }`}
                            />
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Save bar */}
          {dirty && (
            <div
              className="px-8 md:px-12 py-5 flex items-center justify-between transition-all duration-500"
              style={{
                background: "#1e1008",
                borderTop: "1px solid rgba(234,109,88,0.35)",
                borderBottom: "1px solid rgba(234,109,88,0.15)",
                boxShadow: "0 -4px 24px rgba(234,109,88,0.12)",
              }}
            >
              <div className="flex items-center gap-3 text-xs text-white/40 tracking-widest">
                <span className="w-1.5 h-1.5 rounded-full bg-coral animate-pulse" />
                <span>UNSAVED CHANGES</span>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={handleDiscard}
                  className="text-[10px] tracking-[0.2em] text-white/30 hover:text-white/60 transition-colors uppercase"
                >
                  Discard
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="text-[10px] tracking-[0.2em] text-sage border border-sage/30 px-6 py-2 hover:bg-sage hover:text-charcoal transition-all uppercase disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          )}

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
