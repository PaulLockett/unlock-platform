import { vi } from "vitest";
import type { SessionUser } from "@/lib/auth/session";

export const mockUser: SessionUser = {
  id: "user-123",
  email: "testuser@example.com",
  role: "user",
};

export const mockAdmin: SessionUser = {
  id: "admin-456",
  email: "admin@example.com",
  role: "admin",
};

// Shared mock functions — these are the actual vi.fn() instances used by vi.mock
export const mockGetSessionUser = vi.fn();
export const mockRequireAuth = vi.fn();
export const mockRequireAdmin = vi.fn();

export class MockAuthError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "AuthError";
    this.status = status;
  }
}

/**
 * Configure the auth mock to return the specified user type.
 */
export function mockAuthAs(type: "user" | "admin" | null) {
  if (type === null) {
    mockGetSessionUser.mockResolvedValue(null);
    mockRequireAuth.mockRejectedValue(
      new MockAuthError("Authentication required", 401),
    );
    mockRequireAdmin.mockRejectedValue(
      new MockAuthError("Authentication required", 401),
    );
  } else if (type === "user") {
    mockGetSessionUser.mockResolvedValue(mockUser);
    mockRequireAuth.mockResolvedValue(mockUser);
    mockRequireAdmin.mockRejectedValue(
      new MockAuthError("Admin access required", 403),
    );
  } else {
    mockGetSessionUser.mockResolvedValue(mockAdmin);
    mockRequireAuth.mockResolvedValue(mockAdmin);
    mockRequireAdmin.mockResolvedValue(mockAdmin);
  }
}
