"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import SectionButton from "./section-button";
import UserAvatar from "./user-avatar";

export type NavSection = "public" | "shared" | "personal";

interface SideNavProps {
  activeSection?: NavSection;
  onSectionChange?: (section: NavSection) => void;
  userEmail?: string;
  userAvatar?: string | null;
}

export default function SideNav({
  activeSection = "personal",
  onSectionChange,
  userEmail,
  userAvatar,
}: SideNavProps) {
  const pathname = usePathname();
  const isAccountActive = pathname === "/account";

  return (
    <nav className="w-20 md:w-24 border-r border-white/10 flex flex-col justify-between items-center py-8 z-50 bg-charcoal shrink-0">
      {/* Logo */}
      <Link
        href="/"
        className="w-10 h-10 text-sage hover:text-coral transition-colors duration-300 cursor-pointer group"
      >
        <svg viewBox="0 0 100 100" fill="currentColor">
          <rect
            x="10"
            y="10"
            width="35"
            height="80"
            className="group-hover:translate-y-[-5px] transition-transform duration-300"
          />
          <rect
            x="55"
            y="10"
            width="35"
            height="50"
            className="group-hover:translate-y-[5px] transition-transform duration-300"
          />
        </svg>
      </Link>

      {/* Section buttons */}
      <div className="flex flex-col gap-12 items-center">
        <SectionButton
          label="PUBLIC"
          active={activeSection === "public"}
          onClick={() => onSectionChange?.("public")}
        />
        <div className="w-[1px] h-12 bg-white/10" />
        <SectionButton
          label="SHARED"
          active={activeSection === "shared"}
          onClick={() => onSectionChange?.("shared")}
        />
        <div className="w-[1px] h-12 bg-white/10" />
        <SectionButton
          label="PERSONAL"
          active={activeSection === "personal"}
          onClick={() => onSectionChange?.("personal")}
        />
      </div>

      {/* User avatar */}
      <UserAvatar
        email={userEmail}
        avatarUrl={userAvatar}
        isActive={isAccountActive}
      />
    </nav>
  );
}
