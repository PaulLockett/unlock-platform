import { createClient } from "@/lib/supabase/server";
import type { User } from "@supabase/supabase-js";

export interface SessionUser {
  id: string;
  email: string;
  role: string; // "admin" | "user"
}

/**
 * Get the current session user, or null if not authenticated.
 */
export async function getSessionUser(): Promise<SessionUser | null> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) return null;

  return mapUser(user);
}

/**
 * Require authentication — throws a structured error for API routes.
 */
export async function requireAuth(): Promise<SessionUser> {
  const user = await getSessionUser();
  if (!user) {
    throw new AuthError("Authentication required", 401);
  }
  return user;
}

/**
 * Require admin role — checks Supabase app_metadata.role.
 */
export async function requireAdmin(): Promise<SessionUser> {
  const user = await requireAuth();
  if (user.role !== "admin") {
    throw new AuthError("Admin access required", 403);
  }
  return user;
}

function mapUser(user: User): SessionUser {
  return {
    id: user.id,
    email: user.email ?? "",
    role: (user.app_metadata?.role as string) ?? "user",
  };
}

export class AuthError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "AuthError";
    this.status = status;
  }
}
