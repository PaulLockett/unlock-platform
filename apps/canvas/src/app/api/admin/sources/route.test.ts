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

import { GET, POST } from "./route";

describe("GET /api/admin/sources", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAdmin.mockResolvedValue(mocks.mockAdmin);
    mocks.mockExecute.mockResolvedValue({
      success: true,
      all_sources: [{ name: "source-1" }, { name: "source-2" }],
    });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Not authenticated", 401));
    const res = await GET();
    const json = await expectJson(res, 401);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("returns 403 when not admin", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Admin access required", 403));
    const res = await GET();
    const json = await expectJson(res, 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Admin access required");
  });

  it("executes ManageSourceWorkflow with action=identify", async () => {
    await GET();
    expect(mocks.mockExecute).toHaveBeenCalledWith("ManageSourceWorkflow", {
      taskQueue: "data-manager-queue",
      workflowId: expect.stringMatching(/^identify-sources-\d+$/),
      args: [{ action: "identify" }],
    });
  });

  it("returns sources array on success", async () => {
    const res = await GET();
    const json = await expectJson(res, 200);
    expect(json.success).toBe(true);
    expect(json.sources).toEqual([{ name: "source-1" }, { name: "source-2" }]);
  });

  it("returns 500 when workflow fails", async () => {
    mocks.mockExecute.mockResolvedValue({ success: false, message: "workflow error" });
    const res = await GET();
    const json = await expectJson(res, 500);
    expect(json.success).toBe(false);
  });
});

describe("POST /api/admin/sources", () => {
  const validBody = {
    name: "my-source",
    protocol: "rest_api",
    service: "test-service",
    base_url: "https://api.example.com",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAdmin.mockResolvedValue(mocks.mockAdmin);
    mocks.mockExecute.mockResolvedValue({
      success: true,
      source: { id: "src-1", name: "my-source" },
    });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Not authenticated", 401));
    const req = buildRequest("POST", "/api/admin/sources", validBody);
    const res = await POST(req);
    const json = await expectJson(res, 401);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("returns 403 when not admin", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Admin access required", 403));
    const req = buildRequest("POST", "/api/admin/sources", validBody);
    const res = await POST(req);
    const json = await expectJson(res, 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Admin access required");
  });

  it("returns 400 on invalid body (missing name)", async () => {
    const req = buildRequest("POST", "/api/admin/sources", { protocol: "rest_api" });
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
  });

  it("returns 400 on invalid protocol", async () => {
    const req = buildRequest("POST", "/api/admin/sources", {
      name: "my-source",
      protocol: "invalid_protocol",
    });
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
  });

  it("executes ManageSourceWorkflow with action=register", async () => {
    const req = buildRequest("POST", "/api/admin/sources", validBody);
    await POST(req);
    expect(mocks.mockExecute).toHaveBeenCalledWith("ManageSourceWorkflow", {
      taskQueue: "data-manager-queue",
      workflowId: expect.stringMatching(/^register-source-my-source-\d+$/),
      args: [{ action: "register", ...validBody, resource_type: "posts" }],
    });
  });

  it("returns 201 on success", async () => {
    const req = buildRequest("POST", "/api/admin/sources", validBody);
    const res = await POST(req);
    const json = await expectJson(res, 201);
    expect(json.success).toBe(true);
    expect(json.source).toEqual({ id: "src-1", name: "my-source" });
  });
});
