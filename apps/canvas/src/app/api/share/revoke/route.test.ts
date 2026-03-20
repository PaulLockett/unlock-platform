import { describe, it, expect, vi, beforeEach } from "vitest";
import { buildRequest, expectJson } from "@/__tests__/helpers";

// Hoist mock state so vi.mock factories can reference it
const {
  mockGetSessionUser,
  mockRequireAuth,
  mockRequireAdmin,
  MockAuthError,
  mockGetTemporalClient,
  mockExecute,
} = vi.hoisted(() => {
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

  const mockExecute = vi.fn();
  const mockGetTemporalClient = vi.fn().mockResolvedValue({
    workflow: { execute: mockExecute },
  });

  return {
    mockGetSessionUser,
    mockRequireAuth,
    mockRequireAdmin,
    MockAuthError,
    mockGetTemporalClient,
    mockExecute,
  };
});

vi.mock("@/lib/auth/session", () => ({
  getSessionUser: mockGetSessionUser,
  requireAuth: mockRequireAuth,
  requireAdmin: mockRequireAdmin,
  AuthError: MockAuthError,
}));

vi.mock("@/lib/temporal/client", () => ({
  getTemporalClient: mockGetTemporalClient,
  TASK_QUEUES: {
    DATA_MANAGER: "data-manager-queue",
    CONFIG_ACCESS: "config-access-queue",
  },
}));

import { POST } from "./route";

describe("POST /api/share/revoke", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockExecute.mockResolvedValue({ success: true, message: "revoked" });
  });

  it("returns 400 on invalid body", async () => {
    mockRequireAdmin.mockResolvedValue({ id: "admin-1", role: "admin" });
    const req = buildRequest("POST", "/api/share/revoke", {});
    const res = await POST(req);
    await expectJson(res, 400);
  });

  it("returns 401 when not authenticated", async () => {
    mockRequireAdmin.mockRejectedValue(
      new MockAuthError("Authentication required", 401),
    );
    const req = buildRequest("POST", "/api/share/revoke", {
      view_id: "v-1",
      principal_id: "u-1",
    });
    const res = await POST(req);
    await expectJson(res, 401);
  });

  it("returns 403 when not admin", async () => {
    mockRequireAdmin.mockRejectedValue(
      new MockAuthError("Admin access required", 403),
    );
    const req = buildRequest("POST", "/api/share/revoke", {
      view_id: "v-1",
      principal_id: "u-1",
    });
    const res = await POST(req);
    await expectJson(res, 403);
  });

  it("executes RevokeAccessWorkflow on success", async () => {
    mockRequireAdmin.mockResolvedValue({ id: "admin-1", role: "admin" });
    mockExecute.mockResolvedValue({ success: true, message: "revoked" });
    const req = buildRequest("POST", "/api/share/revoke", {
      view_id: "v-1",
      principal_id: "u-1",
    });
    const res = await POST(req);
    const json = await expectJson(res, 200);
    expect(json.success).toBe(true);
    expect(mockExecute).toHaveBeenCalledWith(
      "RevokeAccessWorkflow",
      expect.objectContaining({
        taskQueue: "data-manager-queue",
      }),
    );
  });

  it("returns 400 when workflow fails", async () => {
    mockRequireAdmin.mockResolvedValue({ id: "admin-1", role: "admin" });
    mockExecute.mockResolvedValue({ success: false, message: "not found" });
    const req = buildRequest("POST", "/api/share/revoke", {
      view_id: "v-1",
      principal_id: "u-1",
    });
    const res = await POST(req);
    await expectJson(res, 400);
  });
});
