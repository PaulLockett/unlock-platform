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
vi.mock("@/lib/redis/views", () => ({
  retrieveView: vi.fn().mockResolvedValue({ success: false }),
}));
vi.mock("@/lib/redis/records", () => ({
  fetchSourceRecords: vi.fn().mockResolvedValue({ records: [], total_count: 0 }),
}));

import { POST } from "./route";

describe("POST /api/query", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.mockGetSessionUser.mockResolvedValue(mocks.mockUser);
    mocks.mockExecute.mockResolvedValue({ success: true, rows: [], total: 0 });
    mocks.mockGetTemporalClient.mockResolvedValue({
      workflow: { execute: mocks.mockExecute },
    });
  });

  it("returns 400 on missing share_token", async () => {
    const req = buildRequest("POST", "/api/query", {
      limit: 50,
    });

    const json = await expectJson(await POST(req), 400);
    expect(json.success).toBe(false);
  });

  it("passes user_id 'anonymous' when not authenticated", async () => {
    mocks.mockGetSessionUser.mockResolvedValue(null);

    const req = buildRequest("POST", "/api/query", {
      share_token: "tok-abc",
    });

    const json = await expectJson(await POST(req), 200);
    expect(json.success).toBe(true);
    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "QueryWorkflow",
      expect.objectContaining({
        args: [
          expect.objectContaining({
            user_id: "anonymous",
            user_type: "anonymous",
          }),
        ],
      }),
    );
  });

  it("passes user_id from session when authenticated", async () => {
    const req = buildRequest("POST", "/api/query", {
      share_token: "tok-abc",
    });

    const json = await expectJson(await POST(req), 200);
    expect(json.success).toBe(true);
    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "QueryWorkflow",
      expect.objectContaining({
        args: [
          expect.objectContaining({
            user_id: "user-123",
            user_type: "user",
          }),
        ],
      }),
    );
  });

  it("executes QueryWorkflow and returns success", async () => {
    mocks.mockExecute.mockResolvedValue({ success: true, rows: [{ id: 1 }], total: 1 });

    const req = buildRequest("POST", "/api/query", {
      share_token: "tok-abc",
      channel_key: "facebook",
      engagement_type: "likes",
      since: "2025-01-01",
      until: "2025-12-31",
      limit: 50,
      offset: 10,
    });

    const json = await expectJson(await POST(req), 200);
    expect(json.success).toBe(true);
    expect(mocks.mockExecute).toHaveBeenCalledWith(
      "QueryWorkflow",
      expect.objectContaining({
        taskQueue: "data-manager-queue",
        args: [
          expect.objectContaining({
            share_token: "tok-abc",
            channel_key: "facebook",
            engagement_type: "likes",
            since: "2025-01-01",
            until: "2025-12-31",
            limit: 50,
            offset: 10,
          }),
        ],
      }),
    );
  });

  it("returns 403 when result includes 'Access denied'", async () => {
    mocks.mockExecute.mockResolvedValue({
      success: false,
      message: "Access denied: view not shared with this user",
    });

    const req = buildRequest("POST", "/api/query", {
      share_token: "tok-private",
    });

    const json = await expectJson(await POST(req), 403);
    expect(json.success).toBe(false);
    expect(json.message).toContain("Access denied");
  });

  it("returns 500 when result fails (non-access-denied)", async () => {
    mocks.mockExecute.mockResolvedValue({
      success: false,
      message: "Query execution failed",
    });

    const req = buildRequest("POST", "/api/query", {
      share_token: "tok-abc",
    });

    const json = await expectJson(await POST(req), 500);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Query execution failed");
  });

  it("handles Temporal error gracefully (returns 500)", async () => {
    mocks.mockGetTemporalClient.mockRejectedValue(new Error("Temporal unavailable"));

    const req = buildRequest("POST", "/api/query", {
      share_token: "tok-abc",
    });

    const json = await expectJson(await POST(req), 500);
    expect(json.success).toBe(false);
    expect(json.message).toBe("Internal server error");
  });
});
