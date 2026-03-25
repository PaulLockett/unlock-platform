import Link from "next/link";

export default function UnauthorizedPage() {
  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-charcoal gap-6 font-mono">
      <div className="text-6xl font-display text-coral leading-none uppercase">
        Restricted
      </div>
      <div className="text-white/40 text-xs tracking-widest uppercase max-w-md text-center">
        This view is restricted. Sign in to request access.
      </div>
      <Link
        href="/login"
        className="px-6 py-2 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors"
      >
        Sign In
      </Link>
    </div>
  );
}
