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

describe("POST /api/admin/ingest", () => {
  const validBody = {
    source_name: "test-source",
    source_type: "rest_api",
    resource_type: "posts",
    max_pages: 10,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockRequireAdmin.mockResolvedValue(mocks.mockAdmin);
    mocks.mockExecute.mockResolvedValue({ success: true, records_ingested: 42 });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("returns 401 when not authenticated", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Not authenticated", 401));
    const req = buildRequest("POST", "/api/admin/ingest", validBody);
    const res = await POST(req);
    const json = await expectJson(res, 401);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Not authenticated");
  });

  it("returns 403 when not admin", async () => {
    mocks.mockRequireAdmin.mockRejectedValue(new mocks.MockAuthError("Admin access required", 403));
    const req = buildRequest("POST", "/api/admin/ingest", validBody);
    const res = await POST(req);
    const json = await expectJson(res, 403);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Admin access required");
  });

  it("returns 400 on missing source_name", async () => {
    const req = buildRequest("POST", "/api/admin/ingest", {
      source_type: "rest_api",
    });
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
  });

  it("executes IngestWorkflow on success", async () => {
    const req = buildRequest("POST", "/api/admin/ingest", validBody);
    await POST(req);
    expect(mocks.mockExecute).toHaveBeenCalledWith("IngestWorkflow", {
      taskQueue: "data-manager-queue",
      workflowId: expect.stringMatching(/^ingest-test-source-\d+$/),
      args: [{ ...validBody }],
    });
  });

  it("returns 200 on success", async () => {
    const req = buildRequest("POST", "/api/admin/ingest", validBody);
    const res = await POST(req);
    const json = await expectJson(res, 200);
    expect(json.success).toBe(true);
    expect(json.records_ingested).toBe(42);
  });

  it("returns 400 when workflow fails", async () => {
    mocks.mockExecute.mockResolvedValue({ success: false, message: "ingestion failed" });
    const req = buildRequest("POST", "/api/admin/ingest", validBody);
    const res = await POST(req);
    const json = await expectJson(res, 400);
    expect(json.success).toBe(false);
  });
});
