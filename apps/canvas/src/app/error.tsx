"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Unhandled error:", error);
  }, [error]);

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-charcoal gap-6 font-mono">
      <div className="text-6xl font-display text-coral leading-none uppercase">
        Error
      </div>
      <div className="text-white/40 text-xs tracking-widest uppercase max-w-md text-center">
        Something went wrong. Please try again.
      </div>
      <button
        onClick={reset}
        className="px-6 py-2 bg-coral text-charcoal text-xs font-mono tracking-widest uppercase hover:bg-coral/90 transition-colors"
      >
        Try Again
      </button>
    </div>
  );
}
