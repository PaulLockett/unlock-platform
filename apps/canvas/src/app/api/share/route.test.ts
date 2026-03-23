import { describe, it, expect, vi, beforeEach } from "vitest";
import { buildRequest, expectJson } from "@/__tests__/helpers";

const mocks = vi.hoisted(() => {
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
    MockAuthError, mockGetSessionUser, mockRequireAuth, mockRequireAdmin,
    mockExecute, mockGetTemporalClient, mockUser, mockAdmin,
  };
});

vi.mock("@/lib/auth/session", () => ({
  getSessionUser: mocks.mockGetSessionUser,
  requireAuth: mocks.mockRequireAuth,
  requireAdmin: mocks.mockRequireAdmin,
  AuthError: mocks.MockAuthError,
}));
vi.mock("@/lib/temporal/client", () => ({
  getTemporalClient: mocks.mockGetTemporalClient,
  TASK_QUEUES: { DATA_MANAGER: "data-manager-queue", CONFIG_ACCESS: "config-access-queue" },
}));

import { POST } from "./route";

describe("POST /api/share", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAuth.mockResolvedValue(mocks.mockUser);
    mocks.mockExecute.mockResolvedValue({ success: true });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAuth.mockRejectedValue(
      new mocks.MockAuthError("Not authenticated", 401),
    );

    const req = buildRequest("POST", "/api/share", {
      share_token: "tok-abc",
      recipient_id: "user-789",
      permission: "read",
    });

    const json = await expectJson(await POST(req), 401);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("returns 400 on missing share_token", async () => {
    const req = buildRequest("POST", "/api/share", {
      recipient_id: "user-789",
      permission: "read",
    });

    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
  });

  it("returns 400 on invalid permission value", async () => {
    const req = buildRequest("POST", "/api/share", {
      share_token: "tok-abc",
      recipient_id: "user-789",
      permission: "owner",
    });

    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
  });

  it("executes ShareWorkflow with granter_id from session", async () => {
    const req = buildRequest("POST", "/api/share", {
      share_token: "tok-abc",
      recipient_id: "user-789",
      permission: "write",
    });

    const json = await expectJson(await POST(req), 200);
    expect(json.success).toBe(true);
    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "ShareWorkflow",
      expect.objectContaining({
        taskQueue: "data-manager-queue",
        args: [
          expect.objectContaining({
            share_token: "tok-abc",
            granter_id: "user-123",
            recipient_id: "user-789",
            recipient_type: "user",
            permission: "write",
          }),
        ],
      }),
    );
  });

  it("returns 403 when workflow result includes 'Access denied'", async () => {
    mocks.mockExecute.mockResolvedValue({
      success: false,
      message: "Access denied: insufficient permissions",
    });

    const req = buildRequest("POST", "/api/share", {
      share_token: "tok-abc",
      recipient_id: "user-789",
      permission: "read",
    });

    const json = await expectJson(await POST(req), 403);
    expect(json.success).toBe(false);
    expect(json.message).toContain("Access denied");
  });

  it("returns 400 when workflow result fails (non-access-denied)", async () => {
    mocks.mockExecute.mockResolvedValue({
      success: false,
      message: "Invalid share token",
    });

    const req = buildRequest("POST", "/api/share", {
      share_token: "tok-bad",
      recipient_id: "user-789",
      permission: "read",
    });

    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Invalid share token");
  });
});
