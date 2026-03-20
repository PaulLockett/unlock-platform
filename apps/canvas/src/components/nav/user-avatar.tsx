"use client";

import Link from "next/link";

interface UserAvatarProps {
  email?: string;
  avatarUrl?: string | null;
  isActive?: boolean;
}

export default function UserAvatar({
  email,
  avatarUrl,
  isActive = false,
}: UserAvatarProps) {
  const initial = email?.charAt(0)?.toUpperCase() ?? "?";

  return (
    <Link href="/account" className="relative group cursor-pointer">
      <div
        className={`w-10 h-10 rounded-full border p-1 transition-colors ${
          isActive
            ? "border-coral"
            : "border-white/20 group-hover:border-coral"
        }`}
      >
        {avatarUrl ? (
          <div
            className="w-full h-full rounded-full bg-cover bg-center grayscale group-hover:grayscale-0 transition-all"
            style={{ backgroundImage: `url('${avatarUrl}')` }}
          />
        ) : (
          <div className="w-full h-full rounded-full bg-charcoal-light flex items-center justify-center text-sm font-mono text-white/60 group-hover:text-coral transition-colors">
            {initial}
          </div>
        )}
      </div>
    </Link>
  );
}
