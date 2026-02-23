"use client";

import posthog from "posthog-js";
import { PostHogProvider as PHProvider } from "posthog-js/react";
import { useEffect } from "react";

import { createClient } from "@/lib/supabase/client";

/**
 * Top-level client providers for the Canvas app.
 *
 * PostHog is initialized in instrumentation-client.ts (Next.js 15.3+ pattern).
 * This component handles:
 * 1. PostHogProvider context so usePostHog() works in child components
 * 2. Supabase auth state → PostHog identity sync:
 *    - INITIAL_SESSION / SIGNED_IN  → posthog.identify(user.id, {email})
 *    - SIGNED_OUT                    → posthog.reset()
 */
export default function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const supabase = createClient();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (
        (event === "INITIAL_SESSION" || event === "SIGNED_IN") &&
        session?.user
      ) {
        posthog.identify(session.user.id, {
          email: session.user.email,
        });
      }

      if (event === "SIGNED_OUT") {
        posthog.reset();
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return <PHProvider client={posthog}>{children}</PHProvider>;
}
