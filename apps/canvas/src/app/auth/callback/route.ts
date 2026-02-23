import { createClient } from "@/lib/supabase/server";
import { type NextRequest, NextResponse } from "next/server";

/**
 * Resolve the external-facing origin from proxy headers.
 *
 * Behind a reverse proxy (cloudflared, Railway, Vercel), the request.url
 * origin is the internal server address (e.g. localhost:3000). The real
 * client-facing origin lives in forwarded headers.
 */
function resolveOrigin(request: NextRequest): string {
  const forwardedHost = request.headers.get("x-forwarded-host");
  const forwardedProto = request.headers.get("x-forwarded-proto") ?? "https";

  if (forwardedHost) {
    return `${forwardedProto}://${forwardedHost}`;
  }
  return request.nextUrl.origin;
}

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const origin = resolveOrigin(request);

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      return NextResponse.redirect(`${origin}/`);
    }
  }

  // If code is missing or exchange failed, redirect to login.
  return NextResponse.redirect(`${origin}/login`);
}
