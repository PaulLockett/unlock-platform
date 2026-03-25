import Link from "next/link";

export default function NotFound() {
  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-charcoal gap-6 font-mono">
      <div className="text-[clamp(4rem,12vw,10rem)] font-display text-sage leading-none">
        404
      </div>
      <div className="text-white/40 text-xs tracking-widest uppercase">
        Page not found
      </div>
      <Link
        href="/"
        className="text-coral text-xs font-mono tracking-widest hover:underline uppercase"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
