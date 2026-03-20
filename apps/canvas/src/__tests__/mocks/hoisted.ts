/**
 * Shared hoisted mock state for vi.hoisted().
 *
 * Every route test file needs the same hoisted mocks for auth + temporal.
 * This file provides a factory that returns all the mock functions and
 * classes needed, designed to be spread into vi.hoisted().
 *
 * Usage in test files:
 *   const mocks = vi.hoisted(() => createHoistedMocks());
 *   vi.mock("@/lib/auth/session", () => ({ ...mocks.authModule }));
 *   vi.mock("@/lib/temporal/client", () => ({ ...mocks.temporalModule }));
 */
import { vi } from "vitest";

export function createHoistedMocks() {
  class MockAuthError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.name = "AuthError";
      this.status = status;
    }
  }

  const mockGetSessionUser = vi.fn();
  const mockRequireAuth = vi.fn();
  const mockRequireAdmin = vi.fn();

  const mockExecute = vi.fn().mockResolvedValue({ success: true });
  const mockGetTemporalClient = vi.fn().mockResolvedValue({
    workflow: { execute: mockExecute },
  });

  const mockUser = { id: "user-123", email: "testuser@example.com", role: "user" };
  const mockAdmin = { id: "admin-456", email: "admin@example.com", role: "admin" };

  return {
    MockAuthError,
    mockGetSessionUser,
    mockRequireAuth,
    mockRequireAdmin,
    mockExecute,
    mockGetTemporalClient,
    mockUser,
    mockAdmin,

    authModule: {
      getSessionUser: mockGetSessionUser,
      requireAuth: mockRequireAuth,
      requireAdmin: mockRequireAdmin,
      AuthError: MockAuthError,
    },

    temporalModule: {
      getTemporalClient: mockGetTemporalClient,
      TASK_QUEUES: {
        DATA_MANAGER: "data-manager-queue",
        CONFIG_ACCESS: "config-access-queue",
      },
    },

    // Convenience: set auth state
    asAdmin() {
      mockGetSessionUser.mockResolvedValue(mockAdmin);
      mockRequireAuth.mockResolvedValue(mockAdmin);
      mockRequireAdmin.mockResolvedValue(mockAdmin);
    },
    asUser() {
      mockGetSessionUser.mockResolvedValue(mockUser);
      mockRequireAuth.mockResolvedValue(mockUser);
      mockRequireAdmin.mockRejectedValue(new MockAuthError("Admin access required", 403));
    },
    asAnonymous() {
      mockGetSessionUser.mockResolvedValue(null);
      mockRequireAuth.mockRejectedValue(new MockAuthError("Authentication required", 401));
      mockRequireAdmin.mockRejectedValue(new MockAuthError("Authentication required", 401));
    },
  };
}
